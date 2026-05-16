# Cruce Stock — Farmacias

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
| Config | `config.yaml` |

Sin frameworks frontend (React, Vue, etc.). Deliberado: el sistema corre en una red local o servidor simple, sin build steps.

---

## Estructura de archivos

```
cruce-stock-farmacias/
├── server/
│   ├── app.py              ← Backend Flask (API REST + serve frontend)
│   └── cruce.db            ← Base de datos SQLite (generada al iniciar)
├── cruce_stock/
│   ├── config.yaml         ← Configuración de columnas, zonas, tiers
│   ├── streamlit_app.py    ← App Streamlit original (referencia)
│   └── src/
│       ├── loader.py           ← Carga xlsx/csv, detecta encoding
│       ├── matcher.py          ← Mapeo fuzzy de columnas al config
│       ├── optimizer.py        ← construir_planilla(): asigna sucursales a cada pedido
│       ├── exporter.py         ← exportar_excel_profesional(): genera el xlsx final
│       ├── logger.py
│       └── services/
│           ├── normalizacion.py  ← normalizar_pedidos() / normalizar_stock()
│           ├── matching.py       ← ejecutar_matching(): cruza por GTIN/SKU
│           └── asignacion.py     ← asignar_producto_inteligente(): lógica de tiers
├── css/
│   ├── variables.css       ← Tokens de diseño (colores, espaciado, tipografía)
│   ├── reset.css
│   ├── layout.css          ← Header, main, grids, progress bar fija
│   └── components.css      ← Botones, cards, badges, tablas, formularios, toasts
├── js/
│   ├── auth.js             ← Login, logout, JWT, auto-refresh de sesión
│   ├── storage.js          ← Persistencia de sesión en IndexedDB
│   └── toast.js            ← Notificaciones flotantes
├── login.html              ← Pantalla de ingreso
├── index.html              ← Dashboard (admin/operador) o redirect (cadete)
├── nuevo-cruce.html        ← Upload de archivos y generación del cruce
├── historial.html          ← Lista de todos los cruces
├── cadete.html             ← Vista de trabajo del cadete
├── operador.html           ← Seguimiento en vivo para el operador
└── requirements.txt
```

---

## Cómo iniciar

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Levantar el servidor
python server/app.py

# 3. Abrir en el navegador
http://localhost:5050
```

La base de datos se crea automáticamente en `server/cruce.db` con dos usuarios por defecto:

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | admin |
| cadete | cadete123 | cadete |

**Cambiar las contraseñas antes de usar en producción.**

---

## Roles y permisos

### admin / operador
- Genera nuevos cruces (sube archivos pedidos + stock)
- Ve el dashboard con analytics
- Ve el historial de cruces
- Descarga el Excel de cualquier cruce
- Accede a la **vista operador**: seguimiento en vivo del progreso del cadete
- Puede ver la vista cadete de cualquier cruce

### cadete
- Al hacer login es redirigido directamente a su vista de trabajo del último cruce
- No ve Dashboard, Historial, ni "Nuevo cruce"
- Marca el estado de cada línea: Encontrado / No encontrado / Mal stock / En revisión
- Al marcar Mal stock puede anotar una sucursal alternativa donde vio el producto
- Puede agregar notas libres a cualquier línea

La lógica de roles está implementada en el frontend: `document.body.dataset.rol = session.rol` + CSS `.admin-only { display:none }` para el rol cadete. El backend tiene `require_auth` en todas las rutas y `require_admin` disponible para restringir rutas a admin.

---

## Pipeline de procesamiento

Cuando el operador sube los dos archivos y hace click en "Generar planilla", el backend ejecuta este pipeline en `_procesar_cruce()`:

```
cargar_archivo(pedidos)          →  DataFrame raw
cargar_archivo(stock)            →  DataFrame raw
    ↓
mapear_columnas_pedidos(df, cfg) →  {'nro_pedido': 'col_A', 'gtin': 'col_B', ...}
mapear_columnas_stock(df, cfg)   →  {'nodo': 'col_X', 'stock': 'col_Y', ...}
    ↓  (fuzzy matching contra config.yaml para tolerar cambios de nombre de columna)
