import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { ConfigSectionPaperless } from '../components/ConfigSectionPaperless'

const { mockGetTags } = vi.hoisted(() => ({
  mockGetTags: vi.fn(),
}))

const translate = (key: string, values?: Record<string, unknown>) =>
  values ? `${key} ${JSON.stringify(values)}` : key

vi.mock('../api/client', () => ({
  documentsApi: {
    getTags: mockGetTags,
  },
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: translate,
  }),
}))

describe('ConfigSectionPaperless', () => {
  beforeEach(() => {
    mockGetTags.mockReset()
    mockGetTags.mockResolvedValue({
      data: {
        tags: [{ id: 1, name: 'ai-process' }],
        correspondents: [{ id: 1, name: 'Example' }],
      },
    })
  })

  it('does not load Paperless tags on mount when the token is stored as a secret', () => {
    render(
      <ConfigSectionPaperless
        config={{ paperless_url: 'http://paperless.test', paperless_token: '' }}
        onSave={vi.fn()}
        secretsSet={['paperless_token']}
      />,
    )

    expect(mockGetTags).not.toHaveBeenCalled()
  })

  it('shows a hint before Paperless metadata is loaded', () => {
    render(
      <ConfigSectionPaperless
        config={{ paperless_url: 'http://paperless.test', paperless_token: '' }}
        onSave={vi.fn()}
        secretsSet={['paperless_token']}
      />,
    )

    expect(screen.getByText('config.notConnectedHint')).toBeInTheDocument()
    expect(screen.queryByText(/config.lastLoaded/)).not.toBeInTheDocument()
  })

  it('loads Paperless metadata with refresh when Connect & Load Tags is clicked', async () => {
    render(
      <ConfigSectionPaperless
        config={{ paperless_url: 'http://paperless.test', paperless_token: '' }}
        onSave={vi.fn()}
        secretsSet={['paperless_token']}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'config.connect' }))

    await waitFor(() => {
      expect(mockGetTags).toHaveBeenCalledTimes(1)
    })
    expect(mockGetTags).toHaveBeenCalledWith(true)
  })

  it('shows connected badge and last-loaded status after successful manual load', async () => {
    render(
      <ConfigSectionPaperless
        config={{ paperless_url: 'http://paperless.test', paperless_token: '' }}
        onSave={vi.fn()}
        secretsSet={['paperless_token']}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'config.connect' }))

    expect(
      await screen.findByText('config.connectedBadge {"tags":1,"correspondents":1}'),
    ).toBeInTheDocument()
    expect(screen.getByText(/config.lastLoaded/)).toBeInTheDocument()
  })
})
