// oxlint-disable react/only-export-components -- validator is shared with unit tests.
import { useRef, useState } from 'react'
import { HugeiconsIcon } from '@hugeicons/react'
import { Delete02Icon, Image01Icon, Upload04Icon } from '@hugeicons/core-free-icons'

import { Button } from '@/components/ui/Button'

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
    <section id="analyze" className="upload-module">
      {!file ? (
        <div
          className={`upload-drop ${isDragging ? 'is-dragging' : ''}`}
          onDragEnter={(event) => { event.preventDefault(); setIsDragging(true) }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault()
            setIsDragging(false)
            acceptFile(event.dataTransfer.files[0])
          }}
        >
          <div className="upload-drop-content">
            <span className="upload-icon"><HugeiconsIcon icon={Upload04Icon} className="size-7" strokeWidth={1.6} /></span>
            <h2>Start with a plate.</h2>
            <p>Drop a food photo here, or choose one from your device.</p>
            <Button className="proof-button proof-button-primary upload-cta" size="lg" onClick={() => activeInputRef.current?.click()}>
              Choose a food photo
            </Button>
            <p className="upload-guidance">JPEG, PNG, or WebP · maximum 5 MB</p>
            <p className="upload-privacy">Your image is used only to generate this result.</p>
          </div>
        </div>
      ) : (
        <div className="selected-board">
          <div className="image-frame">
            <img src={previewUrl} alt="Selected food preview" />
            <div className="image-caption">
              <span>Selected photo</span>
              <span>{file.name}</span>
            </div>
          </div>
          <div className="file-details">
            <div className="file-details-top">
              <span>Photo selected</span>
              <span>Ready to read</span>
            </div>
            <div>
              <h2>Ready when you are.</h2>
              <p className="file-name">{file.name}</p>
            </div>
            <div className="action-stack">
              <Button className="proof-button proof-button-primary" size="lg" disabled={isAnalyzing} onClick={onAnalyze}>
                <HugeiconsIcon icon={Image01Icon} data-icon="inline-start" />
                {isAnalyzing ? 'Analyzing your dish…' : 'Analyze food'}
              </Button>
              <Button className="proof-button proof-button-quiet" size="lg" disabled={isAnalyzing} onClick={() => activeInputRef.current?.click()}>
                Choose another photo
              </Button>
              <Button className="proof-button proof-button-danger" size="lg" disabled={isAnalyzing} onClick={onRemove}>
                <HugeiconsIcon icon={Delete02Icon} data-icon="inline-start" />
                Remove photo
              </Button>
            </div>
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
    </section>
  )
}
