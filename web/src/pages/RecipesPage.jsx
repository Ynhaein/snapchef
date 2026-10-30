import { useState } from 'react'

import IngredientBasket from '@/components/IngredientBasket'

export default function RecipesPage() {
  const [basket, setBasket] = useState([])
  return (
    <main className="page-shell">
      <h1 className="page-title">Recipe recommendations</h1>
      <p className="page-lede">Confirm ingredients from your basket to get matching recipes.</p>
      <IngredientBasket ingredients={basket} onChange={setBasket} onOpenRecipe={() => {}} />
    </main>
  )
}
