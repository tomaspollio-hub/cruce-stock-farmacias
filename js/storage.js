/**
 * storage.js — sesión local (localStorage).
 * La autenticación vive en localStorage; los datos en el servidor.
 */

const storage = {
  async getSession() {
    try {
      const raw = localStorage.getItem('cruce_session');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  },

  async saveSession(data) {
    localStorage.setItem('cruce_session', JSON.stringify(data));
  },

  async clearSession() {
    localStorage.removeItem('cruce_session');
    localStorage.removeItem('cruce_token');
  },
};

export default storage;
