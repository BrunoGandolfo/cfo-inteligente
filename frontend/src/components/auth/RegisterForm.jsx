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
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/register`,
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
    ${errors[fieldName] ? 'border-red-400' : 'border-gray-300 dark:border-slate-600'} 
    rounded-md bg-white dark:bg-slate-700 
    text-gray-900 dark:text-white 
    placeholder-gray-400 
    focus:outline-none focus:ring-2 focus:ring-indigo-500
  `;

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      {errors.submit && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errors.submit}</span>
        </div>
      )}
      
      {/* Nombre */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
          Nombre completo
        </label>
        <div className="relative">
          <User className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          <input
            type="text"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            className={inputClass('nombre')}
            placeholder="Ej: Natalia Araujo"
          />
        </div>
        {errors.nombre && <p className="mt-1 text-sm text-red-600">{errors.nombre}</p>}
      </div>
      
      {/* Email con autocompletado de dominio */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
          Email corporativo
        </label>
        <div className="relative">
          {/* Capa visual: muestra prefijo + dominio en gris */}
          <div 
            className={`absolute inset-0 flex items-center px-3 py-2 pointer-events-none border rounded-md bg-white dark:bg-slate-700 ${
              errors.prefijoEmail ? 'border-red-400' : 'border-gray-300 dark:border-slate-600'
            }`}
            aria-hidden="true"
          >
            {formData.prefijoEmail ? (
              <>
                <span className="text-gray-900 dark:text-white">{formData.prefijoEmail}</span>
                <span className="text-gray-400 dark:text-slate-500">@{dominio}</span>
              </>
            ) : (
              <span className="text-gray-400 dark:text-slate-500">tunombre@{dominio}</span>
            )}
          </div>
          {/* Input real: invisible pero funcional */}
          <input
            type="text"
            name="prefijoEmail"
            value={formData.prefijoEmail}
            onChange={handleChange}
            className={`w-full px-3 py-2 border rounded-md bg-transparent text-transparent caret-gray-900 dark:caret-white focus:outline-none focus:ring-2 focus:ring-indigo-500 relative z-10 ${
              errors.prefijoEmail ? 'border-red-400' : 'border-gray-300 dark:border-slate-600'
            }`}
            autoComplete="off"
            spellCheck="false"
          />
        </div>
        {errors.prefijoEmail && <p className="mt-1 text-sm text-red-600">{errors.prefijoEmail}</p>}
        {emailCompleto && !errors.prefijoEmail && (
          <p className="mt-1 text-sm text-green-600 dark:text-green-400">
            Tu email será: {emailCompleto}
          </p>
        )}
      </div>
      
      {/* Contraseña */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
          Contraseña
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className={inputClass('password')}
            placeholder="Mínimo 6 caracteres"
          />
        </div>
        {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
      </div>
      
      {/* Confirmar Contraseña */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
          Confirmar contraseña
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            className={inputClass('confirmPassword')}
            placeholder="Repetir contraseña"
          />
        </div>
        {errors.confirmPassword && <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>}
      </div>
      
      {/* Botón Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <UserPlus className="w-5 h-5" />
        {loading ? 'Creando cuenta...' : 'Crear cuenta'}
      </button>
      
      {/* Link para volver a login */}
      {onSwitchToLogin && (
        <p className="text-center text-sm text-gray-600 dark:text-slate-400">
          ¿Ya tienes cuenta?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
          >
            Iniciar sesión
          </button>
        </p>
      )}
    </form>
  );
}

export default RegisterForm;
