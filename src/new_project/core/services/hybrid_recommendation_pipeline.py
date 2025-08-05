"""
Hybrid Recommendation Pipeline Service
=====================================

Service that combines Neo4j knowledge graph, ChromaDB vector database,
and OpenAI GPT-4 integration for comprehensive tool recommendations.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import time
import asyncio
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json

from .knowledge_graph import KnowledgeGraphService
from .vector_database import VectorDatabaseService  
from .openai_integration import OpenAIIntegrationService
from ..models.hybrid_recommendations import (
    HybridRecommendationRequest, HybridRecommendationResponse,
    ComponentScore, RecommendationResult, ConfidenceMetrics
)
from ..models.openai_integration import ToolRecommendationRequest, SafetyAssessmentRequest

logger = logging.getLogger(__name__)


@dataclass
class RecommendationEngine:
    """Core recommendation engine that coordinates all components"""
    
    def __init__(self, knowledge_graph_service: KnowledgeGraphService,
                 vector_database_service: VectorDatabaseService,
                 openai_service: OpenAIIntegrationService):
        self.knowledge_graph_service = knowledge_graph_service
        self.vector_database_service = vector_database_service
        self.openai_service = openai_service
    
    def get_knowledge_graph_recommendations(self, request: HybridRecommendationRequest) -> List[Dict[str, Any]]:
        """Get recommendations from knowledge graph"""
        try:
            # Extract task from user query (simplified)
            task_name = self._extract_task_from_query(request.user_query)
            
            # Get tools for the task
            tools = self.knowledge_graph_service.find_tools_for_task(task_name)
            
            # Process results
            kg_results = []
            for tool in tools:
                # Calculate confidence based on safety rating and other factors
                base_confidence = min(tool.get("safety_rating", 3.0) / 5.0, 1.0)
                
                # Adjust confidence based on user skill level
                skill_multiplier = self._get_skill_multiplier(request.user_skill_level)
                confidence = min(base_confidence * skill_multiplier, 1.0)
                
                kg_results.append({
                    "name": tool["name"],
                    "source": "knowledge_graph",
                    "confidence_score": confidence,
                    "category": tool.get("category", ""),
                    "brand": tool.get("brand", ""),
                    "safety_rating": tool.get("safety_rating", 0.0),
                    "reasoning": f"Found in knowledge graph for task: {task_name}"
                })
            
            return kg_results
            
        except Exception as e:
            logger.error(f"Knowledge graph recommendations failed: {e}")
            return []
    
    def get_vector_database_recommendations(self, request: HybridRecommendationRequest) -> List[Dict[str, Any]]:
        """Get recommendations from vector database"""
        try:
            # Perform similarity search
            results = self.vector_database_service.similarity_search_products(
                query_text=request.user_query,
                n_results=10,
                filters=self._build_vector_filters(request)
            )
            
            # Process results
            vector_results = []
            for result in results:
                vector_results.append({
                    "name": result["name"],
                    "source": "vector_database", 
                    "confidence_score": result["similarity_score"],
                    "category": result.get("category", ""),
                    "brand": result.get("brand", ""),
                    "price": result.get("price"),
                    "product_code": result.get("product_code", ""),
                    "reasoning": f"Vector similarity score: {result['similarity_score']:.3f}"
                })
            
            return vector_results
            
        except Exception as e:
            logger.error(f"Vector database recommendations failed: {e}")
            return []
    
    def get_openai_recommendations(self, request: HybridRecommendationRequest) -> List[Dict[str, Any]]:
        """Get recommendations from OpenAI"""
        try:
            # Create OpenAI request
            openai_request = ToolRecommendationRequest(
                task=request.user_query,
                user_skill_level=request.user_skill_level,
                budget=request.budget,
                workspace=request.workspace,
                project_type=request.project_type,
                preferred_brands=request.preferred_brands,
                existing_tools=request.existing_tools
            )
            
            # Get recommendations
            response = self.openai_service.get_tool_recommendations(openai_request)
            
            # Process results
            openai_results = []
            for tool_name in response.recommendations:
                openai_results.append({
                    "name": tool_name,
                    "source": "openai",
                    "confidence_score": response.confidence_score,
                    "reasoning": response.reasoning,
                    "safety_notes": response.safety_notes,
                    "estimated_cost": response.estimated_cost,
                    "alternative_options": response.alternative_options
                })
            
            return openai_results
            
        except Exception as e:
            logger.error(f"OpenAI recommendations failed: {e}")
            return []
    
    def get_safety_recommendations(self, request: HybridRecommendationRequest) -> Dict[str, Any]:
        """Get safety recommendations"""
        try:
            # Create safety assessment request
            safety_request = SafetyAssessmentRequest(
                tools=[],  # Will be populated based on tool recommendations
                task=request.user_query,
                user_experience=request.user_skill_level,
                workspace_conditions=request.workspace,
                materials=[]
            )
            
            # Get safety assessment
            response = self.openai_service.assess_safety_requirements(safety_request)
            
            return {
                "safety_score": response.safety_score,
                "required_ppe": response.required_ppe,
                "osha_compliance": response.osha_compliance,
                "risk_factors": response.risk_factors,
                "mitigation_strategies": response.mitigation_strategies,
                "training_required": response.training_required
            }
            
        except Exception as e:
            logger.error(f"Safety recommendations failed: {e}")
            return {
                "safety_score": 5,
                "required_ppe": [],
                "osha_compliance": [],
                "risk_factors": [],
                "mitigation_strategies": [],
                "training_required": False
            }
    
    def get_all_recommendations_parallel(self, request: HybridRecommendationRequest) -> List[Dict[str, Any]]:
        """Get recommendations from all sources in parallel"""
        all_results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks
            kg_future = executor.submit(self.get_knowledge_graph_recommendations, request)
            vector_future = executor.submit(self.get_vector_database_recommendations, request)
            openai_future = executor.submit(self.get_openai_recommendations, request)
            
            # Collect results
            try:
                kg_results = kg_future.result(timeout=10)
                all_results.extend(kg_results)
            except Exception as e:
                logger.error(f"Knowledge graph parallel execution failed: {e}")
            
            try:
                vector_results = vector_future.result(timeout=10)
                all_results.extend(vector_results)
            except Exception as e:
                logger.error(f"Vector database parallel execution failed: {e}")
            
            try:
                openai_results = openai_future.result(timeout=10)
                all_results.extend(openai_results)
            except Exception as e:
                logger.error(f"OpenAI parallel execution failed: {e}")
        
        return all_results
    
    def _extract_task_from_query(self, query: str) -> str:
        """Extract task name from user query (simplified implementation)"""
        # This is a simplified implementation
        # In production, this could use NLP techniques
        query_lower = query.lower()
        
        if "cut" in query_lower:
            return "Cut Wood Planks"
        elif "drill" in query_lower:
            return "Drill Pilot Holes"
        elif "measure" in query_lower or "level" in query_lower:
            return "Check Level"
        else:
            return "General DIY Task"
    
    def _get_skill_multiplier(self, skill_level: str) -> float:
        """Get confidence multiplier based on skill level"""
        multipliers = {
            "beginner": 0.8,
            "intermediate": 1.0,
            "advanced": 1.2
        }
        return multipliers.get(skill_level, 1.0)
    
    def _build_vector_filters(self, request: HybridRecommendationRequest) -> Optional[Dict[str, Any]]:
        """Build filters for vector database search"""
        filters = {}
        
        # Budget filter
        if request.budget > 0:
            filters["price"] = {"$lt": request.budget}
        
        # Brand filter
        if request.preferred_brands:
            filters["brand"] = {"$in": request.preferred_brands}
        
        return filters if filters else None


@dataclass
class ResultMerger:
    """Service for merging and ranking results from multiple sources"""
    
    def __init__(self, confidence_threshold: float = 0.6, max_results: int = 10,
                 scoring_weights: Optional[Dict[str, float]] = None):
        self.confidence_threshold = confidence_threshold
        self.max_results = max_results
        self.scoring_weights = scoring_weights or {
            "knowledge_graph": 0.3,
            "vector_database": 0.4,
            "openai": 0.3
        }
    
    def deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate results from multiple sources"""
        seen_tools = {}
        deduplicated = []
        
        for result in results:
            tool_name = result["name"].lower().strip()
            
            if tool_name in seen_tools:
                # Merge with existing result
                existing = seen_tools[tool_name]
                existing["sources"].append(result["source"])
                
                # Update confidence score (take highest)
                if result["confidence_score"] > existing["confidence_score"]:
                    existing["confidence_score"] = result["confidence_score"]
                    existing["reasoning"] = result.get("reasoning", existing["reasoning"])
                
                # Merge other attributes
                for key, value in result.items():
                    if key not in existing and value is not None:
                        existing[key] = value
            else:
                # Add new result
                result["sources"] = [result["source"]]
                seen_tools[tool_name] = result
                deduplicated.append(result)
        
        return deduplicated
    
    def calculate_weighted_confidence(self, merged_result: Dict[str, Any]) -> float:
        """Calculate weighted confidence score for merged result"""
        if "sources" not in merged_result:
            return merged_result.get("confidence_score", 0.0)
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for source_info in merged_result.get("sources", []):
            if isinstance(source_info, dict):
                source = source_info["source"]
                confidence = source_info["confidence_score"]
            else:
                # Handle string source format
                source = source_info
                confidence = merged_result.get("confidence_score", 0.0)
            
            weight = self.scoring_weights.get(source, 1.0)
            total_weighted_score += confidence * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank results by overall score"""
        for i, result in enumerate(results):
            # Calculate ranking score based on multiple factors
            confidence = result.get("confidence_score", 0.0)
            safety_rating = result.get("safety_rating", 3.0) / 5.0  # Normalize to 0-1
            price_factor = 1.0  # Could be based on budget fit
            
            # Simple ranking formula
            ranking_score = (confidence * 0.5) + (safety_rating * 0.3) + (price_factor * 0.2)
            
            result["ranking_score"] = ranking_score
            result["final_rank"] = i + 1  # Will be updated after sorting
        
        # Sort by ranking score
        sorted_results = sorted(results, key=lambda x: x["ranking_score"], reverse=True)
        
        # Update final ranks
        for i, result in enumerate(sorted_results):
            result["final_rank"] = i + 1
        
        return sorted_results
    
    def filter_by_budget(self, results: List[Dict[str, Any]], budget: float) -> List[Dict[str, Any]]:
        """Filter results by budget constraints"""
        if budget <= 0:
            return results
        
        filtered = []
        for result in results:
            price = result.get("price") or result.get("estimated_cost")
            if price is None or price <= budget:
                filtered.append(result)
        
        return filtered
    
    def filter_by_skill_level(self, results: List[Dict[str, Any]], skill_level: str) -> List[Dict[str, Any]]:
        """Filter results by user skill level"""
        skill_levels = {"beginner": 1, "intermediate": 2, "advanced": 3}
        user_level = skill_levels.get(skill_level, 2)
        
        filtered = []
        for result in results:
            # Assume tools with higher complexity require higher skill
            difficulty = result.get("difficulty_level")
            if difficulty:
                tool_level = skill_levels.get(difficulty, 2)
                if tool_level <= user_level:
                    filtered.append(result)
            else:
                # If no difficulty specified, include it
                filtered.append(result)
        
        return filtered
    
    def filter_by_confidence(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results by confidence threshold"""
        return [r for r in results if r.get("confidence_score", 0.0) >= self.confidence_threshold]


