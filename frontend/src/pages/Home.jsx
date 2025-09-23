import { useState } from 'react';
import { Shield, BarChart3, FileText, Users, Lock, CheckCircle } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

export default function Home() {
  const [activeTab, setActiveTab] = useState('login');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    remember: false
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post('http://localhost:8000/api/auth/login', {
        email: formData.email,
        password: formData.password
      });
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userName', formData.email.split('@')[0]);
      
      toast.success('Bienvenido al sistema');
      window.location.href = '/dashboard';
    } catch (error) {
      toast.error('Credenciales incorrectas');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 h-24 flex items-center justify-between">
          <img src="/logo-conexion.png" alt="Conexión" className="h-20" />
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
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Iniciar Sesión
              </button>
              <button
                onClick={() => setActiveTab('first')}
                className={`pb-2 px-1 text-sm font-medium transition ${
                  activeTab === 'first' 
                    ? 'text-white border-b-2 border-blue-500' 
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Primer Acceso
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
                  <a href="#" className="text-sm text-blue-400 hover:text-blue-300">
                    ¿Olvidaste tu contraseña?
                  </a>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 transition disabled:opacity-50"
                >
                  {loading ? 'Ingresando...' : 'Ingresar al Sistema'}
                </button>
              </form>
            ) : (
              <div className="space-y-4 text-slate-300">
                <p className="text-lg font-medium">¿Primera vez en el sistema?</p>
                <p className="text-slate-400">
                  Para obtener tus credenciales de acceso, contacta al administrador del sistema:
                </p>
                <div className="bg-slate-800/50 rounded-lg p-4 space-y-2">
                  <p className="text-sm">
                    <span className="text-slate-500">Email:</span>{' '}
                    <span className="text-white">admin@conexionconsultora.uy</span>
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">Teléfono:</span>{' '}
                    <span className="text-white">+598 99 123 456</span>
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">Horario:</span>{' '}
                    <span className="text-white">Lun-Vie 9:00 - 18:00</span>
                  </p>
                </div>
                <p className="text-xs text-slate-500">
                  Solo usuarios autorizados pueden acceder al sistema.
                </p>
              </div>
            )}
          </div>
        </div>
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


