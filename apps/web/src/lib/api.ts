import type { District } from './types'

// Same-origin in dev via the Vite proxy (see vite.config.ts).
export async function getDistrict(): Promise<District> {
  const res = await fetch('/api/district')
  if (!res.ok) throw new Error(`GET /api/district failed: ${res.status}`)
  return res.json()
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch('/health')
  if (!res.ok) throw new Error(`GET /health failed: ${res.status}`)
  return res.json()
}
