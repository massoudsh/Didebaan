const numberFmt = new Intl.NumberFormat('fa-IR');
const dateFmt = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { dateStyle: 'medium', timeStyle: 'short' });

export const fmtNumber = (value) => numberFmt.format(Number(value) || 0);

export const fmtScore = (value) =>
  new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 1 }).format(Number(value) || 0);

export const fmtDate = (iso) => (iso ? dateFmt.format(new Date(iso)) : '—');

export const fmtAmount = (amount, currency) => `${fmtNumber(amount)} ${currency || ''}`.trim();

export function fmtAge(iso) {
  if (!iso) return '—';
  const hours = (Date.now() - new Date(iso).getTime()) / 36e5;
  if (hours < 1) return 'کمتر از یک ساعت';
  if (hours < 48) return `${fmtNumber(Math.floor(hours))} ساعت`;
  return `${fmtNumber(Math.floor(hours / 24))} روز`;
}

export const STATUS_LABELS = {
  OPEN: 'باز',
  UNDER_REVIEW: 'در حال بررسی',
  RESOLVED: 'حل‌شده',
  FALSE_POSITIVE: 'مثبت کاذب',
  ESCALATED: 'ارجاع سطح بالا',
};

export const SEVERITY_LABELS = {
  LOW: 'کم',
  MEDIUM: 'متوسط',
  HIGH: 'بالا',
  CRITICAL: 'بحرانی',
};

export const COMMENT_TYPE_LABELS = {
  COMMENT: 'یادداشت',
  ASSIGNMENT: 'ارجاع',
  STATUS_CHANGE: 'تغییر وضعیت',
};

export const REVIEW_STATUSES = ['UNDER_REVIEW', 'RESOLVED', 'FALSE_POSITIVE', 'ESCALATED'];
