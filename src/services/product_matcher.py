"""
Product Matching Service
Matches RFP requirements to real products in database using semantic search
NO MOCK DATA - All matches from real product database
"""

import logging
from typing import Dict, Any, List, Optional
import asyncpg

logger = logging.getLogger(__name__)


class ProductMatcher:
    """Matches requirements to products using database search"""

    def __init__(self):
        pass

    async def match_products(
        self,
        requirements: Dict[str, Any],
        db_pool: asyncpg.Pool
    ) -> List[Dict[str, Any]]:
        """
        Match requirement items to products in database

        Args:
            requirements: Extracted requirements from document
            db_pool: Database connection pool

        Returns:
            List of matched products with pricing and quantities
        """
        logger.info("Starting product matching")

        items = requirements.get('items', [])
        if not items:
            logger.warning("No items to match")
            return []

        matched_products = []

        for idx, item in enumerate(items):
            try:
                matches = await self._find_product_matches(item, db_pool)

                if matches:
                    # Take best match
                    best_match = matches[0]

                    matched_product = {
                        'line_number': idx + 1,
                        'requirement_description': item.get('description', ''),
                        'quantity': item.get('quantity', 1),
                        'unit': item.get('unit', 'pieces'),
                        'product_id': best_match['id'],
                        'product_name': best_match['name'],
                        'product_code': best_match.get('product_code', 'N/A'),
                        'unit_price': float(best_match.get('price', 0)),
                        'currency': best_match.get('currency', 'SGD'),
                        'supplier': best_match.get('supplier', 'Horme'),
                        'match_confidence': best_match.get('confidence', 0.8),
                        'stock_quantity': best_match.get('stock_quantity', 0),  # Add stock quantity
                        'specifications': item.get('specifications', []),
                        'alternatives': matches[1:3] if len(matches) > 1 else []  # Include 2 alternatives
                    }

                    # Calculate line total
                    matched_product['line_total'] = (
                        matched_product['quantity'] * matched_product['unit_price']
                    )

                    matched_products.append(matched_product)
                    logger.info(f"Matched item {idx + 1}: {item.get('description')} → {best_match['name']}")

                else:
                    logger.warning(f"No match found for item: {item.get('description')}")

                    # Add unmatched item for manual review
                    matched_products.append({
                        'line_number': idx + 1,
                        'requirement_description': item.get('description', ''),
                        'quantity': item.get('quantity', 1),
                        'unit': item.get('unit', 'pieces'),
                        'product_id': None,
                        'product_name': 'MANUAL REVIEW REQUIRED',
                        'unit_price': 0,
                        'line_total': 0,
                        'match_confidence': 0,
                        'needs_review': True
                    })

            except Exception as e:
                logger.error(f"Error matching item {idx + 1}: {str(e)}")
                continue

        logger.info(f"Matched {len(matched_products)} products")

        return matched_products

    async def _find_product_matches(
        self,
        requirement_item: Dict[str, Any],
        db_pool: asyncpg.Pool
    ) -> List[Dict[str, Any]]:
        """
        Find matching products in database

        Uses keyword matching on product name, description, and category
        Returns top matches ordered by relevance
        """
        description = requirement_item.get('description', '').lower()
        category = requirement_item.get('category', '').lower()

        # Extract search keywords
        keywords = self._extract_keywords(description)

        if not keywords:
            return []

        logger.info(f"Searching for products with keywords: {keywords}")

        async with db_pool.acquire() as conn:
            # Search products by keywords in name and description
            # Using PostgreSQL full-text search or simple ILIKE for now
            search_query = """
                SELECT
                    id,
                    name,
                    product_code,
                    description,
                    category,
                    price,
                    currency,
                    supplier,
                    stock_quantity,
                    (
                        CASE
                            WHEN LOWER(name) LIKE $1 THEN 1.0
                            WHEN LOWER(description) LIKE $1 THEN 0.8
                            WHEN LOWER(category) LIKE $2 THEN 0.6
                            ELSE 0.4
                        END
                    ) as confidence
                FROM products
                WHERE
                    LOWER(name) LIKE $1
                    OR LOWER(description) LIKE $1
                    OR LOWER(category) LIKE $2
                ORDER BY confidence DESC, price ASC
                LIMIT 5
            """

            # Create LIKE patterns
            name_pattern = f"%{keywords[0]}%"
            category_pattern = f"%{category}%" if category else f"%{keywords[0]}%"

            rows = await conn.fetch(search_query, name_pattern, category_pattern)

            matches = []
            for row in rows:
                matches.append({
                    'id': row['id'],
                    'name': row['name'],
                    'product_code': row['product_code'],
                    'description': row['description'],
                    'category': row['category'],
                    'price': row['price'],
                    'currency': row['currency'],
                    'supplier': row['supplier'],
                    'stock_quantity': row['stock_quantity'],
                    'confidence': float(row['confidence'])
                })

            return matches

    def _extract_keywords(self, description: str) -> List[str]:
        """Extract meaningful keywords from description"""

        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}

        words = description.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords[:3]  # Return top 3 keywords

    async def calculate_pricing(
        self,
        matched_products: List[Dict[str, Any]],
        discount_rate: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculate total pricing with optional discount

        Args:
            matched_products: List of matched products with quantities
            discount_rate: Discount percentage (0.0 to 1.0)

        Returns:
            Pricing summary with subtotal, discount, tax, and total
        """

        subtotal = sum(p['line_total'] for p in matched_products)

        discount_amount = subtotal * discount_rate
        subtotal_after_discount = subtotal - discount_amount

        # Calculate tax (9% GST for Singapore)
        tax_rate = 0.09
        tax_amount = subtotal_after_discount * tax_rate

        total = subtotal_after_discount + tax_amount

        pricing = {
            'subtotal': round(subtotal, 2),
            'discount_rate': discount_rate,
            'discount_amount': round(discount_amount, 2),
            'subtotal_after_discount': round(subtotal_after_discount, 2),
            'tax_rate': tax_rate,
            'tax_amount': round(tax_amount, 2),
            'total': round(total, 2),
            'currency': 'SGD',
            'item_count': len(matched_products)
        }

        logger.info(f"Calculated pricing: Total {pricing['currency']} {pricing['total']}")

        return pricing