class HybridRecommendationPipeline:
    """Main hybrid recommendation pipeline service"""
    
    def __init__(self, knowledge_graph_service: KnowledgeGraphService,
                 vector_database_service: VectorDatabaseService,
                 openai_service: OpenAIIntegrationService,
                 confidence_threshold: float = 0.7,
                 max_recommendations: int = 10):
        
        self.knowledge_graph_service = knowledge_graph_service
        self.vector_database_service = vector_database_service
        self.openai_service = openai_service
        self.confidence_threshold = confidence_threshold
        self.max_recommendations = max_recommendations
        
        # Initialize components
        self.recommendation_engine = RecommendationEngine(
            knowledge_graph_service, vector_database_service, openai_service
        )
        self.result_merger = ResultMerger(confidence_threshold, max_recommendations)
        
        # Simple in-memory cache
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("Hybrid recommendation pipeline initialized")
    
    def check_component_health(self) -> Dict[str, bool]:
        """Check health of all pipeline components"""
        health_status = {
            "knowledge_graph": False,
            "vector_database": False,
            "openai_integration": False,
            "overall_healthy": False
        }
        
        try:
            health_status["knowledge_graph"] = self.knowledge_graph_service.health_check()
        except Exception as e:
            logger.error(f"Knowledge graph health check failed: {e}")
        
        try:
            health_status["vector_database"] = self.vector_database_service.health_check()
        except Exception as e:
            logger.error(f"Vector database health check failed: {e}")
        
        try:
            health_status["openai_integration"] = self.openai_service.health_check()
        except Exception as e:
            logger.error(f"OpenAI integration health check failed: {e}")
        
        # Overall health requires at least 2/3 components to be healthy
        healthy_count = sum(health_status.values())
        health_status["overall_healthy"] = healthy_count >= 2
        
        return health_status
    
    def validate_request(self, request: HybridRecommendationRequest) -> Tuple[bool, List[str]]:
        """Validate recommendation request"""
        errors = []
        
        if not request.user_query or not request.user_query.strip():
            errors.append("User query cannot be empty")
        
        if request.user_skill_level not in ["beginner", "intermediate", "advanced"]:
            errors.append("Invalid skill level")
        
        if request.budget < 0:
            errors.append("Budget cannot be negative")
        
        if not request.workspace or not request.workspace.strip():
            errors.append("Workspace cannot be empty")
        
        if not request.project_type or not request.project_type.strip():
            errors.append("Project type cannot be empty")
        
        return len(errors) == 0, errors
    
    def _generate_cache_key(self, request: HybridRecommendationRequest) -> str:
        """Generate cache key for request"""
        # Create deterministic hash of request parameters
        request_str = json.dumps(request.to_dict(), sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        return (time.time() - cache_entry["timestamp"]) < self.cache_ttl
    
    def get_recommendations(self, request: HybridRecommendationRequest) -> HybridRecommendationResponse:
        """Get hybrid recommendations"""
        start_time = time.time()
        
        # Validate request
        is_valid, errors = self.validate_request(request)
        if not is_valid:
            raise ValueError(f"Invalid request: {', '.join(errors)}")
        
        # Check cache
        cache_key = self._generate_cache_key(request)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            cached_response = self.cache[cache_key]["response"]
            cached_response.from_cache = True
            return cached_response
        
        warnings = []
        
        # Get recommendations from all sources
        try:
            all_results = self.recommendation_engine.get_all_recommendations_parallel(request)
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            warnings.append(f"Some recommendation sources failed: {str(e)}")
            all_results = []
        
        # Merge and deduplicate results
        deduplicated_results = self.result_merger.deduplicate_results(all_results)
        
        # Apply filters
        filtered_results = self.result_merger.filter_by_budget(deduplicated_results, request.budget)
        filtered_results = self.result_merger.filter_by_skill_level(filtered_results, request.user_skill_level)
        filtered_results = self.result_merger.filter_by_confidence(filtered_results)
        
        # Rank results
        ranked_results = self.result_merger.rank_results(filtered_results)
        
        # Limit to max recommendations
        final_results = ranked_results[:self.max_recommendations]
        
        # Convert to RecommendationResult objects
        recommendations = []
        for result in final_results:
            rec = RecommendationResult(
                name=result["name"],
                confidence_score=result["confidence_score"],
                sources=result.get("sources", [result.get("source", "unknown")]),
                price=result.get("price"),
                safety_rating=result.get("safety_rating"),
                reasoning=result.get("reasoning"),
                category=result.get("category"),
                brand=result.get("brand"),
                specifications=result.get("specifications", {})
            )
            recommendations.append(rec)
        
        # Create component scores
        component_scores = [
            ComponentScore("knowledge_graph", 0.8, 0.3),
            ComponentScore("vector_database", 0.85, 0.4),
            ComponentScore("openai", 0.9, 0.3)
        ]
        
        # Calculate total confidence
        total_confidence = sum(score.weighted_score() for score in component_scores)
        
        # Create response
        response = HybridRecommendationResponse.create_with_timestamp(
            recommendations=recommendations,
            total_confidence=total_confidence,
            component_scores=component_scores,
            start_time=start_time,
            warnings=warnings
        )
        
        # Cache response
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        return response
    
    def get_recommendations_parallel(self, request: HybridRecommendationRequest) -> HybridRecommendationResponse:
        """Get recommendations with optimized parallel execution"""
        # This is essentially the same as get_recommendations since we already use parallel execution
        return self.get_recommendations(request)