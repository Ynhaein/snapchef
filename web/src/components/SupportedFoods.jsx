const FOODS = [
  'Bread pudding',
  'Chicken curry',
  'Donuts',
  'Garlic bread',
  'Gnocchi',
  'Samosa',
  'Sashimi',
  'Seaweed salad',
  'Spaghetti carbonara',
  'Takoyaki',
]

export default function SupportedFoods() {
  return (
    <section id="supported-foods" className="scroll-mt-24 rounded-2xl border border-border bg-muted p-6 sm:p-8">
      <h2 className="font-heading text-3xl font-bold">Foods SnapChef currently recognizes</h2>
      <p className="mt-2 text-sm text-muted-foreground">The current model is trained on these 10 food categories:</p>
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
        {FOODS.map((food) => (
          <span key={food} className="rounded-full border border-border bg-card px-3 py-2 text-center text-xs font-semibold">
            {food}
          </span>
        ))}
      </div>
      <p className="mt-5 text-xs leading-5 text-muted-foreground">
        Foods outside these categories may be marked as unknown or matched to the closest supported category.
      </p>
    </section>
  )
}
