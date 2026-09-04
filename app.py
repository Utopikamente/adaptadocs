"""Ventana de escritorio para adaptar documentos de Word.

Ejecutar con:  python app.py
"""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.perfiles import PERFILES, PERFIL_POR_DEFECTO, opciones_de_perfil
from core.transformador import OpcionesAdaptacion, adaptar_documento

# Arrastrar y soltar es opcional: si tkinterdnd2 no está instalado, se usa
# solo el botón "Examinar".
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _Raiz = TkinterDnD.Tk
    _HAY_DND = True
except Exception:  # pragma: no cover - depende del entorno
    _Raiz = tk.Tk
    _HAY_DND = False


FUENTES = ["Verdana", "Arial", "Tahoma", "Calibri", "Century Gothic",
           "Comic Sans MS", "Lexend", "OpenDyslexic"]
INTERLINEADOS = ["1.0", "1.15", "1.5", "2.0"]
COLORES = ["Amarillo", "Verde", "Turquesa", "Rosa", "Gris"]
COLOR_A_CLAVE = {
    "Amarillo": "AMARILLO", "Verde": "VERDE", "Turquesa": "TURQUESA",
    "Rosa": "ROSA", "Gris": "GRIS",
}
CLAVE_A_COLOR = {v: k for k, v in COLOR_A_CLAVE.items()}


def _ruta_salida_por_defecto(entrada: str) -> str:
    carpeta, nombre = os.path.split(entrada)
    raiz, _ = os.path.splitext(nombre)
    return os.path.join(carpeta, f"{raiz} (adaptado).docx")


