import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { HugeiconsIcon } from '@hugeicons/react'
import { ArrowLeft01Icon, Clock01Icon, StarIcon } from '@hugeicons/core-free-icons'

import { fetchRecipe } from '@/lib/ApiClient'
import { Button } from '@/components/ui/Button'
import { formatDuration } from '@/lib/Formatters'

const FALLBACK_IMAGE = '/images/RecipeFallback.jpg'

export default function RecipeDetails() {
  const { id } = useParams()
  const [status, setStatus] = useState('loading')
  const [recipe, setRecipe] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setStatus('loading')
      setError('')
      try {
        const data = await fetchRecipe(id)
        if (cancelled) return
        setRecipe(data)
        setStatus('ready')
      } catch (err) {
        if (cancelled) return
        setError(err.message)
        setStatus('error')
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [id])

  if (status === 'loading') {
    return (
      <main className="page-shell">
        <p className="scan-status">Loading recipe…</p>
      </main>
    )
  }

  if (status === 'error' || !recipe) {
    return (
      <main className="page-shell">
        <p role="alert" className="scan-error">{error || 'Recipe not found.'}</p>
        <Link to="/"><Button className="proof-button proof-button-quiet">Back home</Button></Link>
      </main>
    )
  }

  return (
    <main className="page-shell">
      <Link to="/" className="recipe-back">
        <HugeiconsIcon icon={ArrowLeft01Icon} /> Back
      </Link>
      <section className="recipe-detail">
        <div className="recipe-detail-image">
          <img src={recipe.image_url || FALLBACK_IMAGE} alt="" onError={(e) => { e.currentTarget.src = FALLBACK_IMAGE }} />
        </div>
        <div className="recipe-detail-body">
          <h1>{recipe.name}</h1>
          <p className="recipe-card-description">{recipe.description || 'No description available.'}</p>
          <div className="recipe-card-meta">
            <span><HugeiconsIcon icon={StarIcon} /> {recipe.rating ?? 'Not rated'}{recipe.review_count != null ? ` (${recipe.review_count})` : ''}</span>
            <span><HugeiconsIcon icon={Clock01Icon} /> {formatDuration(recipe.total_time)}</span>
            <span>{recipe.servings ? `${recipe.servings} servings` : 'Servings not available'}</span>
          </div>

          <h2>Ingredients</h2>
          <ul className="recipe-ingredient-list">
            {recipe.ingredients?.length ? (
              recipe.ingredients.map((item, index) => (
                <li key={index}>
                  {item.quantity ? <strong>{item.quantity}</strong> : null} {item.name}
                </li>
              ))
            ) : (
              <li>Ingredients not available.</li>
            )}
          </ul>

          <h2>Instructions</h2>
          <ol className="recipe-instruction-list">
            {recipe.instructions?.length ? (
              recipe.instructions.map((step, index) => <li key={index}>{step}</li>)
            ) : (
              <li>Instructions not available.</li>
            )}
          </ol>
        </div>
      </section>
    </main>
  )
}
