from langchain.llms import OpenAI, HuggingFacePipeline
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import chromadb
from typing import List, Dict, Optional, Tuple
import asyncio
import json
import re
from ..core.config import settings

class VectorStoreManager:
    """Manages the Chroma vector database for semantic search"""
    
    def __init__(self):
        self.client = chromadb.HttpClient(host=settings.chroma_url.replace("http://", "").split(":")[0], 
                                        port=int(settings.chroma_url.split(":")[-1]))
        self.embeddings = self._get_embeddings()
        self.collection_name = "argo_data_embeddings"
        
    def _get_embeddings(self):
        """Initialize embedding model"""
        if settings.openai_api_key:
            return OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        else:
            return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    async def add_documents(self, documents: List[Document]):
        """Add documents to vector store"""
        try:
            collection = self.client.get_or_create_collection(name=self.collection_name)
            
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Generate embeddings
            embeddings = await asyncio.to_thread(self.embeddings.embed_documents, texts)
            
            # Add to Chroma
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=[f"doc_{i}" for i in range(len(texts))]
            )
            
            return {"status": "success", "count": len(documents)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """Perform semantic search"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            query_embedding = await asyncio.to_thread(self.embeddings.embed_query, query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            return [
                {
                    "content": doc,
                    "metadata": meta,
                    "distance": dist
                }
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0], 
                    results["distances"][0]
                )
            ]
        except Exception as e:
            return []

class NaturalLanguageToSQL:
    """Converts natural language queries to SQL using LangChain RAG"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.vector_store = VectorStoreManager()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define database schema information
        self.schema_info = self._get_schema_info()
        
    def _initialize_llm(self):
        """Initialize the language model"""
        if settings.openai_api_key:
            return OpenAI(
                openai_api_key=settings.openai_api_key,
                temperature=0.1,
                max_tokens=1000
            )
        else:
            # Use HuggingFace model as fallback
            return HuggingFacePipeline.from_model_id(
                model_id="microsoft/DialoGPT-medium",
                task="text-generation",
                model_kwargs={"temperature": 0.1}
            )
    
    def _get_schema_info(self) -> str:
        """Return database schema information for the LLM"""
        return """
        Database Schema for ARGO Oceanographic Data:
        
        Tables:
        1. argo_floats: id, float_id, platform_number, project_name, deployment_date, status, location
        2. argo_profiles: id, float_id, cycle_number, profile_date, latitude, longitude, location, profile_type, data_mode
        3. argo_measurements: id, profile_id, pressure, depth, temperature, salinity, oxygen, ph, nitrate, quality_flag
        4. satellite_data: id, satellite_name, instrument, data_type, measurement_date, latitude, longitude, value, unit
        5. buoy_data: id, buoy_id, buoy_type, measurement_date, latitude, longitude, sea_surface_temperature, air_temperature, wind_speed
        6. glider_data: id, glider_id, mission_name, measurement_date, latitude, longitude, depth, temperature, salinity, oxygen, chlorophyll
        7. ocean_anomalies: id, anomaly_type, severity, start_date, end_date, latitude, longitude, description, confidence_score
        
        Key Relationships:
        - argo_floats.id → argo_profiles.float_id
        - argo_profiles.id → argo_measurements.profile_id
        
        Common Query Patterns:
        - Temperature and salinity by depth/location/time
        - Ocean anomaly detection
        - Float trajectory analysis
        - Multi-source data correlation
        """
    
    async def generate_sql(self, natural_query: str, user_context: Optional[Dict] = None) -> Dict:
        """
        Convert natural language to SQL with explainable reasoning
        """
        try:
            # Get relevant context from vector store
            context_docs = await self.vector_store.similarity_search(natural_query, k=3)
            context_text = "\n".join([doc["content"] for doc in context_docs])
            
            # Create the prompt template
            prompt_template = PromptTemplate(
                input_variables=["schema", "context", "query", "user_context"],
                template="""
                You are an expert SQL generator for oceanographic data analysis.
                
                Database Schema:
                {schema}
                
                Relevant Context:
                {context}
                
                User Context: {user_context}
                
                Natural Language Query: {query}
                
                Generate a SQL query that answers the user's question. Follow these rules:
                1. Use PostgreSQL syntax with PostGIS functions for spatial queries
                2. Include appropriate JOINs for related tables
                3. Use proper date/time filtering
                4. Add spatial filters when location is mentioned
                5. Include quality filters (exclude poor quality data)
                6. Limit results to reasonable numbers (use LIMIT)
                
                Provide your response in this JSON format:
                {{
                    "sql": "SELECT ...",
                    "reasoning": "Explanation of the query logic",
                    "confidence": 0.85,
                    "suggested_visualizations": ["map", "time_series", "depth_profile"]
                }}
                """
            )
            
            # Create and run the chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt_template,
                memory=self.memory
            )
            
            response = await asyncio.to_thread(
                chain.run,
                schema=self.schema_info,
                context=context_text,
                query=natural_query,
                user_context=json.dumps(user_context or {})
            )
            
            # Parse the response
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                result = self._parse_fallback_response(response, natural_query)
            
            return result
            
        except Exception as e:
            return {
                "sql": "SELECT 'Error generating query' as message;",
                "reasoning": f"Error: {str(e)}",
                "confidence": 0.0,
                "suggested_visualizations": []
            }
    
    def _parse_fallback_response(self, response: str, query: str) -> Dict:
        """Fallback parser for non-JSON responses"""
        
        # Extract SQL using regex
        sql_match = re.search(r'SELECT.*?;', response, re.IGNORECASE | re.DOTALL)
        sql = sql_match.group(0) if sql_match else self._generate_simple_query(query)
        
        return {
            "sql": sql,
            "reasoning": "Generated using fallback parsing due to LLM response format issues",
            "confidence": 0.6,
            "suggested_visualizations": self._infer_visualizations(query)
        }
    
    def _generate_simple_query(self, query: str) -> str:
        """Generate a simple query based on keywords"""
        query_lower = query.lower()
        
        if "temperature" in query_lower and "depth" in query_lower:
            return """
            SELECT am.depth, AVG(am.temperature) as avg_temperature, COUNT(*) as measurements
            FROM argo_measurements am
            JOIN argo_profiles ap ON am.profile_id = ap.id
            WHERE am.temperature IS NOT NULL 
            AND am.quality_flag != '4'
            GROUP BY am.depth
            ORDER BY am.depth
            LIMIT 100;
            """
        elif "salinity" in query_lower:
            return """
            SELECT ap.latitude, ap.longitude, am.salinity, ap.profile_date
            FROM argo_measurements am
            JOIN argo_profiles ap ON am.profile_id = ap.id
            WHERE am.salinity IS NOT NULL 
            AND am.quality_flag != '4'
            ORDER BY ap.profile_date DESC
            LIMIT 1000;
            """
        else:
            return """
            SELECT ap.latitude, ap.longitude, am.temperature, am.salinity, ap.profile_date
            FROM argo_measurements am
            JOIN argo_profiles ap ON am.profile_id = ap.id
            WHERE am.temperature IS NOT NULL 
            AND am.salinity IS NOT NULL
            AND am.quality_flag != '4'
            ORDER BY ap.profile_date DESC
            LIMIT 500;
            """
    
    def _infer_visualizations(self, query: str) -> List[str]:
        """Infer appropriate visualizations based on query"""
        query_lower = query.lower()
        visualizations = []
        
        if any(word in query_lower for word in ["map", "location", "region", "area"]):
            visualizations.append("map")
        
        if any(word in query_lower for word in ["time", "trend", "series", "over time"]):
            visualizations.append("time_series")
        
        if "depth" in query_lower:
            visualizations.append("depth_profile")
        
        if any(word in query_lower for word in ["temperature", "salinity"]):
            visualizations.extend(["map", "depth_profile"])
        
        return list(set(visualizations)) if visualizations else ["map", "time_series"]

