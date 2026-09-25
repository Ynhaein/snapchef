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
    <section id="supported-foods" className="supported-sheet">
      <div className="supported-heading">
        <h2>Foods SnapChef currently recognizes</h2>
      </div>
      <p className="supported-intro">The model is trained on these 10 food categories:</p>
      <ol className="supported-list">
        {FOODS.map((food, index) => (
          <li key={food}>
            <span className="food-number">{String(index + 1).padStart(2, '0')}</span>
            <span>{food}</span>
          </li>
        ))}
      </ol>
      <p className="supported-note">Foods outside these categories may be marked as unknown or matched to the closest supported category.</p>
    </section>
  )
}
