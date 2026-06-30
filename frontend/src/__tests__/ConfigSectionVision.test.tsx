import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ConfigSectionVision } from '../components/ConfigSectionVision'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('ConfigSectionVision', () => {
  it('offers OpenRouter with image-compatible vision defaults', () => {
    render(
      <ConfigSectionVision
        config={{ enable_vision: 'true', llm_provider_vision: 'openrouter' }}
        onSave={vi.fn()}
        secretsSet={[]}
      />,
    )

    expect(screen.getByRole('option', { name: 'OpenRouter' })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('openai/gpt-4o')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('https://openrouter.ai/api/v1')).toBeInTheDocument()
  })

  it('renders configurable vision generation parameters', () => {
    render(
      <ConfigSectionVision
        config={{
          enable_vision: 'true',
          llm_provider_vision: 'openrouter',
          llm_temperature_vision: '0.2',
          llm_max_tokens_vision: '1024',
          llm_num_ctx_vision: '32768',
        }}
        onSave={vi.fn()}
        secretsSet={[]}
      />,
    )

    expect(screen.getByText('config.llmTemperatureVision')).toBeInTheDocument()
    expect(screen.getByDisplayValue('0.2')).toBeInTheDocument()
    expect(screen.getByText('config.llmMaxTokensVision')).toBeInTheDocument()
    expect(screen.getByDisplayValue('1024')).toBeInTheDocument()
    expect(screen.getByText('config.llmContextWindowVision')).toBeInTheDocument()
    expect(screen.getByDisplayValue('32768')).toBeInTheDocument()
  })
})
