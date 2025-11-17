"""Simple script to generate embeddings for Mercer jobs."""
import openai
import os
from src.job_pricing.models.mercer import MercerJobLibrary
from src.job_pricing.utils.database import get_db_context
import time

def generate_embeddings():
    """Generate OpenAI embeddings for all Mercer jobs without embeddings."""
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if not openai.api_key:
        print("ERROR: OPENAI_API_KEY not set in environment")
        return

    print("Generating OpenAI embeddings for Mercer jobs...")
    print(f"Model: text-embedding-3-large (1536 dimensions)")
    print(f"Cost: ~$0.13 per 1M tokens")

    with get_db_context() as session:
        # Get jobs without embeddings
        jobs = session.query(MercerJobLibrary).filter(
            MercerJobLibrary.embedding.is_(None)
        ).all()

        print(f"\nFound {len(jobs)} jobs without embeddings")

        if len(jobs) == 0:
            print("All jobs already have embeddings!")
            return

        # Estimate cost
        avg_tokens_per_job = 500  # Conservative estimate
        total_tokens = len(jobs) * avg_tokens_per_job
        estimated_cost = total_tokens / 1_000_000 * 0.13
        print(f"Estimated cost: ${estimated_cost:.2f}")
        print(f"Estimated time: ~{len(jobs) / 50:.1f} minutes (50 jobs/min with rate limit)")
        print()

        # Process jobs one by one
        successful = 0
        errors = 0

        for idx, job in enumerate(jobs, 1):
            try:
                # Prepare text for embedding
                text = f"{job.job_title}. {job.job_description or ''}. Family: {job.family or ''}. Level: {job.career_level or ''}."

                # Call OpenAI API
                response = openai.embeddings.create(
                    model="text-embedding-3-large",
                    input=text,
                    dimensions=1536
                )

                # Update job with embedding
                job.embedding = response.data[0].embedding
                session.commit()

                successful += 1

                # Progress message every 25 jobs
                if idx % 25 == 0:
                    print(f"Generated {idx}/{len(jobs)} embeddings...")

                # Rate limiting: ~50 embeddings per minute
                time.sleep(1.2)  # 60 seconds / 50 = 1.2 seconds per request

            except Exception as e:
                session.rollback()
                errors += 1
                print(f"Error generating embedding for job {job.job_code}: {e}")
                continue

        print(f"\nComplete! Generated {successful} embeddings with {errors} errors")
        return successful, errors

if __name__ == '__main__':
    generate_embeddings()
