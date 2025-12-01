/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_TRAIN_STATUS_POLL_INTERVAL: string;
  readonly VITE_TRAIN_LIST_POLL_INTERVAL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
