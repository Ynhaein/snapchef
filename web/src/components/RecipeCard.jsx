import { HugeiconsIcon } from '@hugeicons/react'
import { Clock01Icon, StarIcon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card'
import { formatDuration } from '@/lib/Formatters'

const FALLBACK_IMAGE = '/images/RecipeFallback.jpg'

export default function RecipeCard({ recipe, onOpen }) {
  return (
    <Card className="border border-border py-0 shadow-[0_4px_16px_-2px_rgba(43,33,24,.06)]">
      <img
        src={recipe.image_url || FALLBACK_IMAGE}
        alt=""
        className="aspect-[4/3] w-full object-cover"
        onError={(event) => { event.currentTarget.src = FALLBACK_IMAGE }}
      />
      <CardHeader className="pt-1">
        <div className="flex items-center gap-1 text-xs font-semibold text-accent-foreground">
          <HugeiconsIcon icon={StarIcon} className="size-4 text-accent" />
          {recipe.rating ?? 'Not rated'}
          {recipe.review_count != null && <span className="font-normal text-muted-foreground">({recipe.review_count})</span>}
        </div>
        <CardTitle className="line-clamp-2 font-heading text-xl">{recipe.name}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="line-clamp-3 text-sm leading-6 text-muted-foreground">{recipe.description || 'No description available.'}</p>
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1">
            <HugeiconsIcon icon={Clock01Icon} className="size-3.5" />
            {formatDuration(recipe.total_time)}
          </span>
          {recipe.servings && <span className="rounded-full bg-muted px-2.5 py-1">{recipe.servings} servings</span>}
        </div>
      </CardContent>
      <CardFooter className="pb-4">
        <Button className="w-full" size="lg" onClick={() => onOpen(recipe)}>View recipe</Button>
      </CardFooter>
    </Card>
  )
}
