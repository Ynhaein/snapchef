import { coverTransform } from '@/lib/coverTransform'
import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/Button'

function iou(a, b) {
  const ix1 = Math.max(a[0], b[0])
  const iy1 = Math.max(a[1], b[1])
  const ix2 = Math.min(a[2], b[2])
  const iy2 = Math.min(a[3], b[3])
  const inter = Math.max(0, ix2 - ix1) * Math.max(0, iy2 - iy1)
  const ua = (a[2] - a[0]) * (a[3] - a[1])
  const ub = (b[2] - b[0]) * (b[3] - b[1])
  const union = ua + ub - inter
  return union > 0 ? inter / union : 0
}

export default function CameraView({ videoRef, stream, detections, imageWidth, imageHeight, mirrored, onUse, onIgnore }) {
  const containerRef = useRef(null)
  const [size, setSize] = useState({ w: 0, h: 0 })
  const tracksRef = useRef(new Map())
  const frameCounterRef = useRef(0)
  const [tracks, setTracks] = useState([])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      setSize({ w: el.clientWidth, h: el.clientHeight })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    const video = videoRef.current
    if (!video || !stream) return
    video.srcObject = stream
    video.play().catch(() => {})
  }, [stream, videoRef])

  useEffect(() => {
    frameCounterRef.current += 1
    const fc = frameCounterRef.current
    const prev = [...tracksRef.current.values()]
    const matched = new Set()
    const newTracks = []
    for (const d of detections || []) {
      let bestIdx = -1
      let bestIoU = 0.3
      prev.forEach((t, i) => {
        if (t.label !== d.label || matched.has(i)) return
        const v = iou(t.box, d.box)
        if (v > bestIoU) {
          bestIoU = v
          bestIdx = i
        }
      })
      let trackId
      if (bestIdx >= 0) {
        trackId = prev[bestIdx].trackId
        matched.add(bestIdx)
      } else {
        trackId = `t${fc}-${d.label}-${Math.random().toString(36).slice(2, 6)}`
      }
      const track = {
        trackId,
        label: d.label,
        display_name: d.display_name,
        type: d.type,
        detection_score: d.detection_score,
        status: d.status,
        box: d.box,
        lastSeen: fc,
      }
      tracksRef.current.set(trackId, track)
      newTracks.push(track)
    }
    for (const [id, t] of tracksRef.current) {
      if (fc - t.lastSeen > 2) tracksRef.current.delete(id)
    }
    setTracks(newTracks)
  }, [detections])

  const boxes = tracks
    .map((t) => {
      const r = coverTransform(t.box, imageWidth, imageHeight, size.w, size.h)
      if (!r || r.w < 4 || r.h < 4) return null
      return { ...t, rect: r }
    })
    .filter(Boolean)

  return (
    <>
      <div ref={containerRef} className="camera-stage">
        <video
          ref={videoRef}
          className={`camera-video ${mirrored ? 'is-mirrored' : ''}`}
          playsInline
          muted
          autoPlay
        />
        <svg className="camera-overlay" viewBox={`0 0 ${size.w} ${size.h}`} preserveAspectRatio="none">
          {boxes.map((b) => (
            <rect
              key={b.trackId}
              x={b.rect.x}
              y={b.rect.y}
              width={b.rect.w}
              height={b.rect.h}
              className={`camera-box camera-box-${b.status}`}
            />
          ))}
        </svg>
        {boxes.map((b) => {
          const panelW = Math.min(160, size.w * 0.4)
          let left = b.rect.x + b.rect.w + 8
          if (left + panelW > size.w) left = b.rect.x - panelW - 8
          if (left < 4) left = 4
          let top = b.rect.y
          if (top + 70 > size.h) top = Math.max(4, size.h - 80)
          const displayLeft = mirrored ? size.w - left - panelW : left
          return (
            <div key={'panel-' + b.trackId} className="camera-panel" style={{ left: displayLeft, top, width: panelW }}>
              <p className="camera-panel-title">{b.display_name}</p>
              <p className="camera-panel-meta">Detection Score {Number(b.detection_score).toFixed(2)}</p>
            </div>
          )
        })}
        {boxes.length === 0 && <div className="camera-empty-hint">Looking for ingredients…</div>}
      </div>
      {boxes.length > 0 && (
        <div className="camera-actions">
          {boxes.map((b) => (
            <div key={'act-' + b.trackId} className="camera-action-row">
              <span className="camera-action-label">{b.display_name} ({Number(b.detection_score).toFixed(2)})</span>
              <div className="camera-panel-actions">
                <Button size="sm" className="proof-button proof-button-primary" onClick={() => onUse?.(b.label)}>
                  Use
                </Button>
                <Button size="sm" className="proof-button proof-button-quiet" onClick={() => onIgnore?.(b.label)}>
                  Ignore
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
