"""
RFP Orchestration Workflow

Master workflow that coordinates all RFP processing components:
- Document Processing
- Product Matching
- Pricing Calculation
- Quotation Generation

Uses Kailash SDK workflow orchestration patterns.
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

# Import component workflows
from .document_processing import DocumentProcessingWorkflow
from .product_matching import ProductMatchingWorkflow
from .pricing_engine import PricingEngineWorkflow
from .quotation_generation import QuotationGenerationWorkflow

logger = logging.getLogger(__name__)

class RFPOrchestrationWorkflow:
    """Master workflow orchestrating complete RFP processing pipeline."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.workflow_builder = WorkflowBuilder()
        self.runtime = LocalRuntime()
        self.config = config or self._get_default_config()
        
        # Initialize component workflows
        self.document_processor = DocumentProcessingWorkflow()
        self.product_matcher = ProductMatchingWorkflow(
            database_url=self.config.get('database_url')
        )
        self.pricing_engine = PricingEngineWorkflow(
            pricing_config=self.config.get('pricing_config')
        )
        self.quotation_generator = QuotationGenerationWorkflow(
            template_config=self.config.get('template_config')
        )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default orchestration configuration."""
        return {
            'processing_settings': {
                'fuzzy_threshold': 60,
                'max_matches_per_requirement': 5,
                'enable_parallel_processing': False,
                'timeout_seconds': 300
            },
            'validation_settings': {
                'require_minimum_matches': True,
                'minimum_match_score': 50,
                'validate_pricing': True,
                'enforce_margin_protection': True
            },
            'output_settings': {
                'generate_pdf': True,
                'generate_html': True,
                'store_in_database': True,
                'include_debug_info': False
            },
            'customer_defaults': {
                'tier': 'standard',
                'payment_terms': 30,
                'tax_rate': 0.10
            }
        }
    
    def create_sequential_workflow(self) -> Any:
        """Create sequential workflow processing all components in order."""
        workflow = WorkflowBuilder()
        
        # Step 1: Document Processing
        workflow.add_node("PythonCodeNode", "process_document", {
            "code": """
# Document processing step
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.workflows.document_processing import DocumentProcessingWorkflow
    
    processor = DocumentProcessingWorkflow()
    
    # Process document based on input type
    if 'file_path' in locals() and file_path:
        doc_result = processor.execute_document_processing(file_path=file_path)
    elif 'text_content' in locals() and text_content:
        doc_result = processor.execute_document_processing(text_content=text_content)
    elif 'rfp_text' in locals() and rfp_text:
        doc_result = processor.execute_document_processing(text_content=rfp_text)
    else:
        doc_result = {
            'success': False,
            'error': 'No input provided (file_path, text_content, or rfp_text)',
            'results': None
        }
    
    if doc_result['success']:
        result = {
            'requirements': doc_result['results']['requirements'],
            'count': doc_result['results']['count'],
            'extracted_text': doc_result['results'].get('extracted_text', ''),
            'success': True,
            'processing_stage': 'document_processing'
        }
    else:
        result = {
            'requirements': [],
            'count': 0,
            'extracted_text': '',
            'success': False,
            'error': doc_result.get('error', 'Document processing failed'),
            'processing_stage': 'document_processing'
        }
        
except ImportError as e:
    result = {
        'requirements': [],
        'count': 0,
        'success': False,
        'error': f'Import error: {str(e)}',
        'processing_stage': 'document_processing'
    }
except Exception as e:
    result = {
        'requirements': [],
        'count': 0,
        'success': False,
        'error': f'Document processing error: {str(e)}',
        'processing_stage': 'document_processing'
    }
"""
        })
        
        # Step 2: Product Matching
        workflow.add_node("PythonCodeNode", "match_products", {
            "code": """