class QueryExplainer:
    """Provides explanations for generated queries and results"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM for explanations"""
        if settings.openai_api_key:
            return OpenAI(
                openai_api_key=settings.openai_api_key,
                temperature=0.3,
                max_tokens=500
            )
        else:
            return HuggingFacePipeline.from_model_id(
                model_id="microsoft/DialoGPT-medium",
                task="text-generation"
            )
    
    async def explain_query(self, natural_query: str, sql_query: str, results_count: int) -> str:
        """Generate explanation for the query and results"""
        
        prompt = f"""
        Explain this oceanographic data query in simple terms:
        
        User asked: "{natural_query}"
        Generated SQL: {sql_query}
        Found {results_count} results
        
        Provide a clear, educational explanation of:
        1. What data was searched
        2. How the search was performed
        3. What the results represent
        4. Any limitations or considerations
        
        Keep it accessible for scientists, policymakers, and students.
        """
        
        try:
            explanation = await asyncio.to_thread(self.llm, prompt)
            return explanation
        except Exception as e:
            return f"Query retrieved {results_count} oceanographic measurements. The search focused on data matching your criteria from ARGO floats and related ocean monitoring systems."

# Initialize global instances
vector_store_manager = VectorStoreManager()
nl_to_sql = NaturalLanguageToSQL()
query_explainer = QueryExplainer()