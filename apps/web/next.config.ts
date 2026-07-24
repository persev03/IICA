import type { NextConfig } from 'next';
import { fileURLToPath } from 'url';

const configuredBasePath = process.env.NEXT_PUBLIC_BASE_PATH?.replace(/\/$/, '');

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
  transpilePackages: ['@iica/ui'],
  outputFileTracingRoot: fileURLToPath(new URL('../../', import.meta.url)),
  basePath: configuredBasePath || undefined,
  assetPrefix: configuredBasePath ? `${configuredBasePath}/` : undefined,
};

export default nextConfig;
