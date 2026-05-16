/**
 * storage.js — sesión local (sessionStorage).
 * La autenticación vive en sessionStorage; los datos en el servidor.
 */

const storage = {
  async getSession() {
    try {
      const raw = sessionStorage.getItem('cruce_session');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  },

  async saveSession(data) {
    sessionStorage.setItem('cruce_session', JSON.stringify(data));
  },

  async clearSession() {
    sessionStorage.removeItem('cruce_session');
    sessionStorage.removeItem('cruce_token');
  },
};

export default storage;
