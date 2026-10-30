import { NavLink } from 'react-router-dom'
import { HugeiconsIcon } from '@hugeicons/react'
import { ChefHatIcon, Camera01Icon, ShoppingBasket01Icon, Upload04Icon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'

const TABS = [
  { to: '/', label: 'Home', desc: 'Discover SnapChef', icon: ChefHatIcon },
  { to: '/scan', label: 'Scan', desc: 'Live camera detection', icon: Camera01Icon },
  { to: '/recipes', label: 'Recipes', desc: 'Recommendations', icon: Upload04Icon },
  { to: '/basket', label: 'Basket', desc: 'Your ingredients', icon: ShoppingBasket01Icon },
]

export default function Header({ onUpload }) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a href="#top" className="brand-lockup" aria-label="SnapChef home">
          <span className="brand-mark"><HugeiconsIcon icon={ChefHatIcon} /></span>
          <span className="brand-wordmark">SnapChef</span>
        </a>
        <Button className="proof-button proof-button-primary" size="sm" onClick={onUpload}>
          <HugeiconsIcon icon={Upload04Icon} data-icon="inline-start" />
          Choose photo
        </Button>
      </div>
      <nav className="card-tabs" aria-label="Main navigation">
        {TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.to === '/'} className={({ isActive }) => `card-tab ${isActive ? 'is-active' : ''}`}>
            <HugeiconsIcon icon={tab.icon} />
            <span>{tab.label}</span>
            <small>{tab.desc}</small>
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
