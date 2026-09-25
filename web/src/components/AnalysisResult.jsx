import { HugeiconsIcon } from '@hugeicons/react'
import { Alert02Icon, CheckmarkCircle02Icon } from '@hugeicons/core-free-icons'

import { Progress } from '@/components/ui/Progress'
import { formatFoodName, formatPercent } from '@/lib/Formatters'

export default function AnalysisResult({ prediction }) {
  const known = prediction.is_known
  const StatusIcon = known ? CheckmarkCircle02Icon : Alert02Icon

  return (
    <section aria-live="polite" className={`analysis-board ${known ? 'is-known' : 'is-unknown'}`}>
      <div className="analysis-board-head">
        <h2>{known ? 'We found a match' : 'We could not identify this dish reliably'}</h2>
        <span className={`result-stamp ${known ? 'result-stamp-known' : 'result-stamp-unknown'}`}>
          <HugeiconsIcon icon={StatusIcon} data-icon="inline-start" />
          {known ? 'Match found' : 'Needs another look'}
        </span>
      </div>
      <div className="analysis-board-content">
        {known ? (
          <div className="result-grid">
            <div className="primary-reading">
              <p className="readout-label">Detected food</p>
              <h3 className="food-reading">{formatFoodName(prediction.label)}</h3>
              <div className="confidence-readout">
                <span>Model confidence</span>
                <strong>{formatPercent(prediction.confidence)}</strong>
              </div>
              <Progress className="confidence-progress" value={prediction.confidence * 100} aria-label="Model confidence" />
            </div>
            <CandidateList candidates={prediction.top_candidates} />
          </div>
        ) : (
          <div className="result-grid">
            <div className="unknown-copy-wrap">
              <p className="unknown-copy">The photo may show a food outside SnapChef&apos;s current categories, or the visible details may not be clear enough. Try a well-lit photo with the dish centered in the frame.</p>
            </div>
            <CandidateList candidates={prediction.top_candidates} title="Closest supported matches" />
          </div>
        )}
        <p className="confidence-note">Confidence describes the model&apos;s certainty among its supported categories; it does not guarantee that the dish was identified correctly.</p>
      </div>
    </section>
  )
}

function CandidateList({ candidates = [], title = 'Other possible matches' }) {
  return (
    <div className="candidate-board">
      <div className="candidate-head">
        <p>{title}</p>
        <span>rank / confidence</span>
      </div>
      <div className="candidate-list">
        {candidates.map((candidate, index) => (
          <div key={candidate.label} className="candidate-row">
            <span className="candidate-index">{String(index + 1).padStart(2, '0')}</span>
            <span className="candidate-name">{formatFoodName(candidate.label)}</span>
            <span className="candidate-score">
              <span>{formatPercent(candidate.confidence)}</span>
              <span className="candidate-meter" aria-hidden="true"><span style={{ width: `${Math.max(candidate.confidence * 100, 2)}%` }} /></span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
