import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'

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

  it('loads Paperless tags on mount when the token is stored as a secret', async () => {
    render(
      <ConfigSectionPaperless
        config={{ paperless_url: 'http://paperless.test', paperless_token: '' }}
        onSave={vi.fn()}
        secretsSet={['paperless_token']}
      />,
    )

    await waitFor(() => {
      expect(mockGetTags).toHaveBeenCalledTimes(1)
    })
  })
})
