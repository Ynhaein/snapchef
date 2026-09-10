import { HugeiconsIcon } from '@hugeicons/react'
import { ChefHatIcon } from '@hugeicons/core-free-icons'

export default function Footer() {
  return (
    <footer className="border-t border-border bg-muted/60">
      <div className="mx-auto grid max-w-6xl gap-4 px-4 py-10 text-xs text-muted-foreground sm:px-6 md:grid-cols-[1fr_auto]">
        <div>
          <p className="flex items-center gap-2 font-heading text-lg font-bold text-foreground">
            <HugeiconsIcon icon={ChefHatIcon} className="text-primary" /> SnapChef
          </p>
          <p className="mt-2 text-foreground">SnapChef helps turn food inspiration into practical recipe ideas.</p>
          <p className="mt-1">SnapChef currently recognizes 10 food categories. Predictions and recipe matches may not always be accurate.</p>
        </div>
        <p className="md:text-right">Model images are based on Food-101 data.<br />Recipe information is based on the Food.com Recipes and Reviews dataset.</p>
      </div>
    </footer>
  )
}
