# Mercer IPE Integration Specification

**Version**: 1.0
**Date**: 2025-01-10
**Status**: Production-Ready

## Overview

The Mercer International Position Evaluation (IPE) System is a point-based job evaluation framework that assigns standardized position classes to jobs based on 5 key factors. This document specifies the production implementation for integrating Mercer IPE data and methodologies into the Dynamic Job Pricing Engine.

## Mercer IPE System Components

### 1. Five Core Factors

| Factor | Description | Modifiers | Point Range |
|--------|-------------|-----------|-------------|
| **Impact** | Nature and scope of influence on organization | Organization Size, Contribution | 5-705 |
| **Communication** | Communication skills required | Frame (context) | 10-115 |
| **Innovation** | Level of innovation expected | Complexity | 10-130 |
| **Knowledge** | Depth and breadth of knowledge | Teams, Breadth (geography) | 15-260 |
| **Risk** | Mental/physical risk exposure | Environment | 0-35 (optional) |

### 2. Position Class System

- **Total Points Range**: 26 - 1225+
- **Position Classes**: 40 - 87
- **Conversion**: 25-point bands (e.g., 26-50 = Class 40, 51-75 = Class 41)

### 3. Organization Size Calculation

**Formula**: `Adjusted Size = Net Revenue × Value Chain Multiplier`

**Value Chain Multipliers** (Products Organizations):
- Basic R&D: 4.0
- Applied R&D: 2.0
- Engineering: 1.5
- Procurement/Inbound Logistics: 2.0
- Production: 2.0
- Application/Assembly: 2.5
- Marketing: 1.0
- Sales: 1.5
- Distribution: 1.5
- Service: 2.0

**Value Chain Multipliers** (Services Organizations):
- Idea & Concept Origination: 3.0
- Generate Application: 2.0
- Apply Solutions: 2.5
- Marketing: 1.5
- Sales: 3.0
- Distribution: 1.5
- Service: 1.5

## Data Requirements

### Mercer Job Library Structure

```
mercer_job_library/
├── job_code: String (e.g., "HRM.04.005.M50")
├── job_title: String
├── job_family: String (e.g., "Human Resources")
├── job_subfamily: String (e.g., "Total Rewards")
├── career_level: String (e.g., "M5" - Director)
├── position_class: Integer (40-87)
├── job_description: Text
├── typical_titles: Array[String]
├── specialization_notes: Text
└── ipe_factors:
    ├── impact_range: Object {min, max}
    ├── communication_range: Object {min, max}
    ├── innovation_range: Object {min, max}
    ├── knowledge_range: Object {min, max}
    └── risk_range: Object {min, max}
```

### Mercer Market Data Structure

```
mercer_market_data/
├── job_code: String
├── country_code: String (ISO 3166-1 alpha-2)
├── location: String
├── currency: String (ISO 4217)
├── industry: String
├── sample_size: Integer
├── data_date: Date
├── benchmarks:
    ├── by_job:
    │   ├── p10, p25, p50, p75, p90: Decimal
    │   └── sample_size: Integer
    ├── by_family_career_level:
    │   └── [same structure]
    ├── by_family_position_class:
    │   └── [same structure]
    ├── by_subfamily_career_level:
    │   └── [same structure]
    └── by_subfamily_position_class:
        └── [same structure]
└── metadata:
    ├── survey_date: Date
    ├── participant_count: Integer
    └── notes: Text
```

## Production Implementation

### Phase 1: Data Ingestion & Storage

**File**: `src/job_pricing/services/mercer_integration.py`

```python
class MercerJobLibraryLoader:
    """
    Production-ready loader for Mercer Job Library data.
    NO mock data, reads from actual Excel files.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.jobs = []

    def load_from_excel(self) -> List[MercerJob]:
        """Load Mercer Job Library from Excel file"""
        # Implementation using pandas or openpyxl
        # Read from: data/Mercer/Mercer Job Library.xlsx
        pass

    def parse_job_code(self, job_code: str) -> Dict:
        """Parse Mercer job code into components"""
        # Format: FAMILY.SUBFAMILY.SEQUENCENUMBER.LEVEL
        # Example: HRM.04.005.M50
        parts = job_code.split('.')
        return {
            'family_code': parts[0],
            'subfamily_code': parts[1],
            'sequence': parts[2],
            'level': parts[3]
        }

    def store_in_database(self, jobs: List[MercerJob]):
        """Store jobs in PostgreSQL database"""
        # Implementation with SQLAlchemy
        pass
```

**Database Schema**:

