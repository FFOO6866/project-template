# Salary Pricing Algorithm Documentation

## Overview

The Job Pricing Engine uses a sophisticated multi-factor algorithm to calculate competitive salary recommendations for job positions. The algorithm considers experience, location, skills, industry, and company size to generate accurate, data-driven salary bands.

## Algorithm Formula

The final adjusted salary is calculated using the following formula:

```
Adjusted Salary = Base Salary
                × Experience Multiplier
                × Location Multiplier
                × (1 + Skill Premium)
                × Industry Adjustment
                × Company Size Factor
```

## Calculation Steps

### 1. Base Salary Determination

The base salary is determined by classifying the position into one of five experience levels:

| Experience Level | Years | Annual Base Salary (SGD) |
|-----------------|-------|--------------------------|
| Entry | 0-2 years | 45,000 - 65,000 |
| Junior | 2-4 years | 60,000 - 85,000 |
| Mid | 4-7 years | 85,000 - 120,000 |
| Senior | 7-10 years | 120,000 - 170,000 |
| Lead | 10+ years | 170,000 - 250,000 |

**Calculation**: The midpoint of the range is used as the base salary.

**Example**:
- Position requires 5-7 years experience
- Average: 6 years → **Mid level**
- Base salary: (85,000 + 120,000) / 2 = **SGD 102,500**

### 2. Experience Multiplier

Progressive multiplier based on years of experience:

```
Experience Multiplier = min(1.0 + (years × 0.03), 1.45)
```

- **3% increase per year** of experience
- **Capped at 1.45x** (equivalent to 15 years experience)

**Examples**:
- 0 years: 1.00x (no multiplier)
- 5 years: 1.15x (+15%)
- 10 years: 1.30x (+30%)
- 15+ years: 1.45x (+45%, capped)

### 3. Location Multiplier

Cost-of-living adjustment based on geographic location:

| Location | Multiplier | Rationale |
|----------|-----------|-----------|
| Singapore | 1.00x | Base reference |
| Other locations | Variable | From `location_index` table |

- Looks up `cost_of_living_index` from database
- Falls back to 1.00x if location not found
- Case-insensitive matching

**Example**:
- Singapore: 1.00x (no adjustment)
- High-cost city: 1.25x (+25%)
- Lower-cost region: 0.85x (-15%)

### 4. Skill Premium

Additional premium for in-demand technical skills:

**High-Value Skills** (2% premium each):
- Python
- AWS
- Kubernetes
- Machine Learning
- React
- TypeScript
- Terraform

**Formula**:
```
Skill Premium = min(count(high_value_skills) × 0.02, 0.20)
```

- **2% per high-value skill**
- **Capped at 20%** maximum

**Examples**:
- No high-value skills: 0%
- 3 high-value skills (Python, AWS, Kubernetes): 6%
- 10+ high-value skills: 20% (capped)

### 5. Industry Adjustment

Industry-specific salary factors:

| Industry | Factor | Adjustment |
|----------|--------|------------|
| Finance | 1.20x | +20% |
| Technology | 1.15x | +15% |
| Consulting | 1.10x | +10% |
| Healthcare | 1.05x | +5% |
| Manufacturing | 1.00x | Base |
| Government | 0.95x | -5% |
| Retail | 0.95x | -5% |
| Education | 0.90x | -10% |
| Default | 1.00x | Base |

### 6. Company Size Factor

Company size scaling:

| Company Size | Employees | Factor |
|-------------|-----------|--------|
| 1-10 | Startup | 0.85x |
| 11-50 | Small | 0.90x |
| 51-200 | Medium | 1.00x |
| 201-500 | Large | 1.10x |
| 501-1000 | Enterprise | 1.15x |
| 1000+ | Corporation | 1.20x |
| Default | Unknown | 1.00x |

## Salary Band Generation

From the adjusted salary, the system generates a comprehensive salary band:

### Recommended Range
- **Minimum**: Target × 0.80 (80%)
- **Maximum**: Target × 1.20 (120%)
- **Spread**: ±20% from target

### Percentile Distribution
| Percentile | Formula | Description |
|-----------|---------|-------------|
| P10 | Target × 0.75 | 10th percentile |
| P25 | Target × 0.90 | 25th percentile |
| P50 | Target × 1.00 | Median (target) |
| P75 | Target × 1.10 | 75th percentile |
| P90 | Target × 1.25 | 90th percentile |

