export default function AnalysisSkeleton() {
  return (
    <section aria-live="polite" aria-busy="true" className="analysis-board skeleton-board">
      <div className="section-bar">
        <h2>Reading your dish</h2>
        <span className="section-meta">In progress</span>
      </div>
      <div className="skeleton-layout">
        <div className="skeleton-readout">
          <span className="skeleton-line short" />
          <span className="skeleton-line title" />
          <span className="skeleton-line meter" />
        </div>
        <div className="skeleton-candidates">
          <span className="skeleton-candidate" />
          <span className="skeleton-candidate" />
          <span className="skeleton-candidate" />
        </div>
      </div>
      <p className="skeleton-message">Analyzing your dish…</p>
      <p className="skeleton-note">Comparing the photo with SnapChef&apos;s supported food categories.</p>
    </section>
  )
}
