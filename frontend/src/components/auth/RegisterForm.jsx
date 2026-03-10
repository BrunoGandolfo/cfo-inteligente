import { useState, useMemo } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { UserPlus, User, Lock, AlertCircle } from 'lucide-react';

const DOMINIO_DEFAULT = 'grupoconexion.uy';
const DOMINIOS_EXCEPCION = {
  bgandolfo: 'cgmasociados.com'
};

function RegisterForm({ onSuccess, onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    prefijoEmail: '',
    nombre: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  // Calcular dominio y email completo en tiempo real
  const dominio = useMemo(() => {
    const prefijo = formData.prefijoEmail.toLowerCase().trim();
    return DOMINIOS_EXCEPCION[prefijo] || DOMINIO_DEFAULT;
  }, [formData.prefijoEmail]);

  const emailCompleto = useMemo(() => {
    const prefijo = formData.prefijoEmail.toLowerCase().trim();
    return prefijo ? `${prefijo}@${dominio}` : '';
  }, [formData.prefijoEmail, dominio]);

  const shouldShowEmailPreview = Boolean(emailCompleto) && !errors.prefijoEmail;

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.prefijoEmail.trim()) {
      newErrors.prefijoEmail = 'El usuario de email es requerido';
    } else if (formData.prefijoEmail.includes('@')) {
      newErrors.prefijoEmail = 'Solo ingresa tu usuario, sin @';
    }
    
    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El nombre es requerido';
    }
    
    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    // Para prefijoEmail, eliminar espacios y @
    const cleanValue = name === 'prefijoEmail' 
      ? value.replace(/[@\s]/g, '').toLowerCase()
      : value;
    
    setFormData(prev => ({ ...prev, [name]: cleanValue }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      await axios.post(
        `${import.meta.env.VITE_API_URL || 'https://cfo-inteligente-production.up.railway.app'}/api/auth/register`,
        {
          prefijo_email: formData.prefijoEmail.trim().toLowerCase(),
          nombre: formData.nombre.trim(),
          password: formData.password
        }
      );
      
      toast.success('¡Cuenta creada! Ya puedes iniciar sesión');
      if (onSuccess) onSuccess();
    } catch (error) {
      const message = error.response?.data?.detail || 'Error al crear cuenta';
      toast.error(message);
      setErrors({ submit: message });
    } finally {
      setLoading(false);
    }
  };

  const inputClass = (fieldName) => `
    w-full pl-10 pr-3 py-2 border 
    ${errors[fieldName] ? 'border-danger' : 'border-border'} 
    rounded-md bg-surface 
    text-text-primary 
    placeholder:text-text-muted 
    focus:outline-none focus:ring-2 focus:ring-accent
  `;

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      {errors.submit ? (
        <div className="bg-danger/10 border border-danger/30 text-danger px-4 py-3 rounded flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errors.submit}</span>
        </div>
      ) : null}
      
      {/* Nombre */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Nombre completo
        </label>
        <div className="relative">
          <User className="absolute left-3 top-2.5 h-5 w-5 text-text-muted" />
          <input
            type="text"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            className={inputClass('nombre')}
            placeholder="Ej: Natalia Araujo"
          />
        </div>
        {errors.nombre ? <p className="mt-1 text-sm text-danger">{errors.nombre}</p> : null}
      </div>
      
      {/* Email con autocompletado de dominio */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Email corporativo
        </label>
        <div className="relative">
          {/* Capa visual: muestra prefijo + dominio en gris */}
          <div 
            className={`absolute inset-0 flex items-center px-3 py-2 pointer-events-none border rounded-md bg-surface ${
              errors.prefijoEmail ? 'border-danger' : 'border-border'
            }`}
            aria-hidden="true"
          >
            {formData.prefijoEmail ? (
              <>
                <span className="text-text-primary">{formData.prefijoEmail}</span>
                <span className="text-text-muted">@{dominio}</span>
              </>
            ) : (
              <span className="text-text-muted">tunombre@{dominio}</span>
            )}
          </div>
          {/* Input real: invisible pero funcional */}
          <input
            type="text"
            name="prefijoEmail"
            value={formData.prefijoEmail}
            onChange={handleChange}
            className={`w-full px-3 py-2 border rounded-md bg-transparent text-transparent caret-text-primary focus:outline-none focus:ring-2 focus:ring-accent relative z-10 ${
              errors.prefijoEmail ? 'border-danger' : 'border-border'
            }`}
            autoComplete="off"
            spellCheck="false"
          />
        </div>
        {errors.prefijoEmail ? <p className="mt-1 text-sm text-danger">{errors.prefijoEmail}</p> : null}
        {shouldShowEmailPreview ? (
          <p className="mt-1 text-sm text-success">
            Tu email será: {emailCompleto}
          </p>
        ) : null}
      </div>
      
      {/* Contraseña */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Contraseña
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-2.5 h-5 w-5 text-text-muted" />
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className={inputClass('password')}
            placeholder="Mínimo 6 caracteres"
          />
        </div>
        {errors.password ? <p className="mt-1 text-sm text-danger">{errors.password}</p> : null}
      </div>
      
      {/* Confirmar Contraseña */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Confirmar contraseña
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-2.5 h-5 w-5 text-text-muted" />
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            className={inputClass('confirmPassword')}
            placeholder="Repetir contraseña"
          />
        </div>
        {errors.confirmPassword ? <p className="mt-1 text-sm text-danger">{errors.confirmPassword}</p> : null}
      </div>
      
      {/* Botón Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-success hover:bg-success/90 focus:outline-none focus:ring-2 focus:ring-success disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <UserPlus className="w-5 h-5" />
        {loading ? 'Creando cuenta...' : 'Crear cuenta'}
      </button>
      
      {/* Link para volver a login */}
      {onSwitchToLogin ? (
        <p className="text-center text-sm text-text-secondary">
          ¿Ya tienes cuenta?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-medium text-accent hover:text-accent-hover"
          >
            Iniciar sesión
          </button>
        </p>
      ) : null}
    </form>
  );
}

export default RegisterForm;
