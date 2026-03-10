/**
 * Calculadora de honorarios notariales.
 * 
 * Calcula el 3% del monto de operación y muestra equivalencia en UR.
 */

import { useState } from 'react';
import PropTypes from 'prop-types';
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

export function CalculadoraHonorarios({ valorUR }) {
  const [monto, setMonto] = useState('');
  const [resultado, setResultado] = useState(null);

  const calcular = () => {
    const montoNum = parseFloat(monto.replace(/\./g, '').replace(',', '.'));
    if (isNaN(montoNum) || montoNum <= 0) {
      setResultado(null);
      return;
    }

    const honorario = montoNum * 0.03;
    const enUR = valorUR > 0 ? honorario / valorUR : 0;

    setResultado({
      honorario,
      enUR,
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      calcular();
    }
  };

  return (
    <Card className="p-5">
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        Honorarios Notariales
      </h3>
      <p className="text-sm text-text-secondary mb-4">
        Calcula el arancel base (3%) sobre el monto de la operación.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1">
            Monto de la operación ($)
          </label>
          <input
            type="text"
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: 100000"
            className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-surface text-text-primary"
          />
        </div>

        <Button variant="primary" onClick={calcular} className="w-full">
          Calcular
        </Button>

        {resultado && (
          <div className="bg-surface-alt p-4 rounded-lg mt-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-text-secondary">Honorario (3%):</span>
              <span className="text-lg font-bold text-text-primary tabular-nums">
                {formatearPesos(resultado.honorario)}
              </span>
            </div>
            <div className="flex justify-between items-center border-t border-border pt-2">
              <span className="text-sm text-text-secondary">Equivale a:</span>
              <span className="text-md font-semibold text-cyan-600 dark:text-cyan-400 tabular-nums">
                {resultado.enUR.toFixed(2)} UR
              </span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

CalculadoraHonorarios.propTypes = {
  valorUR: PropTypes.number,
};

CalculadoraHonorarios.defaultProps = {
  valorUR: 1841.56,
};

export default CalculadoraHonorarios;
