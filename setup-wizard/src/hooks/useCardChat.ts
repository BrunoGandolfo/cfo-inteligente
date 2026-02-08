import { useState, useCallback } from 'react';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface CardChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
}

// Store conversations per component so they persist while the tab is open
const chatStates = new Map<string, ChatMessage[]>();

export function useCardChat(componentId: string) {
  const [state, setState] = useState<CardChatState>({
    messages: chatStates.get(componentId) || [],
    loading: false,
    error: null,
  });

  const send = useCallback(async (
    userMessage: string,
    componentInfo: {
      name: string;
      status: string;
      message: string;
      details?: string;
    }
  ) => {
    const newUserMsg: ChatMessage = { role: 'user', content: userMessage };
    const updatedMessages = [...state.messages, newUserMsg];

    setState(prev => ({
      ...prev,
      messages: updatedMessages,
      loading: true,
      error: null,
    }));

    try {
      const res = await fetch('/api/claude/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          componentId,
          componentName: componentInfo.name,
          componentStatus: componentInfo.status,
          componentMessage: componentInfo.message,
          componentDetails: componentInfo.details,
          messages: updatedMessages,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${res.status}`);
      }

      const data = await res.json();
      const assistantMsg: ChatMessage = { role: 'assistant', content: data.response };
      const allMessages = [...updatedMessages, assistantMsg];

      chatStates.set(componentId, allMessages);

      setState({
        messages: allMessages,
        loading: false,
        error: null,
      });
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : String(err),
      }));
    }
  }, [componentId, state.messages]);

  const clear = useCallback(() => {
    chatStates.delete(componentId);
    setState({ messages: [], loading: false, error: null });
  }, [componentId]);

  return { ...state, send, clear };
}
