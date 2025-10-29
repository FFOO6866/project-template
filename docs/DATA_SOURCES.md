# Data Sources for Horme POV Classification System

## CRITICAL POLICY: NO MOCK DATA

This project uses **REAL external data sources ONLY** for product classification. All mock data files have been removed and are strictly prohibited.

**Violation of this policy is a critical error.**

---

## Required Data Sources

### 1. UNSPSC (United Nations Standard Products and Services Code)

#### What is UNSPSC?
UNSPSC is a global classification system for products and services. It provides a 4-level hierarchy with over 50,000 commodity codes.

#### Data Hierarchy
- **Level 1: Segment** (2 digits) - e.g., `10000000` - Live Plant and Animal Material
- **Level 2: Family** (4 digits) - e.g., `10100000` - Live animals
- **Level 3: Class** (6 digits) - e.g., `10101500` - Livestock
- **Level 4: Commodity** (8 digits) - e.g., `10101501` - Cattle

#### How to Obtain UNSPSC Data

**Purchase Required:**
- **Website:** https://www.unspsc.org/purchase-unspsc
- **Cost:** Approximately **$500 USD** for commercial license
- **Format:** Excel/CSV download with full code hierarchy
- **Updates:** Annual updates available for additional fee
- **License:** Commercial use license included

**Purchase Process:**
1. Visit https://www.unspsc.org/purchase-unspsc
2. Select "Commercial License" option
3. Complete payment (credit card or purchase order)
4. Download Excel/CSV file immediately after purchase
5. Save as `UNSPSC_v24.csv` (or current version number)

**CSV Format:**
```csv
Code,Segment,Family,Class,Commodity,Title,Definition
10000000,Live Plant and Animal Material and Accessories and Supplies,,,,Live Plant and Animal Material,...
10100000,,Live animals,,,Live animals,...
10101500,,,Livestock,,,Livestock animals...
10101501,,,,Cattle,,Bovine animals...
```

**Support:**
- Email: support@unspsc.org
- Phone: Available on website
- Documentation: https://www.unspsc.org/resources

---

### 2. ETIM (Electro-Technical Information Model)

#### What is ETIM?
ETIM is an international standard for classifying electro-technical products with multi-lingual support (13+ languages) and technical features.

#### Data Structure
- **Class Codes:** Format `EC######` (e.g., `EC000001`)
- **Versions:** Current version is 9.0 (check portal for latest)
- **Languages:** English, German, French, Dutch, Spanish, Italian, Portuguese, and more
- **Features:** Technical specifications and characteristics in JSONB format

#### How to Obtain ETIM Data

**Membership Required:**
- **Website:** https://www.etim-international.com/
- **Membership:** https://www.etim-international.com/become-a-member/
- **Portal:** https://portal.etim-international.com/ (members only)

**Membership Process:**
1. Visit https://www.etim-international.com/become-a-member/
2. Select appropriate membership tier:
   - **Manufacturer/Brand:** Full access to classification and features
   - **Wholesaler/Retailer:** Access to classifications
   - **Software Provider:** API access and integration support
3. Complete membership application
4. Annual membership fees apply (contact ETIM for pricing)
5. Access member portal at https://portal.etim-international.com/

**Data Access Methods:**

**Option 1: CSV Export (Recommended)**
1. Log in to https://portal.etim-international.com/
2. Navigate to "Downloads" section
3. Select version (e.g., "ETIM 9.0")
4. Download CSV export for your required languages
5. Save as `etim_classes_9.0.csv`

**CSV Format:**
```csv
ClassCode,Version,DescriptionEN,DescriptionDE,DescriptionFR,DescriptionNL,ParentClass
EC000001,9.0,Building automation,Gebäudeautomation,Automatisation du bâtiment,Gebouwautomatisering,
EC000002,9.0,Cable management,Kabelmanagement,Gestion de câbles,Kabelmanagement,EC000001
```

**Option 2: API Access**
1. Obtain API key from member portal
2. Set environment variable: `export ETIM_API_KEY="your_api_key"`
3. Use `src/integrations/etim_client.py` for API access
4. API endpoint: https://portal.etim-international.com/api/v1

**API Documentation:**
- Available in member portal
- RESTful API with JSON responses
- Rate limits apply (check documentation)

**Support:**
- Member Portal: https://portal.etim-international.com/support
- Email: info@etim-international.com
- Technical Support: Available for members

---

## Data Loading Instructions

### Prerequisites

1. **PostgreSQL Database Running**
   ```bash
   # Verify PostgreSQL is running
   docker-compose up -d postgres

   # Set DATABASE_URL environment variable
   export DATABASE_URL="postgresql://horme_user:horme_password@localhost:5433/horme_db"
   ```

