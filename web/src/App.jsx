import { useEffect, useRef, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { HugeiconsIcon } from '@hugeicons/react'
import { Alert02Icon } from '@hugeicons/core-free-icons'

import AnalysisResult from '@/components/AnalysisResult'
import AnalysisSkeleton from '@/components/AnalysisSkeleton'
import DetectedItems from '@/components/DetectedItems'
import IngredientBasket from '@/components/IngredientBasket'
import ScanPage from '@/pages/ScanPage'
import RecipeDetails from '@/pages/RecipeDetails'
import BasketPage from '@/pages/BasketPage'
import RecipesPage from '@/pages/RecipesPage'
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
  const [basket, setBasket] = useState([])
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
      if (!payload?.prediction || !Array.isArray(payload.recipes)) {
        throw new Error('SnapChef received an unexpected response. Please try again.')
      }
      setResult(payload)
      setStatus(payload.prediction.is_known ? 'known' : 'unknown')
      window.setTimeout(() => document.querySelector('[aria-live="polite"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50)
    } catch (requestError) {
      if (requestError.name === 'AbortError') return
      setResult(null)
      setError(requestError.message)
      setStatus('error')
    }
  }

  const readIsActive = status === 'known' || status === 'unknown'

  return (
    <main id="top" className="page-shell">
      <section className="hero-band">
        <div className="hero-copy">
          <h1>Turn a food photo into something worth cooking.</h1>
          <p className="hero-lede">
            Upload a dish and SnapChef will find the closest supported food, then point you toward a recipe for the kitchen.
          </p>
          <div className="hero-rail" aria-label="SnapChef workflow">
            <span className={`rail-step ${readIsActive ? 'is-complete' : 'is-active'}`}>Upload</span>
            <span className={`rail-line ${readIsActive ? 'is-complete' : ''}`} />
            <span className={`rail-step ${readIsActive ? 'is-active' : ''}`}>Read</span>
            <span className="rail-line" />
            <span className="rail-step">Cook</span>
          </div>
          <a className="hero-link" href="#analyze">Start with a photo <span aria-hidden="true">↓</span></a>
        </div>
        <div className="hero-station">
          <div className="station-header">
            <span>Photo intake</span>
            <span>01 / 03</span>
          </div>
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
        </div>
      </section>

      <div className="content-grid">
        <aside className="sidebar">
          <SupportedFoods />
          <div className="sidebar-note">
            <p className="sidebar-note-title">A focused read</p>
            <p>SnapChef looks for the closest match among 10 food categories, not every dish in the world.</p>
          </div>
        </aside>

        <section className="workflow-column" aria-label="SnapChef analysis workflow">
          {error && (
            <Alert variant="destructive" className="workflow-alert">
              <HugeiconsIcon icon={Alert02Icon} />
              <AlertTitle>We could not analyze this photo</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
              <AlertAction>
                <Button className="proof-button proof-button-danger" size="sm" onClick={() => { setError(''); setStatus(file ? 'selected' : 'idle') }}>
                  Try again
                </Button>
              </AlertAction>
            </Alert>
          )}
          {status === 'analyzing' && <AnalysisSkeleton />}
          {result && status !== 'analyzing' && <AnalysisResult prediction={result.prediction} />}
          {result?.detected_items?.length > 0 && (
            <DetectedItems
              items={result.detected_items}
              onConfirm={(label) => setBasket((current) => (current.includes(label) ? current : [...current, label]))}
            />
          )}
          {result?.prediction.is_known && result?.path === 'dish' && (
            <RecipeCollection foodName={result.prediction.label} recipes={result.recipes} onOpenRecipe={setActiveRecipe} />
          )}
          {!result && status === 'idle' && (
            <div className="workflow-empty">
              <span className="workflow-empty-mark">02</span>
              <div>
                <h2>Your read will land here.</h2>
                <p>Choose a supported dish photo above and we&apos;ll show the closest match, its confidence, and recipe ideas.</p>
              </div>
            </div>
          )}
        </section>
      </div>
      <IngredientBasket ingredients={basket} onChange={setBasket} onOpenRecipe={setActiveRecipe} />
      <RecipeDialog recipe={activeRecipe} onClose={() => setActiveRecipe(null)} />
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout onUpload={() => document.querySelector('input[type="file"]')?.click()} />}>
        <Route index element={<SnapChefPage />} />
        <Route path="scan" element={<ScanPage />} />
        <Route path="recipes" element={<RecipesPage />} />
        <Route path="recipes/:id" element={<RecipeDetails />} />
        <Route path="basket" element={<BasketPage />} />
      </Route>
    </Routes>
  )
}
