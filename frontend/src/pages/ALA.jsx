/**
 * Página ALA (Anti-Lavado de Activos)
 * 
 * Verificación de debida diligencia contra listas:
 * PEP (Uruguay), ONU, OFAC, UE, GAFI
 * 
 * Decreto 379/018 - Arts. 17-18, 44
 * 
 * @author Sistema CFO Inteligente
 * @date Febrero 2026
 */

import { useEffect, useState } from 'react';
import { Shield, Search, CheckCircle, XCircle, AlertTriangle, Clock, FileText, ChevronDown, Save, Globe, Newspaper, BookOpen, Download, Eye, RotateCcw, Trash2 } from 'lucide-react';
import { useALA } from '../hooks/useALA';

// Colores por nivel de riesgo
const RIESGO_COLORS = {
  CRITICO: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-800 dark:text-red-200',
    border: 'border-red-300 dark:border-red-700',
    dot: 'bg-red-500',
  },
  ALTO: {
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    text: 'text-orange-800 dark:text-orange-200',
    border: 'border-orange-300 dark:border-orange-700',
    dot: 'bg-orange-500',
  },
  MEDIO: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    text: 'text-yellow-800 dark:text-yellow-200',
    border: 'border-yellow-300 dark:border-yellow-700',
    dot: 'bg-yellow-500',
  },
  BAJO: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-800 dark:text-green-200',
    border: 'border-green-300 dark:border-green-700',
    dot: 'bg-green-500',
  },
};

// Colores por nivel de diligencia
const DILIGENCIA_COLORS = {
  INTENSIFICADA: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
  NORMAL: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200',
  SIMPLIFICADA: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200',
};