## Confidence Scoring

The system calculates a confidence score (0-100) to indicate reliability:

### Base Confidence
- **Starting point**: 70%

### Confidence Bonuses
| Factor | Bonus | Condition |
|--------|-------|-----------|
| Job Description Quality | +10% | Length > 100 characters |
| Skills Match Rate | +10% × rate | Proportion of skills matched to SSG TSC |
| Experience Data | +5% | Both min and max years provided |
| Location Data | +5% | Location specified |

### Confidence Levels
- **High**: ≥85%
- **Medium**: 70-84%
- **Low**: <70%

**Example Calculation**:
```
Base: 70%
+ Good description (200 chars): +10%
+ Skills match (50%): +5%
+ Experience data: +5%
+ Location data: +5%
= 95% (High confidence)
```

## Complete Example

### Input
```json
{
  "job_title": "Senior Data Engineer",
  "years_of_experience_min": 8,
  "years_of_experience_max": 12,
  "location_text": "Singapore",
  "industry": "Finance",
  "company_size": "1000+",
  "skills": ["Python", "AWS", "Kubernetes", "Machine Learning", "TypeScript", "React"]
}
```

### Calculation Steps

1. **Base Salary**:
   - Average experience: (8 + 12) / 2 = 10 years → **Lead level**
   - Base: (170,000 + 250,000) / 2 = **SGD 210,000**

2. **Experience Multiplier**:
   - 10 years: 1.0 + (10 × 0.03) = **1.30x**

3. **Location Multiplier**:
   - Singapore: **1.00x**

4. **Skill Premium**:
   - 6 high-value skills: 6 × 0.02 = **0.12** (12%)

5. **Industry Adjustment**:
   - Finance: **1.20x**

6. **Company Size Factor**:
   - 1000+: **1.20x**

7. **Adjusted Salary**:
   ```
   210,000 × 1.30 × 1.00 × 1.12 × 1.20 × 1.20
   = SGD 416,793
   ```

8. **Salary Band**:
   - **Target**: SGD 416,793
   - **Min**: SGD 333,434 (80%)
   - **Max**: SGD 500,152 (120%)
   - **P10**: SGD 312,595
   - **P25**: SGD 375,114
   - **P50**: SGD 416,793
   - **P75**: SGD 458,472
   - **P90**: SGD 520,991

9. **Confidence Score**:
   ```
   70% (base)
   + 10% (good description)
   + 8% (6/8 skills matched = 75%)
   + 5% (experience data)
   + 5% (location data)
   = 98% (High confidence)
   ```

### Output
```json
{
  "currency": "SGD",
  "period": "annual",
  "target_salary": 416793,
  "recommended_min": 333434,
  "recommended_max": 500152,
  "p10": 312595,
  "p25": 375114,
  "p50": 416793,
  "p75": 458472,
  "p90": 520991,
  "confidence_score": 98.0,
  "confidence_level": "High",
  "summary_text": "Based on the job title 'Senior Data Engineer' with 8-12 years of experience in Finance industry, we recommend an annual salary range of SGD 333,434 to SGD 500,152, with a target of SGD 416,793. This estimate has high confidence."
}
```

## Configuration

### Modifying Factors

To adjust pricing factors, edit `src/job_pricing/services/pricing_calculation_service.py`:

#### Base Salary Ranges
```python
BASE_SALARY_BY_EXPERIENCE = {
    "entry": (45000, 65000),
    "junior": (60000, 85000),
    "mid": (85000, 120000),
    "senior": (120000, 170000),
    "lead": (170000, 250000),
}
```

#### Industry Factors
```python
INDUSTRY_FACTORS = {
    "Technology": 1.15,
    "Finance": 1.20,
    # Add or modify industries here
}
```

#### Company Size Factors
```python
COMPANY_SIZE_FACTORS = {
    "1-10": 0.85,
    "11-50": 0.90,
    # Add or modify size ranges here
}
```

#### High-Value Skills
```python
high_value_skills = {
    "python",
    "aws",
    "kubernetes",
    # Add skills here
}
```