normalizar_pedidos(df, mapa)     →  DataFrame con columnas estandarizadas + _gtin_norm
normalizar_stock(df, mapa)       →  DataFrame con columnas estandarizadas + _id_norm
    ↓
ejecutar_matching(ped, stk, ...)  →  ResultadoMatching (por GTIN primero, SKU como fallback)
    ↓
construir_planilla(...)          →  df_ruta + df_sin_stock
    ↓  (asigna sucursales con lógica de tiers + consolidación de pedidos)
exportar_excel_profesional(...)  →  planilla_cruce.xlsx (4 hojas)
    ↓
INSERT en lineas (SQLite)        →  estado inicial = PENDIENTE / SIN_COBERTURA
```

### Lógica de asignación (tiers)

El sistema prioriza sucursales en este orden:

| Tier | Criterio |
|---|---|
| 0 | Sucursales preferidas (definidas en config.yaml > asignacion > nodos_tier_0) |
| 1 | Segunda opción (nodos_tier_1 + palabras_clave_tier_1) |
| 2 | Resto (default) |
| 3 | Último recurso (palabras_clave_tier_3) |

Además aplica **bonus de consolidación**: si una sucursal ya tiene otro producto del mismo pedido asignado, se la prefiere para minimizar paradas del cadete.

---

## API REST

Base URL: `http://localhost:5050/api`

Todas las rutas requieren header `Authorization: Bearer <token>`.

### Auth
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/login` | Login. Body: `{usuario, password}`. Devuelve JWT. |
| POST | `/auth/refresh` | Renueva el token antes de que expire. |
| POST | `/auth/logout` | Invalida la sesión del cliente. |

### Cruces
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/cruces` | Lista los últimos 50 cruces. |
| POST | `/cruces` | Crea un cruce nuevo. Form-data: `pedidos` (file), `stock` (file). |
| GET | `/cruces/:id` | Detalle de un cruce + sus líneas. |
| GET | `/cruces/:id/download` | Descarga el Excel generado. |

### Líneas
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/cruces/:id/lineas` | Lista todas las líneas del cruce. |
| PATCH | `/cruces/:id/lineas/:lid` | Actualiza estado, notas, o alternativa_nodo de una línea. |
| GET | `/cruces/:id/progreso` | Resumen de estados + % completado. |
| GET | `/cruces/:id/incidencias` | Solo líneas con MAL_STOCK / NO_ENCONTRADO / EN_REVISION / REASIGNADO. |

### Entregas a puntos de retiro
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/cruces/:id/entregas` | Lista farmacias de retiro del cruce, agrupadas con sus pedidos y estado de confirmación. |
| POST | `/cruces/:id/entregas` | Confirma entrega en una farmacia. Body: `{punto_retiro, receptor, firma_base64}`. |

El campo `firma_base64` es un PNG en base64 capturado desde la tablet del cadete. Se guarda en SQLite y es visible desde la vista operador haciendo click en "Ver firma".

### Analytics
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/analytics` | Totales históricos, tendencia de cobertura, top productos sin stock, top nodos. |

### Estados válidos de línea
`PENDIENTE` · `ENCONTRADO` · `NO_ENCONTRADO` · `MAL_STOCK` · `REASIGNADO` · `EN_REVISION` · `SIN_COBERTURA`

El cálculo de % completado cuenta como resueltos: ENCONTRADO + NO_ENCONTRADO + SIN_COBERTURA + REASIGNADO. Las líneas SIN_COBERTURA no requieren acción del cadete.

---

## Base de datos

```sql
usuarios              id, usuario, password_hash, nombre, rol, created_at
cruces                id, fecha, archivo_pedidos, archivo_stock, total_lineas,
                      con_cobertura, sin_cobertura, pct_cobertura, excel_path,
                      usuario_id, created_at
lineas                id, cruce_id, nro_pedido, gtin, sku, producto, marca,
                      unidades, nodo_asignado, zona, tier, stock_disponible,
                      alternativas (JSON), estado, notas, alternativa_nodo,
                      punto_retiro, updated_at
eventos_estado        id, linea_id, estado_anterior, estado_nuevo, motivo,
                      origen (rol del usuario), created_at
entregas_confirmadas  id, cruce_id, punto_retiro, receptor, firma_base64,
                      entregado_at, usuario_id
                      UNIQUE(cruce_id, punto_retiro)
