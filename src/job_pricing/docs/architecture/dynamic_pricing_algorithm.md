# Dynamic Pricing Algorithm Specification

**Version**: 1.0
**Date**: 2025-01-10
**Status**: Production-Ready

## Overview

The Dynamic Job Pricing Algorithm is the core intelligence engine that generates compensation recommendations by aggregating data from multiple sources, applying AI-powered job matching, and producing confidence-scored pricing bands. This document defines the complete algorithm flow, data sources, weighting methodology, and output specifications.

## Algorithm Objectives

1. **Accuracy**: Provide market-competitive compensation recommendations within ±10% of actual market rates
2. **Transparency**: Explain how each data source contributes to the final recommendation
3. **Confidence**: Quantify certainty levels to guide HR decision-making
4. **Speed**: Generate recommendations in <5 seconds (P95 latency)
5. **Fairness**: Eliminate bias through objective, data-driven methodology

## High-Level Algorithm Flow

```
┌─────────────────┐
│  User Input     │ Job Title, Description, Location,
│  (10 fields)    │ Grade, Skills, etc.
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 1: Job Standardization & Enrichment               │
│ - Clean and normalize input                            │
│ - Extract skills using NER + SSG mapping               │
│ - Map to Mercer job code (AI-powered matching)         │
│ - Determine position class                             │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 2: Multi-Source Data Aggregation                  │
│                                                         │
│ ┌─────────────────┐  ┌─────────────────┐              │
│ │ Mercer Market   │  │ SSG Skills      │              │
│ │ Data (40%)      │  │ Framework       │              │
│ └─────────────────┘  └─────────────────┘              │
│                                                         │
│ ┌─────────────────┐  ┌─────────────────┐              │
│ │ My Careers      │  │ Glassdoor       │              │
│ │ Future (25%)    │  │ Data (15%)      │              │
│ └─────────────────┘  └─────────────────┘              │
│                                                         │
│ ┌─────────────────┐                                    │
│ │ Internal HRIS   │  Applicant Data (5%)               │
│ │ (15%)           │                                    │
│ └─────────────────┘                                    │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 3: Weighted Aggregation & Normalization           │
│ - Apply source-specific weights                        │
│ - Normalize to same currency/time period               │
│ - Adjust for location cost-of-living                   │
│ - Apply recency weighting                              │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 4: Statistical Analysis & Band Generation         │
│ - Calculate P10, P25, P50, P75, P90 percentiles        │
│ - Generate recommended salary range                    │
│ - Apply internal grade constraints                     │
│ - Calculate confidence scores                          │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 5: Output Generation                              │
│ - Recommended salary range (P25-P75)                   │
│ - Full percentile distribution                         │
│ - Source contribution breakdown                        │
│ - Confidence score (0-100)                             │
│ - Recommendation explanation                           │
│ - Alternative scenarios                                │
└─────────────────────────────────────────────────────────┘
```

## STEP 1: Job Standardization & Enrichment

### Input Data Structure

```python
{
    "job_title": str,              # Required
    "job_description": str,        # Required
    "location": str,               # Required (e.g., "Singapore", "Central")
    "portfolio": str,              # Optional
    "department": str,             # Optional
    "employment_type": str,        # Required (Full-time, Contract, Part-time)
    "internal_grade": str,         # Required (e.g., "8", "9", "10")
    "job_family": str,             # Required (e.g., "Engineering", "HR")
    "skills": List[str],           # Optional (extracted if not provided)
    "alternative_titles": List[str] # Optional
}
```

### 1.1: Input Validation & Cleaning

**System Touchpoint**: Input Validation Service

