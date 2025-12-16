import { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/login`, {
        email,
        password
      });
      
      // 🔍 DEBUG TEMPORAL - BORRAR DESPUÉS
      console.log('🔑 === LOGIN DEBUG ===');
      console.log('🔑 response.data completo:', JSON.stringify(response.data, null, 2));
      console.log('🔑 es_socio valor:', response.data.es_socio);
      console.log('🔑 es_socio tipo:', typeof response.data.es_socio);
      console.log('🔑 String(es_socio).toLowerCase():', String(response.data.es_socio).toLowerCase());

      // Guardar token y datos del usuario
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userName', response.data.nombre);
      localStorage.setItem('esSocio', String(response.data.es_socio).toLowerCase());
      
      // 🔍 DEBUG TEMPORAL - BORRAR DESPUÉS
      console.log('🔑 localStorage esSocio guardado:', localStorage.getItem('esSocio'));

      // Redirigir a dashboard
      toast.success('Bienvenido al sistema');
      window.location.href = '/dashboard';
    } catch {
      setError('Email o contraseña incorrectos');
      toast.error('Credenciales incorrectas');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            CFO Inteligente
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sistema Financiero - Conexión Consultora
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>
          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Iniciar Sesión
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Login;
