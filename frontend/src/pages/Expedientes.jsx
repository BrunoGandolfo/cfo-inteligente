import { useEffect, useState } from 'react';
import { useExpedientes } from '../hooks/useExpedientes';
import { 
  Scale, 
  RefreshCw, 
  Plus, 
  FileText, 
  Bell,
  Calendar,
  MapPin,
  AlertCircle,
  CheckCircle2,
  BookOpen,
  Trash2
} from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import axiosClient from '../services/api/axiosClient';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

function Expedientes() {
  const { 
    expedientes, 
    loading, 
    resumen,
    historiaActual,
    loadingHistoria,
    fetchExpedientes, 
    fetchResumen,
    sincronizarNuevo,
    reSincronizar,
    fetchExpediente,
    fetchHistoria,
    setHistoriaActual
  } = useExpedientes();
  
  const [showModal, setShowModal] = useState(false);
  const [syncingAll, setSyncingAll] = useState(false);
  const [syncingId, setSyncingId] = useState(null);
  const [addingExpediente, setAddingExpediente] = useState(false);
  const [showHistoriaModal, setShowHistoriaModal] = useState(false);
  const [iueInput, setIueInput] = useState('');

  useEffect(() => {
    fetchExpedientes();
    fetchResumen();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);  // Ejecutar solo al montar - funciones son estables con useCallback([])

  const handleSyncAll = async () => {
    const confirmacion = window.confirm(
      '¿Sincronizar todos los expedientes? Esto puede demorar varios minutos.'
    );
    if (!confirmacion) return;

    try {
      setSyncingAll(true);
      const { data } = await axiosClient.post('/api/expedientes/sincronizar-todos');
      toast.success(
        `Sincronización completada: ${data.sincronizados_ok}/${data.total_expedientes} expedientes`
      );
      fetchExpedientes();
      fetchResumen();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al sincronizar');
    } finally {
      setSyncingAll(false);
    }
  };

  const handleAddExpediente = async () => {
    if (!iueInput.trim()) {
      toast.error('Ingrese un IUE válido');
      return;
    }

    if (addingExpediente) {
      return; // Prevenir múltiples clicks
    }

    try {
      setAddingExpediente(true);
      await sincronizarNuevo(iueInput.trim());
      setShowModal(false);
      setIueInput('');
      fetchResumen();
    } catch (err) {
      // Error ya manejado en el hook
    } finally {
      setAddingExpediente(false);
    }
  };

  const handleReSync = async (id) => {
    setSyncingId(id);
    try {
      await reSincronizar(id);
      fetchResumen();
    } finally {
      setSyncingId(null);
    }
  };

  const handleVerHistoria = async (id) => {
    console.log('handleVerHistoria llamado con id:', id);
    setShowHistoriaModal(true); // Mostrar modal primero (con loading)
    await fetchHistoria(id);
    // No cerrar si falla, el usuario puede cerrar manualmente
  };

  const handleEliminar = async (expedienteId) => {
    if (!window.confirm('¿Está seguro de eliminar este expediente?')) return;

    try {
      await axiosClient.delete(`/api/expedientes/${expedienteId}`);
      toast.success('Expediente eliminado');
      fetchExpedientes();
      fetchResumen();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const handleRowClick = async (id) => {
    console.log('handleRowClick - ID:', id, 'Type:', typeof id);
    await fetchExpediente(id);
    // TODO: Abrir modal de detalle
    toast.info('Detalle de expediente (próximamente)');
  };

  if (loading && expedientes.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="text-gray-600 dark:text-slate-200">Cargando expedientes...</div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Scale className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Expedientes Judiciales
            </h1>
            {resumen?.movimientos_sin_notificar > 0 && (
              <div className="flex items-center gap-2 mt-1">
                <Bell className="w-4 h-4 text-orange-500" />
                <span className="text-sm text-orange-600 dark:text-orange-400">
                  {resumen.movimientos_sin_notificar} movimientos sin notificar
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            onClick={handleSyncAll}
            disabled={syncingAll}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${syncingAll ? 'animate-spin' : ''}`} />
            Sincronizar Todos
          </Button>
          <Button
            variant="primary"
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Agregar Expediente
          </Button>
        </div>
      </div>

      {/* Cards de Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-slate-400">Total Activos</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {resumen?.total_expedientes_activos || 0}
              </p>
            </div>
            <FileText className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-slate-400">Sincronizados Hoy</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {resumen?.sincronizados_hoy || 0}
              </p>
            </div>
            <CheckCircle2 className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-slate-400">Pendientes</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {resumen?.movimientos_sin_notificar || 0}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-orange-500" />
          </div>
        </Card>
      </div>

      {/* Tabla de Expedientes */}
      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Expedientes ({expedientes.length})
          </h3>
        </div>
        
        {loading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-gray-200 dark:bg-slate-800 rounded w-1/3" />
              <div className="h-10 bg-gray-100 dark:bg-slate-900 rounded" />
              <div className="h-10 bg-gray-100 dark:bg-slate-900 rounded" />
            </div>
          </div>
        ) : expedientes.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-16 h-16 text-gray-400 dark:text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No hay expedientes
            </h3>
            <p className="text-gray-500 dark:text-slate-400 mb-4">
              Agrega tu primer expediente para comenzar
            </p>
            <Button variant="primary" onClick={() => setShowModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Agregar Expediente
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50 dark:bg-slate-800/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    IUE
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Carátula
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Sede
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Último Movimiento
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Movimientos
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-slate-900 divide-y divide-gray-200 dark:divide-slate-800">
                {expedientes.map((exp) => {
                  return (
                  <tr
                    key={exp.id}
                    onClick={() => handleRowClick(exp.id)}
                    className="hover:bg-gray-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {exp.iue}
                        </span>
                        {/* TODO: Badge "nuevos" si tiene movimientos sin notificar */}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 dark:text-white max-w-md truncate">
                        {exp.caratula || 'Sin carátula'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-slate-400">
                        <MapPin className="w-4 h-4" />
                        {exp.iue_sede}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {exp.ultimo_movimiento ? (
                        <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-slate-400">
                          <Calendar className="w-4 h-4" />
                          {format(new Date(exp.ultimo_movimiento), 'dd/MM/yyyy')}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400 dark:text-slate-500">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {exp.cantidad_movimientos || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleReSync(exp.id);
                          }}
                          disabled={syncingId === exp.id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors disabled:opacity-50"
                        >
                          <RefreshCw className={`w-4 h-4 ${syncingId === exp.id ? 'animate-spin' : ''}`} />
                          {syncingId === exp.id ? 'Sincronizando...' : 'Re-sincronizar'}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleVerHistoria(exp.id);
                          }}
                          disabled={loadingHistoria}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-md transition-colors disabled:opacity-50"
                        >
                          <BookOpen className={`w-4 h-4 ${loadingHistoria ? 'animate-pulse' : ''}`} />
                          Ver Historia
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEliminar(exp.id);
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal Historia */}
      {showHistoriaModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-700 flex-shrink-0">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Historia del Expediente
                  </h2>
                  {historiaActual && (
                    <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
                      {historiaActual.iue} - {historiaActual.caratula}
                    </p>
                  )}
                </div>
                <button 
                  onClick={() => {
                    setShowHistoriaModal(false);
                    setHistoriaActual(null);
                  }} 
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ✕
                </button>
              </div>
            </div>
            
            {/* Body - scrollable */}
            <div className="px-6 py-4 overflow-y-auto flex-1">
              {loadingHistoria ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  <p className="mt-2 text-gray-500 dark:text-slate-400">Generando historia...</p>
                </div>
              ) : historiaActual ? (
                <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap text-gray-700 dark:text-slate-200">
                  {historiaActual.resumen}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 dark:text-slate-400">No se pudo cargar la historia</p>
                </div>
              )}
            </div>
            
            {/* Footer */}
            {historiaActual && (
              <div className="px-6 py-4 border-t border-gray-200 dark:border-slate-700 flex-shrink-0">
                <p className="text-xs text-gray-400 dark:text-slate-500">
                  Generado: {format(new Date(historiaActual.generado_en), "dd/MM/yyyy HH:mm", { locale: es })}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal Agregar Expediente */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Agregar Expediente
              </h2>
              <button
                onClick={() => {
                  setShowModal(false);
                  setIueInput('');
                }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  IUE (Sede-Número/Año)
                </label>
                <input
                  type="text"
                  value={iueInput}
                  onChange={(e) => setIueInput(e.target.value)}
                  placeholder="Ej: 2-12345/2023"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && handleAddExpediente()}
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-slate-400">
                  Formato: Sede-Número/Año (ej: 2-12345/2023)
                </p>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="ghost" onClick={() => {
                  setShowModal(false);
                  setIueInput('');
                }}>
                  Cancelar
                </Button>
                <Button 
                  variant="primary" 
                  onClick={handleAddExpediente}
                  disabled={addingExpediente}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className={`w-4 h-4 ${addingExpediente ? 'animate-spin' : ''}`} />
                  {addingExpediente ? 'Sincronizando...' : 'Sincronizar'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Expedientes;

