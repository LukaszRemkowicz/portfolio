// frontend/scripts/ssr-smoke-test.ts
//
// Real SSR import smoke test.
// Run with: npm run smoke:ssr
//
// Uses tsx to import actual TypeScript project modules in a plain Node
// context — no jsdom, no Vite, no browser globals.
// If any import crashes on window/document/localStorage, this script fails.

// Set before any project imports so constants.ts doesn't emit 'not set' warnings
process.env['API_URL'] = 'http://smoke-test-placeholder';

import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

let passed = 0;
let failed = 0;

async function check(label: string, fn: () => Promise<void> | void) {
  try {
    await fn();
    console.log(`  ✅  ${label}`);
    passed++;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`  ❌  ${label}`);
    console.error(`      ${msg}`);
    failed++;
  }
}

console.log('\nSSR Node Import Smoke Test\n');

// 1. env.shared — must import and resolve process.env without crashing
await check('env.shared: imports cleanly in Node', async () => {
  const { getSharedEnv } = await import('../src/utils/env.shared');
  process.env['API_URL'] = 'http://ssr-smoke-test';
  const val = getSharedEnv('API_URL', '');
  if (val !== 'http://ssr-smoke-test')
    throw new Error(`Expected http://ssr-smoke-test, got: ${val}`);
  process.env['API_URL'] = 'http://smoke-test-placeholder';
});

await check('env.shared: returns fallback when key is missing', async () => {
  const { getSharedEnv } = await import('../src/utils/env.shared');
  const val = getSharedEnv('__NONEXISTENT_KEY__', 'default-fallback');
  if (val !== 'default-fallback') throw new Error(`Got: ${val}`);
});

// 2. api/routes — constants-only module, must be safe
await check('api/routes: imports cleanly in Node', async () => {
  await import('../src/api/routes');
});

// 3. api/api — must NOT import browser i18n anymore
await check('api/api: imports without browser globals', async () => {
  // If this crashes with "window is not defined" or similar, the fix regressed
  const mod = await import('../src/api/api');
  if (typeof mod.api === 'undefined') throw new Error('api export missing');
  if (typeof mod.setLanguageGetter !== 'function')
    throw new Error('setLanguageGetter export missing');
});

// 4. i18n.server — per-request factory must work in Node
await check('i18n.server: createServerI18n() works in Node', async () => {
  const { createServerI18n } = await import('../src/i18n.server');
  const instance = await createServerI18n('pl,en;q=0.9');
  if (instance.language !== 'pl')
    throw new Error(`Expected pl, got: ${instance.language}`);
});

await check('i18n.server: falls back to en for unknown language', async () => {
  const { createServerI18n } = await import('../src/i18n.server');
  const instance = await createServerI18n('xx-XX');
  if (instance.language !== 'en')
    throw new Error(`Expected en, got: ${instance.language}`);
});

// 5. api/services — the shared data fetch layer must not drag in browser globals
await check('api/services: imports cleanly in Node', async () => {
  await import('../src/api/services');
});

// 6. entry-server — verify the compiled SSR bundle renders in Node
await check(
  'entry-server bundle: render("/") returns HTML in Node',
  async () => {
    execFileSync('npm', ['run', 'build:ssr'], {
      stdio: 'pipe',
      cwd: resolve(import.meta.dirname, '..'),
    });

    const bundleUrl = pathToFileURL(
      resolve(import.meta.dirname, '../dist/server/entry-server.js')
    ).href;
    const { render } = await import(bundleUrl);
    const result = await render('/');
    if (!result.html || typeof result.html !== 'string') {
      throw new Error('render() did not return HTML');
    }
    if (
      !result.html.includes('Loading') &&
      !result.html.includes('root') &&
      result.html.length < 50
    ) {
      throw new Error(
        `Unexpectedly small render output: ${result.html.length}`
      );
    }
  }
);

console.log(`\n${passed} passed, ${failed} failed\n`);
if (failed > 0) process.exit(1);
