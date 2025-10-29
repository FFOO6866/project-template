# Multi-lingual Translation Quick Start Guide

## ⚡ Quick Installation (5 minutes)

### 1. Install Dependencies
```bash
pip install openai>=1.0.0 langdetect>=1.0.9 redis>=5.0.0
```

### 2. Verify Configuration
Ensure your `.env.production` has:
```bash
OPENAI_API_KEY=sk-proj-...    # Your OpenAI API key
REDIS_URL=redis://...          # Redis connection string
DATABASE_URL=postgresql://...  # PostgreSQL connection string
```

### 3. Test the System
```bash
# Run comprehensive test suite
python test_multilingual_support.py

# Run Asian languages accuracy test
python test_translation_accuracy.py
```

---

## 🚀 Usage Examples

### Example 1: Basic Translation
```python
from src.translation import TranslationService

service = TranslationService()

# Translate to Chinese
result = service.translate(
    text="Safety helmet for construction work",
    target_lang="zh"
)

print(result.translated_text)  # "建筑工作用安全头盔"
print(result.confidence)        # 0.95
print(result.cache_hit)         # False (first time), True (cached)
```

### Example 2: Product Translation
```python
# Translate product name and description
result = service.translate_product(
    product_name="LED Light Fixture",
    product_description="High-quality industrial LED light with IP65 rating",
    target_lang="ms"  # Malay
)

print(result['name'].translated_text)
# "Lekapan Lampu LED"

print(result['description'].translated_text)
# "Lampu LED industri berkualiti tinggi dengan penarafan IP65"

print(result['description'].technical_terms_preserved)
# ['LED', 'IP65']
```

### Example 3: Database Integration
```python
from src.core.postgresql_database import get_database

db = get_database()

# Translate existing product by ID
result = db.translate_product(
    product_id=1234,
    target_lang="ta"  # Tamil
)

print(result['translated']['name'])         # Tamil product name
print(result['translation_metadata']['confidence'])  # 0.93
```

### Example 4: API Usage
```bash
# Translate text via API
curl -X POST http://localhost:8002/api/translate/text \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Safety equipment for workers",
    "target_lang": "zh",
    "context": "product"
  }'

# Response:
{
  "success": true,
  "translated_text": "工人安全设备",
  "confidence": 0.95,
  "technical_terms_preserved": [],
  "cache_hit": false,
  "processing_time_ms": 1234.5
}
```

---

## 🌍 Supported Languages

**Primary (Singapore):**
- `en` - English
- `zh` - Chinese (Simplified)
- `ms` - Malay
- `ta` - Tamil

**Extended:**
- `de` - German
- `fr` - French
- `es` - Spanish
- `it` - Italian
- `nl` - Dutch
- `pt` - Portuguese
- `ja` - Japanese
- `ko` - Korean
- `th` - Thai

---

## 📊 Translation Sample Translations

### Safety Equipment

| English | Chinese | Malay | Tamil |
|---------|---------|-------|-------|
| Safety helmet | 安全头盔 | Topi keledar keselamatan | பாதுகாப்பு தலைக்கவசம் |
| Safety gloves | 安全手套 | Sarung tangan keselamatan | பாதுகாப்பு கையுறைகள் |
| Safety boots | 安全靴 | But keselamatan | பாதுகாப்பு பூட்ஸ் |
| Safety goggles | 安全护目镜 | Cermin mata keselamatan | பாதுகாப்பு கண்ணாடிகள் |

### Tools & Equipment

| English | Chinese | Malay | Tamil |
|---------|---------|-------|-------|
| LED light | LED灯 | Lampu LED | LED விளக்கு |
| Power tool | 电动工具 | Alat berkuasa | மின்சார கருவி |
| Hand tool | 手工具 | Alat tangan | கை கருவி |
| Measuring tool | 测量工具 | Alat ukur | அளவிடும் கருவி |

---

## 🧪 Testing Your Installation

### Test 1: Language Detection
```python
from src.translation import LanguageDetector

detector = LanguageDetector()

# Test Chinese detection
result = detector.detect("安全头盔")
assert result.language_code == "zh"
print("✅ Chinese detection working")

# Test Malay detection
result = detector.detect("Produk keselamatan")
assert result.language_code == "ms"
print("✅ Malay detection working")

# Test Tamil detection
result = detector.detect("பாதுகாப்பு")
assert result.language_code == "ta"
print("✅ Tamil detection working")
```

