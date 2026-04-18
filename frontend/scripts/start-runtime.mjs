import { cpSync, existsSync, mkdirSync, rmSync, statSync } from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

const appRoot = path.resolve(import.meta.dirname, '..');
const bundledDistDir = path.join(appRoot, 'dist');
const assetRoot = process.env.FRONTEND_ASSET_ROOT || '/app/runtime-assets';
const currentDistDir = path.join(assetRoot, 'current');
const previousDistDir = path.join(assetRoot, 'previous');
const serverEntrypoint = path.join(appRoot, 'server', 'index.mjs');

function emitLog(level, message, extra = {}) {
  process.stdout.write(
    `${JSON.stringify({
      timestamp: new Date().toISOString(),
      level,
      logger: 'frontend.runtime',
      module: 'start-runtime',
      message,
      environment:
        process.env.ENVIRONMENT ||
        process.env.VITE_ENVIRONMENT ||
        process.env.NODE_ENV ||
        'development',
      ...extra,
    })}\n`
  );
}

function copyDirectory(sourceDir, targetDir) {
  cpSync(sourceDir, targetDir, {
    dereference: true,
    errorOnExist: false,
    force: true,
    preserveTimestamps: true,
    recursive: true,
  });
}

function prepareRuntimeAssets() {
  if (!existsSync(bundledDistDir) || !statSync(bundledDistDir).isDirectory()) {
    emitLog(
      'WARN',
      'Skipping runtime asset preparation because dist is missing'
    );
    return false;
  }

  try {
    mkdirSync(assetRoot, { recursive: true });

    if (existsSync(previousDistDir)) {
      rmSync(previousDistDir, { force: true, recursive: true });
    }

    if (existsSync(currentDistDir)) {
      copyDirectory(currentDistDir, previousDistDir);
      rmSync(currentDistDir, { force: true, recursive: true });
    }

    copyDirectory(bundledDistDir, currentDistDir);

    emitLog('INFO', 'Prepared runtime frontend assets', {
      asset_root: assetRoot,
      current_dir: currentDistDir,
      previous_dir: previousDistDir,
    });
    return true;
  } catch (error) {
    emitLog(
      'WARN',
      'Runtime asset preparation failed; serving bundled assets only',
      {
        asset_root: assetRoot,
        error: error instanceof Error ? error.message : String(error),
      }
    );
    return false;
  }
}

function startServer(useRuntimeAssets) {
  const child = spawn(process.execPath, [serverEntrypoint], {
    env: {
      ...process.env,
      ...(useRuntimeAssets ? { FRONTEND_ASSET_ROOT: assetRoot } : {}),
    },
    stdio: 'inherit',
  });

  child.on('exit', code => {
    process.exit(code ?? 0);
  });

  child.on('error', error => {
    emitLog('ERROR', 'Failed to launch frontend runtime server', {
      error: error instanceof Error ? error.message : String(error),
    });
    process.exit(1);
  });
}

const useRuntimeAssets = prepareRuntimeAssets();
startServer(useRuntimeAssets);
