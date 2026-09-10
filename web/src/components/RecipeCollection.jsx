import RecipeCard from '@/components/RecipeCard'
import { formatFoodName } from '@/lib/Formatters'

export default function RecipeCollection({ foodName, recipes, onOpenRecipe }) {
  return (
    <section id="recipes" className="scroll-mt-24">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-heading text-3xl font-bold">Recipes for {formatFoodName(foodName)}</h2>
          <p className="mt-1 text-sm text-muted-foreground">Explore up to five recipes related to the detected dish.</p>
        </div>
        <span className="text-xs font-medium text-muted-foreground">{recipes.length} recipes found</span>
      </div>
      {recipes.length ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {recipes.map((recipe) => <RecipeCard key={recipe.id ?? recipe.name} recipe={recipe} onOpen={onOpenRecipe} />)}
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <h3 className="font-heading text-xl font-semibold">No matching recipes found</h3>
          <p className="mt-2 text-sm text-muted-foreground">Try another image or check a different supported food.</p>
        </div>
      )}
    </section>
  )
}
