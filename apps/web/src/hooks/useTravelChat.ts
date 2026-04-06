import { useCallback, useEffect, useState } from 'react'
import type { ChatMessage } from '../types/chat'
import {
  clearAllChatStorage,
  ensureSessionId,
  newSessionId,
  readAllMessages,
  readSessionId,
  writeAllMessages,
} from '../lib/chatStorage'
import { getHealth, getHistory, postChat } from '../lib/chatApi'

function newMessage(role: ChatMessage['role'], content: string): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    createdAt: new Date().toISOString(),
  }
}

export function useTravelChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    ensureSessionId()
    return readAllMessages()
  })
  const [isTyping, setIsTyping] = useState(false)
  const [historyReady, setHistoryReady] = useState(false)

  useEffect(() => {
    writeAllMessages(messages)
  }, [messages])

  useEffect(() => {
    let cancelled = false
    async function bootstrapHistory() {
      const sessionId = ensureSessionId()
      try {
        const health = await getHealth()
        if (health.database !== 'up') {
          if (!cancelled) {
            setMessages((prev) => {
              if (prev.length > 0) return prev
              return [
                newMessage(
                  'assistant',
                  'Backend chưa sẵn sàng (DB down). Bạn có thể chạy API/DB rồi thử lại.',
                ),
              ]
            })
          }
          return
        }
        const remote = await getHistory(sessionId)
        if (!cancelled && remote.length > 0) {
          setMessages(remote)
        }
      } catch {
        if (!cancelled) {
          setMessages((prev) => {
            if (prev.length > 0) return prev
            return [
              newMessage(
                'assistant',
                'Không thể kết nối backend lúc này. Bạn kiểm tra API trước khi tiếp tục.',
              ),
            ]
          })
        }
      } finally {
        if (!cancelled) setHistoryReady(true)
      }
    }

    void bootstrapHistory()
    return () => {
      cancelled = true
    }
  }, [])

  const clearChat = useCallback(() => {
    if (isTyping) return
    if (
      messages.length > 0 &&
      !window.confirm(
        'Xóa toàn bộ tin trên màn hình và bắt đầu đoạn chat mới? Dữ liệu demo trên máy bạn sẽ được xóa.',
      )
    ) {
      return
    }
    clearAllChatStorage()
    newSessionId()
    setMessages([])
  }, [isTyping, messages.length])

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isTyping) return

      const userMsg = newMessage('user', trimmed)
      setMessages((prev) => [...prev, userMsg])
      setIsTyping(true)
      try {
        const health = await getHealth()
        if (health.database !== 'up') {
          throw new Error('db-not-ready')
        }
        const sessionId = readSessionId() ?? ensureSessionId()
        const replyText = await postChat({ sessionId, message: trimmed, mode: 'agent' })
        const botMsg = newMessage('assistant', replyText)
        setMessages((prev) => [...prev, botMsg])
      } catch {
        const errorMsg = newMessage(
          'assistant',
          'Mình chưa thể xử lý vì backend/DB chưa sẵn sàng. Vui lòng thử lại sau ít phút.',
        )
        setMessages((prev) => [...prev, errorMsg])
      } finally {
        setIsTyping(false)
      }
    },
    [isTyping],
  )

  return {
    messages,
    isTyping,
    historyReady,
    sendMessage,
    clearChat,
  }
}
