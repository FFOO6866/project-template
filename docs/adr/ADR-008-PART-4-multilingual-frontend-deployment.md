# ADR-008 PART 4: Multi-lingual LLM & Production Frontend Deployment

**Continuation of**: ADR-008-PART-3-safety-multilingual-deployment.md
**Status**: PROPOSED
**Date**: 2025-01-16

---

## Phase 5: Multi-lingual LLM Support (2 weeks)

### Overview

Implement comprehensive multi-lingual support leveraging:
1. **ETIM Translations**: 13+ languages for product classifications
2. **LLM Translation**: OpenAI GPT-4 for dynamic content translation
3. **Language Detection**: Automatic detection of user's language
4. **Context-Aware Translation**: Maintain technical accuracy in translations
5. **Fallback System**: Graceful degradation when translations unavailable

**Supported Languages (ETIM Standard)**:
- English (en)
- Chinese Simplified (zh)
- Malay (ms)
- Tamil (ta)
- German (de)
- French (fr)
- Spanish (es)
- Italian (it)
- Dutch (nl)
- Portuguese (pt)
- Japanese (ja)
- Korean (ko)
- Thai (th)
- Vietnamese (vi)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│             Multi-lingual Translation System                 │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │   Language   │     │     ETIM     │     │    LLM     │ │
│  │  Detection   │────▶│ Translations │────▶│ Translation│ │
│  │              │     │   (static)   │     │ (dynamic)  │ │
│  │  (FastText)  │     │              │     │  (GPT-4)   │ │
│  └──────────────┘     └──────────────┘     └────────────┘ │
│         │                     │                     │       │
│         └──────────┬──────────┴──────────┬──────────┘       │
│                    │                     │                  │
│                    ▼                     ▼                  │
│          ┌─────────────────┐   ┌─────────────────┐         │
│          │ Translation     │   │   Redis Cache   │         │
│          │ Quality Check   │   │   (Fast lookup) │         │
│          └─────────────────┘   └─────────────────┘         │
│                    │                     │                  │
│                    └──────────┬──────────┘                  │
│                               │                             │
│                               ▼                             │
│                      [Translated Content]                   │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

**File**: `src/services/multilingual_service.py`

