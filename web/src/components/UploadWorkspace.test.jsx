import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import UploadWorkspace, { validateImage } from '@/components/UploadWorkspace'

describe('UploadWorkspace', () => {
  it('rejects unsupported files and files larger than 5 MB', () => {
    expect(validateImage(new File(['text'], 'note.txt', { type: 'text/plain' }))).toMatch(/JPEG/)
    const largeImage = new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'large.jpg', { type: 'image/jpeg' })
    expect(validateImage(largeImage)).toMatch(/smaller than 5 MB/)
  })

  it('accepts an image selected from the file input', () => {
    const onFile = vi.fn()
    render(
      <UploadWorkspace
        file={null}
        previewUrl=""
        isAnalyzing={false}
        onFile={onFile}
        onAnalyze={vi.fn()}
        onRemove={vi.fn()}
        onValidationError={vi.fn()}
      />,
    )
    const file = new File(['image'], 'dish.png', { type: 'image/png' })
    fireEvent.change(screen.getByLabelText(/choose a food photo/i), { target: { files: [file] } })
    expect(onFile).toHaveBeenCalledWith(file)
  })
})
