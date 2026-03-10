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
        className="fixed inset-0 bg-bg/70 transition-opacity"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-surface border border-border rounded-lg shadow-xl w-full max-w-2xl p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <Users className="w-5 h-5 text-accent" />
              Administrar Usuarios
            </h3>
            <button
              onClick={handleClose}
              className="text-text-muted hover:text-text-secondary"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Mensaje de contraseña temporal */}
          {tempPassword ? (
            <div className="mb-4 p-4 bg-success/10 border border-success/30 rounded-lg">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                <div>
                  <p className="font-medium text-success">
                    Contraseña reseteada para {tempPassword.nombre}
                  </p>
                  <p className="mt-1 text-sm text-text-secondary">
                    Nueva contraseña temporal: <code className="bg-success/15 px-2 py-0.5 rounded font-mono text-success">{tempPassword.password}</code>
                  </p>
                  <p className="mt-1 text-xs text-text-secondary">
                    El usuario deberá cambiarla en su próximo inicio de sesión.
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          {/* Error */}
          {error ? (
            <div className="mb-4 p-4 bg-danger/10 border border-danger/30 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-danger" />
              <span className="text-danger">{error}</span>
            </div>
          ) : null}

          {/* Lista de usuarios */}
          <div className="border border-border rounded-lg overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-surface-alt">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Rol
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border bg-surface">
                {loading ? (
                  <tr>
                    <td colSpan="4" className="px-4 py-8 text-center text-text-secondary">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-accent" />
                      Cargando usuarios...
                    </td>
                  </tr>
                ) : usuarios.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="px-4 py-8 text-center text-text-secondary">
                      No hay usuarios registrados
                    </td>
                  </tr>
                ) : (
                  usuarios.map((usuario) => (
                    <tr key={usuario.id} className="hover:bg-surface-alt">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-text-primary">
                            {usuario.nombre}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary">
                        {usuario.email}
                      </td>
                      <td className="px-4 py-3">
                        {usuario.es_socio ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-accent-soft text-accent rounded-full">
                            <Shield className="w-3 h-3" />
                            Socio
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-surface-alt text-text-secondary rounded-full">
                            Colaborador
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleResetPassword(usuario.id, usuario.nombre)}
                          disabled={resetting === usuario.id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-warning bg-warning/10 hover:bg-warning/20 rounded-md transition-colors disabled:opacity-50"
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
              className="px-4 py-2 border border-border rounded-md text-text-secondary hover:bg-surface-alt transition-colors"
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