```python
def validate_and_clean_input(job_data: Dict) -> Dict:
    """
    Validate required fields and clean input data.

    Validation Rules:
    - job_title: 5-200 characters
    - job_description: 50-5000 characters
    - location: Must be valid Singapore location
    - internal_grade: Must be in range 1-15
    - employment_type: Must be in ['Full-time', 'Contract', 'Part-time']
    """

    cleaned_data = {
        "job_title": job_data["job_title"].strip().title(),
        "job_description": job_data["job_description"].strip(),
        "location": standardize_location(job_data["location"]),
        "internal_grade": str(job_data["internal_grade"]),
        "employment_type": job_data["employment_type"],
        "job_family": job_data["job_family"]
    }

    return cleaned_data
```

### 1.2: Skills Extraction (If Not Provided)

**System Touchpoint**: SSG Skills Extraction Workflow

**Data Source**: SSG SkillsFuture Framework (38 sectors, 18,000+ skills)

```python
def extract_skills(job_description: str, job_family: str) -> List[Dict]:
    """
    Extract skills from job description using:
    1. Named Entity Recognition (NER) with LLM
    2. Fuzzy matching to SSG TSC database
    3. Confidence scoring

    Returns: [
        {
            "skill_name": "Python Programming",
            "tsc_code": "ICT-DCA-3001-1.1",
            "proficiency_level": "Advanced",
            "confidence": 0.92
        }
    ]
    """

    # Use Kailash workflow (defined in ssg_skillsfuture_integration.md)
    workflow = build_skills_extraction_workflow(job_description, job_family)
    results, run_id = runtime.execute(workflow.build())

    return results["matched_skills"]
```

### 1.3: Mercer Job Mapping

**System Touchpoint**: Mercer Job Mapping Workflow

**Data Source**: Mercer Job Library (18,000+ standardized jobs)

**Algorithm**:
1. Generate embedding for input job (title + description)
2. Vector similarity search against Mercer library
3. Rule-based validation (family match, grade alignment, skills overlap)
4. LLM re-ranking for best match
5. Confidence scoring

```python
def map_to_mercer_job(
    job_title: str,
    job_description: str,
    job_family: str,
    internal_grade: str,
    skills: List[str]
) -> Dict:
    """
    Map user job to Mercer Job Library.

    Returns: {
        "mercer_job_code": "HRM.04.005.M50",
        "mercer_job_title": "Total Rewards Director",
        "position_class": 62,
        "career_level": "M5",
        "confidence_score": 0.87,
        "explanation": "Strong match based on...",
        "ipe_factors": {
            "impact": {"min": 325, "max": 405},
            "communication": {"min": 70, "max": 87},
            ...
        }
    }
    """

    # Use Kailash workflow (defined in mercer_ipe_integration.md)
    workflow = build_mercer_mapping_workflow(
        job_title, job_description, job_family, internal_grade, skills
    )
    results, run_id = runtime.execute(workflow.build())

    return results["mercer_match"]
```

**Output from Step 1**:
```python
{
    "standardized_job": {
        "job_title": "Senior Software Engineer",
        "job_description": "...",
        "location": "Central Business District",
        "internal_grade": "9",
        "employment_type": "Full-time",
        "job_family": "Engineering"
    },
    "extracted_skills": [
        {"skill": "Python", "tsc_code": "...", "confidence": 0.95},
        {"skill": "AWS", "tsc_code": "...", "confidence": 0.88}
    ],
    "mercer_mapping": {
        "job_code": "ICT.02.015.M40",
        "position_class": 58,
        "confidence": 0.89
    }
}
```

## STEP 2: Multi-Source Data Aggregation

### 2.1: Mercer Market Data (Weight: 40%)

**System Touchpoint**: Mercer Market Data API / Database

