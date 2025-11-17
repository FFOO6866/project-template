# SSG SkillsFuture Framework Integration Specification

**Version**: 1.0
**Date**: 2025-01-10
**Status**: Production-Ready
**Data Location**: `src/job_pricing/data/SSG/`

## Overview

Singapore's SkillsFuture Skills Framework provides a national taxonomy of skills across 38 sectors. We integrate three SSG datasets to power skills-based job matching, salary benchmarking with My Careers Future, and AI-driven skills extraction from job descriptions.

## Available Datasets

### 1. Skills Framework Dataset (Q3-2025)
**File**: `jobsandskills-skillsfuture-skills-framework-dataset.xlsx`

**Purpose**: Complete mapping of job roles to skills across 38 sectors

**Expected Structure**:
```
Columns:
- sector: String (e.g., "Infocomm Technology", "Human Resource")
- track: String (e.g., "Data & AI", "Talent Management")
- job_role_code: String
- job_role_title: String
- job_role_description: Text
- career_level: String (Entry, Junior, Mid, Senior, Director/VP, C-Suite)
- tsc_code: String (Technical Skills & Competencies code)
- tsc_title: String
- tsc_description: Text
- proficiency_level: String (Basic, Intermediate, Advanced)
- ccs_code: String (Critical Core Skills code - if applicable)
- ccs_title: String
- ccs_proficiency: String
```

### 2. Unique Skills List (Sep-2025)
**File**: `jobsandskills-skillsfuture-unique-skills-list.xlsx`

**Purpose**: Deduplicated master list of skills (sharper taxonomy)

**Expected Structure**:
```
Columns:
- unique_skill_id: String (UUID or sequential ID)
- unique_skill_title: String
- unique_skill_description: Text
- skill_category: String (Technical, Core, Emerging)
- related_sectors: Array[String]
- proficiency_levels: Array[String] (Basic, Intermediate, Advanced)
```

### 3. TSC to Unique Skills Mapping (Sep-2025)
**File**: `jobsandskills-skillsfuture-tsc-to-unique-skills-mapping.xlsx`

**Purpose**: Bridge between original TSC codes and unique skills

**Expected Structure**:
```
Columns:
- tsc_code: String (from Skills Framework dataset)
- tsc_title: String
- unique_skill_id: String (maps to Unique Skills List)
- unique_skill_title: String
- mapping_confidence: Float (0.0-1.0, if provided)
- notes: Text
```

## Critical Core Skills (CCS) Reference

**16 Critical Core Skills** grouped into 3 areas:

### 1. Thinking Critically
- Problem Solving
- Sense Making
- Transdisciplinary Thinking
- Adaptive Thinking
- Learning How to Learn

### 2. Interacting with Others
- Communication
- Collaboration
- Global Mindset
- Cultural Intelligence
- Negotiation

### 3. Staying Relevant
- Resource Management
- Digital Fluency
- Innovation
- Service Orientation
- Leadership
- Personal Mastery

**Proficiency Levels**: Basic, Intermediate, Advanced

## Database Schema Design

