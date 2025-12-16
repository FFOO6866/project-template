/** @type {import('next').NextConfig} */

// Validate required environment variables
if (!process.env.NEXT_PUBLIC_API_BASE_URL) {
  throw new Error('NEXT_PUBLIC_API_BASE_URL environment variable is required')
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL

const nextConfig = {
  reactStrictMode: true,

  // Enable standalone output for Docker production builds
  output: 'standalone',

  env: {
    NEXT_PUBLIC_API_BASE_URL: API_BASE_URL,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_BASE_URL}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
