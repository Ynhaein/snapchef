import { HugeiconsIcon } from '@hugeicons/react'
import { ChefHatIcon } from '@hugeicons/core-free-icons'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-primary">
          <p className="footer-brand">
            <span className="brand-mark"><HugeiconsIcon icon={ChefHatIcon} /></span>
            SnapChef
          </p>
          <p className="footer-copy">Practical ideas from a single food photo.</p>
          <p className="footer-copy">SnapChef currently recognizes 10 food categories. Predictions and recipe matches may not always be accurate.</p>
        </div>
        <p className="footer-attribution">Model images are based on Food-101 data.<br />Recipe information is based on the Food.com Recipes and Reviews dataset.</p>
      </div>
    </footer>
  )
}
