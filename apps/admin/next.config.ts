import type { NextConfig } from 'next';
import { fileURLToPath } from 'url';

const nextConfig: NextConfig = {
  outputFileTracingRoot: fileURLToPath(new URL('../../', import.meta.url)),
};

export default nextConfig;
