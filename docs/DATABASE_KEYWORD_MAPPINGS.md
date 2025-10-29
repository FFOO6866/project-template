# Database-Loaded Keyword Mappings

## Overview

The Hybrid AI Recommendation Engine now loads category and task keyword mappings from PostgreSQL instead of using hardcoded dictionaries. This enables:

- **Dynamic Updates**: Change keyword mappings without code deployment
- **Centralized Management**: Single source of truth in database
- **Production Safety**: Fail-fast validation ensures data integrity
- **Audit Trail**: Track when mappings were added/modified

## Architecture

### Before (Hardcoded)
```python
# Lines 949-955 in hybrid_recommendation_engine.py
category_keywords = {
    'lighting': ['light', 'led', 'lamp', 'fixture'],
    'safety': ['safety', 'ppe', 'protection', 'helmet'],
    # ... hardcoded data
}
```

### After (Database-Loaded)
```python
# Lazy-loaded from PostgreSQL on first use
def _load_category_keywords_from_db(self) -> Dict[str, List[str]]:
    """Load from category_keyword_mappings table"""
    # Fail-fast if table is empty
```

## Database Schema

### category_keyword_mappings
```sql
CREATE TABLE category_keyword_mappings (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    keyword VARCHAR(200) NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, keyword)
);
```

**Purpose**: Maps keywords to product categories for requirement extraction

**Example Data**:
| category   | keyword    | priority |
|------------|------------|----------|
| lighting   | light      | 1        |
| lighting   | led        | 1        |
| safety     | ppe        | 1        |

### task_keyword_mappings
```sql
CREATE TABLE task_keyword_mappings (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(200) NOT NULL,
    task_id VARCHAR(200) NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, task_id)
);
```

**Purpose**: Maps keywords to knowledge graph task IDs

**Example Data**:
| keyword   | task_id              | priority |
|-----------|---------------------|----------|
| drill     | task_drill_hole     | 1        |
| paint     | task_paint_surface  | 1        |
| install   | task_install_fixture| 1        |

## Setup Instructions

### 1. Apply Database Schema
```bash
# Run unified schema (includes keyword mapping tables)
psql -U horme_user -d horme_db -f init-scripts/unified-postgresql-schema.sql
```

### 2. Load Initial Data
```bash
# Load category and task keyword mappings
python scripts/load_category_task_mappings.py
```

**Expected Output**:
```
================================================================================
Category and Task Keyword Mappings Loader
================================================================================
Connecting to PostgreSQL database...
✅ Connected to database
Loading category keyword mappings...
✅ Inserted 19 category keyword mappings
Loading task keyword mappings...
✅ Inserted 8 task keyword mappings
✅ Data verification passed

================================================================================
LOADED CATEGORY KEYWORD MAPPINGS
================================================================================
lighting        -> fixture, lamp, led, light
networking      -> cable, ethernet, network, wifi
power           -> battery, electrical, power, supply
safety          -> helmet, ppe, protection, safety
tools           -> drill, hammer, saw, tool

================================================================================
LOADED TASK KEYWORD MAPPINGS
================================================================================
cut             -> task_cut_material
drill           -> task_drill_hole
install         -> task_install_fixture
lighting        -> task_install_lighting
measure         -> task_measure_dimension
paint           -> task_paint_surface
safety          -> task_safety_compliance
secure          -> task_secure_fastener
================================================================================
```

### 3. Verify Loading
```bash
# Run test suite
python scripts/test_database_keyword_loading.py

# Test fail-fast behavior (optional)
python scripts/test_database_keyword_loading.py --test-fail-fast
```

## Usage in Code

### Automatic Loading (Recommended)
```python
from src.ai.hybrid_recommendation_engine import get_hybrid_engine

# Initialize engine (database connection required)
engine = get_hybrid_engine()

# Keywords are lazy-loaded on first use
recommendations = engine.recommend_products(
    rfp_text="Need LED lighting and safety equipment",
    limit=20
)
```

### Manual Inspection
```python
# Access loaded mappings (triggers lazy loading)
categories = engine._extract_categories_from_requirements([
    "Need LED lighting",
    "Safety helmets required"
])
# Returns: ['lighting', 'safety']

tasks = engine._extract_tasks_from_requirements([
    "Drill holes in concrete",
    "Paint surfaces"
])
# Returns: ['task_drill_hole', 'task_paint_surface']
```

## Fail-Fast Behavior

### Empty Database Tables
```python
# If category_keyword_mappings is empty
engine._extract_categories_from_requirements(["test"])

# Raises:
# ValueError: CRITICAL: No category keyword mappings found in database.
# Run 'python scripts/load_category_task_mappings.py' to populate mappings.
```

### Database Connection Failed
```python
# If PostgreSQL is unavailable
engine = HybridRecommendationEngine(database=db)

# Raises:
# RuntimeError: Database query failed for category keywords: connection failed.
# Ensure PostgreSQL is running and category_keyword_mappings table exists.
```

## Adding New Mappings

### Manual SQL Insert
```sql
-- Add new category keyword
INSERT INTO category_keyword_mappings (category, keyword, priority)
VALUES ('plumbing', 'pipe', 1)
ON CONFLICT (category, keyword) DO NOTHING;

-- Add new task keyword
INSERT INTO task_keyword_mappings (keyword, task_id, priority)
VALUES ('weld', 'task_weld_metal', 1)
ON CONFLICT (keyword, task_id) DO NOTHING;
```

