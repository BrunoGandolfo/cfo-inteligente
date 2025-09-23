import { format, formatISO, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

export const formatMoneyUYU = (n) =>
  new Intl.NumberFormat('es-UY', { style: 'currency', currency: 'UYU', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(n || 0);

export const formatMoney = (n, currency = 'UYU') => {
  const amount = Number(n || 0);
  if (currency === 'USD') {
    return `US$ ${amount.toLocaleString('es-UY', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  }
  return `$ ${amount.toLocaleString('es-UY', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

export const formatMoneySmart = (op) => {
  const usd = Number(op.monto_usd || 0); const uyu = Number(op.monto_uyu || 0);
  const isUSD = usd > 100 && uyu / (usd || 1) > 30;
  const val = isUSD ? usd : uyu; const symbol = isUSD ? 'USD ' : '$ ';
  return `${symbol}${val.toLocaleString('es-UY', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const formatDateShort = (iso) => format(parseISO(iso), 'dd/MM', { locale: es });
export const formatDateTime = (iso) => format(parseISO(iso), "dd/MM/yyyy HH:mm", { locale: es });
export const todayISO = () => formatISO(new Date(), { representation: 'date' });

export const deriveTipoCambio = (op) => {
  const usd = Number(op.monto_usd || 0); const uyu = Number(op.monto_uyu || 0);
  if (usd > 0) return (uyu / usd).toFixed(2);
  return null;
};


