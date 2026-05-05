import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { fetchEventSource } from '../api/fetchEventSource'

function createMockResponse(body: ReadableStream | null, status = 200) {
  return {
    status,
    statusText: status === 200 ? 'OK' : 'Unauthorized',
    body,
  } as Response
}

function createMockReader(chunks: Uint8Array[]) {
  let index = 0
  return {
    read: vi.fn(async () => {
      if (index < chunks.length) {
        return { done: false, value: chunks[index++] }
      }
      return { done: true, value: undefined }
    }),
    releaseLock: vi.fn(),
  }
}

function createReadableStream(chunks: Uint8Array[]) {
  const reader = createMockReader(chunks)
  return {
    getReader: vi.fn(() => reader),
  } as unknown as ReadableStream
}

function stringToChunks(text: string): Uint8Array[] {
  return [new TextEncoder().encode(text)]
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('fetchEventSource', () => {
  it('calls onopen when connection succeeds', async () => {
    const onopen = vi.fn()
    const stream = createReadableStream(stringToChunks('data: hello\n\n'))
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(stream))

    fetchEventSource({ url: 'http://test.com', onopen })
    await waitFor(() => expect(onopen).toHaveBeenCalledTimes(1))
  })

  it('calls onerror on non-200 response', async () => {
    const onerror = vi.fn()
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(null, 401))

    fetchEventSource({ url: 'http://test.com', onerror })
    await waitFor(() => expect(onerror).toHaveBeenCalledTimes(1))
    expect(onerror).toHaveBeenCalledWith(expect.objectContaining({
      message: expect.stringContaining('401'),
    }))
  })

  it('sends auth headers when provided', async () => {
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(createReadableStream([])))

    fetchEventSource({
      url: 'http://test.com',
      headers: { Authorization: 'Bearer test-token' },
    })
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('http://test.com', {
      headers: { Authorization: 'Bearer test-token' },
      signal: expect.any(AbortSignal),
    }))
  })

  it('calls onmessage with data from SSE lines', async () => {
    const onmessage = vi.fn()
    const stream = createReadableStream(stringToChunks('data: {"msg":"hello"}\n\n'))
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(stream))

    fetchEventSource({ url: 'http://test.com', onmessage })
    await waitFor(() => expect(onmessage).toHaveBeenCalledWith('{"msg":"hello"}'))
  })

  it('calls onclose when stream ends normally', async () => {
    const onclose = vi.fn()
    const stream = createReadableStream(stringToChunks('data: hello\n\n'))
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(stream))

    fetchEventSource({ url: 'http://test.com', onclose })
    await waitFor(() => expect(onclose).toHaveBeenCalledTimes(1))
  })

  it('aborts when controller.abort() is called', async () => {
    const onclose = vi.fn()
    const onerror = vi.fn()
    let rejectFetch: (err: Error) => void
    const fetchPromise = new Promise<Response>((_, reject) => {
      rejectFetch = reject
    })
    global.fetch = vi.fn().mockReturnValue(fetchPromise)

    const controller = fetchEventSource({ url: 'http://test.com', onclose, onerror })
    controller.abort()

    rejectFetch!(new DOMException('Aborted', 'AbortError'))
    await waitFor(() => expect(onclose).toHaveBeenCalledTimes(1))
    expect(onerror).not.toHaveBeenCalled()
  })

  it('extracts data while ignoring event type lines', async () => {
    const onmessage = vi.fn()
    const stream = createReadableStream(stringToChunks('event: ping\ndata: {}\n\n'))
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(stream))

    fetchEventSource({ url: 'http://test.com', onmessage })
    await waitFor(() => expect(onmessage).toHaveBeenCalledTimes(1))
    expect(onmessage).toHaveBeenCalledWith('{}')
  })

  it('handles empty data lines', async () => {
    const onmessage = vi.fn()
    const stream = createReadableStream(stringToChunks('data: \n\n'))
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(stream))

    fetchEventSource({ url: 'http://test.com', onmessage })
    await waitFor(() => expect(onmessage).not.toHaveBeenCalled())
  })

  it('handles multiline data', async () => {
    const onmessage = vi.fn()
    const stream = createReadableStream(stringToChunks('data: line1\ndata: line2\n\n'))
    global.fetch = vi.fn().mockResolvedValue(createMockResponse(stream))

    fetchEventSource({ url: 'http://test.com', onmessage })
    await waitFor(() => expect(onmessage).toHaveBeenCalledWith('line1\nline2'))
  })
})