### Programmatic Insert
```python
from src.core.postgresql_database import get_database

db = get_database()

# Add category keyword
with db.connection.cursor() as cursor:
    cursor.execute("""
        INSERT INTO category_keyword_mappings (category, keyword, priority)
        VALUES (%s, %s, %s)
        ON CONFLICT (category, keyword) DO NOTHING
    """, ('plumbing', 'pipe', 1))
    db.connection.commit()
```

### Bulk Import
```python
# Update load_category_task_mappings.py with new data
CATEGORY_KEYWORDS = {
    'lighting': ['light', 'led', 'lamp', 'fixture'],
    'safety': ['safety', 'ppe', 'protection', 'helmet'],
    'plumbing': ['pipe', 'valve', 'faucet'],  # New category
    # ...
}

# Re-run loader
python scripts/load_category_task_mappings.py
```

## Priority Weighting (Future Enhancement)

The `priority` column supports weighted keyword matching:

```python
# Higher priority keywords could be weighted more
INSERT INTO category_keyword_mappings (category, keyword, priority)
VALUES
    ('safety', 'ppe', 3),        -- High priority
    ('safety', 'protection', 2), -- Medium priority
    ('safety', 'helmet', 1);     -- Standard priority
```

**Note**: Priority weighting is not yet implemented in extraction logic but schema is ready.

## Testing

### Test Suite Coverage
1. **Category Keyword Loading**: Verify categories load from database
2. **Task Keyword Loading**: Verify tasks load from database
3. **Fail-Fast Behavior**: Verify errors on empty tables (optional)
4. **Data Integrity**: Verify database contains expected data

### Run Tests
```bash
# Standard tests
python scripts/test_database_keyword_loading.py

# Test fail-fast (requires empty tables)
python scripts/test_database_keyword_loading.py --test-fail-fast
```

### Expected Test Output
```
================================================================================
Database Keyword Loading Test Suite
================================================================================
TEST 1: Category Keyword Loading from Database
✅ Successfully extracted categories: ['lighting', 'safety', 'tools', 'power']
✅ TEST 1 PASSED: Category keywords loaded from database

TEST 2: Task Keyword Loading from Database
✅ Successfully extracted tasks: ['task_drill_hole', 'task_paint_surface', ...]
✅ TEST 2 PASSED: Task keywords loaded from database

TEST 4: Database Data Integrity
Category keyword counts:
  lighting: 4 keywords
  networking: 4 keywords
  power: 4 keywords
  safety: 4 keywords
  tools: 4 keywords
✅ TEST 4 PASSED: Database data integrity verified

TEST SUMMARY
category_loading: ✅ PASSED
task_loading: ✅ PASSED
data_integrity: ✅ PASSED
Total: 3 passed, 0 failed, 1 skipped
✅ ALL TESTS PASSED
```

## Migration Checklist

- [x] Add `category_keyword_mappings` table to schema
- [x] Add `task_keyword_mappings` table to schema
- [x] Create data loading script (`load_category_task_mappings.py`)
- [x] Update `hybrid_recommendation_engine.py` to load from database
- [x] Add fail-fast validation for empty tables
- [x] Remove hardcoded dictionaries from code
- [x] Create test suite (`test_database_keyword_loading.py`)
- [ ] Run schema migration on production database
- [ ] Load initial data on production
- [ ] Verify tests pass on production
- [ ] Deploy updated code to production

## Troubleshooting

### Tables Not Found
```
ERROR: relation "category_keyword_mappings" does not exist
```
**Solution**: Run `unified-postgresql-schema.sql` to create tables

### No Data Loaded
```
ValueError: CRITICAL: No category keyword mappings found in database
```
**Solution**: Run `python scripts/load_category_task_mappings.py`

### Database Connection Failed
```
RuntimeError: Database query failed for category keywords: connection failed
```
**Solution**:
1. Check PostgreSQL is running
2. Verify `POSTGRES_*` environment variables
3. Ensure database exists and is accessible

## Files Modified

### Schema
- `init-scripts/unified-postgresql-schema.sql` - Added mapping tables

### Scripts
- `scripts/load_category_task_mappings.py` - Data loader (NEW)
- `scripts/test_database_keyword_loading.py` - Test suite (NEW)

### Application Code
- `src/ai/hybrid_recommendation_engine.py` - Database loading logic
  - Added `_load_category_keywords_from_db()` method
  - Added `_load_task_keywords_from_db()` method
  - Updated `_extract_categories_from_requirements()` to use database
  - Updated `_extract_tasks_from_requirements()` to use database
  - Removed hardcoded dictionaries (lines 687-696, 949-955)

### Documentation
- `docs/DATABASE_KEYWORD_MAPPINGS.md` - This file (NEW)

## Next Steps

1. **Enhance Priority Weighting**: Implement priority-based keyword scoring
2. **Admin Interface**: Build UI for managing keyword mappings
3. **Audit Logging**: Track changes to keyword mappings
4. **Machine Learning**: Auto-suggest new keyword mappings from RFP data
5. **Multi-Language**: Support keyword mappings in multiple languages