### Experience Multiplier Parameters
```python
# Current: 3% per year, capped at 1.45x
return min(1.0 + (avg_years * 0.03), 1.45)

# To adjust: change 0.03 (percentage) or 1.45 (cap)
```

### Skill Premium Parameters
```python
# Current: 2% per skill, capped at 20%
return min(matched_high_value * 0.02, 0.20)

# To adjust: change 0.02 (percentage) or 0.20 (cap)
```

## API Usage

### Create Pricing Request
```bash
POST /api/v1/job-pricing/requests
```

```json
{
  "job_title": "Senior Software Engineer",
  "job_description": "Looking for experienced engineer with Python, AWS, and Kubernetes skills...",
  "years_of_experience_min": 5,
  "years_of_experience_max": 8,
  "location_text": "Singapore",
  "industry": "Technology",
  "company_size": "201-500",
  "urgency": "normal",
  "requestor_email": "hr@company.com"
}
```

### Check Status
```bash
GET /api/v1/job-pricing/requests/{request_id}/status
```

### Get Results
```bash
GET /api/v1/job-pricing/results/{request_id}
```

## Data Sources

The pricing algorithm uses:

1. **Internal Calculations**: Base salaries, multipliers, and factors
2. **SSG TSC Taxonomy**: Skills matching and validation
3. **Location Index**: Cost-of-living adjustments (when available)

Future enhancements may include:
- Mercer IPE salary data integration
- Real-time market data feeds
- Historical salary trends
- Company-specific benchmarks

## Limitations and Considerations

### Current Limitations
1. **Singapore-Centric**: Base salaries are calibrated for Singapore market
2. **Static Factors**: Industry and company size multipliers are fixed
3. **Limited Skills Database**: Only tracks specific high-value skills
4. **No Real-Time Data**: Does not incorporate live market data yet

### Important Notes
- **Benefits Excluded**: Salary recommendations do not include bonuses, stock options, or benefits
- **Candidate Quality**: Actual offers may vary based on individual candidate qualifications
- **Market Fluctuations**: Recommendations should be reviewed periodically
- **Industry Variations**: Some industries may have unique compensation structures

### Confidence Interpretation
- **High (≥85%)**: Strong recommendation with good data quality
- **Medium (70-84%)**: Reasonable estimate, some data gaps
- **Low (<70%)**: Limited data, use with caution

## Best Practices

### For Accurate Pricing
1. **Provide Detailed Job Descriptions**: Longer, detailed descriptions improve confidence
2. **Specify Experience Ranges**: Both min and max years for better classification
3. **Include Location**: Enables cost-of-living adjustments
4. **List Key Skills**: Helps identify high-value skill premiums
5. **Specify Industry**: Applies appropriate market factors

### For Interpretation
1. **Use Salary Bands**: Don't rely solely on target, consider the range
2. **Check Confidence Score**: Higher confidence = more reliable
3. **Consider Percentiles**: P75-P90 for competitive offers, P25-P50 for entry offers
4. **Review Key Factors**: Understand what drove the recommendation
5. **Account for Intangibles**: Algorithm doesn't capture all value (culture fit, unique skills, etc.)

## Maintenance

### Regular Review Schedule
- **Quarterly**: Review base salary ranges
- **Semi-Annual**: Update industry and company size factors
- **Annual**: Comprehensive algorithm review and calibration
- **As Needed**: Add new high-value skills, adjust multipliers

### Monitoring
Track these metrics to ensure accuracy:
- Actual offers vs. recommendations
- Confidence score distribution
- Skills match rates
- Location coverage

## Support

For questions or issues:
- **Technical Issues**: Check logs in `logs/` directory
- **Configuration**: Review `src/job_pricing/services/pricing_calculation_service.py`
- **API Errors**: Check API logs in Docker: `docker-compose logs api`
- **Algorithm Questions**: Refer to this documentation or review unit tests in `tests/unit/test_pricing_calculation_service.py`

## Version History

### Version 1.0 (Current)
- Multi-factor pricing algorithm
- Experience-based classification
- Location, industry, and company size adjustments
- Skill premium calculation
- Confidence scoring
- Percentile distribution
- SGD currency, annual period

### Future Enhancements
- Multi-currency support
- Machine learning price predictions
- Real-time market data integration
- Company-specific benchmarking
- Historical trend analysis
- Advanced skill taxonomy
- Regional salary variation modeling
