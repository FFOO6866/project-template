"""
Quotation Generation Workflow for RFP Analysis

Handles professional quotation generation with PDF export, email delivery,
and database storage using Kailash SDK workflows.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

logger = logging.getLogger(__name__)

class QuotationGenerationWorkflow:
    """Workflow for generating professional quotations with PDF export."""
    
    def __init__(self, template_config: Optional[Dict[str, Any]] = None):
        self.workflow_builder = WorkflowBuilder()
        self.runtime = LocalRuntime()
        self.template_config = template_config or self._get_default_template_config()
    
    def _get_default_template_config(self) -> Dict[str, Any]:
        """Get default quotation template configuration."""
        return {
            'company_info': {
                'name': 'HORME Solutions Inc.',
                'address': '123 Business Park Drive\\nSuite 456\\nNew York, NY 10001',
                'phone': '+1 (555) 123-4567',
                'email': 'quotes@horme.com',
                'website': 'www.horme.com',
                'tax_id': 'EIN: 12-3456789'
            },
            'quotation_settings': {
                'validity_days': 30,
                'tax_rate': 0.10,
                'payment_terms': 'Net 30 days',
                'delivery_terms': 'FOB Origin',
                'warranty': '1 Year Manufacturer Warranty'
            },
            'pdf_settings': {
                'page_size': 'letter',
                'margin': 72,  # 1 inch in points
                'font_size': 10,
                'header_font_size': 16,
                'logo_path': None  # Path to company logo
            },
            'email_settings': {
                'subject_template': 'Quotation #{quote_number} - {customer_name}',
                'body_template': '''Dear {customer_name},

Please find attached our quotation #{quote_number} for your recent RFP request.

Quotation Summary:
- Total Items: {item_count}
- Subtotal: ${subtotal:,.2f}
- Tax: ${tax_amount:,.2f}
- Total Amount: ${total_amount:,.2f}

This quotation is valid until {valid_until}.

Please don't hesitate to contact us if you have any questions.

Best regards,
HORME Solutions Team'''
            }
        }
    
    def create_quotation_data_workflow(self) -> Any:
        """Create workflow for generating quotation data structure."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "generate_quotation_data", {
            "code": """
from datetime import datetime, timedelta
# Removed typing import for Kailash SDK compatibility
import uuid
import hashlib

def generate_quote_number() -> str:
    '''Generate unique quotation number'''
    timestamp = datetime.now().strftime('%Y%m%d')
    random_suffix = str(uuid.uuid4().hex[:6]).upper()
    return f"Q{timestamp}-{random_suffix}"

def calculate_quotation_totals(pricing_results: Dict, tax_rate: float = 0.10) -> Dict:
    '''Calculate quotation totals including tax'''
    subtotal = 0.0
    total_items = 0
    
    line_items = []
    
    for req_key, pricing in pricing_results.items():
        line_item = {
            'line_number': total_items + 1,
            'product_id': pricing.get('product_id', ''),
            'product_name': pricing.get('product_name', ''),
            'description': pricing.get('product_name', ''),
            'quantity': pricing.get('quantity', 1),
            'unit_price': pricing.get('final_unit_price', 0.0),
            'line_total': pricing.get('total_price', 0.0),
            'brand': pricing.get('brand', ''),
            'model': pricing.get('model', ''),
            'category': pricing.get('category', ''),
            'savings': pricing.get('savings_breakdown', {}).get('total_savings', 0.0)
        }
        
        line_items.append(line_item)
        subtotal += line_item['line_total']
        total_items += 1
    
    # Calculate tax and total
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount
    total_savings = sum(item['savings'] for item in line_items)
    
    return {
        'line_items': line_items,
        'subtotal': round(subtotal, 2),
        'tax_rate': tax_rate,
        'tax_amount': round(tax_amount, 2),
        'total_amount': round(total_amount, 2),
        'total_items': total_items,
        'total_savings': round(total_savings, 2)
    }

def create_quotation_structure(requirements: List[Dict], pricing_results: Dict,
                             customer_name: str = 'Valued Customer',
                             customer_tier: str = 'standard') -> Dict:
    '''Create complete quotation data structure'''
    
    # Generate quotation metadata
    quote_number = generate_quote_number()
    quote_date = datetime.now()
    valid_until = quote_date + timedelta(days=30)
    
    # Calculate totals
    totals = calculate_quotation_totals(pricing_results)
    
    # Create quotation structure
    quotation = {
        'quote_number': quote_number,
        'quote_date': quote_date.strftime('%Y-%m-%d'),
        'valid_until': valid_until.strftime('%Y-%m-%d'),
        'customer_info': {
            'name': customer_name,
            'tier': customer_tier,
            'contact': '',  # To be filled from request
            'address': '',  # To be filled from request
            'email': '',    # To be filled from request
            'phone': ''     # To be filled from request
        },
        'rfp_info': {
            'requirements_count': len(requirements),
            'categories': list(set(req.get('category', 'General') for req in requirements)),
            'total_quantity': sum(req.get('quantity', 1) for req in requirements)
        },
        'line_items': totals['line_items'],
        'financial_summary': {
            'subtotal': totals['subtotal'],
            'tax_rate': totals['tax_rate'] * 100,  # Convert to percentage
            'tax_amount': totals['tax_amount'],
            'total_amount': totals['total_amount'],
            'total_items': totals['total_items'],
            'total_savings': totals['total_savings'],
            'average_discount': (totals['total_savings'] / (totals['subtotal'] + totals['total_savings']) * 100) if (totals['subtotal'] + totals['total_savings']) > 0 else 0
        },
        'terms_and_conditions': {
            'payment_terms': 'Net 30 days',
            'delivery_terms': 'FOB Origin',
            'validity': f"Valid until {valid_until.strftime('%B %d, %Y')}",
            'warranty': '1 Year Manufacturer Warranty',
            'notes': 'Prices subject to change without notice. All sales final.'
        },
        'created_at': quote_date.isoformat(),
        'status': 'draft',
        'version': '1.0'
    }
    
    return quotation

# Generate quotation data
if 'requirements' in locals() and 'pricing_results' in locals():
    quotation_data = create_quotation_structure(
        requirements,
        pricing_results.get('pricing_results', {}),
        customer_name if 'customer_name' in locals() else 'Valued Customer',
        customer_tier if 'customer_tier' in locals() else 'standard'
    )
    
    result = {
        'quotation': quotation_data,
        'success': True,
        'quote_number': quotation_data['quote_number'],
        'total_amount': quotation_data['financial_summary']['total_amount']
    }
else:
    result = {
        'quotation': {},
        'success': False,
        'error': 'Missing requirements or pricing_results data'
    }
"""
        })
        
        return workflow.build()
    
    def create_pdf_generation_workflow(self) -> Any:
        """Create workflow for PDF generation."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "generate_pdf", {
            "code": """
