export default {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/frontend'],
  testMatch: [
    '<rootDir>/frontend/test/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/frontend/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/frontend/src/**/*.{test,spec}.{js,jsx,ts,tsx}'
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/frontend/src/$1'
  }
};
