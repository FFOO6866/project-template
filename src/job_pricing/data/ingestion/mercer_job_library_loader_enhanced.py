"""
Enhanced Mercer Job Library Loader with OpenAI Embeddings

Production-ready loader that:
1. Loads all Mercer jobs from Excel (18,000+ jobs)
2. Generates OpenAI embeddings for vector similarity search
3. Batch processes for efficiency
4. Handles errors gracefully
5. NO MOCK DATA - real production implementation

Based on spec: docs/integration/mercer_ipe_integration.md
"""
import logging
import pandas as pd
import re
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import time

from sqlalchemy.orm import Session
from openai import OpenAI

from src.job_pricing.models.mercer import MercerJobLibrary
from src.job_pricing.core.database import get_session
from src.job_pricing.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MercerJobLibraryLoaderEnhanced:
    """
    Production-ready Mercer Job Library loader with OpenAI embeddings.

    Features:
    - Loads from actual Excel file (no mock data)
    - Generates embeddings using OpenAI text-embedding-3-small
    - Batch processing (100 jobs at a time)
    - Comprehensive error handling
    - Progress tracking
    - Duplicate detection
    """

    EXCEL_FILE_PATH = "data/Mercer/Mercer Job Library.xlsx"
    SHEET_NAME = "Mercer Combined Jobs and Jobs"
    HEADER_ROW = 10
    BATCH_SIZE = 100  # Process 100 jobs at a time
    EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, $0.020 / 1M tokens
    EMBEDDING_BATCH_SIZE = 20  # OpenAI recommends batching embeddings

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize loader.

        Args:
            openai_api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env")

        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.stats = {
            "total_jobs": 0,
            "loaded": 0,
            "skipped_duplicates": 0,
            "errors": 0,
            "embeddings_generated": 0,
            "start_time": None,
            "end_time": None,
        }

    def extract_career_level_code(self, level_title: str) -> Optional[str]:
        """
        Extract career level code from title.

        Examples:
            'Executive Tier 3 (ET3)' -> 'ET3'
            'Manager 5 (M5)' -> 'M5'
            'Professional 3 (P3)' -> 'P3'

        Args:
            level_title: Full career level title

        Returns:
            Extracted code or None
        """
        if pd.isna(level_title):
            return None

        # Try to extract code from parentheses
        match = re.search(r'\(([^)]+)\)', level_title)
        if match:
            return match.group(1)

        # If no parentheses, return as is
        return level_title.strip()

    def load_excel_data(self) -> pd.DataFrame:
        """
        Load Mercer Job Library from Excel file.

        Returns:
            DataFrame with all Mercer jobs

        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ValueError: If sheet or header not found
        """
        logger.info(f"Loading Mercer jobs from: {self.EXCEL_FILE_PATH}")

        try:
            df = pd.read_excel(
                self.EXCEL_FILE_PATH,
                sheet_name=self.SHEET_NAME,
                header=self.HEADER_ROW
            )

            logger.info(f"✅ Loaded {len(df)} jobs from Excel")
            logger.info(f"Columns: {df.columns.tolist()}")

            self.stats["total_jobs"] = len(df)
            return df

        except FileNotFoundError:
            logger.error(f"❌ Excel file not found: {self.EXCEL_FILE_PATH}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading Excel: {e}")
            raise

    def create_embedding_text(self, row: pd.Series) -> str:
        """
        Create rich text representation for embedding generation.

        Combines job title, description, family, and subfamily for semantic search.

        Args:
            row: DataFrame row with job data

        Returns:
            Combined text for embedding
        """
        parts = []

        # Job title (most important)
        if pd.notna(row.get('Job Title')):
            parts.append(f"Title: {row['Job Title']}")

        # Job description
        if pd.notna(row.get('Job Description')):
            desc = str(row['Job Description'])[:500]  # Truncate to 500 chars
            parts.append(f"Description: {desc}")

        # Family and subfamily context
        if pd.notna(row.get('Family Title')):
            parts.append(f"Family: {row['Family Title']}")

        if pd.notna(row.get('Sub-family Title')):
            parts.append(f"Subfamily: {row['Sub-family Title']}")

        # Career level
        if pd.notna(row.get('Career Level Title')):
            parts.append(f"Level: {row['Career Level Title']}")

        return " | ".join(parts)

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts using OpenAI.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each 1536 dimensions)
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            self.stats["embeddings_generated"] += len(embeddings)

            return embeddings

        except Exception as e:
            logger.error(f"❌ OpenAI embeddings error: {e}")
            raise

    def parse_job_row(self, row: pd.Series) -> Dict:
        """
        Parse a DataFrame row into job data dictionary.

        Args:
            row: DataFrame row

        Returns:
            Dictionary with parsed job data
        """
        return {
            "job_code": row['Job Code'] if pd.notna(row.get('Job Code')) else None,
            "job_title": row['Job Title'] if pd.notna(row.get('Job Title')) else None,
            "job_description": row['Job Description'] if pd.notna(row.get('Job Description')) else None,
            "family": row['Family Code'] if pd.notna(row.get('Family Code')) else None,
            "subfamily": str(int(row['Sub-family Code'])) if pd.notna(row.get('Sub-family Code')) else None,
            "career_level": self.extract_career_level_code(row.get('Career Level Title')),
            "family_title": row['Family Title'] if pd.notna(row.get('Family Title')) else None,
            "subfamily_title": row['Sub-family Title'] if pd.notna(row.get('Sub-family Title')) else None,
            "specialization_code": row['Specialization Code'] if pd.notna(row.get('Specialization Code')) else None,
            "specialization_title": row['Specialization Title'] if pd.notna(row.get('Specialization Title')) else None,
            "career_stream": row['Career Stream Title'] if pd.notna(row.get('Career Stream Title')) else None,
        }

    def job_exists(self, session: Session, job_code: str) -> bool:
        """
        Check if job already exists in database.

        Args:
            session: Database session
            job_code: Mercer job code

        Returns:
            True if job exists, False otherwise
        """
        existing = session.query(MercerJobLibrary).filter_by(job_code=job_code).first()
        return existing is not None

    def load_jobs(self, skip_existing: bool = True) -> Dict:
        """
        Load all Mercer jobs with embeddings into database.

        Main entry point for loading process.

        Args:
            skip_existing: If True, skip jobs that already exist in database

        Returns:
            Dictionary with loading statistics
        """
        self.stats["start_time"] = datetime.now()
        logger.info("=" * 80)
        logger.info("MERCER JOB LIBRARY LOADER - ENHANCED WITH OPENAI EMBEDDINGS")
        logger.info("=" * 80)

        # Load Excel data
        df = self.load_excel_data()

        # Process in batches
        total_batches = (len(df) + self.BATCH_SIZE - 1) // self.BATCH_SIZE
        logger.info(f"Processing {len(df)} jobs in {total_batches} batches of {self.BATCH_SIZE}")

        session = next(get_session())

        try:
            for batch_idx in range(0, len(df), self.BATCH_SIZE):
                batch_df = df.iloc[batch_idx:batch_idx + self.BATCH_SIZE]
                batch_num = (batch_idx // self.BATCH_SIZE) + 1

                logger.info(f"\n--- Batch {batch_num}/{total_batches} ---")

                # Prepare batch data
                jobs_to_insert = []
                embedding_texts = []

                for idx, row in batch_df.iterrows():
                    try:
                        job_code = row.get('Job Code')
                        if not job_code or pd.isna(job_code):
                            logger.warning(f"Skipping row {idx}: no job code")
                            self.stats["errors"] += 1
                            continue

                        # Check if exists
                        if skip_existing and self.job_exists(session, job_code):
                            self.stats["skipped_duplicates"] += 1
                            continue

                        # Parse job data
                        job_data = self.parse_job_row(row)

                        # Create embedding text
                        embedding_text = self.create_embedding_text(row)

                        jobs_to_insert.append(job_data)
                        embedding_texts.append(embedding_text)

                    except Exception as e:
                        logger.error(f"Error parsing row {idx}: {e}")
                        self.stats["errors"] += 1
                        continue

                # Generate embeddings for batch (in sub-batches if needed)
                if jobs_to_insert:
                    all_embeddings = []

                    for emb_batch_idx in range(0, len(embedding_texts), self.EMBEDDING_BATCH_SIZE):
                        emb_batch = embedding_texts[emb_batch_idx:emb_batch_idx + self.EMBEDDING_BATCH_SIZE]
                        embeddings = self.generate_embeddings_batch(emb_batch)
                        all_embeddings.extend(embeddings)

                        # Rate limiting - OpenAI has 3,000 RPM limit for embeddings
                        if emb_batch_idx + self.EMBEDDING_BATCH_SIZE < len(embedding_texts):
                            time.sleep(0.1)  # Small delay between embedding batches

                    # Insert jobs with embeddings
                    for job_data, embedding in zip(jobs_to_insert, all_embeddings):
                        try:
                            job = MercerJobLibrary(
                                **job_data,
                                embedding=embedding  # pgvector column
                            )
                            session.add(job)
                            self.stats["loaded"] += 1

                        except Exception as e:
                            logger.error(f"Error inserting job {job_data.get('job_code')}: {e}")
                            self.stats["errors"] += 1
                            session.rollback()
                            continue

                    # Commit batch
                    try:
                        session.commit()
                        logger.info(f"✅ Batch {batch_num}: inserted {len(jobs_to_insert)} jobs")
                    except Exception as e:
                        logger.error(f"❌ Error committing batch {batch_num}: {e}")
                        session.rollback()
                        self.stats["errors"] += len(jobs_to_insert)

                # Progress update
                progress_pct = (batch_idx + self.BATCH_SIZE) / len(df) * 100
                logger.info(f"Progress: {progress_pct:.1f}% | Loaded: {self.stats['loaded']} | Errors: {self.stats['errors']}")

        finally:
            session.close()

        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total jobs in Excel:    {self.stats['total_jobs']}")
        logger.info(f"Successfully loaded:    {self.stats['loaded']}")
        logger.info(f"Skipped (duplicates):   {self.stats['skipped_duplicates']}")
        logger.info(f"Errors:                 {self.stats['errors']}")
        logger.info(f"Embeddings generated:   {self.stats['embeddings_generated']}")
        logger.info(f"Duration:               {duration:.1f} seconds")
        logger.info(f"Rate:                   {self.stats['loaded'] / duration:.1f} jobs/second")
        logger.info("=" * 80)

        return self.stats


def main():
    """Main entry point for running loader standalone."""
    loader = MercerJobLibraryLoaderEnhanced()
    stats = loader.load_jobs(skip_existing=True)

    if stats["errors"] > 0:
        logger.warning(f"⚠️  Completed with {stats['errors']} errors")
    else:
        logger.info("✅ All jobs loaded successfully!")


if __name__ == "__main__":
    main()
