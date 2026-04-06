import type { ChatMessage } from '../types/chat'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
  ? (import.meta.env.VITE_API_BASE_URL as string).replace(/\/+$/, '')
  : 'http://localhost:8000'

type ChatMode = 'simple' | 'agent'

interface PostChatInput {
  sessionId: string
  message: string
  mode?: ChatMode
}

interface ChatResponseDTO {
  reply: string
}

interface HistoryResponseDTO {
  session_id: string
  messages: Array<{
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    created_at?: string
  }>
}

interface HealthResponseDTO {
  status: string
  database: 'up' | 'down' | 'skipped'
  app_env?: string
}

function debugRequestError(endpoint: string, error: unknown): void {
  // Ghi ro context frontend/backend de phan biet CORS, API down hay sai base URL.
  console.error('[chatApi] Request failed', {
    endpoint,
    apiBaseUrl: API_BASE_URL,
    browserOrigin: window.location.origin,
    error,
  })
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json()
  } catch {
    return null
  }
}

function toUiMessage(message: HistoryResponseDTO['messages'][number]): ChatMessage | null {
  if (message.role !== 'user' && message.role !== 'assistant') return null
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: message.created_at ?? new Date().toISOString(),
  }
}

export async function getHealth(): Promise<HealthResponseDTO> {
  const endpoint = `${API_BASE_URL}/api/health`
  try {
    const res = await fetch(endpoint)
    const body = (await safeJson(res)) as HealthResponseDTO | null
    if (!res.ok || !body) {
      console.error('[chatApi] Invalid health response', {
        status: res.status,
        endpoint,
        browserOrigin: window.location.origin,
      })
      throw new Error('Không thể kiểm tra trạng thái backend.')
    }
    return body
  } catch (error) {
    debugRequestError(endpoint, error)
    throw error
  }
}

export async function getHistory(sessionId: string): Promise<ChatMessage[]> {
  const query = new URLSearchParams({ session_id: sessionId, limit: '200' })
  const endpoint = `${API_BASE_URL}/api/chat/history?${query.toString()}`
  try {
    const res = await fetch(endpoint)
    const body = (await safeJson(res)) as HistoryResponseDTO | null
    if (!res.ok || !body) {
      console.error('[chatApi] Invalid history response', {
        status: res.status,
        endpoint,
        browserOrigin: window.location.origin,
      })
      throw new Error('Không thể tải lịch sử chat từ backend.')
    }
    return body.messages.map(toUiMessage).filter((x): x is ChatMessage => x !== null)
  } catch (error) {
    debugRequestError(endpoint, error)
    throw error
  }
}

export async function postChat({
  sessionId,
  message,
  mode = 'agent',
}: PostChatInput): Promise<string> {
  const endpoint = `${API_BASE_URL}/api/chat`
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        mode,
      }),
    })
    const body = (await safeJson(res)) as ChatResponseDTO | null
    if (!res.ok || !body) {
      console.error('[chatApi] Invalid chat response', {
        status: res.status,
        endpoint,
        browserOrigin: window.location.origin,
      })
      throw new Error('Không thể gửi tin tới backend.')
    }
    return body.reply
  } catch (error) {
    debugRequestError(endpoint, error)
    throw error
  }
}

