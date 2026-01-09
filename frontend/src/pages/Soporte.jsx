/**
 * Página de Soporte AI
 * 
 * Chat de asistencia para usuarios del sistema.
 * Usa streaming para mostrar respuestas de a poco.
 */

import { useState, useRef, useEffect } from 'react';
import { HelpCircle, Send, RefreshCw, ArrowLeft, Scale, ChevronDown, ChevronUp, Users, Clock, Bell, BookOpen, AlertCircle, CheckCircle2, Plus, FileText } from 'lucide-react';
import PropTypes from 'prop-types';
import { useSoporte } from '../hooks/useSoporte';

export default function Soporte({ onNavigate }) {
  const [input, setInput] = useState('');
  const { mensajes, loading, enviarMensaje, limpiarChat } = useSoporte();
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Detectar si es socio
  const esSocio = localStorage.getItem('esSocio')?.toLowerCase() === 'true';
  
  // Estado para sección de documentación de Expedientes
  const [expedientesDocOpen, setExpedientesDocOpen] = useState(false);

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

  // Sugerencias diferentes según rol
  const sugerencias = esSocio ? [
    '¿Cómo cargo un ingreso?',
    '¿Dónde veo mis operaciones?',
    '¿Qué es un retiro?',
    '¿Cómo se distribuyen utilidades?',
    '¿Cómo agrego un expediente judicial?',
    '¿Cómo funciona la sincronización de expedientes?'
  ] : [
    '¿Cómo cargo un ingreso?',
    '¿Cómo registro un gasto?',
    '¿Dónde veo mis operaciones?',
    '¿Cómo cambio mi contraseña?'
  ];

  // Mensaje de bienvenida según rol
  const textoAyuda = esSocio 
    ? 'Preguntame lo que necesites sobre cómo usar CFO Inteligente.'
    : 'Preguntame sobre cómo registrar ingresos y gastos.';

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
                {textoAyuda}
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
            
            {/* Documentación de Expedientes Judiciales */}
            {esSocio && (
              <div className="mt-8 border-t border-gray-200 dark:border-slate-700 pt-6">
                <button
                  onClick={() => setExpedientesDocOpen(!expedientesDocOpen)}
                  className="w-full flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:border-purple-400 dark:hover:border-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                      <Scale className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-gray-900 dark:text-white">Expedientes Judiciales</h3>
                      <p className="text-xs text-gray-500 dark:text-slate-400">Documentación completa del módulo</p>
                    </div>
                  </div>
                  {expedientesDocOpen ? (
                    <ChevronUp className="w-5 h-5 text-gray-500 dark:text-slate-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-500 dark:text-slate-400" />
                  )}
                </button>
                
                {expedientesDocOpen && (
                  <div className="mt-4 space-y-6 text-sm text-gray-700 dark:text-slate-300">
                    {/* Para Socios */}
                    <section className="bg-white dark:bg-slate-800 rounded-lg p-5 border border-gray-200 dark:border-slate-700">
                      <div className="flex items-center gap-2 mb-4">
                        <Users className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                        <h4 className="font-semibold text-gray-900 dark:text-white">Para Socios</h4>
                      </div>
                      
                      <div className="space-y-4">
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                            <Plus className="w-4 h-4" />
                            Agregar un nuevo expediente
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400 ml-6">
                            Haz clic en el botón <strong>"Agregar Expediente"</strong> en la parte superior de la página. 
                            Ingresa el <strong>IUE (Identificador Único de Expediente)</strong> del expediente que deseas monitorear. 
                            El sistema validará el IUE y comenzará a sincronizar automáticamente.
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            ¿Qué es el IUE?
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400 ml-6">
                            El <strong>IUE (Identificador Único de Expediente)</strong> es el número único que identifica 
                            cada expediente judicial en el sistema del Poder Judicial de Uruguay. Lo encontrarás en los 
                            documentos oficiales del expediente. Ejemplo: <code className="bg-gray-100 dark:bg-slate-700 px-1 rounded">123456/2023</code>
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Sincronización automática
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400 ml-6">
                            El sistema sincroniza automáticamente todos los expedientes activos <strong>cada día a las 8:00 AM</strong> 
                            (hora de Montevideo). Durante esta sincronización, se consultan los movimientos más recientes 
                            del Poder Judicial y se actualizan en la base de datos.
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                            <RefreshCw className="w-4 h-4" />
                            Re-sincronizar manualmente
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400 ml-6">
                            Puedes forzar una sincronización manual de un expediente específico haciendo clic en el botón 
                            <strong>"Re-sincronizar"</strong> en la fila correspondiente. También puedes sincronizar todos 
                            los expedientes usando el botón <strong>"Sincronizar Todos"</strong> en la parte superior.
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                            <BookOpen className="w-4 h-4" />
                            Ver historia del expediente
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400 ml-6">
                            Haz clic en el botón <strong>"Ver Historia"</strong> en cualquier fila de la tabla. 
                            El sistema generará un resumen inteligente usando IA que incluye:
                          </p>
                          <ul className="list-disc list-inside ml-6 mt-2 space-y-1 text-gray-600 dark:text-slate-400">
                            <li>Cronología de las etapas principales del proceso</li>
                            <li>Estado actual del expediente</li>
                            <li>Hitos importantes (decretos, resoluciones)</li>
                            <li>Plazos corriendo o vencidos</li>
                            <li>Sugerencias de próximos pasos</li>
                          </ul>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                            <Bell className="w-4 h-4" />
                            Notificaciones por WhatsApp
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400 ml-6">
                            Cuando se detectan nuevos movimientos después de la sincronización automática, el sistema 
                            envía notificaciones por WhatsApp a los socios configurados. Las notificaciones incluyen un 
                            resumen inteligente generado por IA de los movimientos más relevantes.
                          </p>
                          <p className="text-gray-600 dark:text-slate-400 ml-6 mt-2">
                            <strong>Configuración:</strong> Las notificaciones se configuran mediante variables de entorno 
                            en el servidor. Contacta al administrador para agregar o modificar números de WhatsApp.
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                            Información en la tabla
                          </h5>
                          <div className="ml-6 space-y-2 text-gray-600 dark:text-slate-400">
                            <p><strong>IUE:</strong> Identificador único del expediente</p>
                            <p><strong>Carátula:</strong> Descripción del caso</p>
                            <p><strong>Origen:</strong> Juzgado o sede de origen</p>
                            <p><strong>Última Sincronización:</strong> Fecha y hora de la última actualización</p>
                            <p><strong>Movimientos:</strong> Cantidad total de movimientos procesales registrados</p>
                            <p><strong>Estado:</strong> Indicador visual del estado del expediente</p>
                          </div>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                            Cards de resumen
                          </h5>
                          <div className="ml-6 space-y-2 text-gray-600 dark:text-slate-400">
                            <p><strong>Total Activos:</strong> Cantidad de expedientes activos en el sistema</p>
                            <p><strong>Sincronizados Hoy:</strong> Expedientes actualizados en las últimas 24 horas</p>
                            <p><strong>Pendientes:</strong> Expedientes con movimientos nuevos que requieren atención</p>
                          </div>
                        </div>
                      </div>
                    </section>
                    
                    {/* Para Colaboradores */}
                    <section className="bg-white dark:bg-slate-800 rounded-lg p-5 border border-gray-200 dark:border-slate-700">
                      <div className="flex items-center gap-2 mb-4">
                        <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        <h4 className="font-semibold text-gray-900 dark:text-white">Para Colaboradores</h4>
                      </div>
                      <p className="text-gray-600 dark:text-slate-400">
                        El módulo de Expedientes Judiciales es una funcionalidad <strong>exclusiva para socios</strong>. 
                        Los colaboradores no tienen acceso a esta sección del sistema.
                      </p>
                    </section>
                    
                    {/* Información Técnica */}
                    <section className="bg-white dark:bg-slate-800 rounded-lg p-5 border border-gray-200 dark:border-slate-700">
                      <div className="flex items-center gap-2 mb-4">
                        <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                        <h4 className="font-semibold text-gray-900 dark:text-white">Información Técnica</h4>
                      </div>
                      <div className="space-y-3 text-gray-600 dark:text-slate-400">
                        <p>
                          <strong>Fuente de datos:</strong> Los datos provienen directamente del sistema web del 
                          <strong> Poder Judicial de Uruguay</strong> mediante su servicio web oficial.
                        </p>
                        <p>
                          <strong>Sincronización:</strong> La sincronización automática se ejecuta diariamente a las 
                          8:00 AM (hora de Montevideo, UTC-3) mediante un scheduler programado.
                        </p>
                        <p>
                          <strong>Inteligencia Artificial:</strong> El sistema utiliza <strong>Claude AI</strong> para 
                          analizar los movimientos procesales y generar resúmenes ejecutivos inteligentes que facilitan 
                          la comprensión del estado y evolución del expediente.
                        </p>
                        <p>
                          <strong>Notificaciones:</strong> Las notificaciones por WhatsApp se envían automáticamente 
                          cuando se detectan nuevos movimientos después de la sincronización diaria, utilizando la 
                          plataforma <strong>Twilio</strong>.
                        </p>
                      </div>
                    </section>
                    
                    {/* Preguntas Frecuentes */}
                    <section className="bg-white dark:bg-slate-800 rounded-lg p-5 border border-gray-200 dark:border-slate-700">
                      <div className="flex items-center gap-2 mb-4">
                        <HelpCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                        <h4 className="font-semibold text-gray-900 dark:text-white">Preguntas Frecuentes</h4>
                      </div>
                      <div className="space-y-4">
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-1">
                            ¿Cada cuánto se actualiza un expediente?
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400">
                            Los expedientes se actualizan automáticamente <strong>una vez al día a las 8:00 AM</strong>. 
                            También puedes forzar una actualización manual en cualquier momento usando el botón de 
                            re-sincronización.
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-1">
                            ¿Qué pasa si el expediente tiene un error?
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400">
                            Si hay un error al sincronizar (por ejemplo, IUE inválido o problema de conexión), el sistema 
                            registrará el error en los logs. Puedes intentar re-sincronizar manualmente. Si el problema 
                            persiste, verifica que el IUE sea correcto y que el expediente exista en el sistema del Poder Judicial.
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-1">
                            ¿Cómo interpretar los movimientos?
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400">
                            Cada movimiento representa una actuación procesal (decreto, resolución, notificación, etc.). 
                            Usa la función <strong>"Ver Historia"</strong> para obtener un análisis inteligente generado por IA 
                            que explica el contexto y significado de los movimientos en lenguaje claro.
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-1">
                            ¿Puedo agregar expedientes de cualquier sede?
                          </h5>
                          <p className="text-gray-600 dark:text-slate-400">
                            Sí, puedes agregar expedientes de <strong>cualquier sede del Poder Judicial de Uruguay</strong>. 
                            El sistema consulta automáticamente la información del expediente independientemente de su sede de origen.
                          </p>
                        </div>
                      </div>
                    </section>
                  </div>
                )}
              </div>
            )}
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
