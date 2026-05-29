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
})
