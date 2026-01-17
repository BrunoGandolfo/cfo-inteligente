import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useContratos } from '../hooks/useContratos';
import { FileText, ChevronDown, FileCheck } from 'lucide-react';

function Contratos() {
  const {
    contratos,
    loading,
    error,
    total,
    fetchContratos,
    fetchContrato,
    contratoActual,
  } = useContratos();

  const [contratoSeleccionadoId, setContratoSeleccionadoId] = useState('');
  const [valoresCampos, setValoresCampos] = useState({});
  const [todosContratos, setTodosContratos] = useState([]);

  // Cargar todos los contratos al montar (en múltiples llamadas si hay más de 100)
  useEffect(() => {
    const cargarTodosContratos = async () => {
      try {
        // Primera llamada: primeros 100
        const primera = await fetchContratos({ limit: 100, skip: 0 });
        const totalContratos = primera?.total || 0;
        let contratosAcumulados = [...(primera?.contratos || [])];
        
        // Si hay más de 100, cargar el resto en llamadas adicionales
        if (totalContratos > 100) {
          const llamadasAdicionales = Math.ceil((totalContratos - 100) / 100);
          for (let i = 1; i <= llamadasAdicionales; i++) {
            const siguiente = await fetchContratos({ limit: 100, skip: i * 100 });
            if (siguiente?.contratos) {
              contratosAcumulados = [...contratosAcumulados, ...siguiente.contratos];
            }
          }
        }
        
        // Actualizar estado local con todos los contratos
        setTodosContratos(contratosAcumulados);
      } catch (err) {
        console.error('Error cargando contratos:', err);
      }
    };
    
    cargarTodosContratos();
  }, [fetchContratos]);

  // Cargar contrato cuando se selecciona
  useEffect(() => {
    if (contratoSeleccionadoId) {
      fetchContrato(contratoSeleccionadoId);
      setValoresCampos({}); // Resetear valores al cambiar contrato
    }
  }, [contratoSeleccionadoId, fetchContrato]);

  // Usar todosContratos si está disponible, sino usar contratos del hook
  const contratosDisponibles = todosContratos.length > 0 ? todosContratos : contratos;
  
  // Ordenar contratos alfabéticamente
  const contratosOrdenados = [...contratosDisponibles].sort((a, b) => 
    a.titulo.localeCompare(b.titulo)
  );

  const handleSelectContrato = (e) => {
    setContratoSeleccionadoId(e.target.value);
  };

  const handleCampoChange = (campoId, valor) => {
    setValoresCampos(prev => ({
      ...prev,
      [campoId]: valor
    }));
  };

  const handleGenerarContrato = async (e) => {
    e.preventDefault();
    
    if (!contratoSeleccionadoId || !contratoActual) {
      toast.error('Por favor selecciona un contrato');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_URL}/api/contratos/${contratoSeleccionadoId}/generar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ valores: valoresCampos })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error al generar contrato' }));
        throw new Error(errorData.detail || `Error ${response.status}`);
      }
      
      // Descargar el archivo
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${contratoActual.titulo.replace(/\s+/g, '_')}_completado.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Contrato generado y descargado exitosamente');
    } catch (err) {
      console.error('Error generando contrato:', err);
      toast.error(err.message || 'Error al generar el contrato');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Módulo Notarial
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Gestión de Contratos
        </p>
      </div>

      {/* Estadísticas */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <span className="text-lg font-semibold text-gray-900 dark:text-white">
            Total de contratos: <span className="text-blue-600 dark:text-blue-400">{total}</span>
          </span>
        </div>
      </div>

      {/* Dropdown de selección */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
        <div className="relative">
          <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          <select
            value={contratoSeleccionadoId}
            onChange={handleSelectContrato}
            className="w-full pl-4 pr-10 py-3 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
          >
            <option value="">Seleccionar contrato...</option>
            {contratosOrdenados.map((contrato) => (
              <option key={contrato.id} value={contrato.id}>
                {contrato.titulo}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Detalle del contrato seleccionado */}
      {contratoActual && contratoSeleccionadoId && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {contratoActual.titulo}
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Categoría: <span className="font-medium">{contratoActual.categoria?.charAt(0).toUpperCase() + contratoActual.categoria?.slice(1).replace(/_/g, ' ') || 'Sin categoría'}</span>
            </p>
            {contratoActual.campos_editables && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {contratoActual.campos_editables.total_campos || 0} campos editables
              </p>
            )}
          </div>

          {/* Formulario de campos */}
          {contratoActual.campos_editables?.campos && contratoActual.campos_editables.campos.length > 0 ? (
            <form onSubmit={handleGenerarContrato} className="space-y-4">
              {contratoActual.campos_editables.campos
                .sort((a, b) => (a.orden || 0) - (b.orden || 0))
                .map((campo) => (
                  <div key={campo.id} className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {campo.nombre}
                      {campo.requerido && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </label>
                    <input
                      type="text"
                      value={valoresCampos[campo.id] || ''}
                      onChange={(e) => handleCampoChange(campo.id, e.target.value)}
                      placeholder={campo.placeholder_original || campo.contexto || 'Ingrese el valor...'}
                      required={campo.requerido}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    {campo.contexto && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                        {campo.contexto}
                      </p>
                    )}
                  </div>
                ))}
              
              <div className="pt-4 border-t border-gray-200 dark:border-slate-700">
                <button
                  type="submit"
                  className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
                >
                  <FileCheck className="w-5 h-5" />
                  Generar Contrato
                </button>
              </div>
            </form>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                Este contrato no tiene campos editables disponibles
              </p>
            </div>
          )}
        </div>
      )}

      {/* Estado inicial - sin contrato seleccionado */}
      {!contratoSeleccionadoId && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando contratos...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <p className="text-red-600 dark:text-red-400">
                {typeof error === 'string' ? error : error?.message || error?.msg || 'Error desconocido'}
              </p>
            </div>
          ) : contratosOrdenados.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No hay contratos disponibles
              </p>
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-600 dark:text-gray-400">
                Selecciona un contrato del dropdown para comenzar
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Contratos;
