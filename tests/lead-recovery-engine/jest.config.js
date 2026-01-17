module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/tests/**/*.test.ts',
    '**/?(*.)+(spec|test).ts'
  ],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
    '!src/**/*.interface.ts'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov', 
    'html',
    'json-summary',
    'clover'
  ],
  coverageThreshold: {
    global: {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95
    }
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 30000,
  maxWorkers: 4,
  verbose: true,
  // Performance optimizations
  cache: true,
  cacheDirectory: '<rootDir>/.jest-cache',
  // Test organization
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/coverage/'
  ],
  // Mock configurations
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@tests/(.*)$': '<rootDir>/tests/$1'
  },
  // Global test settings
  clearMocks: true,
  restoreMocks: true,
  // Performance monitoring
  collectCoverage: false, // Enable only when needed
  bail: false, // Run all tests even if some fail
  // Environment variables for testing
  setupFiles: ['<rootDir>/tests/env.ts']
};