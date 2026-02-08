import { useState } from 'react';
import { useHardware } from '../hooks/useHardware';
import { CardExplainer } from './CardExplainer';
import type { HardwareItem, DetectionResult } from '../types';

const statusConfig: Record<string, { label: string; className: string }> = {
  installed: { label: 'Instalado', className: 'hw-installed' },
  ordered: { label: 'Pedido', className: 'hw-ordered' },
  pending: { label: 'Pendiente', className: 'hw-pending' },
};

const categories = ['CPU', 'GPU', 'Motherboard', 'RAM', 'Almacenamiento', 'Fuente', 'Gabinete', 'Ventilacion', 'Adaptador', 'Otro'];

function AddForm({ onAdd, onCancel }: { onAdd: (item: Omit<HardwareItem, 'id'>) => void; onCancel: () => void }) {
  const [form, setForm] = useState<{ category: string; model: string; specs: string; status: HardwareItem['status']; price: number; notes: string }>({ category: 'GPU', model: '', specs: '', status: 'pending', price: 0, notes: '' });

  return (
    <div className="hw-form card">
      <h3 className="hw-form-title">Agregar componente</h3>
      <div className="hw-form-grid">
        <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="hw-input">
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input placeholder="Modelo" value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} className="hw-input" />
        <input placeholder="Especificaciones" value={form.specs} onChange={e => setForm({ ...form, specs: e.target.value })} className="hw-input" />
        <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value as HardwareItem['status'] })} className="hw-input">
          <option value="installed">Instalado</option>
          <option value="ordered">Pedido</option>
          <option value="pending">Pendiente</option>
        </select>
        <input type="number" placeholder="Precio USD" value={form.price || ''} onChange={e => setForm({ ...form, price: Number(e.target.value) })} className="hw-input" />
        <input placeholder="Notas" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} className="hw-input" />
      </div>
      <div className="hw-form-actions">
        <button className="btn-secondary" onClick={onCancel}>Cancelar</button>
        <button className="btn-primary" onClick={() => { if (form.model) onAdd(form); }} disabled={!form.model}>Agregar</button>
      </div>
    </div>
  );
}

// Convert a HardwareItem into a DetectionResult-like object for the CardExplainer
function hwToDetection(item: HardwareItem): DetectionResult {
  return {
    id: `hw_${item.id}`,
    name: `${item.model}`,
    category: 'hardware',
    status: item.status === 'installed' ? 'ok' : 'warning',
    message: item.specs,
    details: [
      `Categoria: ${item.category}`,
      `Modelo: ${item.model}`,
      `Specs: ${item.specs}`,
      `Estado: ${item.status}`,
      item.price ? `Precio: USD $${item.price}` : '',
      item.notes ? `Notas: ${item.notes}` : '',
    ].filter(Boolean).join('\n'),
  };
}

export function HardwareInventory() {
  const { installed, pending, totalCost, loading, addItem, updateItem, deleteItem } = useHardware();
  const [showForm, setShowForm] = useState(false);
  const [expandedCard, setExpandedCard] = useState<string | null>(null);

  if (loading) return <div className="view-container"><p>Cargando inventario...</p></div>;

  const handleDownloadDocx = () => {
    window.open('/api/docs/plan-maestro', '_blank');
  };

  const allItems = [...installed, ...pending];
  const expandedItem = expandedCard ? allItems.find(i => i.id === expandedCard) : null;

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h2 className="view-title">Inventario de Hardware</h2>
          <p className="view-subtitle">
            {installed.length} instalados, {pending.length} pendientes
            {totalCost > 0 && <span className="view-meta"> — Inversion estimada: USD ${totalCost.toLocaleString()}</span>}
          </p>
        </div>
        <div className="view-actions">
          <button className="btn-secondary" onClick={handleDownloadDocx}>Descargar Plan Maestro</button>
          <button className="btn-primary" onClick={() => setShowForm(true)}>+ Agregar</button>
        </div>
      </div>

      {showForm && (
        <AddForm
          onAdd={(item) => { addItem(item); setShowForm(false); }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {installed.length > 0 && (
        <>
          <h3 className="hw-section-title">Instalado</h3>
          <div className="hw-grid">
            {installed.map(item => (
              <HardwareCard
                key={item.id}
                item={item}
                isExpanded={expandedCard === item.id}
                onToggleExplainer={() => setExpandedCard(prev => prev === item.id ? null : item.id)}
                onUpdate={updateItem}
                onDelete={deleteItem}
              />
            ))}
          </div>
        </>
      )}

      {pending.length > 0 && (
        <>
          <h3 className="hw-section-title">Pedido / Pendiente</h3>
          <div className="hw-grid">
            {pending.map(item => (
              <HardwareCard
                key={item.id}
                item={item}
                isExpanded={expandedCard === item.id}
                onToggleExplainer={() => setExpandedCard(prev => prev === item.id ? null : item.id)}
                onUpdate={updateItem}
                onDelete={deleteItem}
              />
            ))}
          </div>
        </>
      )}

      {expandedItem && (
        <CardExplainer
          component={hwToDetection(expandedItem)}
          onClose={() => setExpandedCard(null)}
        />
      )}
    </div>
  );
}

function HardwareCard({
  item,
  isExpanded,
  onToggleExplainer,
  onUpdate,
  onDelete,
}: {
  item: HardwareItem;
  isExpanded: boolean;
  onToggleExplainer: () => void;
  onUpdate: (id: string, u: Partial<HardwareItem>) => void;
  onDelete: (id: string) => void;
}) {
  const cfg = statusConfig[item.status] || statusConfig.pending;

  return (
    <div className={`hw-card ${cfg.className} ${isExpanded ? 'hw-card-active' : ''}`}>
      <div className="hw-card-header">
        <span className="hw-category">{item.category}</span>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button
            className={`learn-btn ${isExpanded ? 'learn-btn-active' : ''}`}
            onClick={onToggleExplainer}
            title={isExpanded ? 'Cerrar explicacion' : 'Aprender sobre este componente'}
          >
            {isExpanded ? '✕' : '📖'}
          </button>
          <span className={`hw-status-badge ${cfg.className}`}>{cfg.label}</span>
        </div>
      </div>
      <div className="hw-model">{item.model}</div>
      <div className="hw-specs">{item.specs}</div>
      {item.price && <div className="hw-price">USD ${item.price.toLocaleString()}</div>}
      {item.notes && <div className="hw-notes">{item.notes}</div>}
      <div className="hw-card-actions">
        {item.status !== 'installed' && (
          <button className="hw-btn-small" onClick={() => onUpdate(item.id, { status: 'installed' })}>
            Marcar instalado
          </button>
        )}
        <button className="hw-btn-small hw-btn-danger" onClick={() => { if (confirm('Eliminar?')) onDelete(item.id); }}>
          Eliminar
        </button>
      </div>
    </div>
  );
}
