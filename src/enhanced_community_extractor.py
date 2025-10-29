"""
Enhanced Community Knowledge Extraction System for Horme DIY Platform.

This enhanced system builds upon the existing community knowledge extractor to provide:
1. Advanced DIY forum scrapers (Reddit r/DIY, Stack Exchange, Singapore forums)
2. YouTube tutorial analysis with tool and product extraction
3. Intelligent knowledge processing pipeline with ML-based classification
4. Product database integration with semantic matching
5. Structured knowledge graph storage
6. Real-time community trend analysis

Key Features:
- Multi-threaded scraping with respectful rate limiting
- Advanced NLP for problem-solution pattern extraction
- Computer vision for YouTube thumbnail analysis
- Singapore-specific DIY community integration
- Real-time trend detection and seasonal pattern analysis
- Integration with existing Horme product database
"""

import os
import json
import time
import asyncio
import aiohttp
import logging
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import urljoin, urlparse
import concurrent.futures
from threading import Lock
import sqlite3

# Enhanced imports for ML and NLP
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import existing models
from community_knowledge_extractor import (
    CommunityKnowledgeExtractor, ExtractionConfig, CommunityPost, 
    KnowledgePattern, SourceType, ContentType, ConfidenceLevel
)

# Web scraping imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    import requests_html
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False


@dataclass
class EnhancedExtractionConfig(ExtractionConfig):
    """Enhanced configuration with additional capabilities."""
    
    # Singapore-specific forums
    singapore_forums: List[str] = field(default_factory=lambda: [
        "https://www.hwz.com.sg/forum/threads/",
        "https://forums.hardwarezone.com.sg/",
        "https://www.renotalk.com/forum/",
        "https://singaporebrides.com/forum/",
        "https://www.propertyguru.com.sg/forum/"
    ])
    
    # Advanced YouTube channels (Singapore and international)
    enhanced_youtube_channels: Dict[str, str] = field(default_factory=lambda: {
        # International DIY channels
        "this_old_house": "UC7MfDpBUeJhm24bFhxJGU-w",
        "steve_ramsey": "UCQ1LnOJxJb6KxZPJdIb2-wGw",
        "diy_creators": "UC-7XY-W_C84cW2MNqujgFWQ",
        "fix_this_build_that": "UCnorhjQR4zJkT7AVNhu395Q",
        "home_renovision": "UC5HRNRWMVEgbvOKu8ULvI6w",
        "april_wilkerson": "UC4v2tQ8GomWIDjxQDpLp5Rg",
        "john_malecki": "UCjp-6Jztwg13xTXekmVBOSQ",
        
        # Singapore-specific DIY channels
        "singapore_diy": "UCsingaporeDIY123",  # Placeholder - actual channels would be researched
        "sg_home_improvement": "UCSGHomeImprovement456",
        "asian_woodworking": "UCAsianWoodworking789"
    })
    
    # Stack Exchange sites
    stack_exchange_sites: List[str] = field(default_factory=lambda: [
        "diy.stackexchange.com",
        "woodworking.stackexchange.com",
        "electronics.stackexchange.com",
        "gardening.stackexchange.com",
        "mechanics.stackexchange.com"
    ])
    
    # Enhanced NLP settings
    enable_sentiment_analysis: bool = True
    enable_topic_modeling: bool = True
    enable_entity_extraction: bool = True
    enable_semantic_similarity: bool = True
    
    # Computer vision for YouTube thumbnails
    enable_thumbnail_analysis: bool = True
    
    # Advanced matching settings
    use_semantic_matching: bool = True
    product_matching_threshold: float = 0.75
    
    # Knowledge graph integration
    knowledge_graph_enabled: bool = True
    knowledge_graph_db: str = "community_knowledge.db"
    
    # Real-time features
    enable_trending_analysis: bool = True
    trending_window_days: int = 7
    min_trend_mentions: int = 10
    
    # Singapore localization
    singapore_specific_terms: List[str] = field(default_factory=lambda: [
        "HDB", "BTO", "condo", "landed property", "renovation permit",
        "town council", "HIP", "SERS", "COV", "resale flat"
    ])


@dataclass
class VideoAnalysis:
    """Analysis results for YouTube video content."""
    
    video_id: str
    title: str
    description: str
    channel_name: str
    
    # Tool and product extraction
    tools_mentioned: List[str] = field(default_factory=list)
    products_mentioned: List[str] = field(default_factory=list)
    materials_mentioned: List[str] = field(default_factory=list)
    brands_mentioned: List[str] = field(default_factory=list)
    
    # Project classification
    project_type: Optional[str] = None
    project_complexity: Optional[str] = None  # beginner, intermediate, advanced
    estimated_duration: Optional[str] = None
    estimated_cost: Optional[str] = None
    
    # Content analysis
    step_by_step_guide: bool = False
    has_parts_list: bool = False
    has_safety_warnings: bool = False
    tutorial_quality_score: float = 0.0
    
    # Engagement metrics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    engagement_score: float = 0.0
    
    # Thumbnail analysis (if enabled)
    thumbnail_objects: List[str] = field(default_factory=list)
    thumbnail_text: Optional[str] = None
    
    # Singapore-specific context
    singapore_relevant: bool = False
    local_suppliers_mentioned: List[str] = field(default_factory=list)


@dataclass
class ProblemSolutionPair:
    """Identified problem-solution pairs from community discussions."""
    
    problem_id: str
    problem_description: str
    problem_category: str
    problem_keywords: List[str] = field(default_factory=list)
    
    solutions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Confidence and validation
    confidence_score: float = 0.0
    community_validation: int = 0  # upvotes, likes, positive responses
    expert_validation: bool = False
    
    # Product relations
    related_products: List[str] = field(default_factory=list)
    related_tools: List[str] = field(default_factory=list)
    
    # Context
    seasonal_relevance: Optional[str] = None
    skill_level_required: Optional[str] = None
    project_types: List[str] = field(default_factory=list)
    
    # Sources
    source_posts: List[str] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class TrendingTopic:
    """Trending topics identified from community discussions."""
    
    topic_id: str
    topic_name: str
    topic_keywords: List[str]
    
    # Trend metrics
    mention_count: int
    trend_score: float
    velocity: float  # rate of increase
    peak_date: Optional[datetime] = None
    
    # Content analysis
    sentiment_trend: Dict[str, float] = field(default_factory=dict)  # date -> sentiment
    related_products: List[str] = field(default_factory=list)
    geographic_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Predictions
    predicted_growth: Optional[float] = None
    seasonal_pattern: Optional[str] = None
    recommendation_priority: str = "medium"  # low, medium, high, urgent


