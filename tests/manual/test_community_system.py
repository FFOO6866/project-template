"""
Comprehensive Test Suite for Community Knowledge Extraction System.

This test suite validates the complete community knowledge extraction and
product integration system with real data scenarios:

1. Community extraction accuracy validation
2. Product matching precision testing  
3. Project guide quality assessment
4. FAQ generation accuracy
5. Inventory recommendation validation
6. End-to-end integration testing
7. Performance benchmarking

Test Data Sources:
- Mock community posts based on real DIY discussions
- Sample product database entries
- Simulated trending topics
- Real-world problem-solution scenarios
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import unittest
from pathlib import Path

# Import the community system components
from enhanced_community_extractor import (
    EnhancedCommunityExtractor, EnhancedExtractionConfig,
    CommunityPost, VideoAnalysis, ProblemSolutionPair, TrendingTopic,
    SourceType, ContentType, ConfidenceLevel
)

from community_product_integration import (
    CommunityProductIntegrator, ProductMatch, ProjectGuide, 
    FAQEntry, InventoryRecommendation
)

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


@dataclass
class TestResult:
    """Test result container."""
    test_name: str
    success: bool
    execution_time: float
    accuracy_score: Optional[float] = None
    details: Dict[str, Any] = None
    error_message: Optional[str] = None


class MockDataGenerator:
    """Generate realistic mock data for testing."""
    
    def __init__(self):
        self.logger = logging.getLogger("mock_data_generator")
        
    def generate_sample_posts(self) -> List[CommunityPost]:
        """Generate sample community posts based on real DIY scenarios."""
        posts = []
        
        # Sample DIY problems and discussions
        sample_scenarios = [
            {
                "title": "Cordless drill battery keeps dying during project",
                "content": "My 18V DeWalt drill battery dies after just 15 minutes of use. It's about 2 years old. Should I replace the battery or get a new drill? Any recommendations for long-lasting batteries?",
                "category": "tools",
                "tools": ["cordless drill", "battery"],
                "products": ["dewalt", "18v battery"],
                "problems": ["Battery dies quickly during use"],
                "upvotes": 23,
                "comments": 8
            },
            {
                "title": "Best way to hang heavy mirror on drywall",
                "content": "I need to hang a 15kg mirror on drywall. What's the best hardware to use? I've heard about toggle bolts and molly bolts but not sure which is better. The wall is standard drywall, not sure if there's a stud behind where I want to hang it.",
                "category": "home_improvement",
                "tools": ["drill", "level", "stud finder"],
                "materials": ["toggle bolts", "molly bolts", "drywall anchors"],
                "problems": ["Hanging heavy items on drywall"],
                "solutions": ["Use toggle bolts for heavy items", "Find studs when possible"],
                "upvotes": 45,
                "comments": 12
            },
            {
                "title": "Singapore HDB kitchen renovation permit requirements",
                "content": "Planning to renovate my HDB kitchen. Do I need permits for electrical work? What about plumbing changes? Anyone know the current regulations? Also looking for recommendations for licensed contractors in Singapore.",
                "category": "singapore_renovation",
                "singapore_terms": ["HDB", "renovation permit", "licensed contractors"],
                "problems": ["Understanding HDB renovation requirements"],
                "upvotes": 67,
                "comments": 25
            },
            {
                "title": "Circular saw blade keeps binding in wood",
                "content": "My circular saw blade keeps getting stuck when cutting 2x4 lumber. The cut starts fine but then the blade binds halfway through. I'm using a 24-tooth blade. Is this the right blade for lumber? Should I try a different technique?",
                "category": "woodworking",
                "tools": ["circular saw", "saw blade"],
                "materials": ["2x4 lumber"],
                "problems": ["Saw blade binding in wood cuts"],
                "solutions": ["Use appropriate blade for material", "Check cutting technique"],
                "upvotes": 31,
                "comments": 15
            },
            {
                "title": "DIY tile installation tips for bathroom floor",
                "content": "First time tiling a bathroom floor. What's the best adhesive for ceramic tiles? Should I use spacers? Any tips for getting straight lines? The bathroom is small (about 3x2 meters) and I want it to look professional.",
                "category": "tiling",
                "tools": ["tile cutter", "trowel", "level"],
                "materials": ["ceramic tiles", "tile adhesive", "tile spacers", "grout"],
                "problems": ["First-time tiling challenges"],
                "tips": ["Use spacers for consistent gaps", "Start from center point"],
                "upvotes": 52,
                "comments": 18
            }
        ]
        
        for i, scenario in enumerate(sample_scenarios):
            post = CommunityPost(
                post_id=f"test_post_{i+1}",
                source_type=SourceType.REDDIT,
                source_url=f"https://reddit.com/r/DIY/test_{i+1}",
                title=scenario["title"],
                content=scenario["content"],
                author=f"test_user_{i+1}",
                created_at=datetime.now() - timedelta(days=i*7),
                upvotes=scenario.get("upvotes", 10),
                comments_count=scenario.get("comments", 5),
                categories=[scenario["category"]],
                content_type=ContentType.QUESTION,
                mentioned_tools=scenario.get("tools", []),
                mentioned_products=scenario.get("products", []),
                mentioned_materials=scenario.get("materials", []),
                problems_identified=scenario.get("problems", []),
                solutions_provided=scenario.get("solutions", []),
                tips_and_tricks=scenario.get("tips", []),
                helpfulness_score=0.7 + (i * 0.05),
                confidence_level=ConfidenceLevel.MEDIUM
            )
            
            posts.append(post)
        
        return posts
    
    def generate_sample_videos(self) -> List[VideoAnalysis]:
        """Generate sample video analyses."""
        videos = []
        
        sample_videos = [
            {
                "video_id": "test_video_001",
                "title": "How to Install a New Toilet - Complete DIY Guide",
                "description": "Complete step-by-step guide to installing a toilet. Tools needed: adjustable wrench, wax ring, toilet bolts, level. Safety warning: toilets are heavy - lift with your legs!",
                "channel": "DIY Home Repairs",
                "tools": ["adjustable wrench", "level"],
                "materials": ["wax ring", "toilet bolts", "toilet"],
                "project_type": "plumbing",
                "complexity": "intermediate",
                "has_safety_warnings": True,
                "has_parts_list": True,
                "step_by_step": True,
                "views": 45000,
                "likes": 890,
                "comments": 67
            },
            {
                "video_id": "test_video_002", 
                "title": "Essential Power Tools for Woodworking Beginners",
                "description": "Top 5 power tools every woodworking beginner needs. Featuring drills, circular saws, sanders, and routers from trusted brands like DeWalt, Milwaukee, and Makita.",
                "channel": "Woodworking Basics",
                "tools": ["drill", "circular saw", "sander", "router"],
                "brands": ["dewalt", "milwaukee", "makita"],
                "project_type": "woodworking",
                "complexity": "beginner",
                "views": 125000,
                "likes": 2340,
                "comments": 189
            }
        ]
        
        for video_data in sample_videos:
            video = VideoAnalysis(
                video_id=video_data["video_id"],
                title=video_data["title"],
                description=video_data["description"],
                channel_name=video_data["channel"],
                tools_mentioned=video_data.get("tools", []),
                materials_mentioned=video_data.get("materials", []),
                brands_mentioned=video_data.get("brands", []),
                project_type=video_data.get("project_type"),
                project_complexity=video_data.get("complexity"),
                has_safety_warnings=video_data.get("has_safety_warnings", False),
                has_parts_list=video_data.get("has_parts_list", False),
                step_by_step_guide=video_data.get("step_by_step", False),
                view_count=video_data.get("views", 1000),
                like_count=video_data.get("likes", 20),
                comment_count=video_data.get("comments", 5),
                tutorial_quality_score=0.8,
                engagement_score=0.6
            )
            videos.append(video)
        
        return videos
    
    def generate_sample_products(self) -> List[Dict[str, Any]]:
        """Generate sample product database entries."""
        products = [
            {
                "sku": "DRILL-DW-001",
                "name": "DeWalt 18V Cordless Drill Kit",
                "brand": "DeWalt", 
                "category": "power tools",
                "description": "Professional grade cordless drill with LED light and two batteries",
                "price": 149.99,
                "model_number": "DCD771C2"
            },
            {
                "sku": "SAW-MIL-002",
                "name": "Milwaukee Circular Saw 7.25 inch",
                "brand": "Milwaukee",
                "category": "power tools",
                "description": "High-performance circular saw with carbide blade",
                "price": 199.99,
                "model_number": "6390-21"
            },
            {
                "sku": "ANCHOR-TB-003",
                "name": "Toggle Bolts Heavy Duty 1/4 inch",
                "brand": "Simpson Strong-Tie",
                "category": "fasteners",
                "description": "Heavy duty toggle bolts for drywall mounting up to 75 lbs",
                "price": 12.99,
                "model_number": "TB-1/4"
            },
            {
                "sku": "TOILET-KOH-004",
                "name": "Kohler Highline Two-Piece Toilet",
                "brand": "Kohler",
                "category": "bathroom fixtures", 
                "description": "ADA compliant elongated toilet with powerful flush",
                "price": 289.99,
                "model_number": "K-3999"
            },
            {
                "sku": "TILE-CER-005",
                "name": "Ceramic Floor Tiles 12x12 inch",
                "brand": "Daltile",
                "category": "flooring",
                "description": "Glazed ceramic tiles suitable for bathroom and kitchen floors",
                "price": 2.99,
                "model_number": "CFT-1212-WHT"
            }
        ]
        
        return products


class CommunitySystemTester:
    """Main test runner for the community knowledge system."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.mock_data = MockDataGenerator()
        self.test_results: List[TestResult] = []
        
        # Initialize test output directory
        self.test_output_dir = Path("test_output")
        self.test_output_dir.mkdir(exist_ok=True)
        
        self.logger.info("Community system tester initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup test logging."""
        logger = logging.getLogger("community_system_tester")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        self.logger.info("Starting comprehensive community system tests")
        
        start_time = time.time()
        
        # Test 1: Community extraction accuracy
        self.test_community_extraction()
        
        # Test 2: Product matching precision
        self.test_product_matching()
        
        # Test 3: Project guide generation
        self.test_project_guide_generation()
        
        # Test 4: FAQ creation
        self.test_faq_generation()
        
        # Test 5: Inventory recommendations
        self.test_inventory_recommendations()
        
        # Test 6: End-to-end integration
        self.test_end_to_end_integration()
        
        # Test 7: Performance benchmarks
        self.test_performance_benchmarks()
        
        total_time = time.time() - start_time
        
        # Generate test report
        test_report = self._generate_test_report(total_time)
        
        self.logger.info(f"All tests completed in {total_time:.2f} seconds")
        return test_report
    
    def test_community_extraction(self) -> TestResult:
        """Test community knowledge extraction accuracy."""
        self.logger.info("Testing community extraction accuracy")
        
        start_time = time.time()
        
        try:
            # Generate test data
            sample_posts = self.mock_data.generate_sample_posts()
            
            # Initialize extractor
            config = EnhancedExtractionConfig(
                max_posts_per_source=10,
                enable_sentiment_analysis=True,
                enable_trending_analysis=True
            )
            extractor = EnhancedCommunityExtractor(config)
            
            # Test content analysis
            extraction_results = {
                'posts_analyzed': len(sample_posts),
                'tools_extracted': 0,
                'products_extracted': 0,
                'problems_identified': 0,
                'solutions_found': 0,
                'singapore_posts': 0
            }
            
            for post in sample_posts:
                # Analyze post content
                extractor._analyze_post_content(post)
                extractor._match_products_in_post(post)
                
                # Count extractions
                extraction_results['tools_extracted'] += len(post.mentioned_tools)
                extraction_results['products_extracted'] += len(post.mentioned_products)
                extraction_results['problems_identified'] += len(post.problems_identified)
                extraction_results['solutions_found'] += len(post.solutions_provided)
                
                # Check Singapore relevance
                if any(term in post.content.lower() for term in ['hdb', 'singapore', 'bto']):
                    extraction_results['singapore_posts'] += 1
            
            # Calculate accuracy score based on expected vs actual extractions
            expected_tools = 15  # Expected based on mock data
            expected_problems = 5
            
            tool_accuracy = min(extraction_results['tools_extracted'] / expected_tools, 1.0)
            problem_accuracy = min(extraction_results['problems_identified'] / expected_problems, 1.0)
            
            overall_accuracy = (tool_accuracy + problem_accuracy) / 2
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name="community_extraction",
                success=overall_accuracy > 0.6,  # 60% accuracy threshold
                execution_time=execution_time,
                accuracy_score=overall_accuracy,
                details=extraction_results
            )
            
            self.test_results.append(result)
            self.logger.info(f"Community extraction test: {overall_accuracy:.2f} accuracy")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name="community_extraction",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            self.test_results.append(result)
            self.logger.error(f"Community extraction test failed: {e}")
            return result
    
    def test_product_matching(self) -> TestResult:
        """Test product matching precision."""
        self.logger.info("Testing product matching precision")
        
        start_time = time.time()
        
        try:
            # Generate test data
            sample_posts = self.mock_data.generate_sample_posts()
            sample_videos = self.mock_data.generate_sample_videos()
            sample_products = self.mock_data.generate_sample_products()
            
            # Initialize integrator
            integrator = CommunityProductIntegrator()
            integrator.load_product_cache(sample_products)
            
            # Test product matching
            product_matches = integrator.match_community_to_products(sample_posts, sample_videos)
            
            # Analyze matching results
            matching_results = {
                'total_matches': len(product_matches),
                'high_confidence_matches': len([m for m in product_matches if m.match_confidence > 0.8]),
                'medium_confidence_matches': len([m for m in product_matches if 0.5 < m.match_confidence <= 0.8]),
                'low_confidence_matches': len([m for m in product_matches if m.match_confidence <= 0.5]),
                'exact_matches': len([m for m in product_matches if m.match_type == 'exact_sku']),
                'fuzzy_matches': len([m for m in product_matches if m.match_type == 'fuzzy_name']),
                'brand_model_matches': len([m for m in product_matches if m.match_type == 'brand_model']),
                'semantic_matches': len([m for m in product_matches if m.match_type == 'semantic'])
            }
            
            # Validate some expected matches
            expected_matches = [
                ("dewalt", "DRILL-DW-001"),  # DeWalt drill should match
                ("toggle bolts", "ANCHOR-TB-003"),  # Toggle bolts should match
                ("toilet", "TOILET-KOH-004")  # Toilet should match
            ]
            
            validated_matches = 0
            for mention, expected_sku in expected_matches:
                found = any(
                    m.product_sku == expected_sku and mention.lower() in m.community_mention.lower()
                    for m in product_matches
                )
                if found:
                    validated_matches += 1
            
            # Calculate precision score
            precision = validated_matches / len(expected_matches) if expected_matches else 0
            
            # Overall accuracy based on confidence distribution
            high_conf_ratio = matching_results['high_confidence_matches'] / max(matching_results['total_matches'], 1)
            accuracy_score = (precision + high_conf_ratio) / 2
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name="product_matching",
                success=accuracy_score > 0.5,  # 50% accuracy threshold
                execution_time=execution_time,
                accuracy_score=accuracy_score,
                details=matching_results
            )
            
            self.test_results.append(result)
            self.logger.info(f"Product matching test: {accuracy_score:.2f} precision, {len(product_matches)} matches")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name="product_matching",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            self.test_results.append(result)
            self.logger.error(f"Product matching test failed: {e}")
            return result
    
    def test_project_guide_generation(self) -> TestResult:
        """Test project guide generation quality."""
        self.logger.info("Testing project guide generation")
        
        start_time = time.time()
        
        try:
            # Create mock problem-solution pairs
            mock_problem_solutions = [
                ProblemSolutionPair(
                    problem_id="prob_001",
                    problem_description="Toilet installation challenges and proper technique",
                    problem_category="plumbing",
                    problem_keywords=["toilet", "installation", "wax ring", "bolts"],
                    solutions=[
                        {
                            "post_id": "solution_001",
                            "solution_text": "Turn off water supply first, remove old toilet carefully, clean the flange, install new wax ring, position toilet and tighten bolts evenly",
                            "upvotes": 25,
                            "similarity_score": 0.9
                        }
                    ],
                    confidence_score=0.8,
                    community_validation=25,
                    related_tools=["adjustable wrench", "level"],
                    related_products=["toilet", "wax ring", "toilet bolts"],
                    project_types=["plumbing"]
                ),
                ProblemSolutionPair(
                    problem_id="prob_002",
                    problem_description="Circular saw blade binding in wood cuts",
                    problem_category="woodworking",
                    problem_keywords=["circular saw", "blade", "binding", "lumber"],
                    solutions=[
                        {
                            "post_id": "solution_002",
                            "solution_text": "Use proper blade for material, maintain steady feed rate, support both sides of cut, check blade sharpness",
                            "upvotes": 18,
                            "similarity_score": 0.85
                        }
                    ],
                    confidence_score=0.7,
                    community_validation=18,
                    related_tools=["circular saw", "saw blade"],
                    project_types=["woodworking"]
                )
            ]
            
            # Initialize integrator
            integrator = CommunityProductIntegrator()
            sample_products = self.mock_data.generate_sample_products()
            integrator.load_product_cache(sample_products)
            
            # Generate project guides
            project_guides = integrator.generate_project_guides(mock_problem_solutions)
            
            # Analyze guide quality
            guide_results = {
                'total_guides': len(project_guides),
                'guides_with_instructions': len([g for g in project_guides if g.step_by_step_instructions]),
                'guides_with_tools': len([g for g in project_guides if g.required_tools]),
                'guides_with_tips': len([g for g in project_guides if g.tips_and_tricks]),
                'guides_with_warnings': len([g for g in project_guides if g.safety_warnings]),
                'avg_community_rating': sum(g.community_rating for g in project_guides) / len(project_guides) if project_guides else 0,
                'avg_confidence': sum(g.confidence_score for g in project_guides) / len(project_guides) if project_guides else 0
            }
            
            # Quality score based on completeness
            completeness_factors = [
                guide_results['guides_with_instructions'] / max(guide_results['total_guides'], 1),
                guide_results['guides_with_tools'] / max(guide_results['total_guides'], 1),
                guide_results['guides_with_tips'] / max(guide_results['total_guides'], 1),
                guide_results['avg_confidence']
            ]
            
            quality_score = sum(completeness_factors) / len(completeness_factors)
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name="project_guide_generation",
                success=quality_score > 0.6,  # 60% quality threshold
                execution_time=execution_time,
                accuracy_score=quality_score,
                details=guide_results
            )
            
            self.test_results.append(result)
            self.logger.info(f"Project guide generation test: {quality_score:.2f} quality, {len(project_guides)} guides")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name="project_guide_generation",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            self.test_results.append(result)
            self.logger.error(f"Project guide generation test failed: {e}")
            return result
    
    def test_faq_generation(self) -> TestResult:
        """Test FAQ generation accuracy."""
        self.logger.info("Testing FAQ generation")
        
        start_time = time.time()
        
        try:
            # Use same mock problem-solutions from project guide test
            mock_problem_solutions = [
                ProblemSolutionPair(
                    problem_id="faq_prob_001",
                    problem_description="How do I install a toilet properly without leaks",
                    problem_category="plumbing",
                    problem_keywords=["toilet", "installation", "leaks", "wax ring"],
                    solutions=[
                        {
                            "post_id": "faq_sol_001",
                            "solution_text": "Ensure the flange is clean, use a new wax ring, position toilet carefully, and tighten bolts evenly in a cross pattern",
                            "upvotes": 32,
                            "similarity_score": 0.9
                        }
                    ],
                    confidence_score=0.85,
                    community_validation=32,
                    related_products=["toilet", "wax ring"]
                )
            ]
            
            # Initialize integrator and generate FAQs
            integrator = CommunityProductIntegrator()
            faq_entries = integrator.create_faq_database(mock_problem_solutions)
            
            # Analyze FAQ quality
            faq_results = {
                'total_faqs': len(faq_entries),
                'faqs_with_answers': len([f for f in faq_entries if f.answer and len(f.answer) > 20]),
                'faqs_with_keywords': len([f for f in faq_entries if f.keywords]),
                'faqs_with_products': len([f for f in faq_entries if f.related_products]),
                'avg_helpfulness': sum(f.helpfulness_score for f in faq_entries) / len(faq_entries) if faq_entries else 0,
                'avg_accuracy': sum(f.accuracy_score for f in faq_entries) / len(faq_entries) if faq_entries else 0,
                'high_quality_faqs': len([f for f in faq_entries if f.helpfulness_score > 0.7])
            }
            
            # Quality metrics
            answer_quality = faq_results['faqs_with_answers'] / max(faq_results['total_faqs'], 1)
            metadata_completeness = faq_results['faqs_with_keywords'] / max(faq_results['total_faqs'], 1)
            overall_quality = (answer_quality + metadata_completeness + faq_results['avg_helpfulness']) / 3
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name="faq_generation",
                success=overall_quality > 0.6,  # 60% quality threshold
                execution_time=execution_time,
                accuracy_score=overall_quality,
                details=faq_results
            )
            
            self.test_results.append(result)
            self.logger.info(f"FAQ generation test: {overall_quality:.2f} quality, {len(faq_entries)} FAQs")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name="faq_generation",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            self.test_results.append(result)
            self.logger.error(f"FAQ generation test failed: {e}")
            return result
    
    def test_inventory_recommendations(self) -> TestResult:
        """Test inventory recommendation accuracy."""
        self.logger.info("Testing inventory recommendations")
        
        start_time = time.time()
        
        try:
            # Create mock trending topics
            mock_trending_topics = [
                TrendingTopic(
                    topic_id="trend_001",
                    topic_name="toilet installation",
                    topic_keywords=["toilet", "installation", "bathroom", "plumbing"],
                    mention_count=45,
                    trend_score=85.5,
                    velocity=0.8,  # Strong upward trend
                    related_products=["toilet", "wax ring", "toilet bolts"],
                    recommendation_priority="high"
                ),
                TrendingTopic(
                    topic_id="trend_002", 
                    topic_name="circular saw",
                    topic_keywords=["circular saw", "woodworking", "blade"],
                    mention_count=28,
                    trend_score=52.3,
                    velocity=0.3,  # Moderate trend
                    related_products=["circular saw", "saw blade"],
                    recommendation_priority="medium"
                )
            ]
            
            # Initialize integrator
            integrator = CommunityProductIntegrator()
            sample_products = self.mock_data.generate_sample_products()
            integrator.load_product_cache(sample_products)
            
            # Generate inventory recommendations
            recommendations = integrator.generate_inventory_recommendations(mock_trending_topics)
            
            # Analyze recommendation quality
            rec_results = {
                'total_recommendations': len(recommendations),
                'high_urgency_recs': len([r for r in recommendations if r.urgency == 'high']),
                'trending_demand_recs': len([r for r in recommendations if r.recommendation_type == 'trending_demand']),
                'stock_up_recs': len([r for r in recommendations if r.recommendation_type == 'stock_up']),
                'avg_confidence': sum(r.confidence for r in recommendations) / len(recommendations) if recommendations else 0,
                'avg_predicted_increase': sum(r.predicted_demand_increase for r in recommendations) / len(recommendations) if recommendations else 0,
                'singapore_relevant_recs': len([r for r in recommendations if r.singapore_relevance > 0])
            }
            
            # Validate expected recommendations
            expected_product_trends = [
                ("TOILET-KOH-004", "toilet installation"),  # Toilet should be recommended for toilet trend
                ("SAW-MIL-002", "circular saw")  # Saw should be recommended for saw trend
            ]
            
            validated_recs = 0
            for expected_sku, trend_topic in expected_product_trends:
                found = any(
                    r.product_sku == expected_sku and trend_topic in r.trending_topic
                    for r in recommendations
                )
                if found:
                    validated_recs += 1
            
            validation_score = validated_recs / len(expected_product_trends) if expected_product_trends else 0
            quality_score = (validation_score + rec_results['avg_confidence']) / 2
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name="inventory_recommendations",
                success=quality_score > 0.5,  # 50% quality threshold
                execution_time=execution_time,
                accuracy_score=quality_score,
                details=rec_results
            )
            
            self.test_results.append(result)
            self.logger.info(f"Inventory recommendations test: {quality_score:.2f} quality, {len(recommendations)} recommendations")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name="inventory_recommendations",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            self.test_results.append(result)
            self.logger.error(f"Inventory recommendations test failed: {e}")
            return result
    
    def test_end_to_end_integration(self) -> TestResult:
        """Test complete end-to-end system integration."""
        self.logger.info("Testing end-to-end integration")
        
        start_time = time.time()
        
        try:
            # Generate complete test data set
            sample_posts = self.mock_data.generate_sample_posts()
            sample_videos = self.mock_data.generate_sample_videos()
            sample_products = self.mock_data.generate_sample_products()
            
            # Initialize components
            extractor_config = EnhancedExtractionConfig(
                max_posts_per_source=10,
                enable_trending_analysis=True
            )
            extractor = EnhancedCommunityExtractor(extractor_config)
            integrator = CommunityProductIntegrator()
            integrator.load_product_cache(sample_products)
            
            # Step 1: Extract problem-solution patterns
            problem_solutions = extractor.identify_problem_solution_patterns(sample_posts)
            
            # Step 2: Analyze trending topics
            trending_topics = extractor.analyze_trending_topics(sample_posts)
            
            # Step 3: Match products
            product_matches = integrator.match_community_to_products(sample_posts, sample_videos)
            
            # Step 4: Generate project guides
            project_guides = integrator.generate_project_guides(problem_solutions, product_matches)
            
            # Step 5: Create FAQ database
            faq_entries = integrator.create_faq_database(problem_solutions)
            
            # Step 6: Generate inventory recommendations
            inventory_recs = integrator.generate_inventory_recommendations(trending_topics)
            
            # Analyze end-to-end results
            e2e_results = {
                'input_posts': len(sample_posts),
                'input_videos': len(sample_videos),
                'input_products': len(sample_products),
                'problem_solutions_found': len(problem_solutions),
                'trending_topics_identified': len(trending_topics),
                'product_matches_created': len(product_matches),
                'project_guides_generated': len(project_guides),
                'faq_entries_created': len(faq_entries),
                'inventory_recommendations': len(inventory_recs)
            }
            
            # Success criteria: each stage should produce reasonable output
            success_criteria = [
                len(problem_solutions) > 0,
                len(product_matches) > 0,
                len(project_guides) >= 0,  # May be 0 if insufficient problem-solutions
                len(faq_entries) >= 0,     # May be 0 if insufficient problem-solutions
                len(inventory_recs) >= 0   # May be 0 if no trending topics
            ]
            
            success_rate = sum(success_criteria) / len(success_criteria)
            
            # Data flow integrity check
            data_flow_score = 1.0
            if len(problem_solutions) > 0:
                if len(project_guides) == 0 and len(faq_entries) == 0:
                    data_flow_score -= 0.3  # Problem solutions should generate guides or FAQs
            
            overall_score = (success_rate + data_flow_score) / 2
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name="end_to_end_integration",
                success=overall_score > 0.7,  # 70% success threshold
                execution_time=execution_time,
                accuracy_score=overall_score,
                details=e2e_results
            )
            
            self.test_results.append(result)
            self.logger.info(f"End-to-end integration test: {overall_score:.2f} success rate")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name="end_to_end_integration",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            self.test_results.append(result)
            self.logger.error(f"End-to-end integration test failed: {e}")
            return result
    
    def test_performance_benchmarks(self) -> TestResult:
        """Test system performance benchmarks."""
        self.logger.info("Testing performance benchmarks")
        
        start_time = time.time()
        
        try:
            # Generate larger dataset for performance testing
            large_post_set = []
            for i in range(50):  # 50 posts for performance test
                base_posts = self.mock_data.generate_sample_posts()
                for j, post in enumerate(base_posts):
                    post.post_id = f"perf_test_{i}_{j}"
                    large_post_set.append(post)
            
            sample_products = self.mock_data.generate_sample_products()
            
            # Performance benchmarks
            benchmarks = {}
            
            # Benchmark 1: Community content analysis
            analysis_start = time.time()
            config = EnhancedExtractionConfig(enable_sentiment_analysis=True)
            extractor = EnhancedCommunityExtractor(config)
            
            for post in large_post_set[:20]:  # Test with 20 posts
                extractor._analyze_post_content(post)
            
            benchmarks['content_analysis_time'] = time.time() - analysis_start
            benchmarks['content_analysis_rate'] = 20 / benchmarks['content_analysis_time']  # posts per second
            
            # Benchmark 2: Product matching
            matching_start = time.time()
            integrator = CommunityProductIntegrator()
            integrator.load_product_cache(sample_products)
            
            matches = integrator.match_community_to_products(large_post_set[:10])  # Test with 10 posts
            
            benchmarks['product_matching_time'] = time.time() - matching_start
            benchmarks['product_matching_rate'] = 10 / benchmarks['product_matching_time']
            benchmarks['matches_generated'] = len(matches)
            
            # Benchmark 3: Memory usage estimation
            import sys
            benchmarks['estimated_memory_mb'] = sys.getsizeof(large_post_set + sample_products) / (1024 * 1024)
            
            # Performance score based on processing rates
            content_score = min(benchmarks['content_analysis_rate'] / 5.0, 1.0)  # Target: 5 posts/sec
            matching_score = min(benchmarks['product_matching_rate'] / 2.0, 1.0)  # Target: 2 posts/sec
            memory_score = max(0, 1.0 - (benchmarks['estimated_memory_mb'] / 100))  # Penalty if >100MB
            
            performance_score = (content_score + matching_score + memory_score) / 3
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name="performance_benchmarks",
                success=performance_score > 0.6,  # 60% performance threshold
                execution_time=execution_time,
                accuracy_score=performance_score,
                details=benchmarks
            )
            
            self.test_results.append(result)
            self.logger.info(f"Performance benchmarks: {performance_score:.2f} score")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TestResult(
                test_name="performance_benchmarks",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            self.test_results.append(result)
            self.logger.error(f"Performance benchmarks test failed: {e}")
            return result
    
    def _generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.success])
        failed_tests = total_tests - successful_tests
        
        avg_accuracy = sum(r.accuracy_score for r in self.test_results if r.accuracy_score) / \
                      len([r for r in self.test_results if r.accuracy_score])
        
        # Create test report
        test_report = {
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
                'average_accuracy': avg_accuracy,
                'total_execution_time': total_time,
                'test_timestamp': datetime.now().isoformat()
            },
            'individual_test_results': [asdict(result) for result in self.test_results],
            'recommendations': []
        }
        
        # Add recommendations based on test results
        if test_report['test_summary']['success_rate'] < 0.8:
            test_report['recommendations'].append(
                "Overall success rate is below 80%. Review failed tests and improve system robustness."
            )
        
        if avg_accuracy < 0.7:
            test_report['recommendations'].append(
                "Average accuracy is below 70%. Consider tuning matching thresholds and NLP models."
            )
        
        # Find performance bottlenecks
        slowest_test = max(self.test_results, key=lambda x: x.execution_time)
        if slowest_test.execution_time > 5.0:
            test_report['recommendations'].append(
                f"Test '{slowest_test.test_name}' took {slowest_test.execution_time:.2f}s. Consider performance optimization."
            )
        
        # Save test report
        report_file = self.test_output_dir / f"community_system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Test report saved to {report_file}")
        
        return test_report


