"""
Pricing Engine Workflow for RFP Analysis

Handles dynamic pricing calculations with business rules, volume discounts, 
and margin controls using Kailash SDK workflows.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

logger = logging.getLogger(__name__)

class PricingEngineWorkflow:
    """Workflow for calculating pricing with business rules and volume discounts."""
    
    def __init__(self, pricing_config: Optional[Dict[str, Any]] = None):
        self.workflow_builder = WorkflowBuilder()
        self.runtime = LocalRuntime()
        self.pricing_config = pricing_config or self._get_default_pricing_config()
    
    def _get_default_pricing_config(self) -> Dict[str, Any]:
        """Get default pricing configuration with business rules."""
        return {
            'category_rules': {
                'Power Tools': {
                    'base_markup': 0.30,      # 30% markup
                    'volume_discount': 0.15,  # Up to 15% volume discount
                    'minimum_margin': 0.20,   # Minimum 20% margin
                    'cost_factor': 0.70       # Assume cost is 70% of base price
                },
                'Safety Equipment': {
                    'base_markup': 0.25,
                    'volume_discount': 0.12,
                    'minimum_margin': 0.18,
                    'cost_factor': 0.75
                },
                'Lighting': {
                    'base_markup': 0.25,
                    'volume_discount': 0.10,
                    'minimum_margin': 0.15,
                    'cost_factor': 0.75
                },
                'Security': {
                    'base_markup': 0.30,
                    'volume_discount': 0.12,
                    'minimum_margin': 0.20,
                    'cost_factor': 0.70
                },
                'Networking': {
                    'base_markup': 0.20,
                    'volume_discount': 0.08,
                    'minimum_margin': 0.12,
                    'cost_factor': 0.80
                },
                'Power': {
                    'base_markup': 0.22,
                    'volume_discount': 0.09,
                    'minimum_margin': 0.15,
                    'cost_factor': 0.78
                },
                'Electronics': {
                    'base_markup': 0.35,
                    'volume_discount': 0.15,
                    'minimum_margin': 0.25,
                    'cost_factor': 0.65
                },
                'Hardware': {
                    'base_markup': 0.18,
                    'volume_discount': 0.05,
                    'minimum_margin': 0.10,
                    'cost_factor': 0.82
                },
                'Accessories': {
                    'base_markup': 0.40,
                    'volume_discount': 0.20,
                    'minimum_margin': 0.25,
                    'cost_factor': 0.60
                },
                'General': {
                    'base_markup': 0.25,
                    'volume_discount': 0.10,
                    'minimum_margin': 0.15,
                    'cost_factor': 0.75
                }
            },
            'volume_thresholds': [
                {'min_quantity': 100, 'discount_factor': 1.0},
                {'min_quantity': 50, 'discount_factor': 0.7},
                {'min_quantity': 20, 'discount_factor': 0.4},
                {'min_quantity': 10, 'discount_factor': 0.2},
                {'min_quantity': 1, 'discount_factor': 0.0}
            ],
            'brand_multipliers': {
                'DEWALT': 1.1,      # Premium brand 10% increase
                'MILWAUKEE': 1.1,
                '3M': 1.05,         # 5% premium
                'MAKITA': 1.05,
                'BOSCH': 1.05,
                'FLUKE': 1.15,      # High-end 15% premium
                'CommScope': 1.0,   # Standard pricing
                'Hikvision': 0.95,  # Competitive pricing
                'Generic': 0.90     # 10% discount for generic
            },
            'market_conditions': {
                'inflation_factor': 1.03,    # 3% inflation adjustment
                'supply_chain_factor': 1.02, # 2% supply chain surcharge
                'competition_factor': 0.98   # 2% competitive discount
            },
            'customer_tiers': {
                'enterprise': {'discount': 0.05, 'payment_terms': 30},
                'government': {'discount': 0.08, 'payment_terms': 45},
                'standard': {'discount': 0.0, 'payment_terms': 30},
                'new': {'discount': -0.02, 'payment_terms': 15}  # New customer surcharge
            }
        }
    
    def create_base_pricing_workflow(self) -> Any:
        """Create workflow for base price calculations."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "calculate_base_pricing", {
            "code": """
from typing import Dict, List, Any
import json

def get_pricing_rules(category: str, pricing_config: Dict) -> Dict:
    '''Get pricing rules for category'''
    return pricing_config.get('category_rules', {}).get(category, pricing_config['category_rules']['General'])

def calculate_base_price_with_markup(base_price: float, category: str, 
                                   brand: str, pricing_config: Dict) -> Dict:
    '''Calculate base price with markup and brand adjustments'''
    
    # Get category rules
    rules = get_pricing_rules(category, pricing_config)
    
    # Apply brand multiplier
    brand_multiplier = pricing_config.get('brand_multipliers', {}).get(brand, 1.0)
    adjusted_base = base_price * brand_multiplier
    
    # Apply market conditions
    market_conditions = pricing_config.get('market_conditions', {})
    market_factor = (
        market_conditions.get('inflation_factor', 1.0) *
        market_conditions.get('supply_chain_factor', 1.0) *
        market_conditions.get('competition_factor', 1.0)
    )
    market_adjusted_price = adjusted_base * market_factor
    
    # Apply base markup
    marked_up_price = market_adjusted_price * (1 + rules['base_markup'])
    
    return {
        'original_base_price': base_price,
        'brand_adjusted_price': adjusted_base,
        'market_adjusted_price': market_adjusted_price,
        'marked_up_price': marked_up_price,
        'brand_multiplier': brand_multiplier,
        'market_factor': market_factor,
        'markup_percentage': rules['base_markup'] * 100,
        'category_rules': rules
    }

# Process pricing for matched products
pricing_results = {}

if 'matches' in locals() and matches:
    for req_key, product_matches in matches.items():
        if product_matches:
            # Get the best match (first one)
            best_match = product_matches[0]
            
            # Calculate base pricing
            base_pricing = calculate_base_price_with_markup(
                base_price=best_match.get('unit_price', 0.0),
                category=best_match.get('category', 'General'),
                brand=best_match.get('brand', 'Generic'),
                pricing_config=pricing_config if 'pricing_config' in locals() else {}
            )
            
            pricing_results[req_key] = {
                'product_id': best_match.get('product_id'),
                'product_name': best_match.get('product_name'),
                'base_pricing': base_pricing
            }

result = {
    'pricing_results': pricing_results,
    'processed_count': len(pricing_results)
}
"""
        })
        
        return workflow.build()
    
    def create_volume_discount_workflow(self) -> Any:
        """Create workflow for volume discount calculations."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "calculate_volume_discounts", {
            "code": """