```sql
CREATE TABLE mercer_job_library (
    id SERIAL PRIMARY KEY,
    job_code VARCHAR(50) UNIQUE NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    family VARCHAR(100) NOT NULL,
    subfamily VARCHAR(100),
    career_level VARCHAR(10),
    position_class INTEGER,
    job_description TEXT,
    typical_titles TEXT[],
    specialization_notes TEXT,
    impact_min INTEGER,
    impact_max INTEGER,
    communication_min INTEGER,
    communication_max INTEGER,
    innovation_min INTEGER,
    innovation_max INTEGER,
    knowledge_min INTEGER,
    knowledge_max INTEGER,
    risk_min INTEGER,
    risk_max INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mercer_job_family ON mercer_job_library(family);
CREATE INDEX idx_mercer_job_subfamily ON mercer_job_library(subfamily);
CREATE INDEX idx_mercer_job_level ON mercer_job_library(career_level);
CREATE INDEX idx_mercer_position_class ON mercer_job_library(position_class);

-- Full-text search index for job matching
CREATE INDEX idx_mercer_job_description_fts ON mercer_job_library
USING gin(to_tsvector('english', job_description));
```

### Phase 2: AI-Powered Job Mapping

**Workflow**: User Job → Mercer Job Library Match

**File**: `src/job_pricing/workflows/mercer_mapping.py`

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

class MercerJobMapper:
    """
    AI-powered job mapping to Mercer Job Library.
    Uses semantic similarity + rule-based validation.
    """

    def build_mapping_workflow(
        self,
        job_title: str,
        job_description: str,
        job_family: str,
        internal_grade: str,
        skills: List[str]
    ) -> str:
        """
        Build Kailash workflow for Mercer job mapping.
        Returns: Mercer job code with confidence score.
        """
        workflow = WorkflowBuilder()

        # Step 1: Generate embeddings for user job description
        workflow.add_node(
            "LLMAgentNode",
            "generate_embedding",
            {
                "model": "text-embedding-3-large",
                "input_text": f"{job_title}\n\n{job_description}",
                "output_key": "user_job_embedding"
            }
        )

        # Step 2: Vector similarity search against Mercer library
        workflow.add_node(
            "DatabaseQueryNode",
            "vector_search",
            {
                "query": """
                    SELECT job_code, job_title, job_description, family, subfamily,
                           career_level, position_class,
                           (embedding <=> :user_embedding) AS similarity_score
                    FROM mercer_job_library
                    WHERE family = :job_family
                    ORDER BY similarity_score ASC
                    LIMIT 10
                """,
                "params": {
                    "user_embedding": "{{user_job_embedding}}",
                    "job_family": job_family
                },
                "output_key": "candidate_jobs"
            }
        )

        # Step 3: Rule-based validation
        workflow.add_node(
            "PythonCodeNode",
            "validate_candidates",
            {
                "code": self._get_validation_code(),
                "inputs": {
                    "candidates": "{{candidate_jobs}}",
                    "user_job_family": job_family,
                    "user_internal_grade": internal_grade,
                    "user_skills": skills
                },
                "output_key": "validated_candidates"
            }
        )

        # Step 4: LLM re-ranking and explanation
        workflow.add_node(
            "LLMAgentNode",
            "rerank_and_explain",
            {
                "model": "gpt-4",
                "prompt": self._get_reranking_prompt(),
                "inputs": {
                    "user_job_title": job_title,
                    "user_job_description": job_description,
                    "candidates": "{{validated_candidates}}"
                },
                "output_format": "json",
                "output_key": "final_match"
            }
        )

        # Step 5: Confidence scoring
        workflow.add_node(
            "PythonCodeNode",
            "calculate_confidence",
            {
                "code": self._get_confidence_scoring_code(),
                "inputs": {
                    "match_result": "{{final_match}}",
                    "semantic_score": "{{user_job_embedding}}",
                    "validation_result": "{{validated_candidates}}"
                },
                "output_key": "confidence_score"
            }
        )

        # Execute workflow
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())

        return results["final_match"], results["confidence_score"]

    def _get_validation_code(self) -> str:
        """Python code for rule-based validation"""
        return """
def validate(candidates, user_job_family, user_internal_grade, user_skills):
    validated = []
    for candidate in candidates:
        score = 0.0

        # Family match (mandatory)
        if candidate['family'] == user_job_family:
            score += 0.2
        else:
            continue  # Skip if family doesn't match

        # Career level alignment (map internal grade to Mercer level)
        grade_to_level_map = {
            '8': ['M3', 'M4'], '9': ['M4', 'M5'], '10': ['M5', 'M6'],
            '11': ['M6', 'M7'], '12': ['M7', 'M8']
        }
        expected_levels = grade_to_level_map.get(user_internal_grade, [])
        if candidate['career_level'] in expected_levels:
            score += 0.1

        # Skills overlap (Jaccard similarity)
        candidate_skills = extract_skills_from_description(candidate['job_description'])
        overlap = len(set(user_skills) & set(candidate_skills))
        total = len(set(user_skills) | set(candidate_skills))
        if total > 0:
            score += (overlap / total) * 0.2

        candidate['validation_score'] = score
        if score >= 0.2:  # Minimum threshold
            validated.append(candidate)

    return sorted(validated, key=lambda x: x['validation_score'], reverse=True)
"""

    def _get_reranking_prompt(self) -> str:
        """LLM prompt for re-ranking candidates"""
        return """
You are an expert in job evaluation and the Mercer IPE system.

User Job:
Title: {{user_job_title}}
Description: {{user_job_description}}

Candidate Mercer Jobs:
{{candidates}}

Task: Select the BEST matching Mercer job and explain why.

Output JSON format:
{
    "selected_job_code": "HRM.04.005.M50",
    "match_confidence": 0.92,
    "explanation": "This role aligns with Mercer's Total Rewards - Director (M5) because...",
    "key_similarities": ["Designs total rewards philosophy", "Strategic level", "M5 career level matches grade 10"],
    "key_differences": ["User role has more focus on technology integration"]
}
"""

    def _get_confidence_scoring_code(self) -> str:
        """Multi-factor confidence scoring"""
        return """
def calculate_confidence(match_result, semantic_score, validation_result):
    # Weighted confidence calculation
    semantic_weight = 0.4
    validation_weight = 0.2
    family_match_weight = 0.2
    llm_confidence_weight = 0.2

    confidence = (
        semantic_score * semantic_weight +
        validation_result['validation_score'] * validation_weight +
        (1.0 if validation_result['family_match'] else 0.0) * family_match_weight +
        match_result['match_confidence'] * llm_confidence_weight
    )

    # Classify confidence level
    if confidence >= 0.80:
        level = "High"
    elif confidence >= 0.60:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": confidence,
        "level": level,
        "requires_manual_review": confidence < 0.60
    }
"""
```

### Phase 3: Mercer Market Data Integration

**API Integration** (if Mercer provides API):

```python
class MercerAPIClient:
    """
    Production client for Mercer compensation survey API.
    """

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def get_market_data(
        self,
        job_code: str,
        country: str,
        industry: str = None
    ) -> Dict:
        """
        Fetch market compensation data for a Mercer job.

        Returns benchmark data across multiple cuts:
        - By Job
        - By Job Family + Career Level
        - By Job Family + Position Class
        - By Sub Family + Career Level
        - By Sub Family + Position Class
        """
        endpoint = f"{self.base_url}/v1/market-data"
        params = {
            'job_code': job_code,
            'country': country,
            'industry': industry,
            'benchmark_cuts': 'all',
            'percentiles': 'p10,p25,p50,p75,p90'
        }

        response = self.session.get(endpoint, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    def cache_market_data(self, data: Dict):
        """Cache Mercer data in Redis for 24 hours"""
        cache_key = f"mercer_market:{data['job_code']}:{data['country']}"
        redis_client.setex(cache_key, 86400, json.dumps(data))
```

**Database Schema for Market Data**:

```sql
CREATE TABLE mercer_market_data (
    id SERIAL PRIMARY KEY,
    job_code VARCHAR(50) NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    location VARCHAR(100),
    currency VARCHAR(3),
    industry VARCHAR(100),
    benchmark_cut VARCHAR(50), -- 'by_job', 'by_family_level', etc.
    p10 NUMERIC(12, 2),
    p25 NUMERIC(12, 2),
    p50 NUMERIC(12, 2),
    p75 NUMERIC(12, 2),
    p90 NUMERIC(12, 2),
    sample_size INTEGER,
    survey_date DATE,
    data_retrieved_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_code, country_code, benchmark_cut, survey_date)
);

