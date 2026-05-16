"""
Cruce Stock Farmacias — Flask + SQLite
Backend: auth JWT, cruces, lineas, estados cadete, analytics, descarga Excel.
"""

import io
import json
import os
import sys
import threading
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

import jwt
import yaml
from flask import Flask, g, jsonify, request, send_from_directory, send_file
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR    = Path(__file__).parent.parent
SERVER_DIR  = Path(__file__).parent
DB_PATH     = Path(os.environ.get('CRUCE_DB_PATH',      str(SERVER_DIR / 'cruce.db')))
UPLOADS_DIR = Path(os.environ.get('CRUCE_UPLOADS_DIR',  str(SERVER_DIR / 'uploads')))
CONFIG_PATH = BASE_DIR / 'cruce_stock' / 'config.yaml'

SECRET_KEY = os.environ.get('CRUCE_SECRET', 'dev-secret-change-in-prod')
TOKEN_TTL  = int(os.environ.get('CRUCE_TOKEN_TTL', 86400))

# Agregar src al path para importar los módulos de procesamiento
sys.path.insert(0, str(BASE_DIR / 'cruce_stock'))

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path='')

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ── DB ─────────────────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        import sqlite3
        g.db = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario      TEXT    UNIQUE NOT NULL,
            password_hash TEXT   NOT NULL,
            nombre       TEXT,
            rol          TEXT    DEFAULT 'operador',
            created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cruces (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT    NOT NULL,
            archivo_pedidos TEXT,
            archivo_stock   TEXT,
            total_lineas    INTEGER DEFAULT 0,
            con_cobertura   INTEGER DEFAULT 0,
            sin_cobertura   INTEGER DEFAULT 0,
            pct_cobertura   REAL    DEFAULT 0,
            excel_path      TEXT,
            usuario_id      INTEGER REFERENCES usuarios(id),
            created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS lineas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            cruce_id         INTEGER NOT NULL REFERENCES cruces(id) ON DELETE CASCADE,
            nro_pedido       TEXT,
            gtin             TEXT,
            sku              TEXT,
            producto         TEXT,
            marca            TEXT,
            unidades         INTEGER DEFAULT 1,
            nodo_asignado    TEXT,
            zona             TEXT,
            tier             INTEGER DEFAULT 2,
            stock_disponible INTEGER DEFAULT 0,
            alternativas     TEXT    DEFAULT '[]',
            estado           TEXT    DEFAULT 'PENDIENTE',
            notas            TEXT    DEFAULT '',
            updated_at       TEXT
        );

        CREATE TABLE IF NOT EXISTS eventos_estado (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            linea_id        INTEGER NOT NULL REFERENCES lineas(id) ON DELETE CASCADE,
            estado_anterior TEXT,
            estado_nuevo    TEXT,
            motivo          TEXT,
            origen          TEXT    DEFAULT 'cadete',
            created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_lineas_cruce    ON lineas(cruce_id);
        CREATE INDEX IF NOT EXISTS idx_lineas_estado   ON lineas(estado);
        CREATE INDEX IF NOT EXISTS idx_eventos_linea   ON eventos_estado(linea_id);
    """)

    # Migraciones para versiones anteriores de la DB
    for col_sql in [
        "ALTER TABLE lineas ADD COLUMN alternativa_nodo TEXT DEFAULT ''",
        "ALTER TABLE lineas ADD COLUMN punto_retiro TEXT DEFAULT ''",
        "ALTER TABLE entregas_habilitadas ADD COLUMN nro_pedidos TEXT DEFAULT '[]'",
    ]:
        try:
            db.execute(col_sql)
            db.commit()
        except Exception:
            pass

    # Tablas de entregas
    db.executescript("""
        CREATE TABLE IF NOT EXISTS entregas_confirmadas (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            cruce_id     INTEGER NOT NULL REFERENCES cruces(id) ON DELETE CASCADE,
            punto_retiro TEXT    NOT NULL,
            receptor     TEXT    NOT NULL,
            firma_base64 TEXT,
            entregado_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            usuario_id   INTEGER REFERENCES usuarios(id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_entrega_unica
            ON entregas_confirmadas(cruce_id, punto_retiro);

        CREATE TABLE IF NOT EXISTS entregas_habilitadas (
            cruce_id     INTEGER NOT NULL REFERENCES cruces(id) ON DELETE CASCADE,
            punto_retiro TEXT    NOT NULL,
            nro_pedidos  TEXT    DEFAULT '[]',
            PRIMARY KEY (cruce_id, punto_retiro)
        );

        CREATE TABLE IF NOT EXISTS jornadas (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha      TEXT    NOT NULL,
            cadete_id  INTEGER NOT NULL REFERENCES usuarios(id),
            cruce_id   INTEGER NOT NULL REFERENCES cruces(id),
            puntos     TEXT    NOT NULL DEFAULT '[]',
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fecha, cadete_id)
        );
    """)

    # Usuario admin por defecto si no existe ninguno
    existing = db.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
    if existing == 0:
        db.execute(
            'INSERT INTO usuarios (usuario, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
            ('admin', generate_password_hash('admin123'), 'Administrador', 'admin')
        )
        db.execute(
            'INSERT INTO usuarios (usuario, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
            ('cadete', generate_password_hash('cadete123'), 'Cadete', 'cadete')
        )
    db.commit()

# ── Auth ────────────────────────────────────────────────────────────────────────

def _make_token(user_id, usuario, rol):
    payload = {
        'sub': user_id,
        'usr': usuario,
        'rol': rol,
        'exp': datetime.now(timezone.utc) + timedelta(seconds=TOKEN_TTL),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def _decode_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return jsonify({'ok': False, 'motivo': 'sin_token'}), 401
        try:
            payload = _decode_token(header[7:])
        except jwt.ExpiredSignatureError:
            return jsonify({'ok': False, 'motivo': 'token_vencido'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'ok': False, 'motivo': 'token_invalido'}), 401
        g.user_id  = payload['sub']
        g.usuario  = payload['usr']
        g.rol      = payload['rol']
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if getattr(g, 'rol', None) != 'admin':
            return jsonify({'ok': False, 'motivo': 'sin_permiso'}), 403
        return f(*args, **kwargs)
    return require_auth(wrapper)

# ── Rutas auth ──────────────────────────────────────────────────────────────────

@app.post('/api/auth/login')
def auth_login():
    data   = request.get_json(silent=True) or {}
    usuario = data.get('usuario', '').strip()
    password = data.get('password', '')
    if not usuario or not password:
        return jsonify({'ok': False, 'motivo': 'campos_requeridos'}), 400

    db  = get_db()
    row = db.execute('SELECT * FROM usuarios WHERE usuario = ?', (usuario,)).fetchone()
    if not row or not check_password_hash(row['password_hash'], password):
        return jsonify({'ok': False, 'motivo': 'credenciales_invalidas'}), 401

    token = _make_token(row['id'], row['usuario'], row['rol'])
    return jsonify({
        'ok': True,
        'token': token,
        'session': {
            'id':      row['id'],
            'usuario': row['usuario'],
            'nombre':  row['nombre'],
            'rol':     row['rol'],
        },
    })

@app.post('/api/auth/refresh')
@require_auth
def auth_refresh():
    db  = get_db()
    row = db.execute('SELECT * FROM usuarios WHERE id = ?', (g.user_id,)).fetchone()
    if not row:
        return jsonify({'ok': False}), 401
    token = _make_token(row['id'], row['usuario'], row['rol'])
    return jsonify({'ok': True, 'token': token})

@app.post('/api/auth/logout')
@require_auth
def auth_logout():
    return jsonify({'ok': True})

# ── Rutas cruces ────────────────────────────────────────────────────────────────

@app.get('/api/cruces')
@require_auth
def cruces_list():
    db   = get_db()
    rows = db.execute(
        '''SELECT c.*, u.nombre as usuario_nombre
           FROM cruces c LEFT JOIN usuarios u ON c.usuario_id = u.id
           ORDER BY c.created_at DESC LIMIT 50'''
    ).fetchall()
    return jsonify({'ok': True, 'cruces': [dict(r) for r in rows]})

@app.get('/api/cruces/<int:cruce_id>')
@require_auth
def cruce_detail(cruce_id):
    db  = get_db()
    row = db.execute('SELECT * FROM cruces WHERE id = ?', (cruce_id,)).fetchone()
    if not row:
        return jsonify({'ok': False, 'motivo': 'no_encontrado'}), 404
    lineas = db.execute(
        'SELECT * FROM lineas WHERE cruce_id = ? ORDER BY nro_pedido, nodo_asignado',
        (cruce_id,)
    ).fetchall()
    return jsonify({
        'ok':    True,
        'cruce': dict(row),
        'lineas': [dict(l) for l in lineas],
    })

# ── Jobs (procesamiento asíncrono) ──────────────────────────────────────────────

_jobs: dict = {}   # job_id → {status, step, cruce_id, resumen, error}

def _run_job(job_id, path_pedidos, path_stock, run_dir, nombre_pedidos, nombre_stock, usuario_id):
    """Corre en un hilo separado. Procesa el cruce y guarda en la DB."""
    def upd(step):
        _jobs[job_id]['step'] = step

    try:
        _jobs[job_id]['status'] = 'running'
        upd('Cargando y validando archivos...')
        resultado = _procesar_cruce(path_pedidos, path_stock, run_dir)

        upd('Guardando resultados en la base de datos...')
        with app.app_context():
            db = get_db()
            cur = db.execute(
                '''INSERT INTO cruces
                   (fecha, archivo_pedidos, archivo_stock, total_lineas, con_cobertura,
                    sin_cobertura, pct_cobertura, excel_path, usuario_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    datetime.now(timezone.utc).isoformat(),
                    nombre_pedidos, nombre_stock,
                    resultado['total'], resultado['con_cobertura'],
                    resultado['sin_cobertura'], resultado['pct_cobertura'],
                    resultado.get('excel_path'), usuario_id,
                )
            )
            cruce_id = cur.lastrowid
            for linea in resultado['lineas']:
                db.execute(
                    '''INSERT INTO lineas
                       (cruce_id, nro_pedido, gtin, sku, producto, marca, unidades,
                        nodo_asignado, zona, tier, stock_disponible, alternativas, estado, punto_retiro)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        cruce_id,
                        linea.get('nro_pedido'), linea.get('gtin'), linea.get('sku'),
                        linea.get('producto'), linea.get('marca'), linea.get('unidades', 1),
                        linea.get('nodo_asignado'), linea.get('zona'), linea.get('tier', 2),
                        linea.get('stock_disponible', 0),
                        json.dumps(linea.get('alternativas', []), ensure_ascii=False),
                        'SIN_COBERTURA' if not linea.get('nodo_asignado') else 'PENDIENTE',
                        linea.get('punto_retiro', ''),
                    )
                )
            db.commit()

        _jobs[job_id].update({'status': 'done', 'cruce_id': cruce_id, 'resumen': resultado})

    except Exception as e:
        _jobs[job_id].update({'status': 'error', 'error': str(e)})


@app.post('/api/cruces')
@require_auth
def cruce_nuevo():
    if 'pedidos' not in request.files or 'stock' not in request.files:
        return jsonify({'ok': False, 'motivo': 'archivos_requeridos'}), 400

    f_pedidos = request.files['pedidos']
    f_stock   = request.files['stock']

    run_id  = uuid.uuid4().hex
    run_dir = UPLOADS_DIR / run_id
    run_dir.mkdir()

    path_pedidos = run_dir / f_pedidos.filename
    path_stock   = run_dir / f_stock.filename
    f_pedidos.save(str(path_pedidos))
    f_stock.save(str(path_stock))

    job_id = uuid.uuid4().hex
    _jobs[job_id] = {
        'status': 'pending', 'step': 'En cola...',
        'cruce_id': None, 'resumen': None, 'error': None,
    }

    t = threading.Thread(
        target=_run_job,
        args=(job_id, str(path_pedidos), str(path_stock), str(run_dir),
              f_pedidos.filename, f_stock.filename, g.user_id),
        daemon=True,
    )
    t.start()

    return jsonify({'ok': True, 'job_id': job_id})


@app.get('/api/jobs/<job_id>')
@require_auth
def job_status(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({'ok': False, 'motivo': 'job_no_encontrado'}), 404
    return jsonify({'ok': True, **job})

@app.get('/api/cruces/<int:cruce_id>/download')
@require_auth
def cruce_download(cruce_id):
    db  = get_db()
    row = db.execute('SELECT excel_path FROM cruces WHERE id = ?', (cruce_id,)).fetchone()
    if not row or not row['excel_path']:
        return jsonify({'ok': False, 'motivo': 'sin_excel'}), 404
    path = Path(row['excel_path'])
    if not path.exists():
        return jsonify({'ok': False, 'motivo': 'archivo_no_encontrado'}), 404
    return send_file(str(path), as_attachment=True, download_name=f'cruce_{cruce_id}.xlsx')

# ── Rutas lineas / estados cadete ───────────────────────────────────────────────

@app.get('/api/cruces/<int:cruce_id>/lineas')
@require_auth
def lineas_list(cruce_id):
    db = get_db()
    lineas = db.execute(
        'SELECT * FROM lineas WHERE cruce_id = ? ORDER BY nodo_asignado, nro_pedido',
        (cruce_id,)
    ).fetchall()
    result = []
    for l in lineas:
        d = dict(l)
        d['alternativas'] = json.loads(d['alternativas'] or '[]')
        result.append(d)
    return jsonify({'ok': True, 'lineas': result})

@app.patch('/api/cruces/<int:cruce_id>/lineas/<int:linea_id>')
@require_auth
def linea_update(cruce_id, linea_id):
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get('estado')
    motivo       = data.get('motivo', '')

    ESTADOS_VALIDOS = {'PENDIENTE', 'ENCONTRADO', 'NO_ENCONTRADO',
                       'MAL_STOCK', 'REASIGNADO', 'EN_REVISION', 'SIN_COBERTURA'}
    if nuevo_estado and nuevo_estado not in ESTADOS_VALIDOS:
        return jsonify({'ok': False, 'motivo': 'estado_invalido'}), 400

    db  = get_db()
    row = db.execute(
        'SELECT * FROM lineas WHERE id = ? AND cruce_id = ?', (linea_id, cruce_id)
    ).fetchone()
    if not row:
        return jsonify({'ok': False, 'motivo': 'no_encontrado'}), 404

    updates = {}
    if nuevo_estado:
        updates['estado']     = nuevo_estado
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
    if 'notas' in data:
        updates['notas'] = data['notas']
    if 'alternativa_nodo' in data:
        updates['alternativa_nodo'] = data['alternativa_nodo']

    if updates:
        set_clause = ', '.join(f'{k} = ?' for k in updates)
        db.execute(
            f'UPDATE lineas SET {set_clause} WHERE id = ?',
            list(updates.values()) + [linea_id]
        )

    if nuevo_estado and nuevo_estado != row['estado']:
        db.execute(
            '''INSERT INTO eventos_estado
               (linea_id, estado_anterior, estado_nuevo, motivo, origen)
               VALUES (?, ?, ?, ?, ?)''',
            (linea_id, row['estado'], nuevo_estado, motivo, g.rol)
        )

    db.commit()
    return jsonify({'ok': True})

@app.get('/api/cruces/<int:cruce_id>/progreso')
@require_auth
def cruce_progreso(cruce_id):
    db = get_db()
    row = db.execute(
        '''SELECT
             COUNT(*) as total,
             SUM(CASE WHEN estado = 'ENCONTRADO'    THEN 1 ELSE 0 END) as encontrado,
             SUM(CASE WHEN estado = 'NO_ENCONTRADO' THEN 1 ELSE 0 END) as no_encontrado,
             SUM(CASE WHEN estado = 'MAL_STOCK'     THEN 1 ELSE 0 END) as mal_stock,
             SUM(CASE WHEN estado = 'REASIGNADO'    THEN 1 ELSE 0 END) as reasignado,
             SUM(CASE WHEN estado = 'EN_REVISION'   THEN 1 ELSE 0 END) as en_revision,
             SUM(CASE WHEN estado = 'SIN_COBERTURA' THEN 1 ELSE 0 END) as sin_cobertura,
             SUM(CASE WHEN estado = 'PENDIENTE'     THEN 1 ELSE 0 END) as pendiente
           FROM lineas WHERE cruce_id = ?''',
        (cruce_id,)
    ).fetchone()
    d = dict(row)
    total = d['total'] or 1
    resueltos = (d['encontrado'] or 0) + (d['sin_cobertura'] or 0) + (d['no_encontrado'] or 0) + (d['reasignado'] or 0)
    d['pct_completado'] = round(resueltos / total * 100, 1)
    return jsonify({'ok': True, 'progreso': d})

# ── Entregas a puntos de retiro ─────────────────────────────────────────────────

@app.get('/api/cruces/<int:cruce_id>/entregas')
@require_auth
def cruces_entregas_list(cruce_id):
    db = get_db()

    # Pedidos únicos por punto de retiro
    rows = db.execute(
        '''SELECT punto_retiro, nro_pedido
           FROM lineas
           WHERE cruce_id = ? AND punto_retiro IS NOT NULL AND punto_retiro != ''
           ORDER BY punto_retiro, nro_pedido''',
        (cruce_id,)
    ).fetchall()

    # Confirmaciones existentes
    confs = db.execute(
        'SELECT * FROM entregas_confirmadas WHERE cruce_id = ?', (cruce_id,)
    ).fetchall()
    conf_map = {c['punto_retiro']: dict(c) for c in confs}

    # Farmacias habilitadas con sus pedidos seleccionados
    hab_rows = db.execute(
        'SELECT punto_retiro, nro_pedidos FROM entregas_habilitadas WHERE cruce_id = ?',
        (cruce_id,)
    ).fetchall()
    hab_map     = {r['punto_retiro']: json.loads(r['nro_pedidos'] or '[]') for r in hab_rows}
    habilitadas = set(hab_map.keys())

    # Pedidos con al menos un producto ENCONTRADO por punto de retiro
    enc_rows = db.execute(
        '''SELECT DISTINCT punto_retiro, nro_pedido FROM lineas
           WHERE cruce_id = ? AND estado = 'ENCONTRADO'
             AND punto_retiro IS NOT NULL AND punto_retiro != ''
             AND nro_pedido   IS NOT NULL AND nro_pedido   != ''
        ''', (cruce_id,)
    ).fetchall()
    enc_map: dict = {}
    for r in enc_rows:
        enc_map.setdefault(r['punto_retiro'], set()).add(r['nro_pedido'])

    # Agrupar por punto_retiro (pedidos únicos)
    grupos: dict = {}
    for r in rows:
        pt = r['punto_retiro']
        if pt not in grupos:
            grupos[pt] = set()
        if r['nro_pedido']:
            grupos[pt].add(r['nro_pedido'])

    result = []
    for pt, pedidos in sorted(grupos.items()):
        conf = conf_map.get(pt)
        todos_sorted      = sorted(list(pedidos))
        pedidos_activos   = hab_map.get(pt, [])
        pedidos_enc       = sorted(list(enc_map.get(pt, set())))
        result.append({
            'punto_retiro':       pt,
            'nro_pedidos':        todos_sorted,
            'total_pedidos':      len(pedidos),
            'activa':             pt in habilitadas,
            'pedidos_activos':    pedidos_activos,    # seleccionados por operador
            'pedidos_encontrados': pedidos_enc,        # pre-sugeridos (tienen ENCONTRADO)
            'confirmada':         conf is not None,
            'receptor':           conf['receptor']      if conf else None,
            'entregado_at':       conf['entregado_at']  if conf else None,
            'firma_base64':       conf['firma_base64']  if conf else None,
            'entrega_id':         conf['id']             if conf else None,
        })

    return jsonify({'ok': True, 'entregas': result, 'total': len(result)})


@app.post('/api/cruces/<int:cruce_id>/entregas/activar')
@require_auth
def cruces_entregas_activar(cruce_id):
    data         = request.get_json(silent=True) or {}
    punto_retiro = data.get('punto_retiro', '').strip()
    activa       = data.get('activa', True)
    nro_pedidos  = data.get('nro_pedidos', [])   # lista de pedidos seleccionados

    if not punto_retiro:
        return jsonify({'ok': False, 'motivo': 'falta_punto_retiro'}), 400

    db = get_db()
    if activa:
        db.execute(
            '''INSERT INTO entregas_habilitadas (cruce_id, punto_retiro, nro_pedidos)
               VALUES (?, ?, ?)
               ON CONFLICT(cruce_id, punto_retiro)
               DO UPDATE SET nro_pedidos = excluded.nro_pedidos''',
            (cruce_id, punto_retiro, json.dumps(nro_pedidos))
        )
    else:
        db.execute(
            'DELETE FROM entregas_habilitadas WHERE cruce_id = ? AND punto_retiro = ?',
            (cruce_id, punto_retiro)
        )
    db.commit()
    return jsonify({'ok': True, 'activa': activa})


@app.post('/api/cruces/<int:cruce_id>/entregas')
@require_auth
def cruces_entregas_confirmar(cruce_id):
    data         = request.get_json(silent=True) or {}
    punto_retiro = data.get('punto_retiro', '').strip()
    receptor     = data.get('receptor', '').strip()
    firma_b64    = data.get('firma_base64', '')

    if not punto_retiro or not receptor:
        return jsonify({'ok': False, 'motivo': 'campos_requeridos'}), 400

    db  = get_db()
    now = datetime.now(timezone.utc).isoformat()

    existing = db.execute(
        'SELECT id FROM entregas_confirmadas WHERE cruce_id = ? AND punto_retiro = ?',
        (cruce_id, punto_retiro)
    ).fetchone()

    if existing:
        db.execute(
            '''UPDATE entregas_confirmadas
               SET receptor = ?, firma_base64 = ?, entregado_at = ?, usuario_id = ?
               WHERE id = ?''',
            (receptor, firma_b64, now, g.user_id, existing['id'])
        )
    else:
        db.execute(
            '''INSERT INTO entregas_confirmadas
               (cruce_id, punto_retiro, receptor, firma_base64, entregado_at, usuario_id)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (cruce_id, punto_retiro, receptor, firma_b64, now, g.user_id)
        )

    db.commit()
    return jsonify({'ok': True})

# ── Incidencias (MAL_STOCK / NO_ENCONTRADO / EN_REVISION / REASIGNADO) ──────────

@app.get('/api/cruces/<int:cruce_id>/incidencias')
@require_auth
def cruce_incidencias(cruce_id):
    db = get_db()
    lineas = db.execute(
        '''SELECT * FROM lineas
           WHERE cruce_id = ? AND estado IN ('MAL_STOCK','NO_ENCONTRADO','EN_REVISION','REASIGNADO')
           ORDER BY updated_at DESC''',
        (cruce_id,)
    ).fetchall()
    result = []
    for l in lineas:
        d = dict(l)
        d['alternativas'] = json.loads(d['alternativas'] or '[]')
        result.append(d)
    return jsonify({'ok': True, 'incidencias': result, 'total': len(result)})

@app.get('/api/cruces/<int:cruce_id>/notificaciones')
@require_auth
def cruce_notificaciones(cruce_id):
    """Devuelve MAL_STOCK / NO_ENCONTRADO nuevos desde ?desde=<iso-timestamp>."""
    desde  = request.args.get('desde', '')
    db     = get_db()
    query  = '''SELECT id, nro_pedido, producto, nodo_asignado, estado, updated_at, punto_retiro
                FROM lineas
                WHERE cruce_id = ? AND estado IN ('MAL_STOCK','NO_ENCONTRADO')'''
    params = [cruce_id]
    if desde:
        query  += ' AND updated_at > ?'
        params.append(desde)
    query += ' ORDER BY updated_at DESC LIMIT 20'
    rows   = db.execute(query, params).fetchall()
    return jsonify({'ok': True, 'nuevas': [dict(r) for r in rows]})

# ── Analytics ───────────────────────────────────────────────────────────────────

def _analytics_query(db, desde=None, hasta=None):
    """Ejecuta todas las queries de analytics con filtro de rango de fechas."""
    params_c  = []
    params_l  = []
    where_c   = ''
    where_l   = ''

    if desde:
        where_c += ' AND c.created_at >= ?'
        where_l += ' AND cr.created_at >= ?'
        params_c.append(desde)
        params_l.append(desde)
    if hasta:
        # incluir todo el día "hasta"
        hasta_fin = hasta + 'T23:59:59'
        where_c  += ' AND c.created_at <= ?'
        where_l  += ' AND cr.created_at <= ?'
        params_c.append(hasta_fin)
        params_l.append(hasta_fin)

    totales = db.execute(
        f'''SELECT COUNT(*) as total_cruces,
                   COALESCE(AVG(c.pct_cobertura), 0) as cobertura_promedio,
                   COALESCE(SUM(c.total_lineas), 0)  as total_lineas,
                   COALESCE(SUM(c.con_cobertura), 0)  as total_con_cobertura,
                   COALESCE(SUM(c.sin_cobertura), 0)  as total_sin_cobertura,
                   COUNT(DISTINCT l.nro_pedido) as total_pedidos
            FROM cruces c
            LEFT JOIN lineas l ON l.cruce_id = c.id
            WHERE 1=1 {where_c}''',
        params_c
    ).fetchone()

    evolucion = db.execute(
        f'''SELECT DATE(c.created_at) as dia,
                   ROUND(AVG(c.pct_cobertura), 1) as cobertura,
                   SUM(c.total_lineas) as lineas,
                   COUNT(*) as cruces
            FROM cruces c WHERE 1=1 {where_c}
            GROUP BY dia ORDER BY dia DESC LIMIT 30''',
        params_c
    ).fetchall()

    top_productos = db.execute(
        f'''SELECT l.producto, COUNT(*) as veces,
                   SUM(l.unidades) as unidades
            FROM lineas l
            JOIN cruces cr ON cr.id = l.cruce_id
            WHERE l.producto IS NOT NULL AND l.producto != '' {where_l}
            GROUP BY l.producto ORDER BY veces DESC LIMIT 10''',
        params_l
    ).fetchall()

    top_sin_stock = db.execute(
        f'''SELECT l.producto, COUNT(*) as veces,
                   SUM(l.unidades) as unidades
            FROM lineas l
            JOIN cruces cr ON cr.id = l.cruce_id
            WHERE l.nodo_asignado IS NULL AND l.producto IS NOT NULL {where_l}
            GROUP BY l.producto ORDER BY veces DESC LIMIT 10''',
        params_l
    ).fetchall()

    top_farmacias = db.execute(
        f'''SELECT l.nodo_asignado as farmacia, COUNT(*) as lineas,
                   COUNT(DISTINCT l.nro_pedido) as pedidos
            FROM lineas l
            JOIN cruces cr ON cr.id = l.cruce_id
            WHERE l.nodo_asignado IS NOT NULL AND l.nodo_asignado != ''
              AND l.nodo_asignado != '— SIN COBERTURA —' {where_l}
            GROUP BY l.nodo_asignado ORDER BY lineas DESC LIMIT 10''',
        params_l
    ).fetchall()

    farmacias_problema = db.execute(
        f'''SELECT l.nodo_asignado as farmacia,
                   SUM(CASE WHEN l.estado IN ('MAL_STOCK','NO_ENCONTRADO') THEN 1 ELSE 0 END) as incidencias,
                   COUNT(*) as total_asignadas
            FROM lineas l
            JOIN cruces cr ON cr.id = l.cruce_id
            WHERE l.nodo_asignado IS NOT NULL AND l.nodo_asignado != ''
              AND l.nodo_asignado != '— SIN COBERTURA —' {where_l}
            GROUP BY l.nodo_asignado
            HAVING incidencias > 0
            ORDER BY incidencias DESC LIMIT 10''',
        params_l
    ).fetchall()

    top_puntos_retiro = db.execute(
        f'''SELECT l.punto_retiro, COUNT(DISTINCT l.nro_pedido) as pedidos
            FROM lineas l
            JOIN cruces cr ON cr.id = l.cruce_id
            WHERE l.punto_retiro IS NOT NULL AND l.punto_retiro != '' {where_l}
            GROUP BY l.punto_retiro ORDER BY pedidos DESC LIMIT 10''',
        params_l
    ).fetchall()

    return {
        'totales':           dict(totales),
        'evolucion':         [dict(r) for r in evolucion],
        'top_productos':     [dict(r) for r in top_productos],
        'top_sin_stock':     [dict(r) for r in top_sin_stock],
        'top_farmacias':     [dict(r) for r in top_farmacias],
        'farmacias_problema':[dict(r) for r in farmacias_problema],
        'top_puntos_retiro': [dict(r) for r in top_puntos_retiro],
    }


@app.get('/api/analytics')
@require_auth
def analytics():
    db    = get_db()
    desde = request.args.get('desde', '')
    hasta = request.args.get('hasta', '')
    data  = _analytics_query(db, desde or None, hasta or None)
    return jsonify({'ok': True, **data})


@app.get('/api/analytics/export')
@require_auth
def analytics_export():
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils  import get_column_letter

    db    = get_db()
    desde = request.args.get('desde', '')
    hasta = request.args.get('hasta', '')
    data  = _analytics_query(db, desde or None, hasta or None)

    wb = openpyxl.Workbook()

    hdr_font  = Font(bold=True, color='FFFFFF')
    hdr_fill  = PatternFill('solid', fgColor='1D4ED8')
    thin      = Side(style='thin', color='D1D5DB')
    border    = Border(left=thin, right=thin, top=thin, bottom=thin)

    def make_sheet(title, headers, rows):
        ws = wb.create_sheet(title)
        ws.append(headers)
        for cell in ws[1]:
            cell.font      = hdr_font
            cell.fill      = hdr_fill
            cell.alignment = Alignment(horizontal='center')
        for row in rows:
            ws.append(row)
        for col_idx in range(1, len(headers) + 1):
            col_letter = get_column_letter(col_idx)
            max_len    = max(
                (len(str(ws.cell(row=r, column=col_idx).value or ''))
                 for r in range(1, ws.max_row + 1)),
                default=8
            )
            ws.column_dimensions[col_letter].width = min(max_len + 4, 40)
        return ws

    del wb['Sheet']  # quitar hoja default

    # Resumen
    t   = data['totales']
    ws0 = wb.create_sheet('Resumen')
    periodo_str = f"{desde or 'inicio'} → {hasta or 'hoy'}"
    ws0['A1'] = 'Período'
    ws0['B1'] = periodo_str
    ws0['A1'].font = Font(bold=True)
    ws0.append(['Cruces realizados',        t['total_cruces']])
    ws0.append(['Cobertura promedio (%)',    round(t['cobertura_promedio'], 1)])
    ws0.append(['Líneas procesadas',         t['total_lineas']])
    ws0.append(['Pedidos únicos',            t['total_pedidos']])
    ws0.append(['Líneas con cobertura',      t['total_con_cobertura']])
    ws0.append(['Líneas sin cobertura',      t['total_sin_cobertura']])
    ws0.column_dimensions['A'].width = 28
    ws0.column_dimensions['B'].width = 20

    make_sheet(
        'Evolución',
        ['Día', 'Cobertura (%)', 'Líneas', 'Cruces'],
        [[r['dia'], r['cobertura'], r['lineas'], r['cruces']]
         for r in reversed(data['evolucion'])]
    )
    make_sheet(
        'Top Productos',
        ['Producto', 'Veces pedido', 'Unidades totales'],
        [[r['producto'], r['veces'], r['unidades']] for r in data['top_productos']]
    )
    make_sheet(
        'Sin Stock',
        ['Producto sin cobertura', 'Veces', 'Unidades afectadas'],
        [[r['producto'], r['veces'], r['unidades']] for r in data['top_sin_stock']]
    )
    make_sheet(
        'Top Farmacias',
        ['Farmacia', 'Líneas asignadas', 'Pedidos'],
        [[r['farmacia'], r['lineas'], r['pedidos']] for r in data['top_farmacias']]
    )
    make_sheet(
        'Farmacias Problema',
        ['Farmacia', 'Incidencias', 'Total asignadas'],
        [[r['farmacia'], r['incidencias'], r['total_asignadas']]
         for r in data['farmacias_problema']]
    )
    make_sheet(
        'Puntos de Retiro',
        ['Punto de retiro', 'Pedidos'],
        [[r['punto_retiro'], r['pedidos']] for r in data['top_puntos_retiro']]
    )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    fecha_str = datetime.now().strftime('%Y%m%d')
    nombre    = f'analytics_{fecha_str}.xlsx'
    return send_file(
        buf,
        as_attachment=True,
        download_name=nombre,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

# ── Procesamiento ───────────────────────────────────────────────────────────────

def _procesar_cruce(path_pedidos, path_stock, out_dir):
    """Orquesta el pipeline de procesamiento usando los módulos src/."""
    from src.loader     import cargar_archivo
    from src.matcher    import mapear_columnas_pedidos, mapear_columnas_stock
    from src.services.normalizacion import normalizar_pedidos, normalizar_stock
    from src.services.matching      import ejecutar_matching
    from src.optimizer  import construir_planilla
    from src.exporter   import exportar_excel_profesional, DatosExport

    with open(str(CONFIG_PATH), 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    df_pedidos = cargar_archivo(path_pedidos)
    df_stock   = cargar_archivo(path_stock)

    mapa_pedidos = mapear_columnas_pedidos(df_pedidos, config)
    mapa_stock   = mapear_columnas_stock(df_stock, config)

    df_pedidos = normalizar_pedidos(df_pedidos, mapa_pedidos)
    df_stock   = normalizar_stock(df_stock, mapa_stock)

    resultado_matching = ejecutar_matching(
        df_pedidos, df_stock, mapa_pedidos, mapa_stock, config
    )

    df_ruta, df_sin_stock, _ = construir_planilla(
        df_pedidos=df_pedidos, df_stock=df_stock,
        mapa_pedidos=mapa_pedidos, mapa_stock=mapa_stock, cfg=config,
    )

    excel_path = str(Path(out_dir) / 'planilla_cruce.xlsx')
    datos = DatosExport(
        df_ruta=df_ruta,
        df_sin_stock=df_sin_stock,
        estados_busqueda=config.get('estados_busqueda', []),
        resultado_matching=resultado_matching,
        archivo_pedidos=Path(path_pedidos).name,
        archivo_stock=Path(path_stock).name,
    )
    exportar_excel_profesional(datos, excel_path)

    # Convertir df_ruta al formato de líneas que espera la API
    lineas = []
    if not df_ruta.empty:
        for _, row in df_ruta.iterrows():
            farmacia = row.get('Farmacia', '')
            es_sin_cob = (not farmacia) or farmacia == '— SIN COBERTURA —'
            lineas.append({
                'nro_pedido':      str(row.get('N° Pedido', '') or ''),
                'gtin':            str(row.get('GTIN', '') or ''),
                'sku':             str(row.get('Zetti (ID)', '') or ''),
                'producto':        str(row.get('Producto', '') or ''),
                'marca':           '',
                'unidades':        int(row.get('Unidades a buscar') or row.get('Cantidad pedida') or 1),
                'nodo_asignado':    None if es_sin_cob else farmacia,
                'zona':             int(row.get('prioridad', 2)),
                'tier':             int(row.get('_tier', 2)),
                'stock_disponible': int(row.get('Stock sucursal', 0) or 0),
                'alternativas':     [],
                'punto_retiro':     str(row.get('Punto de Retiro', '') or ''),
            })

    # Líneas sin cobertura del df_sin_stock
    if not df_sin_stock.empty:
        for _, row in df_sin_stock.iterrows():
            lineas.append({
                'nro_pedido':      str(row.get('N° Pedido', '') or ''),
                'gtin':            str(row.get('GTIN', '') or ''),
                'sku':             str(row.get('SKU', '') or ''),
                'producto':        str(row.get('Producto', '') or ''),
                'marca':           '',
                'unidades':        int(row.get('Unidades', 1) or 1),
                'nodo_asignado':    None,
                'zona':             99,
                'tier':             99,
                'stock_disponible': 0,
                'alternativas':     [],
                'punto_retiro':     str(row.get('Punto de Retiro', '') or ''),
            })

    con_cob = sum(1 for l in lineas if l['nodo_asignado'])
    sin_cob = sum(1 for l in lineas if not l['nodo_asignado'])
    total   = len(lineas)
    pct     = round(con_cob / total * 100, 1) if total else 0

    return {
        'total':         total,
        'con_cobertura': con_cob,
        'sin_cobertura': sin_cob,
        'pct_cobertura': pct,
        'excel_path':    excel_path,
        'lineas':        lineas,
    }

# ── Gestión de usuarios (admin) ─────────────────────────────────────────────────

@app.get('/api/usuarios')
@require_admin
def usuarios_list():
    db   = get_db()
    rows = db.execute(
        'SELECT id, usuario, nombre, rol, created_at FROM usuarios ORDER BY id'
    ).fetchall()
    return jsonify({'ok': True, 'usuarios': [dict(r) for r in rows]})


@app.post('/api/usuarios')
@require_admin
def usuarios_crear():
    data     = request.get_json(silent=True) or {}
    usuario  = data.get('usuario', '').strip()
    nombre   = data.get('nombre', '').strip()
    password = data.get('password', '')
    rol      = data.get('rol', 'operador')

    if not usuario or not password:
        return jsonify({'ok': False, 'motivo': 'campos_requeridos'}), 400
    if rol not in ('admin', 'operador', 'cadete'):
        return jsonify({'ok': False, 'motivo': 'rol_invalido'}), 400

    db = get_db()
    if db.execute('SELECT id FROM usuarios WHERE usuario = ?', (usuario,)).fetchone():
        return jsonify({'ok': False, 'motivo': 'usuario_existente'}), 409

    db.execute(
        'INSERT INTO usuarios (usuario, nombre, password_hash, rol) VALUES (?, ?, ?, ?)',
        (usuario, nombre, generate_password_hash(password), rol)
    )
    db.commit()
    return jsonify({'ok': True})


@app.patch('/api/usuarios/<int:uid>')
@require_admin
def usuarios_editar(uid):
    data     = request.get_json(silent=True) or {}
    nombre   = data.get('nombre')
    password = data.get('password')
    rol      = data.get('rol')

    db = get_db()
    if not db.execute('SELECT id FROM usuarios WHERE id = ?', (uid,)).fetchone():
        return jsonify({'ok': False, 'motivo': 'no_existe'}), 404

    if nombre is not None:
        db.execute('UPDATE usuarios SET nombre = ? WHERE id = ?', (nombre.strip(), uid))
    if password:
        db.execute('UPDATE usuarios SET password_hash = ? WHERE id = ?',
                   (generate_password_hash(password), uid))
    if rol and rol in ('admin', 'operador', 'cadete'):
        db.execute('UPDATE usuarios SET rol = ? WHERE id = ?', (rol, uid))

    db.commit()
    return jsonify({'ok': True})


@app.delete('/api/usuarios/<int:uid>')
@require_admin
def usuarios_eliminar(uid):
    if uid == g.user_id:
        return jsonify({'ok': False, 'motivo': 'no_eliminar_propio'}), 400
    db = get_db()
    db.execute('DELETE FROM usuarios WHERE id = ?', (uid,))
    db.commit()
    return jsonify({'ok': True})


# ── Configuración del sistema ───────────────────────────────────────────────────

@app.get('/api/config')
@require_admin
def config_leer():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        return jsonify({'ok': False, 'motivo': str(e)}), 500
    return jsonify({
        'ok': True,
        'asignacion':  cfg.get('asignacion',  {}),
        'optimizacion': cfg.get('optimizacion', {}),
    })


@app.put('/api/config')
@require_admin
def config_guardar():
    body = request.get_json(force=True)
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        if 'asignacion' in body:
            a = cfg.setdefault('asignacion', {})
            for k in ('nodos_tier_0', 'nodos_tier_1', 'palabras_clave_tier_1',
                      'palabras_clave_tier_3', 'consolidacion_por_pedido',
                      'max_sucursales_por_producto'):
                if k in body['asignacion']:
                    a[k] = body['asignacion'][k]

        if 'optimizacion' in body:
            o = cfg.setdefault('optimizacion', {})
            for k in ('stock_seguridad', 'max_sucursales_por_producto',
                      'stock_sospechoso_umbral', 'max_opciones_override'):
                if k in body['optimizacion']:
                    o[k] = body['optimizacion'][k]

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except Exception as e:
        return jsonify({'ok': False, 'motivo': str(e)}), 500
    return jsonify({'ok': True})


# ── Jornada del día ─────────────────────────────────────────────────────────────

@app.get('/api/jornada/hoy')
@require_auth
def jornada_hoy():
    fecha = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    db    = get_db()
    row   = db.execute(
        'SELECT puntos, cruce_id FROM jornadas WHERE fecha = ? AND cadete_id = ?',
        (fecha, g.user_id)
    ).fetchone()
    if not row:
        return jsonify({'ok': True, 'jornada': None})
    return jsonify({'ok': True, 'jornada': {
        'puntos':   json.loads(row['puntos']),
        'cruce_id': row['cruce_id'],
    }})


@app.post('/api/jornada')
@require_auth
def jornada_guardar():
    body     = request.get_json(force=True)
    cruce_id = body.get('cruce_id')
    puntos   = body.get('puntos', [])
    fecha    = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    db = get_db()
    db.execute('''
        INSERT INTO jornadas (fecha, cadete_id, cruce_id, puntos)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(fecha, cadete_id) DO UPDATE SET
            puntos   = excluded.puntos,
            cruce_id = excluded.cruce_id
    ''', (fecha, g.user_id, cruce_id, json.dumps(puntos, ensure_ascii=False)))
    db.commit()
    return jsonify({'ok': True})


@app.get('/api/cruces/<int:cid>/jornadas')
@require_auth
def cruce_jornadas(cid):
    fecha = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    db    = get_db()
    rows  = db.execute('''
        SELECT j.cadete_id, u.nombre, u.usuario, j.puntos
        FROM jornadas j
        JOIN usuarios u ON u.id = j.cadete_id
        WHERE j.fecha = ? AND j.cruce_id = ?
    ''', (fecha, cid)).fetchall()
    return jsonify({'ok': True, 'jornadas': [
        {
            'cadete_id': r['cadete_id'],
            'nombre':    r['nombre'] or r['usuario'],
            'puntos':    json.loads(r['puntos']),
        }
        for r in rows
    ]})


# ── Servir frontend ─────────────────────────────────────────────────────────────

@app.get('/')
def root():
    return send_from_directory(str(BASE_DIR), 'login.html')

@app.get('/<path:path>')
def static_files(path):
    return send_from_directory(str(BASE_DIR), path)

# ── Main ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        init_db()
    print('\n  Cruce Stock Farmacias')
    print('  http://localhost:5050\n')
    app.run(host='0.0.0.0', port=5050, debug=True)
