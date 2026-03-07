import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  eslint: {
    // Linting is enforced in CI via `npm run lint` / `npm run check`.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
