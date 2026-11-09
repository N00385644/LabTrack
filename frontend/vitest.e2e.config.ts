import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    include: ['e2e/**/*.e2e.test.ts'],
    testTimeout: 90_000,
    hookTimeout: 120_000,
    fileParallelism: false,
    reporters: ['verbose', 'junit'],
    outputFile: {
      junit: './e2e/reports/junit.xml',
    },
  },
});
