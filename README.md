# Cruce Stock — Farmacias Global

Sistema web para cruzar pedidos ecommerce con el stock disponible en sucursales, generar la planilla del cadete, y hacer seguimiento del trabajo de retiro en tiempo real.

---

## Por qué existe

Antes del sistema, el operador exportaba el cruce a Excel, lo importaba manualmente a Google Sheets, y el cadete usaba esa planilla en la tablet para marcar los estados (encontrado / mal stock / etc.). El operador monitoreaba el Sheet en paralelo para actuar sobre los problemas.

Este sistema reemplaza ese flujo por una herramienta web integrada: el mismo cruce genera la vista del cadete directamente, y el operador tiene una pantalla de seguimiento en vivo sin necesidad de Sheets.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python · Flask · SQLite |
| Auth | JWT (PyJWT) · bcrypt (werkzeug) |
| Procesamiento | pandas · rapidfuzz · openpyxl |
| Frontend | HTML + CSS + Vanilla JS (ES modules) |
| PWA | Service Worker (network-first) · Web App Manifest |
| Deploy | Railway (1 worker gunicorn gthread · volumen persistente `/data`) |
| Config | `config.yaml` |

Sin frameworks frontend (React, Vue, etc.). Deliberado: sin build steps, corre directo en Railway o red local.

---

## Estructura de archivos

```
cruce-stock-farmacias/
├── server/
│   └── app.py              ← Backend Flask completo (API REST + serve frontend)
├── cruce_stock/
│   ├── config.yaml         ← Configuración de columnas, zonas, tiers
│   └── src/
│       ├── loader.py           ← Carga xlsx/csv, detecta encoding
│       ├── matcher.py          ← Mapeo fuzzy de columnas al config
│       ├── optimizer.py        ← construir_planilla(): asigna sucursales a cada pedido
│       ├── exporter.py         ← exportar_excel_profesional(): genera el xlsx final
│       └── services/
│           ├── normalizacion.py
│           ├── matching.py
│           └── asignacion.py
├── css/
│   ├── variables.css       ← Tokens de diseño (colores, espaciado, tipografía)
│   ├── reset.css
│   ├── layout.css          ← Header, main, grids, menú mobile, progress bar fija
│   └── components.css      ← Botones, cards, badges, formularios, toasts, stat-cards
├── js/
│   ├── auth.js             ← Login, logout, JWT, auto-refresh
│   ├── mobile-nav.js       ← Hamburger + drawer lateral (mobile/tablet)
│   ├── storage.js          ← Persistencia de sesión en IndexedDB
│   └── toast.js            ← Notificaciones flotantes
├── img/
│   └── logo-global.png
├── login.html              ← Pantalla de ingreso
├── index.html              ← Dashboard (admin/operador) o redirect (cadete → ruta del día)
├── nuevo-cruce.html        ← Upload de archivos y generación del cruce
├── historial.html          ← Lista de todos los cruces con opción de borrar
├── cadete.html             ← Vista de trabajo del cadete (PWA, mobile-first)
├── operador.html           ← Seguimiento en vivo para el operador
├── usuarios.html           ← Gestión de usuarios (admin)
├── config.html             ← Configuración de columnas y tiers (admin)
├── manifest.json           ← PWA manifest
├── sw.js                   ← Service Worker (network-first para HTML, cache para assets)
└── requirements.txt
```

---

## Cómo iniciar (local)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Levantar el servidor
python server/app.py

# 3. Abrir en el navegador
http://localhost:5050
```

La base de datos se crea automáticamente. Usuarios por defecto:

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | admin |
| cadete | cadete123 | cadete |

**Cambiar las contraseñas antes de usar en producción.**

Variables de entorno relevantes:
- `CRUCE_DB_PATH` — ruta de la base de datos (default: `server/cruce.db`)
- `CRUCE_UPLOADS_DIR` — directorio de uploads (default: `server/uploads`)
- `SECRET_KEY` — clave JWT (obligatoria en producción)

---

## Deploy (Railway)

```bash
# Requiere Railway CLI instalado
railway up --service farmacias-global
```

- URL pública: `https://farmacias-global-production.up.railway.app`
- Volumen persistente montado en `/data` (DB + uploads sobreviven redeploys)
- **Railway NO está conectado a GitHub** — cada cambio requiere `railway up` manual
- Gunicorn: 1 worker + 4 threads (`gthread`) — con 2 workers el dict `_jobs` no se comparte entre procesos

