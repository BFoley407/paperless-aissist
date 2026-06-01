import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ConfigSectionLLM } from '../components/ConfigSectionLLM'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('ConfigSectionLLM', () => {
  it('offers OpenRouter with OpenRouter defaults', () => {
    render(
      <ConfigSectionLLM config={{ llm_provider: 'openrouter' }} onSave={vi.fn()} secretsSet={[]} />,
    )

    expect(screen.getByRole('option', { name: 'OpenRouter' })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('openai/gpt-4o-mini')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('https://openrouter.ai/api/v1')).toBeInTheDocument()
  })

  it('renders configurable generation parameters', () => {
    render(
      <ConfigSectionLLM
        config={{
          llm_provider: 'openrouter',
          llm_temperature: '0.4',
          llm_max_tokens: '512',
        }}
        onSave={vi.fn()}
        secretsSet={[]}
      />,
    )

    expect(screen.getByText('config.llmTemperature')).toBeInTheDocument()
    expect(screen.getByDisplayValue('0.4')).toBeInTheDocument()
    expect(screen.getByText('config.llmMaxTokens')).toBeInTheDocument()
    expect(screen.getByDisplayValue('512')).toBeInTheDocument()
  })
})