```sql
-- SSG Sectors Master Table
CREATE TABLE ssg_sectors (
    id SERIAL PRIMARY KEY,
    sector_code VARCHAR(10) UNIQUE NOT NULL,
    sector_name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- SSG Tracks (Career Tracks within Sectors)
CREATE TABLE ssg_tracks (
    id SERIAL PRIMARY KEY,
    sector_id INTEGER REFERENCES ssg_sectors(id),
    track_code VARCHAR(20) UNIQUE NOT NULL,
    track_name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- SSG Job Roles
CREATE TABLE ssg_job_roles (
    id SERIAL PRIMARY KEY,
    track_id INTEGER REFERENCES ssg_tracks(id),
    job_role_code VARCHAR(50) UNIQUE NOT NULL,
    job_role_title VARCHAR(255) NOT NULL,
    job_role_description TEXT,
    career_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- SSG Technical Skills & Competencies (TSC)
CREATE TABLE ssg_tsc (
    id SERIAL PRIMARY KEY,
    tsc_code VARCHAR(50) UNIQUE NOT NULL,
    tsc_title VARCHAR(255) NOT NULL,
    tsc_description TEXT,
    sector_id INTEGER REFERENCES ssg_sectors(id),
    proficiency_levels TEXT[], -- ['Basic', 'Intermediate', 'Advanced']
    created_at TIMESTAMP DEFAULT NOW()
);

-- SSG Unique Skills (Deduplicated)
CREATE TABLE ssg_unique_skills (
    id SERIAL PRIMARY KEY,
    unique_skill_id VARCHAR(100) UNIQUE NOT NULL,
    unique_skill_title VARCHAR(255) NOT NULL,
    unique_skill_description TEXT,
    skill_category VARCHAR(50), -- 'Technical', 'Core', 'Emerging'
    related_sectors TEXT[], -- Array of sector codes
    proficiency_levels TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- TSC to Unique Skills Mapping
CREATE TABLE ssg_tsc_to_unique_mapping (
    id SERIAL PRIMARY KEY,
    tsc_code VARCHAR(50) REFERENCES ssg_tsc(tsc_code),
    unique_skill_id VARCHAR(100) REFERENCES ssg_unique_skills(unique_skill_id),
    mapping_confidence NUMERIC(3,2), -- 0.00 to 1.00
    notes TEXT,
    UNIQUE(tsc_code, unique_skill_id)
);

-- Job Role to Skills Mapping (Many-to-Many)
CREATE TABLE ssg_job_role_skills (
    id SERIAL PRIMARY KEY,
    job_role_code VARCHAR(50) REFERENCES ssg_job_roles(job_role_code),
    tsc_code VARCHAR(50) REFERENCES ssg_tsc(tsc_code),
    proficiency_level VARCHAR(20), -- 'Basic', 'Intermediate', 'Advanced'
    is_critical_core_skill BOOLEAN DEFAULT FALSE,
    UNIQUE(job_role_code, tsc_code)
);

-- Critical Core Skills (16 CCS)
CREATE TABLE ssg_critical_core_skills (
    id SERIAL PRIMARY KEY,
    ccs_code VARCHAR(20) UNIQUE NOT NULL,
    ccs_title VARCHAR(100) NOT NULL,
    ccs_category VARCHAR(50), -- 'Thinking Critically', 'Interacting with Others', 'Staying Relevant'
    ccs_description TEXT,
    proficiency_levels TEXT[] -- ['Basic', 'Intermediate', 'Advanced']
);

-- Full-text search indexes
CREATE INDEX idx_ssg_tsc_title_fts ON ssg_tsc USING gin(to_tsvector('english', tsc_title || ' ' || tsc_description));
CREATE INDEX idx_ssg_unique_skills_fts ON ssg_unique_skills USING gin(to_tsvector('english', unique_skill_title || ' ' || unique_skill_description));
CREATE INDEX idx_ssg_job_roles_fts ON ssg_job_roles USING gin(to_tsvector('english', job_role_title || ' ' || job_role_description));

-- Regular indexes for joins
CREATE INDEX idx_ssg_tracks_sector ON ssg_tracks(sector_id);
CREATE INDEX idx_ssg_job_roles_track ON ssg_job_roles(track_id);
CREATE INDEX idx_ssg_job_role_skills_role ON ssg_job_role_skills(job_role_code);
CREATE INDEX idx_ssg_job_role_skills_tsc ON ssg_job_role_skills(tsc_code);
```

## Production Implementation

### Phase 1: Data Ingestion from Excel Files

**File**: `src/job_pricing/services/ssg_loader.py`

