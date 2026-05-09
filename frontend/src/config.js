export const config = {
  baseUrl: import.meta.env.VITE_BASE_URL || 'http://localhost:5000/api',
  testdata: import.meta.env.VITE_TEST_DATA === 'true' || false,
};
