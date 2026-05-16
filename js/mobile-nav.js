/**
 * mobile-nav.js — barra de navegación inferior para mobile/tablet (≤768px).
 * Importar en cada página y llamar initMobileNav('clave-de-pagina').
 */
export function initMobileNav(active) {
  const items = [
    { href: 'index.html',       icon: '🏠', label: 'Inicio',    key: 'dashboard' },
    { href: 'nuevo-cruce.html', icon: '⚡', label: 'Cruce',     key: 'nuevo'     },
    { href: 'operador.html',    icon: '📡', label: 'Operador',  key: 'operador'  },
    { href: 'historial.html',   icon: '📋', label: 'Historial', key: 'historial' },
    { href: 'usuarios.html',    icon: '👥', label: 'Usuarios',  key: 'usuarios'  },
  ];

  const nav = document.createElement('nav');
  nav.id = 'mobile-nav';
  nav.setAttribute('aria-label', 'Navegación principal');
  nav.innerHTML = items.map(it => `
    <a href="${it.href}" class="mnav-item${it.key === active ? ' active' : ''}">
      <span class="mnav-icon">${it.icon}</span>
      <span class="mnav-label">${it.label}</span>
    </a>`).join('');

  document.body.appendChild(nav);
}
