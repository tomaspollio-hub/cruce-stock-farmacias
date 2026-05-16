/**
 * toast.js — notificaciones temporales.
 */

function showToast(message, type = 'info', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { success: '✓', danger: '✕', info: 'ℹ', warning: '⚠' };
  toast.innerHTML = `<span>${icons[type] ?? 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'opacity 250ms, transform 250ms';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

export { showToast };
