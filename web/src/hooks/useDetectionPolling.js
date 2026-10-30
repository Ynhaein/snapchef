import { useCallback, useEffect, useRef, useState } from 'react'

import { detectFood } from '@/lib/ApiClient'

// Default interval; adaptive backoff on failure.
const DEFAULT_INTERVAL = 900
const MAX_INTERVAL = 3000

export function useDetectionPolling(videoRef, canvasRef, active, intervalMs = DEFAULT_INTERVAL, onResult) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const inFlightRef = useRef(false)
  const aliveRef = useRef(true)
  const timerRef = useRef(null)
  const latestIdRef = useRef(0)
  const intervalRef = useRef(intervalMs)

  const captureFrame = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || video.readyState < 2) return null
    const w = Math.min(video.videoWidth || 640, 640)
    const h = Math.round((video.videoHeight || 480) * (w / (video.videoWidth || 640)))
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, w, h)
    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.7)
    })
  }, [videoRef, canvasRef])

  const tickRef = useRef(null)

  const tick = useCallback(async () => {
    if (!aliveRef.current || !active) return
    if (inFlightRef.current) {
      timerRef.current = setTimeout(() => tickRef.current?.(), intervalRef.current)
      return
    }
    inFlightRef.current = true
    setIsAnalyzing(true)
    const requestId = ++latestIdRef.current
    try {
      const blob = await captureFrame()
      if (!blob || !aliveRef.current) return
      const result = await detectFood(blob)
      if (requestId !== latestIdRef.current) return // stale
      onResult?.(result, requestId)
      setError('')
    } catch (err) {
      if (requestId === latestIdRef.current) {
        setError(err?.message || 'Detection failed.')
        intervalRef.current = Math.min(MAX_INTERVAL, Math.round(intervalRef.current * 1.5))
      }
    } finally {
      inFlightRef.current = false
      setIsAnalyzing(false)
      if (aliveRef.current && active) {
        timerRef.current = setTimeout(() => tickRef.current?.(), intervalRef.current)
      }
    }
  }, [active, captureFrame, onResult])

  useEffect(() => {
    tickRef.current = tick
  }, [tick])

  useEffect(() => {
    aliveRef.current = true
    if (active) {
      timerRef.current = setTimeout(() => tickRef.current?.(), 300)
    }
    return () => {
      aliveRef.current = false
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [active, tick])

  return { isAnalyzing, error }
}
