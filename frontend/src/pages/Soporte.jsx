/**
 * Página de Soporte AI
 * 
 * Chat de asistencia para usuarios del sistema.
 * Usa streaming para mostrar respuestas de a poco.
 */

import { useState, useRef, useEffect } from 'react';
import { HelpCircle, Send, RefreshCw, ArrowLeft } from 'lucide-react';
import PropTypes from 'prop-types';
import { useSoporte } from '../hooks/useSoporte';

export default function Soporte({ onNavigate }) {
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

  // Focus en input al cargar
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

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

  const sugerencias = [
    '¿Cómo cargo un ingreso?',
    '¿Dónde veo mis operaciones?',
    '¿Cómo cambio mi contraseña?',
    '¿Qué es un retiro?'
  ];

  const mensajeBienvenida = mensajes.length === 0;

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col max-w-4xl mx-auto">
      {/* Botón volver */}
      <button 
        onClick={() => onNavigate?.('dashboard')}
        className="flex items-center gap-2 text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 mb-3 px-2 transition-colors"
      >
        <ArrowLeft size={18} />
        <span className="text-sm">Volver al Dashboard</span>
      </button>

      {/* Header */}
      <div className="flex items-center justify-between mb-4 px-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <HelpCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Soporte</h1>
            <p className="text-sm text-gray-500 dark:text-slate-400">Asistente del sistema</p>
          </div>
        </div>
        {mensajes.length > 0 && (
          <button 
            onClick={limpiarChat}
            className="flex items-center gap-2 text-sm bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 px-3 py-2 rounded-lg transition-colors text-gray-700 dark:text-slate-300"
          >
            <RefreshCw size={16} />
            Nueva conversación
          </button>
        )}
      </div>

      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-4 space-y-4">
        {/* Mensaje de bienvenida */}
        {mensajeBienvenida && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8 mt-4">
              <div className="inline-flex p-4 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
                <HelpCircle className="w-10 h-10 text-green-600 dark:text-green-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                ¡Hola! Soy el asistente de soporte 👋
              </h2>
              <p className="text-gray-600 dark:text-slate-400">
                Preguntame lo que necesites sobre cómo usar CFO Inteligente.
              </p>
            </div>
            
            {/* Sugerencias */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {sugerencias.map((sug, i) => (
                <button
                  key={i}
                  onClick={() => setInput(sug)}
                  className="text-left px-4 py-3 rounded-lg border border-gray-200 dark:border-slate-700 hover:border-green-400 dark:hover:border-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-all text-sm text-gray-700 dark:text-slate-300"
                >
                  {sug}
                </button>
              ))}
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
              className={`max-w-[80%] p-4 rounded-2xl text-sm ${
                msg.role === 'user'
                  ? 'bg-green-600 text-white rounded-br-md'
                  : 'bg-gray-100 dark:bg-slate-800 text-gray-800 dark:text-slate-200 rounded-bl-md'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.role === 'assistant' && loading && i === mensajes.length - 1 && !msg.content && (
                <div className="flex items-center gap-1 mt-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Indicador de carga (cursor parpadeante al final del texto) */}
        {loading && mensajes.length > 0 && mensajes[mensajes.length - 1].content && (
          <span className="inline-block w-2 h-4 bg-green-500 animate-pulse ml-1" />
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="mt-4">
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribí tu pregunta..."
            className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 dark:disabled:bg-slate-600 text-white rounded-xl transition-colors disabled:cursor-not-allowed"
          >
            <Send size={20} />
          </button>
        </div>
        <p className="text-xs text-gray-400 dark:text-slate-500 mt-2 text-center">
          Enter para enviar
        </p>
      </form>
    </div>
  );
}

Soporte.propTypes = {
  onNavigate: PropTypes.func,
};
