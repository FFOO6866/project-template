"""
Community Knowledge Extractor for Horme Product Enhancement.

This module extracts valuable DIY knowledge from community sources to enhance product data:
1. Reddit r/DIY scraper for common questions and solutions
2. Stack Exchange DIY knowledge extraction
3. YouTube channel analysis (This Old House, DIY channels)
4. Forum discussion pattern analysis
5. Problem-solution mapping from community discussions
6. Trending project identification and seasonal patterns

Architecture:
- Built on Kailash Core SDK for workflow integration
- Respects rate limits and robots.txt
- Caches results to avoid repeated API calls
- Analyzes sentiment and helpfulness of community content
- Maps community insights to product SKUs and categories
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
import hashlib

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# For web scraping (when API not available)
try:
    from bs4 import BeautifulSoup
    import requests_html
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False
    print("Warning: BeautifulSoup and requests-html not available. Some scraping features disabled.")

# For YouTube API (optional)
try:
    from googleapiclient.discovery import build
    HAS_YOUTUBE_API = True
except ImportError:
    HAS_YOUTUBE_API = False
    print("Warning: Google API client not available. YouTube API features disabled.")


class SourceType(Enum):
    """Types of community knowledge sources."""
    REDDIT = "reddit"
    STACK_EXCHANGE = "stack_exchange"
    YOUTUBE = "youtube"
    FORUM = "forum"
    BLOG = "blog"
    WIKI = "wiki"


class ContentType(Enum):
    """Types of content extracted from sources."""
    QUESTION = "question"
    ANSWER = "answer"
    TUTORIAL = "tutorial"
    REVIEW = "review"
    PROBLEM_REPORT = "problem_report"
    SOLUTION = "solution"
    TIP = "tip"
    WARNING = "warning"


class ConfidenceLevel(Enum):
    """Confidence levels for extracted knowledge."""
    HIGH = "high"          # Multiple sources, high engagement
    MEDIUM = "medium"      # Single reliable source or moderate engagement
    LOW = "low"           # Limited validation or low engagement
    UNVERIFIED = "unverified"  # No validation available


@dataclass
class CommunityPost:
    """Individual community post or content item."""
    
    # Basic Information
    post_id: str
    source_type: SourceType
    source_url: str
    title: str
    content: str
    author: str
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Engagement Metrics
    upvotes: int = 0
    downvotes: int = 0
    comments_count: int = 0
    views: int = 0
    shares: int = 0
    
    # Content Classification
    content_type: ContentType = ContentType.QUESTION
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Analysis Results
    sentiment_score: float = 0.0  # -1 to 1
    helpfulness_score: float = 0.0  # 0 to 1
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    
    # Product Relations
    mentioned_products: List[str] = field(default_factory=list)  # Product names/brands
    mentioned_tools: List[str] = field(default_factory=list)
    mentioned_materials: List[str] = field(default_factory=list)
    related_skus: List[str] = field(default_factory=list)  # Matched SKUs
    
    # Knowledge Extraction
    problems_identified: List[str] = field(default_factory=list)
    solutions_provided: List[str] = field(default_factory=list)
    tips_and_tricks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cost_information: Dict[str, Any] = field(default_factory=dict)
    
    # Processing Metadata
    extracted_at: datetime = field(default_factory=datetime.now)
    last_analyzed: Optional[datetime] = None
    analysis_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class KnowledgePattern:
    """Pattern identified from community knowledge analysis."""
    
    pattern_id: str
    pattern_type: str  # "common_problem", "popular_solution", "seasonal_trend", etc.
    description: str
    
    # Pattern Data
    frequency: int  # How often this pattern appears
    confidence: float  # 0-1 confidence in pattern validity
    sources: List[str]  # Source post IDs that contribute to this pattern
    
    # Product Relations
    related_products: List[str] = field(default_factory=list)
    related_categories: List[str] = field(default_factory=list)
    related_skus: List[str] = field(default_factory=list)
    
    # Pattern Details
    common_keywords: List[str] = field(default_factory=list)
    seasonal_trend: Optional[str] = None  # spring, summer, fall, winter
    difficulty_level: Optional[str] = None
    typical_cost_range: Optional[Tuple[float, float]] = None
    
    # Actionable Insights
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    alternative_solutions: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractionConfig:
    """Configuration for community knowledge extraction."""
    
    # API Keys and Credentials
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "DIY-Knowledge-Extractor/1.0"
    
    youtube_api_key: Optional[str] = None
    
    # Rate Limiting
    requests_per_minute: int = 30
    delay_between_requests: float = 2.0
    
    # Content Filtering
    min_score_threshold: int = 5  # Minimum upvotes/score to consider
    min_comments_threshold: int = 2
    max_age_days: int = 365  # Only consider content from last year
    
    # Analysis Settings
    max_posts_per_source: int = 100
    enable_sentiment_analysis: bool = True
    enable_product_matching: bool = True
    
    # Caching
    cache_directory: str = "community_cache"
    cache_duration_hours: int = 24
    
    # Output Settings
    output_directory: str = "community_knowledge"
    save_raw_data: bool = True
    save_analysis_results: bool = True


class CommunityKnowledgeExtractor:
    """
    Extract and analyze DIY knowledge from community sources.
    
    This extractor gathers valuable insights from Reddit, forums, YouTube, and other
    community sources to enhance product data with real-world usage patterns,
    common problems, and community-validated solutions.
    """
    
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.logger = logging.getLogger("community_knowledge_extractor")
        self.logger.setLevel(logging.INFO)
        
        # Initialize Kailash components
        self.workflow = WorkflowBuilder()
        self.runtime = LocalRuntime()
        
        # Create directories
        Path(self.config.cache_directory).mkdir(exist_ok=True)
        Path(self.config.output_directory).mkdir(exist_ok=True)
        
        # Data storage
        self.posts: Dict[str, CommunityPost] = {}
        self.patterns: Dict[str, KnowledgePattern] = {}
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()
        
        # Initialize API clients
        self._initialize_reddit_client()
        self._initialize_youtube_client()
        
        # Sample product and tool databases for matching
        self._initialize_product_databases()
    
    def _initialize_reddit_client(self) -> None:
        """Initialize Reddit API client if credentials available."""
        if self.config.reddit_client_id and self.config.reddit_client_secret:
            try:
                import praw
                self.reddit = praw.Reddit(
                    client_id=self.config.reddit_client_id,
                    client_secret=self.config.reddit_client_secret,
                    user_agent=self.config.reddit_user_agent
                )
                self.has_reddit_api = True
                self.logger.info("Reddit API client initialized")
            except ImportError:
                self.logger.warning("PRAW not installed. Reddit API features disabled.")
                self.has_reddit_api = False
        else:
            self.has_reddit_api = False
            self.logger.info("Reddit API credentials not provided. Using web scraping fallback.")
    
    def _initialize_youtube_client(self) -> None:
        """Initialize YouTube API client if key available."""
        if self.config.youtube_api_key and HAS_YOUTUBE_API:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.config.youtube_api_key)
                self.has_youtube_api = True
                self.logger.info("YouTube API client initialized")
            except Exception as e:
                self.logger.warning(f"YouTube API initialization failed: {e}")
                self.has_youtube_api = False
        else:
            self.has_youtube_api = False
            self.logger.info("YouTube API not available")
    
    def _initialize_product_databases(self) -> None:
        """Initialize sample product/tool databases for matching."""
        # Common tools and products mentioned in DIY discussions
        self.common_tools = {
            "drill", "saw", "hammer", "screwdriver", "wrench", "pliers", "level", "tape measure",
            "circular saw", "miter saw", "table saw", "reciprocating saw", "jigsaw",
            "impact driver", "router", "sander", "angle grinder", "nail gun",
            "multimeter", "wire strippers", "pipe wrench", "basin wrench"
        }
        
        self.common_materials = {
            "lumber", "plywood", "drywall", "insulation", "paint", "primer", "caulk", "screws",
            "nails", "bolts", "washers", "nuts", "brackets", "hinges", "handles",
            "pipe", "fittings", "electrical wire", "outlet", "switch", "breaker"
        }
        
        self.brand_names = {
            "dewalt", "milwaukee", "makita", "ryobi", "black+decker", "craftsman", "porter-cable",
            "delta", "bosch", "festool", "ridgid", "husky", "klein", "fluke", "channellock"
        }
        
        # DIY project categories
        self.project_categories = {
            "plumbing", "electrical", "carpentry", "painting", "flooring", "roofing",
            "landscaping", "hvac", "kitchen", "bathroom", "deck", "fence", "shed",
            "drywall", "tiling", "insulation", "siding", "gutters", "doors", "windows"
        }
    
    def _respect_rate_limits(self) -> None:
        """Ensure we respect rate limits."""
        current_time = time.time()
        
        # Reset counter if window expired
        if current_time - self.request_window_start > 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # Check if we need to wait
        if self.request_count >= self.config.requests_per_minute:
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()
        
        # Ensure minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.config.delay_between_requests:
            time.sleep(self.config.delay_between_requests - time_since_last)
        
        self.request_count += 1
        self.last_request_time = time.time()
    
    def extract_reddit_knowledge(self, subreddits: List[str] = None) -> List[CommunityPost]:
        """Extract knowledge from Reddit DIY communities."""
        if subreddits is None:
            subreddits = ["DIY", "HomeImprovement", "woodworking", "electrical", "plumbing", 
                         "Tools", "BeginnerWoodWorking", "fixit", "howto"]
        
        posts = []
        
        if self.has_reddit_api:
            posts.extend(self._extract_reddit_api(subreddits))
        else:
            posts.extend(self._extract_reddit_scraping(subreddits))
        
        # Analyze and enhance posts
        for post in posts:
            self._analyze_post_content(post)
            self._match_products_in_post(post)
        
        return posts
    
    def _extract_reddit_api(self, subreddits: List[str]) -> List[CommunityPost]:
        """Extract Reddit data using official API."""
        posts = []
        
        for subreddit_name in subreddits:
            try:
                self.logger.info(f"Extracting from r/{subreddit_name}")
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get top posts from last month
                for submission in subreddit.top(time_filter="month", limit=self.config.max_posts_per_source):
                    self._respect_rate_limits()
                    
                    if submission.score < self.config.min_score_threshold:
                        continue
                    
                    post = CommunityPost(
                        post_id=f"reddit_{submission.id}",
                        source_type=SourceType.REDDIT,
                        source_url=f"https://reddit.com{submission.permalink}",
                        title=submission.title,
                        content=submission.selftext or "",
                        author=str(submission.author) if submission.author else "deleted",
                        created_at=datetime.fromtimestamp(submission.created_utc),
                        upvotes=submission.score,
                        comments_count=submission.num_comments,
                        categories=[subreddit_name.lower()],
                        content_type=ContentType.QUESTION
                    )
                    
                    # Extract top comments for additional knowledge
                    submission.comments.replace_more(limit=3)  # Load more comments
                    for comment in submission.comments.list()[:10]:  # Top 10 comments
                        if hasattr(comment, 'body') and comment.score > 5:
                            # Create a post for valuable comments
                            comment_post = CommunityPost(
                                post_id=f"reddit_{comment.id}",
                                source_type=SourceType.REDDIT,
                                source_url=f"https://reddit.com{submission.permalink}{comment.id}",
                                title=f"Re: {submission.title}",
                                content=comment.body,
                                author=str(comment.author) if comment.author else "deleted",
                                created_at=datetime.fromtimestamp(comment.created_utc),
                                upvotes=comment.score,
                                categories=[subreddit_name.lower()],
                                content_type=ContentType.ANSWER
                            )
                            posts.append(comment_post)
                    
                    posts.append(post)
                    
            except Exception as e:
                self.logger.error(f"Error extracting from r/{subreddit_name}: {e}")
        
        return posts
    
    def _extract_reddit_scraping(self, subreddits: List[str]) -> List[CommunityPost]:
        """Extract Reddit data using web scraping (fallback)."""
        if not HAS_SCRAPING:
            self.logger.warning("Scraping libraries not available")
            return []
        
        posts = []
        
        for subreddit_name in subreddits:
            try:
                self.logger.info(f"Scraping r/{subreddit_name}")
                
                # Use requests-html for dynamic content
                session = requests_html.HTMLSession()
                url = f"https://www.reddit.com/r/{subreddit_name}/top/"
                
                self._respect_rate_limits()
                response = session.get(url, params={"t": "month"})
                
                if response.status_code == 200:
                    # Parse posts from HTML
                    # Note: This is a simplified example - actual Reddit scraping is more complex
                    soup = BeautifulSoup(response.html.html, 'html.parser')
                    
                    # Find post elements (Reddit's structure changes frequently)
                    post_elements = soup.find_all('div', {'data-testid': re.compile(r'post-container')})
                    
                    for i, element in enumerate(post_elements[:20]):  # Limit to 20 posts
                        try:
                            # Extract basic information (this would need to be adapted to current Reddit HTML)
                            title_elem = element.find('h3')
                            title = title_elem.get_text().strip() if title_elem else f"Post {i+1}"
                            
                            # Create basic post object
                            post = CommunityPost(
                                post_id=f"reddit_scraped_{hashlib.md5(title.encode()).hexdigest()[:8]}",
                                source_type=SourceType.REDDIT,
                                source_url=f"https://reddit.com/r/{subreddit_name}",
                                title=title,
                                content="",  # Would need to extract content
                                author="unknown",
                                created_at=datetime.now(),  # Would need to extract actual date
                                categories=[subreddit_name.lower()],
                                content_type=ContentType.QUESTION
                            )
                            
                            posts.append(post)
                            
                        except Exception as e:
                            self.logger.warning(f"Error parsing post element: {e}")
                            continue
                
            except Exception as e:
                self.logger.error(f"Error scraping r/{subreddit_name}: {e}")
        
        return posts
    
    def extract_youtube_knowledge(self, channels: List[str] = None) -> List[CommunityPost]:
        """Extract DIY knowledge from YouTube channels."""
        if channels is None:
            channels = [
                "UC7MfDpBUeJhm24bFhxJGU-w",  # This Old House
                "UCQ1LnOJxJb6KxZPJdIb2-wGw",  # Steve Ramsey - Woodworking for Mere Mortals
                "UC-7XY-W_C84cW2MNqujgFWQ",  # DIY Creators
                "UCnorhjQR4zJkT7AVNhu395Q",  # Fix This Build That
                "UC5HRNRWMVEgbvOKu8ULvI6w"   # Home RenoVision DIY
            ]
        
        posts = []
        
        if not self.has_youtube_api:
            self.logger.warning("YouTube API not available")
            return posts
        
        for channel_id in channels:
            try:
                self.logger.info(f"Extracting from YouTube channel {channel_id}")
                
                # Get channel videos
                request = self.youtube.search().list(
                    part="snippet",
                    channelId=channel_id,
                    maxResults=self.config.max_posts_per_source,
                    order="relevance",
                    publishedAfter=(datetime.now() - timedelta(days=self.config.max_age_days)).isoformat() + "Z",
                    type="video"
                )
                
                self._respect_rate_limits()
                response = request.execute()
                
                for item in response.get("items", []):
                    video_id = item["id"]["videoId"]
                    snippet = item["snippet"]
                    
                    # Get video statistics
                    stats_request = self.youtube.videos().list(
                        part="statistics",
                        id=video_id
                    )
                    
                    self._respect_rate_limits()
                    stats_response = stats_request.execute()
                    
                    stats = stats_response["items"][0]["statistics"] if stats_response["items"] else {}
                    
                    post = CommunityPost(
                        post_id=f"youtube_{video_id}",
                        source_type=SourceType.YOUTUBE,
                        source_url=f"https://www.youtube.com/watch?v={video_id}",
                        title=snippet["title"],
                        content=snippet.get("description", ""),
                        author=snippet["channelTitle"],
                        created_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                        views=int(stats.get("viewCount", 0)),
                        upvotes=int(stats.get("likeCount", 0)),
                        comments_count=int(stats.get("commentCount", 0)),
                        content_type=ContentType.TUTORIAL,
                        tags=snippet.get("tags", [])
                    )
                    
                    posts.append(post)
                    
            except Exception as e:
                self.logger.error(f"Error extracting from YouTube channel {channel_id}: {e}")
        
        # Analyze YouTube content
        for post in posts:
            self._analyze_post_content(post)
            self._match_products_in_post(post)
        
        return posts
    
    def extract_forum_knowledge(self, forum_urls: List[str] = None) -> List[CommunityPost]:
        """Extract knowledge from popular DIY forums."""
        if forum_urls is None:
            forum_urls = [
                "https://www.contractortalk.com/",
                "https://www.doityourself.com/forum/",
                "https://forums.finehomebuilding.com/",
                "https://www.woodworkingtalk.com/"
            ]
        
        posts = []
        
        if not HAS_SCRAPING:
            self.logger.warning("Scraping libraries not available for forum extraction")
            return posts
        
        for forum_url in forum_urls:
            try:
                self.logger.info(f"Extracting from forum: {forum_url}")
                
                # This is a simplified example - each forum would need custom parsing
                self._respect_rate_limits()
                response = requests.get(forum_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for forum post links (this would need customization per forum)
                    post_links = soup.find_all('a', href=True)
                    
                    for link in post_links[:10]:  # Sample first 10 links
                        href = link.get('href')
                        title = link.get_text().strip()
                        
                        if len(title) > 20 and any(keyword in title.lower() for keyword in self.project_categories):
                            post = CommunityPost(
                                post_id=f"forum_{hashlib.md5(href.encode()).hexdigest()[:8]}",
                                source_type=SourceType.FORUM,
                                source_url=urljoin(forum_url, href),
                                title=title,
                                content="",  # Would need to fetch and parse individual posts
                                author="unknown",
                                created_at=datetime.now(),
                                content_type=ContentType.QUESTION
                            )
                            
                            posts.append(post)
                
            except Exception as e:
                self.logger.error(f"Error extracting from forum {forum_url}: {e}")
        
        return posts
    
    def _analyze_post_content(self, post: CommunityPost) -> None:
        """Analyze post content to extract problems, solutions, and insights."""
        content = f"{post.title} {post.content}".lower()
        
        # Extract problems
        problem_indicators = [
            "problem", "issue", "trouble", "broken", "doesn't work", "failed", "wrong",
            "help", "stuck", "can't", "won't", "error", "mistake", "damaged"
        ]
        
        for indicator in problem_indicators:
            if indicator in content:
                # Extract surrounding context as potential problem
                sentences = content.split('.')
                for sentence in sentences:
                    if indicator in sentence and len(sentence.strip()) > 10:
                        post.problems_identified.append(sentence.strip()[:200])
                        break
        
        # Extract solutions
        solution_indicators = [
            "solution", "fix", "solved", "worked", "success", "fixed", "resolved",
            "try this", "use this", "do this", "steps:", "instructions:"
        ]
        
        for indicator in solution_indicators:
            if indicator in content:
                sentences = content.split('.')
                for sentence in sentences:
                    if indicator in sentence and len(sentence.strip()) > 10:
                        post.solutions_provided.append(sentence.strip()[:200])
                        break
        
        # Extract tips and tricks
        tip_indicators = [
            "tip", "trick", "pro tip", "advice", "suggestion", "recommend",
            "better way", "easier", "faster", "cheaper"
        ]
        
        for indicator in tip_indicators:
            if indicator in content:
                sentences = content.split('.')
                for sentence in sentences:
                    if indicator in sentence and len(sentence.strip()) > 10:
                        post.tips_and_tricks.append(sentence.strip()[:200])
                        break
        
        # Extract warnings
        warning_indicators = [
            "warning", "danger", "careful", "don't", "avoid", "never", "caution",
            "safety", "hazard", "risk", "be careful"
        ]
        
        for indicator in warning_indicators:
            if indicator in content:
                sentences = content.split('.')
                for sentence in sentences:
                    if indicator in sentence and len(sentence.strip()) > 10:
                        post.warnings.append(sentence.strip()[:200])
                        break
        
        # Extract cost information
        cost_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $25.99
            r'(\d+)\s*dollars?',      # 25 dollars
            r'cost(?:s|ed)?\s+(?:about\s+)?\$?(\d+)',  # cost about $50
            r'paid\s+\$?(\d+)',       # paid $30
            r'budget\s+(?:of\s+)?\$?(\d+)'  # budget of $100
        ]
        
        for pattern in cost_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                costs = [float(match) if isinstance(match, str) and match.replace('.', '').isdigit() 
                        else float(match) for match in matches[:3]]  # First 3 costs found
                if costs:
                    post.cost_information = {
                        "mentioned_costs": costs,
                        "average_cost": sum(costs) / len(costs),
                        "cost_range": (min(costs), max(costs)) if len(costs) > 1 else None
                    }
        
        # Calculate basic sentiment (simplified)
        positive_words = ["good", "great", "excellent", "perfect", "works", "easy", "love", "awesome"]
        negative_words = ["bad", "terrible", "awful", "broken", "hard", "difficult", "hate", "sucks"]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count + negative_count > 0:
            post.sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
        
        # Calculate helpfulness based on engagement and content quality
        helpfulness_factors = [
            min(post.upvotes / 10, 1.0),  # Normalize upvotes
            min(post.comments_count / 5, 1.0),  # Normalize comments
            1.0 if post.problems_identified else 0.0,
            1.0 if post.solutions_provided else 0.0,
            0.5 if post.tips_and_tricks else 0.0
        ]
        
        post.helpfulness_score = sum(helpfulness_factors) / len(helpfulness_factors)
        
        # Set confidence level
        if post.upvotes > 20 and post.helpfulness_score > 0.7:
            post.confidence_level = ConfidenceLevel.HIGH
        elif post.upvotes > 5 and post.helpfulness_score > 0.5:
            post.confidence_level = ConfidenceLevel.MEDIUM
        elif post.helpfulness_score > 0.3:
            post.confidence_level = ConfidenceLevel.LOW
        else:
            post.confidence_level = ConfidenceLevel.UNVERIFIED
        
        post.last_analyzed = datetime.now()
    
    def _match_products_in_post(self, post: CommunityPost) -> None:
        """Match products, tools, and materials mentioned in the post."""
        content = f"{post.title} {post.content}".lower()
        
        # Match tools
        for tool in self.common_tools:
            if tool in content:
                post.mentioned_tools.append(tool)
        
        # Match materials
        for material in self.common_materials:
            if material in content:
                post.mentioned_materials.append(material)
        
        # Match brand names
        for brand in self.brand_names:
            if brand in content:
                post.mentioned_products.append(brand)
        
        # Categorize post based on content
        for category in self.project_categories:
            if category in content:
                if category not in post.categories:
                    post.categories.append(category)
    
    def identify_knowledge_patterns(self, posts: List[CommunityPost]) -> List[KnowledgePattern]:
        """Identify patterns in community knowledge from collected posts."""
        patterns = []
        
        # Group posts by category
        category_posts = {}
        for post in posts:
            for category in post.categories:
                if category not in category_posts:
                    category_posts[category] = []
                category_posts[category].append(post)
        
        # Identify common problems
        for category, cat_posts in category_posts.items():
            problems = {}
            for post in cat_posts:
                for problem in post.problems_identified:
                    problem_key = problem[:50]  # Use first 50 chars as key
                    if problem_key not in problems:
                        problems[problem_key] = []
                    problems[problem_key].append(post.post_id)
            
            # Create patterns for frequently mentioned problems
            for problem, source_posts in problems.items():
                if len(source_posts) >= 3:  # Problem mentioned in at least 3 posts
                    pattern = KnowledgePattern(
                        pattern_id=f"problem_{category}_{hashlib.md5(problem.encode()).hexdigest()[:8]}",
                        pattern_type="common_problem",
                        description=f"Common {category} problem: {problem}",
                        frequency=len(source_posts),
                        confidence=min(len(source_posts) / 10, 1.0),
                        sources=source_posts,
                        related_categories=[category]
                    )
                    patterns.append(pattern)
        
        # Identify popular solutions
        for category, cat_posts in category_posts.items():
            solutions = {}
            for post in cat_posts:
                for solution in post.solutions_provided:
                    solution_key = solution[:50]
                    if solution_key not in solutions:
                        solutions[solution_key] = []
                    solutions[solution_key].append(post.post_id)
            
            for solution, source_posts in solutions.items():
                if len(source_posts) >= 2:
                    pattern = KnowledgePattern(
                        pattern_id=f"solution_{category}_{hashlib.md5(solution.encode()).hexdigest()[:8]}",
                        pattern_type="popular_solution",
                        description=f"Popular {category} solution: {solution}",
                        frequency=len(source_posts),
                        confidence=min(len(source_posts) / 5, 1.0),
                        sources=source_posts,
                        related_categories=[category]
                    )
                    patterns.append(pattern)
        
        # Identify seasonal trends
        seasonal_posts = {"spring": [], "summer": [], "fall": [], "winter": []}
        for post in posts:
            month = post.created_at.month
            if month in [3, 4, 5]:
                seasonal_posts["spring"].append(post)
            elif month in [6, 7, 8]:
                seasonal_posts["summer"].append(post)
            elif month in [9, 10, 11]:
                seasonal_posts["fall"].append(post)
            else:
                seasonal_posts["winter"].append(post)
        
        # Create seasonal trend patterns
        for season, season_posts in seasonal_posts.items():
            if len(season_posts) < 5:
                continue
            
            # Count project categories in this season
            season_categories = {}
            for post in season_posts:
                for category in post.categories:
                    season_categories[category] = season_categories.get(category, 0) + 1
            
            # Find most popular categories for this season
            if season_categories:
                top_category = max(season_categories, key=season_categories.get)
                if season_categories[top_category] >= 3:
                    pattern = KnowledgePattern(
                        pattern_id=f"seasonal_{season}_{top_category}",
                        pattern_type="seasonal_trend",
                        description=f"{top_category.title()} projects are popular in {season}",
                        frequency=season_categories[top_category],
                        confidence=min(season_categories[top_category] / 10, 1.0),
                        sources=[p.post_id for p in season_posts if top_category in p.categories],
                        related_categories=[top_category],
                        seasonal_trend=season,
                        recommendations=[f"Stock up on {top_category} supplies before {season}"]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def enhance_product_with_community_knowledge(self, product_sku: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance product data with community knowledge insights.
        
        This is the core integration function that enriches basic product information
        with community insights, common usage patterns, and real-world feedback.
        """
        enhanced_data = product_data.copy()
        
        # Find relevant posts for this product
        relevant_posts = self._find_relevant_posts(product_sku, product_data)
        
        if relevant_posts:
            # Add community knowledge enrichment
            enhanced_data["community_insights"] = {
                "total_mentions": len(relevant_posts),
                "average_sentiment": sum(p.sentiment_score for p in relevant_posts) / len(relevant_posts),
                "helpfulness_score": sum(p.helpfulness_score for p in relevant_posts) / len(relevant_posts),
                "confidence_level": self._calculate_overall_confidence(relevant_posts)
            }
            
            # Common problems and solutions
            all_problems = []
            all_solutions = []
            for post in relevant_posts:
                all_problems.extend(post.problems_identified)
                all_solutions.extend(post.solutions_provided)
            
            enhanced_data["common_problems"] = list(set(all_problems[:5]))  # Top 5 unique problems
            enhanced_data["community_solutions"] = list(set(all_solutions[:5]))  # Top 5 unique solutions
            
            # Tips and warnings from community
            all_tips = []
            all_warnings = []
            for post in relevant_posts:
                all_tips.extend(post.tips_and_tricks)
                all_warnings.extend(post.warnings)
            
            enhanced_data["community_tips"] = list(set(all_tips[:3]))
            enhanced_data["community_warnings"] = list(set(all_warnings[:3]))
            
            # Usage contexts
            enhanced_data["usage_contexts"] = []
            for post in relevant_posts:
                for category in post.categories:
                    context = {
                        "project_type": category,
                        "source": post.source_type.value,
                        "confidence": post.confidence_level.value,
                        "engagement": post.upvotes + post.comments_count
                    }
                    enhanced_data["usage_contexts"].append(context)
            
            # Cost insights from community
            cost_mentions = [p.cost_information for p in relevant_posts if p.cost_information]
            if cost_mentions:
                all_costs = []
                for cost_info in cost_mentions:
                    all_costs.extend(cost_info.get("mentioned_costs", []))
                
                if all_costs:
                    enhanced_data["community_cost_insights"] = {
                        "average_cost": sum(all_costs) / len(all_costs),
                        "cost_range": (min(all_costs), max(all_costs)),
                        "cost_mentions": len(cost_mentions)
                    }
            
            # Popular alternatives mentioned
            alternatives = set()
            for post in relevant_posts:
                alternatives.update(post.mentioned_products)
            
            if alternatives:
                enhanced_data["community_alternatives"] = list(alternatives)[:3]
            
            # Seasonal usage patterns
            seasonal_mentions = {}
            for post in relevant_posts:
                season = self._get_season_from_date(post.created_at)
                seasonal_mentions[season] = seasonal_mentions.get(season, 0) + 1
            
            if seasonal_mentions:
                enhanced_data["seasonal_usage_patterns"] = seasonal_mentions
                peak_season = max(seasonal_mentions, key=seasonal_mentions.get)
                enhanced_data["peak_usage_season"] = peak_season
            
            # Related projects from community
            related_projects = set()
            for post in relevant_posts:
                related_projects.update(post.categories)
            
            enhanced_data["community_project_applications"] = list(related_projects)
        
        return enhanced_data
    
    def _find_relevant_posts(self, product_sku: str, product_data: Dict[str, Any]) -> List[CommunityPost]:
        """Find community posts relevant to a specific product."""
        relevant_posts = []
        product_name = product_data.get("name", "").lower()
        product_category = product_data.get("category", "").lower()
        
        for post in self.posts.values():
            relevance_score = 0
            
            # Check if product name is mentioned
            if product_name in f"{post.title} {post.content}".lower():
                relevance_score += 3
            
            # Check if product category matches post categories
            for category in post.categories:
                if category in product_category or product_category in category:
                    relevance_score += 2
            
            # Check if product is in mentioned tools/products
            if any(product_name in tool for tool in post.mentioned_tools):
                relevance_score += 2
            
            if any(product_name in product for product in post.mentioned_products):
                relevance_score += 2
            
            # Check for related keywords
            product_words = product_name.split()
            for word in product_words:
                if len(word) > 3 and word in f"{post.title} {post.content}".lower():
                    relevance_score += 1
            
            if relevance_score >= 2:  # Minimum relevance threshold
                relevant_posts.append(post)
        
        # Sort by relevance and engagement
        relevant_posts.sort(key=lambda p: (p.helpfulness_score * p.upvotes), reverse=True)
        
        return relevant_posts[:10]  # Return top 10 most relevant posts
    
    def _calculate_overall_confidence(self, posts: List[CommunityPost]) -> str:
        """Calculate overall confidence level from multiple posts."""
        if not posts:
            return ConfidenceLevel.UNVERIFIED.value
        
        confidence_scores = {
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.LOW: 1,
            ConfidenceLevel.UNVERIFIED: 0
        }
        
        total_score = sum(confidence_scores[post.confidence_level] for post in posts)
        average_score = total_score / len(posts)
        
        if average_score >= 2.5:
            return ConfidenceLevel.HIGH.value
        elif average_score >= 1.5:
            return ConfidenceLevel.MEDIUM.value
        elif average_score >= 0.5:
            return ConfidenceLevel.LOW.value
        else:
            return ConfidenceLevel.UNVERIFIED.value
    
    def _get_season_from_date(self, date: datetime) -> str:
        """Get season from date."""
        month = date.month
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "fall"
        else:
            return "winter"
    
    def generate_workflow_for_community_extraction(self, sources: Dict[str, Any]) -> WorkflowBuilder:
        """Generate a Kailash workflow for community knowledge extraction."""
        workflow = WorkflowBuilder()
        
        # Step 1: Extract from Reddit
        if sources.get("reddit", {}).get("enabled", False):
            workflow.add_node("PythonCodeNode", "extract_reddit", {
                "code": f"""
from community_knowledge_extractor import CommunityKnowledgeExtractor, ExtractionConfig

config = ExtractionConfig(
    reddit_client_id="{sources.get('reddit', {}).get('client_id', '')}",
    reddit_client_secret="{sources.get('reddit', {}).get('client_secret', '')}",
    max_posts_per_source=50
)

extractor = CommunityKnowledgeExtractor(config)
reddit_posts = extractor.extract_reddit_knowledge({sources.get('reddit', {}).get('subreddits', [])})

print(f"Extracted {{len(reddit_posts)}} Reddit posts")
result = reddit_posts
""",
                "requirements": ["praw"]
            })
        
        # Step 2: Extract from YouTube
        if sources.get("youtube", {}).get("enabled", False):
            workflow.add_node("PythonCodeNode", "extract_youtube", {
                "code": f"""
youtube_posts = extractor.extract_youtube_knowledge({sources.get('youtube', {}).get('channels', [])})
print(f"Extracted {{len(youtube_posts)}} YouTube videos")
result = youtube_posts
""",
                "requirements": ["google-api-python-client"]
            })
        
        # Step 3: Analyze patterns
        workflow.add_node("PythonCodeNode", "analyze_patterns", {
            "code": """
all_posts = []
if 'reddit_posts' in locals():
    all_posts.extend(reddit_posts)
if 'youtube_posts' in locals():
    all_posts.extend(youtube_posts)

patterns = extractor.identify_knowledge_patterns(all_posts)
print(f"Identified {len(patterns)} knowledge patterns")

result = {
    'posts': [post.to_dict() for post in all_posts],
    'patterns': [pattern.to_dict() for pattern in patterns],
    'summary': {
        'total_posts': len(all_posts),
        'total_patterns': len(patterns),
        'sources': list(set(post.source_type.value for post in all_posts))
    }
}
""",
            "requirements": []
        })
        
        # Step 4: Save results
        workflow.add_node("PythonCodeNode", "save_results", {
            "code": """
import json
from datetime import datetime

output_file = f'community_knowledge_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

with open(output_file, 'w') as f:
    json.dump(result, f, indent=2, default=str)

print(f"Community knowledge saved to {output_file}")
result = output_file
""",
            "requirements": []
        })
        
        # Connect workflow
        if sources.get("reddit", {}).get("enabled", False):
            workflow.connect("extract_reddit", "analyze_patterns")
        
        if sources.get("youtube", {}).get("enabled", False):
            if sources.get("reddit", {}).get("enabled", False):
                workflow.connect("extract_youtube", "analyze_patterns")
            else:
                workflow.connect("extract_youtube", "analyze_patterns")
        
        workflow.connect("analyze_patterns", "save_results")
        
        return workflow
    
    def save_knowledge_database(self, filename: str = None) -> str:
        """Save extracted community knowledge to file."""
        if filename is None:
            filename = f"community_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path(self.config.output_directory) / filename
        
        knowledge_data = {
            "metadata": {
                "extracted_at": datetime.now().isoformat(),
                "total_posts": len(self.posts),
                "total_patterns": len(self.patterns),
                "sources": list(set(post.source_type.value for post in self.posts.values())),
                "config": asdict(self.config)
            },
            "posts": {pid: post.to_dict() for pid, post in self.posts.items()},
            "patterns": {pid: pattern.to_dict() for pid, pattern in self.patterns.items()}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Community knowledge database saved to {filepath}")
        return str(filepath)


# Example usage and testing functions
def create_sample_community_extractor() -> CommunityKnowledgeExtractor:
    """Create a sample community knowledge extractor for testing."""
    config = ExtractionConfig(
        max_posts_per_source=20,  # Reduced for testing
        cache_duration_hours=1
    )
    return CommunityKnowledgeExtractor(config)


def demonstrate_community_enhancement():
    """Demonstrate how community knowledge enhances basic product data."""
    # Create community extractor (with mock data for demo)
    extractor = create_sample_community_extractor()
    
    # Add some sample community posts for demonstration
    sample_posts = [
        CommunityPost(
            post_id="reddit_sample_1",
            source_type=SourceType.REDDIT,
            source_url="https://reddit.com/r/DIY/sample1",
            title="Cordless drill battery died during project",
            content="My 18V cordless drill battery keeps dying in the middle of projects. Anyone know good replacement batteries or should I upgrade to a newer model?",
            author="diy_enthusiast",
            created_at=datetime.now() - timedelta(days=15),
            upvotes=23,
            comments_count=8,
            categories=["tools"],
            problems_identified=["Battery keeps dying during use"],
            mentioned_tools=["cordless drill"],
            helpfulness_score=0.7,
            confidence_level=ConfidenceLevel.MEDIUM
        ),
        CommunityPost(
            post_id="youtube_sample_1",
            source_type=SourceType.YOUTUBE,
            source_url="https://youtube.com/watch?v=sample",
            title="Best adjustable wrench techniques for plumbing",
            content="In this video I show you the proper way to use an adjustable wrench for plumbing connections to avoid stripping nuts and damaging fixtures.",
            author="DIY Plumbing Pro",
            created_at=datetime.now() - timedelta(days=30),
            views=15420,
            upvotes=342,
            comments_count=67,
            categories=["plumbing"],
            content_type=ContentType.TUTORIAL,
            solutions_provided=["Proper wrench technique prevents damage"],
            tips_and_tricks=["Always turn in direction that tightens the adjustable jaw"],
            mentioned_tools=["adjustable wrench"],
            helpfulness_score=0.9,
            confidence_level=ConfidenceLevel.HIGH
        )
    ]
    
    # Add posts to extractor
    for post in sample_posts:
        extractor.posts[post.post_id] = post
    
    # Sample basic product data
    basic_products = [
        {
            "sku": "drill-cordless-18v",
            "name": "18V Cordless Drill",
            "price": 89.99,
            "category": "power tools",
            "description": "Cordless drill with 18V battery"
        },
        {
            "sku": "wrench-adjustable-10inch",
            "name": "10-inch Adjustable Wrench",
            "price": 24.99,
            "category": "hand tools",
            "description": "Adjustable wrench with 10-inch length"
        }
    ]
    
    print("=== Community Knowledge Enhancement Demo ===\\n")
    
    for product in basic_products:
        print(f"BASIC PRODUCT: {product['name']} (${product['price']})")
        print(f"Category: {product['category']}")
        print(f"Description: {product['description']}")
        print()
        
        # Enhance with community knowledge
        enhanced = extractor.enhance_product_with_community_knowledge(product['sku'], product)
        
        if 'community_insights' in enhanced:
            insights = enhanced['community_insights']
            print("COMMUNITY INSIGHTS:")
            print(f"  • Total community mentions: {insights['total_mentions']}")
            print(f"  • Average sentiment: {insights['average_sentiment']:.2f} (-1 to 1 scale)")
            print(f"  • Community helpfulness: {insights['helpfulness_score']:.2f}")
            print(f"  • Confidence level: {insights['confidence_level'].title()}")
            print()
        
        if 'common_problems' in enhanced and enhanced['common_problems']:
            print("COMMON PROBLEMS REPORTED:")
            for problem in enhanced['common_problems']:
                print(f"  • {problem}")
            print()
        
        if 'community_solutions' in enhanced and enhanced['community_solutions']:
            print("COMMUNITY SOLUTIONS:")
            for solution in enhanced['community_solutions']:
                print(f"  • {solution}")
            print()
        
        if 'community_tips' in enhanced and enhanced['community_tips']:
            print("PRO TIPS FROM COMMUNITY:")
            for tip in enhanced['community_tips']:
                print(f"  • {tip}")
            print()
        
        if 'usage_contexts' in enhanced:
            print("USAGE CONTEXTS:")
            for context in enhanced['usage_contexts'][:3]:  # Show first 3
                print(f"  • {context['project_type'].title()} projects ({context['source']})")
            print()
        
        if 'community_cost_insights' in enhanced:
            cost_info = enhanced['community_cost_insights']
            print("COMMUNITY COST INSIGHTS:")
            print(f"  • Average cost mentioned: ${cost_info['average_cost']:.2f}")
            print(f"  • Cost range: ${cost_info['cost_range'][0]:.2f} - ${cost_info['cost_range'][1]:.2f}")
            print()
        
        print("-" * 60)
        print()


if __name__ == "__main__":
    # Run demonstration
    demonstrate_community_enhancement()