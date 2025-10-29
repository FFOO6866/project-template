"""
DIY Content Enrichment System for Horme Hardware Recommendations

This module provides comprehensive content enrichment capabilities by extracting
knowledge from various DIY sources including YouTube tutorials, forums, and
project guides to enhance product recommendations.

Features:
- YouTube tutorial extraction and analysis
- DIY forum knowledge mining (Reddit, DIY forums)
- Project guide integration and parsing
- How-to content mapping to products
- Expert vs beginner content classification
- Safety information extraction
- Tool usage pattern analysis

Components:
- YouTubeEnricher: Extracts tutorial data and maps to products
- ForumKnowledgeMiner: Mines DIY forums for insights
- ProjectGuideParser: Parses structured project guides
- ContentClassifier: Classifies content by skill level and safety
- KnowledgeIntegrator: Integrates all enriched content
"""

import os
import re
import json
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import praw  # Reddit API
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import spacy
from sentence_transformers import SentenceTransformer
import openai
from textstat import flesch_reading_ease
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download required NLTK data
try:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
except:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class YouTubeTutorial:
    """YouTube tutorial data structure"""
    video_id: str
    title: str
    description: str
    channel_name: str
    duration: int  # seconds
    view_count: int
    like_count: int
    published_date: datetime
    transcript: Optional[str] = None
    tools_mentioned: List[str] = None
    materials_mentioned: List[str] = None
    skill_level: str = "intermediate"  # beginner, intermediate, expert
    project_type: str = "general"
    safety_mentions: List[str] = None
    difficulty_score: float = 0.5  # 0-1 scale
    quality_score: float = 0.5  # 0-1 scale based on engagement

@dataclass
class ForumPost:
    """Forum post data structure"""
    post_id: str
    platform: str  # reddit, diychatroom, etc.
    title: str
    content: str
    author: str
    score: int  # upvotes/likes
    comment_count: int
    created_date: datetime
    project_category: str
    tools_mentioned: List[str] = None
    solutions_provided: List[str] = None
    common_mistakes: List[str] = None
    expert_level: bool = False

@dataclass 
class ProjectGuide:
    """Structured project guide data"""
    guide_id: str
    title: str
    description: str
    source_url: str
    steps: List[Dict[str, Any]]  # Step-by-step instructions
    tools_required: List[str]
    materials_required: List[str]
    skill_level: str
    estimated_time: str
    cost_estimate: Optional[Tuple[float, float]] = None
    safety_warnings: List[str] = None
    tips_and_tricks: List[str] = None

@dataclass
class ContentInsight:
    """Enriched content insight"""
    content_type: str  # youtube, forum, guide
    content_id: str
    product_relevance: Dict[str, float]  # product_id -> relevance_score
    skill_insights: Dict[str, float]  # skill -> importance_score
    safety_insights: List[str]
    usage_patterns: Dict[str, Any]  # tool usage patterns
    quality_indicators: Dict[str, float]
    extracted_knowledge: Dict[str, Any]

