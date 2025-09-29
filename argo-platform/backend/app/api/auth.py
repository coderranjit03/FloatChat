from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

try:
    from ..core.config import settings
    from ..core.database import get_db
    from ..models.models import User
except ImportError:
    # Development fallback
    settings = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

class AuthenticationError(Exception):
    pass

class AuthService:
    """Handles authentication and authorization"""
    
    def __init__(self):
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if settings and settings.firebase_project_id:
                if not firebase_admin._apps:  # Check if already initialized
                    cred_dict = {
                        "type": "service_account",
                        "project_id": settings.firebase_project_id,
                        "private_key_id": settings.firebase_private_key_id,
                        "private_key": settings.firebase_private_key.replace('\\n', '\n') if settings.firebase_private_key else None,
                        "client_email": settings.firebase_client_email,
                        "client_id": settings.firebase_client_id,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": settings.firebase_client_x509_cert_url
                    }
                    
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    print("✅ Firebase initialized successfully")
            else:
                print("⚠️ Firebase configuration not found, using JWT-only authentication")
        except Exception as e:
            print(f"⚠️ Firebase initialization failed: {e}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    async def verify_firebase_token(self, token: str) -> dict:
        """Verify Firebase ID token"""
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise AuthenticationError(f"Firebase token verification failed: {e}")
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        
        if settings and settings.secret_key:
            encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        else:
            # Fallback for development
            encoded_jwt = jwt.encode(to_encode, "dev_secret_key", algorithm="HS256")
        
        return encoded_jwt
    
    async def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            secret_key = settings.secret_key if settings else "dev_secret_key"
            algorithm = settings.algorithm if settings else "HS256"
            
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Token verification failed: {e}")
    
    async def get_or_create_user(self, db: AsyncSession, user_info: dict) -> User:
        """Get existing user or create new one"""
        try:
            # Check if user exists by email or firebase_uid
            query = select(User).where(
                (User.email == user_info.get("email")) |
                (User.firebase_uid == user_info.get("firebase_uid"))
            )
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                # Create new user
                user = User(
                    email=user_info.get("email"),
                    firebase_uid=user_info.get("firebase_uid"),
                    full_name=user_info.get("name", ""),
                    role=user_info.get("role", "student"),  # Default role
                    is_active=True
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            else:
                # Update user info if needed
                if user_info.get("name") and user.full_name != user_info["name"]:
                    user.full_name = user_info["name"]
                    user.updated_at = datetime.utcnow()
                    await db.commit()
            
            return user
        except Exception as e:
            await db.rollback()
            raise AuthenticationError(f"User creation/retrieval failed: {e}")

# Initialize auth service
auth_service = AuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user
    Supports both Firebase tokens and JWT tokens
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # Try Firebase token first
        try:
            firebase_payload = await auth_service.verify_firebase_token(token)
            user_info = {
                "firebase_uid": firebase_payload["uid"],
                "email": firebase_payload.get("email"),
                "name": firebase_payload.get("name"),
                "role": "student"  # Default role, can be updated later
            }
            user = await auth_service.get_or_create_user(db, user_info)
            return user
        except AuthenticationError:
            # If Firebase fails, try JWT
            pass
        
        # Try JWT token
        try:
            payload = await auth_service.verify_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            
            # Get user from database
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if user is None:
                raise credentials_exception
            
            return user
        except AuthenticationError:
            raise credentials_exception
        
    except Exception as e:
        print(f"Authentication error: {e}")
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_roles: list):
    """Role-based access control decorator"""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}"
            )
        return current_user
    return role_checker

# Role-specific dependencies
def get_scientist_user():
    return Depends(require_role(["scientist", "admin"]))

def get_policymaker_user():
    return Depends(require_role(["policymaker", "admin"]))

def get_admin_user():
    return Depends(require_role(["admin"]))

# Authentication endpoints
from fastapi import APIRouter
from pydantic import BaseModel

auth_router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: dict

@auth_router.post("/login", response_model=TokenResponse)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password (development mode)"""
    try:
        # This is a simple implementation for development
        # In production, you'd verify against your user database
        user_info = {
            "email": login_request.email,
            "name": login_request.email.split("@")[0],
            "role": "scientist" if "scientist" in login_request.email else "student"
        }
        
        user = await auth_service.get_or_create_user(db, user_info)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes if settings else 30)
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=access_token_expires.total_seconds(),
            user_info={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

@auth_router.post("/firebase-login", response_model=TokenResponse)
async def firebase_login(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Login with Firebase ID token"""
    try:
        firebase_payload = await auth_service.verify_firebase_token(firebase_token)
        
        user_info = {
            "firebase_uid": firebase_payload["uid"],
            "email": firebase_payload.get("email"),
            "name": firebase_payload.get("name"),
            "role": "student"  # Default role
        }
        
        user = await auth_service.get_or_create_user(db, user_info)
        
        # Create JWT access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes if settings else 30)
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=access_token_expires.total_seconds(),
            user_info={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Firebase authentication failed: {str(e)}"
        )

@auth_router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }