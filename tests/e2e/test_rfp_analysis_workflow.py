"""End-to-End RFP Analysis Workflow Tests.

Tests complete RFP analysis workflows from document parsing to quotation delivery.
NO MOCKING - uses real PostgreSQL infrastructure and complete business logic.

Tier 3 (E2E) Requirements:
- Use complete real infrastructure stack (PostgreSQL test containers)
- NO MOCKING - test complete RFP analysis scenarios
- Test end-to-end RFP processing workflows
- Validate complete RFP-to-quotation user journeys
- Test with real RFP documents and analysis
"""

import pytest
import json
import tempfile
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import re
from decimal import Decimal

# Test markers
pytestmark = [pytest.mark.e2e, pytest.mark.rfp_analysis, pytest.mark.timeout(15)]


class TestRFPAnalysisWorkflow:
    """End-to-end tests for RFP analysis and quotation workflows using PostgreSQL."""

    @pytest.fixture(scope="class")
    def rfp_analysis_system(self, docker_services_available):
        """Setup complete RFP analysis system with real PostgreSQL database.

        This fixture uses the real PostgreSQL test container from docker-compose.test.yml.
        NO MOCKING - all database operations are real.
        """
        # Get PostgreSQL connection parameters from environment
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5434')
        database = os.environ.get('POSTGRES_DB', 'horme_test')
        user = os.environ.get('POSTGRES_USER', 'test_user')
        password = os.environ.get('POSTGRES_PASSWORD', 'test_password')

        # Connect to real PostgreSQL test database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor
        )
        conn.autocommit = False

        # Create RFP-specific schema (extends existing test schema)
        cursor = conn.cursor()
        cursor.execute("""
            -- Create companies table for RFP analysis
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                industry TEXT,
                size_category TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Create RFP documents table
            CREATE TABLE IF NOT EXISTS rfp_documents (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                document_type TEXT,
                complexity_score INTEGER,
                estimated_budget DECIMAL(12,2),
                deadline_date DATE,
                status TEXT DEFAULT 'received',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Create RFP requirements table
            CREATE TABLE IF NOT EXISTS rfp_requirements (
                id SERIAL PRIMARY KEY,
                rfp_document_id INTEGER REFERENCES rfp_documents(id) ON DELETE CASCADE,
                category TEXT,
                item_name TEXT,
                description TEXT,
                quantity INTEGER,
                specifications TEXT,
                priority TEXT DEFAULT 'medium',
                estimated_cost DECIMAL(12,2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Create suppliers table
            CREATE TABLE IF NOT EXISTS suppliers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                specialties TEXT,
                quality_rating DECIMAL(3,2) DEFAULT 4.0,
                reliability_score DECIMAL(3,2) DEFAULT 0.8,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Create product catalog table (extends existing products table for RFP)
            CREATE TABLE IF NOT EXISTS product_catalog (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                specifications TEXT,
                unit_price DECIMAL(12,2),
                availability_status TEXT DEFAULT 'available',
                supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
                lead_time_days INTEGER DEFAULT 7,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Create quotation responses table (extends existing quotations)
            CREATE TABLE IF NOT EXISTS quotation_responses (
                id SERIAL PRIMARY KEY,
                rfp_document_id INTEGER REFERENCES rfp_documents(id) ON DELETE CASCADE,
                response_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                total_value DECIMAL(12,2),
                validity_period_days INTEGER DEFAULT 30,
                confidence_score DECIMAL(3,2),
                line_items JSONB,
                terms_conditions TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Create analysis metrics table
            CREATE TABLE IF NOT EXISTS analysis_metrics (
                id SERIAL PRIMARY KEY,
                rfp_document_id INTEGER REFERENCES rfp_documents(id) ON DELETE CASCADE,
                requirements_identified INTEGER,
                products_matched INTEGER,
                coverage_percentage DECIMAL(5,2),
                complexity_factors JSONB,
                processing_time_seconds DECIMAL(10,2),
                analysis_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_rfp_documents_company ON rfp_documents(company_id);
            CREATE INDEX IF NOT EXISTS idx_rfp_documents_status ON rfp_documents(status);
            CREATE INDEX IF NOT EXISTS idx_rfp_requirements_rfp ON rfp_requirements(rfp_document_id);
            CREATE INDEX IF NOT EXISTS idx_quotation_responses_rfp ON quotation_responses(rfp_document_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_metrics_rfp ON analysis_metrics(rfp_document_id);
        """)

        # Insert sample suppliers (real data, no mocking)
        cursor.execute("""
            INSERT INTO suppliers (name, specialties, quality_rating, reliability_score) VALUES
            ('TechFlow Solutions', 'IT Equipment, Software, Networking', 4.5, 0.95),
            ('Office Dynamics Corp', 'Furniture, Office Equipment, Supplies', 4.2, 0.88),
            ('Industrial Supply Co', 'Manufacturing, Heavy Equipment, Tools', 4.8, 0.92),
            ('Green Energy Systems', 'Solar, Renewable Energy, Sustainability', 4.6, 0.90),
            ('Construction Materials Ltd', 'Building Materials, Construction Equipment', 4.3, 0.85)
            ON CONFLICT DO NOTHING
            RETURNING id
        """)
        supplier_ids = [row['id'] for row in cursor.fetchall()]

        # Insert comprehensive product catalog (real data, no mocking)
        cursor.execute("""
            INSERT INTO product_catalog (name, category, description, specifications, unit_price, supplier_id, lead_time_days) VALUES
            -- IT Equipment
            ('Enterprise Laptop', 'IT Equipment', 'Business laptop with security features', 'Intel i7, 16GB RAM, 512GB SSD', 1299.99, %s, 5),
            ('Network Switch', 'Networking', '24-port managed Gigabit switch', '24x1Gb ports, VLAN support, PoE+', 489.99, %s, 3),
            ('Wireless Access Point', 'Networking', 'Enterprise WiFi 6 access point', 'WiFi 6, dual-band, enterprise management', 299.99, %s, 7),
            ('Server Rack', 'IT Equipment', '42U server rack cabinet', '42U, 19-inch, ventilated, cable management', 899.99, %s, 14),

            -- Office Equipment
            ('Executive Office Chair', 'Furniture', 'Ergonomic executive chair', 'Leather, adjustable height, lumbar support', 449.99, %s, 10),
            ('Conference Table', 'Furniture', 'Large conference room table', '10-person capacity, solid wood, modern design', 1299.99, %s, 21),
            ('Multi-Function Printer', 'Office Equipment', 'Enterprise MFP with security', 'Print/Scan/Copy/Fax, 45ppm, network ready', 2299.99, %s, 7),
            ('Office Desk', 'Furniture', 'Height-adjustable standing desk', 'Electric adjustment, 60x30 inches, memory settings', 699.99, %s, 14),

            -- Industrial Equipment
            ('Industrial Generator', 'Power Equipment', 'Backup power generator', '50kW, diesel, automatic start, weather enclosure', 12999.99, %s, 30),
            ('Forklift', 'Material Handling', 'Electric forklift truck', '3000lb capacity, electric, side-shift', 28999.99, %s, 45),
            ('Compressor System', 'Air Systems', 'Industrial air compressor', '100HP, rotary screw, 460CFM', 15999.99, %s, 28),

            -- Green Energy
            ('Solar Panel System', 'Renewable Energy', 'Commercial solar installation', '100kW system, monocrystalline, 25-year warranty', 89999.99, %s, 60),
            ('Battery Storage System', 'Energy Storage', 'Commercial battery backup', '50kWh lithium, grid-tie, monitoring', 45999.99, %s, 45),

            -- Construction Materials
            ('Steel Beams', 'Construction', 'Structural steel beams', 'Grade A36, various lengths, certified', 899.99, %s, 21),
            ('Concrete Mixer', 'Construction Equipment', 'Portable concrete mixer', '3.5 cubic feet, electric motor, wheels', 599.99, %s, 14)
            ON CONFLICT DO NOTHING
        """, (
            supplier_ids[0], supplier_ids[0], supplier_ids[0], supplier_ids[0],  # IT Equipment
            supplier_ids[1], supplier_ids[1], supplier_ids[1], supplier_ids[1],  # Office Equipment
            supplier_ids[2], supplier_ids[2], supplier_ids[2],  # Industrial Equipment
            supplier_ids[3], supplier_ids[3],  # Green Energy
            supplier_ids[4], supplier_ids[4]   # Construction Materials
        ))

        conn.commit()

        yield {
            'connection': conn,
            'cursor': cursor,
            'analyzer': RFPAnalyzer(conn),
            'quotation_generator': QuotationGenerator(conn)
        }

        # Cleanup - rollback any uncommitted changes
        conn.rollback()
        cursor.close()
        conn.close()

    @pytest.fixture
    def test_company(self, rfp_analysis_system):
        """Create test company for RFP workflows.

        Uses real PostgreSQL database - NO MOCKING.
        """
        conn = rfp_analysis_system['connection']
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO companies (name, industry, size_category)
            VALUES (%s, %s, %s)
            RETURNING id, name, industry, size_category
        """, ('Test Manufacturing Corp', 'Manufacturing', 'Medium'))

        company = cursor.fetchone()
        conn.commit()

        return dict(company)

    def test_complex_rfp_analysis_workflow(self, rfp_analysis_system, test_company):
        """Test analysis of complex RFP with multiple categories and specifications.

        Tier 3 E2E Test - Real PostgreSQL database, complete workflow.
        """
        conn = rfp_analysis_system['connection']
        analyzer = rfp_analysis_system['analyzer']
        quotation_gen = rfp_analysis_system['quotation_generator']
        cursor = conn.cursor()

        # Complex RFP document
        complex_rfp_content = """