from typing import Dict, List, Any

def calculate_volume_discount(quantity: int, category: str, pricing_config: Dict) -> Dict:
    '''Calculate volume discount based on quantity and category'''
    
    # Get category rules
    category_rules = pricing_config.get('category_rules', {}).get(category, 
                     pricing_config.get('category_rules', {}).get('General', {}))
    
    max_volume_discount = category_rules.get('volume_discount', 0.10)
    
    # Get volume thresholds
    volume_thresholds = pricing_config.get('volume_thresholds', [
        {'min_quantity': 100, 'discount_factor': 1.0},
        {'min_quantity': 50, 'discount_factor': 0.7},
        {'min_quantity': 20, 'discount_factor': 0.4},
        {'min_quantity': 10, 'discount_factor': 0.2},
        {'min_quantity': 1, 'discount_factor': 0.0}
    ])
    
    # Find applicable discount tier
    discount_factor = 0.0
    applicable_tier = None
    
    for tier in volume_thresholds:
        if quantity >= tier['min_quantity']:
            discount_factor = tier['discount_factor']
            applicable_tier = tier
            break
    
    # Calculate actual discount
    volume_discount_rate = max_volume_discount * discount_factor
    
    return {
        'quantity': quantity,
        'applicable_tier': applicable_tier,
        'max_volume_discount': max_volume_discount,
        'discount_factor': discount_factor,
        'volume_discount_rate': volume_discount_rate,
        'volume_discount_percentage': volume_discount_rate * 100
    }

