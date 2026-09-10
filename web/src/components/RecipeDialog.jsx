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
      <DialogContent className="flex max-h-[92dvh] flex-col gap-0 overflow-hidden p-0 sm:max-w-4xl">
        {recipe && (
          <>
            <DialogHeader className="shrink-0 border-b border-border bg-muted/35 px-5 py-5 pr-14 sm:px-7 sm:py-6 sm:pr-16">
              <DialogTitle className="font-heading text-2xl leading-tight sm:text-3xl">{recipe.name}</DialogTitle>
              <DialogDescription className="mt-1 line-clamp-3 max-w-3xl text-sm leading-6">
                {recipe.description || 'Everything you need to prepare this recipe.'}
              </DialogDescription>
              <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium text-muted-foreground">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5">
                  <HugeiconsIcon icon={StarIcon} className="size-4 text-accent" />
                  {recipe.rating ?? 'Not rated'}
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5">
                  <HugeiconsIcon icon={Clock01Icon} className="size-4 text-primary" />
                  {formatDuration(recipe.total_time)}
                </span>
                {recipe.servings && (
                  <span className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1.5">
                    {recipe.servings} servings
                  </span>
                )}
              </div>
            </DialogHeader>

            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-7 [scrollbar-gutter:stable] sm:px-7 sm:py-8">
              <div className="grid gap-10 md:grid-cols-[minmax(0,.85fr)_minmax(0,1.15fr)] md:gap-12">
                <section aria-labelledby="recipe-ingredients">
                  <div className="mb-5 flex items-baseline justify-between gap-3">
                    <h3 id="recipe-ingredients" className="font-heading text-xl font-semibold">Ingredients</h3>
                    <span className="text-xs text-muted-foreground">{recipe.ingredients?.length || 0} items</span>
                  </div>
                  {recipe.ingredients?.length ? (
                    <ul className="overflow-hidden rounded-xl border border-border bg-muted/20">
                      {recipe.ingredients.map((ingredient, index) => (
                        <li key={`${ingredient.name}-${index}`} className="grid grid-cols-[minmax(4rem,auto)_1fr] gap-4 border-b border-border px-4 py-4 text-sm last:border-b-0">
                          <span className="font-semibold text-primary">{ingredient.quantity || '—'}</span>
                          <span className="leading-6">{ingredient.name}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="rounded-xl bg-muted/40 p-4 text-sm text-muted-foreground">No ingredient list is available.</p>
                  )}
                </section>

                <section aria-labelledby="recipe-instructions">
                  <h3 id="recipe-instructions" className="mb-5 font-heading text-xl font-semibold">Instructions</h3>
                  {recipe.instructions?.length ? (
                    <ol className="space-y-4">
                      {recipe.instructions.map((instruction, index) => (
                        <li key={`${index}-${instruction.slice(0, 20)}`} className="grid grid-cols-[2rem_1fr] gap-4 rounded-xl border border-border bg-card p-4 text-sm leading-7 shadow-sm">
                          <span className="grid size-8 place-items-center rounded-full bg-primary font-bold text-primary-foreground">{index + 1}</span>
                          <p className="pt-1">{instruction}</p>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="rounded-xl bg-muted/40 p-4 text-sm text-muted-foreground">No preparation instructions are available.</p>
                  )}
                </section>
              </div>
            </div>

            <footer className="flex shrink-0 flex-col gap-2 border-t border-border bg-card px-5 py-3 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-7">
              <p>Recipe information is sourced from the local Food.com dataset.</p>
              <p className="shrink-0">
                Press <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 font-sans font-semibold text-foreground">Esc</kbd> to close
              </p>
            </footer>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
