import { useState } from 'react'
import { HugeiconsIcon } from '@hugeicons/react'
import { Delete02Icon } from '@hugeicons/core-free-icons'

import RecipeCollection from '@/components/RecipeCollection'
import { Button } from '@/components/ui/Button'
import { recommendRecipes } from '@/lib/ApiClient'

const MAX_INGREDIENTS = 10

export default function IngredientBasket({ ingredients, onChange, onOpenRecipe }) {
  const [value, setValue] = useState('')
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  function addIngredient(event) {
    event.preventDefault()
    const name = value.trim().toLowerCase()
    if (!name || ingredients.includes(name) || ingredients.length >= MAX_INGREDIENTS) return
    onChange([...ingredients, name])
    setValue('')
  }

  function removeIngredient(name) {
    onChange(ingredients.filter((item) => item !== name))
    setResult(null)
    setStatus('idle')
  }

  async function findRecipes() {
    if (!ingredients.length) return
    setStatus('loading')
    setError('')
    try {
      setResult(await recommendRecipes(ingredients))
      setStatus('ready')
    } catch (requestError) {
      setError(requestError.message)
      setStatus('error')
    }
  }

  return (
    <section id="basket" className="basket-section" aria-label="Cook from your ingredients">
      <div className="section-bar">
        <h2>Cook from what you have</h2>
        <span className="section-meta">Manual ingredient basket</span>
      </div>

      <form className="basket-form" onSubmit={addIngredient}>
        <label className="sr-only" htmlFor="basket-input">Add an ingredient</label>
        <input
          id="basket-input"
          className="basket-input"
          value={value}
          maxLength={60}
          placeholder="e.g. apple, egg, tomato"
          onChange={(event) => setValue(event.target.value)}
        />
        <Button type="submit" className="proof-button proof-button-quiet" disabled={!value.trim() || ingredients.length >= MAX_INGREDIENTS}>
          Add
        </Button>
      </form>

      {ingredients.length > 0 && (
        <ul className="basket-chips" aria-label="Selected ingredients">
          {ingredients.map((name) => (
            <li key={name} className="basket-chip">
              {name}
              <button type="button" aria-label={`Remove ${name}`} onClick={() => removeIngredient(name)}>
                <HugeiconsIcon icon={Delete02Icon} />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="basket-actions">
        <Button className="proof-button proof-button-primary" disabled={!ingredients.length || status === 'loading'} onClick={findRecipes}>
          {status === 'loading' ? 'Finding recipes…' : 'Find recipes'}
        </Button>
        <p className="basket-hint">Add up to {MAX_INGREDIENTS} ingredients. Unknown ingredients are reported, not guessed.</p>
      </div>

      {error && <p className="basket-error" role="alert">{error}</p>}
      {result?.unknown?.length > 0 && (
        <p className="basket-hint">No recipe matches for: {result.unknown.join(', ')}</p>
      )}
      {result && status === 'ready' && (
        <RecipeCollection
          foodName={result.ingredients.join(' + ')}
          recipes={result.recommendations}
          onOpenRecipe={onOpenRecipe}
        />
      )}
    </section>
  )
}
