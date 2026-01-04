/**
 * Calculadora de ITP (Impuesto a las Transmisiones Patrimoniales).
 * 
 * Calcula el 2% para comprador y 2% para vendedor.
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

export function CalculadoraITP() {
  const [valorCatastral, setValorCatastral] = useState('');
  const [resultado, setResultado] = useState(null);

  const calcular = () => {
    const valor = parseFloat(valorCatastral.replace(/\./g, '').replace(',', '.'));
    if (isNaN(valor) || valor <= 0) {
      setResultado(null);
      return;
    }

    const itpComprador = valor * 0.02;
    const itpVendedor = valor * 0.02;
    const total = itpComprador + itpVendedor;

    setResultado({
      itpComprador,
      itpVendedor,
      total,
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
        ITP - Transmisiones Patrimoniales
      </h3>
      <p className="text-sm text-gray-500 dark:text-slate-400 mb-4">
        Calcula el impuesto del 2% para comprador y vendedor.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
            Valor catastral del inmueble ($)
          </label>
          <input
            type="text"
            value={valorCatastral}
            onChange={(e) => setValorCatastral(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: 500000"
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <Button variant="primary" onClick={calcular} className="w-full">
          Calcular
        </Button>

        {resultado && (
          <div className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg mt-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-slate-400">ITP Comprador (2%):</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white tabular-nums">
                {formatearPesos(resultado.itpComprador)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-slate-400">ITP Vendedor (2%):</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white tabular-nums">
                {formatearPesos(resultado.itpVendedor)}
              </span>
            </div>
            <div className="flex justify-between items-center border-t border-gray-200 dark:border-slate-700 pt-2">
              <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Total ITP:</span>
              <span className="text-lg font-bold text-rose-600 dark:text-rose-400 tabular-nums">
                {formatearPesos(resultado.total)}
              </span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

export default CalculadoraITP;