```python
"""
Multi-lingual Support Service
13+ language support using ETIM + LLM translations
"""

import openai
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import redis
import json
import hashlib

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages."""
    ENGLISH = "en"
    CHINESE_SIMPLIFIED = "zh"
    MALAY = "ms"
    TAMIL = "ta"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    ITALIAN = "it"
    DUTCH = "nl"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    KOREAN = "ko"
    THAI = "th"
    VIETNAMESE = "vi"


@dataclass
class TranslationResult:
    """Translation result with metadata."""
    original_text: str
    translated_text: str
    source_language: Language
    target_language: Language
    translation_method: str  # 'etim', 'llm', 'cache'
    confidence: float
    technical_terms_preserved: List[str]


class MultilingualService:
    """
    Comprehensive multi-lingual support service.
    Uses ETIM translations for product data, LLM for dynamic content.
    """

    def __init__(
        self,
        openai_api_key: str,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        etim_data: Optional[Dict] = None
    ):
        """Initialize multi-lingual service."""

        # OpenAI for dynamic translation
        openai.api_key = openai_api_key

        # Redis for translation caching
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )

        # ETIM translations (loaded from classification service)
        self.etim_data = etim_data or {}

        # Language names (for user display)
        self.language_names = {
            Language.ENGLISH: "English",
            Language.CHINESE_SIMPLIFIED: "中文 (简体)",
            Language.MALAY: "Bahasa Melayu",
            Language.TAMIL: "தமிழ்",
            Language.GERMAN: "Deutsch",
            Language.FRENCH: "Français",
            Language.SPANISH: "Español",
            Language.ITALIAN: "Italiano",
            Language.DUTCH: "Nederlands",
            Language.PORTUGUESE: "Português",
            Language.JAPANESE: "日本語",
            Language.KOREAN: "한국어",
            Language.THAI: "ไทย",
            Language.VIETNAMESE: "Tiếng Việt"
        }

        # Technical terms that should NOT be translated
        self.technical_terms = {
            'en': ['ANSI', 'OSHA', 'UNSPSC', 'ETIM', 'IP65', 'Cat6', 'Li-Ion', 'HSS', 'RPM', 'NRR'],
            # Add more as needed
        }

        logger.info("Multi-lingual Service initialized")

    def detect_language(self, text: str) -> Language:
        """
        Detect language of input text.
        Uses simple heuristics + LLM fallback.

        Args:
            text: Input text

        Returns:
            Detected Language
        """
        # Simple heuristic: Check for Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return Language.CHINESE_SIMPLIFIED

        # Check for Tamil script
        if any('\u0b80' <= char <= '\u0bff' for char in text):
            return Language.TAMIL

        # Check for Thai script
        if any('\u0e00' <= char <= '\u0e7f' for char in text):
            return Language.THAI

        # Use LLM for detection (more accurate but slower)
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Detect the language of the following text. Respond with only the ISO 639-1 language code (e.g., 'en', 'zh', 'ms', 'ta')."},
                    {"role": "user", "content": text[:200]}  # First 200 chars
                ],
                temperature=0.0,
                max_tokens=10
            )

            lang_code = response.choices[0].message.content.strip().lower()

            # Map to Language enum
            for lang in Language:
                if lang.value == lang_code:
                    return lang

        except Exception as e:
            logger.warning(f"Language detection failed: {e}")

        # Default to English
        return Language.ENGLISH

    def translate_text(
        self,
        text: str,
        target_language: Language,
        source_language: Optional[Language] = None,
        preserve_technical_terms: bool = True,
        context: str = "hardware_diy"
    ) -> TranslationResult:
        """
        Translate text to target language using LLM.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)
            preserve_technical_terms: Keep technical terms untranslated
            context: Domain context for better translation

        Returns:
            TranslationResult with translated text
        """
        # Auto-detect source language if not provided
        if source_language is None:
            source_language = self.detect_language(text)

        # Check cache first
        cache_key = self._get_cache_key(text, source_language, target_language)
        cached = self.redis_client.get(cache_key)

        if cached:
            logger.debug(f"Cache hit for translation: {cache_key}")
            cached_data = json.loads(cached)
            return TranslationResult(
                original_text=text,
                translated_text=cached_data['translated_text'],
                source_language=source_language,
                target_language=target_language,
                translation_method='cache',
                confidence=1.0,
                technical_terms_preserved=cached_data.get('technical_terms', [])
            )

        # If same language, return as-is
        if source_language == target_language:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                translation_method='none',
                confidence=1.0,
                technical_terms_preserved=[]
            )

        # Extract technical terms to preserve
        technical_terms = []
        if preserve_technical_terms:
            for term in self.technical_terms.get(source_language.value, []):
                if term in text:
                    technical_terms.append(term)

        # Translate using GPT-4
        try:
            system_prompt = f"""You are a professional translator specializing in hardware and DIY content.

Translate the following text from {self.language_names[source_language]} to {self.language_names[target_language]}.

Important guidelines:
1. Preserve technical accuracy
2. Do NOT translate these technical terms: {', '.join(technical_terms)}
3. Maintain any measurements, codes, or standards as-is
4. Use appropriate industry terminology
5. Context: {context}"""

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,  # Lower for consistency
                max_tokens=1500
            )

            translated_text = response.choices[0].message.content.strip()

            # Cache the translation (24-hour expiry)
            cache_data = {
                'translated_text': translated_text,
                'technical_terms': technical_terms
            }
            self.redis_client.setex(cache_key, 86400, json.dumps(cache_data))

            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                translation_method='llm',
                confidence=0.95,
                technical_terms_preserved=technical_terms
            )

        except Exception as e:
            logger.error(f"LLM translation failed: {e}")

            # Fallback: return original text with error
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                translation_method='fallback',
                confidence=0.0,
                technical_terms_preserved=[]
            )

    def translate_product_data(
        self,
        product: Dict,
        target_language: Language
    ) -> Dict:
        """
        Translate product data using ETIM translations + LLM.

        Args:
            product: Product dict with name, description, etc.
            target_language: Target language

        Returns:
            Translated product dict
        """
        translated_product = product.copy()

        # Use ETIM translation if available
        if 'etim_code' in product and product['etim_code'] in self.etim_data:
            etim_class = self.etim_data[product['etim_code']]
            translations = etim_class.get('translations', {})

            if target_language.value in translations:
                # Use ETIM translation for product category
                translated_product['category_translated'] = translations[target_language.value]

        # Translate product name and description using LLM
        if 'name' in product:
            name_result = self.translate_text(
                product['name'],
                target_language,
                preserve_technical_terms=True,
                context="product_name"
            )
            translated_product['name_translated'] = name_result.translated_text

        if 'description' in product:
            desc_result = self.translate_text(
                product['description'],
                target_language,
                preserve_technical_terms=True,
                context="product_description"
            )
            translated_product['description_translated'] = desc_result.translated_text

        return translated_product

    def translate_rfp(
        self,
        rfp_text: str,
        target_language: Language = Language.ENGLISH
    ) -> str:
        """
        Translate RFP to English for processing.
        Handles multi-lingual RFP submissions.

        Args:
            rfp_text: RFP text in any language
            target_language: Target language (default: English for processing)

        Returns:
            Translated RFP text
        """
        result = self.translate_text(
            rfp_text,
            target_language,
            preserve_technical_terms=True,
            context="rfp_document"
        )

        return result.translated_text

    def translate_quotation(
        self,
        quotation: Dict,
        target_language: Language
    ) -> Dict:
        """
        Translate entire quotation to target language.

        Args:
            quotation: Quotation dict
            target_language: Target language

        Returns:
            Translated quotation
        """
        translated = quotation.copy()

        # Translate quotation items
        if 'quotation_items' in quotation:
            translated['quotation_items'] = []
            for item in quotation['quotation_items']:
                translated_item = item.copy()

                # Translate product name
                if 'product_name' in item:
                    result = self.translate_text(
                        item['product_name'],
                        target_language,
                        preserve_technical_terms=True
                    )
                    translated_item['product_name_translated'] = result.translated_text

                # Translate description
                if 'description' in item:
                    result = self.translate_text(
                        item['description'],
                        target_language,
                        preserve_technical_terms=True
                    )
                    translated_item['description_translated'] = result.translated_text

                translated['quotation_items'].append(translated_item)

        # Add language metadata
        translated['language'] = target_language.value
        translated['translation_method'] = 'llm'

        return translated

    def _get_cache_key(
        self,
        text: str,
        source_lang: Language,
        target_lang: Language
    ) -> str:
        """Generate Redis cache key for translation."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"translation:{source_lang.value}:{target_lang.value}:{text_hash}"

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages for UI.

        Returns:
            List of dicts with code and name
        """
        return [
            {'code': lang.value, 'name': self.language_names[lang]}
            for lang in Language
        ]


# ============================================================================
# API INTEGRATION
# ============================================================================

def create_multilingual_api_endpoints(app, multilingual_service: MultilingualService):
    """Add multi-lingual API endpoints to FastAPI app."""
    from fastapi import Query

    @app.get("/api/languages")
    async def get_supported_languages():
        """Get list of supported languages."""
        return {
            "success": True,
            "languages": multilingual_service.get_supported_languages()
        }

    @app.post("/api/translate")
    async def translate_text(
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ):
        """Translate text to target language."""
        try:
            # Parse language codes
            target_lang = Language(target_language)
            source_lang = Language(source_language) if source_language else None

            # Translate
            result = multilingual_service.translate_text(
                text=text,
                target_language=target_lang,
                source_language=source_lang
            )

            return {
                "success": True,
                "translation": {
                    "original": result.original_text,
                    "translated": result.translated_text,
                    "source_language": result.source_language.value,
                    "target_language": result.target_language.value,
                    "confidence": result.confidence,
                    "method": result.translation_method
                }
            }

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @app.post("/api/process-rfp-multilingual")
    async def process_rfp_multilingual(
        rfp_text: str,
        customer_name: str,
        rfp_language: str = "en",
        response_language: str = "en"
    ):
        """
        Process RFP in any language, return quotation in requested language.
        """
        try:
            # Step 1: Translate RFP to English for processing
            rfp_lang = Language(rfp_language)
            if rfp_lang != Language.ENGLISH:
                logger.info(f"Translating RFP from {rfp_language} to English")
                rfp_text = multilingual_service.translate_rfp(rfp_text)

            # Step 2: Process RFP (use existing processor)
            # (This would call the hybrid recommendation engine)
            quotation = {
                # ... quotation generation logic ...
            }

            # Step 3: Translate quotation to response language
            response_lang = Language(response_language)
            if response_lang != Language.ENGLISH:
                logger.info(f"Translating quotation to {response_language}")
                quotation = multilingual_service.translate_quotation(
                    quotation,
                    response_lang
                )

            return {
                "success": True,
                "quotation": quotation
            }

        except Exception as e:
            logger.error(f"Multi-lingual RFP processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import os

    # Initialize service
    multilingual_service = MultilingualService(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", 6379)),
        redis_password=os.getenv("REDIS_PASSWORD")
    )

    # Example 1: Translate product description to Chinese
    print("\n=== Product Translation ===")
    product = {
        "name": "Cordless Power Drill 20V",
        "description": "20V lithium-ion cordless drill with variable speed and LED light",
        "etim_code": "EC001489"
    }

    translated = multilingual_service.translate_product_data(
        product,
        Language.CHINESE_SIMPLIFIED
    )

    print(f"Original: {product['name']}")
    print(f"Chinese: {translated.get('name_translated', 'N/A')}")
    print(f"Category: {translated.get('category_translated', 'N/A')}")

    # Example 2: Translate RFP from Chinese
    print("\n=== RFP Translation ===")
    chinese_rfp = "我需要购买5个电钻和10个安全眼镜"

    english_rfp = multilingual_service.translate_rfp(chinese_rfp)
    print(f"Original (Chinese): {chinese_rfp}")
    print(f"Translated (English): {english_rfp}")

    # Example 3: Language detection
    print("\n=== Language Detection ===")
    samples = [
        "I need 5 drills",
        "我需要5个电钻",
        "Saya perlukan 5 gerudi",
        "எனக்கு 5 துளையிடும் கருவிகள் தேவை"
    ]

    for sample in samples:
        detected = multilingual_service.detect_language(sample)
        print(f"{sample} → {multilingual_service.language_names[detected]}")
```

