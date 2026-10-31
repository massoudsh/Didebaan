import { useEffect, useState } from 'react';
import { SEVERITY_LABELS, STATUS_LABELS } from './../format.js';

const SEVERITY_ICONS = { LOW: '●', MEDIUM: '◆', HIGH: '▲', CRITICAL: '■' };

export function GlassSurface({ variant = 'medium', className = '', as: Tag = 'div', ...props }) {
  return <Tag className={`glass glass-${variant} ${className}`.trim()} {...props} />;
}

export function Button({ variant = 'default', loading = false, children, className = '', disabled, ...props }) {
  return (
    <button
      className={`btn ${variant === 'default' ? '' : variant} ${className}`.trim()}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <span className="spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

export function IconButton({ label, children, ...props }) {
  return (
    <button type="button" className="icon-btn" aria-label={label} title={label} {...props}>
      {children}
    </button>
  );
}

function severityValue(value) {
  return SEVERITY_ICONS[value] ? value : undefined;
}

export function SeverityIndicator({ value, labels = SEVERITY_LABELS }) {
  return (
    <span className={`badge sev-${value}`}>
      <span aria-hidden="true" className="badge-icon">{SEVERITY_ICONS[value] || '•'}</span>
      <span className="sr-only">شدت </span>
      {labels[value] || value}
    </span>
  );
}

export function StatusBadge({ value, labels = STATUS_LABELS }) {
  return <span className={`badge st-${value}`}>{labels[value] || value}</span>;
}

export function Badge({ kind, value, labels }) {
  return kind === 'sev'
    ? <SeverityIndicator value={value} labels={labels} />
    : <StatusBadge value={value} labels={labels} />;
}

export function Field({ label, hint, error, id, children }) {
  const describedBy = [hint ? `${id}-hint` : '', error ? `${id}-error` : ''].filter(Boolean).join(' ');
  const control = typeof children === 'function'
    ? children({ id, 'aria-describedby': describedBy || undefined, 'aria-invalid': error ? true : undefined })
    : children;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {control}
      {hint && <small id={`${id}-hint`} className="field-hint">{hint}</small>}
      {error && <small id={`${id}-error`} className="field-error" role="alert">{error}</small>}
    </div>
  );
}

export function DataTable({ columns, rows, rowKey, empty, loading, loadingText = 'در حال بارگذاری…', caption, selectedKey, onRowClick, interactive = true }) {
  return (
    <div className="table-wrap">
      <table className={`data-table${interactive ? ' interactive' : ''}`}>
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" className={column.className} aria-sort={column.sort || undefined}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const key = rowKey(row);
            return (
              <tr
                key={key}
                className={[selectedKey === key ? 'selected' : '', onRowClick && interactive ? 'clickable' : ''].filter(Boolean).join(' ') || undefined}
                onClick={onRowClick ? (event) => onRowClick(row, event) : undefined}
                tabIndex={onRowClick && interactive ? 0 : undefined}
                onKeyDown={onRowClick && interactive ? (event) => {
                  if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
                    event.preventDefault();
                    onRowClick(row, event);
                  }
                } : undefined}
              >
                {columns.map((column) => (
                  <td key={column.key} className={column.className}>{column.render ? column.render(row) : row[column.key]}</td>
                ))}
              </tr>
            );
          })}
          {!loading && rows.length === 0 && (
            <tr className="empty-row"><td colSpan={columns.length} className="empty">{empty}</td></tr>
          )}
        </tbody>
      </table>
      {loading && <p className="muted pad" role="status">{loadingText}</p>}
    </div>
  );
}

export function TableSkeleton({ rows = 5, columns = 5 }) {
  return (
    <div className="skeleton-table" aria-hidden="true">
      <div className="skeleton-row skeleton-head" />
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="skeleton-row">
          {Array.from({ length: columns }, (_, cell) => <span key={cell} className="skeleton-cell" />)}
        </div>
      ))}
    </div>
  );
}

export function ErrorState({ message, onRetry, title = 'خطا در دریافت داده' }) {
  return (
    <div className="state-card error-state" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
      {onRetry && <Button onClick={onRetry}>تلاش دوباره</Button>}
    </div>
  );
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="state-card empty-state">
      <strong>{title}</strong>
      {children && <p className="muted">{children}</p>}
      {action}
    </div>
  );
}

export function PermissionState({ children = 'برای این بخش دسترسی ندارید. با افسر انطباق یا سرپرست تماس بگیرید.' }) {
  return (
    <div className="state-card permission-state" role="status">
      <strong>دسترسی محدود</strong>
      <p>{children}</p>
    </div>
  );
}

export function InlineNotice({ tone = 'info', children, role }) {
  return <p className={`notice ${tone}`} role={role}>{children}</p>;
}

let toastId = 0;

export function useToasts() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    if (!toasts.length) return undefined;
    const timer = setTimeout(() => setToasts((current) => current.slice(1)), 4500);
    return () => clearTimeout(timer);
  }, [toasts]);

  function push(tone, message) {
    toastId += 1;
    setToasts((current) => [...current, { id: toastId, tone, message }]);
  }

  return {
    toasts,
    success: (message) => push('success', message),
    error: (message) => push('error', message),
    dismiss: (id) => setToasts((current) => current.filter((toast) => toast.id !== id)),
  };
}

export function ToastRegion({ toasts, onDismiss }) {
  return (
    <div className="toast-region" role="region" aria-label="پیام‌های سیستم" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast-${toast.tone}`}>
          <span>{toast.message}</span>
          <IconButton label="بستن پیام" onClick={() => onDismiss(toast.id)}>✕</IconButton>
        </div>
      ))}
    </div>
  );
}

export function ConfirmBar({ message, confirmLabel = 'تأیید', onConfirm, onCancel, busy }) {
  return (
    <div className="confirm-box" role="alertdialog" aria-label="تأیید عملیات">
      <p>{message}</p>
      <div className="row-gap">
        <Button variant="primary" onClick={onConfirm} loading={busy}>{confirmLabel}</Button>
        <Button variant="ghost" onClick={onCancel}>انصراف</Button>
      </div>
    </div>
  );
}

export function Tabs({ items, value, onChange, label }) {
  return (
    <div className="segmented" role="tablist" aria-label={label}>
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          aria-selected={value === item.id}
          className={value === item.id ? 'segmented-item active' : 'segmented-item'}
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
