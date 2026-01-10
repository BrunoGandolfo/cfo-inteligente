import { useEffect, useState } from 'react';
import { useCasos } from '../hooks/useCasos';
import { 
  FileText, 
  Plus,
  Calendar,
  Edit,
  Trash2,
  AlertCircle
} from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

function Casos() {
  const { 
    casos, 
    casoActual,
    loading, 
    fetchCasos, 
    crearCaso,
    actualizarCaso,
    eliminarCaso,
    setCasoActual
  } = useCasos();
  
  const [showModal, setShowModal] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    titulo: '',
    estado: 'pendiente',
    prioridad: 'media',
    fecha_vencimiento: '',
    expediente_id: ''
  });

  useEffect(() => {
    fetchCasos();
  }, [fetchCasos]);

  const handleOpenModal = (caso = null) => {
    if (caso) {
      setEditMode(true);
      setCasoActual(caso);
      setFormData({
        titulo: caso.titulo || '',
        estado: caso.estado || 'pendiente',
        prioridad: caso.prioridad || 'media',
        fecha_vencimiento: caso.fecha_vencimiento ? format(new Date(caso.fecha_vencimiento), 'yyyy-MM-dd') : '',
        expediente_id: caso.expediente_id || ''
      });
    } else {
      setEditMode(false);
      setCasoActual(null);
      setFormData({
        titulo: '',
        estado: 'pendiente',
        prioridad: 'media',
        fecha_vencimiento: '',
        expediente_id: ''
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditMode(false);
    setCasoActual(null);
    setFormData({
      titulo: '',
      estado: 'pendiente',
      prioridad: 'media',
      fecha_vencimiento: '',
      expediente_id: ''
    });
  };

  const handleSubmit = async () => {
    if (!formData.titulo.trim()) {
      return;
    }

    const payload = {
      titulo: formData.titulo.trim(),
      estado: formData.estado,
      prioridad: formData.prioridad,
      fecha_vencimiento: formData.fecha_vencimiento || null,
      expediente_id: formData.expediente_id || null
    };

    // Remover null values
    Object.keys(payload).forEach(key => 
      payload[key] === null && delete payload[key]
    );

    if (editMode && casoActual) {
      await actualizarCaso(casoActual.id, payload);
    } else {
      await crearCaso(payload);
    }
    
    handleCloseModal();
  };

  const handleDelete = async (id) => {
    await eliminarCaso(id);
  };

  const getPrioridadBadge = (prioridad) => {
    const colors = {
      critica: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      alta: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      media: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      baja: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    };

    const labels = {
      critica: 'Crítica',
      alta: 'Alta',
      media: 'Media',
      baja: 'Baja'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[prioridad] || colors.media}`}>
        {labels[prioridad] || prioridad}
      </span>
    );
  };

  const getEstadoBadge = (estado) => {
    const colors = {
      pendiente: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      en_proceso: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      requiere_accion: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      cerrado: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    };

    const labels = {
      pendiente: 'Pendiente',
      en_proceso: 'En Proceso',
      requiere_accion: 'Requiere Acción',
      cerrado: 'Cerrado'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[estado] || colors.pendiente}`}>
        {labels[estado] || estado}
      </span>
    );
  };

  if (loading && casos.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="text-gray-600 dark:text-slate-200">Cargando casos...</div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Casos Legales
            </h1>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
              Gestión y seguimiento de casos legales
            </p>
          </div>
        </div>
        <Button
          variant="primary"
          onClick={() => handleOpenModal()}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Nuevo Caso
        </Button>
      </div>

      {/* Tabla de Casos */}
      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Casos ({casos.length})
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
        ) : casos.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-16 h-16 text-gray-400 dark:text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No hay casos
            </h3>
            <p className="text-gray-500 dark:text-slate-400 mb-4">
              Crea tu primer caso para comenzar
            </p>
            <Button variant="primary" onClick={() => handleOpenModal()}>
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Caso
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50 dark:bg-slate-800/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Título
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Prioridad
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Fecha Vencimiento
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-slate-400 uppercase">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-slate-900 divide-y divide-gray-200 dark:divide-slate-800">
                {casos.map((caso) => {
                  const fechaVencimiento = caso.fecha_vencimiento 
                    ? new Date(caso.fecha_vencimiento)
                    : null;
                  const hoy = new Date();
                  hoy.setHours(0, 0, 0, 0);
                  const vencido = fechaVencimiento && fechaVencimiento < hoy;
                  
                  return (
                    <tr
                      key={caso.id}
                      className="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-white max-w-md">
                          {caso.titulo}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getEstadoBadge(caso.estado)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getPrioridadBadge(caso.prioridad)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {fechaVencimiento ? (
                          <div className="flex items-center gap-1 text-sm">
                            <Calendar className={`w-4 h-4 ${vencido ? 'text-red-500' : 'text-gray-400'}`} />
                            <span className={vencido ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-600 dark:text-slate-400'}>
                              {format(fechaVencimiento, 'dd/MM/yyyy', { locale: es })}
                            </span>
                            {vencido && (
                              <AlertCircle className="w-4 h-4 text-red-500" />
                            )}
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400 dark:text-slate-500">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleOpenModal(caso)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                          >
                            <Edit className="w-4 h-4" />
                            Editar
                          </button>
                          <button
                            onClick={() => handleDelete(caso.id)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
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

      {/* Modal Crear/Editar Caso */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {editMode ? 'Editar Caso' : 'Nuevo Caso'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  Título *
                </label>
                <input
                  type="text"
                  value={formData.titulo}
                  onChange={(e) => setFormData({...formData, titulo: e.target.value})}
                  placeholder="Título del caso"
                  maxLength={300}
                  required
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                    Estado *
                  </label>
                  <select
                    value={formData.estado}
                    onChange={(e) => setFormData({...formData, estado: e.target.value})}
                    required
                    className="w-full px-4 py-2 border border-gray-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="pendiente">Pendiente</option>
                    <option value="en_proceso">En Proceso</option>
                    <option value="requiere_accion">Requiere Acción</option>
                    <option value="cerrado">Cerrado</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                    Prioridad *
                  </label>
                  <select
                    value={formData.prioridad}
                    onChange={(e) => setFormData({...formData, prioridad: e.target.value})}
                    required
                    className="w-full px-4 py-2 border border-gray-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="baja">Baja</option>
                    <option value="media">Media</option>
                    <option value="alta">Alta</option>
                    <option value="critica">Crítica</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  Fecha de Vencimiento
                </label>
                <input
                  type="date"
                  value={formData.fecha_vencimiento}
                  onChange={(e) => setFormData({...formData, fecha_vencimiento: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  ID Expediente (opcional)
                </label>
                <input
                  type="text"
                  value={formData.expediente_id}
                  onChange={(e) => setFormData({...formData, expediente_id: e.target.value})}
                  placeholder="UUID del expediente asociado"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <Button variant="ghost" onClick={handleCloseModal}>
                  Cancelar
                </Button>
                <Button 
                  variant="primary" 
                  onClick={handleSubmit}
                  disabled={!formData.titulo.trim()}
                >
                  {editMode ? 'Actualizar' : 'Crear'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Casos;
