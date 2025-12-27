import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { X, Send, Sparkles, TrendingUp, DollarSign, BarChart3, CalendarDays, FileDown, Loader2 } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useStreamingChat } from '../../hooks/useStreamingChat';

export function ChatPanel({ isOpen, onClose }) {
  const [exportando, setExportando] = useState(null);
  
  const {
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
    scrollToBottom
  } = useStreamingChat();

  // Contador de mensajes del usuario para límite
  const mensajesUsuario = messages.filter(m => m.role === 'user').length;

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Función para exportar mensaje a PDF
  const exportarPDF = async (mensajeId) => {
    if (!mensajeId || exportando) return;
    
    try {
      setExportando(mensajeId);
      
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/cfo/export-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ mensaje_id: mensajeId })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error exportando PDF');
      }
      
      // Descargar el PDF
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const disposition = response.headers.get('Content-Disposition');
      a.download = disposition?.split('filename=')[1]?.replace(/"/g, '') || 'reporte_cfo.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Error exportando PDF:', error);
      alert(error.message);
    } finally {
      setExportando(null);
    }
  };

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

  const handleSend = () => {
    if (!input.trim() || isTyping) return;
    sendMessage(input);
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
    clearHistory();
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
            initial={{ x: 600, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 600, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={clsx(
              'fixed right-0 top-16 h-[calc(100vh-4rem)] w-full sm:w-[600px]',
              'bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800',
              'shadow-2xl z-50 flex flex-col font-sans'
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
            <div 
              ref={messagesContainerRef}
              className="flex-1 overflow-y-auto px-2 py-4 space-y-4"
            >
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
                    'flex gap-2 group',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0 mt-1">
                      <Sparkles className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                    </div>
                  )}
                  <div
                    className={clsx(
                      'px-3 py-2.5 rounded-2xl text-sm font-sans relative',
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-sm max-w-[85%]'
                        : 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white rounded-tl-sm max-w-full'
                    )}
                  >
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-headings:my-2">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                    
                    {/* Botón Exportar PDF - visible después de cada respuesta */}
                    {msg.role === 'assistant' && msg.backendId && !msg.streaming && msg.content && (
                      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-slate-700">
                        <button
                          onClick={() => exportarPDF(msg.backendId)}
                          disabled={exportando === msg.backendId}
                          className={clsx(
                            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm',
                            'bg-blue-600 hover:bg-blue-700 text-white',
                            'disabled:opacity-50 disabled:cursor-not-allowed',
                            'transition-all duration-200 shadow-sm hover:shadow-md'
                          )}
                        >
                          {exportando === msg.backendId ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Generando PDF...</span>
                            </>
                          ) : (
                            <>
                              <FileDown className="w-4 h-4" />
                              <span>📄 Exportar a PDF</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
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

            {/* Avisos de límite de mensajes */}
            {mensajesUsuario >= 25 && mensajesUsuario < 27 && (
              <div className="mx-4 mb-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800/30 rounded-lg">
                <p className="text-sm text-yellow-700 dark:text-yellow-400 flex items-center gap-2">
                  <span>⚠️</span>
                  <span>Quedan pocos mensajes en esta conversación. Considerá iniciar una nueva para mejor precisión.</span>
                </p>
              </div>
            )}
            
            {mensajesUsuario >= 27 && (
              <div className="mx-4 mb-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/30 rounded-lg">
                <p className="text-sm text-red-700 dark:text-red-400 flex items-center gap-2 mb-2">
                  <span>🔴</span>
                  <span>Límite de conversación alcanzado. Iniciá una nueva conversación para continuar.</span>
                </p>
                <button
                  onClick={handleClearHistory}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  🔄 Nueva conversación
                </button>
              </div>
            )}

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