---

## Roles y permisos

### admin
- Todo lo de operador, más:
- Gestión de usuarios (crear, editar rol/nombre, cambiar contraseña, eliminar)
- Configuración de columnas y tiers (`config.yaml` vía UI)
- Borrar cruces del historial

### operador
- Genera nuevos cruces (sube archivos pedidos + stock)
- Ve el dashboard con analytics históricos
- Ve el historial de cruces y descarga Excel de cualquier cruce
- Accede a la **vista operador**: seguimiento en vivo, incidencias, entregas del día
- Agrega productos manualmente a un cruce activo
- Reasigna sucursales a líneas existentes
- Activa/desactiva farmacias para la jornada del cadete

### cadete
- Al hacer login es redirigido directamente a su vista de trabajo del último cruce
- No ve Dashboard, Historial, ni Nuevo cruce
- Planifica su jornada: registra qué farmacias va a visitar
- Marca el estado de cada línea: Encontrado / No encontrado / Mal stock / En revisión
- Al marcar Mal stock puede anotar una sucursal alternativa donde vio el producto
- Agrega notas libres a cualquier línea
- Confirma entregas por farmacia con nombre del receptor y firma digital
- La vista es PWA: se puede instalar en la tablet y funciona con conexión inestable

---

## Pipeline de procesamiento

Cuando el operador sube los dos archivos, el backend ejecuta `_procesar_cruce()`:

```
cargar_archivo(pedidos)          →  DataFrame raw
cargar_archivo(stock)            →  DataFrame raw
    ↓
mapear_columnas_pedidos(df, cfg) →  {'nro_pedido': 'col_A', 'gtin': 'col_B', ...}
mapear_columnas_stock(df, cfg)   →  {'nodo': 'col_X', 'stock': 'col_Y', ...}
    ↓  (fuzzy matching contra config.yaml para tolerar cambios de nombre de columna)
normalizar_pedidos(df, mapa)     →  DataFrame con columnas estandarizadas
normalizar_stock(df, mapa)       →  DataFrame con columnas estandarizadas
    ↓
ejecutar_matching(ped, stk)      →  ResultadoMatching (por GTIN primero, SKU como fallback)
    ↓
construir_planilla(...)          →  df_ruta + df_sin_stock
    ↓  (asigna sucursales con lógica de tiers + consolidación de pedidos)
exportar_excel_profesional(...)  →  planilla_cruce.xlsx (4 hojas)
    ↓
INSERT en lineas (SQLite)        →  estado = PENDIENTE / SIN_COBERTURA
```

### Lógica de asignación (tiers)

| Tier | Criterio |
|---|---|
| 0 | Sucursales preferidas (`nodos_tier_0` en config.yaml) |
| 1 | Segunda opción (`nodos_tier_1` + `palabras_clave_tier_1`) |
| 2 | Resto (default) |
| 3 | Último recurso (`palabras_clave_tier_3`) |

**Bonus de consolidación**: si una sucursal ya tiene otro producto del mismo pedido asignado, se la prefiere para minimizar paradas del cadete.

**Alternativas**: cada línea guarda las top-3 sucursales con stock como JSON en `alternativas` — visibles en la vista cadete y en el modal de reasignación del operador.

---

## API REST

Base URL: `/api` · Todas las rutas requieren `Authorization: Bearer <token>`.

### Auth
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/login` | Login. Body: `{usuario, password}`. Devuelve JWT. |
| POST | `/auth/refresh` | Renueva el token. |
| POST | `/auth/logout` | Invalida la sesión del cliente. |

### Cruces
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/cruces` | Lista los últimos 50 cruces. |
| POST | `/cruces` | Crea un cruce. Form-data: `pedidos` (file), `stock` (file). Devuelve `job_id`. |
| GET | `/cruces/:id` | Detalle de un cruce. |
| DELETE | `/cruces/:id` | Elimina un cruce y sus líneas (admin). |
| GET | `/cruces/:id/download` | Descarga el Excel generado al crear el cruce. |
| GET | `/cruces/:id/export` | Genera y descarga un Excel fresco con el estado actual de las líneas. |
| GET | `/jobs/:job_id` | Polling del estado de procesamiento asíncrono del cruce. |

