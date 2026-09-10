import { Outlet } from 'react-router-dom'

import Footer from '@/components/Footer'
import Header from '@/components/Header'

const MainLayout = ({ onUpload }) => {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header onUpload={onUpload} />
      <Outlet />
      <Footer />
    </div>
  )
}

export default MainLayout
