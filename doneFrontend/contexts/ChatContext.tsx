'use client'
import React, { createContext, useContext } from 'react'

type ChatCtxType = { /* placeholder */ }
const ChatCtx = createContext<ChatCtxType>({})

export function ChatProvider({ children }: { children: React.ReactNode }) {
  return <ChatCtx.Provider value={{}}>{children}</ChatCtx.Provider>
}
export const useChat = () => useContext(ChatCtx)
