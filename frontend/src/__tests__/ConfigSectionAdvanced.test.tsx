import { describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'

import { ConfigSectionAdvanced } from '../components/ConfigSectionAdvanced'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('ConfigSectionAdvanced', () => {
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
})
