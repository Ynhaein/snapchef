// oxlint-disable react/only-export-components -- validator is shared with unit tests.
import { useRef, useState } from 'react'
import { HugeiconsIcon } from '@hugeicons/react'
import { Delete02Icon, Image01Icon, Upload04Icon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_FILE_SIZE = 5 * 1024 * 1024

export function validateImage(file) {
  if (!file) return 'Choose a valid image and try again.'
  if (!ACCEPTED_TYPES.includes(file.type)) return 'Choose a JPEG, PNG, or WebP image.'
  if (file.size > MAX_FILE_SIZE) return 'Choose an image smaller than 5 MB.'
  return null
}

export default function UploadWorkspace({
  file,
  previewUrl,
  isAnalyzing,
  onFile,
  onAnalyze,
  onRemove,
  onValidationError,
  inputRef,
}) {
  const fallbackRef = useRef(null)
  const activeInputRef = inputRef ?? fallbackRef
  const [isDragging, setIsDragging] = useState(false)

  function acceptFile(nextFile) {
    const error = validateImage(nextFile)
    if (error) {
      onValidationError(error)
      return
    }
    onFile(nextFile)
  }

  return (
    <section id="analyze" className="scroll-mt-24">
      <Card className="border border-border bg-card py-0 shadow-[0_4px_16px_-2px_rgba(43,33,24,.06)]">
        <CardContent className="p-4 sm:p-6">
          {!file ? (
            <div
              className={`grid min-h-64 place-items-center rounded-xl border-2 border-dashed p-8 text-center transition-colors ${isDragging ? 'border-primary bg-muted' : 'border-border bg-background'}`}
              onDragEnter={(event) => { event.preventDefault(); setIsDragging(true) }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(event) => {
                event.preventDefault()
                setIsDragging(false)
                acceptFile(event.dataTransfer.files[0])
              }}
            >
              <div>
                <span className="mx-auto mb-4 grid size-14 place-items-center rounded-full bg-muted text-primary">
                  <HugeiconsIcon icon={Upload04Icon} className="size-7" strokeWidth={1.8} />
                </span>
                <h2 className="font-heading text-2xl font-semibold">Drop an image here</h2>
                <p className="mt-2 text-sm text-muted-foreground">or choose a food photo from your device</p>
                <Button className="mt-5" size="lg" onClick={() => activeInputRef.current?.click()}>
                  Choose a food photo
                </Button>
                <p className="mt-4 text-xs text-muted-foreground">JPEG, PNG, or WebP. Maximum file size: 5 MB.</p>
                <p className="mt-1 text-xs text-muted-foreground">Your image is used only to generate this result.</p>
              </div>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(18rem,.75fr)]">
              <div className="overflow-hidden rounded-xl border border-border bg-muted">
                <img src={previewUrl} alt="Selected food preview" className="aspect-video h-full w-full object-cover" />
              </div>
              <div className="flex flex-col justify-center">
                <div className="mb-5 flex items-center gap-3">
                  <span className="grid size-9 place-items-center rounded-full bg-muted text-secondary">
                    <HugeiconsIcon icon={Image01Icon} />
                  </span>
                  <div className="min-w-0">
                    <p className="font-semibold">Selected photo</p>
                    <p className="truncate text-xs text-muted-foreground">{file.name}</p>
                  </div>
                </div>
                <Button size="lg" disabled={isAnalyzing} onClick={onAnalyze}>
                  {isAnalyzing ? 'Analyzing your dish…' : 'Analyze food'}
                </Button>
                <Button className="mt-2" variant="outline" size="lg" disabled={isAnalyzing} onClick={() => activeInputRef.current?.click()}>
                  Choose another photo
                </Button>
                <Button className="mt-2" variant="destructive" size="lg" disabled={isAnalyzing} onClick={onRemove}>
                  <HugeiconsIcon icon={Delete02Icon} data-icon="inline-start" />
                  Remove photo
                </Button>
              </div>
            </div>
          )}
          <input
            aria-label="Choose a food photo"
            ref={activeInputRef}
            className="sr-only"
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={(event) => {
              acceptFile(event.target.files[0])
              event.target.value = ''
            }}
          />
        </CardContent>
      </Card>
    </section>
  )
}