# Apply volume discounts to pricing results
volume_pricing_results = {}

if 'requirements' in locals() and 'pricing_results' in locals():
    # Create requirement lookup for quantities
    req_quantities = {}
    for req in requirements:
        req_key = f"{req['category']}_{hash(req['description']) % 10000}"
        req_quantities[req_key] = {
            'quantity': req.get('quantity', 1),
            'category': req.get('category', 'General')
        }
    
    for req_key, pricing_data in pricing_results.items():
        if req_key in req_quantities:
            req_info = req_quantities[req_key]
            
            # Calculate volume discount
            volume_discount = calculate_volume_discount(
                quantity=req_info['quantity'],
                category=req_info['category'],
                pricing_config=pricing_config if 'pricing_config' in locals() else {}
            )
            
            # Apply volume discount to marked up price
            base_pricing = pricing_data['base_pricing']
            marked_up_price = base_pricing['marked_up_price']
            
            # Calculate discounted price
            discount_amount = marked_up_price * volume_discount['volume_discount_rate']
            discounted_unit_price = marked_up_price - discount_amount
            
            # Ensure minimum margin
            category_rules = base_pricing['category_rules']
            minimum_price = base_pricing['original_base_price'] * (1 + category_rules.get('minimum_margin', 0.15))
            final_unit_price = max(discounted_unit_price, minimum_price)
            
            # Calculate total
            total_price = final_unit_price * req_info['quantity']
            total_discount = (marked_up_price - final_unit_price) * req_info['quantity']
            
            volume_pricing_results[req_key] = {
                **pricing_data,
                'volume_discount': volume_discount,
                'discounted_unit_price': discounted_unit_price,
                'final_unit_price': round(final_unit_price, 2),
                'total_price': round(total_price, 2),
                'total_discount_amount': round(total_discount, 2),
                'quantity': req_info['quantity'],
                'margin_protected': final_unit_price > discounted_unit_price
            }

result = {
    'volume_pricing_results': volume_pricing_results,
    'processed_count': len(volume_pricing_results)
}
"""
        })
        
        return workflow.build()
    
    def create_customer_tier_workflow(self) -> Any:
        """Create workflow for customer tier pricing adjustments."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "apply_customer_tier_pricing", {
            "code": """
from typing import Dict, List, Any

def apply_customer_tier_adjustment(pricing_data: Dict, customer_tier: str, 
                                 pricing_config: Dict) -> Dict:
    '''Apply customer tier adjustments to pricing'''
    
    customer_tiers = pricing_config.get('customer_tiers', {})
    tier_config = customer_tiers.get(customer_tier, customer_tiers.get('standard', {}))
    
    tier_discount = tier_config.get('discount', 0.0)
    payment_terms = tier_config.get('payment_terms', 30)
    
    # Apply tier discount
    base_price = pricing_data['final_unit_price']
    tier_adjustment = base_price * tier_discount
    tier_adjusted_price = base_price - tier_adjustment
    
    # Recalculate total
    quantity = pricing_data['quantity']
    tier_total_price = tier_adjusted_price * quantity
    
    return {
        **pricing_data,
        'customer_tier': customer_tier,
        'tier_discount_rate': tier_discount,
        'tier_adjustment_amount': round(tier_adjustment, 2),
        'tier_adjusted_unit_price': round(tier_adjusted_price, 2),
        'tier_adjusted_total_price': round(tier_total_price, 2),
        'payment_terms': payment_terms
    }

# Apply customer tier pricing
customer_tier = customer_tier if 'customer_tier' in locals() else 'standard'
final_pricing_results = {}

if 'volume_pricing_results' in locals():
    for req_key, volume_pricing in volume_pricing_results.items():
        final_pricing = apply_customer_tier_adjustment(
            volume_pricing,
            customer_tier,
            pricing_config if 'pricing_config' in locals() else {}
        )
        final_pricing_results[req_key] = final_pricing

# Calculate totals
subtotal = sum(pricing['tier_adjusted_total_price'] for pricing in final_pricing_results.values())
total_discount = sum(pricing.get('total_discount_amount', 0) + 
                    (pricing.get('tier_adjustment_amount', 0) * pricing.get('quantity', 1))
                    for pricing in final_pricing_results.values())

result = {
    'final_pricing_results': final_pricing_results,
    'pricing_summary': {
        'subtotal': round(subtotal, 2),
        'total_discount': round(total_discount, 2),
        'item_count': len(final_pricing_results),
        'customer_tier': customer_tier
    }
}
"""
        })
        
        return workflow.build()
    
    def create_complete_pricing_workflow(self) -> Any:
        """Create complete pricing workflow with all calculations."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "complete_pricing_calculation", {
            "code": """
