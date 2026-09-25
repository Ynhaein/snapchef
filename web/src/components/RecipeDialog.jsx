import { Clock01Icon, StarIcon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import { formatDuration } from '@/lib/Formatters'

export default function RecipeDialog({ recipe, onClose }) {
  return (
    <Dialog open={Boolean(recipe)} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="recipe-dialog-content flex max-h-[92dvh] flex-col gap-0 overflow-hidden p-0 sm:max-w-4xl">
        {recipe && (
          <>
            <DialogHeader className="recipe-dialog-header shrink-0 border-b px-5 py-5 pr-14 sm:px-7 sm:py-6 sm:pr-16">
              <DialogTitle className="recipe-dialog-title">{recipe.name}</DialogTitle>
              <DialogDescription className="recipe-dialog-description mt-1 max-w-3xl text-sm leading-6">
                {recipe.description || 'Everything you need to prepare this recipe.'}
              </DialogDescription>
              <div className="dialog-meta mt-3">
                <span><HugeiconsIcon icon={StarIcon} /> {recipe.rating ?? 'Not rated'}</span>
                <span><HugeiconsIcon icon={Clock01Icon} /> {formatDuration(recipe.total_time)}</span>
                {recipe.servings && <span>{recipe.servings} servings</span>}
              </div>
            </DialogHeader>

            <div className="dialog-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-7 [scrollbar-gutter:stable] sm:px-7 sm:py-8">
              <div className="grid gap-10 md:grid-cols-[minmax(0,.85fr)_minmax(0,1.15fr)] md:gap-12">
                <section aria-labelledby="recipe-ingredients">
                  <div className="dialog-section-title">
                    <h3 id="recipe-ingredients">Ingredients</h3>
                    <span>{recipe.ingredients?.length || 0} items</span>
                  </div>
                  {recipe.ingredients?.length ? (
                    <ul className="ingredient-list">
                      {recipe.ingredients.map((ingredient, index) => (
                        <li key={`${ingredient.name}-${index}`}>
                          <span>{ingredient.quantity || '—'}</span>
                          <span>{ingredient.name}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="dialog-empty">No ingredient list is available.</p>
                  )}
                </section>

                <section aria-labelledby="recipe-instructions">
                  <div className="dialog-section-title">
                    <h3 id="recipe-instructions">Instructions</h3>
                    <span>ordered steps</span>
                  </div>
                  {recipe.instructions?.length ? (
                    <ol className="instruction-list">
                      {recipe.instructions.map((instruction, index) => (
                        <li key={`${index}-${instruction.slice(0, 20)}`}>
                          <span className="instruction-index">{String(index + 1).padStart(2, '0')}</span>
                          <p>{instruction}</p>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="dialog-empty">No preparation instructions are available.</p>
                  )}
                </section>
              </div>
            </div>

            <footer className="dialog-footer flex shrink-0 flex-col gap-2 border-t px-5 py-3 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-7">
              <p>Recipe information is sourced from the local Food.com dataset.</p>
              <p className="shrink-0">Press <kbd className="border border-border bg-muted px-1.5 py-0.5 font-sans font-semibold text-foreground">Esc</kbd> to close</p>
            </footer>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