# Product matching step
try:
    from src.workflows.product_matching import ProductMatchingWorkflow
    
    if doc_processing_success and 'requirements' in locals() and requirements:
        matcher = ProductMatchingWorkflow(
            database_url=database_url if 'database_url' in locals() else None
        )
        
        matching_result = matcher.execute_product_matching(
            requirements=requirements,
            fuzzy_threshold=fuzzy_threshold if 'fuzzy_threshold' in locals() else 60
        )
        
        if matching_result['success']:
            result = {
                'matches': matching_result['results']['matches'],
                'total_matches': matching_result['results']['total_matches'],
                'algorithm': matching_result['results'].get('algorithm', 'standard'),
                'success': True,
                'processing_stage': 'product_matching'
            }
        else:
            result = {
                'matches': {},
                'total_matches': 0,
                'success': False,
                'error': matching_result.get('error', 'Product matching failed'),
                'processing_stage': 'product_matching'
            }
    else:
        result = {
            'matches': {},
            'total_matches': 0,
            'success': False,
            'error': 'No requirements from document processing',
            'processing_stage': 'product_matching'
        }
        
except ImportError as e:
    result = {
        'matches': {},
        'total_matches': 0,
        'success': False,
        'error': f'Import error: {str(e)}',
        'processing_stage': 'product_matching'
    }
except Exception as e:
    result = {
        'matches': {},
        'total_matches': 0,
        'success': False,
        'error': f'Product matching error: {str(e)}',
        'processing_stage': 'product_matching'
    }
"""
        })
        
        # Step 3: Pricing Calculation
        workflow.add_node("PythonCodeNode", "calculate_pricing", {
            "code": """
# Pricing calculation step
try:
    from src.workflows.pricing_engine import PricingEngineWorkflow
    
    if (doc_processing_success and matching_success and 
        'requirements' in locals() and 'matches' in locals()):
        
        pricing_engine = PricingEngineWorkflow(
            pricing_config=pricing_config if 'pricing_config' in locals() else None
        )
        
        pricing_result = pricing_engine.execute_pricing_calculation(
            requirements=requirements,
            matches=matches,
            customer_tier=customer_tier if 'customer_tier' in locals() else 'standard'
        )
        
        if pricing_result['success']:
            result = {
                'pricing_results': pricing_result['results']['pricing_results'],
                'pricing_summary': pricing_result['results']['pricing_summary'],
                'success': True,
                'processing_stage': 'pricing_calculation'
            }
        else:
            result = {
                'pricing_results': {},
                'pricing_summary': {},
                'success': False,
                'error': pricing_result.get('error', 'Pricing calculation failed'),
                'processing_stage': 'pricing_calculation'
            }
    else:
        result = {
            'pricing_results': {},
            'pricing_summary': {},
            'success': False,
            'error': 'Prerequisites not met (document processing or product matching failed)',
            'processing_stage': 'pricing_calculation'
        }
        
except ImportError as e:
    result = {
        'pricing_results': {},
        'pricing_summary': {},
        'success': False,
        'error': f'Import error: {str(e)}',
        'processing_stage': 'pricing_calculation'
    }
except Exception as e:
    result = {
        'pricing_results': {},
        'pricing_summary': {},
        'success': False,
        'error': f'Pricing calculation error: {str(e)}',
        'processing_stage': 'pricing_calculation'
    }
"""
        })
        
        # Step 4: Quotation Generation
        workflow.add_node("PythonCodeNode", "generate_quotation", {
            "code": """
# Quotation generation step
try:
    from src.workflows.quotation_generation import QuotationGenerationWorkflow
    
    if (doc_processing_success and matching_success and pricing_success and
        'requirements' in locals() and 'pricing_results' in locals()):
        
        quotation_generator = QuotationGenerationWorkflow(
            template_config=template_config if 'template_config' in locals() else None
        )
        
        quotation_result = quotation_generator.execute_quotation_generation(
            requirements=requirements,
            pricing_results={'pricing_results': pricing_results},
            customer_name=customer_name if 'customer_name' in locals() else 'Valued Customer',
            customer_tier=customer_tier if 'customer_tier' in locals() else 'standard'
        )
        
        if quotation_result['success']:
            result = {
                'quotation': quotation_result['results']['quotation'],
                'html_content': quotation_result['results']['html_content'],
                'quote_number': quotation_result['results']['quote_number'],
                'storage': quotation_result['results']['storage'],
                'success': True,
                'processing_stage': 'quotation_generation'
            }
        else:
            result = {
                'quotation': {},
                'html_content': '',
                'storage': {'success': False},
                'success': False,
                'error': quotation_result.get('error', 'Quotation generation failed'),
                'processing_stage': 'quotation_generation'
            }
    else:
        result = {
            'quotation': {},
            'html_content': '',
            'storage': {'success': False},
            'success': False,
            'error': 'Prerequisites not met (previous stages failed)',
            'processing_stage': 'quotation_generation'
        }
        
