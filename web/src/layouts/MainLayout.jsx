import { NavLink, Outlet } from 'react-router-dom'
import { HugeiconsIcon } from '@hugeicons/react'
import { Camera01Icon, Home01Icon, ShoppingBasket01Icon, ChefHatIcon } from '@hugeicons/core-free-icons'

import Footer from '@/components/Footer'
import Header from '@/components/Header'

const BOTTOM_TABS = [
  { to: '/', label: 'Home', icon: Home01Icon, end: true },
  { to: '/scan', label: 'Scan', icon: Camera01Icon },
  { to: '/recipes', label: 'Recipes', icon: ChefHatIcon },
  { to: '/basket', label: 'Basket', icon: ShoppingBasket01Icon },
]

const MainLayout = ({ onUpload }) => {
  return (
    <div className="site-shell">
      <Header onUpload={onUpload} />
      <div className="site-main">
        <Outlet />
      </div>
      <Footer />
      <nav className="bottom-nav" aria-label="Mobile navigation">
        {BOTTOM_TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.end} className={({ isActive }) => `bottom-nav-item ${isActive ? 'is-active' : ''}`}>
            <HugeiconsIcon icon={tab.icon} />
            <span>{tab.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

export default MainLayout
