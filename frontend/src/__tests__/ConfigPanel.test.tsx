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
})