except ImportError as e:
    result = {
        'quotation': {},
        'html_content': '',
        'storage': {'success': False},
        'success': False,
        'error': f'Import error: {str(e)}',
        'processing_stage': 'quotation_generation'
    }
except Exception as e:
    result = {
        'quotation': {},
        'html_content': '',
        'storage': {'success': False},
        'success': False,
        'error': f'Quotation generation error: {str(e)}',
        'processing_stage': 'quotation_generation'
    }
"""
        })
        
        # Connect workflow components
        workflow.add_connection("process_document", "success", "match_products", "doc_processing_success")
        workflow.add_connection("process_document", "requirements", "match_products", "requirements")
        
        workflow.add_connection("match_products", "success", "calculate_pricing", "matching_success")
        workflow.add_connection("match_products", "matches", "calculate_pricing", "matches")
        workflow.add_connection("process_document", "requirements", "calculate_pricing", "requirements")
        
        workflow.add_connection("calculate_pricing", "success", "generate_quotation", "pricing_success")
        workflow.add_connection("calculate_pricing", "pricing_results", "generate_quotation", "pricing_results")
        workflow.add_connection("process_document", "requirements", "generate_quotation", "requirements")
        
        return workflow.build()
    
    def create_complete_orchestration_workflow(self) -> Any:
        """Create complete orchestration workflow with integrated processing."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "rfp_complete_processing", {
            "code": """
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def process_rfp_complete(file_path=None, text_content=None, rfp_text=None,
                        customer_name='Valued Customer', customer_tier='standard',
                        fuzzy_threshold=60, database_url=None, pricing_config=None,
                        template_config=None) -> Dict:
    '''Complete RFP processing pipeline'''
    
    processing_log = []
    start_time = datetime.now()
    
    try:
        # Step 1: Document Processing
        processing_log.append({'stage': 'document_processing', 'status': 'started', 'timestamp': datetime.now().isoformat()})
        
        # Determine input
        input_text = None
        if rfp_text:
            input_text = rfp_text
        elif text_content:
            input_text = text_content
        elif file_path:
            # Simple file reading (fallback)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    input_text = f.read()
            except Exception as e:
                processing_log.append({'stage': 'document_processing', 'status': 'failed', 'error': str(e)})
                return {
                    'success': False,
                    'error': f'File reading failed: {str(e)}',
                    'processing_log': processing_log,
                    'stage_failed': 'document_processing'
                }
        
        if not input_text:
            processing_log.append({'stage': 'document_processing', 'status': 'failed', 'error': 'No input provided'})
            return {
                'success': False,
                'error': 'No input provided (file_path, text_content, or rfp_text)',
                'processing_log': processing_log,
                'stage_failed': 'document_processing'
            }
        
        # Parse requirements directly (embedded parser)
        import re
        
        def extract_keywords_from_description(description: str) -> List[str]:
            if not description:
                return []
            words = re.findall(r'\\b[a-zA-Z0-9]+\\b', description.lower())
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            return list(set(keywords))
        
        def infer_category(description: str, keywords: List[str]) -> str:
            category_mappings = {
                'power tools': ['drill', 'saw', 'driver', 'impact', 'grinder', 'sander', 'dewalt', 'makita', 'milwaukee', 'cordless', '20v', '18v'],
                'safety equipment': ['helmet', 'hat', 'hard hat', 'respirator', 'mask', 'safety', 'vest', 'visibility', '3m', 'n95', 'protection'],
                'lighting': ['light', 'led', 'lamp', 'fixture', 'illumination', 'bulb'],
                'security': ['camera', 'sensor', 'security', 'surveillance', 'alarm', 'detector'],
                'networking': ['cable', 'ethernet', 'network', 'switch', 'router', 'wifi', 'cat6', 'cat6a', 'utp', 'rj45'],
                'power': ['power', 'supply', 'battery', 'transformer', 'ups', 'voltage'],
                'electronics': ['circuit', 'board', 'component', 'resistor', 'capacitor', 'ic'],
                'hardware': ['screw', 'bolt', 'mounting', 'bracket', 'enclosure', 'cabinet'],
                'accessories': ['ties', 'zip', 'cable ties', 'assortment', 'pack', 'kit']
            }
            
            description_lower = description.lower()
            for category, category_keywords in category_mappings.items():
                for keyword in category_keywords:
                    if keyword in description_lower or keyword in keywords:
                        return category.title()
            return 'General'
        
        def extract_brand_model_from_description(description: str) -> tuple:
            brand_patterns = {
                r'\\b(DEWALT|DeWalt)\\b': 'DEWALT',
                r'\\b(3M)\\b': '3M',
                r'\\b(MAKITA|Makita)\\b': 'MAKITA',
                r'\\b(MILWAUKEE|Milwaukee)\\b': 'MILWAUKEE',
                r'\\b(BOSCH|Bosch)\\b': 'BOSCH'
            }
            
            brand = None
            model = None
            
            for pattern, brand_name in brand_patterns.items():
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    brand = brand_name
                    brand_pos = match.end()
                    remaining_text = description[brand_pos:].strip()
                    model_match = re.match(r'^\\s*([A-Z0-9-]{3,15})', remaining_text, re.IGNORECASE)
                    if model_match:
                        model = model_match.group(1)
                    break
            
            return brand, model
        
        # Parse requirements from text
        requirements = []
        patterns = [
            r'(\\d+)\\s*(?:units?|pcs?|pieces?)\\s+of\\s+([A-Z][A-Z0-9&]+)\\s+([A-Z0-9-]+)\\s+(.+?)(?:\\n|$|\\.)',
            r'(\\d+)\\s*(?:units?|pcs?|pieces?)\\s+(?:of\\s+)?(.+?)(?:\\n|$)',
            r'(.+?):\\s*(\\d+)\\s*(?:units?|pcs?|pieces?)',
        ]
        
        processed_lines = set()
        lines = input_text.split('\\n')
        
        for line in lines:
            line = line.strip()
            if not line or line in processed_lines:
                continue
            processed_lines.add(line)
            
            for pattern in patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    try:
                        if len(match) == 4:  # Brand/model pattern
                            quantity_str, brand, model, description = match
                            quantity = int(quantity_str)
                            full_description = f"{brand} {model} {description}"
                            req_brand = brand.upper()
                            req_model = model.upper()
                        elif len(match) == 2:
                            quantity_str, description = match
                            try:
                                quantity = int(quantity_str)
                            except ValueError:
                                description, quantity_str = match
                                quantity = int(quantity_str)
                            full_description = description
                            req_brand, req_model = extract_brand_model_from_description(description)
                        else:
                            continue
                        
                        keywords = extract_keywords_from_description(full_description)
                        category = infer_category(full_description, keywords)
                        
                        if req_brand:
                            keywords.append(req_brand.lower())
                        if req_model:
                            keywords.append(req_model.lower())
                        
                        requirement = {
                            'category': category,
                            'description': full_description.strip(),
                            'quantity': quantity,
                            'specifications': {},
                            'keywords': list(set(keywords)),
                            'brand': req_brand,
                            'model': req_model,
                            'sku': req_model
                        }
                        requirements.append(requirement)
                        break
                        
                    except (ValueError, IndexError):
                        continue
        
        processing_log.append({'stage': 'document_processing', 'status': 'completed', 'count': len(requirements)})
        
        if not requirements:
            processing_log.append({'stage': 'document_processing', 'status': 'failed', 'error': 'No requirements extracted'})
            return {
                'success': False,
                'error': 'No requirements could be extracted from the document',
                'processing_log': processing_log,
                'stage_failed': 'document_processing'
            }
        
        # Step 2: Product Matching (using REAL database - NO MOCK DATA)
        processing_log.append({'stage': 'product_matching', 'status': 'started'})

        try:
            # Use ProductMatchingWorkflow with real database queries
            matching_result = self.product_matcher.execute_product_matching(
                requirements=requirements,
                fuzzy_threshold=fuzzy_threshold,
                max_results_per_requirement=3  # Top 3 matches per requirement
            )

            if not matching_result['success']:
                processing_log.append({
                    'stage': 'product_matching',
                    'status': 'failed',
                    'error': 'Product matching workflow failed'
                })
                return {
                    'success': False,
                    'error': 'Product matching failed',
                    'processing_log': processing_log,
                    'stage_failed': 'product_matching'
                }

            # Extract matches from result
            all_matches = matching_result['matches']
            total_matches = matching_result['total_matches']

            processing_log.append({
                'stage': 'product_matching',
                'status': 'completed',
                'total_matches': total_matches,
                'products_searched': matching_result.get('products_searched', 0)
            })

        except Exception as e:
            # CRITICAL: Fail fast - NO fallback to mock data
            logger.error(f"Product matching failed: {e}")
            processing_log.append({
                'stage': 'product_matching',
                'status': 'failed',
                'error': str(e)
            })
            return {
                'success': False,
                'error': f'Product matching failed: {str(e)}',
                'processing_log': processing_log,
                'stage_failed': 'product_matching'
            }
        
        # Step 3: Pricing Calculation
        processing_log.append({'stage': 'pricing_calculation', 'status': 'started'})
        
        # Pricing rules
        category_rules = {
            'Power Tools': {'base_markup': 0.30, 'volume_discount': 0.15, 'minimum_margin': 0.20},
            'Safety Equipment': {'base_markup': 0.25, 'volume_discount': 0.12, 'minimum_margin': 0.18},
            'Lighting': {'base_markup': 0.25, 'volume_discount': 0.10, 'minimum_margin': 0.15},
            'Security': {'base_markup': 0.30, 'volume_discount': 0.12, 'minimum_margin': 0.20},
            'Networking': {'base_markup': 0.20, 'volume_discount': 0.08, 'minimum_margin': 0.12},
            'General': {'base_markup': 0.25, 'volume_discount': 0.10, 'minimum_margin': 0.15}
        }
        
        brand_multipliers = {
            'DEWALT': 1.1, '3M': 1.05, 'MAKITA': 1.05, 'CommScope': 1.0, 'Hikvision': 0.95, 'Leviton': 1.0
        }
        
        customer_tiers = {
            'enterprise': 0.05, 'government': 0.08, 'standard': 0.0, 'new': -0.02
        }
        
        # Calculate pricing
        pricing_results = {}
        req_lookup = {f"{req['category']}_{hash(req['description']) % 10000}": req for req in requirements}
        
        for req_key, matches in all_matches.items():
            if matches and req_key in req_lookup:
                best_match = matches[0]
                requirement = req_lookup[req_key]
                
                # Get pricing parameters
                category = best_match.get('category', 'General')
                brand = best_match.get('brand', 'Generic')
                quantity = requirement.get('quantity', 1)
                base_price = best_match.get('unit_price', 0.0)
                
                rules = category_rules.get(category, category_rules['General'])
                brand_multiplier = brand_multipliers.get(brand, 1.0)
                
                # Calculate pricing
                adjusted_base = base_price * brand_multiplier
                marked_up_price = adjusted_base * (1 + rules['base_markup'])
                
                # Volume discount
                volume_discount_rate = 0.0
                if quantity >= 100:
                    volume_discount_rate = rules['volume_discount']
                elif quantity >= 50:
                    volume_discount_rate = rules['volume_discount'] * 0.7
                elif quantity >= 20:
                    volume_discount_rate = rules['volume_discount'] * 0.4
                elif quantity >= 10:
                    volume_discount_rate = rules['volume_discount'] * 0.2
                
                discounted_price = marked_up_price * (1 - volume_discount_rate)
                
                # Minimum margin protection
                minimum_price = base_price * (1 + rules['minimum_margin'])
                protected_price = max(discounted_price, minimum_price)
                
                # Customer tier discount
                tier_discount = customer_tiers.get(customer_tier, 0.0)
                final_unit_price = protected_price * (1 - tier_discount)
                total_price = final_unit_price * quantity
                
                pricing_results[req_key] = {
                    'product_id': best_match['product_id'],
                    'product_name': best_match['product_name'],
                    'category': category,
                    'brand': brand,
                    'quantity': quantity,
                    'final_unit_price': round(final_unit_price, 2),
                    'total_price': round(total_price, 2),
                    'savings_breakdown': {
                        'total_savings': round((marked_up_price - final_unit_price) * quantity, 2)
                    }
                }
        
        subtotal = sum(p['total_price'] for p in pricing_results.values())
        total_savings = sum(p['savings_breakdown']['total_savings'] for p in pricing_results.values())
        
        pricing_summary = {
            'subtotal': round(subtotal, 2),
            'total_savings': round(total_savings, 2),
            'item_count': len(pricing_results),
            'customer_tier': customer_tier
        }
        
        processing_log.append({'stage': 'pricing_calculation', 'status': 'completed', 'subtotal': subtotal})
        
        # Step 4: Quotation Generation
        processing_log.append({'stage': 'quotation_generation', 'status': 'started'})
        
        # Generate quotation
        quote_number = f"Q{datetime.now().strftime('%Y%m%d')}-{datetime.now().microsecond // 1000:03d}"
        quote_date = datetime.now().strftime('%Y-%m-%d')
        valid_until = (datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Calculate totals
        tax_rate = 0.10
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        line_items = []
        for i, (req_key, pricing) in enumerate(pricing_results.items(), 1):
            line_items.append({
                'line_number': i,
                'product_id': pricing['product_id'],
                'product_name': pricing['product_name'],
                'brand': pricing.get('brand', ''),
                'model': pricing.get('model', ''),
                'category': pricing['category'],
                'quantity': pricing['quantity'],
                'unit_price': pricing['final_unit_price'],
                'line_total': pricing['total_price'],
                'savings': pricing['savings_breakdown']['total_savings']
            })
        
        quotation = {
            'quote_number': quote_number,
            'quote_date': quote_date,
            'valid_until': valid_until,
            'customer_info': {
                'name': customer_name,
                'tier': customer_tier
            },
            'line_items': line_items,
            'financial_summary': {
                'subtotal': round(subtotal, 2),
                'tax_rate': tax_rate * 100,
                'tax_amount': round(tax_amount, 2),
                'total_amount': round(total_amount, 2),
                'total_items': len(line_items),
                'total_savings': round(total_savings, 2)
            },
            'terms_and_conditions': {
                'payment_terms': 'Net 30 days',
                'delivery_terms': 'FOB Origin',
                'validity': f'Valid until {valid_until}',
                'warranty': '1 Year Manufacturer Warranty'
            },
            'created_at': datetime.now().isoformat(),
            'status': 'draft'
        }
        
        processing_log.append({'stage': 'quotation_generation', 'status': 'completed', 'quote_number': quote_number})
        
        # Generate summary text
        quotation_text = f'''
QUOTATION #{quote_number}
==============================

Customer: {customer_name}
Date: {quote_date}
Valid Until: {valid_until}

ITEMS:
------
'''
        for item in line_items:
            quotation_text += f'''
{item['line_number']}. {item['product_name']}
   Brand: {item['brand']} {item['model']}
   Quantity: {item['quantity']}
   Unit Price: ${item['unit_price']:.2f}
   Total: ${item['line_total']:.2f}
'''
        
        quotation_text += f'''
------
Subtotal: ${subtotal:.2f}
Tax ({tax_rate*100:.1f}%): ${tax_amount:.2f}
Total Savings: ${total_savings:.2f}
TOTAL: ${total_amount:.2f}

Terms: Payment due within 30 days
Validity: This quotation is valid until {valid_until}
'''
        
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()
        
        return {
            'success': True,
            'requirements': requirements,
            'matches': all_matches,
            'pricing_results': pricing_results,
            'pricing_summary': pricing_summary,
            'quotation': quotation,
            'quotation_text': quotation_text,
            'quote_number': quote_number,
            'total_amount': total_amount,
            'processing_log': processing_log,
            'processing_duration': processing_duration,
            'summary': {
                'total_requirements': len(requirements),
                'matched_requirements': len([k for k, v in all_matches.items() if v]),
                'total_amount': total_amount,
                'total_savings': total_savings,
                'currency': 'USD'
            }
        }
        
    except Exception as e:
        error_details = traceback.format_exc()
        processing_log.append({
            'stage': 'error_handler', 
            'status': 'failed', 
            'error': str(e),
            'error_details': error_details
        })
        
        return {
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'processing_log': processing_log,
            'stage_failed': 'unknown'
        }

# Execute complete RFP processing
result = process_rfp_complete(
    file_path=file_path if 'file_path' in locals() else None,
    text_content=text_content if 'text_content' in locals() else None,
    rfp_text=rfp_text if 'rfp_text' in locals() else None,
    customer_name=customer_name if 'customer_name' in locals() else 'Valued Customer',
    customer_tier=customer_tier if 'customer_tier' in locals() else 'standard',
    fuzzy_threshold=fuzzy_threshold if 'fuzzy_threshold' in locals() else 60,
    database_url=database_url if 'database_url' in locals() else None,
    pricing_config=pricing_config if 'pricing_config' in locals() else None,
    template_config=template_config if 'template_config' in locals() else None
)
"""
        })
        
        return workflow.build()
    
    def execute_complete_rfp_processing(self, file_path: Optional[str] = None,
                                       text_content: Optional[str] = None,
                                       rfp_text: Optional[str] = None,
                                       customer_name: str = 'Valued Customer',
                                       customer_tier: str = 'standard',
                                       fuzzy_threshold: int = 60) -> Dict[str, Any]:
        """Execute complete RFP processing workflow."""
        try:
            workflow = self.create_complete_orchestration_workflow()
            
            # Prepare parameters
            params = {
                'customer_name': customer_name,
                'customer_tier': customer_tier,
                'fuzzy_threshold': fuzzy_threshold,
                'database_url': self.config.get('database_url'),
                'pricing_config': self.config.get('pricing_config'),
                'template_config': self.config.get('template_config')
            }
            
            # Add input parameters
            if file_path:
                params['file_path'] = file_path
            if text_content:
                params['text_content'] = text_content
            if rfp_text:
                params['rfp_text'] = rfp_text
            
            # Execute workflow
            results, run_id = self.runtime.execute(workflow, parameters=params)
            
            return {
                'success': True,
                'results': results,
                'run_id': run_id
            }
            
        except Exception as e:
            logger.error(f"RFP orchestration workflow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': None,
                'run_id': None
            }

