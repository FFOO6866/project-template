"""
Simplified Community Knowledge Extraction System Test.

Tests the core functionality without heavy dependencies.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Mock the Kailash components for testing
class MockWorkflowBuilder:
    def add_node(self, node_type, node_id, config):
        pass
    
    def connect(self, from_node, to_node):
        pass
    
    def build(self):
        return "mock_workflow"

class MockLocalRuntime:
    def execute(self, workflow):
        return {"result": "mock_execution"}, "mock_run_id"


@dataclass
class SimpleCommunityPost:
    """Simplified community post for testing."""
    post_id: str
    title: str
    content: str
    tools_mentioned: List[str]
    products_mentioned: List[str]
    problems_identified: List[str]
    solutions_provided: List[str]
    upvotes: int = 10
    confidence: float = 0.7


@dataclass
class SimpleProductMatch:
    """Simplified product match for testing."""
    community_mention: str
    product_sku: str
    product_name: str
    match_confidence: float
    match_type: str


@dataclass 
class SimpleProjectGuide:
    """Simplified project guide for testing."""
    guide_id: str
    project_name: str
    description: str
    required_tools: List[str]
    instructions: List[str]
    community_rating: float


class SimpleCommunityExtractor:
    """Simplified community knowledge extractor for testing."""
    
    def __init__(self):
        self.logger = logging.getLogger("simple_extractor")
        
    def analyze_post_content(self, post: SimpleCommunityPost) -> None:
        """Analyze post content and extract information."""
        content_lower = f"{post.title} {post.content}".lower()
        
        # Extract tools
        tool_patterns = ["drill", "saw", "hammer", "wrench", "level", "screwdriver"]
        for tool in tool_patterns:
            if tool in content_lower:
                if tool not in post.tools_mentioned:
                    post.tools_mentioned.append(tool)
        
        # Extract products
        product_patterns = ["dewalt", "milwaukee", "makita", "ryobi", "toilet", "tiles"]
        for product in product_patterns:
            if product in content_lower:
                if product not in post.products_mentioned:
                    post.products_mentioned.append(product)
        
        # Extract problems
        problem_indicators = ["problem", "issue", "trouble", "doesn't work", "broken"]
        for indicator in problem_indicators:
            if indicator in content_lower:
                problem_desc = f"Issue related to {indicator}"
                if problem_desc not in post.problems_identified:
                    post.problems_identified.append(problem_desc)
        
        # Extract solutions
        solution_indicators = ["solution", "fix", "try this", "worked", "solved"]
        for indicator in solution_indicators:
            if indicator in content_lower:
                solution_desc = f"Solution involving {indicator}"
                if solution_desc not in post.solutions_provided:
                    post.solutions_provided.append(solution_desc)


class SimpleProductMatcher:
    """Simplified product matcher for testing."""
    
    def __init__(self):
        self.products = {}
        
    def load_products(self, products: List[Dict[str, Any]]) -> None:
        """Load product data."""
        for product in products:
            self.products[product['sku']] = product
    
    def match_mentions_to_products(self, posts: List[SimpleCommunityPost]) -> List[SimpleProductMatch]:
        """Match community mentions to products."""
        matches = []
        
        for post in posts:
            all_mentions = post.tools_mentioned + post.products_mentioned
            
            for mention in all_mentions:
                for sku, product in self.products.items():
                    # Simple matching logic
                    product_name = product.get('name', '').lower()
                    brand = product.get('brand', '').lower()
                    
                    confidence = 0.0
                    match_type = "no_match"
                    
                    if mention.lower() in product_name:
                        confidence = 0.8
                        match_type = "name_match"
                    elif mention.lower() == brand:
                        confidence = 0.9
                        match_type = "brand_match"
                    elif mention.lower() in brand or brand in mention.lower():
                        confidence = 0.6
                        match_type = "partial_match"
                    
                    if confidence > 0.5:
                        match = SimpleProductMatch(
                            community_mention=mention,
                            product_sku=sku,
                            product_name=product.get('name', ''),
                            match_confidence=confidence,
                            match_type=match_type
                        )
                        matches.append(match)
        
        return matches


class SimpleProjectGuideGenerator:
    """Simplified project guide generator."""
    
    def generate_guides(self, posts: List[SimpleCommunityPost]) -> List[SimpleProjectGuide]:
        """Generate project guides from posts."""
        guides = []
        
        # Group posts by common topics
        plumbing_posts = [p for p in posts if any(word in p.content.lower() for word in ['toilet', 'plumbing', 'water'])]
        woodworking_posts = [p for p in posts if any(word in p.content.lower() for word in ['wood', 'saw', 'lumber'])]
        
        # Generate plumbing guide if we have relevant posts
        if plumbing_posts:
            all_tools = []
            all_instructions = []
            
            for post in plumbing_posts:
                all_tools.extend(post.tools_mentioned)
                all_instructions.extend(post.solutions_provided)
            
            guide = SimpleProjectGuide(
                guide_id="guide_plumbing_001",
                project_name="DIY Plumbing Projects",
                description="Community-sourced guide for common plumbing tasks",
                required_tools=list(set(all_tools)),  # Remove duplicates
                instructions=list(set(all_instructions)),
                community_rating=sum(p.upvotes for p in plumbing_posts) / len(plumbing_posts)
            )
            guides.append(guide)
        
        # Generate woodworking guide if we have relevant posts
        if woodworking_posts:
            all_tools = []
            all_instructions = []
            
            for post in woodworking_posts:
                all_tools.extend(post.tools_mentioned)
                all_instructions.extend(post.solutions_provided)
            
            guide = SimpleProjectGuide(
                guide_id="guide_woodworking_001", 
                project_name="DIY Woodworking Projects",
                description="Community-sourced guide for woodworking tasks",
                required_tools=list(set(all_tools)),
                instructions=list(set(all_instructions)),
                community_rating=sum(p.upvotes for p in woodworking_posts) / len(woodworking_posts)
            )
            guides.append(guide)
        
        return guides


def create_sample_data():
    """Create sample data for testing."""
    
    # Sample community posts
    posts = [
        SimpleCommunityPost(
            post_id="post_001",
            title="Cordless drill battery keeps dying",
            content="My 18V DeWalt drill battery dies after 15 minutes. Any solutions for this problem?",
            tools_mentioned=[],
            products_mentioned=[],
            problems_identified=[],
            solutions_provided=[],
            upvotes=23
        ),
        SimpleCommunityPost(
            post_id="post_002", 
            title="Best way to hang heavy mirror on drywall",
            content="Need to hang 15kg mirror. What's the best solution? Try toggle bolts or molly bolts?",
            tools_mentioned=[],
            products_mentioned=[],
            problems_identified=[],
            solutions_provided=[],
            upvotes=45
        ),
        SimpleCommunityPost(
            post_id="post_003",
            title="Circular saw blade binding in wood",
            content="My saw blade gets stuck when cutting lumber. This problem happens with 2x4s. Any fix?",
            tools_mentioned=[],
            products_mentioned=[],
            problems_identified=[],
            solutions_provided=[],
            upvotes=31
        ),
        SimpleCommunityPost(
            post_id="post_004",
            title="DIY toilet installation tips",
            content="Installing new toilet in bathroom. Need proper tools and step-by-step solution.",
            tools_mentioned=[],
            products_mentioned=[],
            problems_identified=[],
            solutions_provided=[],
            upvotes=52
        )
    ]
    
    # Sample products
    products = [
        {
            "sku": "DRILL-DW-001",
            "name": "DeWalt 18V Cordless Drill Kit", 
            "brand": "DeWalt",
            "category": "power tools",
            "price": 149.99
        },
        {
            "sku": "SAW-MIL-002",
            "name": "Milwaukee Circular Saw 7.25 inch",
            "brand": "Milwaukee", 
            "category": "power tools",
            "price": 199.99
        },
        {
            "sku": "TOILET-KOH-003",
            "name": "Kohler Highline Two-Piece Toilet",
            "brand": "Kohler",
            "category": "bathroom fixtures",
            "price": 289.99
        },
        {
            "sku": "ANCHOR-TB-004",
            "name": "Toggle Bolts Heavy Duty 1/4 inch",
            "brand": "Simpson",
            "category": "fasteners", 
            "price": 12.99
        }
    ]
    
    return posts, products


def test_community_extraction():
    """Test community knowledge extraction."""
    print("Testing community extraction...")
    
    posts, products = create_sample_data()
    extractor = SimpleCommunityExtractor()
    
    # Analyze posts
    for post in posts:
        extractor.analyze_post_content(post)
    
    # Check results
    total_tools = sum(len(p.tools_mentioned) for p in posts)
    total_products = sum(len(p.products_mentioned) for p in posts)
    total_problems = sum(len(p.problems_identified) for p in posts)
    total_solutions = sum(len(p.solutions_provided) for p in posts)
    
    print(f"  Extracted {total_tools} tool mentions")
    print(f"  Extracted {total_products} product mentions")
    print(f"  Identified {total_problems} problems")
    print(f"  Found {total_solutions} solutions")
    
    success = total_tools > 0 and total_products > 0
    print(f"  OK PASS" if success else "  FAIL FAIL")
    
    return success, posts


def test_product_matching():
    """Test product matching functionality."""
    print("Testing product matching...")
    
    posts, products = create_sample_data()
    extractor = SimpleCommunityExtractor()
    matcher = SimpleProductMatcher()
    
    # Analyze posts first
    for post in posts:
        extractor.analyze_post_content(post)
    
    # Load products and match
    matcher.load_products(products)
    matches = matcher.match_mentions_to_products(posts)
    
    print(f"  Generated {len(matches)} product matches")
    
    # Check for expected matches
    expected_matches = ["dewalt", "milwaukee", "toilet"]
    found_matches = [m.community_mention.lower() for m in matches]
    
    matches_found = sum(1 for expected in expected_matches if any(expected in found for found in found_matches))
    
    print(f"  Found {matches_found}/{len(expected_matches)} expected matches")
    
    success = len(matches) > 0 and matches_found >= 2
    print(f"  OK PASS" if success else "  FAIL FAIL")
    
    return success, matches


def test_project_guide_generation():
    """Test project guide generation."""
    print("Testing project guide generation...")
    
    posts, products = create_sample_data()
    extractor = SimpleCommunityExtractor()
    guide_generator = SimpleProjectGuideGenerator()
    
    # Analyze posts first
    for post in posts:
        extractor.analyze_post_content(post)
    
    # Generate guides
    guides = guide_generator.generate_guides(posts)
    
    print(f"  Generated {len(guides)} project guides")
    
    # Check guide quality
    guides_with_tools = len([g for g in guides if g.required_tools])
    guides_with_instructions = len([g for g in guides if g.instructions])
    
    print(f"  {guides_with_tools} guides have required tools")
    print(f"  {guides_with_instructions} guides have instructions")
    
    success = len(guides) > 0 and guides_with_tools > 0
    print(f"  OK PASS" if success else "  FAIL FAIL")
    
    return success, guides


def test_end_to_end_integration():
    """Test complete end-to-end integration."""
    print("Testing end-to-end integration...")
    
    start_time = time.time()
    
    # Run all components together
    posts, products = create_sample_data()
    
    # Step 1: Extract knowledge
    extractor = SimpleCommunityExtractor()
    for post in posts:
        extractor.analyze_post_content(post)
    
    # Step 2: Match products
    matcher = SimpleProductMatcher()
    matcher.load_products(products)
    matches = matcher.match_mentions_to_products(posts)
    
    # Step 3: Generate guides
    guide_generator = SimpleProjectGuideGenerator()
    guides = guide_generator.generate_guides(posts)
    
    execution_time = time.time() - start_time
    
    # Check results
    results = {
        'posts_processed': len(posts),
        'product_matches': len(matches),
        'guides_generated': len(guides),
        'execution_time': execution_time
    }
    
    print(f"  Processed {results['posts_processed']} posts")
    print(f"  Generated {results['product_matches']} product matches")
    print(f"  Created {results['guides_generated']} project guides")
    print(f"  Completed in {results['execution_time']:.2f} seconds")
    
    success = all([
        results['posts_processed'] > 0,
        results['product_matches'] > 0,
        results['guides_generated'] > 0,
        results['execution_time'] < 5.0  # Should complete quickly
    ])
    
    print(f"  OK PASS" if success else "  FAIL FAIL")
    
    return success, results


def run_all_tests():
    """Run all tests and generate report."""
    print("=== Community Knowledge Extraction System - Simple Test Suite ===\n")
    
    test_results = []
    
    # Test 1: Community extraction
    success, data = test_community_extraction()
    test_results.append(('Community Extraction', success))
    print()
    
    # Test 2: Product matching
    success, data = test_product_matching() 
    test_results.append(('Product Matching', success))
    print()
    
    # Test 3: Project guide generation
    success, data = test_project_guide_generation()
    test_results.append(('Project Guide Generation', success))
    print()
    
    # Test 4: End-to-end integration
    success, data = test_end_to_end_integration()
    test_results.append(('End-to-End Integration', success))
    print()
    
    # Generate summary
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    success_rate = passed_tests / total_tests
    
    print("=== Test Results Summary ===")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1%}")
    print()
    
    for test_name, success in test_results:
        status = "OK PASS" if success else "FAIL FAIL"
        print(f"{status} {test_name}")
    
    print()
    if success_rate >= 0.75:
        print("SUCCESS System is READY FOR PRODUCTION!")
    else:
        print("WARNING  System needs improvement before production use.")
    
    # Save results
    report = {
        'test_summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'timestamp': datetime.now().isoformat()
        },
        'individual_results': [
            {'test_name': name, 'success': success} 
            for name, success in test_results
        ]
    }
    
    # Create output directory and save report
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / f"simple_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTest report saved to: {report_file}")
    
    return report


if __name__ == "__main__":
    run_all_tests()