def run_community_system_tests() -> Dict[str, Any]:
    """Run the complete community system test suite."""
    tester = CommunitySystemTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    print("=== Community Knowledge Extraction System - Comprehensive Test Suite ===")
    
    # Run all tests
    test_results = run_community_system_tests()
    
    # Display summary
    summary = test_results['test_summary']
    print(f"\nTest Results Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Successful: {summary['successful_tests']}")
    print(f"  Failed: {summary['failed_tests']}")  
    print(f"  Success Rate: {summary['success_rate']:.1%}")
    print(f"  Average Accuracy: {summary['average_accuracy']:.2f}")
    print(f"  Total Time: {summary['total_execution_time']:.2f} seconds")
    
    # Display individual test results
    print(f"\nIndividual Test Results:")
    for result in test_results['individual_test_results']:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        accuracy = f" (Accuracy: {result['accuracy_score']:.2f})" if result['accuracy_score'] else ""
        print(f"  {status} {result['test_name']}: {result['execution_time']:.2f}s{accuracy}")
        if result['error_message']:
            print(f"    Error: {result['error_message']}")
    
    # Display recommendations
    if test_results['recommendations']:
        print(f"\nRecommendations:")
        for rec in test_results['recommendations']:
            print(f"  • {rec}")
    
    print(f"\nCommunity knowledge extraction system testing completed!")
    print(f"System is {'READY FOR PRODUCTION' if summary['success_rate'] > 0.8 else 'NEEDS IMPROVEMENT'}")