import { beforeEach, describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { AxiosResponse } from 'axios'

import { ConfigSectionAdvanced } from '../components/ConfigSectionAdvanced'
import { configApi } from '../api/client'

vi.mock('../api/client', () => ({
  configApi: {
    generateAutomationToken: vi.fn(),
    revokeAutomationToken: vi.fn(),
  },
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

function mockAxiosResponse<T>(data: T): AxiosResponse<T> {
  return {
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {},
  } as AxiosResponse<T>
}

describe('ConfigSectionAdvanced', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('saves document list refresh mode changes', () => {
    const onSave = vi.fn()

    render(
      <ConfigSectionAdvanced
        config={{ document_list_refresh_mode: 'automatic' }}
        onSave={onSave}
      />,
    )

    fireEvent.change(screen.getByLabelText('config.documentListRefreshMode'), {
      target: { value: 'manual' },
    })

    expect(onSave).toHaveBeenCalledWith('document_list_refresh_mode', 'manual')
  })

  it('shows automation token status from secret metadata', () => {
    render(
      <ConfigSectionAdvanced
        config={{}}
        onSave={vi.fn()}
        secretsSet={['automation_api_token_hash']}
      />,
    )

    expect(screen.getByText('config.automationTokenConfigured')).toBeInTheDocument()
  })

  it('generates and displays a one-time automation token', async () => {
    vi.mocked(configApi.generateAutomationToken).mockResolvedValue(
      mockAxiosResponse({ token: 'paia_test_token' }),
    )
    const onSecretsChanged = vi.fn()

    render(
      <ConfigSectionAdvanced
        config={{}}
        onSave={vi.fn()}
        secretsSet={[]}
        onSecretsChanged={onSecretsChanged}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'config.generateAutomationToken' }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('paia_test_token')).toBeInTheDocument()
    })
    expect(onSecretsChanged).toHaveBeenCalled()
  })

  it('revokes the automation token', async () => {
    vi.mocked(configApi.revokeAutomationToken).mockResolvedValue(
      mockAxiosResponse({ success: true }),
    )
    const onSecretsChanged = vi.fn()

    render(
      <ConfigSectionAdvanced
        config={{}}
        onSave={vi.fn()}
        secretsSet={['automation_api_token_hash']}
        onSecretsChanged={onSecretsChanged}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'config.revokeAutomationToken' }))

    await waitFor(() => {
      expect(configApi.revokeAutomationToken).toHaveBeenCalled()
    })
    expect(onSecretsChanged).toHaveBeenCalled()
  })
})
