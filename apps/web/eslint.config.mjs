import { FlatCompat } from '@eslint/eslintrc';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const currentFilePath = fileURLToPath(import.meta.url);
const baseDirectory = dirname(currentFilePath);
const compat = new FlatCompat({ baseDirectory });

const eslintConfig = [
  { ignores: ['.next/**', 'next-env.d.ts', 'node_modules/**'] },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
];

export default eslintConfig;