2. **Database Schema Initialized**
   ```bash
   # Initialize database with classification tables
   psql $DATABASE_URL < init-scripts/unified-postgresql-schema.sql
   ```

3. **Python Dependencies Installed**
   ```bash
   pip install psycopg2-binary requests
   ```

### Loading UNSPSC Data

**Step 1: Purchase and Download UNSPSC CSV**
- Purchase from: https://www.unspsc.org/purchase-unspsc
- Save as: `data/UNSPSC_v24.csv` (or your preferred location)

**Step 2: Load into Database**
```bash
python scripts/load_classification_data.py \
  --unspsc-csv data/UNSPSC_v24.csv \
  --database-url $DATABASE_URL
```

**Expected Output:**
```
2025-10-17 12:00:00 - INFO - Loading UNSPSC data from data/UNSPSC_v24.csv...
2025-10-17 12:00:05 - INFO - Successfully loaded 50,000+ UNSPSC codes
2025-10-17 12:00:05 - INFO - ✓ Loaded 50000 UNSPSC codes
```

**Validation:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM unspsc_codes;"
# Should show 50,000+ codes

psql $DATABASE_URL -c "SELECT code, title FROM unspsc_codes LIMIT 5;"
# Should show sample codes
```

### Loading ETIM Data

**Option 1: Load from CSV (Recommended)**

**Step 1: Download ETIM CSV from Member Portal**
- Log in to: https://portal.etim-international.com/
- Download: `etim_classes_9.0.csv`
- Save as: `data/etim_classes_9.0.csv`

**Step 2: Load into Database**
```bash
python scripts/load_classification_data.py \
  --etim-csv data/etim_classes_9.0.csv \
  --database-url $DATABASE_URL
```

**Option 2: Load from API**

**Step 1: Set API Key**
```bash
export ETIM_API_KEY="your_api_key_from_member_portal"
export ETIM_MEMBER_ID="your_organization_id"
```

**Step 2: Load from API**
```bash
python scripts/load_classification_data.py \
  --etim-api \
  --database-url $DATABASE_URL
```

**Expected Output:**
```
2025-10-17 12:05:00 - INFO - Loading ETIM data from API...
2025-10-17 12:05:10 - INFO - Successfully loaded 5,000+ ETIM classes
2025-10-17 12:05:10 - INFO - ✓ Loaded 5000 ETIM classes
```

**Validation:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM etim_classes;"
# Should show 5,000+ classes

psql $DATABASE_URL -c "SELECT class_code, description_en FROM etim_classes LIMIT 5;"
# Should show sample classes
```

### Loading Both (Recommended)

```bash
python scripts/load_classification_data.py \
  --unspsc-csv data/UNSPSC_v24.csv \
  --etim-csv data/etim_classes_9.0.csv \
  --database-url $DATABASE_URL
```

---

## Using Classification Data

### Product Classification

Once data is loaded, you can classify products:

```python
from src.core.product_classifier import ProductClassifier

# Initialize classifier (verifies data is loaded)
with ProductClassifier() as classifier:
    # Classify a product
    result = classifier.classify_product(
        product_id=1,
        product_name="Safety Glasses ANSI Z87.1",
        product_sku="SG-001",
        product_description="Impact-resistant safety glasses",
        category="Personal Protective Equipment"
    )

    # Results include UNSPSC and ETIM classifications
    print(f"UNSPSC: {result.unspsc_code} - {result.unspsc_title}")
    print(f"ETIM: {result.etim_class} - {result.etim_description}")
    print(f"Confidence: UNSPSC={result.unspsc_confidence}, ETIM={result.etim_confidence}")

    # Save to database
    classifier.save_classification(result)
```

### Direct Database Queries

**Search UNSPSC Codes:**
```sql
-- Find safety equipment codes
SELECT code, title, level
FROM unspsc_codes
WHERE to_tsvector('english', title) @@ plainto_tsquery('english', 'safety equipment')
ORDER BY level DESC
LIMIT 10;
```

**Search ETIM Classes:**
```sql
-- Find electrical equipment classes
SELECT class_code, description_en, version
FROM etim_classes
WHERE to_tsvector('english', description_en) @@ plainto_tsquery('english', 'electrical equipment')
LIMIT 10;
```

**Get Product Classifications:**
```sql
-- Get all classified products with UNSPSC and ETIM codes
SELECT
    p.id,
    p.name,
    pc.unspsc_code,
    u.title as unspsc_title,
    pc.etim_class,
    e.description_en as etim_description,
    pc.confidence
FROM products p
JOIN product_classifications pc ON p.id = pc.product_id
LEFT JOIN unspsc_codes u ON pc.unspsc_code = u.code
LEFT JOIN etim_classes e ON pc.etim_class = e.class_code
WHERE pc.confidence > 0.7
ORDER BY pc.classified_at DESC;
```

---

