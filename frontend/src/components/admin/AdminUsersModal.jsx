import { useState, useEffect } from 'react';
import { X, Users, RefreshCw, AlertCircle, CheckCircle, Shield } from 'lucide-react';
import axiosClient from '../../services/api/axiosClient';
import toast from 'react-hot-toast';

function AdminUsersModal({ isOpen, onClose }) {
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(null);
  const [tempPassword, setTempPassword] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchUsuarios();
      setTempPassword(null);
    }
  }, [isOpen]);

  const fetchUsuarios = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosClient.get('/api/auth/usuarios');
      setUsuarios(response.data);
    } catch (err) {
      const message = err.response?.data?.detail || 'Error al cargar usuarios';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (userId, nombre) => {
    if (!confirm(`¿Resetear contraseña de ${nombre}?`)) return;
    
    setResetting(userId);
    setTempPassword(null);
    try {
      const response = await axiosClient.post(`/api/auth/reset-password/${userId}`);
      setTempPassword({
        nombre,
        password: response.data.temp_password
      });
      toast.success(response.data.message);
    } catch (err) {
      const message = err.response?.data?.detail || 'Error al resetear contraseña';
      toast.error(message);
    } finally {
      setResetting(null);
    }
  };

  const handleClose = () => {
    setTempPassword(null);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-2xl p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Users className="w-5 h-5" />
              Administrar Usuarios
            </h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Mensaje de contraseña temporal */}
          {tempPassword && (
            <div className="mb-4 p-4 bg-green-100 dark:bg-green-900/30 border border-green-400 rounded-lg">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
                <div>
                  <p className="font-medium text-green-800 dark:text-green-300">
                    Contraseña reseteada para {tempPassword.nombre}
                  </p>
                  <p className="mt-1 text-sm text-green-700 dark:text-green-400">
                    Nueva contraseña temporal: <code className="bg-green-200 dark:bg-green-800 px-2 py-0.5 rounded font-mono">{tempPassword.password}</code>
                  </p>
                  <p className="mt-1 text-xs text-green-600 dark:text-green-500">
                    El usuario deberá cambiarla en su próximo inicio de sesión.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-400 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <span className="text-red-700 dark:text-red-400">{error}</span>
            </div>
          )}

          {/* Lista de usuarios */}
          <div className="border dark:border-slate-700 rounded-lg overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50 dark:bg-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                    Rol
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan="4" className="px-4 py-8 text-center text-gray-500 dark:text-slate-400">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                      Cargando usuarios...
                    </td>
                  </tr>
                ) : usuarios.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="px-4 py-8 text-center text-gray-500 dark:text-slate-400">
                      No hay usuarios registrados
                    </td>
                  </tr>
                ) : (
                  usuarios.map((usuario) => (
                    <tr key={usuario.id} className="hover:bg-gray-50 dark:hover:bg-slate-700/50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {usuario.nombre}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-slate-400">
                        {usuario.email}
                      </td>
                      <td className="px-4 py-3">
                        {usuario.es_socio ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-full">
                            <Shield className="w-3 h-3" />
                            Socio
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-slate-600 text-gray-700 dark:text-slate-300 rounded-full">
                            Colaborador
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleResetPassword(usuario.id, usuario.nombre)}
                          disabled={resetting === usuario.id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-orange-700 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30 hover:bg-orange-200 dark:hover:bg-orange-900/50 rounded-md transition-colors disabled:opacity-50"
                        >
                          <RefreshCw className={`w-3 h-3 ${resetting === usuario.id ? 'animate-spin' : ''}`} />
                          {resetting === usuario.id ? 'Reseteando...' : 'Resetear'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleClose}
              className="px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminUsersModal;
