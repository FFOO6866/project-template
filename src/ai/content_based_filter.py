"""
Content-Based Filtering Algorithm
TF-IDF, cosine similarity, and semantic embeddings for product matching

Features:
- TF-IDF vectorization
- Cosine similarity scoring
- Semantic embeddings (sentence-transformers)
- Keyword extraction and matching
- N-gram analysis
"""

import logging
from typing import Dict, List, Optional, Tuple
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ContentBasedFilter:
    """
    Content-based filtering using NLP techniques

    Techniques:
    1. TF-IDF: Statistical term importance analysis
    2. Cosine similarity: Vector-based similarity measurement
    3. Semantic embeddings: Deep learning-based semantic understanding
    4. Keyword matching: Exact and fuzzy keyword matching
    """

    def __init__(self, embedding_model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize content-based filter

        Args:
            embedding_model_name: Name of sentence-transformer model to use
        """
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8,
            lowercase=True,
            strip_accents='unicode'
        )

        # Initialize sentence transformer for embeddings
        try:
            self.embedding_model = SentenceTransformer(embedding_model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"✅ Loaded embedding model: {embedding_model_name} (dim={self.embedding_dim})")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.embedding_model = None
            self.embedding_dim = None

        # Cache for embeddings
        self.embedding_cache = {}

        logger.info("✅ Content-based filter initialized")

    def calculate_tfidf_similarity(
        self,
        text1: str,
        text2: str,
        use_cache: bool = True
    ) -> float:
        """
        Calculate TF-IDF cosine similarity between two texts

        Args:
            text1: First text
            text2: Second text
            use_cache: Whether to use cached vectors (not implemented yet)

        Returns:
            Cosine similarity score between 0 and 1

        FAIL-FAST: Raises error if texts are empty or calculation fails
        """
        if not text1 or not text2:
            raise ValueError("Empty text provided for TF-IDF similarity calculation")

        try:
            # Vectorize both texts
            vectors = self.tfidf_vectorizer.fit_transform([text1, text2])

            # Calculate cosine similarity
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

            return float(similarity)

        except Exception as e:
            logger.error(f"❌ TF-IDF similarity calculation failed: {e}")
            raise RuntimeError(
                f"TF-IDF vectorization failed: {e}. "
                "Check that sklearn is installed and texts are valid."
            )

    def calculate_embedding_similarity(
        self,
        text1: str,
        text2: str,
        use_cache: bool = True
    ) -> float:
        """
        Calculate semantic similarity using sentence embeddings

        Args:
            text1: First text
            text2: Second text
            use_cache: Whether to use cached embeddings

        Returns:
            Cosine similarity score between 0 and 1

        FAIL-FAST: Raises error if embedding model unavailable or calculation fails
        """
        if not self.embedding_model:
            raise RuntimeError(
                "CRITICAL: Sentence transformer embedding model not loaded. "
                "Check that sentence-transformers is installed and model is available. "
                "Cannot provide fallback score - embeddings are required."
            )

        if not text1 or not text2:
            raise ValueError("Empty text provided for embedding similarity calculation")

        try:
            # Get embeddings (with caching)
            emb1 = self._get_embedding(text1, use_cache)
            emb2 = self._get_embedding(text2, use_cache)

            if emb1 is None or emb2 is None:
                raise ValueError("Failed to generate embeddings for input texts")

            # Calculate cosine similarity
            similarity = cosine_similarity([emb1], [emb2])[0][0]

            return float(similarity)

        except Exception as e:
            logger.error(f"❌ Embedding similarity calculation failed: {e}")
            raise RuntimeError(
                f"Embedding similarity failed: {e}. "
                "Check that sentence-transformers is properly installed."
            )

    def calculate_keyword_score(
        self,
        product_text: str,
        query_keywords: List[str],
        exact_match_weight: float = 0.7,
        partial_match_weight: float = 0.3
    ) -> float:
        """
        Calculate keyword matching score

        Args:
            product_text: Product text to match against
            query_keywords: List of query keywords
            exact_match_weight: Weight for exact matches
            partial_match_weight: Weight for partial matches

        Returns:
            Keyword match score between 0 and 1

        FAIL-FAST: Raises error if inputs are invalid
        """
        if not query_keywords:
            raise ValueError("No query keywords provided for keyword scoring")

        if not product_text:
            raise ValueError("Empty product text provided for keyword scoring")

        try:
            product_text_lower = product_text.lower()
            product_words = set(re.findall(r'\b\w+\b', product_text_lower))

            exact_matches = 0
            partial_matches = 0

            for keyword in query_keywords:
                keyword_lower = keyword.lower()

                # Exact match (whole keyword in product text)
                if keyword_lower in product_text_lower:
                    exact_matches += 1
                else:
                    # Partial match (any word in keyword matches product words)
                    keyword_words = set(re.findall(r'\b\w+\b', keyword_lower))
                    if keyword_words & product_words:
                        partial_matches += 1

            # Calculate weighted score
            total_keywords = len(query_keywords)
            exact_score = (exact_matches / total_keywords) * exact_match_weight
            partial_score = (partial_matches / total_keywords) * partial_match_weight

            return min(exact_score + partial_score, 1.0)

        except Exception as e:
            logger.error(f"❌ Keyword scoring failed: {e}")
            raise RuntimeError(f"Keyword matching calculation failed: {e}")

    def extract_keywords(
        self,
        text: str,
        max_keywords: int = 20,
        min_word_length: int = 3
    ) -> List[str]:
        """
        Extract important keywords from text

        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract
            min_word_length: Minimum word length to consider

        Returns:
            List of extracted keywords
        """
        try:
            # Clean and tokenize
            text_lower = text.lower()
            words = re.findall(r'\b[a-z]{' + str(min_word_length) + r',}\b', text_lower)

            # Remove common stop words
            stop_words = {
                'the', 'and', 'for', 'are', 'with', 'from', 'will', 'has',
                'have', 'been', 'this', 'that', 'can', 'all', 'our', 'you',
                'your', 'their', 'they', 'them', 'these', 'those', 'what',
                'which', 'when', 'where', 'who', 'why', 'how', 'but', 'not'
            }

            filtered_words = [w for w in words if w not in stop_words]

            # Count word frequencies
            word_counts = Counter(filtered_words)

            # Get most common keywords
            keywords = [word for word, count in word_counts.most_common(max_keywords)]

            return keywords

        except Exception as e:
            logger.debug(f"Keyword extraction failed: {e}")
            return []

    def calculate_ngram_overlap(
        self,
        text1: str,
        text2: str,
        n: int = 2
    ) -> float:
        """
        Calculate n-gram overlap between two texts

        Args:
            text1: First text
            text2: Second text
            n: N-gram size (default: 2 for bigrams)

        Returns:
            Overlap score between 0 and 1
        """
        try:
            ngrams1 = self._extract_ngrams(text1, n)
            ngrams2 = self._extract_ngrams(text2, n)

            if not ngrams1 or not ngrams2:
                return 0.0

            # Calculate Jaccard similarity
            intersection = len(ngrams1 & ngrams2)
            union = len(ngrams1 | ngrams2)

            if union == 0:
                return 0.0

            return intersection / union

        except Exception as e:
            logger.debug(f"N-gram overlap calculation failed: {e}")
            return 0.0

    def calculate_composite_similarity(
        self,
        product_text: str,
        query_text: str,
        query_keywords: List[str] = None,
        weights: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        Calculate composite similarity using multiple techniques

        Args:
            product_text: Product text
            query_text: Query text
            query_keywords: Optional list of query keywords
            weights: Optional custom weights for each technique

        Returns:
            Dictionary with individual scores and composite score
        """
        try:
            # Default weights
            if weights is None:
                weights = {
                    'tfidf': 0.35,
                    'embedding': 0.35,
                    'keyword': 0.20,
                    'ngram': 0.10
                }

            # Calculate individual scores
            tfidf_score = self.calculate_tfidf_similarity(product_text, query_text)
            embedding_score = self.calculate_embedding_similarity(product_text, query_text)

            # Extract keywords if not provided
            if query_keywords is None:
                query_keywords = self.extract_keywords(query_text)

            keyword_score = self.calculate_keyword_score(product_text, query_keywords)
            ngram_score = self.calculate_ngram_overlap(product_text, query_text)

            # Calculate weighted composite score
            composite_score = (
                tfidf_score * weights['tfidf'] +
                embedding_score * weights['embedding'] +
                keyword_score * weights['keyword'] +
                ngram_score * weights['ngram']
            )

            return {
                'tfidf_score': tfidf_score,
                'embedding_score': embedding_score,
                'keyword_score': keyword_score,
                'ngram_score': ngram_score,
                'composite_score': composite_score,
                'weights': weights
            }

        except Exception as e:
            logger.error(f"Composite similarity calculation failed: {e}")
            return {
                'tfidf_score': 0.0,
                'embedding_score': 0.0,
                'keyword_score': 0.0,
                'ngram_score': 0.0,
                'composite_score': 0.0,
                'weights': weights or {}
            }

    def rank_products_by_similarity(
        self,
        products: List[Dict],
        query_text: str,
        query_keywords: List[str] = None,
        limit: int = 20
    ) -> List[Tuple[Dict, float]]:
        """
        Rank products by similarity to query

        Args:
            products: List of product dictionaries
            query_text: Query text
            query_keywords: Optional query keywords
            limit: Maximum number of results

        Returns:
            List of (product, score) tuples, sorted by score descending
        """
        try:
            scored_products = []

            for product in products:
                # Prepare product text
                product_text = self._prepare_product_text(product)

                # Calculate composite similarity
                similarity_result = self.calculate_composite_similarity(
                    product_text,
                    query_text,
                    query_keywords
                )

                scored_products.append((
                    product,
                    similarity_result['composite_score']
                ))

            # Sort by score descending
            scored_products.sort(key=lambda x: x[1], reverse=True)

            return scored_products[:limit]

        except Exception as e:
            logger.error(f"Product ranking failed: {e}")
            return []

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_embedding(self, text: str, use_cache: bool = True) -> Optional[np.ndarray]:
        """Get embedding for text (with caching)"""
        try:
            if not self.embedding_model:
                return None

            # Check cache
            if use_cache and text in self.embedding_cache:
                return self.embedding_cache[text]

            # Generate embedding
            embedding = self.embedding_model.encode(text)

            # Cache result
            if use_cache:
                # Limit cache size
                if len(self.embedding_cache) > 1000:
                    # Remove oldest entries
                    keys_to_remove = list(self.embedding_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self.embedding_cache[key]

                self.embedding_cache[text] = embedding

            return embedding

        except Exception as e:
            logger.debug(f"Embedding generation failed: {e}")
            return None

    def _prepare_product_text(self, product: Dict) -> str:
        """Prepare product text for similarity analysis"""
        parts = []

        # Add product fields
        if product.get('name'):
            parts.append(product['name'])
        if product.get('description'):
            parts.append(product['description'])
        if product.get('category'):
            parts.append(product['category'])
        if product.get('brand'):
            parts.append(product['brand'])
        if product.get('keywords'):
            if isinstance(product['keywords'], list):
                parts.extend(product['keywords'])
            else:
                parts.append(str(product['keywords']))

        return ' '.join(parts)

    def _extract_ngrams(self, text: str, n: int) -> set:
        """Extract n-grams from text"""
        try:
            # Clean and tokenize
            text_lower = text.lower()
            words = re.findall(r'\b[a-z]+\b', text_lower)

            if len(words) < n:
                return set()

            # Generate n-grams
            ngrams = set()
            for i in range(len(words) - n + 1):
                ngram = tuple(words[i:i + n])
                ngrams.add(ngram)

            return ngrams

        except Exception:
            return set()

    def get_embedding_cache_stats(self) -> Dict[str, int]:
        """Get embedding cache statistics"""
        return {
            'cached_embeddings': len(self.embedding_cache),
            'embedding_dimension': self.embedding_dim or 0,
            'model_loaded': self.embedding_model is not None
        }

    def clear_embedding_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("✅ Embedding cache cleared")
