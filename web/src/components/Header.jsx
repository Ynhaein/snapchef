import { HugeiconsIcon } from '@hugeicons/react'
import { ChefHatIcon, Upload04Icon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'

export default function Header({ onUpload }) {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <a href="#top" className="flex items-center gap-2.5" aria-label="SnapChef home">
          <span className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground">
            <HugeiconsIcon icon={ChefHatIcon} strokeWidth={2} />
          </span>
          <span className="font-heading text-2xl font-bold">SnapChef</span>
        </a>
        <nav className="hidden items-center gap-7 text-sm font-medium md:flex" aria-label="Main navigation">
          <a className="text-primary" href="#analyze">Analyze</a>
          <a className="text-muted-foreground hover:text-foreground" href="#supported-foods">Supported foods</a>
        </nav>
        <Button size="lg" onClick={onUpload}>
          <HugeiconsIcon icon={Upload04Icon} data-icon="inline-start" />
          Upload photo
        </Button>
      </div>
    </header>
  )
}
