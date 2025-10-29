#!/usr/bin/env node

/**
 * Frontend Environment Configuration Validator
 *
 * This script validates that all required environment variables are set
 * and that their values are appropriate for the current environment.
 *
 * Usage:
 *   node validate-env.js
 *   npm run validate-env
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

// Helper functions for colored output
const log = {
  error: (msg) => console.error(`${colors.red}❌ ${msg}${colors.reset}`),
  success: (msg) => console.log(`${colors.green}✅ ${msg}${colors.reset}`),
  warning: (msg) => console.warn(`${colors.yellow}⚠️  ${msg}${colors.reset}`),
  info: (msg) => console.log(`${colors.blue}ℹ️  ${msg}${colors.reset}`),
  section: (msg) => console.log(`\n${colors.cyan}=== ${msg} ===${colors.reset}`),
};

// Load environment variables from .env.local if it exists
const envLocalPath = path.join(__dirname, '.env.local');
if (fs.existsSync(envLocalPath)) {
  const envContent = fs.readFileSync(envLocalPath, 'utf-8');
  envContent.split('\n').forEach((line) => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      const value = valueParts.join('=').trim();
      if (key && value) {
        process.env[key] = value;
      }
    }
  });
}

// Validation rules
const validations = {
  required: [
    {
      name: 'NEXT_PUBLIC_API_URL',
      description: 'Backend API URL',
      validate: (value) => {
        if (!value) return { valid: false, message: 'API URL is required' };
        if (!value.startsWith('http://') && !value.startsWith('https://')) {
          return { valid: false, message: 'API URL must start with http:// or https://' };
        }
        return { valid: true };
      },
    },
    {
      name: 'NEXT_PUBLIC_WEBSOCKET_URL',
      description: 'WebSocket Server URL',
      validate: (value) => {
        if (!value) return { valid: false, message: 'WebSocket URL is required' };
        if (!value.startsWith('ws://') && !value.startsWith('wss://')) {
          return { valid: false, message: 'WebSocket URL must start with ws:// or wss://' };
        }
        return { valid: true };
      },
    },
  ],
  optional: [
    {
      name: 'NEXT_PUBLIC_MCP_URL',
      description: 'MCP Server URL',
      validate: (value) => {
        if (!value) return { valid: true, warning: 'MCP URL not set (optional)' };
        if (!value.startsWith('http://') && !value.startsWith('https://') &&
            !value.startsWith('ws://') && !value.startsWith('wss://')) {
          return { valid: false, message: 'MCP URL must start with http://, https://, ws://, or wss://' };
        }
        return { valid: true };
      },
    },
    {
      name: 'NEXT_PUBLIC_MAX_FILE_SIZE',
      description: 'Maximum file upload size (bytes)',
      validate: (value) => {
        if (!value) return { valid: true, warning: 'Using default (50MB)' };
        const size = parseInt(value, 10);
        if (isNaN(size)) return { valid: false, message: 'Must be a number' };
        if (size < 1048576) return { valid: true, warning: 'Very small (<1MB), is this intentional?' };
        if (size > 104857600) return { valid: true, warning: 'Very large (>100MB), ensure backend supports this' };
        return { valid: true };
      },
    },
    {
      name: 'NEXT_PUBLIC_ALLOWED_FILE_EXTENSIONS',
      description: 'Allowed file extensions',
      validate: (value) => {
        if (!value) return { valid: true, warning: 'No file extensions specified' };
        const extensions = value.split(',').map(e => e.trim());
        if (extensions.length === 0) return { valid: false, message: 'Must specify at least one extension' };
        return { valid: true, info: `${extensions.length} extensions allowed` };
      },
    },
  ],
};

// Environment-specific validations
const environmentChecks = {
  production: [
    {
      check: () => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        return apiUrl.startsWith('https://');
      },
      message: 'API URL should use HTTPS in production',
    },
    {
      check: () => {
        const wsUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL || '';
        return wsUrl.startsWith('wss://');
      },
      message: 'WebSocket URL should use WSS (secure) in production',
    },
    {
      check: () => {
        const debug = (process.env.NEXT_PUBLIC_DEBUG || 'false').toLowerCase();
        return debug === 'false';
      },
      message: 'Debug mode should be disabled in production',
    },
    {
      check: () => {
        const logLevel = (process.env.NEXT_PUBLIC_LOG_LEVEL || 'info').toLowerCase();
        return logLevel === 'error' || logLevel === 'warn';
      },
      message: 'Log level should be "error" or "warn" in production',
    },
  ],
  development: [
    {
      check: () => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        return apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1') || apiUrl.includes('api:');
      },
      message: 'API URL should point to localhost or Docker service in development',
    },
  ],
};

// Main validation function
function validateEnvironment() {
  let errorCount = 0;
  let warningCount = 0;

  log.section('Frontend Environment Configuration Validation');

  // Check if .env.local exists
  if (!fs.existsSync(envLocalPath)) {
    log.warning('.env.local not found. Copy .env.example to .env.local');
    log.info('Run: cp .env.example .env.local');
    console.log('');
  }

  // Detect environment
  const nodeEnv = process.env.NODE_ENV || 'development';
  const environment = process.env.NEXT_PUBLIC_ENVIRONMENT || nodeEnv;
  log.info(`Environment: ${environment}`);
  console.log('');

  // Validate required variables
  log.section('Required Configuration');
  validations.required.forEach(({ name, description, validate }) => {
    const value = process.env[name];
    const result = validate(value);

    if (result.valid) {
      log.success(`${name}: ${description}`);
      if (value) {
        console.log(`   Value: ${value}`);
      }
      if (result.info) {
        log.info(`   ${result.info}`);
      }
    } else {
      log.error(`${name}: ${result.message}`);
      errorCount++;
    }
  });

  // Validate optional variables
  log.section('Optional Configuration');
  validations.optional.forEach(({ name, description, validate }) => {
    const value = process.env[name];
    const result = validate(value);

    if (result.valid) {
      if (result.warning) {
        log.warning(`${name}: ${result.warning}`);
        warningCount++;
      } else {
        log.success(`${name}: ${description}`);
        if (value) {
          console.log(`   Value: ${value.length > 80 ? value.substring(0, 77) + '...' : value}`);
        }
        if (result.info) {
          log.info(`   ${result.info}`);
        }
      }
    } else {
      log.error(`${name}: ${result.message}`);
      errorCount++;
    }
  });

  // Environment-specific checks
  const envChecks = environmentChecks[environment] || [];
  if (envChecks.length > 0) {
    log.section(`Environment-Specific Checks (${environment})`);
    envChecks.forEach(({ check, message }) => {
      if (check()) {
        log.success(message);
      } else {
        log.warning(message);
        warningCount++;
      }
    });
  }

  // File size consistency check
  log.section('Configuration Consistency');
  const maxFileSize = process.env.NEXT_PUBLIC_MAX_FILE_SIZE;
  const maxFileSizeMB = process.env.NEXT_PUBLIC_MAX_FILE_SIZE_MB;

  if (maxFileSize && maxFileSizeMB) {
    const calculatedMB = Math.floor(parseInt(maxFileSize, 10) / 1048576);
    const specifiedMB = parseInt(maxFileSizeMB, 10);

    if (calculatedMB === specifiedMB) {
      log.success('File size values are consistent');
      console.log(`   ${maxFileSizeMB}MB = ${maxFileSize} bytes`);
    } else {
      log.error('File size mismatch!');
      console.log(`   NEXT_PUBLIC_MAX_FILE_SIZE_MB: ${maxFileSizeMB}MB`);
      console.log(`   NEXT_PUBLIC_MAX_FILE_SIZE: ${maxFileSize} bytes (${calculatedMB}MB)`);
      errorCount++;
    }
  }

  // Feature flags summary
  log.section('Feature Flags');
  const features = [
    'NEXT_PUBLIC_ENABLE_CHAT',
    'NEXT_PUBLIC_ENABLE_UPLOAD',
    'NEXT_PUBLIC_ENABLE_REPORTS',
    'NEXT_PUBLIC_ENABLE_AI_RECOMMENDATIONS',
    'NEXT_PUBLIC_ENABLE_NOTIFICATIONS',
    'NEXT_PUBLIC_ENABLE_SEARCH',
    'NEXT_PUBLIC_ENABLE_QUOTATIONS',
  ];

  const enabledFeatures = [];
  const disabledFeatures = [];

  features.forEach((feature) => {
    const value = (process.env[feature] || 'true').toLowerCase();
    const isEnabled = value === 'true';
    const featureName = feature.replace('NEXT_PUBLIC_ENABLE_', '');

    if (isEnabled) {
      enabledFeatures.push(featureName);
    } else {
      disabledFeatures.push(featureName);
    }
  });

  if (enabledFeatures.length > 0) {
    log.success(`Enabled features: ${enabledFeatures.join(', ')}`);
  }
  if (disabledFeatures.length > 0) {
    log.info(`Disabled features: ${disabledFeatures.join(', ')}`);
  }

  // Summary
  log.section('Validation Summary');

  if (errorCount === 0 && warningCount === 0) {
    log.success('All checks passed! Environment is properly configured.');
  } else {
    if (errorCount > 0) {
      log.error(`Found ${errorCount} error(s)`);
    }
    if (warningCount > 0) {
      log.warning(`Found ${warningCount} warning(s)`);
    }
  }

  console.log('');

  // Exit with error code if there are errors
  if (errorCount > 0) {
    log.error('Configuration validation failed. Please fix the errors above.');
    process.exit(1);
  } else {
    log.success('Configuration validation completed.');
    process.exit(0);
  }
}

// Run validation
try {
  validateEnvironment();
} catch (error) {
  log.error(`Validation failed with error: ${error.message}`);
  console.error(error);
  process.exit(1);
}