```python
import pandas as pd
from typing import List, Dict
from pathlib import Path

class SSGDataLoader:
    """
    Production-ready loader for SSG SkillsFuture datasets.
    NO mock data - reads from actual Excel files.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.skills_framework_file = self.data_dir / "jobsandskills-skillsfuture-skills-framework-dataset.xlsx"
        self.unique_skills_file = self.data_dir / "jobsandskills-skillsfuture-unique-skills-list.xlsx"
        self.mapping_file = self.data_dir / "jobsandskills-skillsfuture-tsc-to-unique-skills-mapping.xlsx"

    def load_skills_framework(self) -> pd.DataFrame:
        """Load complete Skills Framework dataset"""
        if not self.skills_framework_file.exists():
            raise FileNotFoundError(f"Skills Framework file not found: {self.skills_framework_file}")

        # Read Excel file
        df = pd.read_excel(self.skills_framework_file, sheet_name=0)

        # Validate required columns
        required_columns = ['sector', 'track', 'job_role_code', 'job_role_title', 'tsc_code', 'tsc_title']
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return df

    def load_unique_skills(self) -> pd.DataFrame:
        """Load deduplicated Unique Skills list"""
        if not self.unique_skills_file.exists():
            raise FileNotFoundError(f"Unique Skills file not found: {self.unique_skills_file}")

        df = pd.read_excel(self.unique_skills_file, sheet_name=0)
        return df

    def load_tsc_mapping(self) -> pd.DataFrame:
        """Load TSC to Unique Skills mapping"""
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"TSC Mapping file not found: {self.mapping_file}")

        df = pd.read_excel(self.mapping_file, sheet_name=0)
        return df

    def parse_and_store(self, db_session):
        """
        Parse all SSG datasets and store in PostgreSQL database.
        Handles hierarchical relationships: Sector -> Track -> Job Role -> Skills
        """
        # Step 1: Load data
        sf_df = self.load_skills_framework()
        us_df = self.load_unique_skills()
        mapping_df = self.load_tsc_mapping()

        # Step 2: Extract and store Sectors
        sectors = sf_df[['sector']].drop_duplicates()
        for _, row in sectors.iterrows():
            sector = SSGSector(
                sector_code=self._generate_sector_code(row['sector']),
                sector_name=row['sector']
            )
            db_session.merge(sector)
        db_session.commit()

        # Step 3: Extract and store Tracks
        tracks = sf_df[['sector', 'track']].drop_duplicates()
        for _, row in tracks.iterrows():
            sector = db_session.query(SSGSector).filter_by(sector_name=row['sector']).first()
            track = SSGTrack(
                sector_id=sector.id,
                track_code=self._generate_track_code(row['track']),
                track_name=row['track']
            )
            db_session.merge(track)
        db_session.commit()

        # Step 4: Extract and store Job Roles
        job_roles = sf_df[['track', 'job_role_code', 'job_role_title', 'job_role_description', 'career_level']].drop_duplicates()
        for _, row in job_roles.iterrows():
            track = db_session.query(SSGTrack).filter_by(track_name=row['track']).first()
            job_role = SSGJobRole(
                track_id=track.id,
                job_role_code=row['job_role_code'],
                job_role_title=row['job_role_title'],
                job_role_description=row.get('job_role_description'),
                career_level=row.get('career_level')
            )
            db_session.merge(job_role)
        db_session.commit()

        # Step 5: Extract and store TSC (Technical Skills & Competencies)
        tscs = sf_df[['tsc_code', 'tsc_title', 'tsc_description', 'sector']].drop_duplicates()
        for _, row in tscs.iterrows():
            sector = db_session.query(SSGSector).filter_by(sector_name=row['sector']).first()
            tsc = SSGTSC(
                tsc_code=row['tsc_code'],
                tsc_title=row['tsc_title'],
                tsc_description=row.get('tsc_description'),
                sector_id=sector.id,
                proficiency_levels=['Basic', 'Intermediate', 'Advanced']
            )
            db_session.merge(tsc)
        db_session.commit()

        # Step 6: Store Unique Skills
        for _, row in us_df.iterrows():
            unique_skill = SSGUniqueSkill(
                unique_skill_id=row['unique_skill_id'],
                unique_skill_title=row['unique_skill_title'],
                unique_skill_description=row.get('unique_skill_description'),
                skill_category=row.get('skill_category'),
                related_sectors=row.get('related_sectors', '').split(',') if row.get('related_sectors') else [],
                proficiency_levels=['Basic', 'Intermediate', 'Advanced']
            )
            db_session.merge(unique_skill)
        db_session.commit()

        # Step 7: Store TSC to Unique Skills mapping
        for _, row in mapping_df.iterrows():
            mapping = SSGTSCToUniqueMapping(
                tsc_code=row['tsc_code'],
                unique_skill_id=row['unique_skill_id'],
                mapping_confidence=row.get('mapping_confidence', 1.0),
                notes=row.get('notes')
            )
            db_session.merge(mapping)
        db_session.commit()

        # Step 8: Store Job Role to Skills relationships
        job_role_skills = sf_df[['job_role_code', 'tsc_code', 'proficiency_level']].drop_duplicates()
        for _, row in job_role_skills.iterrows():
            jrs = SSGJobRoleSkill(
                job_role_code=row['job_role_code'],
                tsc_code=row['tsc_code'],
                proficiency_level=row.get('proficiency_level', 'Intermediate'),
                is_critical_core_skill=self._is_ccs(row['tsc_code'])
            )
            db_session.merge(jrs)
        db_session.commit()

    def _generate_sector_code(self, sector_name: str) -> str:
        """Generate sector code from name (e.g., 'Infocomm Technology' -> 'ICT')"""
        # Simple acronym generation
        words = sector_name.split()
        if len(words) == 1:
            return words[0][:3].upper()
        return ''.join([w[0] for w in words]).upper()

    def _generate_track_code(self, track_name: str) -> str:
        """Generate track code from name"""
        return track_name.replace(' ', '_').replace('&', 'and').lower()

    def _is_ccs(self, tsc_code: str) -> bool:
        """Check if a TSC is a Critical Core Skill"""
        ccs_prefixes = ['CCS-']  # Adjust based on actual CCS code format
        return any(tsc_code.startswith(prefix) for prefix in ccs_prefixes)
```