**Query Strategy**:
```sql
-- Query 1: Exact job match
SELECT p10, p25, p50, p75, p90, sample_size
FROM mercer_market_data
WHERE job_code = :mercer_job_code
  AND country_code = 'SG'
  AND benchmark_cut = 'by_job'
  AND survey_date >= NOW() - INTERVAL '18 months'
ORDER BY survey_date DESC
LIMIT 1;

-- Query 2: Job family + Career level match (fallback)
SELECT p10, p25, p50, p75, p90, sample_size
FROM mercer_market_data
WHERE job_code LIKE :family_prefix || '%'
  AND country_code = 'SG'
  AND benchmark_cut = 'by_family_career_level'
  AND career_level = :career_level
  AND survey_date >= NOW() - INTERVAL '18 months'
ORDER BY survey_date DESC
LIMIT 1;

-- Query 3: Position class range match (broader fallback)
SELECT AVG(p50) as median_salary, COUNT(*) as sample_size
FROM mercer_market_data
WHERE position_class BETWEEN :position_class - 2 AND :position_class + 2
  AND country_code = 'SG'
  AND survey_date >= NOW() - INTERVAL '18 months';
```

**Data Quality Scoring**:
```python
def score_mercer_data_quality(mercer_data: Dict) -> float:
    """
    Score Mercer data quality based on:
    - Match level (exact job > family+level > position class range)
    - Sample size (larger = better)
    - Data recency (newer = better)

    Returns: Quality score 0.0 - 1.0
    """

    quality_score = 0.0

    # Match level scoring
    if mercer_data["match_level"] == "exact_job":
        quality_score += 0.5
    elif mercer_data["match_level"] == "family_level":
        quality_score += 0.3
    else:
        quality_score += 0.1

    # Sample size scoring
    if mercer_data["sample_size"] >= 50:
        quality_score += 0.3
    elif mercer_data["sample_size"] >= 20:
        quality_score += 0.2
    else:
        quality_score += 0.1

    # Recency scoring
    months_old = (datetime.now() - mercer_data["survey_date"]).days / 30
    if months_old <= 6:
        quality_score += 0.2
    elif months_old <= 12:
        quality_score += 0.15
    else:
        quality_score += 0.05

    return quality_score
```

### 2.2: My Careers Future Data (Weight: 25%)

**System Touchpoint**: Scraped Job Listings Database

**Query Strategy**:
```sql
-- Match based on job title similarity + location
SELECT
    salary_min,
    salary_max,
    (salary_min + salary_max) / 2 as salary_midpoint,
    posted_date,
    company_name,
    similarity(job_title, :input_job_title) as title_similarity
FROM scraped_job_listings
WHERE source = 'my_careers_future'
  AND is_active = TRUE
  AND has_salary_data = TRUE
  AND location = :location
  AND similarity(job_title, :input_job_title) > 0.3
  AND posted_date >= NOW() - INTERVAL '90 days'
  AND employment_type = :employment_type
ORDER BY title_similarity DESC
LIMIT 100;
```

**Skills-Based Filtering**:
```python
def filter_by_skills_overlap(mcf_jobs: List[Dict], input_skills: List[str]) -> List[Dict]:
    """
    Filter MCF jobs by skills overlap.
    Keep jobs with at least 30% skill overlap.
    """

    filtered_jobs = []

    for job in mcf_jobs:
        job_skills = set(job.get("skills", []))
        input_skills_set = set(input_skills)

        if not job_skills or not input_skills_set:
            # No skills data, keep based on title match only
            filtered_jobs.append(job)
            continue

        overlap = len(job_skills & input_skills_set)
        total = len(job_skills | input_skills_set)
        jaccard_similarity = overlap / total if total > 0 else 0

        if jaccard_similarity >= 0.3:
            job["skills_match_score"] = jaccard_similarity
            filtered_jobs.append(job)

    return filtered_jobs
```

