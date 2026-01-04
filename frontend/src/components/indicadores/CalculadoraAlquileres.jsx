/**
 * Calculadora de ajuste de alquileres.
 * 
 * Calcula el alquiler ajustado según variación de UR.
 */

import { useState } from 'react';
import Card from '../ui/Card';
import { Button } from '../ui/Button';

const formatearPesos = (valor) => {
  return new Intl.NumberFormat('es-UY', {
    style: 'currency',
    currency: 'UYU',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(valor);
};

export function CalculadoraAlquileres() {
  const [alquilerActual, setAlquilerActual] = useState('');
  const [variacionUR, setVariacionUR] = useState('5');
  const [resultado, setResultado] = useState(null);

  const calcular = () => {
    const alquiler = parseFloat(alquilerActual.replace(/\./g, '').replace(',', '.'));
    const variacion = parseFloat(variacionUR.replace(',', '.'));
    
    if (isNaN(alquiler) || alquiler <= 0 || isNaN(variacion)) {
      setResultado(null);
      return;
    }

    const ajuste = alquiler * (variacion / 100);
    const alquilerAjustado = alquiler + ajuste;

    setResultado({
      alquilerOriginal: alquiler,
      ajuste,
      alquilerAjustado,
      variacion,
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      calcular();
    }
  };

  return (
    <Card className="p-5">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Ajuste de Alquileres
      </h3>
      <p className="text-sm text-gray-500 dark:text-slate-400 mb-4">
        Calcula el alquiler ajustado según variación de UR.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
            Alquiler actual ($)
          </label>
          <input
            type="text"
            value={alquilerActual}
            onChange={(e) => setAlquilerActual(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: 25000"
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
            Variación UR (%)
          </label>
          <input
            type="text"
            value={variacionUR}
            onChange={(e) => setVariacionUR(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: 5"
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <Button variant="primary" onClick={calcular} className="w-full">
          Calcular
        </Button>

        {resultado && (
          <div className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg mt-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-slate-400">Alquiler original:</span>
              <span className="text-md text-gray-700 dark:text-slate-300 tabular-nums">
                {formatearPesos(resultado.alquilerOriginal)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-slate-400">Ajuste ({resultado.variacion}%):</span>
              <span className="text-md text-green-600 dark:text-green-400 tabular-nums">
                + {formatearPesos(resultado.ajuste)}
              </span>
            </div>
            <div className="flex justify-between items-center border-t border-gray-200 dark:border-slate-700 pt-2">
              <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Alquiler ajustado:</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white tabular-nums">
                {formatearPesos(resultado.alquilerAjustado)}
              </span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

export default CalculadoraAlquileres;
