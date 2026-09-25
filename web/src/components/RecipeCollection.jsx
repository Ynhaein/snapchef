import RecipeCard from '@/components/RecipeCard'
import { formatFoodName } from '@/lib/Formatters'

export default function RecipeCollection({ foodName, recipes, onOpenRecipe }) {
  return (
    <section id="recipes" className="workflow-section">
      <div className="section-bar recipe-heading">
        <h2>Recipes for {formatFoodName(foodName)}</h2>
        <span className="recipe-count">{recipes.length} recipes found</span>
      </div>
      {recipes.length ? (
        <div className="recipe-grid">
          {recipes.map((recipe) => <RecipeCard key={recipe.id ?? recipe.name} recipe={recipe} onOpen={onOpenRecipe} />)}
        </div>
      ) : (
        <div className="recipe-empty">
          <h3>No matching recipes found</h3>
          <p>Try another image or check a different supported food.</p>
        </div>
      )}
    </section>
  )
}