**Salary Aggregation**:
```python
def aggregate_mcf_salaries(filtered_jobs: List[Dict]) -> Dict:
    """
    Aggregate MCF salary data.

    Returns percentile distribution with confidence metrics.
    """

    salary_midpoints = [job["salary_midpoint"] for job in filtered_jobs]

    if len(salary_midpoints) < 5:
        return {"insufficient_data": True, "sample_size": len(salary_midpoints)}

    return {
        "p10": np.percentile(salary_midpoints, 10),
        "p25": np.percentile(salary_midpoints, 25),
        "p50": np.percentile(salary_midpoints, 50),
        "p75": np.percentile(salary_midpoints, 75),
        "p90": np.percentile(salary_midpoints, 90),
        "mean": np.mean(salary_midpoints),
        "std_dev": np.std(salary_midpoints),
        "sample_size": len(salary_midpoints),
        "data_source": "my_careers_future"
    }
```

### 2.3: Glassdoor Data (Weight: 15%)

**System Touchpoint**: Scraped Job Listings Database

**Query Strategy**: Similar to MCF, but with additional company rating filter

```sql
SELECT
    salary_min,
    salary_max,
    (salary_min + salary_max) / 2 as salary_midpoint,
    company_rating,
    company_size,
    industry
FROM scraped_job_listings
WHERE source = 'glassdoor'
  AND is_active = TRUE
  AND has_salary_data = TRUE
  AND location LIKE '%Singapore%'
  AND similarity(job_title, :input_job_title) > 0.3
  AND scraped_at >= NOW() - INTERVAL '90 days'
ORDER BY company_rating DESC NULLS LAST
LIMIT 50;
```

**Note**: Glassdoor salaries are often estimated, so lower weight applied.

### 2.4: Internal HRIS Data (Weight: 15%)

**System Touchpoint**: Company HRIS Database

**Query Strategy**:
```sql
-- Query internal employee salary data for similar roles
SELECT
    current_salary,
    years_of_experience,
    performance_rating,
    last_salary_review_date,
    department,
    location
FROM employees
WHERE job_title SIMILAR TO :job_title_pattern
  AND employment_status = 'Active'
  AND internal_grade = :internal_grade
  AND location = :location
ORDER BY last_salary_review_date DESC;
```

**Privacy & Compliance**:
- Anonymize individual employee data
- Aggregate only (minimum 5 employees per aggregation)
- Apply differential privacy techniques
- Comply with PDPA regulations

```python
def aggregate_internal_salaries(employees: List[Dict]) -> Dict:
    """
    Aggregate internal salary data with privacy protection.
    """

    if len(employees) < 5:
        return {"insufficient_data": True, "reason": "privacy_threshold"}

    salaries = [emp["current_salary"] for emp in employees]

    # Apply Laplace noise for differential privacy
    epsilon = 0.1  # Privacy budget
    sensitivity = max(salaries) - min(salaries)
    noise_scale = sensitivity / epsilon

    return {
        "p25": np.percentile(salaries, 25) + np.random.laplace(0, noise_scale),
        "p50": np.percentile(salaries, 50) + np.random.laplace(0, noise_scale),
        "p75": np.percentile(salaries, 75) + np.random.laplace(0, noise_scale),
        "sample_size": len(salaries),
        "data_source": "internal_hris",
        "privacy_protected": True
    }
```

### 2.5: Applicant Data (Weight: 5%)

**System Touchpoint**: Applicant Tracking System (ATS)

**Query Strategy**:
```sql
-- Query applicant salary expectations
SELECT
    expected_salary,
    current_salary,
    years_of_experience,
    application_date
FROM applicants
WHERE applied_job_title SIMILAR TO :job_title_pattern
  AND application_status IN ('Applied', 'Shortlisted', 'Interviewed')
  AND application_date >= NOW() - INTERVAL '180 days'
  AND location = :location;
```

**Data Quality Note**: Applicant data has lowest weight due to:
- Self-reported (may be inflated or deflated)
- Includes unsuccessful applicants
- High variance in expectations

## STEP 3: Weighted Aggregation & Normalization

### 3.1: Currency & Time Period Normalization

All salary data normalized to:
- **Currency**: SGD
- **Time Period**: Annual (per annum)
- **Exchange Rates**: Real-time rates from MAS API

