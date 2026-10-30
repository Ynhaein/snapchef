import { useState } from 'react'

import IngredientBasket from '@/components/IngredientBasket'

export default function BasketPage() {
  const [basket, setBasket] = useState([])
  return (
    <main className="page-shell">
      <h1 className="page-title">Ingredient basket</h1>
      <p className="page-lede">Add ingredients manually or confirm detections from the scanner.</p>
      <IngredientBasket ingredients={basket} onChange={setBasket} onOpenRecipe={() => {}} />
    </main>
  )
}
