/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly mode: string
  readonly base: string
}

declare global {
  interface ImportMetaEnv extends ImportMetaEnv {
    // Additional environment variables here
  }
}

export {}
