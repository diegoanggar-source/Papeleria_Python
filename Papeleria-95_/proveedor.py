
# proveedores.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

from tema import (
    obtener_colores,
    obtener_tema_actual,
    registrar_observador,
    eliminar_observador,
)

# ============================================================
# CONFIGURACIÓN - PAPELERÍA LUNA
# ============================================================

FUENTE = "Arial"

TIPOS_PROVEEDOR = [
    "Papelería",
    "Tecnología",
    "Limpieza",
    "Mobiliario",
    "Oficina",
    "Otros",
]

VENTANAS_PROVEEDORES = []
TEMA_ACTUAL = obtener_tema_actual()
COLORES = obtener_colores(TEMA_ACTUAL)


def actualizar_constantes(colores):
    """Actualiza la paleta compartida del módulo."""
    global COLORES
    global COLOR_FONDO, COLOR_PANEL
    global COLOR_AZUL, COLOR_AZUL_SECUNDARIO, COLOR_AZUL_HOVER
    global COLOR_NARANJA, COLOR_NARANJA_HOVER
    global COLOR_TEXTO, COLOR_TEXTO_SUAVE, COLOR_BORDE
    global COLOR_ROJO, COLOR_ROJO_HOVER
    global COLOR_ENTRADA, COLOR_SELECCION

    COLORES = colores.copy()

    COLOR_FONDO = COLORES["FONDO"]
    COLOR_PANEL = COLORES["PANEL"]

    COLOR_AZUL = COLORES["AZUL"]
    COLOR_AZUL_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
    COLOR_AZUL_HOVER = COLORES["AZUL_SECUNDARIO"]

    COLOR_NARANJA = COLORES["NARANJA"]
    COLOR_NARANJA_HOVER = COLORES["NARANJA_HOVER"]

    COLOR_TEXTO = COLORES["TEXTO"]
    COLOR_TEXTO_SUAVE = COLORES["TEXTO_SUAVE"]
    COLOR_BORDE = COLORES["BORDE"]

    COLOR_ROJO = COLORES["ROJO"]
    COLOR_ROJO_HOVER = COLORES["ROJO_HOVER"]

    COLOR_ENTRADA = COLORES["ENTRADA"]
    COLOR_SELECCION = COLORES["SELECCION"]


actualizar_constantes(COLORES)


# ============================================================
# CONEXIÓN CON MYSQL
# ============================================================

def conectar_bd():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="Papeleria_Luna",
            connection_timeout=10,
        )
    except Error as error:
        messagebox.showerror(
            "Error de conexión",
            f"No se pudo conectar con la base de datos.\n\n{error}",
        )
        return None


# ============================================================
# CONSULTAR PROVEEDORES
# ============================================================

def consultar_proveedores(filtro="", estado=0):
    conexion = conectar_bd()

    if conexion is None:
        return None

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)

        consulta = """
            SELECT
                id_proveedor,
                identificacion,
                nombre,
                telefono,
                correo,
                direccion,
                tipo_proveedor,
                estado
            FROM Proveedores
            WHERE estado = %s
        """

        parametros = [estado]
        filtro = filtro.strip()

        if filtro:
            consulta += """
                AND (
                    identificacion LIKE %s
                    OR nombre LIKE %s
                )
            """
            parametros.extend([f"%{filtro}%", f"%{filtro}%"])

        consulta += " ORDER BY id_proveedor ASC"

        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()

    except Error as error:
        messagebox.showerror(
            "Error de consulta",
            f"No se pudieron consultar los proveedores.\n\n{error}",
        )
        return None

    finally:
        if cursor is not None:
            cursor.close()

        conexion.close()


# ============================================================
# ESTILOS Y ACTUALIZACIÓN DEL TEMA
# ============================================================

def configurar_estilos(ventana):
    estilo = ttk.Style(ventana)

    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    estilo.configure(
        "Luna.Treeview",
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        fieldbackground=COLOR_ENTRADA,
        bordercolor=COLOR_BORDE,
        rowheight=30,
        font=(FUENTE, 9),
        relief="flat",
    )

    estilo.map(
        "Luna.Treeview",
        background=[("selected", COLOR_SELECCION)],
        foreground=[("selected", COLOR_TEXTO)],
    )

    estilo.configure(
        "Luna.Treeview.Heading",
        background=COLOR_AZUL,
        foreground="white",
        font=(FUENTE, 9, "bold"),
        relief="flat",
        padding=(8, 8),
    )

    estilo.map(
        "Luna.Treeview.Heading",
        background=[("active", COLOR_AZUL_SECUNDARIO)],
        foreground=[("active", "white")],
    )

    estilo.configure(
        "Luna.TCombobox",
        fieldbackground=COLOR_ENTRADA,
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        arrowcolor=COLOR_TEXTO,
        bordercolor=COLOR_BORDE,
        padding=5,
    )

    estilo.map(
        "Luna.TCombobox",
        fieldbackground=[
            ("readonly", COLOR_ENTRADA),
            ("disabled", COLOR_FONDO),
        ],
        foreground=[
            ("readonly", COLOR_TEXTO),
            ("disabled", COLOR_TEXTO_SUAVE),
        ],
        selectbackground=[("readonly", COLOR_SELECCION)],
        selectforeground=[("readonly", COLOR_TEXTO)],
    )

    for nombre in (
        "Luna.Vertical.TScrollbar",
        "Luna.Horizontal.TScrollbar",
    ):
        estilo.configure(
            nombre,
            background=COLOR_BORDE,
            troughcolor=COLOR_FONDO,
            bordercolor=COLOR_FONDO,
            arrowcolor=COLOR_TEXTO,
            relief="flat",
        )


