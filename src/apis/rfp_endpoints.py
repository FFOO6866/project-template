"""
RFP Processing API Endpoints

Production API endpoints for RFP processing using Kailash SDK workflows.
Replaces hardcoded processing with real workflow execution.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json
import traceback

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

try:
    from werkzeug.utils import secure_filename
    HAS_WERKZEUG = True
except ImportError:
    HAS_WERKZEUG = False

# Import our workflows
from src.workflows.rfp_orchestration import RFPOrchestrationWorkflow
from src.workflows.document_processing import DocumentProcessingWorkflow
from src.workflows.product_matching import ProductMatchingWorkflow
from src.workflows.pricing_engine import PricingEngineWorkflow
from src.workflows.quotation_generation import QuotationGenerationWorkflow

logger = logging.getLogger(__name__)

class RFPProcessingAPI:
    """Flask API for RFP processing with Kailash workflows."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not HAS_FLASK:
            raise ImportError("Flask is required for API endpoints. Install with: pip install flask flask-cors")
        
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.config = config or {}
        
        # Initialize workflow orchestrator
        self.orchestrator = RFPOrchestrationWorkflow(
            config=self.config.get('workflow_config', {})
        )
        
        # Setup routes
        self._setup_routes()
        
        # Configure file uploads
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        self.app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.pdf', '.docx', '.doc']
    
    def _setup_routes(self):
        """Setup all API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """API health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'service': 'RFP Processing API',
                'version': '2.0.0',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'document_processing': True,
                    'product_matching': True,
                    'pricing_engine': True,
                    'quotation_generation': True,
                    'database': True,
                    'workflows': True
                }
            })
        
        @self.app.route('/api/rfp/process', methods=['POST'])
        def process_rfp():
            """Main RFP processing endpoint using Kailash workflows."""
            try:
                request_start = datetime.now()
                
                # Parse request data
                if request.content_type and 'application/json' in request.content_type:
                    data = request.get_json()
                    if not data:
                        return jsonify({
                            'success': False,
                            'error': 'No JSON data provided',
                            'error_code': 'MISSING_DATA'
                        }), 400
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Content-Type must be application/json',
                        'error_code': 'INVALID_CONTENT_TYPE'
                    }), 400
                
                # Extract parameters
                rfp_text = data.get('rfp_text')
                customer_name = data.get('customer_name', 'Valued Customer')
                customer_tier = data.get('customer_tier', 'standard')
                fuzzy_threshold = data.get('fuzzy_threshold', 60)
                
                # Validate input
                if not rfp_text or not isinstance(rfp_text, str) or len(rfp_text.strip()) < 10:
                    return jsonify({
                        'success': False,
                        'error': 'rfp_text must be a non-empty string with at least 10 characters',
                        'error_code': 'INVALID_RFP_TEXT'
                    }), 400
                
                if customer_tier not in ['standard', 'enterprise', 'government', 'new']:
                    customer_tier = 'standard'
                
                if not isinstance(fuzzy_threshold, int) or fuzzy_threshold < 0 or fuzzy_threshold > 100:
                    fuzzy_threshold = 60
                
                # Execute RFP processing workflow
                logger.info(f"Processing RFP for customer: {customer_name} (tier: {customer_tier})")
                
                processing_result = self.orchestrator.execute_complete_rfp_processing(
                    rfp_text=rfp_text,
                    customer_name=customer_name,
                    customer_tier=customer_tier,
                    fuzzy_threshold=fuzzy_threshold
                )
                
                if processing_result['success']:
                    results = processing_result['results']
                    request_duration = (datetime.now() - request_start).total_seconds()
                    
                    # Prepare response
                    response_data = {
                        'success': True,
                        'data': {
                            'quotation': {
                                'quote_number': results['quote_number'],
                                'customer_name': customer_name,
                                'customer_tier': customer_tier,
                                'quote_date': results['quotation']['quote_date'],
                                'valid_until': results['quotation']['valid_until'],
                                'financial_summary': results['quotation']['financial_summary'],
                                'line_items': results['quotation']['line_items'],
                                'terms_and_conditions': results['quotation']['terms_and_conditions']
                            },
                            'requirements': results['requirements'],
                            'matches': {
                                req_key: [
                                    {
                                        'product_id': match['product_id'],
                                        'product_name': match['product_name'],
                                        'unit_price': match['unit_price'],
                                        'match_score': match['match_score'],
                                        'brand': match.get('brand'),
                                        'model': match.get('model')
                                    }
                                    for match in matches[:3]  # Top 3 matches only
                                ]
                                for req_key, matches in results['matches'].items()
                            },
                            'pricing_summary': results['pricing_summary'],
                            'quotation_text': results['quotation_text'],
                            'processing_metadata': {
                                'processing_duration': results.get('processing_duration', 0),
                                'request_duration': request_duration,
                                'workflow_run_id': processing_result.get('run_id'),
                                'processed_at': datetime.now().isoformat(),
                                'api_version': '2.0.0'
                            }
                        }
                    }
                    
                    logger.info(f"RFP processing completed successfully: {results['quote_number']}")
                    return jsonify(response_data)
                    
                else:
                    logger.error(f"RFP processing failed: {processing_result.get('error')}")
                    return jsonify({
                        'success': False,
                        'error': processing_result.get('error', 'Unknown processing error'),
                        'error_code': 'PROCESSING_FAILED',
                        'processing_log': processing_result.get('results', {}).get('processing_log', [])
                    }), 500
                    
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"API endpoint error: {e}\\n{error_trace}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_code': 'INTERNAL_ERROR',
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/rfp/upload', methods=['POST'])
        def upload_rfp_file():
            """Upload and process RFP document file."""
            try:
                # Check if file was uploaded
                if 'file' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': 'No file uploaded',
                        'error_code': 'NO_FILE'
                    }), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({
                        'success': False,
                        'error': 'No file selected',
                        'error_code': 'EMPTY_FILENAME'
                    }), 400
                
                # Validate file extension
                if HAS_WERKZEUG:
                    filename = secure_filename(file.filename)
                else:
                    filename = file.filename
                
                file_ext = Path(filename).suffix.lower()
                if file_ext not in self.app.config['UPLOAD_EXTENSIONS']:
                    return jsonify({
                        'success': False,
                        'error': f'File type {file_ext} not supported. Supported: {self.app.config["UPLOAD_EXTENSIONS"]}',
                        'error_code': 'UNSUPPORTED_FILE_TYPE'
                    }), 400
                
                # Get form parameters
                customer_name = request.form.get('customer_name', 'Valued Customer')
                customer_tier = request.form.get('customer_tier', 'standard')
                fuzzy_threshold = int(request.form.get('fuzzy_threshold', 60))
                
                # Save file temporarily and read content
                import tempfile
                import os
                
                try:
                    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                        file.save(temp_file.name)
                        temp_path = temp_file.name
                    
                    # Process the uploaded file
                    processing_result = self.orchestrator.execute_complete_rfp_processing(
                        file_path=temp_path,
                        customer_name=customer_name,
                        customer_tier=customer_tier,
                        fuzzy_threshold=fuzzy_threshold
                    )
                    
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    
                    if processing_result['success']:
                        results = processing_result['results']
                        
                        return jsonify({
                            'success': True,
                            'filename': filename,
                            'data': {
                                'quote_number': results['quote_number'],
                                'customer_name': customer_name,
                                'total_amount': results['total_amount'],
                                'requirements_found': len(results['requirements']),
                                'quotation_text': results['quotation_text'],
                                'processing_duration': results.get('processing_duration', 0)
                            }
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'filename': filename,
                            'error': processing_result.get('error', 'File processing failed'),
                            'error_code': 'FILE_PROCESSING_FAILED'
                        }), 500
                        
                except Exception as file_error:
                    return jsonify({
                        'success': False,
                        'filename': filename,
                        'error': f'File handling error: {str(file_error)}',
                        'error_code': 'FILE_HANDLING_ERROR'
                    }), 500
                    
            except Exception as e:
                logger.error(f"File upload error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_code': 'UPLOAD_ERROR'
                }), 500
        
        @self.app.route('/api/quotations/<quote_number>', methods=['GET'])
        def get_quotation(quote_number):
            """Retrieve a specific quotation by quote number."""
            try:
                # Query database for quotation
                import sqlite3
                
                try:
                    conn = sqlite3.connect('quotations.db')
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT * FROM quotations WHERE quote_number = ?
                    ''', (quote_number,))
                    
                    quotation_row = cursor.fetchone()
                    
                    if not quotation_row:
                        return jsonify({
                            'success': False,
                            'error': 'Quotation not found',
                            'error_code': 'NOT_FOUND'
                        }), 404
                    
                    # Get line items
                    cursor.execute('''
                        SELECT * FROM quotation_items 
                        WHERE quotation_id = ?
                        ORDER BY line_number
                    ''', (quotation_row['id'],))
                    
                    items = cursor.fetchall()
                    conn.close()
                    
                    # Prepare response
                    quotation_data = {
                        'quote_number': quotation_row['quote_number'],
                        'customer_name': quotation_row['customer_name'],
                        'customer_tier': quotation_row['customer_tier'],
                        'quote_date': quotation_row['quote_date'],
                        'valid_until': quotation_row['valid_until'],
                        'status': quotation_row['status'],
                        'financial_summary': {
                            'subtotal': quotation_row['subtotal'],
                            'tax_amount': quotation_row['tax_amount'],
                            'total_amount': quotation_row['total_amount'],
                            'total_items': quotation_row['total_items'],
                            'total_savings': quotation_row['total_savings']
                        },
                        'line_items': [
                            {
                                'line_number': item['line_number'],
                                'product_id': item['product_id'],
                                'product_name': item['product_name'],
                                'brand': item['brand'],
                                'model': item['model'],
                                'category': item['category'],
                                'quantity': item['quantity'],
                                'unit_price': item['unit_price'],
                                'line_total': item['line_total'],
                                'savings': item['savings']
                            }
                            for item in items
                        ],
                        'created_at': quotation_row['created_at'],
                        'version': quotation_row['version']
                    }
                    
                    return jsonify({
                        'success': True,
                        'data': quotation_data
                    })
                    
                except Exception as db_error:
                    return jsonify({
                        'success': False,
                        'error': f'Database error: {str(db_error)}',
                        'error_code': 'DATABASE_ERROR'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Get quotation error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_code': 'RETRIEVAL_ERROR'
                }), 500
        
        @self.app.route('/api/quotations', methods=['GET'])
        def list_quotations():
            """List all quotations with pagination."""
            try:
                # Get query parameters
                page = int(request.args.get('page', 1))
                per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
                status = request.args.get('status')
                customer_name = request.args.get('customer_name')
                
                # Calculate offset
                offset = (page - 1) * per_page
                
                # Build query
                query = 'SELECT * FROM quotations'
                params = []
                conditions = []
                
                if status:
                    conditions.append('status = ?')
                    params.append(status)
                
                if customer_name:
                    conditions.append('customer_name LIKE ?')
                    params.append(f'%{customer_name}%')
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([per_page, offset])
                
                # Execute query
                import sqlite3
                
                conn = sqlite3.connect('quotations.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(query, params)
                quotations = cursor.fetchall()
                
                # Get total count
                count_query = 'SELECT COUNT(*) as total FROM quotations'
                if conditions:
                    count_query += ' WHERE ' + ' AND '.join(conditions[:-2] if len(conditions) > 2 else conditions)
                
                cursor.execute(count_query, params[:-2] if len(params) > 2 else params[:-2] if params else [])
                total = cursor.fetchone()['total']
                
                conn.close()
                
                # Prepare response
                quotation_list = []
                for q in quotations:
                    quotation_list.append({
                        'quote_number': q['quote_number'],
                        'customer_name': q['customer_name'],
                        'customer_tier': q['customer_tier'],
                        'quote_date': q['quote_date'],
                        'valid_until': q['valid_until'],
                        'status': q['status'],
                        'total_amount': q['total_amount'],
                        'total_items': q['total_items'],
                        'created_at': q['created_at']
                    })
                
                return jsonify({
                    'success': True,
                    'data': {
                        'quotations': quotation_list,
                        'pagination': {
                            'page': page,
                            'per_page': per_page,
                            'total': total,
                            'pages': (total + per_page - 1) // per_page
                        }
                    }
                })
                
            except Exception as e:
                logger.error(f"List quotations error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_code': 'LIST_ERROR'
                }), 500
        
        @self.app.route('/api/products/search', methods=['POST'])
        def search_products():
            """Search products using product matching workflow."""
            try:
                data = request.get_json()
                
                if not data or 'keywords' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Missing keywords in request',
                        'error_code': 'MISSING_KEYWORDS'
                    }), 400
                
                keywords = data['keywords']
                if isinstance(keywords, str):
                    keywords = keywords.split()
                
                category = data.get('category')
                fuzzy_threshold = data.get('fuzzy_threshold', 60)
                
                # Create mock requirement for product search
                mock_requirement = {
                    'category': category or 'General',
                    'description': ' '.join(keywords),
                    'quantity': 1,
                    'keywords': keywords,
                    'brand': data.get('brand'),
                    'model': data.get('model')
                }
                
                # Execute product matching
                matcher = ProductMatchingWorkflow()
                matching_result = matcher.execute_product_matching(
                    requirements=[mock_requirement],
                    fuzzy_threshold=fuzzy_threshold
                )
                
                if matching_result['success']:
                    matches = matching_result['results']['matches']
                    # Get matches for our mock requirement
                    req_key = list(matches.keys())[0] if matches else 'no_matches'
                    product_matches = matches.get(req_key, [])
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'matches': product_matches,
                            'total_matches': len(product_matches),
                            'search_keywords': keywords,
                            'category_filter': category,
                            'fuzzy_threshold': fuzzy_threshold
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': matching_result.get('error', 'Product search failed'),
                        'error_code': 'SEARCH_FAILED'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Product search error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_code': 'SEARCH_ERROR'
                }), 500
        
        @self.app.route('/api/debug/workflow-status', methods=['GET'])
        def workflow_status():
            """Debug endpoint to check workflow component status."""
            try:
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'components': {}
                }
                
                # Test each workflow component
                try:
                    doc_processor = DocumentProcessingWorkflow()
                    status['components']['document_processing'] = {
                        'status': 'healthy',
                        'class': 'DocumentProcessingWorkflow'
                    }
                except Exception as e:
                    status['components']['document_processing'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
                try:
                    product_matcher = ProductMatchingWorkflow()
                    status['components']['product_matching'] = {
                        'status': 'healthy',
                        'class': 'ProductMatchingWorkflow'
                    }
                except Exception as e:
                    status['components']['product_matching'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
                try:
                    pricing_engine = PricingEngineWorkflow()
                    status['components']['pricing_engine'] = {
                        'status': 'healthy',
                        'class': 'PricingEngineWorkflow'
                    }
                except Exception as e:
                    status['components']['pricing_engine'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
                try:
                    quotation_generator = QuotationGenerationWorkflow()
                    status['components']['quotation_generation'] = {
                        'status': 'healthy',
                        'class': 'QuotationGenerationWorkflow'
                    }
                except Exception as e:
                    status['components']['quotation_generation'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
                try:
                    orchestrator = RFPOrchestrationWorkflow()
                    status['components']['orchestration'] = {
                        'status': 'healthy',
                        'class': 'RFPOrchestrationWorkflow'
                    }
                except Exception as e:
                    status['components']['orchestration'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
                # Overall health
                all_healthy = all(
                    comp.get('status') == 'healthy' 
                    for comp in status['components'].values()
                )
                
                status['overall_status'] = 'healthy' if all_healthy else 'degraded'
                
                return jsonify({
                    'success': True,
                    'data': status
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_code': 'STATUS_CHECK_ERROR'
                }), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask API server."""
        logger.info(f"Starting RFP Processing API on {host}:{port}")
        logger.info("Available endpoints:")
        logger.info("  POST /api/rfp/process - Process RFP text")
        logger.info("  POST /api/rfp/upload - Upload and process RFP file")
        logger.info("  GET  /api/quotations/<quote_number> - Get specific quotation")
        logger.info("  GET  /api/quotations - List quotations")
        logger.info("  POST /api/products/search - Search products")
        logger.info("  GET  /health - Health check")
        logger.info("  GET  /api/debug/workflow-status - Workflow status")
        
        self.app.run(host=host, port=port, debug=debug)

# Factory function for creating the API
def create_rfp_api(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and return Flask app for RFP processing."""
    api = RFPProcessingAPI(config)
    return api.app

# Example usage and testing
if __name__ == "__main__":
    if not HAS_FLASK:
        print("Flask not available. Install with: pip install flask flask-cors")
        sys.exit(1)
    
    # Test configuration
    test_config = {
        'workflow_config': {
            'processing_settings': {
                'fuzzy_threshold': 60,
                'timeout_seconds': 300
            }
        }
    }
    
    # Create and run API
    try:
        api = RFPProcessingAPI(test_config)
        print("RFP Processing API - Production Ready")
        print("Powered by Kailash SDK workflows")
        print("=====================================")
        api.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\\nAPI server stopped")
    except Exception as e:
        print(f"API server error: {e}")
        sys.exit(1)