```python
def normalize_salary(
    salary: float,
    currency: str,
    time_period: str,
    as_of_date: datetime
) -> float:
    """
    Normalize salary to SGD annual.
    """

    # Convert to SGD if needed
    if currency != "SGD":
        exchange_rate = get_exchange_rate(currency, "SGD", as_of_date)
        salary = salary * exchange_rate

    # Convert to annual
    if time_period == "monthly":
        salary = salary * 12
    elif time_period == "hourly":
        salary = salary * 2080  # Assuming 40 hours/week * 52 weeks

    return salary
```

### 3.2: Location Cost-of-Living Adjustment

**System Touchpoint**: Singapore Location Index Database

```python
# Singapore location cost-of-living index (CBD = 1.0 baseline)
LOCATION_INDEX = {
    "Central Business District": 1.0,
    "Orchard Road": 0.98,
    "Marina Bay": 1.02,
    "Jurong": 0.85,
    "Woodlands": 0.82,
    "Tampines": 0.88,
    "Punggol": 0.83
}

def adjust_for_location(salary: float, location: str) -> float:
    """
    Adjust salary based on location cost-of-living.
    """
    index = LOCATION_INDEX.get(location, 0.90)  # Default to 0.90 for other areas
    return salary * index
```

### 3.3: Recency Weighting

More recent data weighted higher:

```python
def calculate_recency_weight(data_date: datetime) -> float:
    """
    Calculate recency weight with exponential decay.
    Data older than 18 months receives minimal weight.
    """

    months_old = (datetime.now() - data_date).days / 30

    if months_old <= 3:
        return 1.0
    elif months_old <= 6:
        return 0.95
    elif months_old <= 12:
        return 0.85
    elif months_old <= 18:
        return 0.70
    else:
        return 0.50  # Old data still considered but heavily discounted
```

### 3.4: Source-Weighted Aggregation

**Core Algorithm**:

```python
def calculate_weighted_percentiles(data_sources: Dict) -> Dict:
    """
    Calculate weighted salary percentiles from multiple sources.

    Args:
        data_sources: {
            "mercer": {"p25": 60000, "p50": 75000, "p75": 90000, "quality": 0.9},
            "mcf": {"p25": 58000, "p50": 72000, "p75": 88000, "quality": 0.85},
            "glassdoor": {"p25": 55000, "p50": 70000, "p75": 85000, "quality": 0.70},
            "internal": {"p25": 62000, "p50": 76000, "p75": 92000, "quality": 0.95},
            "applicant": {"p25": 65000, "p50": 80000, "p75": 95000, "quality": 0.60}
        }

    Returns:
        Weighted percentiles with confidence metrics
    """

    # Base weights
    BASE_WEIGHTS = {
        "mercer": 0.40,
        "mcf": 0.25,
        "glassdoor": 0.15,
        "internal": 0.15,
        "applicant": 0.05
    }

    # Adjust weights based on data quality
    adjusted_weights = {}
    total_weight = 0.0

    for source, data in data_sources.items():
        if not data or data.get("insufficient_data"):
            adjusted_weights[source] = 0.0
            continue

        base_weight = BASE_WEIGHTS.get(source, 0.0)
        quality_score = data.get("quality", 0.5)
        recency_weight = calculate_recency_weight(data.get("data_date", datetime.now()))

        # Adjusted weight = base * quality * recency
        adjusted_weights[source] = base_weight * quality_score * recency_weight
        total_weight += adjusted_weights[source]

    # Normalize weights to sum to 1.0
    if total_weight > 0:
        for source in adjusted_weights:
            adjusted_weights[source] /= total_weight

    # Calculate weighted percentiles
    percentiles = {}
    for percentile in ["p10", "p25", "p50", "p75", "p90"]:
        weighted_value = 0.0

        for source, data in data_sources.items():
            if adjusted_weights.get(source, 0) > 0:
                value = data.get(percentile, data.get("p50", 0))  # Fallback to median
                weighted_value += value * adjusted_weights[source]

        percentiles[percentile] = round(weighted_value, 2)

    return {
        "percentiles": percentiles,
        "weights_applied": adjusted_weights,
        "total_sources": len([w for w in adjusted_weights.values() if w > 0])
    }
```