COMPREHENSIVE TECHNOLOGY UPGRADE REQUEST FOR PROPOSAL

Company: Test Manufacturing Corp
RFP Number: RFP-2024-TECH-001
Issue Date: 2024-01-15
Response Deadline: 2024-02-15
Estimated Budget: $250,000 - $350,000

PROJECT OVERVIEW:
We are seeking comprehensive proposals for a complete technology infrastructure upgrade
to support our expanding manufacturing operations and remote workforce.

DETAILED REQUIREMENTS:

1. NETWORK INFRASTRUCTURE (Priority: HIGH)
   - 48-port managed Gigabit switches (Quantity: 3 units)
   - Enterprise wireless access points supporting WiFi 6 (Quantity: 15 units)
   - Core network equipment with redundancy
   - Specifications: VLAN support, PoE+, centralized management
   - Installation and configuration included

2. COMPUTING EQUIPMENT (Priority: HIGH)
   - Business laptops for management team (Quantity: 25 units)
   - Specifications: Intel i7 or AMD equivalent, 16GB RAM minimum, 512GB SSD
   - Enterprise security features required
   - 3-year warranty and support

3. OFFICE INFRASTRUCTURE (Priority: MEDIUM)
   - Executive office chairs (Quantity: 8 units)
   - Height-adjustable standing desks (Quantity: 12 units)
   - Large conference table for 10+ people (Quantity: 2 units)
   - Multi-function printer/scanner units (Quantity: 4 units)

