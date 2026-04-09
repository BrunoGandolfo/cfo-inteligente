import { useState, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';
import { readSSEStream } from '../utils/sseHelper';

/**
 * Hook para chat con streaming SSE
 * Maneja conexión Server-Sent Events, estado de mensajes y memoria conversacional
 */
export function useStreamingChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const abortControllerRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTo({
          top: messagesContainerRef.current.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 50);
  }, []);

  const sendMessage = useCallback(async (message) => {
    if (!message.trim() || isTyping) return;

    const userMessage = message.trim();
    setInput('');
    setIsTyping(true);

    // CAMBIO 2: Limpiar historial visual (solo frontend, backend mantiene contexto)
    // Mostrar solo la pregunta actual y su respuesta
    const userMsg = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    
    // Crear mensaje assistant vacío para ir llenando
    const assistantMsgId = Date.now();
    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true
    };
    
    // Reemplazar todos los mensajes con solo pregunta + respuesta actual
    setMessages([userMsg, assistantMsg]);
    scrollToBottom();

    try {
      // AbortController para cancelar stream si es necesario
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const token = localStorage.getItem('token');
      const requestBody = {
        pregunta: userMessage,
        ...(conversationId && { conversation_id: conversationId })
      };

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/cfo/ask-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      let streamingContent = '';

      await readSSEStream(response.body, async ({ event, data }) => {
        try {
          if (event === 'conversation_id') {
            const parsed = JSON.parse(data);
            setConversationId(parsed.id);
          } else if (event === 'status' || event === 'sql') {
            JSON.parse(data);
          } else if (event === 'token') {
            streamingContent += data;

            setMessages(prev => prev.map(msg =>
              msg.id === assistantMsgId
                ? { ...msg, content: streamingContent, streaming: true }
                : msg
            ));

            scrollToBottom();
          } else if (event === 'done') {
            const parsed = JSON.parse(data);

            setMessages(prev => prev.map(msg =>
              msg.id === assistantMsgId
                ? { ...msg, streaming: false, backendId: parsed.mensaje_id }
                : msg
            ));

            if (parsed.conversation_id) {
              setConversationId(parsed.conversation_id);
            }
          } else if (event === 'error') {
            const parsed = JSON.parse(data);
            const errorMsg = parsed.message || 'Error desconocido';

            toast.error(errorMsg);
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMsgId
                ? { ...msg, content: `Error: ${errorMsg}`, streaming: false }
                : msg
            ));
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e, data);
        }
      });

    } catch (error) {
      if (error.name === 'AbortError') {
      } else {
        console.error('Error en streaming:', error);
        toast.error('Error al procesar la pregunta');
        
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMsgId
            ? { ...msg, content: 'Lo siento, hubo un error al procesar tu pregunta.', streaming: false }
            : msg
        ));
      }
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  }, [conversationId, isTyping, scrollToBottom]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    toast.success('Historial limpiado - Nueva conversación');
  }, []);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsTyping(false);
    }
  }, []);

  return {
    messages,
    input,
    setInput,
    isTyping,
    conversationId,
    messagesEndRef,
    messagesContainerRef,
    textareaRef,
    sendMessage,
    clearHistory,
    cancelStream,
    scrollToBottom
  };
}
