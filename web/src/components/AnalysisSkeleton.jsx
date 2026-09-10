import { Card, CardContent } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'

export default function AnalysisSkeleton() {
  return (
    <Card aria-live="polite" aria-busy="true" className="border border-border">
      <CardContent className="grid gap-6 p-6 md:grid-cols-2">
        <div className="space-y-4">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-6 w-36" />
        </div>
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
        <p className="text-sm font-medium text-muted-foreground">Analyzing your dish…</p>
      </CardContent>
    </Card>
  )
}
