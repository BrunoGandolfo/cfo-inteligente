import { useEffect, useMemo, useState } from 'react';
import ModalBase from '../shared/ModalBase';

// Metadata por campo: label + placeholder + tipo + en qué clave del payload va.
// Los campos no listados acá caen al genérico (input text en datos_extra).
const CAMPOS_META = {
  rut: {
    label: 'RUT',
    placeholder: '12 dígitos',
    payloadKey: 'rut', // top-level
    inputMode: 'numeric',
    maxLength: 12,
  },
  ci: {
    label: 'Cédula de identidad',
    placeholder: 'Sin puntos ni guiones',
    payloadKey: 'ci',
    inputMode: 'numeric',
    maxLength: 10,
  },
  tipo_doc: {
    label: 'Tipo de documento',
    placeholder: 'CI / RUT / PASAPORTE',
    payloadKey: 'datos_extra.tipo_doc',
  },
  numero_doc: {
    label: 'Número de documento',
    placeholder: '',
    payloadKey: 'datos_extra.numero_doc',
  },
  pais: {
    label: 'País',
    placeholder: 'URUGUAY',
    payloadKey: 'datos_extra.pais',
  },
  nro_tramite: {
    label: 'Número de trámite',
    placeholder: '',
    payloadKey: 'datos_extra.nro_tramite',
  },
  nro_expediente: {
    label: 'Número de expediente',
    placeholder: '',
    payloadKey: 'datos_extra.nro_expediente',
  },
  nro_constancia: {
    label: 'Número de constancia',
    placeholder: '',
    payloadKey: 'datos_extra.nro_constancia',
  },
  nro_solicitud: {
    label: 'Número de solicitud',
    placeholder: '',
    payloadKey: 'datos_extra.nro_solicitud',
  },
  linea: {
    label: 'Línea',
    placeholder: '',
    payloadKey: 'datos_extra.linea',
  },
  tipo: {
    label: 'Tipo',
    placeholder: '',
    payloadKey: 'datos_extra.tipo',
  },
  principio_crc: {
    label: 'Principio CRC',
    placeholder: '',
    payloadKey: 'datos_extra.principio_crc',
  },
};

function metaPara(campo) {
  return CAMPOS_META[campo] || {
    label: campo,
    placeholder: '',
    payloadKey: `datos_extra.${campo}`,
  };
}

function ServiceForm({ servicio, isOpen, onClose, onSubmit, isLoading }) {
  const campos = useMemo(() => servicio?.campos || [], [servicio]);

  const valoresIniciales = useMemo(() => {
    const v = {};
    campos.forEach(c => { v[c] = ''; });
    return { campos: v, cliente_nombre: '', cliente_rut: '' };
  }, [campos]);

  const [valores, setValores] = useState(valoresIniciales);

  useEffect(() => {
    setValores(valoresIniciales);
  }, [valoresIniciales]);

  if (!servicio) return null;

  const handleChange = (campo, valor) => {
    setValores(prev => ({
      ...prev,
      campos: { ...prev.campos, [campo]: valor },
    }));
  };

  const handleMetaChange = (key, valor) => {
    setValores(prev => ({ ...prev, [key]: valor }));
  };

  const construirPayload = () => {
    const payload = { rut: undefined, ci: undefined, datos_extra: {} };
    campos.forEach(c => {
      const meta = metaPara(c);
      const valor = (valores.campos[c] || '').trim();
      if (!valor) return;
      if (meta.payloadKey === 'rut') payload.rut = valor;
      else if (meta.payloadKey === 'ci') payload.ci = valor;
      else if (meta.payloadKey.startsWith('datos_extra.')) {
        const k = meta.payloadKey.slice('datos_extra.'.length);
        payload.datos_extra[k] = valor;
      }
    });
    const nombre = valores.cliente_nombre.trim();
    const rutCliente = valores.cliente_rut.trim();
    if (nombre) payload.cliente_nombre = nombre;
    if (rutCliente) payload.cliente_rut = rutCliente;
    return payload;
  };

  const handleSubmit = async () => {
    const algunCampoConValor = campos.some(c => (valores.campos[c] || '').trim() !== '');
    if (!algunCampoConValor) {
      // El backend va a validar; igual cortamos antes para feedback rápido.
      throw new Error('Completá al menos un campo del formulario');
    }
    const payload = construirPayload();
    await onSubmit(payload);
  };

  return (
    <ModalBase
      isOpen={isOpen}
      onClose={onClose}
      title={`Consultar — ${servicio.nombre}`}
      onSubmit={handleSubmit}
      submitLabel={isLoading ? 'Consultando…' : 'Consultar DGI'}
      isLoading={isLoading}
      size="max-w-xl"
    >
      <div className="space-y-4">
        <p className="text-xs text-text-secondary">
          {servicio.descripcion}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {campos.map(c => {
            const meta = metaPara(c);
            return (
              <div key={c} className={campos.length === 1 ? 'sm:col-span-2' : ''}>
                <label className="block text-xs font-medium text-text-secondary mb-1">
                  {meta.label}
                </label>
                <input
                  type="text"
                  value={valores.campos[c] || ''}
                  onChange={(e) => handleChange(c, e.target.value)}
                  placeholder={meta.placeholder}
                  inputMode={meta.inputMode}
                  maxLength={meta.maxLength}
                  disabled={isLoading}
                  className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
                />
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-border space-y-3">
          <p className="text-[11px] uppercase tracking-wide font-semibold text-text-muted">
            Cliente asociado (opcional)
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Nombre del cliente
              </label>
              <input
                type="text"
                value={valores.cliente_nombre}
                onChange={(e) => handleMetaChange('cliente_nombre', e.target.value)}
                disabled={isLoading}
                className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                RUT del cliente
              </label>
              <input
                type="text"
                value={valores.cliente_rut}
                onChange={(e) => handleMetaChange('cliente_rut', e.target.value)}
                disabled={isLoading}
                inputMode="numeric"
                maxLength={12}
                className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
              />
            </div>
          </div>
        </div>

        {isLoading ? (
          <p className="text-xs text-text-secondary italic">
            La consulta a DGI puede demorar entre 20 y 60 segundos (resuelve un CAPTCHA y navega el portal).
          </p>
        ) : null}
      </div>
    </ModalBase>
  );
}

export default ServiceForm;