class Aplicacion(_Raiz):
    def __init__(self) -> None:
        super().__init__()
        self.title("Adaptador de documentos Word")
        self.minsize(640, 640)
        self.columnconfigure(0, weight=1)

        self._cola: queue.Queue[tuple[str, object]] = queue.Queue()
        self._procesando = False

        self._construir_variables()
        self._construir_interfaz()
        self._cargar_perfil()
        self.after(100, self._vaciar_cola)

    # ------------------------------------------------------------------ #
    # Construcción de la interfaz
    # ------------------------------------------------------------------ #

    def _construir_variables(self) -> None:
        self.var_entrada = tk.StringVar()
        self.var_salida = tk.StringVar()
        self.var_perfil = tk.StringVar(value=PERFIL_POR_DEFECTO)
        self.var_fuente = tk.StringVar()
        self.var_tamano = tk.DoubleVar()
        self.var_interlineado = tk.StringVar()
        self.var_espacio = tk.DoubleVar()
        self.var_margen = tk.DoubleVar()
        self.var_izquierda = tk.BooleanVar()
        self.var_margenes_on = tk.BooleanVar()
        self.var_una_columna = tk.BooleanVar()
        self.var_contraste = tk.BooleanVar()
        self.var_negrita_titulos = tk.BooleanVar()
        self.var_vinetas = tk.BooleanVar()
        self.var_palabras = tk.StringVar()
        self.var_color = tk.StringVar(value="Amarillo")

    def _construir_interfaz(self) -> None:
        pad = {"padx": 8, "pady": 4}
        fila = 0

        # --- Archivo de entrada -------------------------------------- #
        marco_e = ttk.LabelFrame(self, text="1. Documento original (.docx)")
        marco_e.grid(row=fila, column=0, sticky="ew", **pad)
        marco_e.columnconfigure(0, weight=1)
        ent = ttk.Entry(marco_e, textvariable=self.var_entrada)
        ent.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ttk.Button(marco_e, text="Examinar…", command=self._elegir_entrada).grid(
            row=0, column=1, padx=8, pady=8)
        if _HAY_DND:
            ttk.Label(marco_e, text="También puedes arrastrar el archivo aquí.",
                      foreground="#666").grid(row=1, column=0, columnspan=2,
                                              sticky="w", padx=8, pady=(0, 6))
            for w in (marco_e, ent):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._soltar_archivo)
        fila += 1

        # --- Perfil ------------------------------------------------- #
        marco_p = ttk.LabelFrame(self, text="2. Perfil de adaptación")
        marco_p.grid(row=fila, column=0, sticky="ew", **pad)
        marco_p.columnconfigure(0, weight=1)
        combo_p = ttk.Combobox(marco_p, textvariable=self.var_perfil,
                               values=list(PERFILES), state="readonly")
        combo_p.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        combo_p.bind("<<ComboboxSelected>>", lambda _e: self._cargar_perfil())
        fila += 1

        # --- Opciones de formato ---------------------------------- #
        marco_o = ttk.LabelFrame(self, text="3. Opciones de formato")
        marco_o.grid(row=fila, column=0, sticky="ew", **pad)
        marco_o.columnconfigure(1, weight=1)

        ttk.Label(marco_o, text="Fuente").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Combobox(marco_o, textvariable=self.var_fuente, values=FUENTES).grid(
            row=0, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(marco_o, text="Tamaño (pt)").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Spinbox(marco_o, from_=8, to=48, increment=1, textvariable=self.var_tamano).grid(
            row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(marco_o, text="Interlineado").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Combobox(marco_o, textvariable=self.var_interlineado, values=INTERLINEADOS,
                     state="readonly", width=8).grid(row=2, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(marco_o, text="Espacio tras párrafo (pt)").grid(
            row=3, column=0, sticky="w", padx=8, pady=4)
        ttk.Spinbox(marco_o, from_=0, to=48, increment=2, textvariable=self.var_espacio).grid(
            row=3, column=1, sticky="w", padx=8, pady=4)

        marco_m = ttk.Frame(marco_o)
        marco_m.grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(marco_m, text="Márgenes amplios de", variable=self.var_margenes_on).pack(
            side="left")
        ttk.Spinbox(marco_m, from_=1.0, to=6.0, increment=0.5, width=5,
                    textvariable=self.var_margen).pack(side="left", padx=6)
        ttk.Label(marco_m, text="cm").pack(side="left")

        ttk.Checkbutton(marco_o, text="Alinear a la izquierda (quitar justificado)",
                        variable=self.var_izquierda).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(marco_o, text="Forzar una sola columna",
                        variable=self.var_una_columna).grid(
            row=6, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(marco_o, text="Texto en negro (alto contraste)",
                        variable=self.var_contraste).grid(
            row=7, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(marco_o, text="Títulos en negrita",
                        variable=self.var_negrita_titulos).grid(
            row=8, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(marco_o, text="Convertir viñetas en lista numerada (pasos)",
                        variable=self.var_vinetas).grid(
            row=9, column=0, columnspan=2, sticky="w", padx=8, pady=2)

        marco_r = ttk.Frame(marco_o)
        marco_r.grid(row=10, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 4))
        marco_r.columnconfigure(1, weight=1)
        ttk.Label(marco_r, text="Resaltar palabras (separadas por comas)").grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Entry(marco_r, textvariable=self.var_palabras).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Combobox(marco_r, textvariable=self.var_color, values=COLORES,
                     state="readonly", width=10).grid(row=1, column=2, padx=(6, 0), pady=4)
        fila += 1

        # --- Salida ---------------------------------------------- #
        marco_s = ttk.LabelFrame(self, text="4. Guardar documento adaptado como")
        marco_s.grid(row=fila, column=0, sticky="ew", **pad)
        marco_s.columnconfigure(0, weight=1)
        ttk.Entry(marco_s, textvariable=self.var_salida).grid(
            row=0, column=0, sticky="ew", padx=8, pady=8)
        ttk.Button(marco_s, text="Examinar…", command=self._elegir_salida).grid(
            row=0, column=1, padx=8, pady=8)
        fila += 1

        # --- Acción y registro -------------------------------- #
        self.boton = ttk.Button(self, text="Adaptar documento", command=self._lanzar)
        self.boton.grid(row=fila, column=0, sticky="ew", padx=8, pady=(8, 4))
        fila += 1

        self.registro = tk.Text(self, height=7, state="disabled", wrap="word")
        self.registro.grid(row=fila, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.rowconfigure(fila, weight=1)

    # ------------------------------------------------------------------ #
    # Perfil <-> controles
    # ------------------------------------------------------------------ #

    def _cargar_perfil(self) -> None:
        o = opciones_de_perfil(self.var_perfil.get())
        self.var_fuente.set(o.fuente or "")
        self.var_tamano.set(o.tamano_pt or 12)
        self.var_interlineado.set(str(o.interlineado or 1.0))
        self.var_espacio.set(o.espacio_despues_pt or 0)
        self.var_izquierda.set(o.alinear_izquierda)
        self.var_margenes_on.set(o.margenes_cm is not None)
        self.var_margen.set(o.margenes_cm or 2.5)
        self.var_una_columna.set(o.una_columna)
        self.var_contraste.set(o.alto_contraste)
        self.var_negrita_titulos.set(o.negrita_titulos)
        self.var_vinetas.set(o.convertir_vinetas_en_pasos)
        self.var_color.set(CLAVE_A_COLOR.get(o.color_resaltado, "Amarillo"))

    def _recoger_opciones(self) -> OpcionesAdaptacion:
        palabras = [p.strip() for p in self.var_palabras.get().split(",") if p.strip()]
        return OpcionesAdaptacion(
            fuente=self.var_fuente.get().strip() or None,
            tamano_pt=float(self.var_tamano.get()) or None,
            interlineado=float(self.var_interlineado.get()),
            espacio_despues_pt=float(self.var_espacio.get()),
            alinear_izquierda=self.var_izquierda.get(),
            margenes_cm=float(self.var_margen.get()) if self.var_margenes_on.get() else None,
            una_columna=self.var_una_columna.get(),
            alto_contraste=self.var_contraste.get(),
            negrita_titulos=self.var_negrita_titulos.get(),
            convertir_vinetas_en_pasos=self.var_vinetas.get(),
            resaltar_palabras=palabras,
            color_resaltado=COLOR_A_CLAVE.get(self.var_color.get(), "AMARILLO"),
        )

    # ------------------------------------------------------------------ #
    # Selección de archivos
    # ------------------------------------------------------------------ #

    def _fijar_entrada(self, ruta: str) -> None:
        self.var_entrada.set(ruta)
        if ruta and not self.var_salida.get():
            self.var_salida.set(_ruta_salida_por_defecto(ruta))

    def _elegir_entrada(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Elige el documento original",
            filetypes=[("Documentos de Word", "*.docx"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            self._fijar_entrada(ruta)

    def _elegir_salida(self) -> None:
        inicial = self.var_salida.get() or _ruta_salida_por_defecto(self.var_entrada.get() or "documento.docx")
        ruta = filedialog.asksaveasfilename(
            title="Guardar como",
            defaultextension=".docx",
            initialfile=os.path.basename(inicial),
            initialdir=os.path.dirname(inicial) or None,
            filetypes=[("Documentos de Word", "*.docx")],
        )
        if ruta:
            self.var_salida.set(ruta)

    def _soltar_archivo(self, evento) -> None:
        datos = evento.data.strip()
        if datos.startswith("{") and datos.endswith("}"):
            datos = datos[1:-1]
        ruta = datos.split("} {")[0].strip()
        if ruta:
            self._fijar_entrada(ruta)

    # ------------------------------------------------------------------ #
    # Procesamiento
    # ------------------------------------------------------------------ #

    def _log(self, mensaje: str) -> None:
        self.registro.configure(state="normal")
        self.registro.insert("end", mensaje + "\n")
        self.registro.see("end")
        self.registro.configure(state="disabled")

    def _lanzar(self) -> None:
        if self._procesando:
            return
        entrada = self.var_entrada.get().strip()
        salida = self.var_salida.get().strip() or _ruta_salida_por_defecto(entrada)
        self.var_salida.set(salida)

        if not entrada or not os.path.isfile(entrada):
            messagebox.showerror("Falta el documento", "Elige un archivo .docx de entrada válido.")
            return
        if os.path.abspath(entrada) == os.path.abspath(salida):
            messagebox.showerror("Rutas iguales", "El archivo de salida debe ser distinto del original.")
            return
        if os.path.exists(salida) and not messagebox.askyesno(
            "El archivo ya existe", f"«{os.path.basename(salida)}» ya existe. ¿Sobrescribirlo?"
        ):
            return

        try:
            opciones = self._recoger_opciones()
        except (tk.TclError, ValueError):
            messagebox.showerror("Valores no válidos", "Revisa los números de tamaño, espaciado y márgenes.")
            return

        self._procesando = True
        self.boton.configure(state="disabled", text="Procesando…")
        self._log("─" * 40)
        threading.Thread(
            target=self._trabajo, args=(entrada, salida, opciones), daemon=True
        ).start()

    def _trabajo(self, entrada: str, salida: str, opciones: OpcionesAdaptacion) -> None:
        try:
            resumen = adaptar_documento(
                entrada, salida, opciones,
                registrar=lambda m: self._cola.put(("log", m)),
            )
            self._cola.put(("ok", (salida, resumen)))
        except Exception as exc:  # noqa: BLE001 - queremos mostrar cualquier fallo
            self._cola.put(("error", str(exc)))

    def _vaciar_cola(self) -> None:
        try:
            while True:
                tipo, carga = self._cola.get_nowait()
                if tipo == "log":
                    self._log(str(carga))
                elif tipo == "ok":
                    salida, resumen = carga
                    self._log(
                        "Listo. "
                        f"{resumen['parrafos']} párrafos, "
                        f"{resumen['resaltados']} palabras resaltadas, "
                        f"{resumen['vinetas_convertidas']} viñetas convertidas."
                    )
                    self._fin()
                    if messagebox.askyesno("Documento adaptado",
                                           "Se ha creado el documento adaptado.\n\n¿Abrir la carpeta?"):
                        self._abrir_carpeta(salida)
                elif tipo == "error":
                    self._log(f"ERROR: {carga}")
                    self._fin()
                    messagebox.showerror("No se pudo adaptar", str(carga))
        except queue.Empty:
            pass
        self.after(100, self._vaciar_cola)

    def _fin(self) -> None:
        self._procesando = False
        self.boton.configure(state="normal", text="Adaptar documento")

    @staticmethod
    def _abrir_carpeta(ruta: str) -> None:
        try:
            os.startfile(os.path.dirname(os.path.abspath(ruta)))  # type: ignore[attr-defined]
        except OSError:
            pass


def main() -> None:
    Aplicacion().mainloop()


if __name__ == "__main__":
    main()
