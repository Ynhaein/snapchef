import { useRef, useState } from 'react'
import { HugeiconsIcon } from '@hugeicons/react'
import { Camera01Icon, Cancel01Icon, SwitchCameraIcon } from '@hugeicons/core-free-icons'

import CameraView from '@/components/CameraView'
import DetectedItems from '@/components/DetectedItems'
import IngredientBasket from '@/components/IngredientBasket'
import { Button } from '@/components/ui/Button'
import { useCamera } from '@/hooks/useCamera'
import { useDetectionPolling } from '@/hooks/useDetectionPolling'

export default function ScanPage() {
  const { videoRef, status, error, devices, deviceId, start, stop, switchCamera } = useCamera()
  const canvasRef = useRef(null)
  const [mirrored, setMirrored] = useState(false)
  const [detections, setDetections] = useState([])
  const [imageDims, setImageDims] = useState({ w: 0, h: 0 })
  const [basket, setBasket] = useState([])
  const { isAnalyzing, error: detectionError } = useDetectionPolling(
    videoRef,
    canvasRef,
    status === 'active',
    900,
    (result) => {
      setDetections(result?.detected_items || [])
      setImageDims({ w: result?.image_width || 0, h: result?.image_height || 0 })
    },
  )

  function handleUse(label) {
    setBasket((current) => (current.includes(label) ? current : [...current, label]))
  }

  function handleIgnore(label) {
    setDetections((current) => current.filter((item) => item.label !== label))
  }

  return (
    <main className="page-shell">
      <section className="hero-band">
        <div className="hero-copy">
          <h1>Scan ingredients in real time.</h1>
          <p className="hero-lede">
            Point your camera at food or ingredients. SnapChef detects candidates and lets you confirm them before adding to your basket.
          </p>
        </div>
      </section>

      <section className="scan-workspace">
        {status === 'idle' && (
          <div className="scan-intro">
            <h2>Live camera detection</h2>
            <p>
              SnapChef uses your device camera to suggest ingredient candidates. Detection scores are raw model scores, not
              probabilities. The AI may miss ingredients — add them manually if needed.
            </p>
            <Button className="proof-button proof-button-primary" size="lg" onClick={() => start()}>
              <HugeiconsIcon icon={Camera01Icon} data-icon="inline-start" /> Start camera
            </Button>
          </div>
        )}

        {status === 'requesting' && <p className="scan-status">Requesting camera access…</p>}

        {status === 'error' && (
          <div className="scan-error" role="alert">
            <p>{error}</p>
            <Button className="proof-button proof-button-quiet" onClick={() => start()}>Try again</Button>
          </div>
        )}

        {status === 'active' && (
          <>
            <div className="scan-toolbar">
              <span className="scan-live">● Live</span>
              {isAnalyzing && <span className="scan-analyzing">Analyzing…</span>}
              {detectionError && <span className="scan-error-inline">{detectionError}</span>}
              <div className="scan-toolbar-actions">
                {devices.length > 1 && (
                  <Button
                    className="proof-button proof-button-quiet"
                    size="sm"
                    onClick={() => {
                      const idx = devices.findIndex((d) => d.deviceId === deviceId)
                      const next = devices[(idx + 1) % devices.length]
                      switchCamera(next.deviceId)
                    }}
                  >
                    <HugeiconsIcon icon={SwitchCameraIcon} /> Switch
                  </Button>
                )}
                <Button
                  className="proof-button proof-button-quiet"
                  size="sm"
                  onClick={() => setMirrored((v) => !v)}
                >
                  Mirror {mirrored ? 'on' : 'off'}
                </Button>
                <Button className="proof-button proof-button-danger" size="sm" onClick={stop}>
                  <HugeiconsIcon icon={Cancel01Icon} /> Stop
                </Button>
              </div>
            </div>
            <CameraView
              videoRef={videoRef}
              detections={detections}
              imageWidth={imageDims.w}
              imageHeight={imageDims.h}
              mirrored={mirrored}
              onUse={handleUse}
              onIgnore={handleIgnore}
            />
            <canvas ref={canvasRef} className="sr-only" aria-hidden="true" />
            <DetectedItems items={detections} onConfirm={handleUse} />
          </>
        )}

        <IngredientBasket ingredients={basket} onChange={setBasket} onOpenRecipe={() => {}} />
      </section>
    </main>
  )
}
