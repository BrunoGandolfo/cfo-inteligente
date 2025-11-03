import { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { X, Send, Sparkles, TrendingUp, DollarSign, BarChart3, CalendarDays } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import clsx from 'clsx';
import axios from 'axios';
import toast from 'react-hot-toast';

export function ChatPanel({ isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-expand textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const sugerencias = [
    { icon: TrendingUp, text: '¿Cuál es la rentabilidad este mes?' },
    { icon: DollarSign, text: '¿Cuánto hemos facturado este año?' },
    { icon: BarChart3, text: 'Muéstrame el área más rentable' },
    { icon: CalendarDays, text: 'Comparar este trimestre vs anterior' },
  ];

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    
    const userMsg = { role: 'user', content: input.trim(), timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await axios.post('http://localhost:8000/api/cfo/ask', {
        pregunta: input.trim(),
        ...(conversationId && { conversation_id: conversationId })
      }, {
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // Usar la respuesta narrativa de Claude Sonnet 4.5
      const responseText = response.data.respuesta || 'Sin respuesta';

      // Guardar conversation_id para mantener memoria
      if (response.data.conversation_id) {
        if (!conversationId) {
          console.log('🆕 Nueva conversación iniciada:', response.data.conversation_id);
        } else {
          console.log('💬 Continuando conversación:', response.data.conversation_id);
        }
        setConversationId(response.data.conversation_id);
      }

      const aiMsg = { 
        role: 'assistant', 
        content: responseText,
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al consultar al CFO AI');
      const errorMsg = { 
        role: 'assistant', 
        content: 'Lo siento, hubo un error al procesar tu pregunta. Intenta nuevamente.', 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSuggestionClick = (text) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
    setConversationId(null);
    toast.success('Historial limpiado - Nueva conversación');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay para móvil */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 z-40 lg:hidden"
          />

          {/* Panel */}
          <motion.aside
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={clsx(
              'fixed right-0 top-16 h-[calc(100vh-4rem)] w-full sm:w-[400px]',
              'bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800',
              'shadow-2xl z-50 flex flex-col'
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">CFO AI</h2>
                  <p className="text-xs text-gray-500 dark:text-slate-400">Asistente Financiero</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {messages.length > 0 && (
                  <button
                    onClick={handleClearHistory}
                    className="text-xs px-2 py-1 rounded-md text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800"
                  >
                    Limpiar
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                  aria-label="Cerrar chat"
                >
                  <X className="w-5 h-5 text-gray-600 dark:text-slate-400" />
                </button>
              </div>
            </div>

            {/* Indicador de conversación activa */}
            {conversationId && messages.length > 0 && (
              <div className="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-100 dark:border-blue-800/30">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                    <span className="font-medium">Conversación activa</span>
                    <span className="text-blue-500/70">- Recordando contexto</span>
                  </div>
                  <button
                    onClick={handleClearHistory}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
                    title="Iniciar nueva conversación"
                  >
                    🔄 Nueva
                  </button>
                </div>
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center mt-12">
                  <div className="inline-flex p-4 bg-blue-50 dark:bg-blue-900/20 rounded-full mb-4">
                    <Sparkles className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    ¡Hola! Soy tu CFO AI
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-slate-400 mb-6 px-4">
                    Pregúntame lo que quieras sobre tus finanzas. Puedo analizar rentabilidad, 
                    ingresos, gastos y más.
                  </p>
                  
                  {/* Sugerencias iniciales */}
                  <div className="space-y-2 px-2">
                    <p className="text-xs text-gray-400 dark:text-slate-500 font-medium mb-3">
                      Sugerencias para empezar:
                    </p>
                    {sugerencias.map((sug, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestionClick(sug.text)}
                        className={clsx(
                          'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left',
                          'bg-gray-50 dark:bg-slate-800/50 hover:bg-gray-100 dark:hover:bg-slate-800',
                          'border border-gray-200 dark:border-slate-700',
                          'transition-all duration-200 hover:shadow-sm'
                        )}
                      >
                        <sug.icon className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
                        <span className="text-sm text-gray-700 dark:text-slate-200">{sug.text}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    'flex gap-3',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                      <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    </div>
                  )}
                  <div
                    className={clsx(
                      'px-4 py-2.5 rounded-2xl max-w-[85%] text-sm',
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-sm'
                        : 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white rounded-tl-sm'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-slate-700 flex items-center justify-center shrink-0 text-xs font-medium text-gray-700 dark:text-slate-200">
                      {localStorage.getItem('userName')?.[0]?.toUpperCase() || 'U'}
                    </div>
                  )}
                </div>
              ))}
              
              {isTyping && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl bg-gray-100 dark:bg-slate-800 rounded-tl-sm">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 dark:bg-slate-500 rounded-full animate-bounce" />
                      <span className="w-2 h-2 bg-gray-400 dark:bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <span className="w-2 h-2 bg-gray-400 dark:bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="flex gap-2 items-end">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Pregunta lo que quieras..."
                  rows={1}
                  disabled={isTyping}
                  className={clsx(
                    'flex-1 px-4 py-2.5 rounded-xl resize-none',
                    'bg-gray-100 dark:bg-slate-800',
                    'text-gray-900 dark:text-white text-sm',
                    'placeholder-gray-500 dark:placeholder-slate-400',
                    'border border-gray-200 dark:border-slate-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                    'transition-all duration-200'
                  )}
                  style={{ minHeight: '42px', maxHeight: '120px' }}
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isTyping}
                  className={clsx(
                    'p-2.5 rounded-xl shrink-0',
                    'bg-blue-600 hover:bg-blue-700 text-white',
                    'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-600',
                    'transition-all duration-200 hover:shadow-md',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                  )}
                  aria-label="Enviar mensaje"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs text-gray-400 dark:text-slate-500 mt-2 text-center">
                Presiona Enter para enviar, Shift+Enter para nueva línea
              </p>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

ChatPanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default ChatPanel;

