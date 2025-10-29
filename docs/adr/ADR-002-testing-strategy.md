# ADR-002: Three-Tier Testing Strategy with No-Mocking Policy

## Status
Accepted

## Context
The Horme POV project requires a comprehensive testing strategy that validates functionality across multiple layers while maintaining reliability and real-world accuracy. Traditional testing approaches with extensive mocking can hide integration issues and create false confidence in system reliability.

### Requirements
- Validate functionality at unit, integration, and end-to-end levels
- Ensure real infrastructure testing for critical components
- Maintain fast feedback cycles for development
- Support Docker-containerized testing environment
- Enable CI/CD pipeline integration
- Provide realistic test data and scenarios

## Decision
We implement a three-tier testing strategy with a strict no-mocking policy for Tiers 2 and 3:

### Tier 1: Unit Testing (Isolated Components)
- **Scope**: Pure functions, business logic, data transformations
- **Mocking**: Allowed for external dependencies only
- **Infrastructure**: In-memory databases, lightweight containers
- **Speed**: < 100ms per test, < 5 seconds total suite

### Tier 2: Integration Testing (Real Infrastructure)
- **Scope**: Service-to-service communication, database operations, API endpoints
- **Mocking**: PROHIBITED - Use real services in test containers
- **Infrastructure**: Real PostgreSQL, Redis, MCP servers in Docker
- **Speed**: < 5 seconds per test, < 60 seconds total suite

### Tier 3: End-to-End Testing (Complete Workflows)
- **Scope**: Full user journeys, cross-system integration, production-like scenarios
- **Mocking**: PROHIBITED - Full stack testing with real services
- **Infrastructure**: Complete Docker Compose environment
- **Speed**: < 30 seconds per test, < 10 minutes total suite

## Testing Architecture

### Container-Based Test Infrastructure
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: horme_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5434:5432"
    
  test-redis:
    image: redis:7-alpine
    ports:
      - "6381:6379"
    
  test-mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp-lightweight
    environment:
      DATABASE_URL: postgresql://test_user:test_password@test-postgres:5432/horme_test
    depends_on:
      - test-postgres
      - test-redis
```

### Test Data Management
```python
# Real test data patterns
class TestDataManager:
    def setup_realistic_products(self):
        """Load real product data structures"""
        return self.load_from_fixtures('realistic_products.json')
    
    def setup_real_suppliers(self):
        """Create supplier data matching production patterns"""
        return self.create_suppliers_with_real_constraints()
    
    def cleanup_test_data(self):
        """Clean test databases between runs"""
        self.truncate_all_tables_maintaining_schema()
```

## Consequences

### Positive
- **Real-World Accuracy**: Tests validate actual system behavior
- **Integration Confidence**: Catches real integration issues early
- **Production Similarity**: Test environment mirrors production
- **Debugging Clarity**: Real errors easier to diagnose and fix
- **Deployment Confidence**: Tests validate actual deployment scenarios

### Negative
- **Execution Time**: Integration/E2E tests slower than unit tests
- **Infrastructure Complexity**: Requires real services for testing
- **Resource Requirements**: Higher memory/CPU usage during testing
- **Test Data Management**: Complex realistic test data required
- **Debugging Complexity**: More components involved in test failures

## Alternatives Considered

### Option 1: Heavy Mocking Strategy
- **Description**: Mock all external dependencies across all test tiers
- **Pros**: Fast execution, isolated failures, simple setup
- **Cons**: Hides integration issues, mock drift from reality, false confidence
- **Why Rejected**: Proven to hide critical production issues

### Option 2: Single-Tier Testing
- **Description**: Only unit tests with comprehensive mocking
- **Pros**: Very fast, simple implementation
- **Cons**: No integration validation, high production failure risk
- **Why Rejected**: Insufficient for production system validation

### Option 3: Manual Testing Only
- **Description**: Rely on manual QA processes
- **Pros**: Human validation, real user scenarios
- **Cons**: Slow feedback, inconsistent coverage, not scalable
- **Why Rejected**: Cannot support rapid development cycles

## Implementation Plan

### Phase 1: Foundation Testing (Complete)
1. Implement test container infrastructure
2. Create realistic test data generators
3. Set up Tier 1 unit tests for core business logic
4. Establish test database management patterns

### Phase 2: Integration Testing (Complete)
1. Implement Tier 2 tests for all API endpoints
2. Add database integration tests with real PostgreSQL
3. Create MCP server integration tests
4. Validate Docker network communication

### Phase 3: End-to-End Validation (Complete)
1. Implement complete workflow tests
2. Add cross-service communication validation
3. Create production scenario simulations
4. Performance testing under realistic load

## Testing Standards

### Code Coverage Requirements
- **Tier 1**: 90% line coverage, 85% branch coverage
- **Tier 2**: 80% integration path coverage
- **Tier 3**: 100% critical user journey coverage

### Performance Requirements
- **Tier 1**: All tests < 100ms, suite < 5 seconds
- **Tier 2**: Individual tests < 5 seconds, suite < 60 seconds
- **Tier 3**: Individual tests < 30 seconds, suite < 10 minutes

### Reliability Requirements
- **Flaky Test Tolerance**: < 1% failure rate from infrastructure
- **Test Isolation**: No test dependencies or shared state
- **Cleanup Guarantee**: All tests must clean up resources

## Test Infrastructure Management

### Container Lifecycle
```bash
# Test execution pattern
./scripts/run-tests.sh tier1    # Fast unit tests
./scripts/run-tests.sh tier2    # Integration with real services  
./scripts/run-tests.sh tier3    # Full end-to-end workflows
./scripts/run-tests.sh all      # Complete test suite
```

### CI/CD Integration
```yaml
# GitHub Actions pattern
test-tier1:
  runs-on: ubuntu-latest
  steps:
    - name: Run Unit Tests
      run: ./scripts/run-tests.sh tier1

test-tier2:
  runs-on: ubuntu-latest
  needs: test-tier1
  steps:
    - name: Start Test Infrastructure
      run: docker-compose -f docker-compose.test.yml up -d
    - name: Run Integration Tests  
      run: ./scripts/run-tests.sh tier2

test-tier3:
  runs-on: ubuntu-latest
  needs: test-tier2
  steps:
    - name: Run End-to-End Tests
      run: ./scripts/run-tests.sh tier3
```

## Validation Criteria
- [ ] All three tiers implemented and operational
- [ ] No mocking in Tier 2 and Tier 3 tests
- [ ] Real infrastructure containers for integration testing
- [ ] Realistic test data matching production patterns
- [ ] Performance requirements met for all tiers
- [ ] CI/CD pipeline integration functional
- [ ] Test cleanup and isolation verified