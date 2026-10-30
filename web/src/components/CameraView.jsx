import { useEffect, useRef, useState } from 'react'
import { HugeiconsIcon } from '@hugeicons/react'
import { Cancel01Icon, CheckmarkCircle02Icon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'

function coverTransform(box, imgW, imgH, dispW, dispH) {
  if (!imgW || !imgH || !dispW || !dispH) return null
  const scale = Math.max(dispW / imgW, dispH / imgH)
  const offX = (dispW - imgW * scale) / 2
  const offY = (dispH - imgH * scale) / 2
  return {
    x: box[0] * imgW * scale + offX,
    y: box[1] * imgH * scale + offY,
    w: (box[2] - box[0]) * imgW * scale,
    h: (box[3] - box[1]) * imgH * scale,
  }
}

export default function CameraView({ videoRef, detections, imageWidth, imageHeight, mirrored, onUse, onIgnore }) {
  const containerRef = useRef(null)
  const [size, setSize] = useState({ w: 0, h: 0 })

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      setSize({ w: el.clientWidth, h: el.clientHeight })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const boxes = (detections || [])
    .map((d) => {
      const r = coverTransform(d.box, imageWidth, imageHeight, size.w, size.h)
      if (!r || r.w < 4 || r.h < 4) return null
      return { ...d, rect: r }
    })
    .filter(Boolean)

  return (
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
            key={b.label + b.rect.x.toFixed(0)}
            x={b.rect.x}
            y={b.rect.y}
            width={b.rect.w}
            height={b.rect.h}
            className={`camera-box camera-box-${b.status}`}
          />
        ))}
      </svg>
      {boxes.map((b) => {
        // panel position: prefer top-right of box, clamped inside container
        const panelW = 160
        let left = b.rect.x + b.rect.w + 8
        if (left + panelW > size.w) left = b.rect.x - panelW - 8
        if (left < 4) left = 4
        let top = b.rect.y
        if (top + 110 > size.h) top = Math.max(4, size.h - 120)
        const displayLeft = mirrored ? size.w - left - panelW : left
        return (
          <div key={'panel-' + b.label + b.rect.x.toFixed(0)} className="camera-panel" style={{ left: displayLeft, top }}>
            <p className="camera-panel-title">{b.display_name}</p>
            <p className="camera-panel-meta">{b.type || 'ingredient'} · Detection Score {Number(b.detection_score).toFixed(2)}</p>
            <div className="camera-panel-actions">
              <Button size="sm" className="proof-button proof-button-primary" onClick={() => onUse?.(b.label)}>
                <HugeiconsIcon icon={CheckmarkCircle02Icon} /> Use
              </Button>
              <Button size="sm" className="proof-button proof-button-quiet" onClick={() => onIgnore?.(b.label)}>
                <HugeiconsIcon icon={Cancel01Icon} /> Ignore
              </Button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
