import { useState } from 'react';
import { X, Lock, AlertCircle, Check } from 'lucide-react';
import axiosClient from '../../services/api/axiosClient';
import toast from 'react-hot-toast';

function ChangePasswordModal({ isOpen, onClose }) {
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.currentPassword) {
      newErrors.currentPassword = 'La contraseña actual es requerida';
    }
    
    if (!formData.newPassword) {
      newErrors.newPassword = 'La nueva contraseña es requerida';
    } else if (formData.newPassword.length < 6) {
      newErrors.newPassword = 'La nueva contraseña debe tener al menos 6 caracteres';
    }
    
    if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }
    
    if (formData.currentPassword === formData.newPassword) {
      newErrors.newPassword = 'La nueva contraseña debe ser diferente a la actual';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      await axiosClient.post('/api/auth/change-password', {
        current_password: formData.currentPassword,
        new_password: formData.newPassword
      });
      
      toast.success('Contraseña actualizada correctamente');
      handleClose();
    } catch (error) {
      const message = error.response?.data?.detail || 'Error al cambiar contraseña';
      toast.error(message);
      setErrors({ submit: message });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    setErrors({});
    onClose();
  };

  const inputClass = (fieldName) => `
    w-full px-3 py-2 pl-10
    border ${errors[fieldName] ? 'border-danger' : 'border-border'}
    rounded-md bg-surface
    text-text-primary
    placeholder:text-text-muted
    focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent
  `;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-bg/70 transition-opacity"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-surface border border-border rounded-lg shadow-xl w-full max-w-md p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <Lock className="w-5 h-5 text-accent" />
              Cambiar Contraseña
            </h3>
            <button
              onClick={handleClose}
              className="text-text-muted hover:text-text-secondary"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.submit ? (
              <div className="bg-danger/10 border border-danger/30 text-danger px-4 py-3 rounded flex items-center gap-2">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{errors.submit}</span>
              </div>
            ) : null}
            
            {/* Contraseña actual */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Contraseña actual
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-text-muted" />
                <input
                  type="password"
                  name="currentPassword"
                  value={formData.currentPassword}
                  onChange={handleChange}
                  className={inputClass('currentPassword')}
                  placeholder="Tu contraseña actual"
                />
              </div>
              {errors.currentPassword ? (
                <p className="mt-1 text-sm text-danger">{errors.currentPassword}</p>
              ) : null}
            </div>
            
            {/* Nueva contraseña */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Nueva contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-text-muted" />
                <input
                  type="password"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleChange}
                  className={inputClass('newPassword')}
                  placeholder="Mínimo 6 caracteres"
                />
              </div>
              {errors.newPassword ? (
                <p className="mt-1 text-sm text-danger">{errors.newPassword}</p>
              ) : null}
            </div>
            
            {/* Confirmar nueva contraseña */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Confirmar nueva contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-text-muted" />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={inputClass('confirmPassword')}
                  placeholder="Repetir nueva contraseña"
                />
              </div>
              {errors.confirmPassword ? (
                <p className="mt-1 text-sm text-danger">{errors.confirmPassword}</p>
              ) : null}
            </div>
            
            {/* Botones */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-2 border border-border rounded-md text-text-secondary hover:bg-surface-alt transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
              >
                {loading ? (
                  'Guardando...'
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Guardar
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ChangePasswordModal;
