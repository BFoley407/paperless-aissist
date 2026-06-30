import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import ConfigPanel from '../components/ConfigPanel'

const mocks = vi.hoisted(() => ({
  mockGetAll: vi.fn(),
  mockSet: vi.fn(),
}))

vi.mock('../api/client', () => ({
  configApi: {
    getAll: mocks.mockGetAll,
    set: mocks.mockSet,
    testConnection: vi.fn(),
  },
  documentsApi: {
    getTags: vi.fn(),
  },
  schedulerApi: {
    getStatus: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    clearState: vi.fn(),
  },
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
}))

describe('ConfigPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.mockGetAll.mockResolvedValue({
      data: {
        data: {},
        secrets_set: [],
      },
    })
    mocks.mockSet.mockResolvedValue({ data: { key: 'document_list_refresh_mode', value: 'manual' } })
  })

  it('saves document list refresh mode immediately when changed', async () => {
    render(<ConfigPanel />)

    fireEvent.click(await screen.findByText('config.tabAdvanced'))
    fireEvent.change(screen.getByLabelText('config.documentListRefreshMode'), {
      target: { value: 'manual' },
    })

    await waitFor(() => {
      expect(mocks.mockSet).toHaveBeenCalledWith('document_list_refresh_mode', 'manual')
    })
  })

  it('renders and saves vision PDF input mode', async () => {
    render(<ConfigPanel />)

    fireEvent.click(await screen.findByText('config.tabLLM'))
    const pdfMode = await screen.findByLabelText('config.visionPdfMode')

    expect(pdfMode).toHaveValue('auto')
    expect(screen.getByText('config.visionPdfModeAuto')).toBeInTheDocument()

    fireEvent.change(pdfMode, { target: { value: 'page_images' } })
    fireEvent.click(screen.getByText('config.saveConfiguration'))

    await waitFor(() => {
      expect(mocks.mockSet).toHaveBeenCalledWith('vision_pdf_mode', 'page_images')
    })
  })

  it('renders and saves Ollama context window', async () => {
    render(<ConfigPanel />)

    fireEvent.click(await screen.findByText('config.tabLLM'))
    const contextWindow = await screen.findByLabelText('config.llmContextWindow')

    expect(contextWindow).toHaveValue(null)

    fireEvent.change(contextWindow, { target: { value: '16384' } })
    fireEvent.click(screen.getByText('config.saveConfiguration'))

    await waitFor(() => {
      expect(mocks.mockSet).toHaveBeenCalledWith('llm_num_ctx', '16384')
    })
  })

  it('renders and saves OCR fix max chars', async () => {
    render(<ConfigPanel />)

    fireEvent.click(await screen.findByText('config.tabAdvanced'))
    const maxChars = await screen.findByLabelText('config.ocrFixMaxChars')

    expect(maxChars).toHaveValue(10000)

    fireEvent.change(maxChars, { target: { value: '20000' } })
    fireEvent.click(screen.getByText('config.saveConfiguration'))

    await waitFor(() => {
      expect(mocks.mockSet).toHaveBeenCalledWith('ocr_fix_max_chars', '20000')
    })
  })
})
