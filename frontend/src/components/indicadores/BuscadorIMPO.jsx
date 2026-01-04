/**
 * Buscador de legislación IMPO.
 * 
 * Permite buscar leyes y decretos por número y año.
 */

import { useState } from 'react';
import { Search, FileText, AlertCircle, ExternalLink } from 'lucide-react';
import Card from '../ui/Card';
import axiosClient from '../../services/api/axiosClient';

export function BuscadorIMPO() {
  const [tipo, setTipo] = useState('ley');
  const [numero, setNumero] = useState('');
  const [anio, setAnio] = useState('');
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const buscar = async () => {
    if (!numero) {
      setError('Ingresá el número de la norma');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResultado(null);

      // Si hay año, buscar con año; si no, buscar sin año (búsqueda automática)
      const url = anio 
        ? `/api/impo/${tipo}/${numero}/${anio}`
        : `/api/impo/${tipo}/${numero}`;
      
      const { data } = await axiosClient.get(url);
      setResultado(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se encontró la norma');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      buscar();
    }
  };

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          Buscar Legislación
        </h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mb-4">
          Buscá leyes y decretos en la base de datos de IMPO.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Tipo */}
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white"
          >
            <option value="ley">Ley</option>
            <option value="decreto">Decreto</option>
          </select>

          {/* Número */}
          <input
            type="number"
            value={numero}
            onChange={(e) => setNumero(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Número"
            className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white"
          />

          {/* Año */}
          <input
            type="number"
            value={anio}
            onChange={(e) => setAnio(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Año (opcional)"
            className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white"
          />

          {/* Botón */}
          <button
            onClick={buscar}
            disabled={loading}
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
          >
            <Search size={16} />
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        </div>

        {/* Ejemplos */}
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="text-xs text-gray-400 dark:text-slate-500">Ejemplos:</span>
          <button
            onClick={() => { setTipo('ley'); setNumero('17437'); setAnio(''); }}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Ley 17437
          </button>
          <button
            onClick={() => { setTipo('decreto'); setNumero('500'); setAnio(''); }}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Decreto 500
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 mt-4 text-red-600 dark:text-red-400 text-sm">
            <AlertCircle size={16} />
            {error}
          </div>
        )}
      </Card>

      {/* Resultado */}
      {resultado && (
        <Card className="p-5">
          <div className="text-center">
            <span className="inline-block px-3 py-1 text-xs font-medium text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-3">
              {resultado.tipo}
            </span>

            <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              {resultado.tipo} {resultado.numero}/{resultado.anio}
            </h4>

            {resultado.titulo && resultado.titulo !== `${resultado.tipo} ${resultado.numero}/${resultado.anio}` && (
              <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                {resultado.titulo}
              </p>
            )}

            <a
              href={resultado.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              <ExternalLink size={18} />
              Ver documento completo en IMPO
            </a>
          </div>
        </Card>
      )}
    </div>
  );
}

export default BuscadorIMPO;
