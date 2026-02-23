/// <reference types="vite/client" />
import { ViteMappedEnv } from './utils/env';

interface ImportMetaEnv extends ViteMappedEnv {
  readonly DEV: boolean;
  readonly PROD: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