### Implementation Checklist - Phase 5

- [ ] Implement `src/services/multilingual_service.py`
- [ ] Integrate with Redis for translation caching
- [ ] Update API endpoints to accept language parameters
- [ ] Integrate with RFP processing workflow
- [ ] Create language selector UI component
- [ ] Add multi-lingual support to quotation generation
- [ ] Test translations with native speakers
- [ ] Create translation quality metrics dashboard
- [ ] Add language detection to chat interface
- [ ] Document translation best practices for developers

**Estimated Time**: 2 weeks
**Dependencies**: Phase 3 (Hybrid Engine), Phase 2 (ETIM)
**Risk Level**: Medium (OpenAI API dependency, translation accuracy)

---

## Phase 6: Frontend + WebSocket Production Deployment (2 weeks)

### Overview

Deploy the Next.js frontend and WebSocket chat infrastructure to production:
1. **Frontend Production Build**: Optimize and containerize Next.js app
2. **WebSocket Server**: Real-time chat with AI assistant
3. **Nginx Configuration**: Reverse proxy with WebSocket support
4. **SSL/TLS Setup**: HTTPS and WSS security
5. **CDN Integration**: Static asset optimization

### Implementation

#### 6.1 Frontend Dockerfile

**File**: `fe-reference/Dockerfile`