### Líneas
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/cruces/:id/lineas` | Lista todas las líneas del cruce. |
| POST | `/cruces/:id/lineas` | Agrega una línea manualmente (admin/operador). Body: `{gtin, sku, producto, nodo_asignado, unidades, nro_pedido, notas}`. |
| PATCH | `/cruces/:id/lineas/:lid` | Actualiza estado, notas, alternativa_nodo, nodo_asignado, stock_disponible. |
| GET | `/cruces/:id/progreso` | Resumen de estados + % completado. |
| GET | `/cruces/:id/incidencias` | Líneas con MAL_STOCK / NO_ENCONTRADO / EN_REVISION / REASIGNADO. |
| GET | `/cruces/:id/notificaciones` | Incidencias nuevas desde `?desde=<ISO>` (usado por el poll del operador). |
| GET | `/cruces/:id/nodos` | Lista de sucursales asignadas en el cruce (para datalists). |

### Entregas
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/cruces/:id/entregas` | Farmacias de retiro con estado de confirmación y pedidos. |
| POST | `/cruces/:id/entregas` | Confirma entrega. Body: `{punto_retiro, receptor, firma_base64}`. |
| POST | `/cruces/:id/entregas/activar` | Activa/desactiva una farmacia para la jornada. Body: `{punto_retiro, activa, nro_pedidos}`. |

### Jornada
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/jornada/hoy` | Jornada del cadete autenticado para hoy. |
| POST | `/jornada` | Guarda la jornada del día. Body: `{cruce_id, puntos: []}`. |
| GET | `/cruces/:id/jornadas` | Todas las jornadas registradas para un cruce. |

### Sucursales fijas
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/sucursales-fijas` | Agrega una sucursal fija al cruce (sin pedidos asociados). |
| DELETE | `/sucursales-fijas` | Elimina una sucursal fija. |

### Usuarios (admin)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/usuarios` | Lista todos los usuarios. |
| POST | `/usuarios` | Crea un usuario. Body: `{usuario, password, nombre, rol}`. |
| PATCH | `/usuarios/:id` | Edita nombre, rol o contraseña. |
| DELETE | `/usuarios/:id` | Elimina un usuario. |

### Configuración (admin)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/config` | Lee el `config.yaml` actual. |
| PUT | `/config` | Guarda el `config.yaml`. |
| GET | `/config/sugerencias` | Nombres de columnas detectados en el último cruce (para autocompletar config). |

### Analytics
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/analytics` | Totales históricos, tendencia de cobertura, top productos sin stock, top nodos. Soporta `?desde=&hasta=`. |
| GET | `/analytics/export` | Exporta el período filtrado a Excel. |

### Misc
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check (`{"ok": true}`). |

### Estados válidos de línea

`PENDIENTE` · `ENCONTRADO` · `NO_ENCONTRADO` · `MAL_STOCK` · `REASIGNADO` · `EN_REVISION` · `SIN_COBERTURA`

% completado = (ENCONTRADO + NO_ENCONTRADO + SIN_COBERTURA + REASIGNADO) / total. Las líneas SIN_COBERTURA no requieren acción del cadete.

---

## Base de datos

```sql
usuarios              id, usuario, password_hash, nombre, rol, created_at

cruces                id, fecha, archivo_pedidos, archivo_stock, total_lineas,
                      con_cobertura, sin_cobertura, pct_cobertura, excel_path,
                      usuario_id, created_at

lineas                id, cruce_id, nro_pedido, gtin, sku, producto, marca,
                      unidades, nodo_asignado, zona, tier, stock_disponible,
                      alternativas (JSON top-3), estado, notas, alternativa_nodo,
                      punto_retiro, updated_at

eventos_estado        id, linea_id, estado_anterior, estado_nuevo, motivo,
                      origen (rol), created_at

entregas_confirmadas  id, cruce_id, punto_retiro, receptor, firma_base64,
                      entregado_at, usuario_id
                      UNIQUE(cruce_id, punto_retiro)

entregas_habilitadas  cruce_id, punto_retiro, nro_pedidos (JSON)
                      PRIMARY KEY(cruce_id, punto_retiro)

