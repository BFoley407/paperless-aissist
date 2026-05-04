export type FetchEventSourceOptions = {
  url: string
  headers?: Record<string, string>
  onopen?: () => void
  onmessage?: (data: string) => void
  onerror?: (err: Error) => void
  onclose?: () => void
}

function safeCallVoid(fn: (() => void) | undefined): void {
  if (!fn) return
  try {
    fn()
  } catch (e) {
    console.error('fetchEventSource callback error:', e)
  }
}

function safeCallData(fn: ((data: string) => void) | undefined, data: string): void {
  if (!fn) return
  try {
    fn(data)
  } catch (e) {
    console.error('fetchEventSource callback error:', e)
  }
}

function safeCallError(fn: ((err: Error) => void) | undefined, err: Error): void {
  if (!fn) return
  try {
    fn(err)
  } catch (e) {
    console.error('fetchEventSource callback error:', e)
  }
}

export function fetchEventSource(options: FetchEventSourceOptions): AbortController {
  const controller = new AbortController()
  const { url, headers, onopen, onmessage, onerror, onclose } = options

  fetch(url, {
    headers,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      safeCallVoid(onopen)

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let dataBuffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          buffer += decoder.decode()
          break
        }
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (let line of lines) {
          if (line.endsWith('\r')) {
            line = line.slice(0, -1)
          }

          const idx = line.indexOf(':')
          if (idx !== -1) {
            const field = line.slice(0, idx)
            const value = line.slice(idx + 1).replace(/^ /, '')
            if (field === 'data') {
              if (dataBuffer) {
                dataBuffer += '\n'
              }
              dataBuffer += value
            }
          }

          if (line.startsWith('event:')) {
            // Event type field is ignored — we only care about data
          } else if (line === '') {
            if (dataBuffer) {
              safeCallData(onmessage, dataBuffer)
              dataBuffer = ''
            }
          }
        }
      }

      if (buffer) {
        let line = buffer
        if (line.endsWith('\r')) {
          line = line.slice(0, -1)
        }
        const idx = line.indexOf(':')
        if (idx !== -1) {
          const field = line.slice(0, idx)
          const value = line.slice(idx + 1).replace(/^ /, '')
          if (field === 'data') {
            if (dataBuffer) {
              dataBuffer += '\n'
            }
            dataBuffer += value
          }
        }
      }

      // Intentionally discard any incomplete event at stream end
      // (SSE events are only complete after a blank line)
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        safeCallError(onerror, err instanceof Error ? err : new Error(String(err)))
      }
    })
    .finally(() => {
      safeCallVoid(onclose)
    })

  return controller
}
