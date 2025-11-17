# SSG Skills Framework Files

This directory contains SkillsFuture Singapore (SSG) Skills Framework data.

## 📁 Expected Files

### SSG_Job_Roles_2024.xlsx
**Source**: SkillsFuture Singapore Skills Framework
**URL**: https://www.skillsfuture.gov.sg/skills-framework
**Records**: ~500 job roles across 38 sectors
**Last Updated**: 2024-Q2

**Required Columns**:
- `job_role_code` (e.g., "ICT-DIS-4010-1.1")
- `job_role_title`
- `sector`
- `sub_sector`
- `track`
- `career_level` (e.g., "Senior/Lead", "Manager")
- `job_role_description`
- `critical_work_functions`

**Sectors Covered** (38 total):
- Information & Communications Technology (ICT)
- Finance
- Healthcare
- Manufacturing
- Retail
- Hospitality
- ... and 32 more

### SSG_TSC_2024.xlsx
**Source**: SkillsFuture Singapore Technical Skills & Competencies
**URL**: https://www.skillsfuture.gov.sg/skills-framework
**Records**: ~3,000 technical skills
**Last Updated**: 2024-Q2

**Required Columns**:
- `tsc_code` (e.g., "ICT-DIS-4010-1.1-A")
- `skill_title`
- `skill_category`
- `skill_description`
- `proficiency_level` (1-6)
- `programs_of_study` (optional)

**Proficiency Levels**:
1. Basic Awareness
2. Working Knowledge
3. Application
4. Synthesis
5. Expert
6. Mastery

### SSG_Job_Role_TSC_Mappings_2024.xlsx
**Source**: SkillsFuture Singapore Mappings
**URL**: https://www.skillsfuture.gov.sg/skills-framework
**Records**: ~10,000 job role → TSC relationships
**Last Updated**: 2024-Q2

**Required Columns**:
- `job_role_code`
- `tsc_code`
- `required_proficiency_level`
- `is_critical` (Yes/No)

## 📥 Downloading Files

### Option 1: Official SSG Website
1. Visit https://www.skillsfuture.gov.sg/skills-framework
2. Select sector (e.g., "Information & Communications Technology")
3. Download Excel files for:
   - Job Roles
   - TSC (Skills)
   - Job Role-TSC Mappings

### Option 2: SSG Skills Framework Portal
1. Register at https://www.myskillsfuture.gov.sg/
2. Access Skills Framework section
3. Bulk download available for all sectors

### Option 3: API Access (if available)
- Check SSG website for API documentation
- May require API key registration

## 🔄 Update Frequency

- **Job Roles**: Updated quarterly
- **TSC**: Updated quarterly
- **Mappings**: Updated when roles or TSC change

**Recommended**: Check for updates every 3 months

## 📜 Data License

**SkillsFuture Singapore Open Data License**:
- Data is publicly available
- Free to use for commercial and non-commercial purposes
- **Attribution required**: Must acknowledge "SkillsFuture Singapore Skills Framework"
- Check official license terms for updates

**Example Attribution**:
```
Job role and skills data sourced from SkillsFuture Singapore Skills Framework
https://www.skillsfuture.gov.sg/skills-framework
```

## 🔍 Data Quality Notes

- **Job Role Codes**: Some codes may change between versions
- **Sector Names**: May vary slightly (e.g., "ICT" vs "Information & Communications Technology")
- **Proficiency Levels**: Consistently use 1-6 scale
- **Mappings**: Some job roles may have 50+ skills mapped

## 📊 Expected Data Volume

| File Type | Records | Size (approx) |
|-----------|---------|---------------|
| Job Roles | 500 | 2-5 MB |
| TSC | 3,000 | 5-10 MB |
| Mappings | 10,000 | 3-8 MB |
| **Total** | **13,500** | **10-23 MB** |

## 🚀 Processing Tips

1. **Validate Job Role Codes**: Check for duplicates or invalid formats
2. **Normalize Sector Names**: Create mapping for variations
3. **Clean Descriptions**: Remove extra whitespace, HTML tags
4. **Validate Foreign Keys**: Ensure mappings reference valid roles and TSC
5. **Handle Missing Data**: Some fields may be optional or missing

## 📚 Related Documentation

- SSG Official Documentation: https://www.skillsfuture.gov.sg/skills-framework
- Data Ingestion Guide: `docs/data_ingestion_guide.md`
- Phase 3 Todo: `todos/active/003-phase3-data-ingestion.md`
