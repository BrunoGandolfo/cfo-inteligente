/**
 * Componente de Chat de Soporte flotante
 * 
 * Muestra un botón flotante que abre un panel de chat
 * para interactuar con el agente de soporte AI.
 */

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, RefreshCw } from 'lucide-react';
import { useSoporte } from '../../hooks/useSoporte';
import { motion, AnimatePresence } from 'framer-motion';

export default function SoporteChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const { mensajes, loading, enviarMensaje, limpiarChat } = useSoporte();
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll al último mensaje
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [mensajes]);

  // Focus en input al abrir
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    
    const mensaje = input;
    setInput('');
    await enviarMensaje(mensaje);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const mensajeBienvenida = mensajes.length === 0;

  return (
    <>
      {/* Botón flotante */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white p-4 rounded-full shadow-lg z-50 transition-all duration-200"
        title={isOpen ? 'Cerrar soporte' : 'Abrir soporte'}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </motion.button>

      {/* Panel de chat */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-24 right-6 w-[380px] h-[520px] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl z-50 flex flex-col border border-gray-200 dark:border-slate-700 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-lg">
                  <MessageCircle size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-base">Asistente CFO</h3>
                  <p className="text-xs text-blue-100">Soporte del sistema</p>
                </div>
              </div>
              <button 
                onClick={limpiarChat}
                className="flex items-center gap-1 text-xs bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded-lg transition-colors"
                title="Nueva conversación"
              >
                <RefreshCw size={14} />
                <span>Nuevo</span>
              </button>
            </div>

            {/* Mensajes */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-slate-800/50">
              {/* Mensaje de bienvenida */}
              {mensajeBienvenida && (
                <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                  <p className="font-semibold text-blue-800 dark:text-blue-300 flex items-center gap-2">
                    <span>¡Hola! 👋</span>
                  </p>
                  <p className="text-blue-700 dark:text-blue-400 mt-2 text-sm">
                    Soy el asistente de CFO Inteligente. Preguntame lo que necesites sobre el sistema.
                  </p>
                  <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-700">
                    <p className="text-xs text-blue-600 dark:text-blue-400 font-medium mb-2">
                      Ejemplos de preguntas:
                    </p>
                    <div className="space-y-1">
                      {[
                        '¿Cómo cargo un ingreso?',
                        '¿Dónde veo mis operaciones?',
                        '¿Cómo cambio mi contraseña?'
                      ].map((ejemplo, i) => (
                        <button
                          key={i}
                          onClick={() => setInput(ejemplo)}
                          className="block w-full text-left text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-800/30 px-2 py-1 rounded transition-colors"
                        >
                          • {ejemplo}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Historial de mensajes */}
              {mensajes.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-md'
                        : 'bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 text-gray-800 dark:text-slate-200 rounded-bl-md shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  </div>
                </div>
              ))}
              
              {/* Indicador de carga */}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 p-3 rounded-2xl rounded-bl-md shadow-sm">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              
              {/* Anchor para scroll */}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-3 border-t border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Escribí tu pregunta..."
                  className="flex-1 border border-gray-300 dark:border-slate-600 rounded-xl px-4 py-2.5 text-sm bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-slate-600 text-white p-2.5 rounded-xl transition-colors disabled:cursor-not-allowed"
                  title="Enviar mensaje"
                >
                  <Send size={20} />
                </button>
              </div>
              <p className="text-xs text-gray-400 dark:text-slate-500 mt-2 text-center">
                Enter para enviar
              </p>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
