#!/usr/bin/env python3
"""
Pre-download AI models for faster container startup.
This script downloads and caches required models before deployment.
"""

import os
import sys
import signal
from pathlib import Path

# Timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Download timed out")

# Set timeout for model downloads (5 minutes max)
DOWNLOAD_TIMEOUT = 300

def download_sentence_transformer_model():
    """Download SentenceTransformer model for embeddings"""
    try:
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        print(f"Downloading SentenceTransformer model: {model_name}")
        print(f"Timeout set to {DOWNLOAD_TIMEOUT} seconds")

        # Set alarm for timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(DOWNLOAD_TIMEOUT)

        try:
            # Download and cache the model
            model = SentenceTransformer(model_name)

            # Test the model
            test_embedding = model.encode("test sentence")
            print(f"Model downloaded successfully!")
            print(f"Embedding dimension: {len(test_embedding)}")

            # Get cache directory
            cache_dir = Path.home() / '.cache' / 'torch' / 'sentence_transformers'
            print(f"Model cached at: {cache_dir}")

            return True
        finally:
            # Cancel the alarm
            signal.alarm(0)

    except TimeoutError as e:
        print(f"ERROR: Download timed out after {DOWNLOAD_TIMEOUT} seconds")
        print("Models will be downloaded on first API use instead")
        return False
    except ImportError:
        print("ERROR: sentence-transformers not installed")
        print("Install with: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"ERROR downloading model: {e}")
        return False

def download_transformers_model():
    """Download transformer model for intent classification"""
    try:
        from transformers import AutoTokenizer, AutoModel

        model_name = "distilbert-base-uncased"
        print(f"Downloading transformer model: {model_name}")
        print(f"Timeout set to {DOWNLOAD_TIMEOUT} seconds")

        # Set alarm for timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(DOWNLOAD_TIMEOUT)

        try:
            # Download tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)

            print(f"Transformer model downloaded successfully!")
            return True
        finally:
            # Cancel the alarm
            signal.alarm(0)

    except TimeoutError as e:
        print(f"ERROR: Download timed out after {DOWNLOAD_TIMEOUT} seconds")
        print("Models will be downloaded on first API use instead")
        return False
    except ImportError:
        print("ERROR: transformers not installed")
        print("Install with: pip install transformers")
        return False
    except Exception as e:
        print(f"ERROR downloading transformer model: {e}")
        return False

def main():
    """Download all required models"""
    print("=" * 60)
    print("AI Model Pre-download Script")
    print("=" * 60)

    success = True

    # Download SentenceTransformer for embeddings
    print("\n1. Downloading SentenceTransformer model...")
    if not download_sentence_transformer_model():
        success = False

    # Download Transformers for intent classification
    print("\n2. Downloading Transformer model for intent classification...")
    if not download_transformers_model():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: All models downloaded successfully!")
        print("Models are cached and ready for use in containers.")
        return 0
    else:
        print("FAILURE: Some models failed to download.")
        print("Check the errors above and ensure dependencies are installed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
