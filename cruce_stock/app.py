"""
app.py
Interfaz gráfica (GUI) con tkinter.
Pensada para usuarios no técnicos: seleccionan archivos,
hacen clic en "Generar Planilla" y se abre el Excel resultado.

Para empaquetar como .exe:
  pyinstaller --onefile --windowed --name CruceStock app.py
"""

from __future__ import annotations
import os
import pathlib
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


# ── Constantes visuales ──────────────────────────────────────
COLOR_BG       = "#F0F4F8"
COLOR_PRIMARIO = "#2E4057"
COLOR_ACENTO   = "#4CAF50"
COLOR_ERROR    = "#C62828"
COLOR_TEXTO    = "#1A1A2E"
FUENTE_TITULO  = ("Segoe UI", 14, "bold")
FUENTE_LABEL   = ("Segoe UI", 10)
FUENTE_BTN     = ("Segoe UI", 10, "bold")
FUENTE_LOG     = ("Consolas", 9)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cruce de Stock — Ecommerce | Farmacias")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self._centrar_ventana(700, 560)

        self._path_pedidos  = tk.StringVar()
        self._path_stock    = tk.StringVar()
        self._path_salida   = tk.StringVar(value=str(pathlib.Path.home() / "Desktop"))
        self._ejecutando    = False

        self._construir_ui()

    def _centrar_ventana(self, ancho: int, alto: int):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ── Construcción de la UI ────────────────────────────────

    def _construir_ui(self):
        # Título
        tk.Label(
            self, text="Cruce de Stock — Planilla Cadete",
            font=FUENTE_TITULO, bg=COLOR_BG, fg=COLOR_PRIMARIO
        ).pack(pady=(18, 4))

        tk.Label(
            self,
            text="Seleccioná los archivos, elegí la carpeta de salida y generá la planilla.",
            font=FUENTE_LABEL, bg=COLOR_BG, fg=COLOR_TEXTO
        ).pack(pady=(0, 12))

        # Frame central
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(padx=30, fill="x")

        self._fila_archivo(frame, "📋  Archivo de Pedidos (.xlsx / .csv):",
                           self._path_pedidos, self._seleccionar_pedidos, row=0)
        self._fila_archivo(frame, "🏪  Stock de Sucursales (.xlsx / .csv):",
                           self._path_stock, self._seleccionar_stock, row=1)
        self._fila_archivo(frame, "📁  Carpeta de Salida:",
                           self._path_salida, self._seleccionar_salida, row=2, es_carpeta=True)

        # Separador
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=30, pady=14)

        # Botón principal
        self._btn_generar = tk.Button(
            self,
            text="⚡  GENERAR PLANILLA",
            font=FUENTE_BTN,
            bg=COLOR_ACENTO, fg="white",
            activebackground="#388E3C", activeforeground="white",
            relief="flat", padx=20, pady=10,
            cursor="hand2",
            command=self._iniciar_proceso,
        )
        self._btn_generar.pack(pady=(0, 12))

        # Barra de progreso
        self._barra = ttk.Progressbar(self, mode="indeterminate", length=400)
        self._barra.pack(pady=(0, 8))

        # Log de mensajes
        tk.Label(self, text="Registro de actividad:", font=FUENTE_LABEL,
                 bg=COLOR_BG, fg=COLOR_TEXTO).pack(anchor="w", padx=30)

        self._log_box = scrolledtext.ScrolledText(
            self, height=10, font=FUENTE_LOG,
            bg="#1E1E2E", fg="#A8D8A8",
            insertbackground="white", relief="flat",
            state="disabled",
        )
        self._log_box.pack(padx=30, pady=(4, 16), fill="both")

    def _fila_archivo(self, parent, label: str, var: tk.StringVar,
                      comando, row: int, es_carpeta: bool = False):
        tk.Label(parent, text=label, font=FUENTE_LABEL,
                 bg=COLOR_BG, fg=COLOR_TEXTO, anchor="w"
                 ).grid(row=row * 2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        entry = tk.Entry(parent, textvariable=var, font=FUENTE_LABEL,
                         width=52, relief="solid", bd=1)
        entry.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(2, 4), padx=(0, 6))

        btn = tk.Button(
            parent, text="Examinar", font=FUENTE_LABEL,
            bg=COLOR_PRIMARIO, fg="white", relief="flat",
            padx=8, cursor="hand2", command=comando,
        )
        btn.grid(row=row * 2 + 1, column=1, sticky="ew", pady=(2, 4))

        parent.columnconfigure(0, weight=1)

    # ── Selectores de archivo ────────────────────────────────

    def _seleccionar_pedidos(self):
        path = filedialog.askopenfilename(
            title="Seleccioná el archivo de pedidos",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv *.txt"), ("Todos", "*.*")]
        )
        if path:
            self._path_pedidos.set(path)

    def _seleccionar_stock(self):
        path = filedialog.askopenfilename(
            title="Seleccioná el archivo de stock de sucursales",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv *.txt"), ("Todos", "*.*")]
        )
        if path:
            self._path_stock.set(path)

    def _seleccionar_salida(self):
        path = filedialog.askdirectory(title="Seleccioná la carpeta donde guardar el resultado")
        if path:
            self._path_salida.set(path)

    # ── Log visual ───────────────────────────────────────────

    def _log(self, mensaje: str):
        """Agrega una línea al log visible. Thread-safe."""
        def _insertar():
            self._log_box.configure(state="normal")
            self._log_box.insert("end", mensaje + "\n")
            self._log_box.see("end")
            self._log_box.configure(state="disabled")
        self.after(0, _insertar)

    def _limpiar_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # ── Proceso principal ────────────────────────────────────

    def _iniciar_proceso(self):
        if self._ejecutando:
            return

        # Validaciones básicas
        if not self._path_pedidos.get():
            messagebox.showwarning("Falta archivo", "Seleccioná el archivo de pedidos.")
            return
        if not self._path_stock.get():
            messagebox.showwarning("Falta archivo", "Seleccioná el archivo de stock.")
            return
        if not self._path_salida.get():
            messagebox.showwarning("Falta carpeta", "Seleccioná la carpeta de salida.")
            return

        self._ejecutando = True
        self._btn_generar.configure(state="disabled", text="Procesando...")
        self._barra.start(10)
        self._limpiar_log()
        self._log("Iniciando proceso...")

        # Ejecutar en hilo separado para no bloquear la UI
        hilo = threading.Thread(target=self._correr_pipeline, daemon=True)
        hilo.start()

    def _correr_pipeline(self):
        try:
            # Importar aquí para capturar errores de import correctamente
            from main import ejecutar

            resumen = ejecutar(
                path_pedidos=self._path_pedidos.get(),
                path_stock=self._path_stock.get(),
                carpeta_salida=self._path_salida.get(),
                callback_progreso=self._log,
            )
            self.after(0, self._proceso_exitoso, resumen)

        except Exception as e:
            self.after(0, self._proceso_fallido, str(e))

    def _proceso_exitoso(self, resumen: dict):
        self._barra.stop()
        self._btn_generar.configure(state="normal", text="⚡  GENERAR PLANILLA")
        self._ejecutando = False

        self._log(f"\n✅ Archivo generado: {resumen['path_salida']}")
        self._log(f"   Pedidos activos:        {resumen['pedidos_procesados']}")
        self._log(f"   Filas en planilla:      {resumen['filas_planilla']}")
        self._log(f"   Sin cobertura:          {resumen['productos_sin_cobertura']}")

        respuesta = messagebox.askyesno(
            "Proceso finalizado",
            f"Planilla generada exitosamente.\n\n"
            f"📋 Pedidos activos:    {resumen['pedidos_procesados']}\n"
            f"✅ Filas en planilla:  {resumen['filas_planilla']}\n"
            f"⚠️  Sin cobertura:     {resumen['productos_sin_cobertura']}\n\n"
            "¿Querés abrir el archivo ahora?",
        )
        if respuesta:
            self._abrir_archivo(resumen["path_salida"])

    def _proceso_fallido(self, error: str):
        self._barra.stop()
        self._btn_generar.configure(state="normal", text="⚡  GENERAR PLANILLA")
        self._ejecutando = False
        self._log(f"\n❌ ERROR: {error}")
        messagebox.showerror("Error en el proceso", f"Ocurrió un error:\n\n{error}")

    def _abrir_archivo(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showwarning("No se pudo abrir", f"Abrí el archivo manualmente:\n{path}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
