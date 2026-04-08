/**
 * Listas centralizadas de control de acceso por módulo.
 * ÚNICA FUENTE DE VERDAD para permisos en el frontend.
 * Debe mantenerse sincronizado con backend/app/core/access_control.py
 */

export const USUARIOS_ACCESO_EXPEDIENTES_CASOS = [
  'bgandolfo@cgmasociados.com',
  'gtaborda@grupoconexion.uy',
  'falgorta@grupoconexion.uy',
  'gferrari@grupoconexion.uy',
];

export const USUARIOS_ACCESO_JURISPRUDENCIA = [
  'bgandolfo@cgmasociados.com',
  'gtaborda@grupoconexion.uy',
  'falgorta@grupoconexion.uy',
  'gferrari@grupoconexion.uy',
];

export const USUARIOS_ACCESO_ALA = [
  'bgandolfo@cgmasociados.com',
  'gferrari@grupoconexion.uy',
];

export const USUARIOS_ACCESO_NOTARIAL = [
  'gferrari@grupoconexion.uy',
  'jmora@grupoconexion.uy',
];

export const USUARIOS_ACCESO_OPERACIONES_CONTABLE = [
  'naraujo@grupoconexion.uy',
];

export const AREA_CONTABLE_ID = '14700c01-3b3d-49c6-8e2e-f3ebded1b1bb';

export const tieneAcceso = (email, lista) => {
  return lista.some(e => e.toLowerCase() === email?.toLowerCase());
};
