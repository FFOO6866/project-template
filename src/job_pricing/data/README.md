# Data Directory

This directory contains all data-related files for the Job Pricing Engine.

## 📁 Directory Structure

```
data/
├── raw/                    # Raw source files (Excel, CSV, JSON)
│   ├── mercer/            # Mercer Job Library and Market Data
│   └── ssg/               # SSG Skills Framework files
├── ingestion/             # Data ingestion scripts
├── validation/            # Data validation utilities
└── backups/               # Database backups
```

## 📋 Data Sources

### Mercer Job Library
- **File**: `raw/mercer/Mercer_Job_Library_2024.xlsx`
- **Records**: ~18,000 jobs
- **Update Frequency**: Annual
- **Owner**: Mercer Consulting

### SSG Skills Framework
- **Files**:
  - `raw/ssg/SSG_Job_Roles_2024.xlsx` (~500 roles)
  - `raw/ssg/SSG_TSC_2024.xlsx` (~3,000 skills)
  - `raw/ssg/SSG_Job_Role_TSC_Mappings_2024.xlsx` (~10,000 mappings)
- **Update Frequency**: Quarterly
- **Owner**: SkillsFuture Singapore (SSG)
- **Source**: https://www.skillsfuture.gov.sg/skills-framework

### Mercer Market Data
- **File**: `raw/mercer/Mercer_Market_Data_2024.xlsx`
- **Records**: ~5,000 benchmark cuts
- **Update Frequency**: Quarterly (survey cycles)
- **Owner**: Mercer Consulting

## 🚀 Usage

### Initial Data Load

```bash
# Load Mercer Job Library
python -m data.ingestion.mercer_job_library_loader \
    --file data/raw/mercer/Mercer_Job_Library_2024.xlsx \
    --batch-size 100

# Generate embeddings
python -m data.ingestion.generate_embeddings \
    --batch-size 100 \
    --rate-limit 3500

# Load SSG data
python -m data.ingestion.ssg_job_roles_loader \
    --file data/raw/ssg/SSG_Job_Roles_2024.xlsx

python -m data.ingestion.ssg_tsc_loader \
    --file data/raw/ssg/SSG_TSC_2024.xlsx

python -m data.ingestion.ssg_mappings_loader \
    --file data/raw/ssg/SSG_Job_Role_TSC_Mappings_2024.xlsx

# Load Mercer market data
python -m data.ingestion.mercer_market_data_loader \
    --file data/raw/mercer/Mercer_Market_Data_2024.xlsx
```

### Full Refresh

```bash
python -m data.ingestion.full_refresh \
    --backup-dir data/backups/$(date +%Y-%m-%d) \
    --confirm
```

### Incremental Update

```bash
python -m data.ingestion.incremental_update \
    --source mercer \
    --file data/raw/mercer/Mercer_Job_Library_2024_Q4.xlsx
```

## 📊 Data Quality

### Validation

```bash
# Validate all data
python -m data.validation.validate_all

# Validate specific source
python -m data.validation.validate_mercer
python -m data.validation.validate_ssg
```

### Quality Metrics

```bash
# Generate quality report
python -m data.validation.quality_metrics \
    --output reports/quality_$(date +%Y-%m-%d).html
```

## ⚠️ Important Notes

### Data Licensing
- **Mercer data is proprietary** and covered by licensing agreements
- Do NOT commit Mercer data files to version control
- Use `.gitignore` to exclude `data/raw/mercer/*.xlsx`

### SSG Data
- **SSG data is public** but check license terms
- Attribution required when using SSG Skills Framework
- Keep data current (check for updates quarterly)

### Data Security
- Raw files may contain sensitive information
- Do NOT store in public repositories
- Use encryption for backups containing real data
- Follow PDPA guidelines for employee data

## 🗂️ .gitignore Rules

```gitignore
# Raw data files (proprietary)
data/raw/mercer/*.xlsx
data/raw/mercer/*.csv

# SSG data (public but large)
data/raw/ssg/*.xlsx

# Backups
data/backups/

# Processed data
data/processed/
```

## 📚 Related Documentation

- Phase 3 Todo: `todos/active/003-phase3-data-ingestion.md`
- Data Sources Guide: `docs/data_sources.md`
- Data Ingestion Guide: `docs/data_ingestion_guide.md`
