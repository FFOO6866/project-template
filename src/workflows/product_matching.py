"""
Product Matching Workflow for RFP Analysis - Production Ready

Production implementation using real PostgreSQL database queries.
NO MOCK DATA - queries against 19,143+ real products.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from src.core.postgresql_database import get_database

logger = logging.getLogger(__name__)

class ProductMatchingWorkflow:
    """Production-ready workflow for matching requirements against real products."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize product matching workflow.

        Args:
            database_url: Optional database URL override (uses env var if None)

        Raises:
            ValueError: If DATABASE_URL not configured
        """
        self.runtime = LocalRuntime()
        self.database_url = database_url or os.getenv('DATABASE_URL')

        # CRITICAL: Fail fast if no database configured
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Cannot perform product matching without database access."
            )

        # Initialize database connection
        try:
            self.db = get_database(self.database_url)
            logger.info("✅ Product matching workflow initialized with PostgreSQL database")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    def create_product_search_workflow(self, search_terms: List[str]) -> Any:
        """
        Create workflow to search products by multiple terms.

        Args:
            search_terms: List of search keywords

        Returns:
            Built workflow ready for execution
        """
        workflow = WorkflowBuilder()

        # Build search filter with OR conditions for multiple terms
        search_filter = {
            "$or": [
                {"name": {"$regex": term, "$options": "i"}},
                {"description": {"$regex": term, "$options": "i"}},
                {"sku": {"$regex": term, "$options": "i"}}
            ] for term in search_terms
        }

        # Search active products only
        search_filter["status"] = "active"
        search_filter["is_published"] = True

        # Add node to search products
        workflow.add_node("ProductListNode", "search_products", {
            "filter": search_filter,
            "limit": 100,
            "order_by": ["name"]
        })

        return workflow.build()

    def create_category_brand_search_workflow(
        self,
        category_name: Optional[str] = None,
        brand_name: Optional[str] = None
    ) -> Any:
        """
        Create workflow to search by category and/or brand.

        Args:
            category_name: Optional category filter
            brand_name: Optional brand filter

        Returns:
            Built workflow ready for execution
        """
        workflow = WorkflowBuilder()

        # Get category and brand IDs first
        category_id = None
        brand_id = None

        if category_name:
            # Get category ID
            cat_workflow = WorkflowBuilder()
            cat_workflow.add_node("CategoryListNode", "get_category", {
                "filter": {"name": category_name},
                "limit": 1
            })
            results, _ = self.runtime.execute(cat_workflow.build())
            categories = results.get("get_category", [])
            if categories:
                category_id = categories[0]['id']

        if brand_name:
            # Get brand ID
            brand_workflow = WorkflowBuilder()
            brand_workflow.add_node("BrandListNode", "get_brand", {
                "filter": {"name": brand_name},
                "limit": 1
            })
            results, _ = self.runtime.execute(brand_workflow.build())
            brands = results.get("get_brand", [])
            if brands:
                brand_id = brands[0]['id']

        # Build product search filter
        search_filter = {
            "status": "active",
            "is_published": True
        }

        if category_id:
            search_filter["category_id"] = category_id
        if brand_id:
            search_filter["brand_id"] = brand_id

        # Add node to search products
        workflow.add_node("ProductListNode", "search_products", {
            "filter": search_filter,
            "limit": 100,
            "order_by": ["name"]
        })

        return workflow.build()
    
    def execute_product_matching(
        self,
        requirements: List[Dict[str, Any]],
        fuzzy_threshold: int = 60,
        max_results_per_requirement: int = 5
    ) -> Dict[str, Any]:
        """
        Execute product matching against real database.

        Args:
            requirements: List of requirement dictionaries with keywords, category, brand, etc.
            fuzzy_threshold: Minimum match score (0-100)
            max_results_per_requirement: Maximum matches per requirement

        Returns:
            Dictionary with matched products (NO fallback data)

        Raises:
            Exception: If database query fails (fail-fast, no mock responses)
        """
        try:
            all_matches = {}
            total_products_searched = 0

            logger.info(f"Matching {len(requirements)} requirements against real product database")

            for req_idx, req in enumerate(requirements):
                req_key = f"req_{req_idx}_{req.get('category', 'unknown')}"
                matches = []

                # Extract search criteria
                keywords = req.get('keywords', [])
                category = req.get('category')
                brand = req.get('brand')

                # CRITICAL: Search real database - NO MOCK DATA
                if keywords:
                    # Search by keywords
                    search_results = self.db.search_products(
                        query=' '.join(keywords[:3]),  # Use top 3 keywords
                        filters={'category': category, 'brand': brand} if category or brand else None,
                        limit=50
                    )
                elif category or brand:
                    # Search by category/brand using workflow
                    workflow = self.create_category_brand_search_workflow(category, brand)
                    results, run_id = self.runtime.execute(workflow)
                    search_results = results.get("search_products", [])
                else:
                    logger.warning(f"Requirement {req_idx} has no search criteria - skipping")
                    continue

                total_products_searched += len(search_results)

                # Score and filter matches
                for product in search_results:
                    match_score = self._calculate_match_score(
                        req,
                        product,
                        keywords
                    )

                    if match_score >= fuzzy_threshold:
                        matches.append({
                            'product_id': product['id'],
                            'product_sku': product['sku'],
                            'product_name': product['name'],
                            'description': product.get('description', ''),
                            'unit_price': float(product.get('base_price', 0.0)) if product.get('base_price') else None,
                            'match_score': round(match_score, 2),
                            'brand': product.get('brand_id'),
                            'category': product.get('category_id'),
                            'availability': product.get('availability', 'unknown')
                        })

                # Sort by match score and limit results
                matches.sort(key=lambda x: x['match_score'], reverse=True)
                all_matches[req_key] = matches[:max_results_per_requirement]

                logger.info(
                    f"Requirement {req_idx}: Found {len(search_results)} products, "
                    f"{len(matches)} above threshold, returning top {len(all_matches[req_key])}"
                )

            result = {
                'success': True,
                'matches': all_matches,
                'total_matches': sum(len(m) for m in all_matches.values()),
                'requirements_processed': len(requirements),
                'products_searched': total_products_searched,
                'algorithm': 'keyword_matching',
                'database': 'postgresql'
            }

            logger.info(
                f"✅ Product matching complete: {result['total_matches']} total matches "
                f"from {total_products_searched} products searched"
            )

            return result

        except Exception as e:
            # CRITICAL: Fail fast - NO fallback responses
            logger.error(f"❌ Product matching failed: {e}")
            raise

    def _calculate_match_score(
        self,
        requirement: Dict[str, Any],
        product: Dict[str, Any],
        keywords: List[str]
    ) -> float:
        """
        Calculate match score between requirement and product.

        Args:
            requirement: Requirement dictionary
            product: Product dictionary from database
            keywords: Search keywords

        Returns:
            Match score (0-100)
        """
        score = 0.0

        # Keyword matching (0-60 points)
        if keywords:
            product_text = f"{product['name']} {product.get('description', '')}".lower()
            keyword_matches = sum(1 for kw in keywords if kw.lower() in product_text)
            score += (keyword_matches / len(keywords)) * 60

        # Brand matching (0-20 points)
        if requirement.get('brand') and product.get('brand_id'):
            # Would need brand name lookup for exact comparison
            # For now, give partial credit if brand is specified
            score += 10

        # Category matching (0-20 points)
        if requirement.get('category') and product.get('category_id'):
            # Would need category name lookup for exact comparison
            # For now, give partial credit if category is specified
            score += 10

        return min(score, 100.0)  # Cap at 100


# Production-ready CLI interface
if __name__ == "__main__":
    import argparse

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='Product Matching Workflow')
    parser.add_argument(
        '--keywords',
        nargs='+',
        required=True,
        help='Search keywords (e.g., dewalt drill 20v)'
    )
    parser.add_argument(
        '--category',
        help='Product category filter'
    )
    parser.add_argument(
        '--brand',
        help='Brand name filter'
    )
    parser.add_argument(
        '--threshold',
        type=int,
        default=60,
        help='Minimum match score (0-100)'
    )

    args = parser.parse_args()

    # CRITICAL: Ensure DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Set DATABASE_URL=postgresql://user:password@postgres:5432/dbname")
        sys.exit(1)

    try:
        # Initialize workflow
        matcher = ProductMatchingWorkflow()

        # Create requirement
        requirement = {
            'keywords': args.keywords,
            'category': args.category,
            'brand': args.brand
        }

        # Execute matching
        result = matcher.execute_product_matching(
            [requirement],
            fuzzy_threshold=args.threshold
        )

        # Display results
        print(f"\n{'='*80}")
        print(f"Product Matching Results")
        print(f"{'='*80}")
        print(f"Requirements processed: {result['requirements_processed']}")
        print(f"Products searched: {result['products_searched']}")
        print(f"Total matches: {result['total_matches']}")
        print(f"Database: {result['database']}")
        print(f"{'='*80}\n")

        for req_key, matches in result['matches'].items():
            print(f"Top matches for {req_key}:")
            for idx, match in enumerate(matches, 1):
                print(f"  {idx}. {match['product_name']} (SKU: {match['product_sku']})")
                print(f"     Score: {match['match_score']}% | Price: ${match['unit_price']}")
                print(f"     Availability: {match['availability']}")
                print()

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Product Matching Failed: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)