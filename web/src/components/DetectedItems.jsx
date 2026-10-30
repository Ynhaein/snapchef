import { HugeiconsIcon } from '@hugeicons/react'
import { CheckmarkCircle02Icon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'

export default function DetectedItems({ items, onConfirm }) {
  if (!items?.length) return null

  return (
    <section className="workflow-section" aria-label="Detected ingredients">
      <div className="section-bar">
        <h2>Detected ingredients</h2>
        <span className="section-meta">Detection Score is a raw model score, not a probability.</span>
      </div>
      <ul className="detected-chips">
        {items.map((item) => (
          <li key={item.label} className={`detected-chip detected-chip-${item.status}`}>
            <span>
              {item.display_name}
              <small>Detection Score {Number(item.detection_score).toFixed(2)}</small>
            </span>
            {item.status === 'uncertain' && (
              <Button size="sm" className="proof-button proof-button-quiet" onClick={() => onConfirm?.(item.label)}>
                <HugeiconsIcon icon={CheckmarkCircle02Icon} />
                Use
              </Button>
            )}
          </li>
        ))}
      </ul>
      <p className="basket-hint">
        Detection is experimental and may miss ingredients that are actually present. Confirm a candidate with Use, or add it manually in the basket below.
      </p>
    </section>
  )
}