from typing import Dict, List, Any
import json

def get_default_pricing_config():
    return {
        'category_rules': {
            'Power Tools': {
                'base_markup': 0.30,
                'volume_discount': 0.15,
                'minimum_margin': 0.20,
                'cost_factor': 0.70
            },
            'Safety Equipment': {
                'base_markup': 0.25,
                'volume_discount': 0.12,
                'minimum_margin': 0.18,
                'cost_factor': 0.75
            },
            'Lighting': {
                'base_markup': 0.25,
                'volume_discount': 0.10,
                'minimum_margin': 0.15,
                'cost_factor': 0.75
            },
            'Security': {
                'base_markup': 0.30,
                'volume_discount': 0.12,
                'minimum_margin': 0.20,
                'cost_factor': 0.70
            },
            'Networking': {
                'base_markup': 0.20,
                'volume_discount': 0.08,
                'minimum_margin': 0.12,
                'cost_factor': 0.80
            },
            'General': {
                'base_markup': 0.25,
                'volume_discount': 0.10,
                'minimum_margin': 0.15,
                'cost_factor': 0.75
            }
        },
        'volume_thresholds': [
            {'min_quantity': 100, 'discount_factor': 1.0},
            {'min_quantity': 50, 'discount_factor': 0.7},
            {'min_quantity': 20, 'discount_factor': 0.4},
            {'min_quantity': 10, 'discount_factor': 0.2},
            {'min_quantity': 1, 'discount_factor': 0.0}
        ],
        'brand_multipliers': {
            'DEWALT': 1.1,
            'MILWAUKEE': 1.1,
            '3M': 1.05,
            'MAKITA': 1.05,
            'BOSCH': 1.05,
            'FLUKE': 1.15,
            'CommScope': 1.0,
            'Hikvision': 0.95,
            'Generic': 0.90
        },
        'market_conditions': {
            'inflation_factor': 1.03,
            'supply_chain_factor': 1.02,
            'competition_factor': 0.98
        },
        'customer_tiers': {
            'enterprise': {'discount': 0.05, 'payment_terms': 30},
            'government': {'discount': 0.08, 'payment_terms': 45},
            'standard': {'discount': 0.0, 'payment_terms': 30},
            'new': {'discount': -0.02, 'payment_terms': 15}
        }
    }

