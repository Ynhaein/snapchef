import { HugeiconsIcon } from '@hugeicons/react'
import { CheckmarkCircle02Icon } from '@hugeicons/core-free-icons'

import { Badge } from '@/components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Progress } from '@/components/ui/Progress'
import { formatFoodName, formatPercent } from '@/lib/Formatters'

export default function AnalysisResult({ prediction }) {
  const known = prediction.is_known

  return (
    <section aria-live="polite" className="scroll-mt-24">
      <Card className="border border-border shadow-sm">
        <CardHeader>
          <div className={`mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider ${known ? 'text-secondary' : 'text-primary'}`}>
            <HugeiconsIcon icon={CheckmarkCircle02Icon} />
            Analysis complete
          </div>
          <CardTitle className="font-heading text-2xl sm:text-3xl">
            {known ? 'We found a match' : 'We could not identify this dish reliably'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {known ? (
            <div className="grid gap-8 md:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Detected food</p>
                <h3 className="mt-2 font-heading text-3xl font-bold">{formatFoodName(prediction.label)}</h3>
                <Badge className="mt-3 bg-secondary text-secondary-foreground">
                  {formatPercent(prediction.confidence)} confidence
                </Badge>
                <Progress className="mt-5" value={prediction.confidence * 100} aria-label="Model confidence" />
              </div>
              <CandidateList candidates={prediction.top_candidates} />
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              <p className="max-w-xl text-sm leading-6 text-muted-foreground">
                The photo may show a food outside SnapChef&apos;s current categories, or the visible details may not be clear enough. Try a well-lit photo with the dish centered in the frame.
              </p>
              <CandidateList candidates={prediction.top_candidates} title="Closest supported matches" />
            </div>
          )}
          <p className="mt-6 border-t border-border pt-4 text-xs leading-5 text-muted-foreground">
            Confidence describes the model&apos;s certainty among its supported categories; it does not guarantee that the dish was identified correctly.
          </p>
        </CardContent>
      </Card>
    </section>
  )
}

function CandidateList({ candidates = [], title = 'Other possible matches' }) {
  return (
    <div>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</p>
      <div className="space-y-2">
        {candidates.map((candidate, index) => (
          <div key={candidate.label} className="flex items-center gap-3 rounded-lg bg-muted px-3 py-2.5">
            <span className="grid size-6 place-items-center rounded-full bg-background text-xs font-bold">{index + 1}</span>
            <span className="flex-1 text-sm font-medium">{formatFoodName(candidate.label)}</span>
            <span className="text-xs font-semibold text-muted-foreground">{formatPercent(candidate.confidence)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
