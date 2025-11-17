# Frontend-Backend Integration Guide

Complete guide for running the Dynamic Job Pricing Engine with integrated frontend and backend.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                            │
│                  http://localhost:3000                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─ Next.js Frontend (Port 3000)
                 │  ├─ Job Input Form
                 │  ├─ Status Polling (2s interval)
                 │  └─ Results Display
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/job-pricing/requests                   │  │
│  │  GET  /api/v1/job-pricing/requests/{id}/status       │  │
│  │  GET  /api/v1/job-pricing/results/{id}               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─ PostgreSQL (Job data, results)
             ├─ Redis (Caching, Celery broker)
             └─ Celery Worker (Async processing)
                ├─ OpenAI (Skill extraction)
                ├─ Pricing calculation
                └─ Database updates
```

## Prerequisites

1. **Backend Requirements**:
   - Docker and Docker Compose
   - PostgreSQL with pgvector extension
   - Redis
   - OpenAI API key

2. **Frontend Requirements**:
   - Node.js 18+
   - npm 9+

## Quick Start

### Step 1: Start Backend Services

```bash
# Navigate to job pricing directory
cd src/job_pricing

# Ensure .env file is configured with OpenAI API key
# OPENAI_API_KEY=sk-your-key-here

# Start all backend services
docker-compose up -d --build

# Verify services are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "Dynamic Job Pricing Engine",
  "version": "1.0.0",
  "environment": "development"
}
```

### Step 2: Start Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

### Step 3: Test End-to-End

1. Open browser to `http://localhost:3000`
2. You'll be redirected to `http://localhost:3000/job-pricing`
3. Fill out the job pricing form:
   - **Job Title**: "Software Engineer" (required)
   - **Location**: "Singapore"
   - **Industry**: "Technology"
   - **Company Size**: "51-200"
   - **Experience Min**: 3
   - **Experience Max**: 5
   - **Description**: "Build scalable web applications using Python, React, and AWS..."
4. Click "Analyze Job Pricing"
5. Watch the processing status update automatically
6. View results when processing completes

## Environment Configuration

### Backend (.env)

Located at: `src/job_pricing/.env`

```bash
# Critical Settings
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://job_pricing_user:job_pricing_pass@postgres:5432/job_pricing_db
REDIS_URL=redis://:redis_password@redis:6379/0

# CORS - Allow frontend origin
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Celery
CELERY_BROKER_URL=redis://:redis_password@redis:6379/0
CELERY_RESULT_BACKEND=redis://:redis_password@redis:6379/1
```

### Frontend (.env.local)

Located at: `src/job_pricing/frontend/.env.local`

```bash
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Application Settings
NEXT_PUBLIC_APP_NAME=Dynamic Job Pricing Engine
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## API Endpoints

### 1. Create Job Pricing Request

**Endpoint**: `POST /api/v1/job-pricing/requests`

**Request Body**:
```json
{
  "job_title": "Software Engineer",
  "job_description": "Build web applications...",
  "location_text": "Singapore",
  "years_of_experience_min": 3,
  "years_of_experience_max": 5,
  "industry": "Technology",
  "company_size": "51-200",
  "urgency": "normal",
  "requestor_email": "user@example.com"
}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "job_title": "Software Engineer",
  "location_text": "Singapore",
  "urgency": "normal",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Check Request Status

**Endpoint**: `GET /api/v1/job-pricing/requests/{request_id}/status`

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "error_message": null
}
```

**Status Values**:
- `pending` - Queued, waiting to be processed
- `processing` - Currently being analyzed
- `completed` - Analysis complete, results available
- `failed` - Processing failed

### 3. Get Complete Results

**Endpoint**: `GET /api/v1/job-pricing/results/{request_id}`

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "job_title": "Software Engineer",
  "location_text": "Singapore",
  "extracted_skills": [
    {
      "skill_name": "Python",
      "skill_category": "Programming",
      "matched_tsc_code": "TSC-PRG-001",
      "match_confidence": 0.95,
      "is_core_skill": true
    }
  ],
  "pricing_result": {
    "currency": "SGD",
    "period": "annual",
    "recommended_min": 80000,
    "recommended_max": 120000,
    "target_salary": 100000,
    "p10": 70000,
    "p25": 85000,
    "p50": 100000,
    "p75": 115000,
    "p90": 130000,
    "confidence_score": 85.5,
    "confidence_level": "High",
    "market_position": "P50 (Market Median)",
    "summary_text": "Competitive salary for mid-level software engineer in Singapore technology sector",
    "key_factors": [
      "Experience level: 3-5 years (mid-level)",
      "Location: Singapore (high demand market)",
      "Industry: Technology (15% premium)",
      "Company size: 51-200 (10% adjustment)"
    ],
    "total_data_points": 127,
    "data_sources_used": ["Market surveys", "Job postings", "Internal benchmarks"]
  },
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:25Z"
}
```

## Workflow Details

### 1. Job Submission Flow

```
User fills form → Frontend validates → POST to backend →
Backend creates request → Returns request_id →
Celery task queued → Frontend redirects to processing tab
```

