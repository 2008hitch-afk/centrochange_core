// Minimal Node declarations used only by the gated Playwright live fixture.
declare const process: { env: Record<string, string | undefined>; cwd(): string }
declare module 'node:fs' {
  export function readFileSync(path: string, encoding: 'utf8'): string
  export function statSync(path: string): { mode: number }
}
declare module 'node:path' {
  export function resolve(...paths: string[]): string
}