def calculate_comprehensive_pricing(requirements: List[Dict], matches: Dict, 
                                  customer_tier: str = 'standard') -> Dict:
    '''Calculate comprehensive pricing for all requirements'''
    
    pricing_config = get_default_pricing_config()
    final_pricing_results = {}
    
    # Create requirement lookup
    req_lookup = {}
    for req in requirements:
        req_key = f"{req['category']}_{hash(req['description']) % 10000}"
        req_lookup[req_key] = req
    
    for req_key, product_matches in matches.items():
        if not product_matches or req_key not in req_lookup:
            continue
            
        # Get best match and requirement
        best_match = product_matches[0]
        requirement = req_lookup[req_key]
        
        # Get pricing rules
        category = best_match.get('category', 'General')
        brand = best_match.get('brand', 'Generic')
        quantity = requirement.get('quantity', 1)
        base_price = best_match.get('unit_price', 0.0)
        
        category_rules = pricing_config['category_rules'].get(category, 
                         pricing_config['category_rules']['General'])
        
        # Step 1: Brand and market adjustments
        brand_multiplier = pricing_config['brand_multipliers'].get(brand, 1.0)
        market_conditions = pricing_config['market_conditions']
        market_factor = (
            market_conditions['inflation_factor'] *
            market_conditions['supply_chain_factor'] *
            market_conditions['competition_factor']
        )
        
        adjusted_base = base_price * brand_multiplier * market_factor
        
        # Step 2: Apply base markup
        marked_up_price = adjusted_base * (1 + category_rules['base_markup'])
        
        # Step 3: Volume discount
        volume_thresholds = pricing_config['volume_thresholds']
        discount_factor = 0.0
        
        for tier in volume_thresholds:
            if quantity >= tier['min_quantity']:
                discount_factor = tier['discount_factor']
                break
        
        volume_discount_rate = category_rules['volume_discount'] * discount_factor
        volume_discount_amount = marked_up_price * volume_discount_rate
        discounted_price = marked_up_price - volume_discount_amount
        
        # Step 4: Minimum margin protection
        minimum_price = base_price * (1 + category_rules['minimum_margin'])
        protected_price = max(discounted_price, minimum_price)
        
        # Step 5: Customer tier adjustment
        tier_config = pricing_config['customer_tiers'].get(customer_tier, 
                      pricing_config['customer_tiers']['standard'])
        tier_discount = tier_config['discount']
        tier_adjustment = protected_price * tier_discount
        final_unit_price = protected_price - tier_adjustment
        
        # Calculate totals
        total_price = final_unit_price * quantity
        
        # Calculate savings breakdown
        savings_breakdown = {
            'volume_discount': volume_discount_amount * quantity,
            'tier_discount': tier_adjustment * quantity,
            'total_savings': (marked_up_price - final_unit_price) * quantity
        }
        
        final_pricing_results[req_key] = {
            'product_id': best_match.get('product_id'),
            'product_name': best_match.get('product_name'),
            'category': category,
            'brand': brand,
            'quantity': quantity,
            'original_base_price': base_price,
            'brand_multiplier': brand_multiplier,
            'market_factor': market_factor,
            'adjusted_base_price': round(adjusted_base, 2),
            'markup_percentage': category_rules['base_markup'] * 100,
            'marked_up_price': round(marked_up_price, 2),
            'volume_discount_rate': volume_discount_rate,
            'volume_discount_amount': round(volume_discount_amount, 2),
            'discounted_price': round(discounted_price, 2),
            'minimum_margin_protected': protected_price > discounted_price,
            'tier_discount_rate': tier_discount,
            'tier_adjustment': round(tier_adjustment, 2),
            'final_unit_price': round(final_unit_price, 2),
            'total_price': round(total_price, 2),
            'savings_breakdown': {k: round(v, 2) for k, v in savings_breakdown.items()},
            'customer_tier': customer_tier,
            'payment_terms': tier_config['payment_terms']
        }
    
    # Calculate overall totals
    subtotal = sum(p['total_price'] for p in final_pricing_results.values())
    total_savings = sum(p['savings_breakdown']['total_savings'] 
                       for p in final_pricing_results.values())
    
    return {
        'pricing_results': final_pricing_results,
        'pricing_summary': {
            'subtotal': round(subtotal, 2),
            'total_savings': round(total_savings, 2),
            'item_count': len(final_pricing_results),
            'customer_tier': customer_tier,
            'average_discount_rate': (total_savings / (subtotal + total_savings) * 100) if (subtotal + total_savings) > 0 else 0
        },
        'success': True
    }

