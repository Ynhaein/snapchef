export function formatFoodName(value = '') {
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function formatPercent(value) {
  return `${(Number(value ?? 0) * 100).toFixed(2)}%`
}

export function formatDuration(value) {
  if (!value) return 'Not available'
  const match = /^PT(?:(\d+)H)?(?:(\d+)M)?$/.exec(value)
  if (!match) return value
  const hours = Number(match[1] ?? 0)
  const minutes = Number(match[2] ?? 0)
  return [hours && `${hours} hr`, minutes && `${minutes} min`].filter(Boolean).join(' ')
}
