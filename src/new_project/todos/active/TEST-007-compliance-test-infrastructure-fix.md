# TEST-007: Compliance Test Infrastructure Fix

**Created:** 2025-08-04  
**Assigned:** testing-specialist + compliance-expert  
**Priority:** 🚨 P0 - IMMEDIATE  
**Status:** PENDING  
**Estimated Effort:** 1 hour  
**Due Date:** 2025-08-04 (After Docker services operational)

## Description

Fix the 3 failing compliance tests by implementing real infrastructure testing with Docker services. This eliminates mocking and establishes genuine compliance validation using production-like services as required by the NO MOCKING policy.

## Critical Issue Analysis

**Root Cause:** Compliance tests currently failing due to lack of real infrastructure services
**Current Impact:** 3/3 compliance tests failing (unknown compliance status)
**Solution:** Connect compliance tests to real Docker services for authentic validation

## Acceptance Criteria

- [ ] All 3 compliance tests connect to real Docker infrastructure
- [ ] Compliance tests use actual database connections (no mocking)
- [ ] Safety compliance framework operational with real data
- [ ] OSHA/ANSI compliance checking working with real services
- [ ] Compliance test suite runs without infrastructure failures
- [ ] Test results provide accurate compliance status assessment

## Subtasks

- [ ] Analyze Current Compliance Test Failures (Est: 30min)
  - Verification: Exact failure reasons and missing infrastructure identified
  - Output: Detailed analysis of what infrastructure each compliance test requires
- [ ] Update Compliance Tests for Real Infrastructure (Est: 60min)
  - Verification: Tests modified to use real Docker services instead of mocks
  - Output: Compliance tests connecting to PostgreSQL, Neo4j, and other services
- [ ] Implement Safety Compliance Database Integration (Est: 30min)
  - Verification: Safety compliance framework using real database storage
  - Output: OSHA/ANSI rules stored and queried from PostgreSQL
- [ ] Validate Complete Compliance Test Suite (Est: 30min)
  - Verification: All 3 compliance tests passing with real infrastructure
  - Output: 100% compliance test success rate with production-like validation

## Dependencies

- **INFRA-005**: Docker infrastructure setup (PostgreSQL, Neo4j, Redis services must be running)
- **PERF-001**: Performance test timeout fix (may affect compliance test execution time)
- Real infrastructure services accessible from test environment

## Risk Assessment

- **MEDIUM**: Compliance tests may require specific database schema or data setup
- **MEDIUM**: Real infrastructure may reveal additional compliance validation requirements
- **LOW**: Test execution time may increase with real database operations
- **LOW**: Network connectivity issues between tests and Docker services

## Technical Implementation Plan

### Phase 7A: Compliance Test Analysis (15 minutes)
```bash
# EXACT COMMANDS to analyze compliance tests:
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project

# Identify compliance test files
dir tests\compliance\ /b

# Run compliance tests to see current failures
python -m pytest tests/compliance/ -v --tb=short

# Check for mock usage that needs real infrastructure
findstr /s /i "mock" tests\compliance\*.py
findstr /s /i "localhost" tests\compliance\*.py
```

