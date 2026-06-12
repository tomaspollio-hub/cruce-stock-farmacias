/**
 * auth.js — autenticación JWT para Cruce Stock.
 */

import storage from './storage.js';

function _decodeJwtPayload(token) {
  try {
    return JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
  } catch { return null; }
}

function _tokenExp(token) {
  const p = _decodeJwtPayload(token);
  return p?.exp ?? null;
}

let _refreshTimer  = null;
let _warningTimer  = null;
let _warningBanner = null;
const WARN_BEFORE    = 5 * 60;
const REFRESH_BEFORE = 2 * 60;

function _clearTimers() {
  clearTimeout(_refreshTimer);
  clearTimeout(_warningTimer);
  _hideBanner();
}

function _hideBanner() {
  if (_warningBanner) { _warningBanner.remove(); _warningBanner = null; }
}

function _showBanner() {
  if (_warningBanner) return;
  _warningBanner = document.createElement('div');
  _warningBanner.style.cssText = [
    'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);z-index:9999',
    'background:#d97706;color:#fff;font-size:13px;font-weight:600',
    'padding:10px 20px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.2)',
    'display:flex;align-items:center;gap:12px',
  ].join(';');
  _warningBanner.innerHTML = `
    <span>⚠ Tu sesión vence en 5 minutos.</span>
    <button onclick="auth._doRefresh()" style="background:#fff;color:#d97706;border:none;border-radius:4px;padding:4px 10px;font-size:12px;font-weight:700;cursor:pointer">Renovar</button>
    <button onclick="this.closest('div').remove()" style="background:none;border:none;color:#fff;font-size:16px;cursor:pointer;padding:0 4px">✕</button>`;
  document.body.appendChild(_warningBanner);
}

function _scheduleTimers(token) {
  _clearTimers();
  const exp = _tokenExp(token);
  if (!exp) return;
  const now       = Math.floor(Date.now() / 1000);
  const ttl       = exp - now;
  if (ttl <= 0) return;
  const warnIn    = Math.max(0, (ttl - WARN_BEFORE) * 1000);
  const refreshIn = Math.max(0, (ttl - REFRESH_BEFORE) * 1000);
  _warningTimer  = setTimeout(_showBanner, warnIn);
  _refreshTimer  = setTimeout(() => auth._doRefresh(), refreshIn);
}

const auth = {
  async _doRefresh() {
    const token = localStorage.getItem('cruce_token');
    if (!token) return;
    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.ok && data.token) {
        localStorage.setItem('cruce_token', data.token);
        _hideBanner();
        _scheduleTimers(data.token);
      }
    } catch { /* silencioso */ }
  },

  async login(usuario, password) {
    let res;
    try {
      res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario, password }),
      });
    } catch {
      return { ok: false, motivo: 'error_servidor' };
    }
    const data = await res.json();
    if (!data.ok) return { ok: false, motivo: data.motivo };

    localStorage.setItem('cruce_token', data.token);
    await storage.saveSession(data.session);
    _scheduleTimers(data.token);
    return { ok: true, session: data.session };
  },

  async logout() {
    _clearTimers();
    const token = localStorage.getItem('cruce_token');
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }).catch(() => {});
    await storage.clearSession();
    window.location.href = './login.html';
  },

  async getSession() {
    return storage.getSession();
  },

  async requireAuth() {
    const session = await storage.getSession();
    if (!session) { window.location.href = './login.html'; return null; }
    const token = localStorage.getItem('cruce_token');
    if (!token) { await storage.clearSession(); window.location.href = './login.html'; return null; }
    const exp = _tokenExp(token);
    if (exp && Math.floor(Date.now() / 1000) >= exp) {
      await storage.clearSession();
      window.location.href = './login.html';
      return null;
    }
    _scheduleTimers(token);
    return session;
  },

  getToken() {
    return localStorage.getItem('cruce_token');
  },

  async apiFetch(url, options = {}) {
    const token = this.getToken();
    const headers = { ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return fetch(url, { ...options, headers });
  },
};

window.auth = auth;
export default auth;
