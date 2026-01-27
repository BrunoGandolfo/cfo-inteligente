import { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { LogIn, UserPlus, HelpCircle, Lock, Mail } from 'lucide-react';
import RegisterForm from '../components/auth/RegisterForm';

function Login({ onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showHelp, setShowHelp] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL || 'https://cfo-inteligente-production.up.railway.app'}/api/auth/login`,
        { email, password }
      );
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userName', response.data.nombre);
      localStorage.setItem('esSocio', String(response.data.es_socio).toLowerCase());
      localStorage.setItem('userEmail', email);
      
      toast.success(`¡Bienvenido, ${response.data.nombre}!`);
      onLoginSuccess();
    } catch (err) {
      const message = err.response?.data?.detail || 'Email o contraseña incorrectos';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSuccess = () => {
    setActiveTab('login');
    setEmail('');
    setPassword('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">CFO Inteligente</h1>
          <p className="mt-2 text-slate-400">Sistema Financiero - Grupo Conexión</p>
        </div>
        
        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-200 dark:border-slate-700">
            <button
              onClick={() => setActiveTab('login')}
              className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
                activeTab === 'login'
                  ? 'bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600'
                  : 'bg-gray-50 dark:bg-slate-900 text-gray-500 dark:text-slate-400 hover:text-gray-700'
              }`}
            >
              <LogIn className="w-4 h-4" />
              Iniciar Sesión
            </button>
            <button
              onClick={() => setActiveTab('register')}
              className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
                activeTab === 'register'
                  ? 'bg-white dark:bg-slate-800 text-green-600 dark:text-green-400 border-b-2 border-green-600'
                  : 'bg-gray-50 dark:bg-slate-900 text-gray-500 dark:text-slate-400 hover:text-gray-700'
              }`}
            >
              <UserPlus className="w-4 h-4" />
              Registrarse
            </button>
          </div>
          
          {/* Content */}
          <div className="p-6">
            {activeTab === 'login' ? (
              <form onSubmit={handleLogin} className="space-y-5">
                {error && (
                  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm">
                    {error}
                  </div>
                )}
                
                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="usuario@grupoconexion.uy"
                    />
                  </div>
                </div>
                
                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                    Contraseña
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Tu contraseña"
                    />
                  </div>
                </div>
                
                {/* Olvidé contraseña */}
                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setShowHelp(!showHelp)}
                    className="text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 flex items-center justify-center gap-1 mx-auto"
                  >
                    <HelpCircle className="w-4 h-4" />
                    ¿Olvidaste tu contraseña?
                  </button>
                  {showHelp && (
                    <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-md text-sm text-blue-700 dark:text-blue-300">
                      Contacta al administrador del sistema para restablecer tu contraseña.
                    </div>
                  )}
                </div>
                
                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <LogIn className="w-5 h-5" />
                  {loading ? 'Ingresando...' : 'Ingresar'}
                </button>
              </form>
            ) : (
              <RegisterForm 
                onSuccess={handleRegisterSuccess}
                onSwitchToLogin={() => setActiveTab('login')}
              />
            )}
          </div>
        </div>
        
        {/* Footer */}
        <p className="mt-6 text-center text-sm text-slate-500">
          © 2025 Grupo Conexión - Sistema CFO Inteligente
        </p>
      </div>
    </div>
  );
}

export default Login;