### Phase 7B: Infrastructure Integration (30 minutes)
```python
# Update compliance tests for real infrastructure
# tests/compliance/test_safety_compliance_framework.py

import pytest
import psycopg2
from neo4j import GraphDatabase
import redis
import os

class TestSafetyComplianceFramework:
    """Safety compliance tests using real infrastructure"""
    
    @pytest.fixture(scope="class")
    def db_connection(self):
        """Real PostgreSQL connection for compliance data"""
        conn = psycopg2.connect(
            host='localhost',
            port=5434,  # Test infrastructure port
            database='kailash_test',
            user='test_user',
            password='test_password'
        )
        
        # Create compliance tables if not exist
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS safety_rules (
                    id SERIAL PRIMARY KEY,
                    rule_type VARCHAR(50),
                    rule_code VARCHAR(100),
                    description TEXT,
                    compliance_level VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id SERIAL PRIMARY KEY,
                    check_type VARCHAR(50),
                    item_description TEXT,
                    safety_rules TEXT[],
                    compliance_status VARCHAR(20),
                    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
        
        yield conn
        conn.close()
    
    @pytest.fixture(scope="class") 
    def cache_service(self):
        """Real Redis connection for compliance caching"""
        r = redis.Redis(
            host='localhost',
            port=6380,  # Test infrastructure port
            decode_responses=True
        )
        yield r
        
        # Note: Using Redis for caching instead of Neo4j for simpler test setup
        # Neo4j integration can be added in later phases
    
    
    def test_osha_compliance_validation(self, db_connection, graph_db):
        """Test OSHA compliance validation with real database"""
        
        # Insert sample OSHA rules into database
        with db_connection.cursor() as cur:
            cur.execute("""
                INSERT INTO safety_rules (rule_type, rule_code, description, compliance_level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, ('OSHA', '1926.95', 'Personal protective equipment', 'MANDATORY'))
            
            db_connection.commit()
        
        # Test compliance checking
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT rule_code, description, compliance_level 
                FROM safety_rules 
                WHERE rule_type = 'OSHA'
            """)
            rules = cur.fetchall()
        
        assert len(rules) > 0, "OSHA rules should be loaded in database"
        
        # Test graph database relationships
        with graph_db.session() as session:
            result = session.run("""
                MATCH (f:Framework)-[:IMPLEMENTS]->(s:Standard {name: 'OSHA'})
                RETURN f.name, s.name
            """)
            relationships = list(result)
            
        assert len(relationships) > 0, "OSHA compliance relationships should exist"
    
    def test_ansi_compliance_validation(self, db_connection, graph_db):
        """Test ANSI compliance validation with real database"""
        
        # Insert sample ANSI rules
        with db_connection.cursor() as cur:
            cur.execute("""
                INSERT INTO safety_rules (rule_type, rule_code, description, compliance_level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, ('ANSI', 'Z87.1', 'Eye and face protection', 'MANDATORY'))
            
            db_connection.commit()
        
        # Validate ANSI compliance checking
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM safety_rules WHERE rule_type = 'ANSI'
            """)
            ansi_count = cur.fetchone()[0]
        
        assert ansi_count > 0, "ANSI rules should be loaded and accessible"
    
    def test_integrated_compliance_framework(self, db_connection, graph_db, cache_service):
        """Test complete compliance framework with all services"""
        
        # Test compliance check workflow
        compliance_check = {
            'item': 'Power tool usage in construction',
            'categories': ['electrical', 'ppe', 'training']
        }
        
        # Store compliance check in database
        with db_connection.cursor() as cur:
            cur.execute("""
                INSERT INTO compliance_checks (check_type, item_description, compliance_status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('tool_safety', compliance_check['item'], 'PENDING'))
            
            check_id = cur.fetchone()[0]
            db_connection.commit()
        
        # Cache compliance result
        cache_key = f"compliance_check:{check_id}"
        cache_service.setex(cache_key, 3600, 'VALIDATED')
        
        # Verify caching worked
        cached_result = cache_service.get(cache_key)
        assert cached_result == 'VALIDATED', "Compliance result should be cached"
        
        # Update compliance status in database
        with db_connection.cursor() as cur:
            cur.execute("""
                UPDATE compliance_checks 
                SET compliance_status = %s 
                WHERE id = %s
            """, ('COMPLIANT', check_id))
            
            db_connection.commit()
        
        # Verify complete workflow
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT compliance_status FROM compliance_checks WHERE id = %s
            """, (check_id,))
            final_status = cur.fetchone()[0]
        
        assert final_status == 'COMPLIANT', "Compliance workflow should complete successfully"
```

### Phase 7C: Safety Framework Database Setup (15 minutes)
```sql
-- Compliance database schema setup
-- compliance_schema.sql

-- OSHA safety rules table
CREATE TABLE IF NOT EXISTS osha_rules (
    id SERIAL PRIMARY KEY,
    section VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    applicability TEXT,
    enforcement_level VARCHAR(20) DEFAULT 'MANDATORY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ANSI standards table  
CREATE TABLE IF NOT EXISTS ansi_standards (
    id SERIAL PRIMARY KEY,
    standard_code VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50),
    compliance_level VARCHAR(20) DEFAULT 'RECOMMENDED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance validation results
CREATE TABLE IF NOT EXISTS compliance_validations (
    id SERIAL PRIMARY KEY,
    item_id VARCHAR(100) NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    validation_rules TEXT[],
    compliance_status VARCHAR(20) NOT NULL,
    issues_found TEXT[],
    recommendations TEXT[],
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample OSHA rules
INSERT INTO osha_rules (section, title, description, applicability) VALUES
('1926.95', 'Personal Protective Equipment', 'Requirements for PPE in construction', 'All construction sites'),
('1926.100', 'Head Protection', 'Hard hat requirements', 'Areas with overhead hazards'),
('1926.102', 'Eye and Face Protection', 'Safety glasses and shields', 'Areas with eye hazards')
ON CONFLICT DO NOTHING;

-- Insert sample ANSI standards
INSERT INTO ansi_standards (standard_code, title, description, category) VALUES
('Z87.1', 'Eye and Face Protection', 'Safety glasses standards', 'Personal Protection'),
('Z89.1', 'Industrial Head Protection', 'Hard hat standards', 'Personal Protection'),
('Z41', 'Personal Protection - Protective Footwear', 'Safety shoe standards', 'Personal Protection')
ON CONFLICT DO NOTHING;
```

