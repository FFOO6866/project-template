# Job Pricing Frontend

Next.js 14 frontend application for the Dynamic Job Pricing Engine.

## Features

- **Job Input Form**: Comprehensive form for job details including title, description, location, experience, industry, and company size
- **Real-time Status Polling**: Automatic polling of job processing status with visual feedback
- **Results Display**: Beautiful display of salary recommendations, extracted skills, and market insights
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **TypeScript**: Full type safety with TypeScript
- **Tailwind CSS**: Modern, utility-first CSS framework
- **shadcn/ui Components**: High-quality, accessible UI components

## Prerequisites

- Node.js 18+ and npm 9+
- Backend API running on `http://localhost:8000` (or configure via `.env.local`)

## Installation

```bash
# Navigate to frontend directory
cd src/job_pricing/frontend

# Install dependencies
npm install
```

## Configuration

Create or update `.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Application Settings
NEXT_PUBLIC_APP_NAME=Dynamic Job Pricing Engine
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000 in your browser
```

## Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                          # Next.js app directory
│   ├── globals.css              # Global styles
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home page (redirects to /job-pricing)
│   └── job-pricing/
│       └── page.tsx             # Main job pricing page
├── components/
│   └── ui/                      # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── textarea.tsx
│       ├── badge.tsx
│       └── alert.tsx
├── lib/
│   ├── utils.ts                 # Utility functions
│   └── api.ts                   # Backend API integration
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .env.local
```

## API Integration

The frontend integrates with the FastAPI backend using the following endpoints:

- `POST /api/v1/job-pricing/requests` - Create new job pricing request
- `GET /api/v1/job-pricing/requests/{id}/status` - Poll request status
- `GET /api/v1/job-pricing/results/{id}` - Get complete results

See `lib/api.ts` for the complete API client implementation.

## Workflow

1. **Job Input**: User fills out the job details form
2. **Submission**: Form data is sent to backend API, returns request ID
3. **Status Polling**: Frontend polls status endpoint every 2 seconds
4. **Results Display**: When status is "completed", fetches and displays full results

## Type Safety

All API types are defined in `lib/api.ts` and match the backend Pydantic schemas:

- `JobPricingRequest` - Request creation data
- `JobPricingRequestResponse` - Basic request info
- `JobPricingStatusResponse` - Status polling response
- `JobPricingResultResponse` - Complete results with skills and pricing

## Styling

- **Tailwind CSS**: Utility-first CSS framework
- **CSS Variables**: Theme customization via CSS variables
- **shadcn/ui**: Pre-built accessible components
- **Responsive**: Mobile-first responsive design

## Error Handling

- API errors are caught and displayed to users
- Network errors show user-friendly messages
- Failed requests can be retried by creating new request

## Future Enhancements

- Advanced filtering and search
- Historical request tracking
- Export results to PDF
- Comparison between multiple job titles
- Real-time notifications
- Dark mode support

## Troubleshooting

### Backend Connection Issues

If you see "Network Error" or connection failures:

1. Ensure backend is running: `docker-compose up -d`
2. Verify backend health: `curl http://localhost:8000/health`
3. Check CORS settings in backend `.env` file
4. Verify `NEXT_PUBLIC_API_BASE_URL` in frontend `.env.local`

### Styling Issues

If styles don't load:

1. Ensure Tailwind CSS is configured: `npx tailwindcss init`
2. Verify `globals.css` is imported in `layout.tsx`
3. Clear Next.js cache: `rm -rf .next`
4. Restart dev server

### TypeScript Errors

If you see type errors:

1. Run type check: `npm run type-check`
2. Ensure all dependencies are installed
3. Check `tsconfig.json` configuration
4. Restart TypeScript server in your IDE

## License

Proprietary - Internal use only
