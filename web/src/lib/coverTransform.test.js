import { describe, expect, it } from 'vitest'

import { coverTransform } from '@/lib/coverTransform'

describe('coverTransform', () => {
  it('maps a full-image box to the full display for 1:1', () => {
    const r = coverTransform([0, 0, 1, 1], 100, 100, 200, 200)
    expect(r).toEqual({ x: 0, y: 0, w: 200, h: 200 })
  })

  it('handles 16:9 display with 4:3 image (cover, horizontal crop)', () => {
    // image 400x300, display 1600x900 (16:9). scale = max(4,3)=4, offY=(900-1200)/2=-150
    const r = coverTransform([0, 0, 1, 1], 400, 300, 1600, 900)
    expect(r.x).toBe(0)
    expect(r.y).toBe(-150)
    expect(r.w).toBe(1600)
    expect(r.h).toBe(1200)
  })

  it('handles 9:16 display with 4:3 image (cover, vertical crop)', () => {
    // image 400x300, display 900x1600 (9:16). scale = max(2.25,5.333)=5.333, offX=(900-2133.3)/2=-616.67
    const r = coverTransform([0, 0, 1, 1], 400, 300, 900, 1600)
    expect(r.x).toBeCloseTo(-616.666, 2)
    expect(r.y).toBe(0)
    expect(r.w).toBeCloseTo(2133.333, 2)
    expect(r.h).toBe(1600)
  })

  it('handles 4:3 display with 16:9 image (cover, vertical crop)', () => {
    const r = coverTransform([0.25, 0.25, 0.75, 0.75], 1600, 900, 800, 600)
    // scale = max(0.5,0.6667)=0.6667, offX=(800-1066.67)/2=-133.33, offY=0
    expect(r.x).toBeCloseTo(0.25 * 1600 * 0.6667 - 133.33, 1)
    expect(r.y).toBeCloseTo(0.25 * 900 * 0.6667, 1)
    expect(r.w).toBeCloseTo(0.5 * 1600 * 0.6667, 1)
    expect(r.h).toBeCloseTo(0.5 * 900 * 0.6667, 1)
  })

  it('returns null for invalid inputs', () => {
    expect(coverTransform(null, 100, 100, 100, 100)).toBeNull()
    expect(coverTransform([0, 0, 1, 1], 0, 100, 100, 100)).toBeNull()
    expect(coverTransform([0, 0, 1, 1], 100, 100, 0, 100)).toBeNull()
  })

  it('returns null for degenerate box', () => {
    expect(coverTransform([0.5, 0.5, 0.5, 0.5], 100, 100, 100, 100)).toBeNull()
  })
})
