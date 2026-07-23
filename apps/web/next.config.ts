import type { NextConfig } from 'next';
import { fileURLToPath } from 'url';

const isGitHubPagesBuild = process.env.GITHUB_ACTIONS === 'true';

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
  transpilePackages: ['@iica/ui'],
  outputFileTracingRoot: fileURLToPath(new URL('../../', import.meta.url)),
  basePath: isGitHubPagesBuild ? '/IICA' : undefined,
  assetPrefix: isGitHubPagesBuild ? '/IICA/' : undefined,
};

export default nextConfig;