def registrar_ventana(ventana):
    if ventana not in VENTANAS_PROVEEDORES:
        VENTANAS_PROVEEDORES.append(ventana)

    def al_cerrar(event=None):
        if ventana in VENTANAS_PROVEEDORES:
            VENTANAS_PROVEEDORES.remove(ventana)

    ventana.bind("<Destroy>", al_cerrar, add="+")


def recolorear_widget(widget, anteriores):
    """Recolorea los widgets existentes al cambiar de tema."""
    try:
        if not widget.winfo_exists():
            return
    except tk.TclError:
        return

    equivalencias_fondo = {
        anteriores["FONDO"]: COLOR_FONDO,
        anteriores["PANEL"]: COLOR_PANEL,
        anteriores["AZUL"]: COLOR_AZUL,
        anteriores["AZUL_SECUNDARIO"]: COLOR_AZUL_SECUNDARIO,
        anteriores["NARANJA"]: COLOR_NARANJA,
        anteriores["ROJO"]: COLOR_ROJO,
        "#f8fafc": COLOR_ENTRADA,
        "#e2e8f0": COLOR_ENTRADA,
    }

    equivalencias_texto = {
        anteriores["TEXTO"]: COLOR_TEXTO,
        anteriores["TEXTO_SUAVE"]: COLOR_TEXTO_SUAVE,
        "#cbd5e1": COLOR_TEXTO_SUAVE,
    }

    try:
        opciones = widget.configure()

        if "background" in opciones:
            fondo = widget.cget("background")
            if fondo in equivalencias_fondo:
                widget.configure(
                    background=equivalencias_fondo[fondo]
                )

        if "foreground" in opciones:
            texto = widget.cget("foreground")
            if texto in equivalencias_texto:
                widget.configure(
                    foreground=equivalencias_texto[texto]
                )

        if "highlightbackground" in opciones:
            actual = widget.cget("highlightbackground")
            if actual in anteriores.values():
                widget.configure(highlightbackground=COLOR_BORDE)

        if "highlightcolor" in opciones:
            actual = widget.cget("highlightcolor")
            if actual in anteriores.values():
                widget.configure(highlightcolor=COLOR_NARANJA)

        if isinstance(widget, (tk.Entry, tk.Text, tk.Spinbox)):
            widget.configure(
                bg=COLOR_ENTRADA,
                fg=COLOR_TEXTO,
                insertbackground=COLOR_TEXTO,
                selectbackground=COLOR_SELECCION,
                selectforeground=COLOR_TEXTO,
            )

        if isinstance(widget, tk.Button):
            fondo = widget.cget("background")

            if fondo == COLOR_NARANJA:
                widget.configure(activebackground=COLOR_NARANJA_HOVER)
            elif fondo == COLOR_ROJO:
                widget.configure(activebackground=COLOR_ROJO_HOVER)
            elif fondo in (COLOR_AZUL, COLOR_AZUL_SECUNDARIO):
                widget.configure(activebackground=COLOR_AZUL_SECUNDARIO)

    except (tk.TclError, KeyError):
        pass

    try:
        for hijo in widget.winfo_children():
            recolorear_widget(hijo, anteriores)
    except tk.TclError:
        pass


def aplicar_tema_proveedores(nuevos_colores):
    global TEMA_ACTUAL

    anteriores = COLORES.copy()
    actualizar_constantes(nuevos_colores)
    TEMA_ACTUAL = obtener_tema_actual()

    for ventana in VENTANAS_PROVEEDORES[:]:
        try:
            if ventana.winfo_exists():
                ventana.configure(bg=COLOR_FONDO)
                configurar_estilos(ventana)
                recolorear_widget(ventana, anteriores)
        except tk.TclError:
            pass


def sincronizar_tema():
    """Obtiene la paleta vigente antes de abrir una ventana."""
    global TEMA_ACTUAL

    TEMA_ACTUAL = obtener_tema_actual()
    actualizar_constantes(obtener_colores(TEMA_ACTUAL))