```dockerfile
# Multi-stage build for Next.js production

# Stage 1: Dependencies
FROM node:18-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --only=production

# Stage 2: Builder
FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Set environment variables for build
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXT_TELEMETRY_DISABLED=1

# Build Next.js app
RUN npm run build

# Stage 3: Runner
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

CMD ["node", "server.js"]
```

#### 6.2 WebSocket Chat Server

**File**: `src/websocket_chat_server.py`

```python
"""
Production WebSocket Chat Server
Real-time AI-powered chat with context awareness
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Set
from datetime import datetime
import openai
import os

logger = logging.getLogger(__name__)


class ChatServer:
    """WebSocket chat server with AI integration."""

    def __init__(self, host: str = "0.0.0.0", port: int = 3002):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.sessions: Dict[str, Dict] = {}  # session_id -> context

        # Initialize OpenAI
        openai.api_key = os.getenv("OPENAI_API_KEY")

        logger.info(f"Chat server initialized on {host}:{port}")

    async def register(self, websocket: websockets.WebSocketServerProtocol, session_id: str):
        """Register new client."""
        self.clients.add(websocket)
        self.sessions[session_id] = {
            'started_at': datetime.now().isoformat(),
            'messages': [],
            'context': {}
        }
        logger.info(f"Client registered: {session_id}")

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister client."""
        self.clients.discard(websocket)
        logger.info(f"Client unregistered")

    async def handle_message(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: Dict
    ):
        """Handle incoming message from client."""
        try:
            msg_type = message.get('type')
            session_id = message.get('session_id')

            if msg_type == 'chat':
                await self.handle_chat_message(websocket, session_id, message)
            elif msg_type == 'set_context':
                await self.handle_set_context(session_id, message)
            else:
                await self.send_error(websocket, f"Unknown message type: {msg_type}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(websocket, str(e))

    async def handle_chat_message(
        self,
        websocket: websockets.WebSocketServerProtocol,
        session_id: str,
        message: Dict
    ):
        """Handle chat message with AI response."""
        user_message = message.get('message', '')
        session = self.sessions.get(session_id, {})

        # Add user message to history
        session['messages'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })

        # Build context for AI
        context = session.get('context', {})
        system_prompt = self._build_system_prompt(context)

        # Get AI response
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[{"role": msg['role'], "content": msg['content']} for msg in session['messages'][-10:]]  # Last 10 messages
                ],
                temperature=0.7,
                max_tokens=500
            )

            ai_message = response.choices[0].message.content

            # Add AI response to history
            session['messages'].append({
                'role': 'assistant',
                'content': ai_message,
                'timestamp': datetime.now().isoformat()
            })

            # Send response to client
            await self.send_message(websocket, {
                'type': 'chat_response',
                'message': ai_message,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"AI response failed: {e}")
            await self.send_error(websocket, "Failed to generate AI response")

    async def handle_set_context(self, session_id: str, message: Dict):
        """Set context for chat session (e.g., current document, quotation)."""
        session = self.sessions.get(session_id, {})
        session['context'] = message.get('context', {})
        logger.info(f"Context updated for session {session_id}")

    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt based on context."""
        base_prompt = """You are a helpful AI assistant for a hardware and DIY tools platform.
You help users with:
- Product recommendations
- Tool selection for DIY projects
- Safety guidelines
- Technical specifications
- RFP analysis

Always provide accurate, safety-conscious advice."""

        if 'document' in context:
            base_prompt += f"\n\nCurrent document being viewed: {context['document'].get('name', 'Unknown')}"

        if 'quotation' in context:
            base_prompt += f"\n\nCurrent quotation ID: {context['quotation'].get('quote_id', 'Unknown')}"

        return base_prompt

    async def send_message(self, websocket: websockets.WebSocketServerProtocol, message: Dict):
        """Send message to client."""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def send_error(self, websocket: websockets.WebSocketServerProtocol, error: str):
        """Send error message to client."""
        await self.send_message(websocket, {
            'type': 'error',
            'error': error,
            'timestamp': datetime.now().isoformat()
        })

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Main WebSocket handler."""
        session_id = None

        try:
            # Initial handshake
            async for message_str in websocket:
                message = json.loads(message_str)

                # Register client on first message
                if message.get('type') == 'connect':
                    session_id = message.get('session_id', str(id(websocket)))
                    await self.register(websocket, session_id)
                    await self.send_message(websocket, {
                        'type': 'connected',
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat()
                    })
                    continue

                # Handle messages
                await self.handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self.unregister(websocket)

    async def start(self):
        """Start WebSocket server."""
        async with websockets.serve(self.handler, self.host, self.port):
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Validate environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.critical("OPENAI_API_KEY not set")
        sys.exit(1)

    # Create and start server
    server = ChatServer(host="0.0.0.0", port=3002)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
```

