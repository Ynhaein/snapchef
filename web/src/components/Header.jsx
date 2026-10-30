import { HugeiconsIcon } from '@hugeicons/react'
import { ChefHatIcon, Upload04Icon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'

export default function Header({ onUpload }) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a href="#top" className="brand-lockup" aria-label="SnapChef home">
          <span className="brand-mark"><HugeiconsIcon icon={ChefHatIcon} /></span>
          <span className="brand-wordmark">SnapChef</span>
        </a>
        <p className="header-context" aria-label="SnapChef workflow">photo <strong>→</strong> reading <strong>→</strong> recipe</p>
        <nav className="header-nav" aria-label="Main navigation">
          <a href="#analyze">Analyze</a>
          <a href="/scan">Scan</a>
          <a href="#supported-foods">Supported foods</a>
        </nav>
        <Button className="proof-button proof-button-primary" size="sm" onClick={onUpload}>
          <HugeiconsIcon icon={Upload04Icon} data-icon="inline-start" />
          Choose photo
        </Button>
      </div>
    </header>
  )
}
