"""
Production-Ready Mercer Job Library Loader
Loads all jobs from Excel with embeddings and comprehensive error handling.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import os
import pandas as pd
import logging
from datetime import datetime
from typing import Optional
import openai

from job_pricing.core.database import get_session
from job_pricing.models import MercerJobLibrary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EXCEL_PATH = Path(__file__).parent.parent / 'Mercer' / 'Mercer Job Library.xlsx'
SHEET_NAME = "Mercer Combined Jobs and Jobs"
HEADER_ROW = 10
EMBEDDING_MODEL = "text-embedding-3-large"  # Match what job_matching_service uses
EMBEDDING_DIM = 1536
BATCH_SIZE = 20  # Process embeddings in batches

def generate_embedding(text: str, api_key: str) -> Optional[list]:
    """Generate OpenAI embedding for text."""
    try:
        response = openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIM
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None

def load_mercer_jobs():
    """Load all Mercer jobs from Excel with embeddings."""

    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not set!")
        return 0

    openai.api_key = api_key

    session = get_session()

    try:
        # Read Excel
        logger.info(f"Reading Excel: {EXCEL_PATH}")
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, header=HEADER_ROW)
        logger.info(f"Loaded {len(df)} rows from Excel")
        logger.info(f"Columns: {list(df.columns[:10])}")

        # Clean data - use actual column name from Excel
        df = df.dropna(subset=['Job Code'])  # Must have job code
        logger.info(f"After filtering: {len(df)} valid rows")

        # Track stats
        stats = {
            'total': len(df),
            'loaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'embeddings_generated': 0
        }

        # Process each job
        for idx, row in df.iterrows():
            try:
                job_code = str(row['Job Code']).strip()

                # Check if exists
                existing = session.query(MercerJobLibrary).filter(
                    MercerJobLibrary.job_code == job_code
                ).first()

                # Extract data - use actual column names from Excel
                job_title = str(row.get('Job Title', '')).strip() if pd.notna(row.get('Job Title')) else None
                family = str(row.get('Family Title', '')).strip() if pd.notna(row.get('Family Title')) else None
                subfamily = str(row.get('Sub-family Title', '')).strip() if pd.notna(row.get('Sub-family Title')) else None
                career_level = str(row.get('Career Level Code', '')).strip() if pd.notna(row.get('Career Level Code')) else None
                job_description = str(row.get('Job Description', '')).strip() if pd.notna(row.get('Job Description')) else None

                # Validate minimum required fields
                if not job_title:
                    logger.warning(f"Skipping {job_code} - no job title")
                    stats['skipped'] += 1
                    continue

                # Generate embedding text
                embedding_text = f"{job_title}. {job_description}" if job_description else job_title

                # Generate embedding
                embedding = None
                if not existing or existing.embedding is None:
                    embedding = generate_embedding(embedding_text, api_key)
                    if embedding:
                        stats['embeddings_generated'] += 1

                if existing:
                    # Update existing
                    existing.job_title = job_title or existing.job_title
                    existing.family = family or existing.family
                    existing.subfamily = subfamily or existing.subfamily
                    existing.career_level = career_level or existing.career_level
                    existing.job_description = job_description or existing.job_description
                    if embedding:
                        existing.embedding = embedding
                    stats['updated'] += 1
                else:
                    # Create new
                    job = MercerJobLibrary(
                        job_code=job_code,
                        job_title=job_title,
                        family=family,
                        subfamily=subfamily,
                        career_level=career_level,
                        job_description=job_description,
                        embedding=embedding
                    )
                    session.add(job)
                    stats['loaded'] += 1

                # Commit every 50 records
                if (stats['loaded'] + stats['updated']) % 50 == 0:
                    session.flush()
                    logger.info(f"Progress: {stats['loaded']} new, {stats['updated']} updated, {stats['embeddings_generated']} embeddings")

            except Exception as e:
                logger.error(f"Error processing row {idx} ({job_code}): {e}")
                stats['errors'] += 1
                continue

        # Final commit
        session.commit()

        # Final stats
        total_in_db = session.query(MercerJobLibrary).count()

        logger.info("")
        logger.info("=" * 80)
        logger.info("MERCER JOB LIBRARY LOAD COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total in Excel: {stats['total']}")
        logger.info(f"New jobs loaded: {stats['loaded']}")
        logger.info(f"Existing updated: {stats['updated']}")
        logger.info(f"Skipped: {stats['skipped']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Embeddings generated: {stats['embeddings_generated']}")
        logger.info(f"Total in database: {total_in_db}")
        logger.info("=" * 80)

        return stats['loaded'] + stats['updated']

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        session.rollback()
        return 0
    finally:
        session.close()

if __name__ == '__main__':
    load_mercer_jobs()