from typing import Dict, Any
import io
from datetime import datetime

def generate_pdf_content(quotation: Dict, template_config: Dict) -> Dict:
    '''Generate PDF content for quotation'''
    
    try:
        # Try to use reportlab for PDF generation
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#2E3440')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#5E81AC')
        )
        
        # Build content
        content = []
        
        # Company header
        company_info = template_config.get('company_info', {})
        content.append(Paragraph(f"<b>{company_info.get('name', 'HORME Solutions')}</b>", title_style))
        content.append(Paragraph(company_info.get('address', '').replace('\\n', '<br/>'), styles['Normal']))
        content.append(Paragraph(f"Phone: {company_info.get('phone', '')} | Email: {company_info.get('email', '')}", styles['Normal']))
        content.append(Spacer(1, 20))
        
        # Quotation header
        content.append(Paragraph(f"<b>QUOTATION #{quotation['quote_number']}</b>", title_style))
        content.append(Spacer(1, 10))
        
        # Customer and date information
        info_data = [
            ['Customer:', quotation['customer_info']['name']],
            ['Date:', quotation['quote_date']],
            ['Valid Until:', quotation['valid_until']],
            ['Customer Tier:', quotation['customer_info']['tier'].title()]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(info_table)
        content.append(Spacer(1, 20))
        
        # Line items table
        content.append(Paragraph("QUOTATION ITEMS", heading_style))
        
        # Prepare table data
        table_data = [
            ['#', 'Description', 'Qty', 'Unit Price', 'Total']
        ]
        
        for item in quotation['line_items']:
            table_data.append([
                str(item['line_number']),
                f"{item['product_name']}\\n{item.get('brand', '')} {item.get('model', '')}".strip(),
                str(item['quantity']),
                f"${item['unit_price']:,.2f}",
                f"${item['line_total']:,.2f}"
            ])
        
        # Create items table
        items_table = Table(table_data, colWidths=[0.4*inch, 3.5*inch, 0.6*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5E81AC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Description left-aligned
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), # Numbers right-aligned
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DEE2E6')),
        ]))
        
        content.append(items_table)
        content.append(Spacer(1, 20))
        
        # Financial summary
        financial_summary = quotation['financial_summary']
        summary_data = [
            ['Subtotal:', f"${financial_summary['subtotal']:,.2f}"],
            [f"Tax ({financial_summary['tax_rate']:.1f}%):", f"${financial_summary['tax_amount']:,.2f}"],
            ['Total Savings:', f"${financial_summary['total_savings']:,.2f}"],
            ['TOTAL AMOUNT:', f"${financial_summary['total_amount']:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        
        content.append(summary_table)
        content.append(Spacer(1, 30))
        
        # Terms and conditions
        content.append(Paragraph("TERMS AND CONDITIONS", heading_style))
        terms = quotation['terms_and_conditions']
        
        terms_content = f'''
        <b>Payment Terms:</b> {terms['payment_terms']}<br/>
        <b>Delivery:</b> {terms['delivery_terms']}<br/>
        <b>Validity:</b> {terms['validity']}<br/>
        <b>Warranty:</b> {terms['warranty']}<br/><br/>
        {terms.get('notes', '')}
        '''
        
        content.append(Paragraph(terms_content, styles['Normal']))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return {
            'pdf_bytes': pdf_bytes,
            'pdf_size': len(pdf_bytes),
            'success': True,
            'error': None
        }
        
    except ImportError:
        # Fallback: Generate HTML content instead
        html_content = generate_html_quotation(quotation, template_config)
        return {
            'pdf_bytes': None,
            'html_content': html_content,
            'pdf_size': 0,
            'success': True,
            'error': 'ReportLab not available, generated HTML instead'
        }
        
    except Exception as e:
        return {
            'pdf_bytes': None,
            'html_content': None,
            'pdf_size': 0,
            'success': False,
            'error': f'PDF generation failed: {str(e)}'
        }

def generate_html_quotation(quotation: Dict, template_config: Dict) -> str:
    '''Generate HTML quotation as PDF fallback'''
    
    company_info = template_config.get('company_info', {})
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quotation #{quotation['quote_number']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .company-name {{ font-size: 24px; font-weight: bold; color: #2E3440; }}
            .quotation-title {{ font-size: 20px; font-weight: bold; margin: 20px 0; }}
            .info-section {{ margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
            th {{ background-color: #5E81AC; color: white; }}
            .total-row {{ font-weight: bold; background-color: #f0f0f0; }}
            .terms {{ margin-top: 30px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-name">{company_info.get('name', 'HORME Solutions')}</div>
            <p>{company_info.get('address', '').replace(chr(10), '<br>')}</p>
            <p>Phone: {company_info.get('phone', '')} | Email: {company_info.get('email', '')}</p>
        </div>
        
        <div class="quotation-title">QUOTATION #{quotation['quote_number']}</div>
        
        <div class="info-section">
            <p><strong>Customer:</strong> {quotation['customer_info']['name']}</p>
            <p><strong>Date:</strong> {quotation['quote_date']}</p>
            <p><strong>Valid Until:</strong> {quotation['valid_until']}</p>
        </div>
        
        <h3>QUOTATION ITEMS</h3>
        <table>
            <tr>
                <th>#</th>
                <th>Description</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
            </tr>
    '''
    
    for item in quotation['line_items']:
        html_content += f'''
            <tr>
                <td>{item['line_number']}</td>
                <td>{item['product_name']}<br><small>{item.get('brand', '')} {item.get('model', '')}</small></td>
                <td>{item['quantity']}</td>
                <td>${item['unit_price']:,.2f}</td>
                <td>${item['line_total']:,.2f}</td>
            </tr>
        '''
    
    financial = quotation['financial_summary']
    html_content += f'''
        </table>
        
        <table style="width: 50%; float: right;">
            <tr><td>Subtotal:</td><td>${financial['subtotal']:,.2f}</td></tr>
            <tr><td>Tax ({financial['tax_rate']:.1f}%):</td><td>${financial['tax_amount']:,.2f}</td></tr>
            <tr><td>Total Savings:</td><td>${financial['total_savings']:,.2f}</td></tr>
            <tr class="total-row"><td>TOTAL AMOUNT:</td><td>${financial['total_amount']:,.2f}</td></tr>
        </table>
        
        <div style="clear: both;"></div>
        
        <div class="terms">
            <h4>TERMS AND CONDITIONS</h4>
    '''
    
    terms = quotation['terms_and_conditions']
    html_content += f'''
            <p><strong>Payment Terms:</strong> {terms['payment_terms']}</p>
            <p><strong>Delivery:</strong> {terms['delivery_terms']}</p>
            <p><strong>Validity:</strong> {terms['validity']}</p>
            <p><strong>Warranty:</strong> {terms['warranty']}</p>
            <p>{terms.get('notes', '')}</p>
        </div>
    </body>
    </html>
    '''
    
    return html_content

# Generate PDF content
if 'quotation' in locals() and quotation:
    pdf_result = generate_pdf_content(
        quotation,
        template_config if 'template_config' in locals() else {}
    )
    
    result = {
        **pdf_result,
        'quotation': quotation,
        'quote_number': quotation.get('quote_number', ''),
        'filename': f"quotation_{quotation.get('quote_number', 'draft')}.pdf"
    }
else:
    result = {
        'pdf_bytes': None,
        'html_content': None,
        'success': False,
        'error': 'No quotation data provided'
    }
"""
        })
        
        return workflow.build()
    
    def create_database_storage_workflow(self) -> Any:
        """Create workflow for storing quotation in database."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "store_quotation", {
            "code": """
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any

def store_quotation_in_database(quotation: Dict, db_path: str = 'quotations.db') -> Dict:
    '''Store quotation data in database'''
    
    try:
        # Create database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                customer_tier TEXT DEFAULT 'standard',
                quote_date DATE NOT NULL,
                valid_until DATE,
                status TEXT DEFAULT 'draft',
                subtotal REAL NOT NULL,
                tax_amount REAL NOT NULL,
                total_amount REAL NOT NULL,
                total_items INTEGER DEFAULT 0,
                total_savings REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quotation_data TEXT,  -- JSON blob for full quotation data
                version TEXT DEFAULT '1.0'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotation_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                product_id TEXT,
                product_name TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                category TEXT,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                savings REAL DEFAULT 0.0,
                FOREIGN KEY (quotation_id) REFERENCES quotations (id)
            )
        ''')
        
        # Insert quotation
        financial = quotation['financial_summary']
        cursor.execute('''
            INSERT OR REPLACE INTO quotations 
            (quote_number, customer_name, customer_tier, quote_date, valid_until, 
             status, subtotal, tax_amount, total_amount, total_items, total_savings,
             quotation_data, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            quotation['quote_number'],
            quotation['customer_info']['name'],
            quotation['customer_info']['tier'],
            quotation['quote_date'],
            quotation['valid_until'],
            quotation['status'],
            financial['subtotal'],
            financial['tax_amount'],
            financial['total_amount'],
            financial['total_items'],
            financial['total_savings'],
            json.dumps(quotation),  # Store full quotation as JSON
            quotation['version']
        ))
        
        quotation_id = cursor.lastrowid
        
        # Insert line items
        for item in quotation['line_items']:
            cursor.execute('''
                INSERT INTO quotation_items 
                (quotation_id, line_number, product_id, product_name, brand, model,
                 category, quantity, unit_price, line_total, savings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                quotation_id,
                item['line_number'],
                item['product_id'],
                item['product_name'],
                item.get('brand', ''),
                item.get('model', ''),
                item.get('category', ''),
                item['quantity'],
                item['unit_price'],
                item['line_total'],
                item.get('savings', 0.0)
            ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'quotation_id': quotation_id,
            'database_path': db_path,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'quotation_id': None,
            'database_path': db_path,
            'error': f'Database storage failed: {str(e)}'
        }

# Store quotation in database
if 'quotation' in locals() and quotation:
    storage_result = store_quotation_in_database(quotation)
    result = storage_result
else:
    result = {
        'success': False,
        'error': 'No quotation data to store'
    }
"""
        })
        
        return workflow.build()
    
    def create_complete_quotation_workflow(self) -> Any:
        """Create complete quotation generation workflow."""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "complete_quotation_generation", {
            "code": """
from datetime import datetime, timedelta
# Removed typing import for Kailash SDK compatibility
import uuid
import json
import sqlite3
import io
from pathlib import Path

def generate_quote_number() -> str:
    '''Generate unique quotation number'''
    timestamp = datetime.now().strftime('%Y%m%d')
    random_suffix = str(uuid.uuid4().hex[:6]).upper()
    return f"Q{timestamp}-{random_suffix}"

def create_complete_quotation(requirements: List[Dict], pricing_results: Dict,
                            customer_name: str = 'Valued Customer',
                            customer_tier: str = 'standard',
                            template_config: Dict = None) -> Dict:
    '''Create complete quotation with all components'''
    
    if not template_config:
        template_config = {
            'company_info': {
                'name': 'HORME Solutions Inc.',
                'address': '123 Business Park Drive\\nSuite 456\\nNew York, NY 10001',
                'phone': '+1 (555) 123-4567',
                'email': 'quotes@horme.com',
                'website': 'www.horme.com',
                'tax_id': 'EIN: 12-3456789'
            },
            'quotation_settings': {
                'validity_days': 30,
                'tax_rate': 0.10,
                'payment_terms': 'Net 30 days',
                'delivery_terms': 'FOB Origin',
                'warranty': '1 Year Manufacturer Warranty'
            }
        }
    
    # Generate quotation metadata
    quote_number = generate_quote_number()
    quote_date = datetime.now()
    validity_days = template_config.get('quotation_settings', {}).get('validity_days', 30)
    valid_until = quote_date + timedelta(days=validity_days)
    tax_rate = template_config.get('quotation_settings', {}).get('tax_rate', 0.10)
    
    # Process line items
    line_items = []
    subtotal = 0.0
    total_savings = 0.0
    
    for i, (req_key, pricing) in enumerate(pricing_results.items(), 1):
        line_item = {
            'line_number': i,
            'product_id': pricing.get('product_id', ''),
            'product_name': pricing.get('product_name', ''),
            'description': pricing.get('product_name', ''),
            'quantity': pricing.get('quantity', 1),
            'unit_price': pricing.get('final_unit_price', 0.0),
            'line_total': pricing.get('total_price', 0.0),
            'brand': pricing.get('brand', ''),
            'model': pricing.get('model', ''),
            'category': pricing.get('category', ''),
            'savings': pricing.get('savings_breakdown', {}).get('total_savings', 0.0)
        }
        
        line_items.append(line_item)
        subtotal += line_item['line_total']
        total_savings += line_item['savings']
    
    # Calculate financials
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount
    
    # Create complete quotation structure
    quotation = {
        'quote_number': quote_number,
        'quote_date': quote_date.strftime('%Y-%m-%d'),
        'valid_until': valid_until.strftime('%Y-%m-%d'),
        'customer_info': {
            'name': customer_name,
            'tier': customer_tier,
            'contact': '',
            'address': '',
            'email': '',
            'phone': ''
        },
        'company_info': template_config['company_info'],
        'rfp_info': {
            'requirements_count': len(requirements),
            'categories': list(set(req.get('category', 'General') for req in requirements)),
            'total_quantity': sum(req.get('quantity', 1) for req in requirements)
        },
        'line_items': line_items,
        'financial_summary': {
            'subtotal': round(subtotal, 2),
            'tax_rate': tax_rate * 100,
            'tax_amount': round(tax_amount, 2),
            'total_amount': round(total_amount, 2),
            'total_items': len(line_items),
            'total_savings': round(total_savings, 2),
            'average_discount': (total_savings / (subtotal + total_savings) * 100) if (subtotal + total_savings) > 0 else 0
        },
        'terms_and_conditions': {
            'payment_terms': template_config.get('quotation_settings', {}).get('payment_terms', 'Net 30 days'),
            'delivery_terms': template_config.get('quotation_settings', {}).get('delivery_terms', 'FOB Origin'),
            'validity': f"Valid until {valid_until.strftime('%B %d, %Y')}",
            'warranty': template_config.get('quotation_settings', {}).get('warranty', '1 Year Manufacturer Warranty'),
            'notes': 'Prices subject to change without notice. All sales final.'
        },
        'created_at': quote_date.isoformat(),
        'status': 'draft',
        'version': '1.0'
    }
    
    return quotation

def generate_html_quotation(quotation: Dict) -> str:
    '''Generate HTML version of quotation'''
    
    company_info = quotation['company_info']
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Quotation #{quotation['quote_number']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #5E81AC;
                padding-bottom: 20px;
            }}
            .company-name {{
                font-size: 24px;
                font-weight: bold;
                color: #2E3440;
                margin-bottom: 10px;
            }}
            .quotation-title {{
                font-size: 20px;
                font-weight: bold;
                margin: 20px 0;
                color: #5E81AC;
            }}
            .info-section {{
                margin-bottom: 20px;
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #5E81AC;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .total-section {{
                float: right;
                width: 50%;
                margin-top: 20px;
            }}
            .total-row {{
                font-weight: bold;
                background-color: #e9ecef;
                border-top: 2px solid #5E81AC;
            }}
            .terms {{
                clear: both;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
            }}
            .terms h4 {{
                color: #5E81AC;
                margin-bottom: 15px;
            }}
            .summary-box {{
                background-color: #e8f4f8;
                border-left: 4px solid #5E81AC;
                padding: 15px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-name">{company_info['name']}</div>
            <p>{company_info['address'].replace(chr(10), '<br>')}</p>
            <p>Phone: {company_info['phone']} | Email: {company_info['email']}</p>
            <p>Website: {company_info['website']} | {company_info['tax_id']}</p>
        </div>
        
        <div class="quotation-title">QUOTATION #{quotation['quote_number']}</div>
        
        <div class="info-section">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <p><strong>Customer:</strong> {quotation['customer_info']['name']}</p>
                    <p><strong>Customer Tier:</strong> {quotation['customer_info']['tier'].title()}</p>
                </div>
                <div>
                    <p><strong>Date:</strong> {quotation['quote_date']}</p>
                    <p><strong>Valid Until:</strong> {quotation['valid_until']}</p>
                </div>
            </div>
        </div>
        
        <div class="summary-box">
            <h4 style="margin: 0 0 10px 0;">RFP Summary</h4>
            <p><strong>Total Requirements:</strong> {quotation['rfp_info']['requirements_count']} items</p>
            <p><strong>Categories:</strong> {', '.join(quotation['rfp_info']['categories'])}</p>
            <p><strong>Total Quantity:</strong> {quotation['rfp_info']['total_quantity']} units</p>
        </div>
        
        <h3>QUOTATION ITEMS</h3>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Description</th>
                    <th>Brand/Model</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th>Savings</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for item in quotation['line_items']:
        brand_model = f"{item.get('brand', '')} {item.get('model', '')}".strip()
        html_content += f'''
                <tr>
                    <td>{item['line_number']}</td>
                    <td>{item['product_name']}</td>
                    <td>{brand_model}</td>
                    <td>{item['quantity']}</td>
                    <td>${item['unit_price']:,.2f}</td>
                    <td>${item.get('savings', 0):,.2f}</td>
                    <td>${item['line_total']:,.2f}</td>
                </tr>
        '''
    
    financial = quotation['financial_summary']
    html_content += f'''
            </tbody>
        </table>
        
        <div class="total-section">
            <table>
                <tr><td>Subtotal:</td><td>${financial['subtotal']:,.2f}</td></tr>
                <tr><td>Total Savings:</td><td style="color: green;">-${financial['total_savings']:,.2f}</td></tr>
                <tr><td>Tax ({financial['tax_rate']:.1f}%):</td><td>${financial['tax_amount']:,.2f}</td></tr>
                <tr class="total-row"><td>TOTAL AMOUNT:</td><td>${financial['total_amount']:,.2f}</td></tr>
            </table>
        </div>
        
        <div class="terms">
            <h4>TERMS AND CONDITIONS</h4>
    '''
    
    terms = quotation['terms_and_conditions']
    html_content += f'''
            <p><strong>Payment Terms:</strong> {terms['payment_terms']}</p>
            <p><strong>Delivery Terms:</strong> {terms['delivery_terms']}</p>
            <p><strong>Validity:</strong> {terms['validity']}</p>
            <p><strong>Warranty:</strong> {terms['warranty']}</p>
            <p><strong>Notes:</strong> {terms['notes']}</p>
        </div>
        
        <div style="text-align: center; margin-top: 40px; font-size: 12px; color: #666;">
            Generated by HORME RFP Processing System - {quotation['created_at']}
        </div>
    </body>
    </html>
    '''
    
    return html_content

def store_quotation_in_database(quotation: Dict, db_path: str = 'quotations.db') -> Dict:
    '''Store quotation in database'''
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create quotations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                customer_tier TEXT DEFAULT 'standard',
                quote_date DATE NOT NULL,
                valid_until DATE,
                status TEXT DEFAULT 'draft',
                subtotal REAL NOT NULL,
                tax_amount REAL NOT NULL,
                total_amount REAL NOT NULL,
                total_items INTEGER DEFAULT 0,
                total_savings REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quotation_data TEXT,
                version TEXT DEFAULT '1.0'
            )
        ''')
        
        # Create quotation_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotation_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                product_id TEXT,
                product_name TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                category TEXT,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                savings REAL DEFAULT 0.0,
                FOREIGN KEY (quotation_id) REFERENCES quotations (id)
            )
        ''')
        
        # Insert quotation
        financial = quotation['financial_summary']
        cursor.execute('''
            INSERT OR REPLACE INTO quotations 
            (quote_number, customer_name, customer_tier, quote_date, valid_until, 
             status, subtotal, tax_amount, total_amount, total_items, total_savings,
             quotation_data, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            quotation['quote_number'],
            quotation['customer_info']['name'],
            quotation['customer_info']['tier'],
            quotation['quote_date'],
            quotation['valid_until'],
            quotation['status'],
            financial['subtotal'],
            financial['tax_amount'],
            financial['total_amount'],
            financial['total_items'],
            financial['total_savings'],
            json.dumps(quotation),
            quotation['version']
        ))
        
        quotation_id = cursor.lastrowid
        
        # Insert line items
        for item in quotation['line_items']:
            cursor.execute('''
                INSERT INTO quotation_items 
                (quotation_id, line_number, product_id, product_name, brand, model,
                 category, quantity, unit_price, line_total, savings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                quotation_id, item['line_number'], item['product_id'],
                item['product_name'], item.get('brand', ''), item.get('model', ''),
                item.get('category', ''), item['quantity'], item['unit_price'],
                item['line_total'], item.get('savings', 0.0)
            ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'quotation_id': quotation_id,
            'database_path': db_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Database storage failed: {str(e)}'
        }

# Execute complete quotation generation
if 'requirements' in locals() and 'pricing_results' in locals():
    # Create quotation
    quotation = create_complete_quotation(
        requirements,
        pricing_results.get('pricing_results', {}),
        customer_name if 'customer_name' in locals() else 'Valued Customer',
        customer_tier if 'customer_tier' in locals() else 'standard',
        template_config if 'template_config' in locals() else None
    )
    
    # Generate HTML
    html_content = generate_html_quotation(quotation)
    
    # Store in database
    storage_result = store_quotation_in_database(quotation)
    
    result = {
        'quotation': quotation,
        'html_content': html_content,
        'quote_number': quotation['quote_number'],
        'total_amount': quotation['financial_summary']['total_amount'],
        'storage': storage_result,
        'success': True
    }
else:
    result = {
        'quotation': {},
        'html_content': '',
        'storage': {'success': False},
        'success': False,
        'error': 'Missing requirements or pricing_results data'
    }
"""
        })
        
        return workflow.build()
    
    def execute_quotation_generation(self, requirements: List[Dict[str, Any]], 
                                   pricing_results: Dict[str, Any],
                                   customer_name: str = 'Valued Customer',
                                   customer_tier: str = 'standard') -> Dict[str, Any]:
        """Execute the complete quotation generation workflow."""
        try:
            workflow = self.create_complete_quotation_workflow()
            
            # Prepare parameters
            params = {
                'requirements': requirements,
                'pricing_results': pricing_results,
                'customer_name': customer_name,
                'customer_tier': customer_tier,
                'template_config': self.template_config
            }
            
            # Execute workflow
            results, run_id = self.runtime.execute(workflow, parameters=params)
            
            return {
                'success': True,
                'results': results,
                'run_id': run_id
            }
            
        except Exception as e:
            logger.error(f"Quotation generation workflow failed: {e}")
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
        }
    ]
    
    sample_pricing_results = {
        'pricing_results': {
            'Power Tools_1234': {
                'product_id': 'DWT-001',
                'product_name': 'DEWALT DCD791D2 20V MAX XR Cordless Drill',
                'category': 'Power Tools',
                'brand': 'DEWALT',
                'quantity': 50,
                'final_unit_price': 179.99,
                'total_price': 8999.50,
                'savings_breakdown': {'total_savings': 900.50}
            }
        }
    }
    
    quotation_generator = QuotationGenerationWorkflow()
    result = quotation_generator.execute_quotation_generation(
        sample_requirements, 
        sample_pricing_results,
        customer_name='Demo Customer',
        customer_tier='enterprise'
    )
    
    if result['success']:
        quotation = result['results']['quotation']
        print("Quotation Generation Results:")
        print(f"- Quote Number: {quotation['quote_number']}")
        print(f"- Total Amount: ${quotation['financial_summary']['total_amount']:,.2f}")
        print(f"- Items: {quotation['financial_summary']['total_items']}")
        print(f"- Storage: {result['results']['storage']['success']}")
        print(f"- HTML Generated: {len(result['results']['html_content'])} characters")
    else:
        print(f"Quotation generation failed: {result['error']}")