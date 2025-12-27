import { useState, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';

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

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamingContent = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const chunk of lines) {
          if (!chunk.trim()) continue;

          const eventLines = chunk.split('\n');
          let eventType = 'message';
          const dataLines = [];

          for (const line of eventLines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
              dataLines.push(line.slice(5).trim());
            }
          }

          const dataStr = dataLines.join('\n');
          if (!dataStr) continue;

          try {
            // Eventos especiales
            if (eventType === 'conversation_id') {
              const parsed = JSON.parse(dataStr);
              const newConvId = parsed.id;
              setConversationId(newConvId);
            } 
            else if (eventType === 'status') {
              const parsed = JSON.parse(dataStr);
            } 
            else if (eventType === 'sql') {
              const parsed = JSON.parse(dataStr);
            } 
            else if (eventType === 'token') {
              // Token de texto - agregar tal cual (backend ya acumula palabras completas)
              streamingContent += dataStr;
              
              setMessages(prev => prev.map(msg =>
                msg.id === assistantMsgId
                  ? { ...msg, content: streamingContent, streaming: true }
                  : msg
              ));
              
              // Auto-scroll durante streaming
              scrollToBottom();
            } 
            else if (eventType === 'done') {
              const parsed = JSON.parse(dataStr);
              
              // Finalizar streaming y guardar ID del backend para exportar
              setMessages(prev => prev.map(msg =>
                msg.id === assistantMsgId
                  ? { ...msg, streaming: false, backendId: parsed.mensaje_id }
                  : msg
              ));
              
              if (parsed.conversation_id) {
                setConversationId(parsed.conversation_id);
              }
            } 
            else if (eventType === 'error') {
              const parsed = JSON.parse(dataStr);
              const errorMsg = parsed.message || 'Error desconocido';
              
              toast.error(errorMsg);
              setMessages(prev => prev.map(msg =>
                msg.id === assistantMsgId
                  ? { ...msg, content: `Error: ${errorMsg}`, streaming: false }
                  : msg
              ));
            }
          } catch (e) {
            console.error('Error parsing SSE event:', e, dataStr);
          }
        }
      }

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

