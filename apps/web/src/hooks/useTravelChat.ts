import { useCallback, useEffect, useState } from 'react'
import type { ChatMessage } from '../types/chat'
import {
  clearAllChatStorage,
  ensureSessionId,
  newSessionId,
  readAllMessages,
  writeAllMessages,
} from '../lib/chatStorage'
import { getMockReply } from '../lib/mockReplies'

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

  useEffect(() => {
    writeAllMessages(messages)
  }, [messages])

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
        const replyText = await getMockReply(trimmed)
        const botMsg = newMessage('assistant', replyText)
        setMessages((prev) => [...prev, botMsg])
      } finally {
        setIsTyping(false)
      }
    },
    [isTyping],
  )

  return {
    messages,
    isTyping,
    sendMessage,
    clearChat,
  }
}
