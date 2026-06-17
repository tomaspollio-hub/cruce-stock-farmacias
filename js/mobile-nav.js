/**
 * mobile-nav.js — menú hamburguesa con cajón lateral (≤768px).
 * Llamar initMobileNav('clave-de-pagina', session.rol) en cada página.
 */
import { icons } from './icons.js';

export function initMobileNav(active, rol = '') {
  const defs = [
    { href: 'index.html',       icon: icons.home,      label: 'Inicio',       key: 'dashboard',   adminOnly: false },
    { href: 'nuevo-cruce.html', icon: icons.bolt,      label: 'Nuevo cruce',  key: 'nuevo',       adminOnly: false },
    { href: 'operador.html',    icon: icons.signal,    label: 'Operador',     key: 'operador',    adminOnly: false },
    { href: 'cadete.html',      icon: icons.map,       label: 'Ruta del día', key: 'cadete',      adminOnly: false },
    { href: 'incidencias.html', icon: icons.warning,   label: 'Incidencias',  key: 'incidencias', adminOnly: false },
    { href: 'historial.html',   icon: icons.clipboard, label: 'Historial',    key: 'historial',   adminOnly: false },
    { href: 'usuarios.html',    icon: icons.users,     label: 'Usuarios',     key: 'usuarios',    adminOnly: true  },
    { href: 'config.html',      icon: icons.settings,  label: 'Config',       key: 'config',      adminOnly: true  },
  ];

  if (rol) document.body.dataset.rol = rol;

  let items;
  if (rol === 'admin') {
    items = defs;
  } else if (rol === 'operador' || rol === 'cadete') {
    items = [];
  } else {
    items = defs.filter(it => !it.adminOnly);
  }

  if (items.length === 0) return;

  // ── Overlay ──────────────────────────────────────────────────────
  const overlay = document.createElement('div');
  overlay.id = 'mnav-overlay';
  overlay.addEventListener('click', closeDrawer);

  // ── Cajón lateral ────────────────────────────────────────────────
  const drawer = document.createElement('nav');
  drawer.id = 'mnav-drawer';
  drawer.setAttribute('aria-label', 'Menú principal');
  drawer.innerHTML = `
    <div class="mnav-head">
      <span class="mnav-head-title">Menú</span>
      <button class="mnav-close" aria-label="Cerrar menú">${icons.x}</button>
    </div>
    <div class="mnav-links">
      ${items.map(it => `
        <a href="${it.href}" class="mnav-link${it.key === active ? ' active' : ''}">
          <span class="mnav-icon">${it.icon}</span>
          <span>${it.label}</span>
        </a>`).join('')}
    </div>`;
  drawer.querySelector('.mnav-close').addEventListener('click', closeDrawer);

  // ── Botón hamburguesa ────────────────────────────────────────────
  const btn = document.createElement('button');
  btn.id = 'mnav-toggle';
  btn.setAttribute('aria-label', 'Abrir menú');
  btn.setAttribute('aria-expanded', 'false');
  btn.innerHTML = icons.menu;
  btn.addEventListener('click', openDrawer);

  const spacer = document.querySelector('.header-spacer');
  if (spacer) spacer.parentNode.insertBefore(btn, spacer);

  document.body.appendChild(overlay);
  document.body.appendChild(drawer);

  function openDrawer() {
    drawer.classList.add('open');
    overlay.classList.add('open');
    btn.setAttribute('aria-expanded', 'true');
    document.body.classList.add('mnav-open');
  }

  function closeDrawer() {
    drawer.classList.remove('open');
    overlay.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('mnav-open');
  }
}
