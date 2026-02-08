import { useState, useCallback, useEffect } from 'react';
import type { HardwareItem } from '../types';

export function useHardware() {
  const [items, setItems] = useState<HardwareItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/hardware');
      if (res.ok) setItems(await res.json());
    } catch {
      // server not running
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const addItem = useCallback(async (item: Omit<HardwareItem, 'id'>) => {
    const res = await fetch('/api/hardware', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item),
    });
    if (res.ok) await load();
  }, [load]);

  const updateItem = useCallback(async (id: string, updates: Partial<HardwareItem>) => {
    const res = await fetch(`/api/hardware/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (res.ok) await load();
  }, [load]);

  const deleteItem = useCallback(async (id: string) => {
    const res = await fetch(`/api/hardware/${id}`, { method: 'DELETE' });
    if (res.ok) await load();
  }, [load]);

  const installed = items.filter(i => i.status === 'installed');
  const pending = items.filter(i => i.status !== 'installed');
  const totalCost = pending.reduce((sum, i) => sum + (i.price || 0), 0);

  return { items, installed, pending, totalCost, loading, addItem, updateItem, deleteItem, reload: load };
}
