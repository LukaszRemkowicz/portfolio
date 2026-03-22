import { spawn, spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const rootDir = resolve(import.meta.dirname, '..');

const build = spawnSync('npm', ['run', 'build:ssr'], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: process.platform === 'win32',
});

if (build.status !== 0) {
  process.exit(build.status ?? 1);
}

const injectMetadata = spawnSync(
  'node',
  ['./scripts/inject-static-metadata.mjs'],
  {
    cwd: rootDir,
    stdio: 'inherit',
    shell: process.platform === 'win32',
    env: process.env,
  }
);

if (injectMetadata.status !== 0) {
  process.exit(injectMetadata.status ?? 1);
}

const serverProcess = spawn('node', [resolve(rootDir, 'server/index.mjs')], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: process.platform === 'win32',
  env: process.env,
});

const forwardSignal = signal => {
  if (!serverProcess.killed) {
    serverProcess.kill(signal);
  }
};

process.on('exit', () => {
  forwardSignal('SIGTERM');
});
process.on('SIGINT', () => forwardSignal('SIGINT'));
process.on('SIGTERM', () => forwardSignal('SIGTERM'));

serverProcess.on('exit', code => {
  process.exit(code ?? 0);
});
