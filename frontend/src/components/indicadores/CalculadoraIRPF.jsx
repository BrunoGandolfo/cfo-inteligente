/**
 * Calculadora de IRPF sobre incrementos patrimoniales.
 * 
 * Tasa: 12% sobre la ganancia.
 * La ganancia se calcula: Precio venta - (Precio compra actualizado por UI)
 */

import { useState } from 'react';
import PropTypes from 'prop-types';
import Card from '../ui/Card';
import { Button } from '../ui/Button';

const formatearPesos = (valor) => {
  return new Intl.NumberFormat('es-UY', {
    style: 'currency',
    currency: 'UYU',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(valor);
};

export function CalculadoraIRPF({ valorUI }) {
  const [precioCompra, setPrecioCompra] = useState('');
  const [precioVenta, setPrecioVenta] = useState('');
  const [uiCompra, setUiCompra] = useState('');
  const [resultado, setResultado] = useState(null);

  const calcular = () => {
    const compra = parseFloat(precioCompra.replace(/\./g, '').replace(',', '.')) || 0;
    const venta = parseFloat(precioVenta.replace(/\./g, '').replace(',', '.')) || 0;
    const uiAnterior = parseFloat(uiCompra.replace(',', '.')) || valorUI;

    if (compra <= 0 || venta <= 0) {
      setResultado(null);
      return;
    }

    // Actualizar precio de compra por variación de UI
    const factorAjuste = valorUI / uiAnterior;
    const compraActualizada = compra * factorAjuste;

    // Ganancia = Venta - Compra actualizada
    const ganancia = venta - compraActualizada;

    // IRPF = 12% de la ganancia (solo si hay ganancia)
    const irpf = ganancia > 0 ? ganancia * 0.12 : 0;

    setResultado({
      compraActualizada,
      ganancia,
      irpf,
      factorAjuste,
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      calcular();
    }
  };

  return (
    <Card className="p-5">
      <h3 className="text-lg font-semibold text-text-primary mb-2">
        IRPF Incrementos Patrimoniales
      </h3>
      <p className="text-xs text-text-secondary mb-4">
        Calcula el 12% sobre la ganancia de venta de inmuebles.
      </p>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1">
            Precio de compra ($)
          </label>
          <input
            type="text"
            value={precioCompra}
            onChange={(e) => setPrecioCompra(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: 100000"
            className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-surface text-text-primary"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-primary mb-1">
            UI al momento de compra
          </label>
          <input
            type="text"
            value={uiCompra}
            onChange={(e) => setUiCompra(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Actual: ${valorUI}`}
            className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-surface text-text-primary"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-primary mb-1">
            Precio de venta ($)
          </label>
          <input
            type="text"
            value={precioVenta}
            onChange={(e) => setPrecioVenta(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ej: 150000"
            className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-surface text-text-primary"
          />
        </div>

        <Button variant="primary" onClick={calcular} className="w-full">
          Calcular IRPF
        </Button>

        {resultado && (
          <div className="bg-surface-alt p-4 rounded-lg mt-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-text-secondary">Compra actualizada:</span>
              <span className="text-md font-semibold text-text-primary tabular-nums">
                {formatearPesos(resultado.compraActualizada)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-text-secondary">Factor ajuste UI:</span>
              <span className="text-sm text-text-primary tabular-nums">
                {resultado.factorAjuste.toFixed(4)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-text-secondary">Ganancia:</span>
              <span className={`text-md font-semibold tabular-nums ${resultado.ganancia >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {formatearPesos(resultado.ganancia)}
              </span>
            </div>
            <div className="flex justify-between items-center border-t border-border pt-2">
              <span className="text-sm font-medium text-text-primary">IRPF a pagar (12%):</span>
              <span className="text-lg font-bold text-rose-600 dark:text-rose-400 tabular-nums">
                {formatearPesos(resultado.irpf)}
              </span>
            </div>
            {resultado.ganancia <= 0 && (
              <p className="text-xs text-text-muted text-center mt-2">
                No hay ganancia, no corresponde IRPF.
              </p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

CalculadoraIRPF.propTypes = {
  valorUI: PropTypes.number,
};

CalculadoraIRPF.defaultProps = {
  valorUI: 6.4243,
};

export default CalculadoraIRPF;