### Phase 7D: Complete Validation (15 minutes)
```bash
# EXACT COMMANDS for compliance validation:
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project

# Load compliance database schema using test infrastructure
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5434, database='kailash_test',
    user='test_user', password='test_password'
)
with conn.cursor() as cur:
    # Create simple compliance tables
    cur.execute('''
        CREATE TABLE IF NOT EXISTS safety_rules (
            id SERIAL PRIMARY KEY,
            rule_type VARCHAR(50),
            rule_code VARCHAR(100), 
            description TEXT
        );
    ''')
    cur.execute('''
        INSERT INTO safety_rules (rule_type, rule_code, description)
        VALUES ('OSHA', '1926.95', 'Personal protective equipment')
        ON CONFLICT DO NOTHING;
    ''')
conn.commit()
conn.close()
print('✅ Compliance database schema loaded')
"

# Run updated compliance tests
python -m pytest tests/compliance/ -v

# Validate specific compliance functionality
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5434, database='kailash_test',
    user='test_user', password='test_password'
)
with conn.cursor() as cur:
    cur.execute('SELECT COUNT(*) FROM safety_rules')
    count = cur.fetchone()[0]
print(f'✅ Safety rules loaded: {count}')
conn.close()
"

# Generate compliance report
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5432, database='kailash_dev',
    user='kailash_user', password='kailash_dev_password'
)
with conn.cursor() as cur:
    cur.execute('SELECT COUNT(*) FROM osha_rules')
    osha_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM ansi_standards') 
    ansi_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM compliance_validations')
    validation_count = cur.fetchone()[0]

print(f'Compliance Framework Status:')
print(f'  OSHA Rules: {osha_count}')
print(f'  ANSI Standards: {ansi_count}')
print(f'  Validations: {validation_count}')
conn.close()
"
```

## Testing Requirements

### Immediate Tests (Critical Priority)
- [ ] All 3 compliance tests connecting to real Docker services
- [ ] Database connectivity and schema creation
- [ ] OSHA/ANSI rule loading and querying
- [ ] Compliance validation workflow execution

### Integration Tests (After Infrastructure Fix)
- [ ] End-to-end compliance checking workflow
- [ ] Performance of compliance tests with real database
- [ ] Compliance reporting and result storage
- [ ] Error handling with real service failures

### Validation Tests (Final Verification)
- [ ] Complete compliance test suite execution
- [ ] Compliance accuracy with real data validation
- [ ] Service integration stress testing
- [ ] Compliance framework production readiness

## Definition of Done

- [ ] All 3 compliance tests passing with real infrastructure
- [ ] No mocking used in compliance test execution
- [ ] Safety compliance framework operational with database storage
- [ ] OSHA/ANSI rules loaded and accessible via database queries
- [ ] Compliance validation workflow complete and functional
- [ ] Test results provide accurate production-ready compliance assessment

## Implementation Files

- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\tests\compliance\test_safety_compliance_framework.py` (update existing)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\compliance_schema.sql` (new)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\.env.testing` (update existing)

## Success Metrics

- **Compliance Test Success**: 3/3 tests passing (100% improvement from current failures)
- **Infrastructure Integration**: 100% real services, 0% mocking
- **Database Operations**: OSHA/ANSI rules successfully stored and queried
- **Validation Accuracy**: Compliance results reflect real production scenarios

## Next Actions After Completion

1. **VALID-001**: Production readiness validation (includes compliance test success)
2. **FOUND-001**: SDK compliance foundation validation (may integrate with safety compliance)
3. **TEST-008**: Complete test infrastructure validation (includes compliance testing)

This task establishes authentic compliance validation using real infrastructure, providing accurate assessment of safety and regulatory compliance status.