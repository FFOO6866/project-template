# TEST-003-Pytest-Markers-Configuration

## Description
Add missing pytest markers to pytest.ini configuration to eliminate "Unknown pytest.mark.{marker}" warnings and ensure proper test categorization. Multiple tests are using undefined markers causing warnings.

## Acceptance Criteria
- [ ] All pytest marker warnings resolved
- [ ] pytest.ini contains all used markers with descriptions
- [ ] Test execution runs without marker warnings
- [ ] Marker filtering works properly for test categories

## Current Missing Markers
Based on test execution warnings:
- `compliance` - Used in safety compliance framework tests
- `performance` - Used in performance benchmark tests (already in ini but warnings persist)
- Any other markers discovered during full test analysis

## Dependencies
- pytest.ini configuration
- Test marker standardization across test suites

## Risk Assessment
- **LOW**: Warnings don't break tests but indicate configuration issues
- **MEDIUM**: Marker filtering may not work properly
- **LOW**: CI/CD pipeline may be affected by configuration warnings

## Subtasks
- [ ] Audit all test files for marker usage (Est: 1h) - Grep for @pytest.mark usage
- [ ] Update pytest.ini with missing markers (Est: 30m) - Add marker definitions
- [ ] Validate marker filtering works (Est: 30m) - Test -m marker selection
- [ ] Document marker usage standards (Est: 30m) - Create marker usage guidelines

## Testing Requirements
- [ ] Unit tests: Marker filtering validation
- [ ] Integration tests: Category-based test execution
- [ ] E2E tests: Complete marker coverage validation

## Implementation Strategy
1. **Marker Audit**: Scan all test files for marker usage
2. **Configuration Update**: Add all missing markers to pytest.ini
3. **Validation**: Test marker filtering functionality
4. **Documentation**: Document standard marker usage

## Markers to Add
```ini
markers =
    unit: Fast unit tests with mocking allowed
    integration: Integration tests with real services, no mocking
    e2e: End-to-end tests with complete workflows
    requires_docker: Tests requiring Docker infrastructure
    slow: Tests that may take longer than usual
    performance: Performance and SLA validation tests
    compliance: SDK compliance validation tests
    safety: Safety compliance and regulatory tests
    chromadb: Tests requiring ChromaDB service
    neo4j: Tests requiring Neo4j service
    openai: Tests requiring OpenAI API access
```

## Definition of Done
- [ ] All pytest marker warnings eliminated
- [ ] pytest.ini contains comprehensive marker definitions
- [ ] Marker filtering works for all categories
- [ ] Test execution runs cleanly without warnings
- [ ] CI/CD pipeline configuration validated