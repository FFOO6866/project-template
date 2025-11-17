# Mercer Data Files

This directory contains proprietary Mercer data files.

## 📁 Expected Files

### Mercer_Job_Library_2024.xlsx
**Source**: Mercer Job Library (proprietary)
**Records**: ~18,000 jobs
**Last Updated**: 2024-01-01

**Required Sheets**:
- `Job Library` - Main job data

**Required Columns**:
- `job_code` (e.g., "ICT.02.003.M40")
- `job_title`
- `family`
- `sub_family`
- `career_level` (M1-M6, P1-P6, E1-E5)
- `job_description`
- `critical_work_functions`
- `key_responsibilities`
- `ipe_minimum`
- `ipe_midpoint`
- `ipe_maximum`

### Mercer_Market_Data_2024.xlsx
**Source**: Mercer Compensation Survey (proprietary)
**Records**: ~5,000 benchmark cuts
**Last Updated**: 2024-Q3

**Required Columns**:
- `job_code` (links to Job Library)
- `country_code`
- `location`
- `industry`
- `company_size`
- `benchmark_cut` (P25, P50, P75, P90)
- `base_salary`
- `total_cash`
- `survey_date`
- `currency`

## ⚠️ Important

- **These files are PROPRIETARY and CONFIDENTIAL**
- Do NOT commit to version control
- Do NOT share externally without authorization
- Follow Mercer licensing agreements
- Files are excluded in `.gitignore`

## 📝 Obtaining Files

Contact Mercer account manager or HR/Compensation team to obtain:
1. Latest Mercer Job Library export
2. Latest Mercer Market Data export (Singapore focus)

## 🔒 Data Security

- Store files in secure location
- Encrypt if storing outside corporate network
- Delete after loading into database (keep backups encrypted)
- Follow company data security policies