class YouTubeEnricher:
    """Enriches product knowledge from YouTube DIY tutorials"""
    
    def __init__(self, api_key: str = None):
        """Initialize YouTube enrichment system"""
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if self.api_key:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        else:
            self.youtube = None
            logger.warning("No YouTube API key provided - functionality limited")
            
        # Initialize NLP tools
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found - install with: python -m spacy download en_core_web_sm")
            self.nlp = None
            
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Tool and material patterns for extraction
        self.tool_patterns = [
            r'\b(drill|saw|hammer|screwdriver|wrench|pliers|level|tape measure)\b',
            r'\b(router|sander|grinder|jigsaw|miter saw|circular saw)\b',
            r'\b(cordless|battery|electric|pneumatic|manual)\s+(drill|saw|gun)\b'
        ]
        
        self.material_patterns = [
            r'\b(wood|lumber|plywood|mdf|particle board)\b',
            r'\b(screw|nail|bolt|washer|nut|anchor)\b',
            r'\b(paint|stain|varnish|primer|sealer)\b',
            r'\b(drywall|plaster|concrete|tile|vinyl)\b'
        ]
        
        self.safety_patterns = [
            r'\b(safety|protective|protection)\s+(glasses|goggles|gloves|mask)\b',
            r'\b(ear\s+protection|hearing\s+protection|respirator)\b',
            r'\bALWAYS\s+(wear|use|check|ensure)\b',
            r'\bNEVER\s+(forget|skip|ignore)\b'
        ]
        
    def search_tutorials(self, query: str, max_results: int = 25) -> List[YouTubeTutorial]:
        """Search for DIY tutorials on YouTube"""
        if not self.youtube:
            logger.error("YouTube API not available")
            return []
            
        try:
            # Search for videos
            search_response = self.youtube.search().list(
                q=f"{query} DIY tutorial how to",
                part='snippet',
                type='video',
                maxResults=max_results,
                order='relevance',
                videoDuration='medium',  # 4-20 minutes
                videoDefinition='any'
            ).execute()
            
            tutorials = []
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get detailed video statistics
            videos_response = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            # Combine search results with statistics
            for i, item in enumerate(search_response['items']):
                video_stats = videos_response['items'][i]['statistics'] if i < len(videos_response['items']) else {}
                content_details = videos_response['items'][i]['contentDetails'] if i < len(videos_response['items']) else {}
                
                tutorial = YouTubeTutorial(
                    video_id=item['id']['videoId'],
                    title=item['snippet']['title'],
                    description=item['snippet']['description'],
                    channel_name=item['snippet']['channelTitle'],
                    duration=self._parse_duration(content_details.get('duration', 'PT0S')),
                    view_count=int(video_stats.get('viewCount', 0)),
                    like_count=int(video_stats.get('likeCount', 0)),
                    published_date=datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00'))
                )
                
                tutorials.append(tutorial)
                
            return tutorials
            
        except Exception as e:
            logger.error(f"Failed to search YouTube tutorials: {e}")
            return []
            
    def enrich_tutorial(self, tutorial: YouTubeTutorial) -> YouTubeTutorial:
        """Enrich tutorial with extracted knowledge"""
        
        # Get transcript
        tutorial.transcript = self._get_transcript(tutorial.video_id)
        
        # Extract tools and materials
        full_text = f"{tutorial.title} {tutorial.description} {tutorial.transcript or ''}"
        tutorial.tools_mentioned = self._extract_tools(full_text)
        tutorial.materials_mentioned = self._extract_materials(full_text)
        tutorial.safety_mentions = self._extract_safety_info(full_text)
        
        # Classify skill level
        tutorial.skill_level = self._classify_skill_level(full_text)
        
        # Classify project type
        tutorial.project_type = self._classify_project_type(tutorial.title, tutorial.description)
        
        # Calculate difficulty score
        tutorial.difficulty_score = self._calculate_difficulty_score(tutorial)
        
        # Calculate quality score
        tutorial.quality_score = self._calculate_quality_score(tutorial)
        
        return tutorial
        
    def _get_transcript(self, video_id: str) -> Optional[str]:
        """Get video transcript using YouTube Transcript API"""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = ' '.join([entry['text'] for entry in transcript_list])
            return transcript
        except Exception as e:
            logger.debug(f"No transcript available for video {video_id}: {e}")
            return None
            
    def _extract_tools(self, text: str) -> List[str]:
        """Extract tool mentions from text"""
        tools = []
        for pattern in self.tool_patterns:
            matches = re.findall(pattern, text.lower())
            tools.extend(matches)
        return list(set(tools))  # Remove duplicates
        
    def _extract_materials(self, text: str) -> List[str]:
        """Extract material mentions from text"""
        materials = []
        for pattern in self.material_patterns:
            matches = re.findall(pattern, text.lower())
            materials.extend(matches)
        return list(set(materials))
        
    def _extract_safety_info(self, text: str) -> List[str]:
        """Extract safety-related information"""
        safety_info = []
        for pattern in self.safety_patterns:
            matches = re.findall(pattern, text.lower(), re.IGNORECASE)
            safety_info.extend(matches)
        return list(set(safety_info))
        
    def _classify_skill_level(self, text: str) -> str:
        """Classify content skill level based on text analysis"""
        text_lower = text.lower()
        
        beginner_indicators = [
            'beginner', 'first time', 'easy', 'simple', 'basic',
            'step by step', 'for beginners', 'getting started'
        ]
        
        expert_indicators = [
            'advanced', 'professional', 'expert', 'complex',
            'industrial', 'commercial', 'precision', 'detailed'
        ]
        
        beginner_score = sum(1 for indicator in beginner_indicators if indicator in text_lower)
        expert_score = sum(1 for indicator in expert_indicators if indicator in text_lower)
        
        if beginner_score > expert_score:
            return 'beginner'
        elif expert_score > beginner_score * 1.5:
            return 'expert'
        else:
            return 'intermediate'
            
    def _classify_project_type(self, title: str, description: str) -> str:
        """Classify project type from title and description"""
        text = f"{title} {description}".lower()
        
        project_types = {
            'bathroom': ['bathroom', 'toilet', 'shower', 'vanity', 'tub'],
            'kitchen': ['kitchen', 'cabinet', 'countertop', 'backsplash'],
            'flooring': ['floor', 'hardwood', 'laminate', 'tile', 'carpet'],
            'electrical': ['electrical', 'wiring', 'outlet', 'switch', 'light'],
            'plumbing': ['plumbing', 'pipe', 'faucet', 'drain', 'water'],
            'outdoor': ['deck', 'fence', 'patio', 'garden', 'shed'],
            'furniture': ['table', 'chair', 'shelf', 'cabinet', 'desk'],
            'repair': ['fix', 'repair', 'broken', 'replace', 'maintenance']
        }
        
        scores = {}
        for project_type, keywords in project_types.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[project_type] = score
            
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'
        
    def _calculate_difficulty_score(self, tutorial: YouTubeTutorial) -> float:
        """Calculate difficulty score from 0 (easy) to 1 (hard)"""
        score = 0.5  # Base score
        
        # Duration factor (longer = more difficult)
        if tutorial.duration > 1800:  # 30+ minutes
            score += 0.2
        elif tutorial.duration < 600:  # < 10 minutes
            score -= 0.1
            
        # Tool complexity
        advanced_tools = ['router', 'miter saw', 'table saw', 'welder']
        if tutorial.tools_mentioned:
            advanced_count = sum(1 for tool in tutorial.tools_mentioned if any(adv in tool for adv in advanced_tools))
            score += advanced_count * 0.1
            
        # Safety mentions (more safety = more difficult)
        if tutorial.safety_mentions:
            score += len(tutorial.safety_mentions) * 0.05
            
        # Skill level mapping
        skill_scores = {'beginner': 0.2, 'intermediate': 0.5, 'expert': 0.8}
        skill_adjustment = skill_scores.get(tutorial.skill_level, 0.5)
        score = (score + skill_adjustment) / 2
        
        return min(max(score, 0), 1)  # Clamp between 0 and 1
        
    def _calculate_quality_score(self, tutorial: YouTubeTutorial) -> float:
        """Calculate quality score based on engagement metrics"""
        if tutorial.view_count == 0:
            return 0.5
            
        # Engagement ratio
        engagement_ratio = tutorial.like_count / tutorial.view_count if tutorial.view_count > 0 else 0
        
        # Base quality from engagement
        quality = min(engagement_ratio * 1000, 1.0)  # Scale and cap at 1.0
        
        # Channel authority (simplified)
        if tutorial.view_count > 100000:  # Popular video
            quality += 0.2
        elif tutorial.view_count > 10000:
            quality += 0.1
            
        # Recency factor
        days_old = (datetime.now() - tutorial.published_date.replace(tzinfo=None)).days
        if days_old < 365:  # Less than a year old
            quality += 0.1
            
        return min(quality, 1.0)
        
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        # Simple parser for PT#M#S format
        import re
        match = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
            minutes = int(match.group(1) or 0)
            seconds = int(match.group(2) or 0)
            return minutes * 60 + seconds
        return 0

