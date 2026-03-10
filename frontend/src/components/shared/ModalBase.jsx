import React from 'react';
import { X } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ModalBase({
  isOpen,
  onClose,
  title,
  children,
  onSubmit,
  submitLabel = 'Guardar',
  isLoading = false,
  size = 'max-w-2xl',
  borderColor = 'border-border-strong'
}) {
  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await onSubmit();
    } catch (error) {
      toast.error('Error al guardar');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className={`bg-surface rounded-xl shadow-xl w-full border-t-4 transform transition-all duration-200 ease-out ${borderColor} ${size} animate-modal-enter`}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-text-primary">{title}</h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-secondary"
            disabled={isLoading}
          >
            <X size={24} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit}>
          <div className="p-6">
            {children}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-text-secondary hover:bg-surface-alt rounded-lg"
              disabled={isLoading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50"
            >
              {isLoading ? 'Guardando...' : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