## STEP 4: Statistical Analysis & Band Generation

### 4.1: Recommended Salary Range

**Industry Standard**: P25 (conservative) to P75 (competitive)

```python
def generate_recommended_range(percentiles: Dict, internal_grade: str) -> Dict:
    """
    Generate recommended salary range.

    Apply internal grade constraints to ensure consistency.
    """

    # Base recommendation: P25 to P75
    recommended_min = percentiles["p25"]
    recommended_max = percentiles["p75"]
    target_salary = percentiles["p50"]

    # Apply internal grade constraints
    grade_constraints = get_grade_salary_bands(internal_grade)

    if recommended_min < grade_constraints["absolute_min"]:
        recommended_min = grade_constraints["absolute_min"]

    if recommended_max > grade_constraints["absolute_max"]:
        recommended_max = grade_constraints["absolute_max"]

    # Ensure minimum spread of 20%
    spread = (recommended_max - recommended_min) / recommended_min
    if spread < 0.20:
        midpoint = (recommended_min + recommended_max) / 2
        recommended_min = midpoint * 0.90
        recommended_max = midpoint * 1.10

    return {
        "recommended_min": round(recommended_min, 2),
        "recommended_max": round(recommended_max, 2),
        "target_salary": round(target_salary, 2),
        "salary_spread_pct": round(spread * 100, 2)
    }
```

### 4.2: Internal Grade Bands

**System Touchpoint**: Company Grade Structure Configuration

```python
# Example grade structure (configurable per company)
GRADE_BANDS = {
    "8": {"absolute_min": 50000, "absolute_max": 75000, "market_position": 0.50},
    "9": {"absolute_min": 70000, "absolute_max": 95000, "market_position": 0.55},
    "10": {"absolute_min": 90000, "absolute_max": 120000, "market_position": 0.60},
    "11": {"absolute_min": 115000, "absolute_max": 150000, "market_position": 0.65},
    "12": {"absolute_min": 145000, "absolute_max": 190000, "market_position": 0.70},
}

def get_grade_salary_bands(internal_grade: str) -> Dict:
    """
    Retrieve salary bands for internal grade.
    """
    return GRADE_BANDS.get(internal_grade, {
        "absolute_min": 40000,
        "absolute_max": 200000,
        "market_position": 0.50
    })
```

### 4.3: Confidence Score Calculation

**Multi-Factor Confidence Scoring**:

```python
def calculate_confidence_score(
    mercer_match_confidence: float,
    data_quality_scores: Dict,
    sample_sizes: Dict,
    data_consistency: float
) -> Dict:
    """
    Calculate overall confidence score (0-100).

    Factors:
    1. Mercer job match quality (30%)
    2. Data source quality (30%)
    3. Sample sizes adequacy (20%)
    4. Cross-source consistency (20%)
    """

    # Factor 1: Mercer match confidence
    mercer_score = mercer_match_confidence * 30

    # Factor 2: Average data quality across sources
    quality_values = [q for q in data_quality_scores.values() if q > 0]
    avg_quality = np.mean(quality_values) if quality_values else 0.5
    quality_score = avg_quality * 30

    # Factor 3: Sample size adequacy
    total_samples = sum(sample_sizes.values())
    if total_samples >= 100:
        sample_score = 20
    elif total_samples >= 50:
        sample_score = 15
    elif total_samples >= 20:
        sample_score = 10
    else:
        sample_score = 5

    # Factor 4: Cross-source consistency (measured by coefficient of variation)
    consistency_score = data_consistency * 20

    # Total confidence score
    total_confidence = mercer_score + quality_score + sample_score + consistency_score

    # Classify confidence level
    if total_confidence >= 80:
        confidence_level = "High"
        recommendation = "Proceed with confidence"
    elif total_confidence >= 60:
        confidence_level = "Medium"
        recommendation = "Review recommended range"
    else:
        confidence_level = "Low"
        recommendation = "Manual review required"

    return {
        "confidence_score": round(total_confidence, 2),
        "confidence_level": confidence_level,
        "recommendation": recommendation,
        "factors": {
            "mercer_match": round(mercer_score, 2),
            "data_quality": round(quality_score, 2),
            "sample_size": round(sample_score, 2),
            "consistency": round(consistency_score, 2)
        }
    }
```

