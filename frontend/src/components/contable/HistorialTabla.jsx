import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { Eye, Trash2, CheckCircle2, XCircle, FileSearch } from 'lucide-react';

function HistorialTabla({ consultas, loading, mostrarUsuario, onVer, onEliminar }) {
  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-surface-alt rounded w-1/3" />
          <div className="h-10 bg-bg rounded" />
          <div className="h-10 bg-bg rounded" />
          <div className="h-10 bg-bg rounded" />
        </div>
      </div>
    );
  }

  if (!consultas || consultas.length === 0) {
    return (
      <div className="p-12 text-center">
        <FileSearch className="w-16 h-16 text-text-muted mx-auto mb-4" />
        <h3 className="text-lg font-medium text-text-primary mb-2">
          Sin consultas registradas
        </h3>
        <p className="text-text-secondary">
          Cuando realices una consulta a DGI va a aparecer acá.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-surface-alt">
          <tr>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary uppercase">Fecha</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary uppercase">Servicio</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary uppercase">RUT / CI</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary uppercase">Cliente</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary uppercase">Resultado</th>
            {mostrarUsuario ? (
              <th className="px-4 py-2.5 text-left text-xs font-medium text-text-secondary uppercase">Usuario</th>
            ) : null}
            <th className="px-4 py-2.5 text-center text-xs font-medium text-text-secondary uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-surface divide-y divide-border">
          {consultas.map(c => {
            const fecha = c.created_at ? new Date(c.created_at) : null;
            const exitosa = !!c.exitosa;
            return (
              <tr key={c.id} className="hover:bg-surface-alt/60">
                <td className="px-4 py-2 whitespace-nowrap text-text-secondary">
                  {fecha ? format(fecha, 'dd/MM/yyyy HH:mm', { locale: es }) : '-'}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-text-primary font-medium">
                  {c.servicio}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-text-secondary">
                  {c.rut || c.ci || '-'}
                </td>
                <td className="px-4 py-2 text-text-secondary max-w-[180px] truncate">
                  {c.cliente_nombre || '-'}
                </td>
                <td className="px-4 py-2 whitespace-nowrap">
                  {exitosa ? (
                    <span className="inline-flex items-center gap-1 text-success">
                      <CheckCircle2 className="w-4 h-4" />
                      <span className="text-xs font-medium">
                        {c.resultado_texto?.slice(0, 40) || 'OK'}
                      </span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-danger">
                      <XCircle className="w-4 h-4" />
                      <span className="text-xs font-medium">
                        {c.error?.slice(0, 40) || 'Error'}
                      </span>
                    </span>
                  )}
                </td>
                {mostrarUsuario ? (
                  <td className="px-4 py-2 whitespace-nowrap text-text-muted text-xs font-mono">
                    {c.usuario_id ? c.usuario_id.slice(0, 8) : '-'}
                  </td>
                ) : null}
                <td className="px-4 py-2 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center gap-1">
                    <button
                      type="button"
                      onClick={() => onVer(c.id)}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs text-accent hover:bg-accent-soft rounded-md"
                      title="Ver detalle"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => onEliminar(c.id)}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs text-danger hover:bg-danger/10 rounded-md"
                      title="Eliminar"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default HistorialTabla;