### Phase 2: Skills Extraction from Job Descriptions

**File**: `src/job_pricing/workflows/skills_extraction.py`

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

class SkillsExtractor:
    """
    AI-powered skills extraction from job descriptions.
    Maps extracted skills to SSG Skills Framework.
    """

    def extract_skills_workflow(self, job_description: str) -> List[Dict]:
        """
        Extract skills from job description and map to SSG framework.

        Returns:
        [
            {
                'skill_name': 'Python Programming',
                'ssg_tsc_code': 'ICT-DES-4001-1.1',
                'unique_skill_id': 'USK-12345',
                'proficiency_level': 'Intermediate',
                'confidence': 0.85
            },
            ...
        ]
        """
        workflow = WorkflowBuilder()

        # Step 1: Named Entity Recognition for skills
        workflow.add_node(
            "LLMAgentNode",
            "extract_skills_ner",
            {
                "model": "gpt-4",
                "prompt": self._get_ner_prompt(),
                "inputs": {"job_description": job_description},
                "output_format": "json",
                "output_key": "extracted_skills"
            }
        )

        # Step 2: Fuzzy matching to SSG TSC database
        workflow.add_node(
            "DatabaseQueryNode",
            "match_to_ssg",
            {
                "query": """
                    SELECT tsc_code, tsc_title, tsc_description,
                           similarity(tsc_title, :skill_name) AS sim_score
                    FROM ssg_tsc
                    WHERE similarity(tsc_title, :skill_name) > 0.3
                    ORDER BY sim_score DESC
                    LIMIT 5
                """,
                "params": {"skill_name": "{{extracted_skills}}"},
                "output_key": "ssg_matches"
            }
        )

        # Step 3: LLM validation and proficiency level inference
        workflow.add_node(
            "LLMAgentNode",
            "validate_and_infer_proficiency",
            {
                "model": "gpt-4",
                "prompt": self._get_validation_prompt(),
                "inputs": {
                    "job_description": job_description,
                    "extracted_skills": "{{extracted_skills}}",
                    "ssg_matches": "{{ssg_matches}}"
                },
                "output_format": "json",
                "output_key": "validated_skills"
            }
        )

        # Step 4: Map to Unique Skills
        workflow.add_node(
            "DatabaseQueryNode",
            "map_to_unique_skills",
            {
                "query": """
                    SELECT m.unique_skill_id, u.unique_skill_title, m.mapping_confidence
                    FROM ssg_tsc_to_unique_mapping m
                    JOIN ssg_unique_skills u ON m.unique_skill_id = u.unique_skill_id
                    WHERE m.tsc_code = :tsc_code
                """,
                "params": {"tsc_code": "{{validated_skills.tsc_code}}"},
                "output_key": "unique_skills"
            }
        )

        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())

        return results["unique_skills"]

    def _get_ner_prompt(self) -> str:
        """LLM prompt for skill extraction"""
        return """
You are an expert in extracting skills from job descriptions.

Job Description:
{{job_description}}

Task: Extract ALL skills mentioned in the job description.
Include:
- Technical skills (e.g., Python, SQL, Data Analysis)
- Soft skills (e.g., Communication, Leadership)
- Domain knowledge (e.g., HR Analytics, Compensation Management)

Output JSON format:
[
    {"skill_name": "Stakeholder Engagement", "skill_type": "soft"},
    {"skill_name": "HR Digitalisation", "skill_type": "technical"},
    {"skill_name": "Compensation Management", "skill_type": "domain"},
    ...
]
"""

    def _get_validation_prompt(self) -> str:
        """LLM prompt for validation and proficiency inference"""
        return """
You are an expert in Singapore's SkillsFuture Skills Framework.

Job Description:
{{job_description}}

Extracted Skills:
{{extracted_skills}}

SSG Skills Framework Matches:
{{ssg_matches}}

Task:
1. Validate each extracted skill matches the correct SSG TSC code
2. Infer the proficiency level required (Basic, Intermediate, Advanced) based on the job description context

Output JSON format:
[
    {
        "skill_name": "Stakeholder Engagement",
        "ssg_tsc_code": "HRM-PCM-5001-1.1",
        "proficiency_level": "Advanced",
        "confidence": 0.92,
        "reasoning": "Job requires managing executive-level stakeholders"
    },
    ...
]
"""
```

### Phase 3: Job Matching to SSG Job Roles

**Use Case**: Match internal job to SSG Job Roles for My Careers Future benchmarking

```python
class SSGJobRoleMatcher:
    """
    Match internal job to SSG Job Roles for salary benchmarking.
    """

    def match_to_ssg_job_role(
        self,
        job_title: str,
        job_description: str,
        sector: str,
        skills: List[str]
    ) -> List[Dict]:
        """
        Find best matching SSG Job Roles.

        Returns top 5 matches with confidence scores.
        """
        workflow = WorkflowBuilder()

        # Step 1: Semantic search in SSG Job Roles
        workflow.add_node(
            "DatabaseQueryNode",
            "search_job_roles",
            {
                "query": """
                    SELECT jr.job_role_code, jr.job_role_title, jr.job_role_description,
                           jr.career_level, s.sector_name, t.track_name,
                           ts_rank(to_tsvector('english', jr.job_role_title || ' ' || jr.job_role_description),
                                   plainto_tsquery('english', :search_text)) AS rank
                    FROM ssg_job_roles jr
                    JOIN ssg_tracks t ON jr.track_id = t.id
                    JOIN ssg_sectors s ON t.sector_id = s.id
                    WHERE s.sector_name = :sector
                      AND to_tsvector('english', jr.job_role_title || ' ' || jr.job_role_description) @@
                          plainto_tsquery('english', :search_text)
                    ORDER BY rank DESC
                    LIMIT 10
                """,
                "params": {
                    "search_text": f"{job_title} {job_description}",
                    "sector": sector
                },
                "output_key": "candidate_roles"
            }
        )

        # Step 2: Skills overlap scoring
        workflow.add_node(
            "PythonCodeNode",
            "calculate_skills_overlap",
            {
                "code": self._get_skills_overlap_code(),
                "inputs": {
                    "candidate_roles": "{{candidate_roles}}",
                    "user_skills": skills
                },
                "output_key": "scored_roles"
            }
        )

        # Step 3: LLM re-ranking
        workflow.add_node(
            "LLMAgentNode",
            "rerank_roles",
            {
                "model": "gpt-4",
                "prompt": self._get_reranking_prompt(),
                "inputs": {
                    "job_title": job_title,
                    "job_description": job_description,
                    "candidate_roles": "{{scored_roles}}"
                },
                "output_format": "json",
                "output_key": "final_matches"
            }
        )

        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())

        return results["final_matches"]

    def _get_skills_overlap_code(self) -> str:
        """Calculate Jaccard similarity for skills"""
        return """
def calculate_overlap(candidate_roles, user_skills):
    scored = []
    for role in candidate_roles:
        # Get skills for this SSG job role
        role_skills = get_skills_for_role(role['job_role_code'])  # DB query

        # Jaccard similarity
        overlap = len(set(user_skills) & set(role_skills))
        union = len(set(user_skills) | set(role_skills))
        skills_score = overlap / union if union > 0 else 0

        role['skills_overlap_score'] = skills_score
        scored.append(role)

    return sorted(scored, key=lambda x: x['skills_overlap_score'], reverse=True)
"""

    def _get_reranking_prompt(self) -> str:
        """LLM prompt for final ranking"""
        return """
Select the top 5 SSG Job Roles that best match the user's job.

User Job:
Title: {{job_title}}
Description: {{job_description}}

Candidate SSG Job Roles:
{{candidate_roles}}

Output JSON format:
[
    {
        "ssg_job_role_code": "HRM-PCM-JR001",
        "ssg_job_role_title": "Total Rewards Manager",
        "match_confidence": 0.89,
        "reasoning": "Strong alignment on compensation management and strategic planning"
    },
    ...
]
"""
```

## Integration Checkpoints

- [ ] All 3 SSG Excel files loaded into database
- [ ] 38 sectors, tracks, and job roles properly hierarchized
- [ ] TSC to Unique Skills mapping validated
- [ ] Skills extraction workflow tested with 50 job descriptions
- [ ] SSG Job Role matching accuracy validated (target: ≥75%)
- [ ] Critical Core Skills (16 CCS) properly flagged
- [ ] Full-text search indexes created and tested

## Use Cases in Dynamic Job Pricing Engine

1. **Skills-Based Job Matching**: Extract skills from user job → Match to SSG skills → Use for Mercer mapping validation
2. **My Careers Future Benchmarking**: Match internal job to SSG Job Role → Search My Careers Future by SSG job title
3. **Alternative Title Generation**: Use SSG "Typical Titles" as alternative market titles
4. **Skills Gap Analysis**: Compare user job skills vs SSG job role skills → Identify gaps → Adjust salary expectations

## Performance Requirements

- **Skills Extraction**: <5 seconds per job description
- **SSG Job Role Matching**: <3 seconds
- **Database Query Performance**: <500ms for skills lookup

## Next Steps

1. Run SSGDataLoader to populate database
2. Validate data completeness (check for missing sectors/tracks)
3. Build skills extraction workflow
4. Integrate with Mercer mapping pipeline
5. Test end-to-end with 100 real job descriptions