registrar_observador(aplicar_tema_proveedores)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def centrar_ventana(ventana, ancho, alto):
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() - ancho) // 2
    y = (ventana.winfo_screenheight() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


def crear_boton(
    padre,
    texto,
    comando,
    color=None,
    hover=None,
    ancho=16,
    fg="white",
):
    color = color or COLOR_AZUL
    hover = hover or COLOR_AZUL_HOVER

    boton = tk.Button(
        padre,
        text=texto,
        command=comando,
        width=ancho,
        height=2,
        font=(FUENTE, 10, "bold"),
        bg=color,
        fg=fg,
        activebackground=hover,
        activeforeground=fg,
        relief="flat",
        bd=0,
        cursor="hand2",
    )

    boton.bind("<Enter>", lambda evento: boton.config(bg=hover))
    boton.bind("<Leave>", lambda evento: boton.config(bg=color))

    return boton


def crear_etiqueta(
    padre,
    texto,
    fila,
    columna,
    columna_span=1,
):
    tk.Label(
        padre,
        text=texto,
        font=(FUENTE, 9, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
    ).grid(
        row=fila,
        column=columna,
        columnspan=columna_span,
        sticky="w",
        padx=10,
        pady=(2, 0),
    )


def crear_campo(
    padre,
    texto,
    fila,
    columna,
    columna_span=1,
):
    crear_etiqueta(padre, texto, fila, columna, columna_span)

    entrada = tk.Entry(
        padre,
        font=(FUENTE, 9),
        bg=COLOR_ENTRADA,
        fg=COLOR_TEXTO,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=COLOR_BORDE,
        highlightcolor=COLOR_NARANJA,
        insertbackground=COLOR_TEXTO,
        selectbackground=COLOR_SELECCION,
        selectforeground=COLOR_TEXTO,
    )

    entrada.grid(
        row=fila + 1,
        column=columna,
        columnspan=columna_span,
        sticky="ew",
        padx=10,
        pady=(0, 1),
        ipady=3,
    )

    return entrada


def validar_correo(correo):
    if not correo:
        return True

    partes = correo.split("@")

    return (
        len(partes) == 2
        and bool(partes[0])
        and "." in partes[1]
        and not partes[1].startswith(".")
        and not partes[1].endswith(".")
    )


def ejecutar_actualizacion(
    consulta,
    parametros,
    titulo,
    mensaje,
    padre,
):
    conexion = conectar_bd()

    if conexion is None:
        return False

    cursor = None

    try:
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros)
        conexion.commit()

        messagebox.showinfo(titulo, mensaje, parent=padre)
        return True

    except Error as error:
        conexion.rollback()
        messagebox.showerror(
            "Error de base de datos",
            f"No se pudo completar la operación.\n\n{error}",
            parent=padre,
        )
        return False

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


# ============================================================
# ENCABEZADO COMPARTIDO
# ============================================================

def crear_encabezado(ventana, titulo, subtitulo, alto=95):
    encabezado = tk.Frame(
        ventana,
        bg=COLOR_AZUL,
        height=alto,
    )
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA / PROVEEDORES",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_AZUL,
        fg=COLOR_NARANJA,
    ).pack(anchor="w", padx=25, pady=(10, 0))

    tk.Label(
        encabezado,
        text=titulo,
        font=(FUENTE, 18, "bold"),
        bg=COLOR_AZUL,
        fg="white",
    ).pack(anchor="w", padx=25, pady=(3, 4))

    tk.Label(
        encabezado,
        text=subtitulo,
        font=(FUENTE, 10),
        bg=COLOR_AZUL,
        fg="#cbd5e1",
    ).pack(anchor="w", padx=25)

    tk.Frame(
        ventana,
        bg=COLOR_NARANJA,
        height=4,
    ).pack(fill="x")

    return encabezado


# ============================================================
# VENTANA DE REGISTRO
# ============================================================

def abrir_registro(ventana_principal, al_guardar=None):
    sincronizar_tema()

    ventana = tk.Toplevel(ventana_principal)
    ventana.title("Registrar proveedor")
    ventana.configure(bg=COLOR_FONDO)
    ventana.minsize(900, 500)
    ventana.transient(ventana_principal)
    centrar_ventana(ventana, 1050, 600)

    registrar_ventana(ventana)
    configurar_estilos(ventana)

    crear_encabezado(
        ventana,
        "REGISTRAR PROVEEDOR",
        "Introduce los datos del nuevo proveedor",
    )

    panel = tk.Frame(ventana, bg=COLOR_PANEL)
    panel.pack(fill="both", expand=True, padx=22, pady=20)
    panel.columnconfigure(0, weight=1)
    panel.columnconfigure(1, weight=1)

    tk.Label(
        panel,
        text="INFORMACIÓN GENERAL",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
    ).grid(row=0, column=0, columnspan=2, sticky="w",
           padx=10, pady=(10, 2))

    identificacion = crear_campo(panel, "Identificación", 1, 0, 2)
    nombre = crear_campo(panel, "Nombre del proveedor", 3, 0, 2)
    telefono = crear_campo(panel, "Teléfono", 5, 0)
    correo = crear_campo(panel, "Correo electrónico", 5, 1)
    direccion = crear_campo(panel, "Dirección", 7, 0, 2)

    crear_etiqueta(panel, "Tipo de proveedor", 9, 0, 2)

    tipo_proveedor = ttk.Combobox(
        panel,
        font=(FUENTE, 10),
        state="readonly",
        values=TIPOS_PROVEEDOR,
        style="Luna.TCombobox",
    )
    tipo_proveedor.grid(
        row=10, column=0, columnspan=2,
        sticky="ew", padx=10, pady=(0, 5), ipady=4,
    )

    tk.Label(
        panel,
        text="El ID será asignado automáticamente.",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
    ).grid(row=11, column=0, columnspan=2,
           sticky="w", padx=10, pady=8)

    def guardar_proveedor():
        datos_identificacion = identificacion.get().strip()
        datos_nombre = nombre.get().strip()
        datos_telefono = telefono.get().strip()
        datos_correo = correo.get().strip()
        datos_direccion = direccion.get().strip()
        datos_tipo = tipo_proveedor.get().strip()

        if not datos_nombre:
            messagebox.showwarning(
                "Dato obligatorio",
                "Debes introducir el nombre del proveedor.",
                parent=ventana,
            )
            nombre.focus_set()
            return

        if not validar_correo(datos_correo):
            messagebox.showwarning(
                "Correo inválido",
                "Introduce un correo electrónico válido.",
                parent=ventana,
            )
            correo.focus_set()
            return

        correcto = ejecutar_actualizacion(
            """
            INSERT INTO Proveedores (
                identificacion, nombre, telefono, correo,
                direccion, tipo_proveedor, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, 0)
            """,
            (
                datos_identificacion or None,
                datos_nombre,
                datos_telefono or None,
                datos_correo or None,
                datos_direccion or None,
                datos_tipo or None,
            ),
            "Registro exitoso",
            "El proveedor se registró correctamente.",
            ventana,
        )

        if correcto:
            ventana.destroy()
            if al_guardar is not None:
                al_guardar()

    botones = tk.Frame(panel, bg=COLOR_PANEL)
    botones.grid(row=12, column=0, columnspan=2, pady=15)

    crear_boton(
        botones, "Guardar proveedor", guardar_proveedor,
        COLOR_AZUL, COLOR_AZUL_SECUNDARIO, 19,
    ).pack(side="left", padx=5)

    crear_boton(
        botones, "Cancelar", ventana.destroy,
        COLOR_NARANJA, COLOR_NARANJA_HOVER, 12,
    ).pack(side="left", padx=5)

    ventana.grab_set()
    return ventana