class ForumKnowledgeMiner:
    """Mines knowledge from DIY forums and communities"""
    
    def __init__(self, reddit_client_id: str = None, reddit_client_secret: str = None):
        """Initialize forum mining system"""
        
        # Initialize Reddit API
        self.reddit_client_id = reddit_client_id or os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = reddit_client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        
        if self.reddit_client_id and self.reddit_client_secret:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.reddit_client_id,
                    client_secret=self.reddit_client_secret,
                    user_agent='DIY Knowledge Miner 1.0'
                )
                logger.info("Reddit API initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit API: {e}")
                self.reddit = None
        else:
            self.reddit = None
            logger.warning("Reddit API credentials not provided")
            
        # Initialize NLP tools
        try:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except:
            self.sentiment_analyzer = None
            
        # DIY-related subreddits
        self.diy_subreddits = [
            'DIY', 'woodworking', 'HomeImprovement', 'fixit',
            'Tools', 'handtools', 'Carpentry', 'Plumbing',
            'electricians', 'Flooring', 'finishing'
        ]
        
        # Problem/solution patterns
        self.problem_patterns = [
            r'help.*with', r'problem.*with', r'issue.*with',
            r'broken', r'not working', r'failed', r'wrong'
        ]
        
        self.solution_patterns = [
            r'solution', r'fix', r'solved', r'worked',
            r'try.*this', r'what.*worked', r'here.*how'
        ]
        
    def mine_subreddit_knowledge(self, subreddit_name: str, limit: int = 50) -> List[ForumPost]:
        """Mine knowledge from a specific subreddit"""
        if not self.reddit:
            logger.error("Reddit API not available")
            return []
            
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            # Get hot posts
            for submission in subreddit.hot(limit=limit):
                if submission.stickied:  # Skip pinned posts
                    continue
                    
                post = ForumPost(
                    post_id=submission.id,
                    platform='reddit',
                    title=submission.title,
                    content=submission.selftext,
                    author=str(submission.author) if submission.author else 'deleted',
                    score=submission.score,
                    comment_count=submission.num_comments,
                    created_date=datetime.fromtimestamp(submission.created_utc),
                    project_category=subreddit_name.lower()
                )
                
                # Enrich post with extracted knowledge
                post = self._enrich_forum_post(post)
                posts.append(post)
                
            return posts
            
        except Exception as e:
            logger.error(f"Failed to mine subreddit {subreddit_name}: {e}")
            return []
            
    def _enrich_forum_post(self, post: ForumPost) -> ForumPost:
        """Enrich forum post with extracted knowledge"""
        full_text = f"{post.title} {post.content}".lower()
        
        # Extract tools mentioned
        post.tools_mentioned = self._extract_tools_from_text(full_text)
        
        # Extract solutions
        post.solutions_provided = self._extract_solutions(full_text)
        
        # Extract common mistakes
        post.common_mistakes = self._extract_mistakes(full_text)
        
        # Determine if expert-level content
        post.expert_level = self._is_expert_content(post)
        
        return post
        
    def _extract_tools_from_text(self, text: str) -> List[str]:
        """Extract tool names from forum text"""
        tools = []
        tool_keywords = [
            'drill', 'saw', 'hammer', 'screwdriver', 'wrench', 'pliers',
            'router', 'sander', 'grinder', 'level', 'measuring tape'
        ]
        
        for tool in tool_keywords:
            if tool in text:
                tools.append(tool)
                
        return tools
        
    def _extract_solutions(self, text: str) -> List[str]:
        """Extract solution descriptions from text"""
        solutions = []
        
        # Look for solution patterns
        for pattern in self.solution_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract surrounding context (next 100 characters)
                start = match.end()
                solution_text = text[start:start+100].strip()
                if solution_text:
                    solutions.append(solution_text)
                    
        return solutions[:3]  # Limit to top 3 solutions
        
    def _extract_mistakes(self, text: str) -> List[str]:
        """Extract common mistakes from text"""
        mistakes = []
        mistake_indicators = [
            'mistake', 'wrong', 'error', 'don\'t', 'never',
            'avoid', 'careful', 'watch out'
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in mistake_indicators):
                mistakes.append(sentence.strip())
                
        return mistakes[:3]  # Limit to top 3 mistakes
        
    def _is_expert_content(self, post: ForumPost) -> bool:
        """Determine if post contains expert-level content"""
        # High score indicates community approval
        if post.score > 50:
            return True
            
        # Many comments indicate engagement
        if post.comment_count > 20:
            return True
            
        # Technical terms indicate expertise
        expert_terms = [
            'torque', 'tolerance', 'specification', 'grade',
            'commercial', 'industrial', 'professional'
        ]
        
        text = f"{post.title} {post.content}".lower()
        expert_term_count = sum(1 for term in expert_terms if term in text)
        
        return expert_term_count >= 2