## Data Maintenance

### Updating UNSPSC Data

UNSPSC releases annual updates:

1. **Purchase latest version** from https://www.unspsc.org/
2. **Load new data** (will update existing codes):
   ```bash
   python scripts/load_classification_data.py --unspsc-csv UNSPSC_v25.csv
   ```
3. **Verify update:**
   ```sql
   SELECT MAX(updated_at) FROM unspsc_codes;
   ```

### Updating ETIM Data

ETIM releases periodic updates:

1. **Download latest version** from member portal
2. **Load new data:**
   ```bash
   python scripts/load_classification_data.py --etim-csv etim_classes_10.0.csv
   ```
3. **Verify update:**
   ```sql
   SELECT version, COUNT(*) FROM etim_classes GROUP BY version;
   ```

### Backup Classification Data

```bash
# Backup UNSPSC codes
pg_dump $DATABASE_URL -t unspsc_codes > backups/unspsc_$(date +%Y%m%d).sql

# Backup ETIM classes
pg_dump $DATABASE_URL -t etim_classes > backups/etim_$(date +%Y%m%d).sql

# Backup product classifications
pg_dump $DATABASE_URL -t product_classifications > backups/classifications_$(date +%Y%m%d).sql
```

---

## Troubleshooting

### "No classification data found in database"

**Cause:** Classification tables are empty.

**Solution:**
```bash
# Load UNSPSC data
python scripts/load_classification_data.py --unspsc-csv UNSPSC_v24.csv

# Load ETIM data
python scripts/load_classification_data.py --etim-csv etim_classes_9.0.csv
```

### "UNSPSC CSV file not found"

**Cause:** File path is incorrect or file not purchased.

**Solution:**
1. Verify file exists: `ls -la data/UNSPSC_v24.csv`
2. If missing, purchase from: https://www.unspsc.org/purchase-unspsc
3. Use correct path: `--unspsc-csv /full/path/to/UNSPSC_v24.csv`

### "ETIM API key not configured"

**Cause:** ETIM_API_KEY environment variable not set.

**Solution:**
```bash
# Set API key from member portal
export ETIM_API_KEY="your_api_key_here"

# Verify it's set
echo $ETIM_API_KEY

# Or use CSV instead
python scripts/load_classification_data.py --etim-csv etim_classes_9.0.csv
```

### "Classification tables not found"

**Cause:** Database schema not initialized.

**Solution:**
```bash
# Run database migrations
psql $DATABASE_URL < init-scripts/unified-postgresql-schema.sql

# Verify tables exist
psql $DATABASE_URL -c "\dt"
```

---

## Cost Summary

| Data Source | Type | Cost | Frequency | Required |
|------------|------|------|-----------|----------|
| **UNSPSC** | Commercial License | ~$500 USD | One-time (updates ~$200/year) | **Yes** |
| **ETIM** | Membership | Varies by tier | Annual | Optional |

**Total Initial Cost:** $500 USD (UNSPSC only) to $500+ USD (UNSPSC + ETIM)

**Note:** Both UNSPSC and ETIM provide significant value for product classification and are industry-standard solutions. The costs are justified by the comprehensive, maintained, and legally licensed data.

---

## Support and Resources

### UNSPSC
- **Website:** https://www.unspsc.org/
- **Purchase:** https://www.unspsc.org/purchase-unspsc
- **Support:** support@unspsc.org
- **Documentation:** https://www.unspsc.org/resources
- **Training:** https://www.unspsc.org/training

### ETIM
- **Website:** https://www.etim-international.com/
- **Membership:** https://www.etim-international.com/become-a-member/
- **Portal:** https://portal.etim-international.com/ (members only)
- **Support:** info@etim-international.com
- **Documentation:** Available in member portal

### Horme POV Project
- **Integration Code:** `src/integrations/etim_client.py`, `src/integrations/unspsc_client.py`
- **Data Loader:** `scripts/load_classification_data.py`
- **Classifier:** `src/core/product_classifier.py`
- **Database Schema:** `init-scripts/unified-postgresql-schema.sql`

---

## Compliance and Legal

**IMPORTANT LEGAL NOTICES:**

### UNSPSC
- Data is **copyrighted** by UNSPSC
- **Commercial license required** for business use
- **Cannot redistribute** UNSPSC data files
- **Must purchase** individual licenses for each organization

### ETIM
- Data is **proprietary** to ETIM International
- **Membership required** for access
- **Cannot redistribute** ETIM data files
- **API access** governed by member agreement

### This Project
- **No classification data** is included in this repository
- **Users must obtain** their own UNSPSC and ETIM data
- **Data loading scripts** are provided for convenience
- **No warranty** on classification accuracy

---

**Last Updated:** 2025-10-17
**Version:** 1.0
**Maintained By:** Horme POV Development Team