# ============================================================
# VENTANA DE MODIFICACIÓN
# ============================================================

def abrir_modificacion(ventana_principal, datos=None, al_guardar=None):
    sincronizar_tema()

    if not datos:
        messagebox.showwarning(
            "Seleccionar proveedor",
            "No se recibieron los datos del proveedor.",
            parent=ventana_principal,
        )
        return

    ventana = tk.Toplevel(ventana_principal)
    ventana.title("Modificar proveedor")
    ventana.configure(bg=COLOR_FONDO)
    ventana.minsize(500, 620)
    ventana.transient(ventana_principal)
    centrar_ventana(ventana, 580, 690)

    registrar_ventana(ventana)
    configurar_estilos(ventana)

    crear_encabezado(
        ventana,
        "MODIFICAR PROVEEDOR",
        "Edita la información del proveedor seleccionado",
    )

    panel = tk.Frame(ventana, bg=COLOR_PANEL)
    panel.pack(fill="both", expand=True, padx=22, pady=20)
    panel.columnconfigure(0, weight=1)
    panel.columnconfigure(1, weight=1)

    tk.Label(
        panel,
        text="DATOS DEL PROVEEDOR",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
    ).grid(row=0, column=0, columnspan=2, sticky="w",
           padx=10, pady=(10, 2))

    crear_etiqueta(panel, "ID del proveedor", 1, 0, 2)

    id_proveedor = tk.Entry(
        panel,
        font=(FUENTE, 9),
        bg=COLOR_ENTRADA,
        fg=COLOR_TEXTO_SUAVE,
        relief="solid",
        bd=1,
        state="readonly",
    )
    id_proveedor.grid(row=2, column=0, columnspan=2,
                      sticky="ew", padx=10, pady=(0, 1), ipady=3)

    identificacion = crear_campo(panel, "Identificación", 3, 0, 2)
    nombre = crear_campo(panel, "Nombre del proveedor", 5, 0, 2)
    telefono = crear_campo(panel, "Teléfono", 7, 0)
    correo = crear_campo(panel, "Correo electrónico", 7, 1)
    direccion = crear_campo(panel, "Dirección", 9, 0, 2)

    crear_etiqueta(panel, "Tipo de proveedor", 11, 0, 2)

    tipo_proveedor = ttk.Combobox(
        panel,
        font=(FUENTE, 10),
        state="readonly",
        values=TIPOS_PROVEEDOR,
        style="Luna.TCombobox",
    )
    tipo_proveedor.grid(row=12, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=(0, 5), ipady=4)

    id_proveedor.config(state="normal")
    id_proveedor.insert(0, str(datos[0]))
    id_proveedor.config(state="readonly")

    for campo, valor in (
        (identificacion, datos[1]),
        (nombre, datos[2]),
        (telefono, datos[3]),
        (correo, datos[4]),
        (direccion, datos[5]),
    ):
        campo.insert(0, valor if valor is not None else "")

    tipo_actual = datos[6] or ""
    tipos_disponibles = list(TIPOS_PROVEEDOR)

    if tipo_actual and tipo_actual not in tipos_disponibles:
        tipos_disponibles.append(tipo_actual)

    tipo_proveedor["values"] = tipos_disponibles
    tipo_proveedor.set(tipo_actual)

    def guardar_cambios():
        datos_identificacion = identificacion.get().strip()
        datos_nombre = nombre.get().strip()
        datos_telefono = telefono.get().strip()
        datos_correo = correo.get().strip()
        datos_direccion = direccion.get().strip()
        datos_tipo = tipo_proveedor.get().strip()

        if not datos_nombre:
            messagebox.showwarning(
                "Dato obligatorio",
                "Debes introducir el nombre del proveedor.",
                parent=ventana,
            )
            nombre.focus_set()
            return

        if not validar_correo(datos_correo):
            messagebox.showwarning(
                "Correo inválido",
                "Introduce un correo electrónico válido.",
                parent=ventana,
            )
            correo.focus_set()
            return

        correcto = ejecutar_actualizacion(
            """
            UPDATE Proveedores
            SET identificacion = %s,
                nombre = %s,
                telefono = %s,
                correo = %s,
                direccion = %s,
                tipo_proveedor = %s
            WHERE id_proveedor = %s
              AND estado = 0
            """,
            (
                datos_identificacion or None,
                datos_nombre,
                datos_telefono or None,
                datos_correo or None,
                datos_direccion or None,
                datos_tipo or None,
                datos[0],
            ),
            "Modificación exitosa",
            "Los datos del proveedor se actualizaron correctamente.",
            ventana,
        )

        if correcto:
            ventana.destroy()
            if al_guardar is not None:
                al_guardar()

    botones = tk.Frame(panel, bg=COLOR_PANEL)
    botones.grid(row=13, column=0, columnspan=2, pady=15)

    crear_boton(
        botones, "Guardar cambios", guardar_cambios,
        COLOR_AZUL, COLOR_AZUL_SECUNDARIO, 19,
    ).pack(side="left", padx=5)

    crear_boton(
        botones, "Cancelar", ventana.destroy,
        COLOR_NARANJA, COLOR_NARANJA_HOVER, 12,
    ).pack(side="left", padx=5)

    ventana.grab_set()
    ventana.after(200, nombre.focus_set)
    return ventana