function ALA() {
  const {
    verificaciones,
    verificacionActual,
    loading,
    loadingBusquedas,
    error,
    totalVerificaciones,
    ejecutarVerificacion,
    cargarVerificaciones,
    obtenerVerificacion,
    actualizarVerificacion,
    eliminarVerificacion,
    ejecutarBusquedasArt44,
    limpiarVerificacionActual,
    descargarCertificadoPDF,
  } = useALA();

  // Estado para descarga de PDF
  const [descargandoPDF, setDescargandoPDF] = useState(false);

  // Estado del formulario
  const [formData, setFormData] = useState({
    nombre_completo: '',
    tipo_documento: 'CI',
    numero_documento: '',
    nacionalidad: 'UY',
    fecha_nacimiento: '',
    es_persona_juridica: false,
    razon_social: '',
  });

  // Estado de búsquedas complementarias (Art. 44 C.4)
  const [busquedasComplementarias, setBusquedasComplementarias] = useState({
    busqueda_google_realizada: false,
    busqueda_google_observaciones: '',
    busqueda_news_realizada: false,
    busqueda_news_observaciones: '',
    busqueda_wikipedia_realizada: false,
    busqueda_wikipedia_observaciones: '',
  });

  // Cargar verificaciones al montar
  useEffect(() => {
    cargarVerificaciones(20, 0);
  }, [cargarVerificaciones]);

  // Actualizar búsquedas complementarias cuando cambia verificacionActual
  useEffect(() => {
    if (verificacionActual) {
      setBusquedasComplementarias({
        busqueda_google_realizada: verificacionActual.busqueda_google_realizada || false,
        busqueda_google_observaciones: verificacionActual.busqueda_google_observaciones || '',
        busqueda_news_realizada: verificacionActual.busqueda_news_realizada || false,
        busqueda_news_observaciones: verificacionActual.busqueda_news_observaciones || '',
        busqueda_wikipedia_realizada: verificacionActual.busqueda_wikipedia_realizada || false,
        busqueda_wikipedia_observaciones: verificacionActual.busqueda_wikipedia_observaciones || '',
      });
    }
  }, [verificacionActual]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleBusquedaChange = (e) => {
    const { name, value, type, checked } = e.target;
    setBusquedasComplementarias(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.nombre_completo.trim()) {
      return;
    }

    // Preparar datos (solo enviar campos con valor)
    const datos = {
      nombre_completo: formData.nombre_completo.trim(),
      tipo_documento: formData.tipo_documento,
      numero_documento: formData.numero_documento.trim() || null,
      nacionalidad: formData.nacionalidad || 'UY',
      fecha_nacimiento: formData.fecha_nacimiento || null,
      es_persona_juridica: formData.es_persona_juridica,
      razon_social: formData.es_persona_juridica ? formData.razon_social.trim() : null,
    };

    await ejecutarVerificacion(datos);
    
    // Refrescar historial
    await cargarVerificaciones(20, 0);
  };

  const handleGuardarObservaciones = async () => {
    if (!verificacionActual?.id) return;
    
    await actualizarVerificacion(verificacionActual.id, busquedasComplementarias);
  };

  const handleEjecutarBusquedasArt44 = async () => {
    if (!verificacionActual?.id) return;
    
    await ejecutarBusquedasArt44(verificacionActual.id);
  };

  // Handler para descargar certificado PDF
  const handleDescargarPDF = async () => {
    if (!verificacionActual?.id) return;
    
    setDescargandoPDF(true);
    try {
      await descargarCertificadoPDF(verificacionActual.id);
    } finally {
      setDescargandoPDF(false);
    }
  };

  // Handler para ver detalle de verificación del historial
  const handleVerDetalle = async (verificacionId) => {
    await obtenerVerificacion(verificacionId);
  };

  // Handler para eliminar verificación del historial
  const handleEliminarVerificacion = async (e, verificacion) => {
    e.stopPropagation(); // No disparar el click de ver detalle
    
    const confirmacion = window.confirm(
      `¿Eliminar verificación de "${verificacion.nombre_completo}"?`
    );
    
    if (!confirmacion) return;
    
    // Llamar eliminarVerificacion del hook (tiene su propio confirm interno,
    // pero el usuario ya confirmó arriba, así que será un segundo "¿seguro?")
    await eliminarVerificacion(verificacion.id);
  };

  // Verificar si las búsquedas ya fueron realizadas
  const busquedasYaRealizadas = verificacionActual && (
    verificacionActual.busqueda_google_realizada ||
    verificacionActual.busqueda_news_realizada ||
    verificacionActual.busqueda_wikipedia_realizada
  );

  const handleNuevaVerificacion = () => {
    limpiarVerificacionActual();
    setFormData({
      nombre_completo: '',
      tipo_documento: 'CI',
      numero_documento: '',
      nacionalidad: 'UY',
      fecha_nacimiento: '',
      es_persona_juridica: false,
      razon_social: '',
    });
    setBusquedasComplementarias({
      busqueda_google_realizada: false,
      busqueda_google_observaciones: '',
      busqueda_news_realizada: false,
      busqueda_news_observaciones: '',
      busqueda_wikipedia_realizada: false,
      busqueda_wikipedia_observaciones: '',
    });
  };

  // Renderizar resultado de una lista
  const renderResultadoLista = (nombre, resultado, totalRegistros) => {
    if (!resultado) return null;
    
    const esPositivo = resultado.hits > 0;
    const Icon = esPositivo ? XCircle : CheckCircle;
    const colorIcon = esPositivo ? 'text-red-500' : 'text-green-500';
    
    let mensaje = 'No verificado';
    if (resultado.checked) {
      if (nombre === 'PEP') {
        mensaje = esPositivo ? `Es PEP (${resultado.mejor_match || 'match encontrado'})` : 'No es PEP';
      } else if (nombre === 'GAFI') {
        mensaje = esPositivo ? `País en lista GAFI` : 'País sin riesgo GAFI';
      } else {
        mensaje = esPositivo ? `Encontrado (${resultado.hits} coincidencias)` : 'No encontrado';
      }
    } else if (resultado.error) {
      mensaje = resultado.error;
    }

    return (
      <div key={nombre} className="flex items-center gap-2 py-2">
        <Icon className={`w-5 h-5 ${colorIcon}`} />
        <span className="font-medium text-gray-700 dark:text-gray-300">{nombre}</span>
        {totalRegistros && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            ({totalRegistros.toLocaleString()} registros)
          </span>
        )}
        <span className="text-gray-600 dark:text-gray-400">—</span>
        <span className={esPositivo ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-600 dark:text-gray-400'}>
          {mensaje}
        </span>
      </div>
    );
  };

  const riesgoColors = verificacionActual ? RIESGO_COLORS[verificacionActual.nivel_riesgo] || RIESGO_COLORS.BAJO : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <Shield className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          Módulo ALA
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Anti-Lavado de Activos — Verificación de Debida Diligencia
        </p>
      </div>

      {/* Sección 1: Formulario de Verificación */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            Nueva Verificación ALA
          </h2>
          {verificacionActual && (
            <button
              onClick={handleNuevaVerificacion}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Limpiar y empezar nueva
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Nombre completo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nombre completo *
            </label>
            <input
              type="text"
              name="nombre_completo"
              value={formData.nombre_completo}
              onChange={handleInputChange}
              placeholder="Ej: Juan Pérez García"
              required
              className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Tipo y número de documento */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tipo de documento
              </label>
              <div className="relative">
                <select
                  name="tipo_documento"
                  value={formData.tipo_documento}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 appearance-none"
                >
                  <option value="CI">Cédula de Identidad</option>
                  <option value="RUT">RUT</option>
                  <option value="PASAPORTE">Pasaporte</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Número de documento
              </label>
              <input
                type="text"
                name="numero_documento"
                value={formData.numero_documento}
                onChange={handleInputChange}
                placeholder="Ej: 1.234.567-8"
                className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Nacionalidad y fecha de nacimiento */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Nacionalidad (código ISO)
              </label>
              <input
                type="text"
                name="nacionalidad"
                value={formData.nacionalidad}
                onChange={handleInputChange}
                placeholder="UY"
                maxLength={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Fecha de nacimiento
              </label>
              <input
                type="date"
                name="fecha_nacimiento"
                value={formData.fecha_nacimiento}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Persona jurídica */}
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                name="es_persona_juridica"
                checked={formData.es_persona_juridica}
                onChange={handleInputChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Persona jurídica</span>
            </label>
            {formData.es_persona_juridica && (
              <input
                type="text"
                name="razon_social"
                value={formData.razon_social}
                onChange={handleInputChange}
                placeholder="Razón social"
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            )}
          </div>

          {/* Botón submit */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={loading || !formData.nombre_completo.trim()}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Verificando contra 4 listas internacionales... (~30 seg)</span>
                </>
              ) : (
                <>
                  <Shield className="w-5 h-5" />
                  <span>Ejecutar Verificación</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Sección 2: Resultado de verificación */}
      {verificacionActual && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            Resultado de Verificación
          </h2>

          {/* Cards de resumen */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Nivel de Riesgo */}
            <div className={`rounded-lg p-4 border ${riesgoColors.bg} ${riesgoColors.border}`}>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Nivel de Riesgo</p>
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${riesgoColors.dot}`}></span>
                <span className={`text-xl font-bold ${riesgoColors.text}`}>
                  {verificacionActual.nivel_riesgo}
                </span>
              </div>
            </div>

            {/* Nivel de Diligencia */}
            <div className={`rounded-lg p-4 border ${DILIGENCIA_COLORS[verificacionActual.nivel_diligencia] || 'bg-gray-100'}`}>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Diligencia Requerida</p>
              <span className="text-xl font-bold">
                {verificacionActual.nivel_diligencia}
              </span>
            </div>

            {/* Puede Operar */}
            <div className={`rounded-lg p-4 border ${
              verificacionActual.nivel_riesgo === 'CRITICO' 
                ? 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700' 
                : 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700'
            }`}>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Puede Operar</p>
              <div className="flex items-center gap-2">
                {verificacionActual.nivel_riesgo === 'CRITICO' ? (
                  <>
                    <XCircle className="w-6 h-6 text-red-500" />
                    <span className="text-xl font-bold text-red-700 dark:text-red-300">NO</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-6 h-6 text-green-500" />
                    <span className="text-xl font-bold text-green-700 dark:text-green-300">SÍ</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* PEP Badge */}
          {verificacionActual.es_pep && (
            <div className="mb-4 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-300 dark:border-orange-700 rounded-lg">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                <span className="font-semibold text-orange-800 dark:text-orange-300">
                  Esta persona es PEP (Persona Políticamente Expuesta)
                </span>
              </div>
              <p className="text-sm text-orange-700 dark:text-orange-400 mt-1">
                Requiere diligencia intensificada según Art. 44 del Decreto 379/018
              </p>
            </div>
          )}

          {/* Detalle por lista */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Detalle por lista:
            </h3>
            <div className="space-y-1 bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4">
              {renderResultadoLista('PEP Uruguay', verificacionActual.resultado_pep, 5737)}
              {renderResultadoLista('ONU', verificacionActual.resultado_onu, 726)}
              {renderResultadoLista('OFAC', verificacionActual.resultado_ofac, 18598)}
              {renderResultadoLista('UE', verificacionActual.resultado_ue, 23471)}
              {renderResultadoLista('GAFI', verificacionActual.resultado_gafi)}
            </div>
          </div>

          {/* Hash de verificación y botón PDF */}
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              <span className="font-medium">Hash: </span>
              <code className="bg-gray-100 dark:bg-slate-700 px-2 py-1 rounded">
                {verificacionActual.hash_verificacion?.substring(0, 24)}...
              </code>
            </div>
            <button
              onClick={handleDescargarPDF}
              disabled={descargandoPDF || loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg flex items-center gap-2 transition-colors"
            >
              {descargandoPDF ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Generando...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Descargar Certificado PDF</span>
                </>
              )}
            </button>
          </div>

          {/* Búsquedas complementarias Art. 44 C.4 */}
          <div className="border-t border-gray-200 dark:border-slate-700 pt-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Art. 44 C.4 — Búsquedas Complementarias (Decreto 379/018)
            </h3>
            
            {/* Botón ejecutar búsquedas automáticas */}
            {!busquedasYaRealizadas && (
              <button
                onClick={handleEjecutarBusquedasArt44}
                disabled={loadingBusquedas || loading}
                className="mb-4 px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white font-medium rounded-lg flex items-center gap-2 transition-colors w-full justify-center"
              >
                {loadingBusquedas ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Buscando en Wikipedia, analizando con IA... (~15 seg)</span>
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    <span>Ejecutar Búsquedas Automáticas Art. 44 C.4</span>
                  </>
                )}
              </button>
            )}

            {/* Resultados de búsquedas */}
            {busquedasYaRealizadas && (
              <div className="space-y-4 mb-4">
                {/* Google / Análisis IA */}
                <div className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Globe className="w-5 h-5 text-blue-500" />
                    <span className="font-medium text-gray-800 dark:text-gray-200">Google / Análisis IA</span>
                    {verificacionActual.busqueda_google_realizada ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-400" />
                    )}
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {verificacionActual.busqueda_google_realizada ? 'Realizada' : 'No realizada'}
                    </span>
                  </div>
                  {verificacionActual.busqueda_google_observaciones && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                      {verificacionActual.busqueda_google_observaciones}
                    </p>
                  )}
                </div>

                {/* Noticias / Análisis IA */}
                <div className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Newspaper className="w-5 h-5 text-orange-500" />
                    <span className="font-medium text-gray-800 dark:text-gray-200">Noticias / Análisis IA</span>
                    {verificacionActual.busqueda_news_realizada ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-400" />
                    )}
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {verificacionActual.busqueda_news_realizada ? 'Realizada' : 'No realizada'}
                    </span>
                  </div>
                  {verificacionActual.busqueda_news_observaciones && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                      {verificacionActual.busqueda_news_observaciones}
                    </p>
                  )}
                </div>

                {/* Wikipedia */}
                <div className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <BookOpen className="w-5 h-5 text-green-500" />
                    <span className="font-medium text-gray-800 dark:text-gray-200">Wikipedia</span>
                    {verificacionActual.busqueda_wikipedia_realizada ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-400" />
                    )}
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {verificacionActual.busqueda_wikipedia_realizada ? 'Realizada' : 'No realizada'}
                    </span>
                  </div>
                  {verificacionActual.busqueda_wikipedia_observaciones && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                      {verificacionActual.busqueda_wikipedia_observaciones}
                    </p>
                  )}
                </div>

                {/* Botón para volver a ejecutar */}
                <button
                  onClick={handleEjecutarBusquedasArt44}
                  disabled={loadingBusquedas || loading}
                  className="text-sm text-purple-600 dark:text-purple-400 hover:underline disabled:opacity-50"
                >
                  {loadingBusquedas ? 'Ejecutando...' : '↻ Volver a ejecutar búsquedas'}
                </button>
              </div>
            )}

            {/* Observaciones manuales adicionales */}
            <div className="border-t border-gray-200 dark:border-slate-600 pt-4 mt-4">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Observaciones adicionales (manual)
              </h4>
              <textarea
                name="observaciones_adicionales"
                value={busquedasComplementarias.busqueda_google_observaciones || ''}
                onChange={(e) => setBusquedasComplementarias(prev => ({
                  ...prev,
                  busqueda_google_observaciones: e.target.value
                }))}
                placeholder="Agregar observaciones manuales sobre las búsquedas realizadas..."
                rows={3}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white resize-none"
              />
              <button
                onClick={handleGuardarObservaciones}
                disabled={loading}
                className="mt-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-medium rounded-lg flex items-center gap-2 transition-colors"
              >
                <Save className="w-4 h-4" />
                Guardar observaciones
              </button>
            </div>
          </div>

          {/* Botón Nueva Verificación */}
          <div className="border-t border-gray-200 dark:border-slate-700 pt-4 mt-4">
            <button
              onClick={handleNuevaVerificacion}
              className="px-4 py-2 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 font-medium rounded-lg flex items-center gap-2 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Nueva Verificación
            </button>
          </div>
        </div>
      )}

      {/* Sección 3: Historial */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          Historial de Verificaciones
          {totalVerificaciones > 0 && (
            <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
              ({totalVerificaciones} total)
            </span>
          )}
        </h2>

        {loading && verificaciones.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando historial...</p>
          </div>
        ) : verificaciones.length === 0 ? (
          <div className="text-center py-8">
            <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              No hay verificaciones registradas
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-slate-700">
                  <th className="text-left py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Nombre</th>
                  <th className="text-left py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Documento</th>
                  <th className="text-left py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Riesgo</th>
                  <th className="text-left py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Fecha</th>
                  <th className="text-center py-3 px-2 font-semibold text-gray-700 dark:text-gray-300 w-16"></th>
                </tr>
              </thead>
              <tbody>
                {verificaciones.map((v) => {
                  const colors = RIESGO_COLORS[v.nivel_riesgo] || RIESGO_COLORS.BAJO;
                  const isSelected = verificacionActual?.id === v.id;
                  return (
                    <tr 
                      key={v.id} 
                      className={`border-b border-gray-100 dark:border-slate-700/50 hover:bg-blue-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors ${
                        isSelected ? 'bg-blue-100 dark:bg-blue-900/30' : ''
                      }`}
                      onClick={() => handleVerDetalle(v.id)}
                      title="Click para ver detalle"
                    >
                      <td className="py-3 px-2 text-gray-900 dark:text-white">
                        <div className="flex items-center gap-2">
                          <Eye className="w-4 h-4 text-blue-500 opacity-50" />
                          {v.nombre_completo?.length > 30 
                            ? v.nombre_completo.substring(0, 30) + '...' 
                            : v.nombre_completo}
                        </div>
                      </td>
                      <td className="py-3 px-2 text-gray-600 dark:text-gray-400">
                        {v.tipo_documento} {v.numero_documento?.substring(0, 8)}
                        {v.numero_documento?.length > 8 ? '...' : ''}
                      </td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
                          <span className={`w-2 h-2 rounded-full ${colors.dot}`}></span>
                          {v.nivel_riesgo}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-gray-600 dark:text-gray-400">
                        {v.created_at 
                          ? new Date(v.created_at).toLocaleDateString('es-UY', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric'
                            })
                          : '-'}
                      </td>
                      <td className="py-3 px-2 text-center">
                        <button
                          onClick={(e) => handleEliminarVerificacion(e, v)}
                          className="p-1.5 text-red-400 hover:text-red-600 dark:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                          title={`Eliminar verificación de ${v.nombre_completo}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Error global */}
      {error && !loading && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700 dark:text-red-300">{error}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default ALA;