### Test 2: Redis Cache
```python
from src.translation.redis_cache_manager import TranslationCacheManager

cache = TranslationCacheManager()

# Test cache health
if cache.health_check():
    print("✅ Redis cache connected")
else:
    print("❌ Redis cache connection failed")

# Test cache operations
cache.set_translation("test", "en", "zh", {"translated_text": "测试"})
cached = cache.get_translation("test", "en", "zh")
assert cached['translated_text'] == "测试"
print("✅ Cache read/write working")
```

### Test 3: GPT-4 Translation
```python
from src.translation import TranslationService

service = TranslationService()

# Test translation
result = service.translate(
    text="Safety equipment",
    target_lang="zh"
)

assert result.confidence > 0.8
assert result.translated_text  # Should contain Chinese characters
print(f"✅ GPT-4 translation working: {result.translated_text}")
```

---

## 📈 Performance Optimization Tips

### 1. Enable Redis Caching
Ensure Redis is running for optimal performance:
```bash
# Check Redis status
redis-cli ping  # Should return "PONG"

# Monitor cache hit rate
redis-cli info stats | grep keyspace_hits
```

### 2. Batch Translations
For multiple translations, use batch mode:
```python
texts = ["Safety helmet", "LED light", "Power tool"]
results = service.translate_batch(texts, target_lang="zh")
```

### 3. Use ETIM for Product Categories
For standard product categories, ETIM translations are instant:
```python
# This uses ETIM (instant, no API call)
result = service.translate(
    text="safety products",
    target_lang="zh",
    context="etim"  # Use ETIM lookup
)
# Processing time: <10ms
```

---

## 🔍 Monitoring & Statistics

### Check Translation Statistics
```python
from src.translation import get_translation_service

service = get_translation_service()
stats = service.get_statistics()

print(f"Total translations: {stats['total_translations']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.2f}%")
print(f"GPT-4 translations: {stats['translations_gpt4']}")
print(f"ETIM translations: {stats['translations_etim']}")
print(f"Supported languages: {stats['supported_languages']}")
```

### Check Cache Performance
```python
from src.translation.redis_cache_manager import get_translation_cache

cache = get_translation_cache()
stats = cache.get_cache_stats()

print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache misses: {stats['cache_misses']}")
print(f"Hit rate: {stats['hit_rate_percent']:.2f}%")
print(f"Performance: {stats['performance_status']}")
```

---

## ⚠️ Troubleshooting

### Issue 1: OpenAI API Error
```
Error: Authentication failed
Solution: Check OPENAI_API_KEY in .env.production
Verify: curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"
```

### Issue 2: Redis Connection Failed
```
Error: Redis connection refused
Solution: Start Redis server
Command: redis-server  # Or docker-compose up redis
```

### Issue 3: Low Translation Confidence
```
Warning: Confidence < 0.7
Cause: Ambiguous or very technical text
Solution: Add context parameter or use ETIM for standard terms
```

### Issue 4: Slow Translation Speed
```
Warning: Processing time > 3s
Cause: First-time translation (no cache)
Solution: Normal for first translation. Subsequent calls use cache (<5ms)
```

---

## 📚 Additional Resources

### Documentation
- **Full Implementation Report:** `PHASE5_MULTILINGUAL_IMPLEMENTATION_REPORT.md`
- **API Documentation:** http://localhost:8002/docs (when server running)
- **Test Suite:** `test_multilingual_support.py`
- **Accuracy Tests:** `test_translation_accuracy.py`

### API Endpoints
- `POST /api/translate/product` - Translate product by ID
- `POST /api/translate/text` - Translate text with context
- `GET /api/translate/languages` - Get supported languages
- `GET /api/translate/statistics` - Get translation statistics
- `POST /api/translate/clear-cache` - Clear cache (admin only)

### Support
For issues or questions, check:
1. Implementation report for detailed architecture
2. Test scripts for usage examples
3. API documentation at /docs endpoint

---

## ✅ Quick Validation Checklist

- [ ] Dependencies installed (`pip install -r requirements-translation.txt`)
- [ ] OpenAI API key configured in `.env.production`
- [ ] Redis running and accessible
- [ ] PostgreSQL database connected
- [ ] Test suite passes (`python test_multilingual_support.py`)
- [ ] API server starts without errors
- [ ] Translation endpoints accessible with authentication

---

**Status:** ✅ Production-Ready
**Version:** 1.0
**Last Updated:** 2025-01-16
