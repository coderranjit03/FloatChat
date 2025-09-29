from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import numpy as np
import asyncio
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

try:
    from ..models.models import (
        OceanAnomaly, UserAlert, User, ArgoProfile, ArgoMeasurement
    )
    from ..core.config import settings
except ImportError:
    # Development fallback
    settings = None

class AlertService:
    """Handles anomaly detection and user alerts"""
    
    def __init__(self):
        self.anomaly_thresholds = {
            "temperature": {
                "heatwave": 2.0,  # 2°C above normal
                "cold_spell": -2.0,  # 2°C below normal
            },
            "salinity": {
                "high_salinity": 1.0,  # 1 PSU above normal
                "low_salinity": -1.0,  # 1 PSU below normal
            }
        }
    
    async def get_anomalies(
        self,
        db: AsyncSession,
        severity: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get ocean anomalies based on filters"""
        try:
            query = select(OceanAnomaly)
            
            if severity:
                query = query.where(OceanAnomaly.severity == severity)
            if anomaly_type:
                query = query.where(OceanAnomaly.anomaly_type == anomaly_type)
            if start_date:
                query = query.where(OceanAnomaly.start_date >= start_date)
            if end_date:
                query = query.where(OceanAnomaly.end_date <= end_date)
            
            query = query.order_by(OceanAnomaly.start_date.desc())
            result = await db.execute(query)
            anomalies = result.scalars().all()
            
            return [
                {
                    "id": str(anomaly.id),
                    "anomaly_type": anomaly.anomaly_type,
                    "severity": anomaly.severity,
                    "location": {
                        "latitude": float(anomaly.latitude),
                        "longitude": float(anomaly.longitude)
                    },
                    "start_date": anomaly.start_date.isoformat(),
                    "end_date": anomaly.end_date.isoformat() if anomaly.end_date else None,
                    "description": anomaly.description,
                    "confidence_score": float(anomaly.confidence_score) if anomaly.confidence_score else None,
                    "data_source": anomaly.data_source
                }
                for anomaly in anomalies
            ]
        except Exception as e:
            print(f"Error getting anomalies: {e}")
            return []
    
    async def run_anomaly_detection(self, db: AsyncSession):
        """Run anomaly detection algorithms on recent data"""
        try:
            print("🔍 Starting anomaly detection...")
            
            # Get recent measurements (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            # Detect temperature anomalies
            temp_anomalies = await self._detect_temperature_anomalies(db, seven_days_ago)
            
            # Detect salinity anomalies
            salinity_anomalies = await self._detect_salinity_anomalies(db, seven_days_ago)
            
            # Store anomalies in database
            all_anomalies = temp_anomalies + salinity_anomalies
            
            for anomaly_data in all_anomalies:
                anomaly = OceanAnomaly(**anomaly_data)
                db.add(anomaly)
            
            await db.commit()
            
            # Send alerts to relevant users
            if all_anomalies:
                await self._send_anomaly_alerts(db, all_anomalies)
            
            print(f"✅ Anomaly detection completed. Found {len(all_anomalies)} anomalies")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error in anomaly detection: {e}")
    
    async def _detect_temperature_anomalies(
        self, 
        db: AsyncSession, 
        since_date: datetime
    ) -> List[Dict[str, Any]]:
        """Detect temperature anomalies using statistical methods"""
        try:
            # Get recent temperature measurements
            query = select(
                ArgoProfile.latitude,
                ArgoProfile.longitude,
                ArgoProfile.profile_date,
                ArgoMeasurement.temperature,
                ArgoMeasurement.depth
            ).select_from(
                ArgoMeasurement
            ).join(
                ArgoProfile, ArgoMeasurement.profile_id == ArgoProfile.id
            ).where(
                and_(
                    ArgoProfile.profile_date >= since_date,
                    ArgoMeasurement.temperature.isnot(None),
                    ArgoMeasurement.depth <= 10  # Surface measurements only
                )
            )
            
            result = await db.execute(query)
            measurements = result.fetchall()
            
            if len(measurements) < 10:  # Need enough data
                return []
            
            # Calculate statistics
            temperatures = [float(m.temperature) for m in measurements]
            mean_temp = np.mean(temperatures)
            std_temp = np.std(temperatures)
            
            anomalies = []
            
            # Group by location (rough grid)
            location_groups = {}
            for m in measurements:
                # Round to 1-degree grid
                lat_key = round(float(m.latitude))
                lon_key = round(float(m.longitude))
                key = (lat_key, lon_key)
                
                if key not in location_groups:
                    location_groups[key] = []
                location_groups[key].append(m)
            
            # Check each location for anomalies
            for (lat_key, lon_key), group in location_groups.items():
                group_temps = [float(m.temperature) for m in group]
                group_mean = np.mean(group_temps)
                
                # Check for significant deviation
                deviation = group_mean - mean_temp
                
                if abs(deviation) > 2 * std_temp:  # 2 standard deviations
                    severity = self._calculate_severity(abs(deviation), std_temp)
                    anomaly_type = "heatwave" if deviation > 0 else "cold_spell"
                    
                    anomalies.append({
                        "anomaly_type": anomaly_type,
                        "severity": severity,
                        "start_date": min(m.profile_date for m in group),
                        "end_date": max(m.profile_date for m in group),
                        "latitude": lat_key,
                        "longitude": lon_key,
                        "description": f"Temperature anomaly: {deviation:+.1f}°C from normal",
                        "confidence_score": min(0.95, abs(deviation) / (3 * std_temp)),
                        "data_source": "ARGO"
                    })
            
            return anomalies
            
        except Exception as e:
            print(f"Error detecting temperature anomalies: {e}")
            return []
    
    async def _detect_salinity_anomalies(
        self, 
        db: AsyncSession, 
        since_date: datetime
    ) -> List[Dict[str, Any]]:
        """Detect salinity anomalies using statistical methods"""
        try:
            # Get recent salinity measurements
            query = select(
                ArgoProfile.latitude,
                ArgoProfile.longitude,
                ArgoProfile.profile_date,
                ArgoMeasurement.salinity,
                ArgoMeasurement.depth
            ).select_from(
                ArgoMeasurement
            ).join(
                ArgoProfile, ArgoMeasurement.profile_id == ArgoProfile.id
            ).where(
                and_(
                    ArgoProfile.profile_date >= since_date,
                    ArgoMeasurement.salinity.isnot(None),
                    ArgoMeasurement.depth <= 10  # Surface measurements only
                )
            )
            
            result = await db.execute(query)
            measurements = result.fetchall()
            
            if len(measurements) < 10:
                return []
            
            # Calculate statistics
            salinities = [float(m.salinity) for m in measurements]
            mean_salinity = np.mean(salinities)
            std_salinity = np.std(salinities)
            
            anomalies = []
            
            # Group by location
            location_groups = {}
            for m in measurements:
                lat_key = round(float(m.latitude))
                lon_key = round(float(m.longitude))
                key = (lat_key, lon_key)
                
                if key not in location_groups:
                    location_groups[key] = []
                location_groups[key].append(m)
            
            # Check each location for anomalies
            for (lat_key, lon_key), group in location_groups.items():
                group_salinities = [float(m.salinity) for m in group]
                group_mean = np.mean(group_salinities)
                
                deviation = group_mean - mean_salinity
                
                if abs(deviation) > 1.5 * std_salinity:  # 1.5 standard deviations for salinity
                    severity = self._calculate_severity(abs(deviation), std_salinity)
                    anomaly_type = "high_salinity" if deviation > 0 else "low_salinity"
                    
                    anomalies.append({
                        "anomaly_type": anomaly_type,
                        "severity": severity,
                        "start_date": min(m.profile_date for m in group),
                        "end_date": max(m.profile_date for m in group),
                        "latitude": lat_key,
                        "longitude": lon_key,
                        "description": f"Salinity anomaly: {deviation:+.2f} PSU from normal",
                        "confidence_score": min(0.95, abs(deviation) / (2 * std_salinity)),
                        "data_source": "ARGO"
                    })
            
            return anomalies
            
        except Exception as e:
            print(f"Error detecting salinity anomalies: {e}")
            return []
    
    def _calculate_severity(self, deviation: float, std_dev: float) -> str:
        """Calculate anomaly severity based on deviation"""
        if deviation > 3 * std_dev:
            return "extreme"
        elif deviation > 2 * std_dev:
            return "high"
        elif deviation > 1.5 * std_dev:
            return "medium"
        else:
            return "low"
    
    async def _send_anomaly_alerts(self, db: AsyncSession, anomalies: List[Dict[str, Any]]):
        """Send alerts to relevant users"""
        try:
            # Get users who should receive alerts (scientists and policymakers)
            query = select(User).where(
                and_(
                    User.is_active == True,
                    or_(User.role == "scientist", User.role == "policymaker", User.role == "admin")
                )
            )
            result = await db.execute(query)
            users = result.scalars().all()
            
            for user in users:
                for anomaly in anomalies:
                    # Create alert record
                    alert = UserAlert(
                        user_id=user.id,
                        alert_type=f"anomaly_{anomaly['anomaly_type']}",
                        message=f"Ocean anomaly detected: {anomaly['description']} at {anomaly['latitude']:.1f}°N, {anomaly['longitude']:.1f}°E",
                        is_read=False
                    )
                    db.add(alert)
                    
                    # Send email notification
                    await self._send_email_alert(user, anomaly)
            
            await db.commit()
            
        except Exception as e:
            print(f"Error sending alerts: {e}")
    
    async def _send_email_alert(self, user: User, anomaly: Dict[str, Any]):
        """Send email alert to user"""
        try:
            if not settings or not settings.email_username:
                print("⚠️ Email configuration not available")
                return
            
            # Create email message
            msg = MimeMultipart()
            msg['From'] = settings.alert_from_email
            msg['To'] = user.email
            msg['Subject'] = f"Ocean Anomaly Alert - {anomaly['anomaly_type'].replace('_', ' ').title()}"
            
            # Email body
            body = f"""
            Dear {user.full_name or user.email},
            
            An ocean anomaly has been detected in your area of interest:
            
            Type: {anomaly['anomaly_type'].replace('_', ' ').title()}
            Severity: {anomaly['severity'].title()}
            Location: {anomaly['latitude']:.2f}°N, {anomaly['longitude']:.2f}°E
            Description: {anomaly['description']}
            Confidence: {anomaly['confidence_score']:.0%}
            Detection Date: {anomaly['start_date']}
            
            This alert was generated by the ARGO Oceanographic Data Platform's automated anomaly detection system.
            
            Please review the data in your dashboard for more details.
            
            Best regards,
            ARGO Platform Alert System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            await asyncio.to_thread(self._send_smtp_email, msg)
            
        except Exception as e:
            print(f"Error sending email alert: {e}")
    
    def _send_smtp_email(self, msg: MimeMultipart):
        """Send email via SMTP"""
        try:
            server = smtplib.SMTP(settings.email_host, settings.email_port)
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)
            server.quit()
            
            print(f"✅ Email sent to {msg['To']}")
            
        except Exception as e:
            print(f"❌ SMTP error: {e}")
    
    async def create_manual_alert(
        self, 
        db: AsyncSession, 
        anomaly_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a manual anomaly alert"""
        try:
            anomaly = OceanAnomaly(**anomaly_data)
            db.add(anomaly)
            await db.commit()
            await db.refresh(anomaly)
            
            # Send alerts
            await self._send_anomaly_alerts(db, [anomaly_data])
            
            return {
                "id": str(anomaly.id),
                "message": "Anomaly alert created and notifications sent",
                "status": "success"
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "message": f"Error creating alert: {str(e)}",
                "status": "error"
            }
    
    async def mark_alert_read(self, db: AsyncSession, alert_id: str, user_id: str) -> bool:
        """Mark an alert as read"""
        try:
            query = select(UserAlert).where(
                and_(
                    UserAlert.id == alert_id,
                    UserAlert.user_id == user_id
                )
            )
            result = await db.execute(query)
            alert = result.scalar_one_or_none()
            
            if alert:
                alert.is_read = True
                await db.commit()
                return True
            return False
            
        except Exception as e:
            print(f"Error marking alert as read: {e}")
            return False
    
    async def get_user_alerts(
        self, 
        db: AsyncSession, 
        user_id: str, 
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get alerts for a specific user"""
        try:
            query = select(UserAlert).where(UserAlert.user_id == user_id)
            
            if unread_only:
                query = query.where(UserAlert.is_read == False)
            
            query = query.order_by(UserAlert.sent_at.desc())
            result = await db.execute(query)
            alerts = result.scalars().all()
            
            return [
                {
                    "id": str(alert.id),
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "is_read": alert.is_read,
                    "sent_at": alert.sent_at.isoformat()
                }
                for alert in alerts
            ]
            
        except Exception as e:
            print(f"Error getting user alerts: {e}")
            return []