import { useState } from 'react';
import { Shield, BarChart3, FileText, Users, Lock, CheckCircle, Mail } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

export default function Home({ onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState('login');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    remember: false
  });
  const [loading, setLoading] = useState(false);
  const [registerData, setRegisterData] = useState({
    nombre: '',
    usuario: '',
    password: '',
    confirmPassword: ''
  });
  const [registerLoading, setRegisterLoading] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [changePasswordData, setChangePasswordData] = useState({
    usuario: '',
    passwordActual: '',
    passwordNueva: '',
    passwordConfirmar: ''
  });
  const [changePasswordLoading, setChangePasswordLoading] = useState(false);
  const [changePasswordError, setChangePasswordError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/login`, {
        email: formData.email,
        password: formData.password
      });
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userName', response.data.nombre);
      localStorage.setItem('esSocio', String(response.data.es_socio).toLowerCase());
      localStorage.setItem('userEmail', formData.email);
      
      toast.success('Bienvenido al sistema');
      onLoginSuccess();
    } catch (error) {
      toast.error('Credenciales incorrectas');
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegisterLoading(true);
    
    if (registerData.password !== registerData.confirmPassword) {
      toast.error('Las contraseñas no coinciden');
      setRegisterLoading(false);
      return;
    }
    
    try {
      await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/register`, {
        prefijo_email: registerData.usuario,
        nombre: registerData.nombre,
        password: registerData.password
      });
      
      toast.success('Cuenta creada exitosamente. Ya puedes iniciar sesión.');
      setRegisterData({ nombre: '', usuario: '', password: '', confirmPassword: '' });
      setActiveTab('login');
    } catch (error) {
      const message = error.response?.data?.detail || 'Error al crear la cuenta';
      toast.error(message);
    } finally {
      setRegisterLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setChangePasswordError('');
    
    // Validaciones frontend
    if (!changePasswordData.usuario || !changePasswordData.passwordActual || 
        !changePasswordData.passwordNueva || !changePasswordData.passwordConfirmar) {
      setChangePasswordError('Todos los campos son requeridos');
      return;
    }
    
    if (changePasswordData.passwordNueva.length < 6) {
      setChangePasswordError('La nueva contraseña debe tener al menos 6 caracteres');
      return;
    }
    
    if (changePasswordData.passwordNueva !== changePasswordData.passwordConfirmar) {
      setChangePasswordError('Las contraseñas no coinciden');
      return;
    }
    
    if (changePasswordData.passwordActual === changePasswordData.passwordNueva) {
      setChangePasswordError('La nueva contraseña debe ser diferente a la actual');
      return;
    }
    
    setChangePasswordLoading(true);
    
    try {
      await axios.post(
        `${import.meta.env.VITE_API_URL || 'https://cfo-inteligente-production.up.railway.app'}/api/auth/cambiar-password-publico`,
        {
          prefijo_email: changePasswordData.usuario,
          password_actual: changePasswordData.passwordActual,
          password_nueva: changePasswordData.passwordNueva
        }
      );
      
      toast.success('Contraseña actualizada. Ya podés iniciar sesión.');
      setShowChangePassword(false);
      setChangePasswordData({ usuario: '', passwordActual: '', passwordNueva: '', passwordConfirmar: '' });
      setChangePasswordError('');
    } catch (error) {
      if (error.response?.status === 404) {
        toast.error('Usuario no encontrado');
      } else if (error.response?.status === 400) {
        const message = error.response?.data?.detail || 'Error al cambiar contraseña';
        toast.error(message);
        setChangePasswordError(message);
      } else {
        toast.error('Error al cambiar contraseña');
        setChangePasswordError('Error al cambiar contraseña');
      }
    } finally {
      setChangePasswordLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 h-24 flex items-center justify-between">
          <div></div>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
            </span>
            <span className="text-sm text-slate-400">Sistema Online</span>
          </div>
        </div>
      </header>

      {/* Hero + Login Form */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Hero */}
          <div>
            <h1 className="text-5xl font-bold text-white mb-4">
              CFO Inteligente
            </h1>
            <p className="text-2xl text-slate-400 mb-6">
              Sistema Financiero Integral de Conexión Consultora
            </p>
            <p className="text-slate-500 mb-8">
              Plataforma profesional de gestión y análisis financiero con 
              capacidades de inteligencia artificial para optimizar la toma 
              de decisiones empresariales.
            </p>
            
            {/* Security badges */}
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Shield className="w-4 h-4 text-green-500" />
                <span>Encriptación SSL</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Lock className="w-4 h-4 text-green-500" />
                <span>Acceso Seguro</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Respaldos Diarios</span>
              </div>
            </div>
          </div>

          {/* Right: Login Card */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 backdrop-blur">
            {/* Tabs */}
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setActiveTab('login')}
                className={`pb-2 px-1 text-sm font-medium transition ${
                  activeTab === 'login' 
                    ? 'text-white border-b-2 border-blue-500' 
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Iniciar Sesión
              </button>
              <button
                onClick={() => setActiveTab('register')}
                className={`px-3 py-1 text-sm font-medium transition rounded-md border ${
                  activeTab === 'register' 
                    ? 'text-white border-slate-400 bg-slate-800/50' 
                    : 'text-slate-300 border-slate-600 hover:text-white hover:border-slate-500'
                }`}
              >
                Registrarse
              </button>
            </div>

            {activeTab === 'login' ? (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                    placeholder="tu@conexionconsultora.uy"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    required
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2"
                      checked={formData.remember}
                      onChange={(e) => setFormData({...formData, remember: e.target.checked})}
                    />
                    <span className="text-sm text-slate-400">Recordarme</span>
                  </label>
                  <button 
                    type="button"
                    onClick={() => setShowHelp(!showHelp)}
                    className="text-sm text-blue-400 hover:text-blue-300"
                  >
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>
                
                {showHelp && (
                  <div className="p-3 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-slate-300">
                    Contacta al administrador del sistema para restablecer tu contraseña.
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 transition disabled:opacity-50"
                >
                  {loading ? 'Ingresando...' : 'Ingresar al Sistema'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Nombre completo
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                    placeholder="Juan Pérez"
                    value={registerData.nombre}
                    onChange={(e) => setRegisterData({...registerData, nombre: e.target.value})}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Usuario
                  </label>
                  <div className="relative">
                    {/* Capa visual: muestra usuario + dominio en gris */}
                    <div 
                      className="absolute inset-0 flex items-center px-4 py-3 pointer-events-none border border-slate-700 rounded-lg bg-slate-800"
                      aria-hidden="true"
                    >
                      {registerData.usuario ? (
                        <>
                          <span className="text-white">{registerData.usuario}</span>
                          <span className="text-slate-400">@grupoconexion.uy</span>
                        </>
                      ) : (
                        <span className="text-slate-500">tunombre@grupoconexion.uy</span>
                      )}
                    </div>
                    {/* Input real: invisible pero funcional */}
                    <input
                      type="text"
                      required
                      value={registerData.usuario}
                      onChange={(e) => setRegisterData({...registerData, usuario: e.target.value.toLowerCase().replace(/[@\s]/g, '')})}
                      className="w-full px-4 py-3 border border-slate-700 rounded-lg bg-transparent text-transparent caret-white focus:outline-none focus:ring-2 focus:ring-blue-500 relative z-10"
                      autoComplete="off"
                      spellCheck="false"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    required
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                    placeholder="••••••••"
                    value={registerData.password}
                    onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Confirmar Contraseña
                  </label>
                  <input
                    type="password"
                    required
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                    placeholder="••••••••"
                    value={registerData.confirmPassword}
                    onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                  />
                </div>

                <button
                  type="submit"
                  disabled={registerLoading}
                  className="w-full py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-medium rounded-lg hover:from-green-700 hover:to-green-800 transition disabled:opacity-50"
                >
                  {registerLoading ? 'Creando cuenta...' : 'Crear Cuenta'}
                </button>

                <p className="text-xs text-center text-slate-500">
                  Al registrarte, ingresarás como colaborador. Un administrador puede ascenderte a socio.
                </p>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* Link discreto para cambiar contraseña */}
      <div className="max-w-7xl mx-auto px-6 -mt-8 mb-8">
        <div className="flex justify-center">
          <button
            onClick={() => setShowChangePassword(!showChangePassword)}
            className="flex items-center gap-2 px-6 py-3 rounded-full bg-amber-500/10 border border-amber-500/30 text-sm text-amber-400 hover:bg-amber-500/20 hover:border-amber-500/50 transition-colors"
          >
            <Lock className="w-4 h-4 text-amber-400" />
            <span>¿Necesitás cambiar tu contraseña?</span>
          </button>
        </div>
        
        {/* Formulario expandible */}
        {showChangePassword && (
          <div className="mt-6 max-w-md mx-auto">
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 backdrop-blur">
              <form onSubmit={handleChangePassword} className="space-y-6">
                {changePasswordError && (
                  <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-sm text-red-300">
                    {changePasswordError}
                  </div>
                )}
                
                {/* Usuario */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Usuario
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                    <input
                      type="text"
                      required
                      value={changePasswordData.usuario}
                      onChange={(e) => setChangePasswordData({...changePasswordData, usuario: e.target.value.toLowerCase().replace(/[@\s]/g, '')})}
                      className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition"
                      placeholder="Tu usuario ej: gferrari"
                    />
                  </div>
                </div>
                
                {/* Contraseña actual */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Contraseña actual
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                    <input
                      type="password"
                      required
                      value={changePasswordData.passwordActual}
                      onChange={(e) => setChangePasswordData({...changePasswordData, passwordActual: e.target.value})}
                      className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
                
                {/* Contraseña nueva */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Contraseña nueva
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                    <input
                      type="password"
                      required
                      value={changePasswordData.passwordNueva}
                      onChange={(e) => setChangePasswordData({...changePasswordData, passwordNueva: e.target.value})}
                      className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition"
                      placeholder="Mínimo 6 caracteres"
                    />
                  </div>
                </div>
                
                {/* Confirmar contraseña nueva */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Confirmar contraseña nueva
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                    <input
                      type="password"
                      required
                      value={changePasswordData.passwordConfirmar}
                      onChange={(e) => setChangePasswordData({...changePasswordData, passwordConfirmar: e.target.value})}
                      className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
                
                {/* Botones */}
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowChangePassword(false);
                      setChangePasswordData({ usuario: '', passwordActual: '', passwordNueva: '', passwordConfirmar: '' });
                      setChangePasswordError('');
                    }}
                    className="flex-1 py-3 px-4 border border-slate-700 rounded-lg text-slate-300 hover:text-white hover:border-slate-600 transition"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={changePasswordLoading}
                    className="flex-1 py-3 px-4 bg-gradient-to-r from-amber-500 to-amber-600 text-white font-medium rounded-lg hover:from-amber-600 hover:to-amber-700 transition disabled:opacity-50"
                  >
                    {changePasswordLoading ? 'Cambiando...' : 'Cambiar contraseña'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* System Capabilities */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-semibold text-white text-center mb-8">
          Capacidades del Sistema
        </h2>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-6 hover:bg-slate-900/50 transition">
            <FileText className="w-10 h-10 text-blue-500 mb-4" />
            <h3 className="font-semibold text-white mb-2">Registro de Operaciones</h3>
            <p className="text-sm text-slate-400">18+ operaciones procesadas diariamente</p>
          </div>
          <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-6 hover:bg-slate-900/50 transition">
            <BarChart3 className="w-10 h-10 text-green-500 mb-4" />
            <h3 className="font-semibold text-white mb-2">Análisis en Tiempo Real</h3>
            <p className="text-sm text-slate-400">3 gráficos interactivos con datos actualizados</p>
          </div>
          <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-6 hover:bg-slate-900/50 transition">
            <Shield className="w-10 h-10 text-purple-500 mb-4" />
            <h3 className="font-semibold text-white mb-2">Reportes Inteligentes</h3>
            <p className="text-sm text-slate-400">Powered by AI (próximamente)</p>
          </div>
          <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-6 hover:bg-slate-900/50 transition">
            <Users className="w-10 h-10 text-orange-500 mb-4" />
            <h3 className="font-semibold text-white mb-2">Multi-usuario</h3>
            <p className="text-sm text-slate-400">9 usuarios con permisos diferenciados</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-16 py-8">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between text-sm text-slate-500">
          <span>© 2025 Conexión Consultora - Uruguay</span>
          <div className="flex gap-6">
            <span>Versión 2.1.0</span>
            <a href="#" className="hover:text-slate-300">Soporte Técnico</a>
            <a href="#" className="hover:text-slate-300">Políticas de Privacidad</a>
          </div>
        </div>
      </footer>
    </div>
  );
}