### 4.4: Data Consistency Check

```python
def measure_data_consistency(data_sources: Dict) -> float:
    """
    Measure consistency across data sources.

    Uses coefficient of variation on P50 values.
    Lower CV = higher consistency.
    """

    p50_values = [
        data["p50"] for data in data_sources.values()
        if data and not data.get("insufficient_data")
    ]

    if len(p50_values) < 2:
        return 0.5  # Insufficient data for consistency check

    mean_p50 = np.mean(p50_values)
    std_p50 = np.std(p50_values)

    # Coefficient of variation
    cv = std_p50 / mean_p50 if mean_p50 > 0 else 1.0

    # Convert to consistency score (0-1)
    # CV < 0.1 = excellent consistency (1.0)
    # CV > 0.3 = poor consistency (0.0)
    if cv <= 0.1:
        consistency = 1.0
    elif cv >= 0.3:
        consistency = 0.0
    else:
        consistency = 1.0 - ((cv - 0.1) / 0.2)

    return consistency
```

## STEP 5: Output Generation

### 5.1: Primary Output Structure

```python
{
    "job_id": "uuid",
    "timestamp": "2025-01-10T14:30:00Z",
    "input_summary": {
        "job_title": "Senior Software Engineer",
        "location": "Central Business District",
        "internal_grade": "9",
        "employment_type": "Full-time"
    },

    "mercer_mapping": {
        "job_code": "ICT.02.015.M40",
        "job_title": "Software Development Senior Professional",
        "position_class": 58,
        "confidence": 0.89
    },

    "salary_recommendation": {
        "currency": "SGD",
        "period": "annual",
        "recommended_range": {
            "min": 72000,
            "max": 95000,
            "target": 82000
        },
        "full_distribution": {
            "p10": 58000,
            "p25": 72000,
            "p50": 82000,
            "p75": 95000,
            "p90": 110000
        },
        "market_position": "55th percentile"
    },

    "confidence_metrics": {
        "overall_score": 82,
        "confidence_level": "High",
        "recommendation": "Proceed with confidence",
        "factors": {
            "mercer_match": 26.7,
            "data_quality": 25.5,
            "sample_size": 20.0,
            "consistency": 18.5
        }
    },

    "data_sources": {
        "mercer": {
            "weight_applied": 0.38,
            "p50": 84000,
            "sample_size": 127,
            "data_date": "2024-09-01",
            "quality_score": 0.95
        },
        "my_careers_future": {
            "weight_applied": 0.26,
            "p50": 80000,
            "sample_size": 43,
            "data_date": "2025-01-05",
            "quality_score": 0.85
        },
        "glassdoor": {
            "weight_applied": 0.13,
            "p50": 78000,
            "sample_size": 18,
            "data_date": "2025-01-08",
            "quality_score": 0.70
        },
        "internal_hris": {
            "weight_applied": 0.18,
            "p50": 85000,
            "sample_size": 9,
            "data_date": "2025-01-10",
            "quality_score": 0.95
        },
        "applicant_data": {
            "weight_applied": 0.05,
            "p50": 90000,
            "sample_size": 31,
            "data_date": "2025-01-10",
            "quality_score": 0.60
        }
    },

    "explanation": {
        "summary": "Based on analysis of 228 data points across 5 sources, the recommended salary range for Senior Software Engineer (Grade 9) in Central Business District is SGD 72,000 - 95,000 annually. This positions the role at the 55th percentile of market, aligned with company compensation philosophy.",

        "key_factors": [
            "Strong match to Mercer job code ICT.02.015.M40 (89% confidence)",
            "43 similar active listings on My Careers Future",
            "Internal benchmark: 9 employees in similar role",
            "High data consistency across sources (CV: 0.08)"
        ],

        "considerations": [
            "Location: Central Business District commands 10% premium",
            "Grade 9 constraints applied (max SGD 95,000)",
            "Data recency: 85% of data from last 6 months"
        ]
    },

    "alternative_scenarios": [
        {
            "scenario": "Conservative (P10-P25)",
            "range": {"min": 58000, "max": 72000},
            "use_case": "Entry to role, limited experience"
        },
        {
            "scenario": "Competitive (P50-P75)",
            "range": {"min": 82000, "max": 95000},
            "use_case": "Experienced hire, strong credentials"
        },
        {
            "scenario": "Premium (P75-P90)",
            "range": {"min": 95000, "max": 110000},
            "use_case": "Exceptional talent, critical role",
            "note": "Exceeds grade 9 maximum, requires approval"
        }
    ],

    "next_steps": [
        "Review recommended range with hiring manager",
        "Validate against budget allocation",
        "Consider candidate experience and qualifications",
        "Finalize offer within approved range"
    ]
}
```

