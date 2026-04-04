=====================================================
 CÓMO SUBIR LA APP A STREAMLIT CLOUD (GRATIS)
 Para acceder desde cualquier PC o celular
=====================================================

PASO 1 — Crear cuenta en GitHub (si no tenés)
  → Ir a https://github.com
  → Registrarse gratis con tu email

PASO 2 — Subir el proyecto a GitHub
  1. En GitHub, hacer clic en "New repository"
  2. Nombre: cruce-stock-farmacias
  3. Privado (Private) ← importante para que no sea público
  4. Crear repositorio
  5. Subir todos los archivos de esta carpeta "cruce_stock"

  Si no sabés usar Git, la forma más fácil es:
  → En el repositorio creado, hacer clic en "uploading an existing file"
  → Arrastrar todos los archivos de la carpeta cruce_stock

PASO 3 — Crear cuenta en Streamlit Cloud
  → Ir a https://streamlit.io/cloud
  → Registrarse con la misma cuenta de GitHub

PASO 4 — Deployar la app
  1. Clic en "New app"
  2. Elegir tu repositorio "cruce-stock-farmacias"
  3. En "Main file path" escribir: streamlit_app.py
  4. Clic en "Deploy"
  5. Esperar ~2 minutos

PASO 5 — Usar desde cualquier lugar
  → Streamlit te da una URL del estilo:
     https://tu-usuario-cruce-stock-farmacias.streamlit.app
  → Guardá ese link en favoritos
  → Desde el celular: abrir el navegador y entrar al link
  → Subir los dos archivos → hacer clic → descargar Excel

=====================================================
 PREGUNTAS FRECUENTES
=====================================================

¿Es seguro? ¿Pueden ver mis datos otras personas?
  → Si el repositorio es Privado en GitHub, solo vos podés
    acceder al código. Los archivos que subís para procesar
    NO se guardan en ningún lado, se procesan y desaparecen.

¿Necesito pagar?
  → No. El plan gratuito de Streamlit Cloud es suficiente
    para el uso de un equipo chico.

¿Qué pasa si actualizo el código?
  → Solo subís el archivo modificado a GitHub y
    Streamlit actualiza la app automáticamente.

=====================================================
 PARA CORRER EN TU COMPUTADORA (sin internet)
=====================================================

1. Abrir la terminal (cmd) en la carpeta cruce_stock
2. Correr: pip install -r requirements.txt
3. Correr: streamlit run streamlit_app.py
4. Se abre automáticamente en el navegador

=====================================================
