import { readFile } from 'node:fs/promises';
import { transform } from 'esbuild';

export async function load(url, context, nextLoad) {
  if (!url.endsWith('.jsx')) return nextLoad(url, context);
  const source = await readFile(new URL(url), 'utf8');
  const result = await transform(source, { loader: 'jsx', jsx: 'automatic', format: 'esm' });
  return { format: 'module', source: result.code, shortCircuit: true };
}