### 5.2: Visualizations (Data for Frontend)

```python
{
    "charts": {
        "salary_distribution": {
            "type": "box_plot",
            "data": {
                "min": 58000,
                "q1": 72000,
                "median": 82000,
                "q3": 95000,
                "max": 110000
            }
        },

        "source_contribution": {
            "type": "pie_chart",
            "data": {
                "Mercer (40%)": 0.38,
                "My Careers Future (25%)": 0.26,
                "Internal HRIS (15%)": 0.18,
                "Glassdoor (15%)": 0.13,
                "Applicant Data (5%)": 0.05
            }
        },

        "market_comparison": {
            "type": "bar_chart",
            "data": {
                "categories": ["P10", "P25", "P50 (Target)", "P75", "P90"],
                "values": [58000, 72000, 82000, 95000, 110000],
                "recommended_range": [72000, 95000]
            }
        },

        "grade_bands_comparison": {
            "type": "horizontal_bar",
            "data": {
                "Grade 8": {"min": 50000, "max": 75000},
                "Grade 9 (Current)": {"min": 70000, "max": 95000, "highlight": true},
                "Grade 10": {"min": 90000, "max": 120000},
                "Recommended": {"min": 72000, "max": 95000, "color": "blue"}
            }
        }
    }
}
```

## Performance SLAs

- **Algorithm Execution Time**: <5 seconds (P95)
- **Data Freshness**: All scraped data <90 days old
- **Accuracy Target**: ±10% of actual market rates (validated quarterly)
- **Confidence Score Calibration**: >80% of "High" confidence recommendations validated as accurate
- **API Availability**: 99.5% uptime

## Monitoring & Validation

### Real-time Monitoring
- Track execution time per step
- Monitor data source availability
- Alert on confidence scores <60
- Track cache hit rates

### Quarterly Validation
- Compare recommendations against actual hires
- Validate Mercer mapping accuracy
- Audit data source weights effectiveness
- Review and adjust algorithm parameters

### Continuous Improvement
- A/B test algorithm variations
- Collect feedback from HR users
- Retrain ML models quarterly
- Update location indices annually

## Next Steps

1. Implement each algorithm step as Kailash workflow nodes
2. Create comprehensive data models
3. Build API endpoints for algorithm execution
4. Develop frontend visualization components
5. Set up monitoring and alerting infrastructure
6. Conduct user acceptance testing with HR team
7. Deploy to production with gradual rollout
