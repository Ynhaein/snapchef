import { HugeiconsIcon } from '@hugeicons/react'
import { Clock01Icon, StarIcon } from '@hugeicons/core-free-icons'

import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { formatDuration } from '@/lib/Formatters'

const FALLBACK_IMAGE = '/images/RecipeFallback.jpg'

export default function RecipeCard({ recipe, onOpen }) {
  return (
    <article className="recipe-card">
      <div className="recipe-image">
        <img
          src={recipe.image_url || FALLBACK_IMAGE}
          alt=""
          onError={(event) => { event.currentTarget.src = FALLBACK_IMAGE }}
        />
        <span className="recipe-image-label">Recipe match</span>
      </div>
      <div className="recipe-card-body">
        <div className="recipe-card-meta">
          <span><HugeiconsIcon icon={StarIcon} /> {recipe.rating ?? 'Not rated'}{recipe.review_count != null ? ` (${recipe.review_count})` : ''}</span>
          <span><HugeiconsIcon icon={Clock01Icon} /> {formatDuration(recipe.total_time)}</span>
        </div>
        <h3 className="recipe-card-title"><Link to={`/recipes/${recipe.id}`}>{recipe.name}</Link></h3>
        <p className="recipe-card-description">{recipe.description || 'No description available.'}</p>
        <div className="recipe-card-footer">
          <small>{recipe.servings ? `${recipe.servings} servings` : 'Recipe details on open'}</small>
          <Button className="proof-button proof-button-primary recipe-card-button" size="sm" onClick={() => onOpen(recipe)}>
            View recipe
          </Button>
        </div>
      </div>
    </article>
  )
}