```

- `eventos_estado`: historial completo de cambios de estado con quién hizo cada cambio.
- `alternativa_nodo`: sucursal que el cadete anotó al marcar MAL_STOCK. Visible en operador.
- `punto_retiro`: farmacia elegida por el cliente al comprar. Viene de la columna "Sucursal" del archivo de pedidos.
- `entregas_confirmadas`: una fila por farmacia-por-cruce cuando el cadete registra la entrega. La firma digital se guarda como PNG en base64. El constraint UNIQUE garantiza que no haya duplicados (re-confirmar sobreescribe).

---

## Flujo operativo diario

```
MAÑANA — antes de salir
──────────────────────
1. Operador sube archivos → "Nuevo cruce" → planilla generada
2. Operador abre "Vista operador" → pantalla de seguimiento en vivo

DURANTE LA RUTA — el cadete en la tablet
─────────────────────────────────────────
3. Cadete loguea → redirigido a cadete.html con el último cruce
4. Modo 🔍 Búsqueda (pestaña por defecto):
   - Filtra por sucursal al llegar a cada farmacia
   - Por cada producto:
     · Encontrado → toca "Encontrado"
     · No está    → toca "No encontrado"
     · Cantidad mal → toca "Mal stock" → anota sucursal alternativa (opcional)
5. Operador ve incidencias en tiempo real (auto-refresh 30s):
   - Si hay MAL_STOCK con alternativa: contacta esa sucursal
   - Si hay NO_ENCONTRADO: llama al cliente (alternativa o devolución)

AL DEJAR LOS PEDIDOS — cierre en cada farmacia
───────────────────────────────────────────────
6. Cadete cambia a modo 📦 Entregas del día
7. Toca la farmacia correspondiente → lista los pedidos que deja
8. Toca "Confirmar entrega" → ingresa nombre del receptor
9. Receptor firma en el canvas de la tablet
10. Firma queda guardada en el sistema (trazabilidad para reclamos)

OPERADOR — vista en tiempo real
────────────────────────────────
11. Sección "Entregas del día" en operador.html:
    - Tiles verdes = farmacia confirmada (con nombre receptor + hora)
    - Tiles grises = farmacia pendiente
    - Click "Ver firma" → abre el PNG de la firma

CIERRE DEL DÍA
──────────────
12. Operador descarga el Excel con el estado final del cruce
```

---

## Configuración (`config.yaml`)

Define los nombres de columnas esperados en los archivos de entrada (con múltiples candidatos para tolerancia de cambios), zonas geográficas, tiers de sucursales, y parámetros de asignación. El mapeo usa fuzzy matching (RapidFuzz) con score mínimo 70.

---

## Roadmap

### Hecho ✓
- [x] **Cruce automático pedidos/stock** — pipeline completo con fuzzy column matching y lógica de tiers.
- [x] **Vista cadete** — filtro por sucursal, chips de estado, modal MAL STOCK con sucursal alternativa.
- [x] **Vista operador en tiempo real** — progreso del cadete, incidencias, auto-refresh 30s.
- [x] **Puntos de retiro** — columna "Sucursal" del archivo de pedidos mapeada al sistema; modo 📦 Entregas en la tablet.
- [x] **Firma digital** — el cadete registra receptor y captura firma PNG por farmacia. Guardada en SQLite, visible desde operador.
- [x] **Roles** — admin/operador/cadete con navegación diferenciada.

### Pendiente
- [ ] **Gestión de usuarios** — UI para crear/editar usuarios desde admin, sin editar la DB directamente.
- [ ] **App mobile PWA** — el frontend ya es mobile-friendly; instalar como PWA en la tablet del cadete.
- [ ] **Procesamiento asíncrono** — mover `_procesar_cruce()` a un worker para no bloquear Flask durante archivos grandes.
- [ ] **Notificaciones push** — avisar al operador cuando el cadete marca incidencias sin que tenga que mirar la pantalla.
- [ ] **Multi-cadete** — asignación de nodos/zonas específicas por cadete.
- [ ] **Jornada del día** — que el cadete registre en el sistema qué farmacias va a visitar, para que el operador ajuste la búsqueda de stock antes de imprimir la planilla.