jornadas              id, fecha, cadete_id, cruce_id, puntos (JSON), created_at
                      UNIQUE(fecha, cadete_id)
```

**Notas:**
- `alternativas`: top-3 sucursales con stock disponible, guardadas al generar el cruce. Visibles en vista cadete y modal reasignar.
- `alternativa_nodo`: sucursal que el cadete anotó al marcar MAL_STOCK. Visible en el operador.
- `eventos_estado`: historial completo de cambios de estado con quién hizo cada cambio.
- `entregas_habilitadas`: qué pedidos va a dejar el cadete en cada farmacia hoy (activación manual por el operador).
- `jornadas`: farmacias que el cadete planifica visitar. Visible en el operador para anticipar problemas.

---

## Flujo operativo diario

```
MAÑANA — antes de salir
──────────────────────
1. Operador: Nuevo cruce → sube pedidos + stock → planilla generada
2. Operador: abre Vista operador → pantalla de seguimiento en vivo
3. Operador: activa farmacias para la jornada (asigna pedidos a cada punto de retiro)

RUTA — el cadete en la tablet
─────────────────────────────
4. Cadete: login → redirigido a cadete.html (último cruce)
5. Cadete: planifica jornada (qué farmacias va a visitar hoy)
6. Modo 🔍 Búsqueda — en cada farmacia:
   · Filtra por sucursal
   · Encontrado / No encontrado / Mal stock (+ sucursal alternativa opcional)
7. Operador: ve incidencias en tiempo real (auto-refresh 30s + alertas push)
   · MAL_STOCK con alternativa → contacta esa sucursal
   · NO_ENCONTRADO → llama al cliente

AL DEJAR LOS PEDIDOS — cierre en cada farmacia
───────────────────────────────────────────────
8. Cadete: cambia a modo 📦 Entregas del día
9. Toca la farmacia → lista los pedidos a dejar
10. Confirmar entrega → nombre del receptor → firma digital en el canvas
11. Firma guardada en SQLite (trazabilidad para reclamos)

OPERADOR — Entregas del día
────────────────────────────
12. Tiles verdes = confirmadas (receptor + hora + firma)
13. Tiles azules = activas sin confirmar
14. Click "Ver firma" → abre el PNG

CIERRE DEL DÍA
──────────────
15. Operador descarga el Excel con el estado final del cruce
```

---

## Configuración (`config.yaml`)

Define los nombres de columnas esperados en los archivos de entrada (con múltiples candidatos para tolerancia a cambios), zonas geográficas, tiers de sucursales, y parámetros de asignación. El mapeo usa fuzzy matching (RapidFuzz, score mínimo 70).

Editable desde la UI en `config.html` (solo admin).

---

## Roadmap

### Hecho ✓
- [x] Cruce automático pedidos/stock — pipeline con fuzzy column matching y lógica de tiers
- [x] Vista cadete mobile-first — filtros, cards con franja de color por estado, firma digital
- [x] Vista operador en tiempo real — progreso, incidencias, entregas, auto-refresh 30s
- [x] Incidencias con alternativas — top-3 sucursales clickeables en cadete y modal reasignar
- [x] Puntos de retiro — modo Entregas con activación por operador y firma del receptor
- [x] Notificaciones push — alertas al operador cuando el cadete reporta MAL_STOCK / NO_ENCONTRADO
- [x] Jornada del cadete — el cadete planifica qué farmacias visita; visible en operador
- [x] Gestión de usuarios — UI completa (crear, editar, cambiar contraseña, eliminar)
- [x] Configuración via UI — editar `config.yaml` desde el browser sin tocar el servidor
- [x] Historial con borrado — lista de todos los cruces con delete (admin)
- [x] Exportar Excel del estado actual — no solo el Excel original sino el estado en vivo
- [x] PWA instalable — manifest + service worker (network-first); funciona en tablet del cadete
- [x] Roles — admin / operador / cadete con navegación diferenciada

### Pendiente
- [ ] Procesamiento asíncroco mejorado — mover `_procesar_cruce()` a Celery/RQ para archivos grandes
- [ ] Multi-cadete — asignación de zonas específicas por cadete; jornadas independientes
- [ ] Analytics avanzado — comparación entre cruces, tendencia de incidencias por sucursal