#### 6.3 Update docker-compose.production.yml

Add WebSocket and Frontend services:

```yaml
  # WebSocket Chat Server
  websocket:
    build:
      context: .
      dockerfile: Dockerfile.websocket
    container_name: horme-websocket
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
    ports:
      - "3002:3002"
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import websockets; import asyncio; asyncio.run(websockets.connect('ws://localhost:3002'))"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - horme_network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'

  # Frontend (Already exists, verify configuration)
  frontend:
    build:
      context: ./fe-reference
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_URL=http://nginx/api
        - NEXT_PUBLIC_WS_URL=ws://nginx/ws
    container_name: horme-frontend
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://nginx/api
      - NEXT_PUBLIC_WS_URL=ws://nginx/ws
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - horme_network
```

#### 6.4 Nginx Configuration for WebSocket

**File**: `nginx/conf.d/default.conf`

```nginx
# Horme Production Nginx Configuration
# Supports WebSocket proxying

upstream api_backend {
    server api:8000;
}

upstream frontend_backend {
    server frontend:3000;
}

upstream websocket_backend {
    server websocket:3002;
}

# HTTP Server (redirect to HTTPS in production)
server {
    listen 80;
    server_name _;

    location / {
        return 301 https://$host$request_uri;
    }

    # Health check (no redirect)
    location /health {
        proxy_pass http://api_backend/health;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name _;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend (Next.js)
    location / {
        proxy_pass http://frontend_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Backend
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS (handled by FastAPI, but backup here)
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    }

    # WebSocket Chat
    location /ws {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeout
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Static assets caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend_backend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Implementation Checklist - Phase 6

- [ ] Create `fe-reference/Dockerfile` with multi-stage build
- [ ] Create `src/websocket_chat_server.py`
- [ ] Create `Dockerfile.websocket` for chat server
- [ ] Update `docker-compose.production.yml` with websocket service
- [ ] Create `nginx/conf.d/default.conf` with WebSocket support
- [ ] Generate SSL certificates (Let's Encrypt or self-signed for dev)
- [ ] Test WebSocket connection from frontend
- [ ] Integrate chat UI with WebSocket backend
- [ ] Test real-time chat functionality
- [ ] Deploy to staging environment for testing
- [ ] Performance testing (concurrent users, WebSocket stability)
- [ ] Deploy to production

**Estimated Time**: 2 weeks
**Dependencies**: All previous phases
**Risk Level**: Medium (infrastructure, real-time communication)

---

## **COMPREHENSIVE IMPLEMENTATION SUMMARY**

### **Total Timeline**: 15 weeks (3.75 months)
### **Total Investment**: Enterprise-grade recommendation system

### **Phase Breakdown**:
1. **Neo4j Knowledge Graph**: 3 weeks - FOUNDATIONAL
2. **UNSPSC/ETIM Classification**: 2 weeks - STANDARDS COMPLIANCE
3. **Hybrid AI Recommendation Engine**: 4 weeks - CORE INTELLIGENCE
4. **Safety Compliance (OSHA/ANSI)**: 2 weeks - LEGAL PROTECTION
5. **Multi-lingual LLM Support**: 2 weeks - GLOBAL REACH
6. **Frontend + WebSocket Deployment**: 2 weeks - USER INTERFACE

### **Expected Outcomes**:
- **25-40% improvement** in product matching accuracy (industry benchmarks)
- **13+ languages** supported via ETIM + LLM
- **OSHA/ANSI compliance** for legal protection
- **Real-time chat** with AI assistant
- **Enterprise-grade** knowledge graph with 10,000+ products
- **Production-ready** deployment with Docker + Nginx

### **Business Value**:
- Competitive with Home Depot/Lowe's recommendation systems
- Legal compliance for safety-critical recommendations
- Multi-lingual support for Singapore market (English, Chinese, Malay, Tamil)
- Real-time customer engagement via chat
- Scalable architecture for future growth

---

**END OF ADR-008 COMPREHENSIVE IMPLEMENTATION PLAN**
