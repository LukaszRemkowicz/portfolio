// frontend/src/i18n.ts
//
// Re-export barrel.
// - Client build: imports the browser singleton from i18n.client.ts
// - Server build: entry-server.tsx imports i18n.server.ts directly
//
// Do not add any browser-only code here.
export { default } from './i18n.client';
