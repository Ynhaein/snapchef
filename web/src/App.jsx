import { useEffect, useRef, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { HugeiconsIcon } from '@hugeicons/react'
import { Alert02Icon } from '@hugeicons/core-free-icons'

import AnalysisResult from '@/components/AnalysisResult'
import AnalysisSkeleton from '@/components/AnalysisSkeleton'
import RecipeCollection from '@/components/RecipeCollection'
import RecipeDialog from '@/components/RecipeDialog'
import SupportedFoods from '@/components/SupportedFoods'
import UploadWorkspace from '@/components/UploadWorkspace'
import { Alert, AlertAction, AlertDescription, AlertTitle } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import MainLayout from '@/layouts/MainLayout'
import { analyzeFood } from '@/lib/ApiClient'

function SnapChefPage() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [activeRecipe, setActiveRecipe] = useState(null)
  const inputRef = useRef(null)
  const requestRef = useRef(null)

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    requestRef.current?.abort()
  }, [previewUrl])

  function selectFile(nextFile) {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(nextFile)
    setPreviewUrl(URL.createObjectURL(nextFile))
    setStatus('selected')
    setResult(null)
    setError('')
  }

  function removeFile() {
    requestRef.current?.abort()
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(null)
    setPreviewUrl('')
    setStatus('idle')
    setResult(null)
    setError('')
  }

  async function submit() {
    if (!file) return
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    setStatus('analyzing')
    setError('')
    try {
      const payload = await analyzeFood(file, controller.signal)
      setResult(payload)
      setStatus(payload.prediction.is_known ? 'known' : 'unknown')
      window.setTimeout(() => document.querySelector('[aria-live="polite"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50)
    } catch (requestError) {
      if (requestError.name === 'AbortError') return
      setError(requestError.message)
      setStatus('error')
    }
  }

  return (
    <main id="top" className="mx-auto w-full max-w-6xl space-y-14 px-4 py-10 sm:px-6 sm:py-14">
      <section className="mx-auto max-w-3xl text-center">
        <span className="rounded-full bg-muted px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary">AI-powered culinary discovery</span>
        <h1 className="mt-5 font-heading text-4xl font-bold leading-tight sm:text-5xl">Turn a food photo into something worth cooking.</h1>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
          Upload a photo of a dish and SnapChef will identify the closest supported food, then suggest recipes you can try at home.
        </p>
      </section>

      <UploadWorkspace
        file={file}
        previewUrl={previewUrl}
        isAnalyzing={status === 'analyzing'}
        onFile={selectFile}
        onAnalyze={submit}
        onRemove={removeFile}
        onValidationError={(message) => { setError(message); setStatus('error') }}
        inputRef={inputRef}
      />

      {error && (
        <Alert variant="destructive">
          <HugeiconsIcon icon={Alert02Icon} />
          <AlertTitle>We could not analyze this photo</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
          <AlertAction>
            <Button variant="ghost" size="sm" onClick={() => { setError(''); setStatus(file ? 'selected' : 'idle') }}>
              Try again
            </Button>
          </AlertAction>
        </Alert>
      )}
      {status === 'analyzing' && <AnalysisSkeleton />}
      {result && status !== 'analyzing' && <AnalysisResult prediction={result.prediction} />}
      {result?.prediction.is_known && (
        <RecipeCollection foodName={result.prediction.label} recipes={result.recipes} onOpenRecipe={setActiveRecipe} />
      )}
      <SupportedFoods />
      <RecipeDialog recipe={activeRecipe} onClose={() => setActiveRecipe(null)} />
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout onUpload={() => document.querySelector('input[type="file"]')?.click()} />}>
        <Route index element={<SnapChefPage />} />
      </Route>
    </Routes>
  )
}