CREATE INDEX idx_mercer_market_job ON mercer_market_data(job_code);
CREATE INDEX idx_mercer_market_country ON mercer_market_data(country_code);
CREATE INDEX idx_mercer_market_date ON mercer_market_data(survey_date DESC);
```

## Integration Checkpoints

- [ ] Mercer Job Library Excel file loaded into database
- [ ] Embeddings generated for all 18,000+ Mercer jobs
- [ ] Vector search index created (pgvector)
- [ ] AI mapping workflow tested with 100 sample jobs
- [ ] Mapping accuracy validated (target: ≥85%)
- [ ] Mercer API credentials obtained and tested
- [ ] Market data caching layer implemented
- [ ] Confidence scoring calibrated
- [ ] Manual review queue created for low-confidence matches

## Performance Requirements

- **Job Mapping Latency**: <3 seconds (P95)
- **Market Data API Calls**: <1 second (P95)
- **Cache Hit Rate**: >80% for frequently accessed jobs
- **Mapping Accuracy**: ≥85% (validated against human expert evaluations)

## Error Handling

1. **No Good Match Found** (confidence <60%):
   - Add to manual review queue
   - Notify compensation analyst
   - Provide top 3 candidates for review

2. **API Rate Limiting**:
   - Implement exponential backoff
   - Use cached data as fallback
   - Queue requests for retry

3. **Data Quality Issues**:
   - Log anomalies (missing fields, outliers)
   - Flag for data validation review
   - Apply data quality scores

## Next Steps

1. Implement MercerJobLibraryLoader
2. Generate embeddings for all Mercer jobs
3. Build AI mapping workflow
4. Integrate with Dynamic Pricing Engine
5. Create manual review UI for low-confidence matches
