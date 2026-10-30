import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '@/App'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('SnapChef application', () => {
  it('submits a selected image and renders a known prediction', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        prediction: {
          label: 'spaghetti_carbonara',
          is_known: true,
          confidence: 0.96,
          margin: 0.91,
          top_candidates: [
            { label: 'spaghetti_carbonara', confidence: 0.96 },
            { label: 'gnocchi', confidence: 0.03 },
          ],
        },
        recipes: [],
      }),
    })

    render(<MemoryRouter><App /></MemoryRouter>)
    const file = new File(['image'], 'carbonara.jpg', { type: 'image/jpeg' })
    fireEvent.change(screen.getByLabelText(/choose a food photo/i), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Analyze food' }))

    await waitFor(() => expect(screen.getByText('We found a match')).toBeInTheDocument())
    expect(screen.getAllByText('Spaghetti Carbonara')).not.toHaveLength(0)
    expect(globalThis.fetch).toHaveBeenCalledOnce()
  })

  it('renders an API error with a recovery action', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Choose a valid image and try again.' }),
    })

    render(<MemoryRouter><App /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText(/choose a food photo/i), {
      target: { files: [new File(['bad'], 'dish.png', { type: 'image/png' })] },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Analyze food' }))

    await waitFor(() => expect(screen.getByText('Choose a valid image and try again.')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })

  it('adds and removes ingredients in the manual basket', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        ingredients: ['apple', 'banana'],
        unknown: [],
        recommendations: [],
      }),
    })

    render(<MemoryRouter><App /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('Add an ingredient'), { target: { value: 'apple' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect(screen.getByRole('button', { name: 'Remove apple' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Find recipes' }))
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledOnce())
    expect(globalThis.fetch.mock.calls[0][0]).toContain('/api/recommend')

    fireEvent.click(screen.getByRole('button', { name: 'Remove apple' }))
    expect(screen.queryByRole('button', { name: 'Remove apple' })).not.toBeInTheDocument()
  })
})
