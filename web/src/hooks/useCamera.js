import { useCallback, useEffect, useRef, useState } from 'react'

export function useCamera() {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [status, setStatus] = useState('idle') // idle | requesting | active | error
  const [error, setError] = useState('')
  const [devices, setDevices] = useState([])
  const [deviceId, setDeviceId] = useState('')
  const [stream, setStream] = useState(null)

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setStream(null)
    if (videoRef.current) videoRef.current.srcObject = null
    setStatus('idle')
  }, [])

  const start = useCallback(async (preferredDeviceId) => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Camera API is not supported in this browser.')
      setStatus('error')
      return
    }
    setStatus('requesting')
    setError('')
    try {
      const constraints = {
        video: preferredDeviceId
          ? { deviceId: { exact: preferredDeviceId } }
          : { facingMode: { ideal: 'environment' } },
        audio: false,
      }
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream
      setStream(stream)
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
      }
      const track = stream.getVideoTracks()[0]
      setDeviceId(track.getSettings().deviceId || preferredDeviceId || '')
      setStatus('active')

      // enumerate after grant
      try {
        const all = await navigator.mediaDevices.enumerateDevices()
        setDevices(all.filter((d) => d.kind === 'videoinput'))
      } catch {
        /* ignore */
      }
    } catch (err) {
      const name = err?.name || 'Error'
      const messages = {
        NotAllowedError: 'Camera permission was denied. Enable it in browser settings.',
        NotFoundError: 'No camera was found on this device.',
        NotReadableError: 'Camera is in use by another app.',
        OverconstrainedError: 'The selected camera is not available.',
        TypeError: 'Camera API is not supported in this browser.',
      }
      setError(messages[name] || 'Could not start the camera.')
      setStatus('error')
    }
  }, [])

  const switchCamera = useCallback(
    async (nextId) => {
      stop()
      await start(nextId)
    },
    [stop, start],
  )

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
      setStream(null)
    }
  }, [])

  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'hidden') stop()
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [stop])

  return { videoRef, status, error, devices, deviceId, stream, start, stop, switchCamera }
}