# Execute comprehensive pricing calculation
if 'requirements' in locals() and 'matches' in locals():
    pricing_result = calculate_comprehensive_pricing(
        requirements,
        matches,
        customer_tier if 'customer_tier' in locals() else 'standard'
    )
    result = pricing_result
else:
    result = {
        'pricing_results': {},
        'pricing_summary': {'subtotal': 0, 'total_savings': 0, 'item_count': 0},
        'error': 'Missing requirements or matches data',
        'success': False
    }
"""
        })
        
        return workflow.build()
    
    def execute_pricing_calculation(self, requirements: List[Dict[str, Any]], 
                                   matches: Dict[str, List[Dict[str, Any]]],
                                   customer_tier: str = 'standard') -> Dict[str, Any]:
        """Execute the complete pricing calculation workflow."""
        try:
            workflow = self.create_complete_pricing_workflow()
            
            # Prepare parameters
            params = {
                'requirements': requirements,
                'matches': matches,
                'customer_tier': customer_tier,
                'pricing_config': self.pricing_config
            }
            
            # Execute workflow
            results, run_id = self.runtime.execute(workflow, parameters=params)
            
            return {
                'success': True,
                'results': results,
                'run_id': run_id
            }
            
        except Exception as e:
            logger.error(f"Pricing calculation workflow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': None,
                'run_id': None
            }

# Example usage and testing
if __name__ == "__main__":
    # Test with sample data
    sample_requirements = [
        {
            'category': 'Power Tools',
            'description': 'DEWALT DCD791D2 20V cordless drill',
            'quantity': 50,
            'keywords': ['dewalt', 'dcd791d2', '20v', 'cordless', 'drill'],
            'brand': 'DEWALT',
            'model': 'DCD791D2'
        },
        {
            'category': 'Safety Equipment',
            'description': '3M H-700 Series safety helmets',
            'quantity': 100,
            'keywords': ['3m', 'h-700', 'safety', 'helmet'],
            'brand': '3M',
            'model': 'H-700'
        }
    ]
    
    sample_matches = {
        'Power Tools_1234': [{
            'product_id': 'DWT-001',
            'product_name': 'DEWALT DCD791D2 20V MAX XR Cordless Drill',
            'unit_price': 179.99,
            'category': 'Power Tools',
            'brand': 'DEWALT',
            'model': 'DCD791D2'
        }],
        'Safety Equipment_5678': [{
            'product_id': '3M-001',
            'product_name': '3M H-700 Series Hard Hat',
            'unit_price': 24.99,
            'category': 'Safety Equipment',
            'brand': '3M',
            'model': 'H-700'
        }]
    }
    
    pricing_engine = PricingEngineWorkflow()
    result = pricing_engine.execute_pricing_calculation(
        sample_requirements, 
        sample_matches, 
        customer_tier='enterprise'
    )
    
    if result['success']:
        pricing_summary = result['results']['pricing_summary']
        print("Pricing Calculation Results:")
        print(f"- Items: {pricing_summary['item_count']}")
        print(f"- Subtotal: ${pricing_summary['subtotal']:.2f}")
        print(f"- Total Savings: ${pricing_summary['total_savings']:.2f}")
        print(f"- Average Discount: {pricing_summary.get('average_discount_rate', 0):.1f}%")
        
        print("\\nDetailed Pricing:")
        for req_key, pricing in result['results']['pricing_results'].items():
            print(f"  * {pricing['product_name']}: ${pricing['final_unit_price']:.2f} x {pricing['quantity']} = ${pricing['total_price']:.2f}")
    else:
        print(f"Pricing calculation failed: {result['error']}")