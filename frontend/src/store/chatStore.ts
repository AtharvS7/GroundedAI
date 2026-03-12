/** Chat store — manages conversations and messages */

import { create } from 'zustand';
import type { ChatMessage, Conversation } from '@/types';

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  isContextInspectorOpen: boolean;
  selectedMessageId: string | null;
  isSidebarCollapsed: boolean;

  // Actions
  createConversation: () => string;
  setActiveConversation: (id: string | null) => void;
  addMessage: (conversationId: string, message: ChatMessage) => void;
  updateMessage: (conversationId: string, messageId: string, updates: Partial<ChatMessage>) => void;
  toggleContextInspector: () => void;
  setSelectedMessage: (id: string | null) => void;
  toggleSidebar: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  isContextInspectorOpen: false,
  selectedMessageId: null,
  isSidebarCollapsed: false,

  createConversation: () => {
    const id = crypto.randomUUID();
    const conversation: Conversation = {
      id,
      title: 'New Chat',
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    set((state) => ({
      conversations: [conversation, ...state.conversations],
      activeConversationId: id,
    }));
    return id;
  },

  setActiveConversation: (id) => set({ activeConversationId: id }),

  addMessage: (conversationId, message) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: [...conv.messages, message],
              updated_at: new Date().toISOString(),
              // Set title from first user message
              title:
                conv.messages.length === 0 && message.role === 'user'
                  ? message.content.slice(0, 50)
                  : conv.title,
            }
          : conv,
      ),
    })),

  updateMessage: (conversationId, messageId, updates) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: conv.messages.map((msg) =>
                msg.id === messageId ? { ...msg, ...updates } : msg,
              ),
            }
          : conv,
      ),
    })),

  toggleContextInspector: () =>
    set((state) => ({ isContextInspectorOpen: !state.isContextInspectorOpen })),

  setSelectedMessage: (id) => set({ selectedMessageId: id }),

  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
}));
