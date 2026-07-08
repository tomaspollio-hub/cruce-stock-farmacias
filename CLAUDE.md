# Notas para trabajar en este código

Ver `README.md` para stack, endpoints y esquema de base de datos. Esto es lo que **no** está en el README y causó más de un bug: el modelo de datos de entregas tiene tres campos que parecen intercambiables y no lo son.

## Los tres "nombres" de una farmacia

Una misma entrega puede tener hasta tres strings distintos flotando en el código. Confundirlos generó bugs reales (cards "duplicadas" en Operador, pedidos mostrando 0 pese a haber sido entregados).

| Campo | Qué es | De dónde sale |
|---|---|---|
| `punto_retiro` | La **identidad real** de la entrega — el destino donde el cadete tiene que ir. Es la clave primaria de facto: confirmaciones, activaciones y pedidos se agrupan por este valor exacto. | Columna del archivo de pedidos (ecommerce), o `nodo_asignado` cuando no hay punto_retiro propio, o `sucursales_fijas` de `config.yaml`. |
| `nodo_asignado` | La sucursal que **aportó el stock** para una línea de pedido. Puede ser una sucursal distinta a `punto_retiro` — es normal y esperado: el sistema existe justamente para cruzar pedidos con stock de *cualquier* sucursal, no solo la del destino. | Resultado del matcher/optimizer (`cruce_stock/src/optimizer.py`). |
| `nombre_display` | Nombre "lindo" para mostrar en vez del código crudo de `punto_retiro`. Se calcula tomando el `nodo_asignado` más frecuente de esa entrega, **solo si comparte el número de calle** con `punto_retiro` (ver `_mismo_lugar()` en `server/app.py`, función `cruces_entregas_list`). Si no coincide, se muestra `punto_retiro` tal cual. | Calculado en cada request, no se persiste. |

**Regla dura: nunca uses `nombre_display` como identidad.** Dos entregas con destinos distintos pueden mostrar el mismo `nombre_display` por coincidencia (ambas fulfilleadas mayormente desde la misma sucursal grande). Si necesitás saber "es la misma entrega", comparás por `punto_retiro`, nunca por el nombre mostrado.

Antes de `_mismo_lugar()` (jul 2026) el código confiaba ciegamente en "nodo_asignado más frecuente" y eso rompía la UI cada vez que una entrega se fulfilleaba cruzada. Si tocás `nombre_display_map`, no vuelvas a esa versión sin el filtro de número de calle.

## Los tres "conteos de pedidos"

Mismo problema, versión numérica:

| Campo | Qué cuenta | Cuándo es 0 aunque haya una entrega real |
|---|---|---|
| `total_pedidos` / `nro_pedidos` | Pedidos que el **cruce automático** matcheó por `punto_retiro` en la tabla `lineas`. | Cuando el operador activó la farmacia a mano (`Activar manualmente`) e ingresó números de pedido a mano — esos números no tocan `lineas`, así que este campo no los ve. |
| `pedidos_encontrados` | Subconjunto de lo anterior con estado `ENCONTRADO` (stock confirmado). | Mismo caso que arriba, siempre. |
| `pedidos_activos` | Lo que el **operador activó explícitamente** para hoy (`entregas_habilitadas.nro_pedidos`) — a mano o preseleccionado desde `pedidos_encontrados`. Es la fuente de verdad de "qué se entrega hoy". | Nunca — es justamente el campo que hay que usar. |

**Regla dura:** para mostrarle algo al operador o al cadete sobre "cuántos pedidos son", usá `pedidos_activos` con fallback a `nro_pedidos` (`pedidos_activos.length > 0 ? pedidos_activos : nro_pedidos`), nunca `total_pedidos`/`pedidos_encontrados` solos. Esos dos últimos reflejan únicamente lo que el archivo subido trajo automáticamente, y en este flujo de trabajo el operador **nunca** usa los pedidos del archivo tal cual — siempre los activa a mano cada día. Este patrón ya está aplicado en `operador.html` (`renderEntregas`) e `historial.html`; si agregás una vista nueva que muestre pedidos de una entrega, replicalo ahí.

## Dónde vive esto

- `server/app.py`, función `cruces_entregas_list` (`GET /api/cruces/<id>/entregas`): arma `punto_retiro`, `nodo_asignado`→`nombre_display`, y los tres conteos de pedidos por entrega.
- `operador.html`, función `renderEntregas`: tiles de Operador (confirmadas / activas / sin pedidos).
- `cadete.html`, sección de entregas: mismo dato, vista del cadete.
- `historial.html`: mismo dato, de solo lectura.