# ============================================================
# VENTANA DE PAPELERA
# ============================================================

def abrir_papelera(ventana_principal, al_restaurar=None):
    sincronizar_tema()

    ventana = tk.Toplevel(ventana_principal)
    ventana.title("Papelera de proveedores")
    ventana.configure(bg=COLOR_FONDO)
    ventana.minsize(850, 450)
    ventana.transient(ventana_principal)
    centrar_ventana(ventana, 1050, 570)

    registrar_ventana(ventana)
    configurar_estilos(ventana)

    crear_encabezado(
        ventana,
        "PAPELERA DE PROVEEDORES",
        "Los registros pueden restaurarse al directorio activo.",
        alto=90,
    )

    panel = tk.Frame(ventana, bg=COLOR_PANEL)

    tk.Label(
        panel,
        text="Busca por nombre o identificación",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
    ).pack(anchor="w", padx=10, pady=(10, 5))

    busqueda = tk.Frame(panel, bg=COLOR_PANEL)
    busqueda.pack(fill="x", padx=10, pady=(0, 10))

    entrada_busqueda = tk.Entry(
        busqueda,
        font=(FUENTE, 10),
        relief="solid",
        bd=1,
        bg=COLOR_ENTRADA,
        fg=COLOR_TEXTO,
        insertbackground=COLOR_TEXTO,
        highlightthickness=1,
        highlightbackground=COLOR_BORDE,
        highlightcolor=COLOR_NARANJA,
    )
    entrada_busqueda.pack(side="left", fill="x", expand=True,
                          ipady=7, padx=(0, 8))

    columnas = (
        "id_proveedor", "identificacion", "nombre", "telefono",
        "correo", "direccion", "tipo_proveedor",
    )

    contenedor_tabla = tk.Frame(panel, bg=COLOR_PANEL)
    contenedor_tabla.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    contenedor_tabla.rowconfigure(0, weight=1)
    contenedor_tabla.columnconfigure(0, weight=1)

    tabla = ttk.Treeview(
        contenedor_tabla,
        columns=columnas,
        show="headings",
        selectmode="browse",
        style="Luna.Treeview",
    )

    encabezados = {
        "id_proveedor": ("ID", 50),
        "identificacion": ("Identificación", 120),
        "nombre": ("Nombre", 140),
        "telefono": ("Teléfono", 100),
        "correo": ("Correo", 160),
        "direccion": ("Dirección", 150),
        "tipo_proveedor": ("Tipo", 120),
    }

    for columna in columnas:
        titulo, ancho = encabezados[columna]
        tabla.heading(columna, text=titulo, anchor="center")
        tabla.column(columna, width=ancho, minwidth=60, anchor="center")

    barra_vertical = ttk.Scrollbar(
        contenedor_tabla,
        orient="vertical",
        command=tabla.yview,
        style="Luna.Vertical.TScrollbar",
    )
    barra_horizontal = ttk.Scrollbar(
        contenedor_tabla,
        orient="horizontal",
        command=tabla.xview,
        style="Luna.Horizontal.TScrollbar",
    )

    tabla.configure(
        yscrollcommand=barra_vertical.set,
        xscrollcommand=barra_horizontal.set,
    )

    tabla.grid(row=0, column=0, sticky="nsew")
    barra_vertical.grid(row=0, column=1, sticky="ns")
    barra_horizontal.grid(row=1, column=0, sticky="ew")

    def cargar_papelera(filtro=""):
        tabla.delete(*tabla.get_children())

        proveedores = consultar_proveedores(filtro=filtro, estado=1)
        if proveedores is None:
            return

        for proveedor in proveedores:
            valores = (
                proveedor["id_proveedor"],
                proveedor["identificacion"] or "",
                proveedor["nombre"] or "",
                proveedor["telefono"] or "",
                proveedor["correo"] or "",
                proveedor["direccion"] or "",
                proveedor["tipo_proveedor"] or "",
            )
            tabla.insert(
                "", "end",
                iid=str(proveedor["id_proveedor"]),
                values=valores,
            )

    def buscar_en_tiempo_real(event=None):
        cargar_papelera(entrada_busqueda.get().strip())

    def limpiar_busqueda():
        entrada_busqueda.delete(0, tk.END)
        cargar_papelera()
        entrada_busqueda.focus_set()

    entrada_busqueda.bind("<KeyRelease>", buscar_en_tiempo_real)
    entrada_busqueda.bind(
        "<Return>",
        lambda event: cargar_papelera(entrada_busqueda.get().strip()),
    )

    crear_boton(
        busqueda, "Limpiar", limpiar_busqueda,
        COLOR_AZUL, COLOR_AZUL_SECUNDARIO, 10,
    ).pack(side="left")

    def restaurar_proveedor():
        seleccion = tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Seleccionar proveedor",
                "Selecciona un proveedor de la papelera.",
                parent=ventana,
            )
            return

        id_proveedor = seleccion[0]
        valores = tabla.item(id_proveedor, "values")
        nombre_proveedor = valores[2]

        confirmar = messagebox.askyesno(
            "Confirmar restauración",
            f"¿Deseas restaurar al proveedor '{nombre_proveedor}'?",
            parent=ventana,
        )

        if not confirmar:
            return

        correcto = ejecutar_actualizacion(
            """
            UPDATE Proveedores
            SET estado = 0
            WHERE id_proveedor = %s
              AND estado = 1
            """,
            (id_proveedor,),
            "Proveedor restaurado",
            "El proveedor volvió al directorio activo.",
            ventana,
        )

        if correcto:
            cargar_papelera(entrada_busqueda.get().strip())
            if al_restaurar is not None:
                al_restaurar()

    barra_inferior = tk.Frame(ventana, bg=COLOR_AZUL, height=75)
    barra_inferior.pack(side="bottom", fill="x")
    barra_inferior.pack_propagate(False)

    tk.Frame(
        barra_inferior, bg=COLOR_NARANJA, height=4
    ).pack(side="top", fill="x")

    crear_boton(
        barra_inferior, "Recuperar proveedor", restaurar_proveedor,
        COLOR_AZUL_SECUNDARIO, COLOR_AZUL_HOVER, 18,
    ).pack(side="left", padx=15, pady=8)

    crear_boton(
        barra_inferior, "Cerrar", ventana.destroy,
        COLOR_NARANJA, COLOR_NARANJA_HOVER, 12,
    ).pack(side="right", padx=15, pady=8)

    panel.pack(fill="both", expand=True, padx=20, pady=18)

    cargar_papelera()
    return ventana