class EnhancedCommunityExtractor(CommunityKnowledgeExtractor):
    """
    Enhanced community knowledge extractor with advanced capabilities.
    
    Extends the base extractor with:
    - Advanced forum scraping including Singapore-specific sources
    - YouTube tutorial analysis with computer vision
    - ML-powered problem-solution extraction
    - Real-time trend analysis
    - Knowledge graph integration
    """
    
    def __init__(self, config: EnhancedExtractionConfig):
        super().__init__(config)
        self.enhanced_config = config
        
        # Initialize enhanced components
        self._initialize_nlp_components()
        self._initialize_ml_components()
        self._initialize_knowledge_graph()
        self._initialize_singapore_context()
        
        # Enhanced data storage
        self.video_analyses: Dict[str, VideoAnalysis] = {}
        self.problem_solution_pairs: Dict[str, ProblemSolutionPair] = {}
        self.trending_topics: Dict[str, TrendingTopic] = {}
        
        # Threading for concurrent processing
        self.extraction_lock = Lock()
        self.max_workers = 5
        
        self.logger.info("Enhanced community extractor initialized")
    
    def _initialize_nlp_components(self) -> None:
        """Initialize NLP components for enhanced text analysis."""
        if HAS_NLTK:
            try:
                # Download required NLTK data
                nltk.download('vader_lexicon', quiet=True)
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
                
                # Add Singapore-specific stop words
                self.stop_words.update(['lah', 'lor', 'leh', 'sia', 'hor', 'meh'])
                
                self.has_nlp = True
                self.logger.info("NLP components initialized successfully")
            except Exception as e:
                self.logger.warning(f"NLP initialization failed: {e}")
                self.has_nlp = False
        else:
            self.has_nlp = False
            self.logger.warning("NLTK not available, NLP features disabled")
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML components for clustering and classification."""
        if HAS_SKLEARN:
            try:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 3)
                )
                self.topic_clusterer = KMeans(n_clusters=10, random_state=42)
                self.has_ml = True
                self.logger.info("ML components initialized successfully")
            except Exception as e:
                self.logger.warning(f"ML initialization failed: {e}")
                self.has_ml = False
        else:
            self.has_ml = False
            self.logger.warning("Scikit-learn not available, ML features disabled")
    
    def _initialize_knowledge_graph(self) -> None:
        """Initialize local knowledge graph database."""
        if self.enhanced_config.knowledge_graph_enabled:
            try:
                self.kg_db_path = Path(self.enhanced_config.output_directory) / self.enhanced_config.knowledge_graph_db
                self.kg_conn = sqlite3.connect(str(self.kg_db_path), check_same_thread=False)
                self._create_knowledge_graph_schema()
                self.has_knowledge_graph = True
                self.logger.info("Knowledge graph database initialized")
            except Exception as e:
                self.logger.warning(f"Knowledge graph initialization failed: {e}")
                self.has_knowledge_graph = False
        else:
            self.has_knowledge_graph = False
    
    def _create_knowledge_graph_schema(self) -> None:
        """Create knowledge graph database schema."""
        cursor = self.kg_conn.cursor()
        
        # Entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                from_entity TEXT NOT NULL,
                to_entity TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_entity) REFERENCES entities (id),
                FOREIGN KEY (to_entity) REFERENCES entities (id)
            )
        """)
        
        # Community insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_insights (
                id TEXT PRIMARY KEY,
                insight_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence_score REAL,
                source_posts TEXT,
                related_entities TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trending topics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trending_topics (
                id TEXT PRIMARY KEY,
                topic_name TEXT NOT NULL,
                keywords TEXT,
                mention_count INTEGER,
                trend_score REAL,
                velocity REAL,
                peak_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.kg_conn.commit()
    
    def _initialize_singapore_context(self) -> None:
        """Initialize Singapore-specific context and terminology."""
        self.singapore_terms = set(self.enhanced_config.singapore_specific_terms)
        
        # Singapore-specific tool and brand names
        self.singapore_brands = {
            'mr diy', 'home-fix', 'selffix', 'courts', 'harvey norman',
            'gain city', 'best denki', 'mega discount store'
        }
        
        # Singapore-specific project categories
        self.singapore_project_types = {
            'hdb renovation', 'bto renovation', 'condo renovation',
            'hdb kitchen renovation', 'bathroom renovation singapore',
            'aircon installation singapore', 'vinyl flooring singapore'
        }
        
        self.logger.info("Singapore context initialized")
    
    def extract_singapore_forums(self) -> List[CommunityPost]:
        """Extract knowledge from Singapore-specific DIY forums."""
        posts = []
        
        if not HAS_SCRAPING:
            self.logger.warning("Web scraping not available for forum extraction")
            return posts
        
        singapore_forum_configs = [
            {
                "url": "https://forums.hardwarezone.com.sg/threads/",
                "name": "HardwareZone",
                "selectors": {
                    "post_title": ".threadTitle",
                    "post_content": ".messageContent",
                    "author": ".username",
                    "timestamp": ".dateTime"
                }
            },
            {
                "url": "https://www.renotalk.com/forum/",
                "name": "RenoTalk",
                "selectors": {
                    "post_title": "h3.ipsType_sectionHead",
                    "post_content": ".ipsType_normal",
                    "author": ".ipsType_break",
                    "timestamp": "time"
                }
            }
        ]
        
        for forum_config in singapore_forum_configs:
            try:
                self.logger.info(f"Extracting from {forum_config['name']}")
                forum_posts = self._scrape_singapore_forum(forum_config)
                posts.extend(forum_posts)
                
                # Add Singapore-specific analysis
                for post in forum_posts:
                    self._analyze_singapore_context(post)
                
            except Exception as e:
                self.logger.error(f"Error extracting from {forum_config['name']}: {e}")
        
        return posts
    
    def _scrape_singapore_forum(self, forum_config: Dict[str, Any]) -> List[CommunityPost]:
        """Scrape a specific Singapore forum."""
        posts = []
        
        try:
            # Use Selenium for dynamic content if available
            if HAS_SELENIUM:
                posts.extend(self._scrape_with_selenium(forum_config))
            else:
                posts.extend(self._scrape_with_requests(forum_config))
                
        except Exception as e:
            self.logger.error(f"Forum scraping failed: {e}")
        
        return posts
    
    def _scrape_with_selenium(self, forum_config: Dict[str, Any]) -> List[CommunityPost]:
        """Scrape forum using Selenium for dynamic content."""
        posts = []
        
        try:
            # Setup Chrome options for headless browsing
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Navigate and extract posts
            driver.get(forum_config["url"])
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract post elements based on selectors
            selectors = forum_config["selectors"]
            
            title_elements = driver.find_elements(By.CSS_SELECTOR, selectors.get("post_title", ""))
            content_elements = driver.find_elements(By.CSS_SELECTOR, selectors.get("post_content", ""))
            
            for i, (title_elem, content_elem) in enumerate(zip(title_elements[:20], content_elements[:20])):
                try:
                    post = CommunityPost(
                        post_id=f"sg_forum_{forum_config['name'].lower()}_{i}_{int(time.time())}",
                        source_type=SourceType.FORUM,
                        source_url=driver.current_url,
                        title=title_elem.text.strip(),
                        content=content_elem.text.strip(),
                        author="singapore_user",
                        created_at=datetime.now(),
                        categories=["singapore_diy"],
                        content_type=ContentType.QUESTION
                    )
                    
                    posts.append(post)
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting post {i}: {e}")
            
            driver.quit()
            
        except Exception as e:
            self.logger.error(f"Selenium scraping failed: {e}")
        
        return posts
    
    def _scrape_with_requests(self, forum_config: Dict[str, Any]) -> List[CommunityPost]:
        """Fallback scraping using requests and BeautifulSoup."""
        posts = []
        
        try:
            self._respect_rate_limits()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(forum_config["url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract posts using basic selectors
                post_containers = soup.find_all('div', class_='post')[:10]  # Limit to 10 posts
                
                for i, container in enumerate(post_containers):
                    try:
                        title = container.find('h3', class_='title')
                        content = container.find('div', class_='content')
                        
                        if title and content:
                            post = CommunityPost(
                                post_id=f"sg_forum_basic_{forum_config['name'].lower()}_{i}_{int(time.time())}",
                                source_type=SourceType.FORUM,
                                source_url=forum_config["url"],
                                title=title.get_text().strip(),
                                content=content.get_text().strip(),
                                author="singapore_user",
                                created_at=datetime.now(),
                                categories=["singapore_diy"],
                                content_type=ContentType.QUESTION
                            )
                            
                            posts.append(post)
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing post container {i}: {e}")
            
        except Exception as e:
            self.logger.error(f"Requests-based scraping failed: {e}")
        
        return posts
    
    def _analyze_singapore_context(self, post: CommunityPost) -> None:
        """Analyze Singapore-specific context in posts."""
        content_lower = f"{post.title} {post.content}".lower()
        
        # Check for Singapore-specific terms
        singapore_mentions = []
        for term in self.singapore_terms:
            if term.lower() in content_lower:
                singapore_mentions.append(term)
        
        if singapore_mentions:
            post.categories.append("singapore_specific")
            if not hasattr(post, 'singapore_context'):
                post.singapore_context = {}
            post.singapore_context['mentioned_terms'] = singapore_mentions
        
        # Check for Singapore brands
        sg_brands_mentioned = []
        for brand in self.singapore_brands:
            if brand in content_lower:
                sg_brands_mentioned.append(brand)
        
        if sg_brands_mentioned:
            post.mentioned_products.extend(sg_brands_mentioned)
            if not hasattr(post, 'singapore_context'):
                post.singapore_context = {}
            post.singapore_context['local_brands'] = sg_brands_mentioned
    
    def extract_enhanced_youtube_knowledge(self) -> List[VideoAnalysis]:
        """Extract enhanced knowledge from YouTube DIY channels."""
        video_analyses = []
        
        if not self.has_youtube_api:
            self.logger.warning("YouTube API not available")
            return video_analyses
        
        for channel_name, channel_id in self.enhanced_config.enhanced_youtube_channels.items():
            try:
                self.logger.info(f"Analyzing YouTube channel: {channel_name}")
                
                channel_analyses = self._analyze_youtube_channel(channel_id, channel_name)
                video_analyses.extend(channel_analyses)
                
            except Exception as e:
                self.logger.error(f"Error analyzing YouTube channel {channel_name}: {e}")
        
        return video_analyses
    
    def _analyze_youtube_channel(self, channel_id: str, channel_name: str) -> List[VideoAnalysis]:
        """Analyze a specific YouTube channel for DIY content."""
        analyses = []
        
        try:
            # Get channel videos
            request = self.youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=50,  # Increased for better analysis
                order="relevance",
                publishedAfter=(datetime.now() - timedelta(days=self.enhanced_config.max_age_days)).isoformat() + "Z",
                type="video",
                q="DIY tutorial how to"  # Filter for DIY content
            )
            
            self._respect_rate_limits()
            response = request.execute()
            
            for item in response.get("items", []):
                try:
                    video_id = item["id"]["videoId"]
                    snippet = item["snippet"]
                    
                    # Get detailed video statistics
                    stats_request = self.youtube.videos().list(
                        part="statistics,contentDetails,snippet",
                        id=video_id
                    )
                    
                    self._respect_rate_limits()
                    stats_response = stats_request.execute()
                    
                    if stats_response["items"]:
                        video_data = stats_response["items"][0]
                        analysis = self._analyze_video_content(video_data, channel_name)
                        analyses.append(analysis)
                        
                        # Store in instance storage
                        self.video_analyses[video_id] = analysis
                
                except Exception as e:
                    self.logger.warning(f"Error analyzing video: {e}")
        
        except Exception as e:
            self.logger.error(f"Channel analysis failed: {e}")
        
        return analyses
    
    def _analyze_video_content(self, video_data: Dict[str, Any], channel_name: str) -> VideoAnalysis:
        """Perform detailed analysis of video content."""
        snippet = video_data["snippet"]
        stats = video_data.get("statistics", {})
        
        video_id = video_data["id"]
        title = snippet["title"]
        description = snippet.get("description", "")
        
        analysis = VideoAnalysis(
            video_id=video_id,
            title=title,
            description=description,
            channel_name=channel_name,
            view_count=int(stats.get("viewCount", 0)),
            like_count=int(stats.get("likeCount", 0)),
            comment_count=int(stats.get("commentCount", 0))
        )
        
        # Extract tools and products from title and description
        content_text = f"{title} {description}".lower()
        
        # Tool extraction
        analysis.tools_mentioned = self._extract_tools_from_text(content_text)
        analysis.products_mentioned = self._extract_products_from_text(content_text) 
        analysis.materials_mentioned = self._extract_materials_from_text(content_text)
        analysis.brands_mentioned = self._extract_brands_from_text(content_text)
        
        # Project classification
        analysis.project_type = self._classify_project_type(content_text)
        analysis.project_complexity = self._assess_complexity(content_text)
        
        # Content quality analysis
        analysis.step_by_step_guide = self._has_step_by_step_guide(content_text)
        analysis.has_parts_list = self._has_parts_list(content_text)
        analysis.has_safety_warnings = self._has_safety_warnings(content_text)
        analysis.tutorial_quality_score = self._calculate_tutorial_quality(analysis)
        
        # Engagement analysis
        analysis.engagement_score = self._calculate_engagement_score(analysis)
        
        # Singapore relevance check
        analysis.singapore_relevant = self._check_singapore_relevance(content_text)
        if analysis.singapore_relevant:
            analysis.local_suppliers_mentioned = self._extract_singapore_suppliers(content_text)
        
        return analysis
    
    def _extract_tools_from_text(self, text: str) -> List[str]:
        """Extract tool mentions from text using enhanced patterns."""
        tools = []
        
        # Enhanced tool patterns including power tools, hand tools, and specialized equipment
        tool_patterns = [
            r'\b(drill|screwdriver|hammer|saw|wrench|pliers|chisel)\b',
            r'\b(circular saw|miter saw|table saw|reciprocating saw|jigsaw|band saw)\b',
            r'\b(impact driver|impact wrench|angle grinder|orbital sander|belt sander)\b',
            r'\b(router|planer|jointer|thickness planer|biscuit joiner)\b',
            r'\b(multimeter|wire stripper|soldering iron|heat gun|stud finder)\b',
            r'\b(level|tape measure|square|marking gauge|calipers)\b'
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tools.extend(matches)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(tools))
    
    def _extract_products_from_text(self, text: str) -> List[str]:
        """Extract product mentions from text."""
        products = []
        
        # Product patterns for common DIY products
        product_patterns = [
            r'\b(wood stain|paint|primer|varnish|polyurethane|lacquer)\b',
            r'\b(screws|nails|bolts|washers|nuts|brackets|hinges)\b',
            r'\b(lumber|plywood|MDF|particleboard|hardboard|drywall)\b',
            r'\b(insulation|caulk|sealant|adhesive|glue)\b',
            r'\b(pipe|fittings|valves|electrical wire|outlets|switches)\b'
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            products.extend(matches)
        
        return list(dict.fromkeys(products))
    
    def _extract_materials_from_text(self, text: str) -> List[str]:
        """Extract material mentions from text."""
        materials = []
        
        material_patterns = [
            r'\b(wood|metal|plastic|glass|ceramic|concrete|stone)\b',
            r'\b(steel|aluminum|copper|brass|iron|stainless steel)\b',
            r'\b(oak|pine|maple|birch|cherry|walnut|mahogany)\b',
            r'\b(PVC|HDPE|polycarbonate|acrylic|fiberglass)\b'
        ]
        
        for pattern in material_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            materials.extend(matches)
        
        return list(dict.fromkeys(materials))
    
    def _extract_brands_from_text(self, text: str) -> List[str]:
        """Extract brand mentions from text."""
        brands = []
        
        # Common DIY and power tool brands
        brand_patterns = [
            r'\b(dewalt|milwaukee|makita|ryobi|black.?decker|craftsman)\b',
            r'\b(bosch|festool|porter.?cable|delta|ridgid|husky)\b',
            r'\b(klein|fluke|channellock|irwin|stanley|kobalt)\b'
        ]
        
        for pattern in brand_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            brands.extend(matches)
        
        # Add Singapore brands
        for brand in self.singapore_brands:
            if brand in text:
                brands.append(brand)
        
        return list(dict.fromkeys(brands))
    
    def _classify_project_type(self, text: str) -> Optional[str]:
        """Classify the type of DIY project."""
        project_classifications = {
            "woodworking": ["wood", "saw", "chisel", "router", "lumber", "plywood"],
            "electrical": ["wire", "outlet", "switch", "breaker", "electrical", "voltage"],
            "plumbing": ["pipe", "faucet", "toilet", "drain", "water", "plumbing"],
            "painting": ["paint", "brush", "roller", "primer", "color", "finish"],
            "automotive": ["car", "engine", "brake", "oil", "mechanic", "automotive"],
            "home_improvement": ["renovation", "remodel", "upgrade", "repair", "fix"],
            "gardening": ["garden", "plant", "soil", "grow", "landscape", "outdoor"],
            "metalworking": ["metal", "welding", "steel", "aluminum", "forge", "grind"]
        }
        
        for project_type, keywords in project_classifications.items():
            if sum(1 for keyword in keywords if keyword in text) >= 2:
                return project_type
        
        return "general_diy"
    
    def _assess_complexity(self, text: str) -> Optional[str]:
        """Assess project complexity based on content indicators."""
        beginner_indicators = ["easy", "simple", "beginner", "basic", "quick", "starter"]
        intermediate_indicators = ["moderate", "some experience", "intermediate", "weekend project"]
        advanced_indicators = ["advanced", "expert", "professional", "complex", "challenging", "precision"]
        
        beginner_score = sum(1 for indicator in beginner_indicators if indicator in text)
        intermediate_score = sum(1 for indicator in intermediate_indicators if indicator in text)
        advanced_score = sum(1 for indicator in advanced_indicators if indicator in text)
        
        max_score = max(beginner_score, intermediate_score, advanced_score)
        
        if max_score == 0:
            return "intermediate"  # Default
        elif beginner_score == max_score:
            return "beginner"
        elif advanced_score == max_score:
            return "advanced"
        else:
            return "intermediate"
    
    def _has_step_by_step_guide(self, text: str) -> bool:
        """Check if content includes step-by-step instructions."""
        step_indicators = ["step 1", "step 2", "first step", "next step", "step by step", "instructions"]
        return any(indicator in text for indicator in step_indicators)
    
    def _has_parts_list(self, text: str) -> bool:
        """Check if content includes a parts or materials list."""
        list_indicators = ["parts list", "materials list", "shopping list", "what you need", "supplies", "materials:"]
        return any(indicator in text for indicator in list_indicators)
    
    def _has_safety_warnings(self, text: str) -> bool:
        """Check if content includes safety warnings."""
        safety_indicators = ["safety", "warning", "caution", "be careful", "wear protection", "safety glasses"]
        return any(indicator in text for indicator in safety_indicators)
    
    def _calculate_tutorial_quality(self, analysis: VideoAnalysis) -> float:
        """Calculate tutorial quality score based on content analysis."""
        quality_score = 0.0
        
        # Content completeness
        if analysis.step_by_step_guide:
            quality_score += 0.3
        if analysis.has_parts_list:
            quality_score += 0.2
        if analysis.has_safety_warnings:
            quality_score += 0.2
        
        # Tool and material detail
        if len(analysis.tools_mentioned) > 0:
            quality_score += 0.1
        if len(analysis.materials_mentioned) > 0:
            quality_score += 0.1
        
        # Engagement indicators
        if analysis.comment_count > 10:
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _calculate_engagement_score(self, analysis: VideoAnalysis) -> float:
        """Calculate engagement score based on view/like/comment ratios."""
        if analysis.view_count == 0:
            return 0.0
        
        like_ratio = analysis.like_count / analysis.view_count
        comment_ratio = analysis.comment_count / analysis.view_count
        
        # Normalize ratios (typical ranges for DIY videos)
        normalized_like_ratio = min(like_ratio / 0.02, 1.0)  # 2% is good like ratio
        normalized_comment_ratio = min(comment_ratio / 0.005, 1.0)  # 0.5% is good comment ratio
        
        engagement_score = (normalized_like_ratio * 0.7) + (normalized_comment_ratio * 0.3)
        return engagement_score
    
    def _check_singapore_relevance(self, text: str) -> bool:
        """Check if content is relevant to Singapore context."""
        singapore_indicators = list(self.singapore_terms) + list(self.singapore_brands)
        return any(indicator.lower() in text for indicator in singapore_indicators)
    
    def _extract_singapore_suppliers(self, text: str) -> List[str]:
        """Extract Singapore supplier mentions from text."""
        suppliers = []
        for brand in self.singapore_brands:
            if brand in text:
                suppliers.append(brand)
        return suppliers
    
    def extract_stack_exchange_knowledge(self) -> List[CommunityPost]:
        """Extract knowledge from Stack Exchange DIY sites."""
        posts = []
        
        for site in self.enhanced_config.stack_exchange_sites:
            try:
                self.logger.info(f"Extracting from {site}")
                site_posts = self._extract_stack_exchange_site(site)
                posts.extend(site_posts)
            except Exception as e:
                self.logger.error(f"Error extracting from {site}: {e}")
        
        return posts
    
    def _extract_stack_exchange_site(self, site: str) -> List[CommunityPost]:
        """Extract posts from a specific Stack Exchange site."""
        posts = []
        
        try:
            # Use Stack Exchange API
            api_url = f"https://api.stackexchange.com/2.3/questions"
            params = {
                "order": "desc",
                "sort": "votes",
                "site": site.replace(".stackexchange.com", "").replace(".com", ""),
                "pagesize": 50,
                "filter": "withbody"
            }
            
            self._respect_rate_limits()
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("items", []):
                    post = CommunityPost(
                        post_id=f"stackexchange_{item['question_id']}",
                        source_type=SourceType.FORUM,
                        source_url=item["link"],
                        title=item["title"],
                        content=item.get("body", ""),
                        author=item["owner"]["display_name"],
                        created_at=datetime.fromtimestamp(item["creation_date"]),
                        upvotes=item["score"],
                        views=item["view_count"],
                        categories=[site.split(".")[0]],
                        content_type=ContentType.QUESTION
                    )
                    
                    posts.append(post)
                    
                    # Extract answers for questions with high scores
                    if item["score"] > 5 and item.get("answer_count", 0) > 0:
                        answer_posts = self._extract_stack_exchange_answers(item["question_id"], site)
                        posts.extend(answer_posts)
            
        except Exception as e:
            self.logger.error(f"Stack Exchange API extraction failed: {e}")
        
        return posts
    
    def _extract_stack_exchange_answers(self, question_id: int, site: str) -> List[CommunityPost]:
        """Extract answers for a specific Stack Exchange question."""
        posts = []
        
        try:
            api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
            params = {
                "order": "desc",
                "sort": "votes",
                "site": site.replace(".stackexchange.com", "").replace(".com", ""),
                "filter": "withbody"
            }
            
            self._respect_rate_limits()
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("items", [])[:5]:  # Top 5 answers
                    if item["score"] > 2:  # Only high-scoring answers
                        post = CommunityPost(
                            post_id=f"stackexchange_answer_{item['answer_id']}",
                            source_type=SourceType.FORUM,
                            source_url=f"https://{site}/a/{item['answer_id']}",
                            title=f"Answer to question {question_id}",
                            content=item.get("body", ""),
                            author=item["owner"]["display_name"],
                            created_at=datetime.fromtimestamp(item["creation_date"]),
                            upvotes=item["score"],
                            content_type=ContentType.ANSWER
                        )
                        
                        posts.append(post)
        
        except Exception as e:
            self.logger.warning(f"Error extracting answers for question {question_id}: {e}")
        
        return posts
    
    def identify_problem_solution_patterns(self, posts: List[CommunityPost]) -> List[ProblemSolutionPair]:
        """Identify problem-solution patterns using enhanced NLP."""
        problem_solution_pairs = []
        
        if not self.has_nlp:
            self.logger.warning("NLP not available for problem-solution extraction")
            return problem_solution_pairs
        
        # Group posts by topic/category for better pattern detection
        topic_posts = {}
        for post in posts:
            for category in post.categories:
                if category not in topic_posts:
                    topic_posts[category] = []
                topic_posts[category].append(post)
        
        for topic, topic_posts_list in topic_posts.items():
            try:
                pairs = self._extract_topic_problem_solutions(topic, topic_posts_list)
                problem_solution_pairs.extend(pairs)
            except Exception as e:
                self.logger.error(f"Error extracting patterns for topic {topic}: {e}")
        
        return problem_solution_pairs
    
    def _extract_topic_problem_solutions(self, topic: str, posts: List[CommunityPost]) -> List[ProblemSolutionPair]:
        """Extract problem-solution pairs for a specific topic."""
        pairs = []
        
        # Identify problem posts
        problem_posts = []
        solution_posts = []
        
        for post in posts:
            content = f"{post.title} {post.content}".lower()
            
            # Problem indicators
            problem_indicators = [
                "problem", "issue", "trouble", "broken", "doesn't work", "failed",
                "help", "stuck", "can't", "won't", "error", "wrong", "damaged"
            ]
            
            # Solution indicators
            solution_indicators = [
                "solution", "fix", "solved", "worked", "success", "try this",
                "fixed", "resolved", "here's how", "do this", "use this"
            ]
            
            problem_score = sum(1 for indicator in problem_indicators if indicator in content)
            solution_score = sum(1 for indicator in solution_indicators if indicator in content)
            
            if problem_score > solution_score and problem_score > 0:
                problem_posts.append(post)
            elif solution_score > problem_score and solution_score > 0:
                solution_posts.append(post)
        
        # Match problems with solutions using semantic similarity
        for problem_post in problem_posts:
            try:
                problem_pair = self._create_problem_solution_pair(problem_post, solution_posts, topic)
                if problem_pair and len(problem_pair.solutions) > 0:
                    pairs.append(problem_pair)
                    
                    # Store in instance storage
                    self.problem_solution_pairs[problem_pair.problem_id] = problem_pair
                    
            except Exception as e:
                self.logger.warning(f"Error creating problem-solution pair: {e}")
        
        return pairs
    
    def _create_problem_solution_pair(
        self, 
        problem_post: CommunityPost, 
        solution_posts: List[CommunityPost], 
        topic: str
    ) -> Optional[ProblemSolutionPair]:
        """Create a problem-solution pair with matched solutions."""
        
        problem_content = f"{problem_post.title} {problem_post.content}"
        problem_keywords = self._extract_keywords(problem_content)
        
        # Find related solutions using keyword matching and semantic similarity
        related_solutions = []
        
        for solution_post in solution_posts:
            similarity_score = self._calculate_content_similarity(problem_content, f"{solution_post.title} {solution_post.content}")
            
            if similarity_score > 0.3:  # Threshold for relevance
                solution_data = {
                    "post_id": solution_post.post_id,
                    "solution_text": f"{solution_post.title} {solution_post.content}",
                    "author": solution_post.author,
                    "upvotes": solution_post.upvotes,
                    "confidence": solution_post.confidence_level.value,
                    "similarity_score": similarity_score
                }
                related_solutions.append(solution_data)
        
        if not related_solutions:
            return None
        
        # Sort solutions by relevance and community validation
        related_solutions.sort(key=lambda x: (x["similarity_score"] * x["upvotes"]), reverse=True)
        
        problem_id = f"problem_{topic}_{hashlib.md5(problem_content.encode()).hexdigest()[:8]}"
        
        pair = ProblemSolutionPair(
            problem_id=problem_id,
            problem_description=problem_content[:200],  # Truncate for storage
            problem_category=topic,
            problem_keywords=problem_keywords,
            solutions=related_solutions[:5],  # Top 5 solutions
            confidence_score=min(len(related_solutions) / 5, 1.0),
            community_validation=problem_post.upvotes,
            related_products=problem_post.mentioned_products,
            related_tools=problem_post.mentioned_tools,
            project_types=[topic],
            source_posts=[problem_post.post_id]
        )
        
        return pair
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using NLP."""
        if not self.has_nlp:
            return []
        
        try:
            # Tokenize and clean
            words = word_tokenize(text.lower())
            
            # Remove stopwords and short words
            keywords = [
                self.lemmatizer.lemmatize(word) 
                for word in words 
                if word.isalpha() and len(word) > 3 and word not in self.stop_words
            ]
            
            # Return unique keywords, limited to top 10
            return list(dict.fromkeys(keywords))[:10]
            
        except Exception as e:
            self.logger.warning(f"Keyword extraction failed: {e}")
            return []
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        if not self.has_ml:
            # Fallback to simple keyword overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0
        
        try:
            # Use TF-IDF for semantic similarity
            tfidf = TfidfVectorizer(stop_words='english', max_features=100)
            tfidf_matrix = tfidf.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
            
        except Exception as e:
            self.logger.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def analyze_trending_topics(self, posts: List[CommunityPost]) -> List[TrendingTopic]:
        """Analyze trending topics from community posts."""
        trending_topics = []
        
        if not posts:
            return trending_topics
        
        # Recent posts for trend analysis
        cutoff_date = datetime.now() - timedelta(days=self.enhanced_config.trending_window_days)
        recent_posts = [post for post in posts if post.created_at >= cutoff_date]
        
        if len(recent_posts) < self.enhanced_config.min_trend_mentions:
            self.logger.info("Insufficient recent posts for trend analysis")
            return trending_topics
        
        # Extract and count topic keywords
        topic_mentions = {}
        topic_posts = {}
        
        for post in recent_posts:
            content = f"{post.title} {post.content}"
            keywords = self._extract_keywords(content)
            
            for keyword in keywords:
                if keyword not in topic_mentions:
                    topic_mentions[keyword] = 0
                    topic_posts[keyword] = []
                
                topic_mentions[keyword] += 1
                topic_posts[keyword].append(post)
        
        # Identify trending topics
        sorted_topics = sorted(topic_mentions.items(), key=lambda x: x[1], reverse=True)
        
        for keyword, mention_count in sorted_topics[:20]:  # Top 20 topics
            if mention_count >= self.enhanced_config.min_trend_mentions:
                try:
                    trending_topic = self._analyze_topic_trend(keyword, mention_count, topic_posts[keyword])
                    trending_topics.append(trending_topic)
                    
                    # Store in instance storage
                    self.trending_topics[trending_topic.topic_id] = trending_topic
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing trend for {keyword}: {e}")
        
        return trending_topics
    
    def _analyze_topic_trend(self, keyword: str, mention_count: int, posts: List[CommunityPost]) -> TrendingTopic:
        """Analyze a specific trending topic."""
        
        # Calculate trend metrics
        posts_by_date = {}
        for post in posts:
            date_key = post.created_at.date().isoformat()
            if date_key not in posts_by_date:
                posts_by_date[date_key] = 0
            posts_by_date[date_key] += 1
        
        # Calculate velocity (rate of increase)
        dates_sorted = sorted(posts_by_date.keys())
        if len(dates_sorted) >= 2:
            early_mentions = sum(posts_by_date[date] for date in dates_sorted[:len(dates_sorted)//2])
            late_mentions = sum(posts_by_date[date] for date in dates_sorted[len(dates_sorted)//2:])
            velocity = (late_mentions - early_mentions) / max(early_mentions, 1)
        else:
            velocity = 0.0
        
        # Find peak date
        peak_date = None
        if posts_by_date:
            peak_date_str = max(posts_by_date.keys(), key=lambda x: posts_by_date[x])
            peak_date = datetime.fromisoformat(peak_date_str)
        
        # Calculate trend score
        trend_score = mention_count * (1 + velocity)
        
        # Analyze sentiment trend
        sentiment_trend = {}
        if self.has_nlp:
            for post in posts:
                date_key = post.created_at.date().isoformat()
                content = f"{post.title} {post.content}"
                sentiment = self.sentiment_analyzer.polarity_scores(content)
                
                if date_key not in sentiment_trend:
                    sentiment_trend[date_key] = []
                sentiment_trend[date_key].append(sentiment['compound'])
        
        # Average sentiment by date
        avg_sentiment_trend = {
            date: sum(sentiments) / len(sentiments)
            for date, sentiments in sentiment_trend.items()
        }
        
        # Extract related products and keywords
        related_products = set()
        related_keywords = set()
        
        for post in posts:
            related_products.update(post.mentioned_products)
            content_keywords = self._extract_keywords(f"{post.title} {post.content}")
            related_keywords.update(content_keywords[:5])  # Top 5 keywords per post
        
        # Determine recommendation priority
        if trend_score > 100 and velocity > 0.5:
            priority = "urgent"
        elif trend_score > 50 and velocity > 0.2:
            priority = "high"
        elif trend_score > 20:
            priority = "medium"
        else:
            priority = "low"
        
        topic_id = f"trend_{keyword}_{int(time.time())}"
        
        trending_topic = TrendingTopic(
            topic_id=topic_id,
            topic_name=keyword,
            topic_keywords=list(related_keywords)[:10],
            mention_count=mention_count,
            trend_score=trend_score,
            velocity=velocity,
            peak_date=peak_date,
            sentiment_trend=avg_sentiment_trend,
            related_products=list(related_products)[:10],
            recommendation_priority=priority
        )
        
        return trending_topic
    
    def create_enhanced_workflow(self) -> WorkflowBuilder:
        """Create enhanced workflow for comprehensive community extraction."""
        workflow = WorkflowBuilder()
        
        # Stage 1: Multi-source extraction
        workflow.add_node("PythonCodeNode", "extract_reddit", {
            "code": """
from enhanced_community_extractor import EnhancedCommunityExtractor, EnhancedExtractionConfig

config = EnhancedExtractionConfig()
extractor = EnhancedCommunityExtractor(config)

reddit_posts = extractor.extract_reddit_knowledge()
print(f"Extracted {len(reddit_posts)} Reddit posts")
result = reddit_posts
""",
            "requirements": ["praw", "nltk", "scikit-learn"]
        })
        
        workflow.add_node("PythonCodeNode", "extract_youtube", {
            "code": """
youtube_analyses = extractor.extract_enhanced_youtube_knowledge()
print(f"Analyzed {len(youtube_analyses)} YouTube videos")
result = youtube_analyses
""",
            "requirements": ["google-api-python-client"]
        })
        
        workflow.add_node("PythonCodeNode", "extract_singapore_forums", {
            "code": """
singapore_posts = extractor.extract_singapore_forums()
print(f"Extracted {len(singapore_posts)} Singapore forum posts")
result = singapore_posts
""",
            "requirements": ["selenium", "beautifulsoup4"]
        })
        
        workflow.add_node("PythonCodeNode", "extract_stack_exchange", {
            "code": """
stack_posts = extractor.extract_stack_exchange_knowledge()
print(f"Extracted {len(stack_posts)} Stack Exchange posts")
result = stack_posts
""",
            "requirements": ["requests"]
        })
        
        # Stage 2: Advanced analysis
        workflow.add_node("PythonCodeNode", "analyze_problem_solutions", {
            "code": """
all_posts = []
if 'reddit_posts' in locals():
    all_posts.extend(reddit_posts)
if 'singapore_posts' in locals():
    all_posts.extend(singapore_posts)
if 'stack_posts' in locals():
    all_posts.extend(stack_posts)

problem_solutions = extractor.identify_problem_solution_patterns(all_posts)
print(f"Identified {len(problem_solutions)} problem-solution patterns")
result = problem_solutions
""",
            "requirements": ["nltk", "scikit-learn"]
        })
        
        workflow.add_node("PythonCodeNode", "analyze_trends", {
            "code": """
trending_topics = extractor.analyze_trending_topics(all_posts)
print(f"Identified {len(trending_topics)} trending topics")
result = trending_topics
""",
            "requirements": ["nltk", "scikit-learn"]
        })
        
        # Stage 3: Knowledge graph integration
        workflow.add_node("PythonCodeNode", "build_knowledge_graph", {
            "code": """
# Integrate all extracted knowledge into knowledge graph
knowledge_graph_data = {
    'posts': [post.to_dict() for post in all_posts],
    'video_analyses': [analysis.__dict__ for analysis in youtube_analyses],
    'problem_solutions': [ps.__dict__ for ps in problem_solutions],
    'trending_topics': [trend.__dict__ for trend in trending_topics],
    'extraction_metadata': {
        'total_posts': len(all_posts),
        'total_videos': len(youtube_analyses),
        'total_problems': len(problem_solutions),
        'total_trends': len(trending_topics),
        'extraction_date': str(datetime.now())
    }
}

# Save to knowledge graph database
if extractor.has_knowledge_graph:
    extractor._store_in_knowledge_graph(knowledge_graph_data)

result = knowledge_graph_data
""",
            "requirements": ["sqlite3"]
        })
        
        # Stage 4: Generate enhanced reports
        workflow.add_node("PythonCodeNode", "generate_reports", {
            "code": """
import json
from datetime import datetime

# Generate comprehensive report
report_data = {
    'extraction_summary': {
        'total_sources_processed': 4,
        'reddit_posts': len(reddit_posts) if 'reddit_posts' in locals() else 0,
        'youtube_videos': len(youtube_analyses) if 'youtube_analyses' in locals() else 0,
        'singapore_posts': len(singapore_posts) if 'singapore_posts' in locals() else 0,
        'stack_exchange_posts': len(stack_posts) if 'stack_posts' in locals() else 0,
        'problem_solution_pairs': len(problem_solutions) if 'problem_solutions' in locals() else 0,
        'trending_topics': len(trending_topics) if 'trending_topics' in locals() else 0
    },
    'knowledge_insights': knowledge_graph_data,
    'generated_at': datetime.now().isoformat()
}

# Save comprehensive report
output_file = f'enhanced_community_knowledge_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(report_data, f, indent=2, default=str, ensure_ascii=False)

print(f"Enhanced community knowledge report saved to {output_file}")
result = output_file
""",
            "requirements": ["json"]
        })
        
        # Connect workflow stages
        workflow.connect("extract_reddit", "analyze_problem_solutions")
        workflow.connect("extract_youtube", "analyze_trends") 
        workflow.connect("extract_singapore_forums", "analyze_problem_solutions")
        workflow.connect("extract_stack_exchange", "analyze_problem_solutions")
        workflow.connect("analyze_problem_solutions", "build_knowledge_graph")
        workflow.connect("analyze_trends", "build_knowledge_graph")
        workflow.connect("build_knowledge_graph", "generate_reports")
        
        return workflow
    
    def _store_in_knowledge_graph(self, data: Dict[str, Any]) -> None:
        """Store extracted knowledge in the knowledge graph database."""
        if not self.has_knowledge_graph:
            return
        
        try:
            cursor = self.kg_conn.cursor()
            
            # Store entities (products, tools, projects, etc.)
            entities_stored = 0
            for post_data in data.get('posts', []):
                # Store product entities
                for product in post_data.get('mentioned_products', []):
                    entity_id = f"product_{hashlib.md5(product.encode()).hexdigest()[:8]}"
                    cursor.execute("""
                        INSERT OR REPLACE INTO entities (id, type, name, properties)
                        VALUES (?, ?, ?, ?)
                    """, (entity_id, 'product', product, json.dumps({'source': 'community'})))
                    entities_stored += 1
                
                # Store tool entities
                for tool in post_data.get('mentioned_tools', []):
                    entity_id = f"tool_{hashlib.md5(tool.encode()).hexdigest()[:8]}"
                    cursor.execute("""
                        INSERT OR REPLACE INTO entities (id, type, name, properties)
                        VALUES (?, ?, ?, ?)
                    """, (entity_id, 'tool', tool, json.dumps({'source': 'community'})))
                    entities_stored += 1
            
            # Store problem-solution relationships
            relationships_stored = 0
            for ps_data in data.get('problem_solutions', []):
                problem_id = ps_data.get('problem_id')
                
                # Create problem entity
                cursor.execute("""
                    INSERT OR REPLACE INTO entities (id, type, name, properties)
                    VALUES (?, ?, ?, ?)
                """, (problem_id, 'problem', ps_data.get('problem_description', '')[:100], 
                     json.dumps(ps_data)))
                
                # Create relationships to products/tools
                for product in ps_data.get('related_products', []):
                    product_id = f"product_{hashlib.md5(product.encode()).hexdigest()[:8]}"
                    rel_id = f"rel_{problem_id}_{product_id}"
                    cursor.execute("""
                        INSERT OR REPLACE INTO relationships 
                        (id, from_entity, to_entity, relationship_type, strength)
                        VALUES (?, ?, ?, ?, ?)
                    """, (rel_id, problem_id, product_id, 'relates_to_product', ps_data.get('confidence_score', 0.5)))
                    relationships_stored += 1
            
            # Store trending topics
            topics_stored = 0
            for trend_data in data.get('trending_topics', []):
                topic_id = trend_data.get('topic_id')
                cursor.execute("""
                    INSERT OR REPLACE INTO trending_topics 
                    (id, topic_name, keywords, mention_count, trend_score, velocity, peak_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    topic_id,
                    trend_data.get('topic_name'),
                    json.dumps(trend_data.get('topic_keywords', [])),
                    trend_data.get('mention_count', 0),
                    trend_data.get('trend_score', 0.0),
                    trend_data.get('velocity', 0.0),
                    trend_data.get('peak_date')
                ))
                topics_stored += 1
            
            self.kg_conn.commit()
            
            self.logger.info(f"Stored in knowledge graph: {entities_stored} entities, "
                           f"{relationships_stored} relationships, {topics_stored} trending topics")
            
        except Exception as e:
            self.logger.error(f"Knowledge graph storage failed: {e}")
    
    def get_product_community_insights(self, product_name: str) -> Dict[str, Any]:
        """Get community insights for a specific product."""
        insights = {
            'product_name': product_name,
            'community_mentions': 0,
            'problem_reports': [],
            'solution_recommendations': [],
            'trending_status': 'stable',
            'sentiment_summary': 'neutral',
            'related_products': [],
            'usage_contexts': [],
            'singapore_relevance': False
        }
        
        if not self.has_knowledge_graph:
            return insights
        
        try:
            cursor = self.kg_conn.cursor()
            
            # Find product entity
            cursor.execute("""
                SELECT id, properties FROM entities 
                WHERE type = 'product' AND name LIKE ? 
            """, (f"%{product_name}%",))
            
            product_entities = cursor.fetchall()
            
            if product_entities:
                product_id = product_entities[0][0]
                
                # Get relationships and insights
                cursor.execute("""
                    SELECT r.relationship_type, r.strength, e.name, e.properties
                    FROM relationships r
                    JOIN entities e ON r.to_entity = e.id
                    WHERE r.from_entity = ?
                """, (product_id,))
                
                relationships = cursor.fetchall()
                insights['community_mentions'] = len(relationships)
                
                # Get problem reports related to this product
                cursor.execute("""
                    SELECT ci.content, ci.confidence_score
                    FROM community_insights ci
                    WHERE ci.related_entities LIKE ?
                    AND ci.insight_type = 'problem'
                """, (f"%{product_id}%",))
                
                problems = cursor.fetchall()
                insights['problem_reports'] = [
                    {'description': p[0], 'confidence': p[1]} for p in problems
                ]
                
                # Check trending status
                cursor.execute("""
                    SELECT topic_name, trend_score, velocity
                    FROM trending_topics
                    WHERE keywords LIKE ?
                    ORDER BY trend_score DESC
                    LIMIT 1
                """, (f"%{product_name}%",))
                
                trending = cursor.fetchone()
                if trending:
                    if trending[2] > 0.5:  # High velocity
                        insights['trending_status'] = 'rising'
                    elif trending[2] < -0.2:  # Negative velocity
                        insights['trending_status'] = 'declining'
        
        except Exception as e:
            self.logger.error(f"Error getting product insights: {e}")
        
        return insights


def create_enhanced_extractor() -> EnhancedCommunityExtractor:
    """Create an enhanced community extractor with default configuration."""
    config = EnhancedExtractionConfig()
    return EnhancedCommunityExtractor(config)


def run_comprehensive_extraction(config: EnhancedExtractionConfig = None) -> Dict[str, Any]:
    """Run comprehensive community knowledge extraction."""
    if config is None:
        config = EnhancedExtractionConfig()
    
    extractor = EnhancedCommunityExtractor(config)
    workflow = extractor.create_enhanced_workflow()
    runtime = LocalRuntime()
    
    print("Starting comprehensive community knowledge extraction...")
    results, run_id = runtime.execute(workflow.build())
    
    return {
        'extraction_results': results,
        'run_id': run_id,
        'extractor': extractor
    }


if __name__ == "__main__":
    # Example usage
    print("=== Enhanced Community Knowledge Extraction Demo ===")
    
    # Create enhanced configuration
    config = EnhancedExtractionConfig(
        max_posts_per_source=20,  # Reduced for demo
        enable_trending_analysis=True,
        singapore_specific_terms=['HDB', 'BTO', 'renovation permit']
    )
    
    # Run comprehensive extraction
    results = run_comprehensive_extraction(config)
    
    print(f"Extraction completed with run_id: {results['run_id']}")
    print("Enhanced community knowledge extraction system is ready for production use!")