### 2. Status Polling Flow

```
Frontend polls every 2 seconds → GET /requests/{id}/status →
If status="completed" → Fetch full results →
Display results tab → Stop polling
```

### 3. Processing Flow (Backend)

```
Celery picks up task → Marks request as "processing" →
1. Extract skills from description (OpenAI) →
2. Match skills to SSG TSC codes →
3. Calculate experience level →
4. Apply location multiplier →
5. Calculate skill premiums →
6. Generate salary bands (p10-p90) →
7. Calculate confidence score →
8. Save results to database →
9. Mark request as "completed"
```

## Troubleshooting

### Frontend Can't Connect to Backend

**Symptoms**: "Network Error" in browser console

**Solutions**:
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check Docker services
cd src/job_pricing
docker-compose ps

# 3. Check backend logs
docker-compose logs api

# 4. Verify CORS settings
# Ensure CORS_ORIGINS in backend .env includes http://localhost:3000
```

### Backend Processing Fails

**Symptoms**: Request status becomes "failed"

**Solutions**:
```bash
# 1. Check Celery worker logs
docker-compose logs celery-worker

# 2. Verify OpenAI API key
docker-compose exec api python -c "from src.job_pricing.core.config import get_settings; print(get_settings().OPENAI_API_KEY[:10])"

# 3. Check database connectivity
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "SELECT COUNT(*) FROM job_pricing_requests;"

# 4. Restart services
docker-compose restart
```

### Frontend Build Fails

**Symptoms**: `npm run build` errors

**Solutions**:
```bash
# 1. Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# 2. Clear Next.js cache
rm -rf .next

# 3. Check TypeScript errors
npm run type-check

# 4. Update dependencies
npm update
```

### Status Polling Not Working

**Symptoms**: Frontend stuck on "Processing" forever

**Solutions**:
```bash
# 1. Check request status manually
curl http://localhost:8000/api/v1/job-pricing/requests/{request_id}/status

# 2. Check if Celery worker is running
docker-compose ps celery-worker

# 3. Check Celery logs for errors
docker-compose logs celery-worker --tail=50

# 4. Restart Celery worker
docker-compose restart celery-worker
```

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Changes to `.tsx` files reload automatically
- **Backend**: Changes to `.py` files reload uvicorn (if `--reload` flag is set)

### Debugging Backend

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery-worker

# Enter backend container
docker-compose exec api bash

# Run Python shell with app context
docker-compose exec api python
>>> from src.job_pricing.core.database import get_session
>>> session = next(get_session())
```

### Debugging Frontend

```bash
# Check browser console for errors
# Open DevTools → Console tab

# Check Network tab for API calls
# Open DevTools → Network tab → Filter by "job-pricing"

# Run type check
npm run type-check

# Lint code
npm run lint
```

## Testing the Integration

### Manual Test Checklist

- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] Job form validates required fields
- [ ] Form submission creates request
- [ ] Processing status updates automatically
- [ ] Results display when complete
- [ ] All salary data renders correctly
- [ ] Extracted skills are displayed
- [ ] "New Request" button works
- [ ] Error messages display correctly

### Automated Testing

```bash
# Backend tests
cd src/job_pricing
docker-compose exec -T api pytest tests/ -v

# Frontend tests (if implemented)
cd frontend
npm test
```

## Production Deployment

### Backend

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with production settings
ENVIRONMENT=production docker-compose -f docker-compose.prod.yml up -d
```

### Frontend

```bash
# Build for production
npm run build

# Start production server
npm start

# Or deploy to Vercel/Netlify
# Configure NEXT_PUBLIC_API_BASE_URL to production backend URL
```

## Monitoring

### Backend Metrics

- API response times: Check FastAPI `/docs` for metrics
- Celery task queue: Monitor Redis queue length
- Database connections: Check PostgreSQL connection pool
- Error rates: Review application logs

### Frontend Metrics

- Page load times: Use browser DevTools Performance tab
- API call latency: Check Network tab waterfall
- Error rates: Monitor browser console logs
- User interactions: Implement analytics (optional)

## Security Considerations

1. **CORS**: Restrict `CORS_ORIGINS` to specific domains in production
2. **API Keys**: Never expose OpenAI API key in frontend
3. **Rate Limiting**: Implement rate limiting on backend endpoints
4. **Authentication**: Add auth middleware for production use
5. **HTTPS**: Use HTTPS for both frontend and backend in production

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Review this guide
3. Check backend API docs: `http://localhost:8000/docs`
4. Review test files for usage examples

## Summary

You now have a fully integrated frontend-backend system for dynamic job pricing:

✅ **Frontend** (Next.js + React 19 + Tailwind + shadcn/ui)
- Clean, professional UI matching reference design
- Real-time status polling
- Complete workflow from input to results

✅ **Backend** (FastAPI + PostgreSQL + Celery + OpenAI)
- RESTful API endpoints
- Async job processing
- AI-powered skill extraction
- Salary calculation engine

✅ **Integration**
- Seamless API communication
- Automatic status updates
- Error handling
- Type-safe data flow

🚀 **Ready to use at http://localhost:3000**
