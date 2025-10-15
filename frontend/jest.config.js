module.exports = {
  // setupFilesAfterEnv removed - each test file imports jest-dom directly
  testMatch: [
    '<rootDir>/src/__tests__/**/*.test.{js,jsx}',
    '<rootDir>/src/**/*.test.{js,jsx}'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/src/__tests__/setupTests\\.js$',
    '/src/__tests__/test-utils\\.js$'
  ],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  testEnvironment: 'jsdom',
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/__tests__/**',
    '!src/index.jsx'
  ]
}; 