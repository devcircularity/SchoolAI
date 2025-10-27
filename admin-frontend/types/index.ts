export type Chat = { id: number; title: string }
export type Message = { id: number; chat_id: number; role: 'user' | 'assistant'; content: string }
