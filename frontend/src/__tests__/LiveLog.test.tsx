import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render } from '@testing-library/react'

import LiveLog from '../components/LiveLog'
import type { FetchEventSourceOptions } from '../api/fetchEventSource'

const mocks = vi.hoisted(() => ({
  fetchEventSource: vi.fn(),
}))

vi.mock('../api/fetchEventSource', () => ({
  fetchEventSource: mocks.fetchEventSource,
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('LiveLog', () => {
  const controllers: Array<{ abort: ReturnType<typeof vi.fn> }> = []
  const options: FetchEventSourceOptions[] = []

  beforeEach(() => {
    vi.useFakeTimers()
    controllers.length = 0
    options.length = 0
    mocks.fetchEventSource.mockReset()
    mocks.fetchEventSource.mockImplementation((opts: FetchEventSourceOptions) => {
      const controller = { abort: vi.fn() }
      options.push(opts)
      controllers.push(controller)
      return controller
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('ignores close callbacks from a disposed log stream', () => {
    const first = render(<LiveLog />)
    expect(mocks.fetchEventSource).toHaveBeenCalledTimes(1)

    first.unmount()
    render(<LiveLog />)
    expect(mocks.fetchEventSource).toHaveBeenCalledTimes(2)

    act(() => {
      options[0].onclose?.()
      vi.advanceTimersByTime(1000)
    })

    expect(mocks.fetchEventSource).toHaveBeenCalledTimes(2)
    expect(controllers[0].abort).toHaveBeenCalledTimes(1)
  })
})
