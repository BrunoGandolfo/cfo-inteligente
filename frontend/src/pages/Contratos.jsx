import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useContratos } from '../hooks/useContratos';
import axiosClient from '../services/api/axiosClient';
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
  const tieneContratoSeleccionado = Boolean(contratoActual) && Boolean(contratoSeleccionadoId);
  const tieneCamposEditables = (contratoActual?.campos_editables?.campos?.length || 0) > 0;

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
      const response = await axiosClient.post(
        `/api/contratos/${contratoSeleccionadoId}/generar`,
        { valores: valoresCampos },
        { responseType: 'blob' }
      );

      // Descargar el archivo
      const blob = response.data;
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
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-text-primary">
          Módulo Notarial
        </h1>
        <p className="mt-2 text-text-secondary">
          Gestión de Contratos
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Estadísticas */}
        <div className="bg-surface border border-border rounded-lg shadow-sm p-4 md:p-6">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-accent" />
            <span className="text-lg font-semibold text-text-primary">
              Total de contratos: <span className="text-accent">{total}</span>
            </span>
          </div>
        </div>

        {/* Dropdown de selección */}
        <div className="bg-surface border border-border rounded-lg shadow-sm p-4 md:p-6">
          <div className="relative">
            <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted pointer-events-none" />
            <select
              value={contratoSeleccionadoId}
              onChange={handleSelectContrato}
              className="w-full pl-4 pr-10 py-3 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent appearance-none"
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
      </div>

      {/* Mensaje de advertencia */}
      <div className="bg-warning/10 border border-warning/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-warning text-xl">⚠️</span>
          <div>
            <p className="font-semibold text-warning mb-1">
              Importante sobre los contratos
            </p>
            <p className="text-sm text-text-secondary">
              Algunos contratos están completos y listos para usar. Otros son <strong>modelos de ejemplo</strong> donde, al completar los campos, algunos valores aparecerán en el documento y otros no. Los datos ingresados quedarán en los lugares correctos. <strong>El documento Word descargado puede requerir revisión y ajustes adicionales.</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Detalle del contrato seleccionado */}
      {tieneContratoSeleccionado ? (
        <div className="bg-surface border border-border rounded-lg shadow-sm p-4 md:p-6">
          <div className="mb-6">
            <h2 className="text-xl md:text-2xl font-bold text-text-primary mb-2">
              {contratoActual.titulo}
            </h2>
            <p className="text-text-secondary">
              Categoría: <span className="font-medium">{contratoActual.categoria?.charAt(0).toUpperCase() + contratoActual.categoria?.slice(1).replace(/_/g, ' ') || 'Sin categoría'}</span>
            </p>
            {contratoActual.campos_editables ? (
              <p className="text-sm text-text-muted mt-1">
                {contratoActual.campos_editables.total_campos || 0} campos editables
              </p>
            ) : null}
          </div>

          {/* Formulario de campos */}
          {tieneCamposEditables ? (
            <form onSubmit={handleGenerarContrato} className="space-y-4">
              <div className="mb-4 p-3 bg-success/10 border border-success/30 rounded-lg">
                <p className="text-sm text-success">
                  Todos los campos son opcionales. Complete solo los que necesite.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {contratoActual.campos_editables.campos
                  .sort((a, b) => (a.orden || 0) - (b.orden || 0))
                  .map((campo) => (
                    <div key={campo.id} className="space-y-1">
                      <label className="block text-sm font-medium text-text-secondary">
                        {campo.nombre}
                      </label>
                      <input
                        type="text"
                        value={valoresCampos[campo.id] || ''}
                        onChange={(e) => handleCampoChange(campo.id, e.target.value)}
                        placeholder={campo.placeholder_original || campo.contexto || 'Ingrese el valor...'}
                        className="w-full px-4 py-2 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent"
                      />
                      {campo.contexto ? (
                        <p className="text-xs text-text-muted italic">
                          {campo.contexto}
                        </p>
                      ) : null}
                    </div>
                  ))}
              </div>
              
              <div className="pt-4 border-t border-border">
                <button
                  type="submit"
                  className="w-full px-6 py-3 bg-accent hover:bg-accent-hover text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
                >
                  <FileCheck className="w-5 h-5" />
                  Generar Contrato
                </button>
              </div>
            </form>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">
                Este contrato no tiene campos editables disponibles
              </p>
            </div>
          )}
        </div>
      ) : null}

      {/* Estado inicial - sin contrato seleccionado */}
      {!contratoSeleccionadoId ? (
        <div className="bg-surface border border-border rounded-lg shadow-sm">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
              <p className="mt-4 text-text-secondary">Cargando contratos...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <p className="text-danger">
                {typeof error === 'string' ? error : error?.message || error?.msg || 'Error desconocido'}
              </p>
            </div>
          ) : contratosOrdenados.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">
                No hay contratos disponibles
              </p>
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-text-secondary">
                Selecciona un contrato del dropdown para comenzar
              </p>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

export default Contratos;
