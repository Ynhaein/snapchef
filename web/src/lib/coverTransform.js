export function coverTransform(box, imgW, imgH, dispW, dispH) {
  if (!imgW || !imgH || !dispW || !dispH || !box || box.length < 4) return null
  const scale = Math.max(dispW / imgW, dispH / imgH)
  const offX = (dispW - imgW * scale) / 2
  const offY = (dispH - imgH * scale) / 2
  const w = (box[2] - box[0]) * imgW * scale
  const h = (box[3] - box[1]) * imgH * scale
  if (w < 1 || h < 1) return null
  return {
    x: box[0] * imgW * scale + offX,
    y: box[1] * imgH * scale + offY,
    w,
    h,
  }
}