# Example usage and testing
if __name__ == "__main__":
    # Test with sample RFP
    sample_rfp = """
    Request for Proposal - Office Equipment Upgrade
    
    We require the following items for our office renovation:
    
    1. 50 units of DEWALT DCD791D2 20V cordless drill
    2. 100 units of 3M H-700 Series safety helmets
    3. 25 pieces motion sensors for lighting control
    4. 200 meters of Cat6A ethernet cable
    5. 10 units security cameras for lobby area
    
    Please provide detailed quotation with competitive pricing.
    """
    
    orchestrator = RFPOrchestrationWorkflow()
    result = orchestrator.execute_complete_rfp_processing(
        rfp_text=sample_rfp,
        customer_name='Demo Corporation',
        customer_tier='enterprise',
        fuzzy_threshold=50
    )
    
    if result['success']:
        summary = result['results']['summary']
        print("RFP Processing Complete!")
        print(f"- Quote Number: {result['results']['quote_number']}")
        print(f"- Requirements: {summary['total_requirements']}")
        print(f"- Matched: {summary['matched_requirements']}")
        print(f"- Total: ${summary['total_amount']:,.2f}")
        print(f"- Savings: ${summary['total_savings']:,.2f}")
        print(f"- Duration: {result['results']['processing_duration']:.2f}s")
        
        # Print quotation summary
        print("\\nQuotation Preview:")
        print(result['results']['quotation_text'][:500] + "...")
        
    else:
        print(f"RFP Processing failed: {result['error']}")
        if 'processing_log' in result.get('results', {}):
            print("Processing Log:")
            for log_entry in result['results']['processing_log']:
                print(f"  - {log_entry['stage']}: {log_entry['status']}")