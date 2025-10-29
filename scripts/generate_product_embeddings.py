"""
Generate Product Embeddings for Semantic Search
================================================

This script generates OpenAI embeddings for all products in the database
to enable semantic search capabilities in the AI chat.

PRODUCTION SCRIPT - Uses real OpenAI API (requires OPENAI_API_KEY)
NO MOCK DATA - All embeddings are real vectors from OpenAI

Usage:
    python scripts/generate_product_embeddings.py [--limit N] [--force]

Options:
    --limit N       Limit number of products to process (default: all)
    --force         Force regenerate embeddings even if they exist
    --batch-size N  Number of products per batch (default: 100)
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.embedding_service import EmbeddingService
from src.core.config import config


async def main():
    """Generate embeddings for products in the database."""

    parser = argparse.ArgumentParser(description="Generate product embeddings for semantic search")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of products to process")
    parser.add_argument("--force", action="store_true", help="Force regenerate all embeddings")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    args = parser.parse_args()

    print("=" * 80)
    print("Product Embedding Generation")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Database: {config.DATABASE_HOST}:{config.DATABASE_PORT}/{config.DATABASE_NAME}")
    print(f"Force regenerate: {args.force}")
    print(f"Batch size: {args.batch_size}")
    if args.limit:
        print(f"Limit: {args.limit} products")
    print()

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("   Please set it before running this script:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return 1

    try:
        # Connect to database
        print("Connecting to database...")
        db_pool = await asyncpg.create_pool(
            host=config.DATABASE_HOST,
            port=config.DATABASE_PORT,
            user=config.DATABASE_USER,
            password=config.DATABASE_PASSWORD,
            database=config.DATABASE_NAME,
            min_size=2,
            max_size=10
        )
        print("✅ Connected to database\n")

        # Initialize embedding service
        embedding_service = EmbeddingService(db_pool)

        # Get current statistics
        print("Checking current embedding coverage...")
        stats = await embedding_service.get_embedding_statistics()

        print(f"📊 Current Status:")
        print(f"   Total products: {stats['total_products']}")
        print(f"   Products with embeddings: {stats['products_with_embeddings']}")
        print(f"   Products without embeddings: {stats['products_without_embeddings']}")
        print(f"   Coverage: {stats['coverage_percentage']:.1f}%")
        print(f"   Embedding model: {stats['embedding_model']}")
        print(f"   Embedding dimensions: {stats['embedding_dimensions']}")
        print()

        # Generate embeddings
        if stats['products_without_embeddings'] == 0 and not args.force:
            print("✅ All products already have embeddings!")
            print("   Use --force to regenerate embeddings")
            return 0

        print("🔄 Generating embeddings...")
        print("   This may take a few minutes depending on the number of products...")
        print()

        result = await embedding_service.generate_product_embeddings(
            product_ids=None,  # Process all products
            batch_size=args.batch_size,
            force_regenerate=args.force
        )

        # Display results
        print()
        print("=" * 80)
        print("✅ Embedding Generation Complete!")
        print("=" * 80)
        print(f"Products processed: {result['products_processed']}")
        print(f"Embeddings generated: {result['embeddings_generated']}")
        print(f"Status: {result['status']}")
        print(f"Model used: {result['embedding_model']}")
        print(f"Dimensions: {result['embedding_dimensions']}")

        if result.get('errors', 0) > 0:
            print(f"\n⚠️  Errors: {result['errors']}")
            if result.get('error_details'):
                print("Error details:")
                for error in result['error_details']:
                    print(f"  Batch {error['batch']}: {error['error']}")

        # Get updated statistics
        print("\nUpdated coverage:")
        stats = await embedding_service.get_embedding_statistics()
        print(f"   Products with embeddings: {stats['products_with_embeddings']}")
        print(f"   Coverage: {stats['coverage_percentage']:.1f}%")

        # Close database connection
        await db_pool.close()

        print(f"\nCompleted at: {datetime.now().isoformat()}")
        print()
        print("🎯 Next steps:")
        print("   1. Embeddings are now available for semantic search")
        print("   2. AI chat will use vector similarity to find relevant products")
        print("   3. Test the chat with queries like:")
        print("      - 'I need sanders for metal and plastic'")
        print("      - 'What cordless drills do you have?'")
        print("      - 'Show me safety equipment'")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
