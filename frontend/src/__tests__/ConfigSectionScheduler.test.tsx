import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ConfigSectionScheduler } from '../components/ConfigSectionScheduler'

const mocks = vi.hoisted(() => ({
  mockGetStatus: vi.fn(),
}))

vi.mock('../api/client', () => ({
  schedulerApi: {
    getStatus: mocks.mockGetStatus,
    start: vi.fn(),
    stop: vi.fn(),
    clearState: vi.fn(),
  },
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: { id?: number }) => (
      params?.id ? `${key} ${params.id}` : key
    ),
  }),
}))

describe('ConfigSectionScheduler', () => {
  beforeEach(() => {
    mocks.mockGetStatus.mockResolvedValue({
      data: {
        running: true,
        interval_minutes: 5,
        next_run: null,
        is_processing: true,
        current_document_ids: [77],
        active_documents: [],
      },
    })
  })

  it('links the current scheduler document when Paperless URL is configured', async () => {
    render(
      <ConfigSectionScheduler
        config={{ paperless_url: 'http://paperless.test/' }}
        onSave={vi.fn()}
      />,
    )

    const link = await screen.findByRole('link', { name: /config.schedulerCurrentDoc 77/ })
    expect(link).toHaveAttribute('href', 'http://paperless.test/documents/77')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noreferrer')
  })
})