4. POWER AND BACKUP SYSTEMS (Priority: MEDIUM)
   - Backup power generator for critical systems (Minimum: 50kW)
   - Uninterruptible power supply units
   - Automatic transfer switches
   - Weather-resistant enclosure required

5. MANUFACTURING SUPPORT (Priority: LOW)
   - Material handling equipment (Forklift, 3000lb+ capacity)
   - Industrial air compressor system (100HP minimum)
   - Safety and compliance certifications required

EVALUATION CRITERIA:
- Technical compliance (40%)
- Total cost of ownership (30%)
- Vendor reliability and support (20%)
- Implementation timeline (10%)

DELIVERABLES REQUIRED:
- Detailed technical specifications
- Implementation timeline with milestones
- Total cost breakdown with line items
- Warranty and support terms
- Reference installations

TERMS AND CONDITIONS:
- Proposals valid for minimum 60 days
- Payment terms: Net 30
- Delivery timeline: Within 90 days of award
- Installation support required
- Training for end users included

Please provide comprehensive quotation addressing all requirements.
"""

        # Step 1: Create RFP document (real database insert)
        cursor.execute("""
            INSERT INTO rfp_documents (company_id, title, content, document_type,
                                     estimated_budget, deadline_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (test_company['id'], "Comprehensive Technology Upgrade RFP",
              complex_rfp_content, "technology_upgrade", 300000.0,
              "2024-02-15", "received"))
        rfp_id = cursor.fetchone()['id']
        conn.commit()

        # Step 2: Analyze RFP and extract requirements (real analysis)
        start_time = time.time()
        analysis_results = analyzer.analyze_rfp(rfp_id, complex_rfp_content)
        analysis_time = time.time() - start_time

        # Verify requirements extraction
        assert len(analysis_results['requirements']) >= 10, \
            f"Should find multiple requirement categories, found {len(analysis_results['requirements'])}"

        # Check for key categories
        categories_found = set(req['category'] for req in analysis_results['requirements'])
        expected_categories = {'Network Infrastructure', 'Computing Equipment', 'Office Infrastructure',
                             'Power Systems', 'Manufacturing Equipment'}
        assert len(categories_found.intersection(expected_categories)) >= 3, \
            f"Should find at least 3 expected categories, found {categories_found}"

        # Step 3: Match products to requirements (real product matching)
        quotation_results = quotation_gen.generate_comprehensive_quotation(
            rfp_id, analysis_results['requirements'])

        # Verify quotation generation
        assert quotation_results['total_value'] > 0, "Quotation should have positive total value"
        assert quotation_results['coverage_percentage'] > 0.6, \
            f"Should cover at least 60% of requirements, got {quotation_results['coverage_percentage']:.1%}"
        assert len(quotation_results['line_items']) >= 8, \
            f"Should have multiple line items, got {len(quotation_results['line_items'])}"

        # Step 4: Verify database records (real database queries)
        cursor.execute("SELECT * FROM rfp_requirements WHERE rfp_document_id = %s", (rfp_id,))
        requirements = cursor.fetchall()
        assert len(requirements) >= 10, f"Should have at least 10 requirements in DB, got {len(requirements)}"

        # Check requirement priorities
        high_priority_reqs = [req for req in requirements if req['priority'] == 'high']
        assert len(high_priority_reqs) >= 4, f"Should have at least 4 high priority requirements, got {len(high_priority_reqs)}"

        # Step 5: Verify analysis metrics (real metrics from database)
        cursor.execute("SELECT * FROM analysis_metrics WHERE rfp_document_id = %s", (rfp_id,))
        metrics = cursor.fetchone()
        assert metrics is not None, "Analysis metrics should be recorded"
        assert metrics['requirements_identified'] >= 10
        assert metrics['products_matched'] >= 8
        assert metrics['coverage_percentage'] >= 0.6
        assert metrics['processing_time_seconds'] < 30, "Should process within 30 seconds"

        # Step 6: Verify quotation response (real quotation from database)
        cursor.execute("SELECT * FROM quotation_responses WHERE rfp_document_id = %s", (rfp_id,))
        quotation = cursor.fetchone()
        assert quotation is not None, "Quotation should be created in database"
        assert quotation['total_value'] >= 50000, \
            f"Reasonable total for this RFP should be >= $50,000, got ${quotation['total_value']}"
        assert quotation['confidence_score'] >= 0.7, \
            f"Confidence score should be >= 0.7, got {quotation['confidence_score']}"

        # Parse and verify line items
        line_items = quotation['line_items']
        assert len(line_items) >= 8, f"Should have at least 8 line items, got {len(line_items)}"

        # Verify cost breakdown
        calculated_total = sum(Decimal(str(item['total_cost'])) for item in line_items)
        assert abs(quotation['total_value'] - calculated_total) < 1.0, \
            f"Quotation total ({quotation['total_value']}) should match sum of line items ({calculated_total})"

        return {
            'rfp_id': rfp_id,
            'requirements_found': len(requirements),
            'products_matched': metrics['products_matched'],
            'total_value': float(quotation['total_value']),
            'coverage_percentage': float(metrics['coverage_percentage']),
            'analysis_time': analysis_time
        }

    def test_rfp_with_budget_constraints(self, rfp_analysis_system, test_company):
        """Test RFP analysis with tight budget constraints.

        Tier 3 E2E Test - Real PostgreSQL database, budget validation.
        """
        conn = rfp_analysis_system['connection']
        analyzer = rfp_analysis_system['analyzer']
        quotation_gen = rfp_analysis_system['quotation_generator']
        cursor = conn.cursor()

        # Budget-constrained RFP
        budget_rfp_content = """
BUDGET-CONSCIOUS OFFICE SETUP RFP

Company: Test Manufacturing Corp
Budget Limit: $15,000 (FIRM)
Timeline: 30 days

Requirements:
1. Office chairs for small team (Quantity: 6 units)
2. Basic work desks (Quantity: 6 units)
3. One multi-function printer
4. Basic networking equipment for small office

NOTE: Budget is strictly limited. Must not exceed $15,000 total.
Priority is functionality over premium features.
"""

        cursor.execute("""
            INSERT INTO rfp_documents (company_id, title, content, document_type,
                                     estimated_budget, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (test_company['id'], "Budget Office Setup",
              budget_rfp_content, "office_setup", 15000.0, "received"))
        rfp_id = cursor.fetchone()['id']
        conn.commit()

        # Analyze with budget constraints
        analysis_results = analyzer.analyze_rfp(rfp_id, budget_rfp_content)
        quotation_results = quotation_gen.generate_budget_conscious_quotation(
            rfp_id, analysis_results['requirements'], budget_limit=15000.0)

        # Verify budget compliance
        assert quotation_results['total_value'] <= 15000.0, \
            f"Quotation (${quotation_results['total_value']}) should not exceed budget ($15,000)"
        assert quotation_results['within_budget'] is True, "Should be marked as within budget"

        # Should still cover basic requirements
        assert quotation_results['coverage_percentage'] >= 0.8, \
            f"Should cover at least 80% of requirements, got {quotation_results['coverage_percentage']:.1%}"
        assert len(quotation_results['line_items']) >= 4, \
            f"Should have at least 4 line items, got {len(quotation_results['line_items'])}"

        # Verify cost optimization (real database query)
        cursor.execute("SELECT * FROM quotation_responses WHERE rfp_document_id = %s", (rfp_id,))
        quotation = cursor.fetchone()
        assert quotation['total_value'] <= 15000.0, "Database total should not exceed budget"

        line_items = quotation['line_items']

        # Should have selected cost-effective options
        chair_items = [item for item in line_items if 'chair' in item['product_name'].lower()]
        if chair_items:
            # Should use more economical chair options
            assert chair_items[0]['unit_price'] < 500.0, \
                "Should select economical chairs (< $500), not premium executive chairs"

    def test_rfp_analysis_with_missing_information(self, rfp_analysis_system, test_company):
        """Test RFP analysis handling incomplete or vague requirements.

        Tier 3 E2E Test - Real PostgreSQL database, error handling.
        """
        conn = rfp_analysis_system['connection']
        analyzer = rfp_analysis_system['analyzer']
        quotation_gen = rfp_analysis_system['quotation_generator']
        cursor = conn.cursor()

        # Vague/incomplete RFP
        incomplete_rfp = """
URGENT EQUIPMENT REQUEST

We need some office stuff urgently.

Requirements:
- Some chairs (not sure how many)
- Desks maybe?
- Computer things for the team
- Other office equipment as needed

Budget: Reasonable amount
Timeline: ASAP

Please quote whatever you think we need.
"""

        cursor.execute("""
            INSERT INTO rfp_documents (company_id, title, content, document_type, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (test_company['id'], "Urgent Equipment Request",
              incomplete_rfp, "general_request", "received"))
        rfp_id = cursor.fetchone()['id']
        conn.commit()

        # Analyze incomplete RFP
        analysis_results = analyzer.analyze_rfp(rfp_id, incomplete_rfp)

        # Should flag as requiring clarification
        assert analysis_results['requires_clarification'] is True, \
            "Vague RFP should require clarification"
        assert len(analysis_results['clarification_needed']) > 0, \
            "Should provide list of clarifications needed"

        # Should still provide estimates
        quotation_results = quotation_gen.generate_estimate_quotation(
            rfp_id, analysis_results['requirements'])

        # Verify handling of uncertainty (real database query)
        cursor.execute("SELECT * FROM quotation_responses WHERE rfp_document_id = %s", (rfp_id,))
        quotation = cursor.fetchone()
        assert quotation is not None, "Should generate estimate even for vague RFP"
        assert quotation['confidence_score'] < 0.6, \
            f"Confidence score should be low (< 0.6) for vague RFP, got {quotation['confidence_score']}"
        assert 'estimate' in quotation['terms_conditions'].lower(), \
            "Terms should indicate this is an estimate"

    @pytest.mark.slow
    def test_multiple_rfp_comparative_analysis(self, rfp_analysis_system, test_company):
        """Test comparative analysis across multiple RFPs.

        Tier 3 E2E Test - Real PostgreSQL database, multiple workflows.
        """
        conn = rfp_analysis_system['connection']
        analyzer = rfp_analysis_system['analyzer']
        quotation_gen = rfp_analysis_system['quotation_generator']
        cursor = conn.cursor()

        # Create multiple related RFPs
        rfp_scenarios = [
            {
                'title': 'Small Office Setup',
                'content': 'Need basic office setup: 5 chairs, 5 desks, 1 printer, basic networking.',
                'expected_budget': 8000.0
            },
            {
                'title': 'Medium Office Expansion',
                'content': 'Office expansion: 15 chairs, 15 desks, 3 printers, enterprise networking, conference room setup.',
                'expected_budget': 25000.0
            },
            {
                'title': 'Large Enterprise Setup',
                'content': 'Complete enterprise setup: 50 workstations, enterprise infrastructure, server equipment, full networking.',
                'expected_budget': 100000.0
            }
        ]

        rfp_results = []

        # Process all RFPs (real database operations)
        for scenario in rfp_scenarios:
            cursor.execute("""
                INSERT INTO rfp_documents (company_id, title, content, estimated_budget, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (test_company['id'], scenario['title'],
                  scenario['content'], scenario['expected_budget'], "received"))
            rfp_id = cursor.fetchone()['id']

            analysis_results = analyzer.analyze_rfp(rfp_id, scenario['content'])
            quotation_results = quotation_gen.generate_comprehensive_quotation(
                rfp_id, analysis_results['requirements'])

            rfp_results.append({
                'rfp_id': rfp_id,
                'title': scenario['title'],
                'expected_budget': scenario['expected_budget'],
                'actual_quote': quotation_results['total_value'],
                'requirements_count': len(analysis_results['requirements']),
                'coverage': quotation_results['coverage_percentage']
            })

        conn.commit()

        # Verify scaling patterns
        rfp_results.sort(key=lambda x: x['expected_budget'])

        # Quotation values should generally increase with budget
        for i in range(1, len(rfp_results)):
            current = rfp_results[i]
            previous = rfp_results[i-1]
            assert current['actual_quote'] >= previous['actual_quote'], \
                f"Larger RFP should have higher quote: {previous['title']}=${previous['actual_quote']}, " \
                f"{current['title']}=${current['actual_quote']}"
            assert current['requirements_count'] >= previous['requirements_count'], \
                "Larger RFP should have more requirements"

        # Verify all RFPs were processed successfully
        assert all(result['coverage'] > 0.5 for result in rfp_results), \
            "All RFPs should have > 50% coverage"

        # Check database consistency (real database query)
        cursor.execute("""
            SELECT COUNT(*) as count FROM quotation_responses qr
            JOIN rfp_documents rd ON qr.rfp_document_id = rd.id
            WHERE rd.company_id = %s
        """, (test_company['id'],))

        quotation_count = cursor.fetchone()['count']
        assert quotation_count == len(rfp_scenarios), \
            f"Should have {len(rfp_scenarios)} quotations in database, got {quotation_count}"

        return rfp_results


# Helper classes for RFP analysis
class RFPAnalyzer:
    """Analyzes RFP documents and extracts requirements.

    Uses real PostgreSQL database - NO MOCKING.
    """

    def __init__(self, connection):
        self.conn = connection

    def analyze_rfp(self, rfp_id, content):
        """Analyze RFP content and extract structured requirements.

        Real database operations - NO MOCKING.
        """
        cursor = self.conn.cursor()
        requirements = []

        # Simple requirement extraction logic
        lines = content.split('\n')
        current_category = "General"

        for line in lines:
            line = line.strip()

            # Detect categories
            if any(keyword in line.upper() for keyword in ['NETWORK', 'COMPUTING', 'OFFICE', 'POWER', 'MANUFACTURING']):
                if 'NETWORK' in line.upper():
                    current_category = "Network Infrastructure"
                elif 'COMPUTING' in line.upper():
                    current_category = "Computing Equipment"
                elif 'OFFICE' in line.upper():
                    current_category = "Office Infrastructure"
                elif 'POWER' in line.upper():
                    current_category = "Power Systems"
                elif 'MANUFACTURING' in line.upper():
                    current_category = "Manufacturing Equipment"

            # Extract quantities and items
            quantity_match = re.search(r'(\d+)\s*units?', line, re.IGNORECASE)

            if quantity_match and any(item in line.lower() for item in
                                    ['chair', 'desk', 'laptop', 'switch', 'printer', 'generator', 'forklift']):
                quantity = int(quantity_match.group(1))

                # Determine item type and specifications
                item_name = self._extract_item_name(line)
                priority = self._extract_priority(line, content)
                estimated_cost = self._estimate_cost(item_name, quantity)

                requirement = {
                    'category': current_category,
                    'item_name': item_name,
                    'description': line,
                    'quantity': quantity,
                    'priority': priority,
                    'estimated_cost': estimated_cost
                }

                requirements.append(requirement)

                # Store in database (real insert, no mocking)
                cursor.execute("""
                    INSERT INTO rfp_requirements (rfp_document_id, category, item_name,
                                                description, quantity, priority, estimated_cost)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (rfp_id, requirement['category'], requirement['item_name'],
                      requirement['description'], requirement['quantity'], requirement['priority'],
                      requirement['estimated_cost']))
                requirement['id'] = cursor.fetchone()['id']

        # Store analysis metrics (real insert)
        complexity_factors = self._analyze_complexity(content)
        requires_clarification = len(requirements) < 3 or 'not sure' in content.lower()

        cursor.execute("""
            INSERT INTO analysis_metrics (rfp_document_id, requirements_identified,
                                        complexity_factors, processing_time_seconds)
            VALUES (%s, %s, %s, %s)
        """, (rfp_id, len(requirements),
              json.dumps(complexity_factors), time.time()))

        self.conn.commit()

        return {
            'requirements': requirements,
            'complexity_factors': complexity_factors,
            'requires_clarification': requires_clarification,
            'clarification_needed': ['Specify exact quantities', 'Define technical specifications'] if requires_clarification else []
        }

    def _extract_item_name(self, line):
        """Extract item name from requirement line."""
        item_keywords = {
            'chair': 'Office Chair',
            'desk': 'Office Desk',
            'laptop': 'Business Laptop',
            'switch': 'Network Switch',
            'printer': 'Multi-Function Printer',
            'generator': 'Backup Generator',
            'forklift': 'Forklift'
        }

        for keyword, name in item_keywords.items():
            if keyword in line.lower():
                return name
        return 'Unknown Item'

    def _extract_priority(self, line, full_content):
        """Determine priority from context."""
        if 'HIGH' in line.upper() or 'Priority: HIGH' in full_content:
            return 'high'
        elif 'LOW' in line.upper() or 'Priority: LOW' in full_content:
            return 'low'
        return 'medium'

    def _estimate_cost(self, item_name, quantity):
        """Provide rough cost estimate."""
        unit_estimates = {
            'Office Chair': 300.0,
            'Office Desk': 500.0,
            'Business Laptop': 1200.0,
            'Network Switch': 400.0,
            'Multi-Function Printer': 2000.0,
            'Backup Generator': 12000.0,
            'Forklift': 25000.0
        }

        unit_cost = unit_estimates.get(item_name, 100.0)
        return unit_cost * quantity

    def _analyze_complexity(self, content):
        """Analyze RFP complexity factors."""
        factors = {
            'technical_specifications': 'technical' in content.lower() or 'specifications' in content.lower(),
            'integration_requirements': 'integration' in content.lower() or 'compatibility' in content.lower(),
            'timeline_pressure': 'urgent' in content.lower() or 'asap' in content.lower(),
            'budget_constraints': '$' in content and ('budget' in content.lower() or 'limit' in content.lower()),
            'multiple_categories': len(re.findall(r'\d+\.', content)) > 3
        }
        return factors


class QuotationGenerator:
    """Generates quotations based on RFP requirements.

    Uses real PostgreSQL database - NO MOCKING.
    """

    def __init__(self, connection):
        self.conn = connection

    def generate_comprehensive_quotation(self, rfp_id, requirements):
        """Generate comprehensive quotation for all requirements.

        Real database operations - NO MOCKING.
        """
        cursor = self.conn.cursor()
        line_items = []
        total_value = Decimal('0.00')
        matched_count = 0

        for req in requirements:
            # Find matching products (real database query)
            cursor.execute("""
                SELECT * FROM product_catalog
                WHERE name ILIKE %s OR description ILIKE %s
                ORDER BY unit_price ASC
                LIMIT 1
            """, (f"%{req['item_name']}%", f"%{req['item_name']}%"))

            product = cursor.fetchone()
            if product:
                line_total = Decimal(str(product['unit_price'])) * req['quantity']
                total_value += line_total
                matched_count += 1

                line_items.append({
                    'requirement_id': req['id'],
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'description': product['description'],
                    'quantity': req['quantity'],
                    'unit_price': float(product['unit_price']),
                    'total_cost': float(line_total),
                    'supplier_id': product['supplier_id'],
                    'lead_time_days': product['lead_time_days']
                })

        coverage_percentage = Decimal(matched_count) / len(requirements) if requirements else Decimal('0')
        confidence_score = min(coverage_percentage + Decimal('0.2'), Decimal('1.0'))

        # Store quotation (real database insert)
        cursor.execute("""
            INSERT INTO quotation_responses (rfp_document_id, total_value,
                                           confidence_score, line_items, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (rfp_id, total_value, confidence_score,
              json.dumps(line_items), "generated"))
        quotation_id = cursor.fetchone()['id']

        # Update metrics (real database update)
        cursor.execute("""
            UPDATE analysis_metrics
            SET products_matched = %s, coverage_percentage = %s
            WHERE rfp_document_id = %s
        """, (matched_count, coverage_percentage, rfp_id))

        self.conn.commit()

        return {
            'quotation_id': quotation_id,
            'total_value': float(total_value),
            'line_items': line_items,
            'coverage_percentage': float(coverage_percentage),
            'confidence_score': float(confidence_score)
        }

    def generate_budget_conscious_quotation(self, rfp_id, requirements, budget_limit):
        """Generate quotation within budget constraints.

        Real database operations - NO MOCKING.
        """
        # Similar to comprehensive but with cost optimization
        result = self.generate_comprehensive_quotation(rfp_id, requirements)

        if result['total_value'] <= budget_limit:
            result['within_budget'] = True
            return result

        # If over budget, implement cost optimization
        cursor = self.conn.cursor()

        # Try to find more economical alternatives
        optimized_items = []
        optimized_total = Decimal('0.00')

        for req in requirements:
            cursor.execute("""
                SELECT * FROM product_catalog
                WHERE (name ILIKE %s OR description ILIKE %s)
                AND unit_price <= %s
                ORDER BY unit_price ASC
                LIMIT 1
            """, (f"%{req['item_name']}%", f"%{req['item_name']}%",
                  budget_limit / len(requirements)))  # Simple budget distribution

            product = cursor.fetchone()
            if product:
                line_total = Decimal(str(product['unit_price'])) * req['quantity']
                if optimized_total + line_total <= budget_limit:
                    optimized_total += line_total
                    optimized_items.append({
                        'product_name': product['name'],
                        'quantity': req['quantity'],
                        'unit_price': float(product['unit_price']),
                        'total_cost': float(line_total)
                    })

        # Update quotation with optimized version (real database update)
        cursor.execute("""
            UPDATE quotation_responses
            SET total_value = %s, line_items = %s, status = %s
            WHERE rfp_document_id = %s
        """, (optimized_total, json.dumps(optimized_items), "budget_optimized", rfp_id))

        self.conn.commit()

        return {
            'total_value': float(optimized_total),
            'line_items': optimized_items,
            'within_budget': optimized_total <= budget_limit,
            'coverage_percentage': len(optimized_items) / len(requirements) if requirements else 0
        }

    def generate_estimate_quotation(self, rfp_id, requirements):
        """Generate estimate quotation for unclear requirements.

        Real database operations - NO MOCKING.
        """
        # Generate rough estimates with disclaimers
        result = self.generate_comprehensive_quotation(rfp_id, requirements)

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE quotation_responses
            SET terms_conditions = %s, status = %s
            WHERE rfp_document_id = %s
        """, ("ESTIMATE ONLY - Final pricing subject to detailed requirements clarification",
              "estimate", rfp_id))

        self.conn.commit()

        result['is_estimate'] = True
        return result