class ProjectGuideParser:
    """Parses structured project guides from various sources"""
    
    def __init__(self):
        """Initialize project guide parser"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DIY Knowledge Enrichment Bot 1.0'
        })
        
    def parse_guide_from_url(self, url: str) -> Optional[ProjectGuide]:
        """Parse project guide from URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            steps = self._extract_steps(soup)
            tools = self._extract_tools_list(soup)
            materials = self._extract_materials_list(soup)
            
            guide = ProjectGuide(
                guide_id=self._generate_guide_id(url),
                title=title,
                description=description,
                source_url=url,
                steps=steps,
                tools_required=tools,
                materials_required=materials,
                skill_level=self._infer_skill_level(soup),
                estimated_time=self._extract_time_estimate(soup)
            )
            
            return guide
            
        except Exception as e:
            logger.error(f"Failed to parse guide from {url}: {e}")
            return None
            
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML"""
        title_selectors = ['h1', 'title', '.title', '.guide-title']
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text().strip()
                
        return "Unknown Project"
        
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract description from HTML"""
        desc_selectors = ['.description', '.intro', '.summary', 'meta[name="description"]']
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                if desc_elem.name == 'meta':
                    return desc_elem.get('content', '').strip()
                else:
                    return desc_elem.get_text().strip()[:500]  # Limit length
                    
        return ""
        
    def _extract_steps(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract step-by-step instructions"""
        steps = []
        
        # Look for ordered list or numbered steps
        step_selectors = ['ol li', '.step', '.instruction', '[class*="step"]']
        
        for selector in step_selectors:
            step_elements = soup.select(selector)
            if step_elements:
                for i, elem in enumerate(step_elements[:20]):  # Limit to 20 steps
                    step_text = elem.get_text().strip()
                    if step_text:
                        steps.append({
                            'step_number': i + 1,
                            'instruction': step_text,
                            'tools_needed': [],  # Could be enhanced
                            'materials_needed': []  # Could be enhanced
                        })
                break
                
        return steps
        
    def _extract_tools_list(self, soup: BeautifulSoup) -> List[str]:
        """Extract tools list from HTML"""
        tools = []
        
        # Look for tools sections
        tools_sections = soup.find_all(text=re.compile(r'tools?', re.IGNORECASE))
        
        for section in tools_sections:
            parent = section.parent
            if parent:
                # Look for lists near tools heading
                lists = parent.find_next_siblings(['ul', 'ol']) or parent.find_all(['ul', 'ol'])
                for list_elem in lists[:1]:  # Just first list
                    items = list_elem.find_all('li')
                    for item in items:
                        tool_text = item.get_text().strip()
                        if tool_text:
                            tools.append(tool_text)
                            
        return tools[:10]  # Limit results
        
    def _extract_materials_list(self, soup: BeautifulSoup) -> List[str]:
        """Extract materials list from HTML"""
        materials = []
        
        # Look for materials sections
        materials_sections = soup.find_all(text=re.compile(r'materials?|supplies?', re.IGNORECASE))
        
        for section in materials_sections:
            parent = section.parent
            if parent:
                lists = parent.find_next_siblings(['ul', 'ol']) or parent.find_all(['ul', 'ol'])
                for list_elem in lists[:1]:
                    items = list_elem.find_all('li')
                    for item in items:
                        material_text = item.get_text().strip()
                        if material_text:
                            materials.append(material_text)
                            
        return materials[:10]  # Limit results
        
    def _infer_skill_level(self, soup: BeautifulSoup) -> str:
        """Infer skill level from content"""
        text = soup.get_text().lower()
        
        beginner_indicators = ['beginner', 'easy', 'simple', 'basic', 'first time']
        expert_indicators = ['advanced', 'expert', 'professional', 'complex']
        
        beginner_count = sum(1 for indicator in beginner_indicators if indicator in text)
        expert_count = sum(1 for indicator in expert_indicators if indicator in text)
        
        if beginner_count > expert_count:
            return 'beginner'
        elif expert_count > beginner_count:
            return 'expert'
        else:
            return 'intermediate'
            
    def _extract_time_estimate(self, soup: BeautifulSoup) -> str:
        """Extract time estimate from content"""
        text = soup.get_text()
        
        time_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*days?',
            r'(\d+)\s*weeks?',
            r'(\d+)\s*minutes?'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
                
        return "Unknown"
        
    def _generate_guide_id(self, url: str) -> str:
        """Generate unique guide ID from URL"""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]

class ContentClassifier:
    """Classifies content by skill level, safety requirements, and quality"""
    
    def __init__(self):
        """Initialize content classifier"""
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Safety keywords by category
        self.safety_categories = {
            'eye_protection': ['safety glasses', 'goggles', 'eye protection'],
            'hearing_protection': ['ear plugs', 'ear muffs', 'hearing protection'],
            'respiratory': ['dust mask', 'respirator', 'ventilation'],
            'hand_protection': ['gloves', 'hand protection'],
            'electrical_safety': ['turn off breaker', 'voltage tester', 'GFCI'],
            'tool_safety': ['blade guard', 'safety switch', 'emergency stop']
        }
        
    def classify_safety_level(self, content: str) -> Dict[str, float]:
        """Classify safety level and requirements"""
        safety_scores = {}
        content_lower = content.lower()
        
        for category, keywords in self.safety_categories.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            safety_scores[category] = min(score / len(keywords), 1.0)
            
        return safety_scores
        
    def classify_expertise_level(self, content: str, engagement_metrics: Dict[str, Any] = None) -> str:
        """Classify content expertise level"""
        
        # Text-based classification
        reading_level = flesch_reading_ease(content)
        
        # Technical term density
        technical_terms = [
            'specification', 'tolerance', 'precision', 'calibration',
            'torque', 'tension', 'grade', 'professional', 'commercial'
        ]
        
        tech_density = sum(1 for term in technical_terms if term.lower() in content.lower())
        tech_density = tech_density / len(content.split()) * 100  # Percentage
        
        # Combine factors
        if reading_level < 30 or tech_density > 0.5:  # Hard to read or technical
            base_level = 'expert'
        elif reading_level > 60 and tech_density < 0.1:  # Easy to read
            base_level = 'beginner'
        else:
            base_level = 'intermediate'
            
        # Adjust based on engagement metrics
        if engagement_metrics:
            high_engagement = engagement_metrics.get('score', 0) > 100
            if high_engagement and base_level != 'expert':
                base_level = 'intermediate'  # Popular content often intermediate
                
        return base_level
        
    def extract_quality_indicators(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, float]:
        """Extract quality indicators from content"""
        indicators = {}
        
        # Content length (longer usually better for tutorials)
        word_count = len(content.split())
        indicators['content_length'] = min(word_count / 1000, 1.0)  # Normalize to 1000 words
        
        # Step-by-step structure
        step_indicators = ['step', 'first', 'next', 'then', 'finally']
        step_mentions = sum(1 for indicator in step_indicators if indicator in content.lower())
        indicators['structured_content'] = min(step_mentions / 10, 1.0)
        
        # Safety mentions (good tutorials mention safety)
        safety_mentions = sum(1 for category in self.safety_categories.values() 
                            for keyword in category if keyword in content.lower())
        indicators['safety_awareness'] = min(safety_mentions / 5, 1.0)
        
        # Image/visual references
        visual_indicators = ['image', 'photo', 'diagram', 'illustration', 'video']
        visual_mentions = sum(1 for indicator in visual_indicators if indicator in content.lower())
        indicators['visual_content'] = min(visual_mentions / 3, 1.0)
        
        # Metadata-based indicators
        if metadata:
            # Engagement metrics
            views = metadata.get('view_count', 0)
            likes = metadata.get('like_count', 0)
            
            if views > 0:
                engagement_ratio = likes / views
                indicators['engagement'] = min(engagement_ratio * 1000, 1.0)
            else:
                indicators['engagement'] = 0.0
                
            # Recency
            pub_date = metadata.get('published_date')
            if pub_date:
                days_old = (datetime.now() - pub_date.replace(tzinfo=None)).days
                recency_score = max(0, 1 - (days_old / 365))  # Decreases over year
                indicators['recency'] = recency_score
                
        return indicators

class KnowledgeIntegrator:
    """Integrates all enriched content into actionable insights"""
    
    def __init__(self):
        """Initialize knowledge integrator"""
        self.youtube_enricher = YouTubeEnricher()
        self.forum_miner = ForumKnowledgeMiner()
        self.guide_parser = ProjectGuideParser()
        self.classifier = ContentClassifier()
        
    def generate_content_insights(self, query: str, max_sources: int = 20) -> List[ContentInsight]:
        """Generate comprehensive content insights for a query"""
        insights = []
        
        # Get YouTube tutorials
        tutorials = self.youtube_enricher.search_tutorials(query, max_results=max_sources//2)
        for tutorial in tutorials:
            enriched_tutorial = self.youtube_enricher.enrich_tutorial(tutorial)
            insight = self._tutorial_to_insight(enriched_tutorial)
            insights.append(insight)
            
        # Get forum discussions (simplified - would need actual implementation)
        # This would require more sophisticated forum mining
        
        return insights
        
    def _tutorial_to_insight(self, tutorial: YouTubeTutorial) -> ContentInsight:
        """Convert tutorial to content insight"""
        
        # Calculate product relevance (simplified)
        product_relevance = {}
        if tutorial.tools_mentioned:
            for tool in tutorial.tools_mentioned:
                # In real implementation, would map to actual product IDs
                product_relevance[f"tool_{tool}"] = 0.8
                
        # Extract skill insights
        skill_insights = {
            'tool_usage': 0.7,
            'safety_awareness': 0.6 if tutorial.safety_mentions else 0.3,
            'project_planning': 0.5
        }
        
        # Quality indicators
        quality_indicators = {
            'engagement': tutorial.quality_score,
            'difficulty_appropriate': 1.0 - abs(tutorial.difficulty_score - 0.5),
            'educational_value': 0.8 if tutorial.transcript else 0.5
        }
        
        return ContentInsight(
            content_type='youtube',
            content_id=tutorial.video_id,
            product_relevance=product_relevance,
            skill_insights=skill_insights,
            safety_insights=tutorial.safety_mentions or [],
            usage_patterns={'tools': tutorial.tools_mentioned or []},
            quality_indicators=quality_indicators,
            extracted_knowledge={
                'title': tutorial.title,
                'skill_level': tutorial.skill_level,
                'project_type': tutorial.project_type,
                'duration': tutorial.duration,
                'tools': tutorial.tools_mentioned or [],
                'materials': tutorial.materials_mentioned or []
            }
        )
        
    def aggregate_insights(self, insights: List[ContentInsight]) -> Dict[str, Any]:
        """Aggregate multiple content insights into summary"""
        if not insights:
            return {}
            
        aggregated = {
            'total_sources': len(insights),
            'content_types': {},
            'most_relevant_products': {},
            'key_skills': {},
            'safety_requirements': [],
            'quality_score': 0.0,
            'common_tools': {},
            'skill_level_distribution': {}
        }
        
        # Count content types
        for insight in insights:
            content_type = insight.content_type
            aggregated['content_types'][content_type] = aggregated['content_types'].get(content_type, 0) + 1
            
        # Aggregate product relevance
        for insight in insights:
            for product_id, relevance in insight.product_relevance.items():
                if product_id not in aggregated['most_relevant_products']:
                    aggregated['most_relevant_products'][product_id] = []
                aggregated['most_relevant_products'][product_id].append(relevance)
                
        # Average product relevance scores
        for product_id, scores in aggregated['most_relevant_products'].items():
            aggregated['most_relevant_products'][product_id] = sum(scores) / len(scores)
            
        # Aggregate skills
        for insight in insights:
            for skill, importance in insight.skill_insights.items():
                if skill not in aggregated['key_skills']:
                    aggregated['key_skills'][skill] = []
                aggregated['key_skills'][skill].append(importance)
                
        # Average skill importance
        for skill, scores in aggregated['key_skills'].items():
            aggregated['key_skills'][skill] = sum(scores) / len(scores)
            
        # Collect safety requirements
        all_safety = []
        for insight in insights:
            all_safety.extend(insight.safety_insights)
        aggregated['safety_requirements'] = list(set(all_safety))  # Remove duplicates
        
        # Calculate overall quality score
        quality_scores = []
        for insight in insights:
            avg_quality = sum(insight.quality_indicators.values()) / len(insight.quality_indicators)
            quality_scores.append(avg_quality)
        aggregated['quality_score'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Aggregate tools mentioned
        for insight in insights:
            tools = insight.usage_patterns.get('tools', [])
            for tool in tools:
                aggregated['common_tools'][tool] = aggregated['common_tools'].get(tool, 0) + 1
                
        # Skill level distribution
        for insight in insights:
            skill_level = insight.extracted_knowledge.get('skill_level', 'intermediate')
            aggregated['skill_level_distribution'][skill_level] = aggregated['skill_level_distribution'].get(skill_level, 0) + 1
            
        return aggregated

# Example usage and testing
if __name__ == "__main__":
    # Initialize systems (would need API keys for full functionality)
    integrator = KnowledgeIntegrator()
    
    # Test content enrichment
    test_queries = [
        "how to install bathroom vanity",
        "build wooden deck railing",
        "fix leaky kitchen faucet"
    ]
    
    print("Testing DIY Content Enrichment System:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Generate insights (limited without API keys)
        insights = integrator.generate_content_insights(query, max_sources=3)
        
        if insights:
            aggregated = integrator.aggregate_insights(insights)
            print(f"Found {len(insights)} content sources")
            print(f"Overall quality score: {aggregated.get('quality_score', 0):.2f}")
            print(f"Common tools mentioned: {list(aggregated.get('common_tools', {}).keys())[:3]}")
        else:
            print("No insights generated (API keys required for full functionality)")
            
    print("\nContent enrichment system testing completed!")
    print("Note: Full functionality requires YouTube API and Reddit API credentials")