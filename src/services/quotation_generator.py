"""
Quotation Generation Service
Generates professional quotations with PDF export
NO MOCK DATA - All data from real database and matched products
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import asyncpg

logger = logging.getLogger(__name__)


class QuotationGenerator:
    """Generates quotations and stores in database"""

    def __init__(self):
        self.company_info = {
            'name': os.getenv('COMPANY_NAME', 'HORME Hardware Pte Ltd'),
            'address': os.getenv('COMPANY_ADDRESS', '21 Penjuru Lane, Singapore 609197'),
            'phone': os.getenv('COMPANY_PHONE', '+65 6262 6662'),
            'email': os.getenv('COMPANY_EMAIL', 'sales@horme.com.sg'),
            'website': os.getenv('COMPANY_WEBSITE', 'www.horme.com.sg'),
            'tax_id': os.getenv('COMPANY_TAX_ID', 'GST Reg No: M2-0095504-0')
        }

    async def generate_quotation(
        self,
        document_id: int,
        requirements: Dict[str, Any],
        matched_products: List[Dict[str, Any]],
        pricing: Dict[str, Any],
        db_pool: asyncpg.Pool
    ) -> int:
        """
        Generate quotation and store in database

        Args:
            document_id: Source document ID
            requirements: Extracted requirements
            matched_products: Products matched to requirements
            pricing: Pricing calculation results
            db_pool: Database connection pool

        Returns:
            Created quotation ID
        """
        logger.info(f"Generating quotation for document {document_id}")

        try:
            # Generate unique quotation number
            quote_number = await self._generate_quote_number(db_pool)

            # Get customer info from requirements
            customer_name = requirements.get('customer_name') or 'Valued Customer'
            project_name = requirements.get('project_name') or f'RFP {document_id}'

            # Calculate expiry date (30 days validity)
            expiry_date = datetime.utcnow() + timedelta(days=30)

            # Create quotation record
            async with db_pool.acquire() as conn:
                quotation_id = await conn.fetchval("""
                    INSERT INTO quotes (
                        quote_number,
                        document_id,
                        customer_name,
                        title,
                        description,
                        status,
                        created_date,
                        expiry_date,
                        currency,
                        subtotal,
                        discount_amount,
                        tax_amount,
                        total_amount,
                        terms_and_conditions,
                        notes
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    ) RETURNING id
                """,
                    quote_number,
                    document_id,
                    customer_name,
                    f"Quotation for {project_name}",
                    f"Generated quotation based on RFP requirements",
                    'draft',
                    datetime.utcnow(),
                    expiry_date,
                    pricing['currency'],
                    pricing['subtotal'],
                    pricing['discount_amount'],
                    pricing['tax_amount'],
                    pricing['total'],
                    self._get_terms_and_conditions(),
                    f"Valid until {expiry_date.strftime('%Y-%m-%d')}"
                )

                # Insert line items
                for product in matched_products:
                    await conn.execute("""
                        INSERT INTO quote_items (
                            quote_id,
                            line_number,
                            product_id,
                            product_name,
                            product_code,
                            description,
                            quantity,
                            unit,
                            unit_price,
                            discount_percent,
                            line_total
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                        )
                    """,
                        quotation_id,
                        product['line_number'],
                        product.get('product_id'),
                        product['product_name'],
                        product.get('product_code', ''),
                        product['requirement_description'],
                        product['quantity'],
                        product['unit'],
                        product['unit_price'],
                        0.0,  # No item-level discount for now
                        product['line_total']
                    )

                logger.info(f"Created quotation {quote_number} (ID: {quotation_id}) with {len(matched_products)} items")

                # Update document with quotation link
                await conn.execute("""
                    UPDATE documents
                    SET quotation_id = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """, quotation_id, document_id)

                return quotation_id

        except Exception as e:
            logger.error(f"Error generating quotation: {str(e)}", exc_info=True)
            raise

    async def _generate_quote_number(self, db_pool: asyncpg.Pool) -> str:
        """Generate unique quotation number in format Q-YYYYMMDD-NNNN"""

        date_prefix = datetime.utcnow().strftime('%Y%m%d')

        async with db_pool.acquire() as conn:
            # Get today's quote count
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM quotes
                WHERE quote_number LIKE $1
            """, f"Q-{date_prefix}-%")

            # Increment and format
            sequence = (count or 0) + 1
            quote_number = f"Q-{date_prefix}-{sequence:04d}"

            return quote_number

    def _get_terms_and_conditions(self) -> str:
        """Get standard terms and conditions"""

        return """
TERMS AND CONDITIONS:

1. PRICES: All prices are in Singapore Dollars (SGD) unless otherwise stated.
2. VALIDITY: This quotation is valid for 30 days from the date of issue.
3. PAYMENT TERMS: Net 30 days from invoice date.
4. DELIVERY: Delivery timeline to be confirmed upon order placement.
5. WARRANTY: All products carry manufacturer's standard warranty.
6. TAXES: Prices exclude GST unless otherwise stated. GST will be added to the final invoice.
7. CANCELLATION: Orders once placed cannot be cancelled without written consent.
8. ACCEPTANCE: This quotation is subject to our standard terms and conditions of sale.

For any queries, please contact us at sales@horme.com.sg or +65 6262 6662.
        """.strip()

    async def generate_pdf(
        self,
        quotation_id: int,
        db_pool: asyncpg.Pool
    ) -> str:
        """
        Generate PDF for quotation

        Args:
            quotation_id: Quotation database ID
            db_pool: Database connection pool

        Returns:
            Path to generated PDF file
        """
        logger.info(f"Generating PDF for quotation {quotation_id}")

        try:
            # Get quotation data
            async with db_pool.acquire() as conn:
                quote = await conn.fetchrow("""
                    SELECT * FROM quotes WHERE id = $1
                """, quotation_id)

                if not quote:
                    raise ValueError(f"Quotation {quotation_id} not found")

                # Get line items
                items = await conn.fetch("""
                    SELECT * FROM quote_items
                    WHERE quote_id = $1
                    ORDER BY line_number
                """, quotation_id)

            # Generate PDF using reportlab
            pdf_path = await self._create_pdf(quote, items)

            # Update quotation with PDF path
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE quotes
                    SET pdf_path = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """, pdf_path, quotation_id)

            logger.info(f"Generated PDF: {pdf_path}")

            return pdf_path

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
            raise

    async def _create_pdf(self, quote: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """Create PDF document using reportlab"""

        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors

            # Create PDF directory
            pdf_dir = "/app/pdfs"
            os.makedirs(pdf_dir, exist_ok=True)

            # PDF filename
            pdf_filename = f"{quote['quote_number']}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)

            # Create PDF
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            story = []

            styles = getSampleStyleSheet()

            # Company header
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#C41E3A')  # Horme red
            )

            story.append(Paragraph(self.company_info['name'], header_style))
            story.append(Paragraph(self.company_info['address'], styles['Normal']))
            story.append(Paragraph(f"Tel: {self.company_info['phone']} | Email: {self.company_info['email']}", styles['Normal']))
            story.append(Paragraph(self.company_info['tax_id'], styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # Quotation title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#333333')
            )

            story.append(Paragraph("QUOTATION", title_style))
            story.append(Spacer(1, 0.2*inch))

            # Quotation details
            details_data = [
                ['Quotation No:', quote['quote_number']],
                ['Date:', quote['created_date'].strftime('%Y-%m-%d')],
                ['Valid Until:', quote['expiry_date'].strftime('%Y-%m-%d')],
                ['Customer:', quote['customer_name']],
                ['Project:', quote['title']]
            ]

            details_table = Table(details_data, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            story.append(details_table)
            story.append(Spacer(1, 0.3*inch))

            # Line items table
            table_data = [['#', 'Description', 'Qty', 'Unit', 'Unit Price', 'Total']]

            for item in items:
                table_data.append([
                    str(item['line_number']),
                    f"{item['product_name']}\n{item['description']}" if item['description'] else item['product_name'],
                    str(item['quantity']),
                    item['unit'],
                    f"{item['unit_price']:.2f}",
                    f"{item['line_total']:.2f}"
                ])

            items_table = Table(table_data, colWidths=[0.4*inch, 3*inch, 0.6*inch, 0.6*inch, 1*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            story.append(items_table)
            story.append(Spacer(1, 0.3*inch))

            # Pricing summary
            summary_data = [
                ['Subtotal:', f"{quote['currency']} {quote['subtotal']:.2f}"],
                ['Discount:', f"{quote['currency']} {quote['discount_amount']:.2f}"],
                ['GST (10%):', f"{quote['currency']} {quote['tax_amount']:.2f}"],
                ['', ''],
                ['TOTAL:', f"{quote['currency']} {quote['total_amount']:.2f}"]
            ]

            summary_table = Table(summary_data, colWidths=[4.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('LINEABOVE', (0, -2), (-1, -2), 1, colors.black),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ]))

            story.append(summary_table)
            story.append(Spacer(1, 0.4*inch))

            # Terms and conditions
            story.append(Paragraph("Terms and Conditions", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))

            terms_paragraphs = quote['terms_and_conditions'].split('\n')
            for para in terms_paragraphs:
                if para.strip():
                    story.append(Paragraph(para, styles['Normal']))

            # Build PDF
            doc.build(story)

            return pdf_path

        except ImportError:
            logger.error("reportlab not installed, cannot generate PDF")
            raise ImportError("reportlab library required for PDF generation (pip install reportlab)")