# ============================================================
# VENTANA PRINCIPAL DE PROVEEDORES
# ============================================================

def abrir_proveedores(raiz=None):
    sincronizar_tema()

    if raiz is None:
        ventana = tk.Tk()
    else:
        ventana = tk.Toplevel(raiz)

    ventana.title("Papelería Luna | Proveedores")
    ventana.configure(bg=COLOR_FONDO)
    ventana.minsize(1000, 650)
    ventana.resizable(True, True)
    centrar_ventana(ventana, 1200, 760)

    registrar_ventana(ventana)
    configurar_estilos(ventana)

    encabezado = tk.Frame(ventana, bg=COLOR_AZUL, height=105)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA / PROVEEDORES",
        font=(FUENTE, 11, "bold"),
        bg=COLOR_AZUL,
        fg=COLOR_NARANJA,
    ).pack(anchor="w", padx=25, pady=(15, 2))

    tk.Label(
        encabezado,
        text="Gestión de proveedores",
        font=(FUENTE, 22, "bold"),
        bg=COLOR_AZUL,
        fg="white",
    ).pack(anchor="w", padx=25)

    tk.Label(
        encabezado,
        text="Directorio - administración de contactos comerciales",
        font=(FUENTE, 10),
        bg=COLOR_AZUL,
        fg="#cbd5e1",
    ).pack(anchor="w", padx=25, pady=(3, 10))

    tk.Frame(ventana, bg=COLOR_NARANJA, height=4).pack(fill="x")

    barra = tk.Frame(ventana, bg=COLOR_FONDO)
    barra.pack(fill="x", padx=22, pady=12)

    tk.Label(
        barra,
        text="Directorio de proveedores",
        font=(FUENTE, 15, "bold"),
        bg=COLOR_FONDO,
        fg=COLOR_TEXTO,
    ).pack(side="left")

    contenido = tk.Frame(ventana, bg=COLOR_FONDO)
    contenido.pack(fill="both", expand=True, padx=22, pady=(0, 12))
    contenido.columnconfigure(0, weight=1, minsize=300)
    contenido.columnconfigure(1, weight=2, minsize=450)
    contenido.rowconfigure(0, weight=1)

    # --------------------------------------------------------
    # PANEL IZQUIERDO: DETALLES
    # --------------------------------------------------------

    panel_datos = tk.Frame(
        contenido,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
    )
    panel_datos.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

    tk.Label(
        panel_datos,
        text="DETALLES DEL PROVEEDOR",
        font=(FUENTE, 12, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
    ).pack(anchor="w", padx=14, pady=(8, 2))

    tk.Label(
        panel_datos,
        text="Selecciona un registro de la tabla",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
    ).pack(anchor="w", padx=14, pady=(0, 6))

    formulario = tk.Frame(panel_datos, bg=COLOR_PANEL)
    formulario.pack(fill="x", padx=6)

    campos = {}
    nombres_campos = [
        ("ID del proveedor", "id"),
        ("Identificación", "identificacion"),
        ("Nombre", "nombre"),
        ("Teléfono", "telefono"),
        ("Correo electrónico", "correo"),
        ("Dirección", "direccion"),
        ("Tipo de proveedor", "tipo_proveedor"),
        ("Estado", "estado"),
    ]

    for fila, (etiqueta, clave) in enumerate(nombres_campos):
        crear_etiqueta(formulario, etiqueta, fila * 2, 0)

        entrada = tk.Entry(
            formulario,
            font=(FUENTE, 9),
            bg=COLOR_ENTRADA,
            fg=COLOR_TEXTO,
            relief="solid",
            bd=1,
            state="readonly",
            readonlybackground=COLOR_ENTRADA,
            insertbackground=COLOR_TEXTO,
        )
        entrada.grid(
            row=fila * 2 + 1, column=0, sticky="ew",
            padx=10, pady=(0, 1), ipady=2,
        )
        campos[clave] = entrada

    formulario.columnconfigure(0, weight=1)

    def mostrar_datos(valores):
        claves = [
            "id", "identificacion", "nombre", "telefono",
            "correo", "direccion", "tipo_proveedor", "estado",
        ]

        for clave, valor in zip(claves, valores):
            campo = campos[clave]
            campo.config(state="normal")
            campo.delete(0, tk.END)
            campo.insert(0, valor if valor is not None else "")
            campo.config(state="readonly")

    def limpiar_detalles():
        for campo in campos.values():
            campo.config(state="normal")
            campo.delete(0, tk.END)
            campo.config(state="readonly")

    botones_datos = tk.Frame(panel_datos, bg=COLOR_PANEL)
    botones_datos.pack(side="bottom", fill="x", padx=10, pady=6)

    def modificar_seleccionado():
        if not campos["id"].get():
            messagebox.showwarning(
                "Seleccionar proveedor",
                "Primero selecciona un proveedor de la tabla.",
                parent=ventana,
            )
            return

        datos = (
            campos["id"].get(),
            campos["identificacion"].get(),
            campos["nombre"].get(),
            campos["telefono"].get(),
            campos["correo"].get(),
            campos["direccion"].get(),
            campos["tipo_proveedor"].get(),
        )

        abrir_modificacion(ventana, datos, actualizar_lista_proveedores)

    def enviar_a_papelera():
        id_proveedor = campos["id"].get()
        nombre_proveedor = campos["nombre"].get()

        if not id_proveedor:
            messagebox.showwarning(
                "Seleccionar proveedor",
                "Selecciona primero un proveedor de la tabla.",
                parent=ventana,
            )
            return

        confirmar = messagebox.askyesno(
            "Enviar a papelera",
            f"¿Deseas enviar a la papelera a '{nombre_proveedor}'?\n\n"
            "Podrás restaurarlo después.",
            parent=ventana,
        )

        if not confirmar:
            return

        correcto = ejecutar_actualizacion(
            """
            UPDATE Proveedores
            SET estado = 1
            WHERE id_proveedor = %s
              AND estado = 0
            """,
            (id_proveedor,),
            "Proveedor enviado a papelera",
            "El proveedor se guardó en la papelera.",
            ventana,
        )

        if correcto:
            limpiar_detalles()
            actualizar_lista_proveedores()

    crear_boton(
        botones_datos, "Modificar", modificar_seleccionado,
        COLOR_NARANJA, COLOR_NARANJA_HOVER, 10,
    ).pack(side="left", padx=2, expand=True, fill="x")

    crear_boton(
        botones_datos, "Eliminar", enviar_a_papelera,
        COLOR_ROJO, COLOR_ROJO_HOVER, 10,
    ).pack(side="left", padx=2, expand=True, fill="x")

    crear_boton(
        botones_datos, "Limpiar", limpiar_detalles,
        COLOR_AZUL, COLOR_AZUL_SECUNDARIO, 9,
    ).pack(side="left", padx=2, expand=True, fill="x")

    # --------------------------------------------------------
    # PANEL DERECHO: TABLA
    # --------------------------------------------------------

    panel_lista = tk.Frame(
        contenido,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
    )
    panel_lista.grid(row=0, column=1, sticky="nsew")

    tk.Label(
        panel_lista,
        text="PROVEEDORES REGISTRADOS",
        font=(FUENTE, 12, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
    ).pack(anchor="w", padx=18, pady=(16, 4))

    tk.Label(
        panel_lista,
        text="Busca por identificación o nombre",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
    ).pack(anchor="w", padx=18, pady=(0, 10))

    busqueda = tk.Frame(panel_lista, bg=COLOR_PANEL)
    busqueda.pack(fill="x", padx=15, pady=(0, 10))

    entrada_busqueda = tk.Entry(
        busqueda,
        font=(FUENTE, 10),
        relief="solid",
        bd=1,
        bg=COLOR_ENTRADA,
        fg=COLOR_TEXTO,
        insertbackground=COLOR_TEXTO,
        highlightthickness=1,
        highlightbackground=COLOR_BORDE,
        highlightcolor=COLOR_NARANJA,
    )
    entrada_busqueda.pack(
        side="left", fill="x", expand=True, ipady=7, padx=(0, 8)
    )

    columnas = (
        "id_proveedor", "identificacion", "nombre", "telefono",
        "correo", "direccion", "tipo_proveedor",
    )

    encabezados_tabla = {
        "id_proveedor": ("ID", 45),
        "identificacion": ("Identificación", 120),
        "nombre": ("Nombre", 120),
        "telefono": ("Teléfono", 105),
        "correo": ("Correo electrónico", 165),
        "direccion": ("Dirección", 140),
        "tipo_proveedor": ("Tipo de proveedor", 130),
    }

    contenedor_tabla = tk.Frame(panel_lista, bg=COLOR_PANEL)
    contenedor_tabla.pack(fill="both", expand=True, padx=15, pady=(0, 8))
    contenedor_tabla.rowconfigure(0, weight=1)
    contenedor_tabla.columnconfigure(0, weight=1)

    tabla = ttk.Treeview(
        contenedor_tabla,
        columns=columnas,
        show="headings",
        selectmode="browse",
        style="Luna.Treeview",
    )

    for columna in columnas:
        texto, ancho = encabezados_tabla[columna]
        tabla.heading(columna, text=texto, anchor="center")
        tabla.column(columna, width=ancho, minwidth=60, anchor="center")

    barra_vertical = ttk.Scrollbar(
        contenedor_tabla,
        orient="vertical",
        command=tabla.yview,
        style="Luna.Vertical.TScrollbar",
    )
    barra_horizontal = ttk.Scrollbar(
        contenedor_tabla,
        orient="horizontal",
        command=tabla.xview,
        style="Luna.Horizontal.TScrollbar",
    )

    tabla.configure(
        yscrollcommand=barra_vertical.set,
        xscrollcommand=barra_horizontal.set,
    )

    tabla.grid(row=0, column=0, sticky="nsew")
    barra_vertical.grid(row=0, column=1, sticky="ns")
    barra_horizontal.grid(row=1, column=0, sticky="ew")

    def cargar_proveedores(filtro=""):
        tabla.delete(*tabla.get_children())
        limpiar_detalles()

        proveedores = consultar_proveedores(filtro=filtro, estado=0)
        if proveedores is None:
            return

        for proveedor in proveedores:
            valores = (
                proveedor["id_proveedor"],
                proveedor["identificacion"] or "",
                proveedor["nombre"] or "",
                proveedor["telefono"] or "",
                proveedor["correo"] or "",
                proveedor["direccion"] or "",
                proveedor["tipo_proveedor"] or "",
            )
            tabla.insert(
                "", "end",
                iid=str(proveedor["id_proveedor"]),
                values=valores,
            )

    def seleccionar_proveedor(event=None):
        seleccion = tabla.selection()
        if not seleccion:
            return

        valores = tabla.item(seleccion[0], "values")
        mostrar_datos((*valores, "ACTIVO"))

    def buscar_en_tiempo_real(event=None):
        cargar_proveedores(entrada_busqueda.get().strip())

    def buscar_manual():
        cargar_proveedores(entrada_busqueda.get().strip())

    def limpiar_busqueda():
        entrada_busqueda.delete(0, tk.END)
        cargar_proveedores()
        entrada_busqueda.focus_set()

    def actualizar_lista_proveedores():
        cargar_proveedores(entrada_busqueda.get().strip())

    tabla.bind("<<TreeviewSelect>>", seleccionar_proveedor)
    entrada_busqueda.bind("<KeyRelease>", buscar_en_tiempo_real)
    entrada_busqueda.bind(
        "<Return>",
        lambda event: buscar_manual(),
    )

    crear_boton(
        busqueda, "Limpiar", limpiar_busqueda,
        COLOR_AZUL, COLOR_AZUL_SECUNDARIO, 10,
    ).pack(side="left")

    # --------------------------------------------------------
    # ACCIONES SUPERIORES
    # --------------------------------------------------------

    crear_boton(
        barra,
        "Papelera de proveedores",
        lambda: abrir_papelera(ventana, actualizar_lista_proveedores),
        COLOR_AZUL_SECUNDARIO,
        COLOR_AZUL_HOVER,
        21,
    ).pack(side="right", padx=(8, 0))

    crear_boton(
        barra,
        "+ Nuevo proveedor",
        lambda: abrir_registro(ventana, actualizar_lista_proveedores),
        COLOR_NARANJA,
        COLOR_NARANJA_HOVER,
        19,
    ).pack(side="right", padx=(8, 0))

    # --------------------------------------------------------
    # PIE DE VENTANA
    # --------------------------------------------------------

    pie = tk.Frame(ventana, bg=COLOR_AZUL, height=48)
    pie.pack(side="bottom", fill="x")
    pie.pack_propagate(False)

    tk.Frame(pie, bg=COLOR_NARANJA, height=4).pack(
        side="top", fill="x"
    )

    tk.Label(
        pie,
        text="Papelería Luna | Gestión de proveedores",
        font=(FUENTE, 9),
        bg=COLOR_AZUL,
        fg="#cbd5e1",
    ).pack(side="left", padx=22)

    crear_boton(
        pie, "Volver al menú", ventana.destroy,
        COLOR_NARANJA, COLOR_NARANJA_HOVER, 18, fg="white",
    ).pack(side="right", padx=18, pady=5)

    cargar_proveedores()

    if raiz is None:
        ventana.mainloop()
