import { Link } from 'react-router-dom'

import IngredientBasket from '@/components/IngredientBasket'
import { Button } from '@/components/ui/Button'

export default function BasketPage({ basket = [], setBasket = () => {} }) {
  return (
    <main className="page-shell">
      <h1 className="page-title">Basket &amp; recipes</h1>
      <p className="page-lede">
        Ingredients you confirm from the scanner or add manually appear here. Find matching recipes once your basket is ready.
      </p>
      {basket.length === 0 && (
        <div className="basket-empty">
          <p>Your basket is empty.</p>
          <p className="basket-hint">Scan ingredients with your camera or add them manually below.</p>
          <Link to="/scan">
            <Button className="proof-button proof-button-primary">Go to scanner</Button>
          </Link>
        </div>
      )}
      <IngredientBasket ingredients={basket} onChange={setBasket} onOpenRecipe={() => {}} />
    </main>
  )
}
