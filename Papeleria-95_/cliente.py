import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import IntegrityError
# ============================================================
# PALETA DE COLORES - PAPELERÍA LUNA
# ============================================================

from tema import (
    obtener_colores,
    obtener_tema_actual,
    registrar_observador,
    eliminar_observador
)

TEMA_ACTUAL = obtener_tema_actual()
COLORES = obtener_colores(TEMA_ACTUAL)

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

FUENTE = "Arial"    

TIPOS_CLIENTE = [
    "Cliente particular",
    "Empresa",
    "Cliente frecuente",
    "Cliente VIP"
]

PLACEHOLDER_BUSQUEDA = ""

# ============================================================
# CONEXIÓN A MYSQL
# ============================================================

def obtener_conexion():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Papeleria_Luna"
    )


# ============================================================
# FUNCIONES VISUALES
# ============================================================

def centrar_ventana(ventana, ancho, alto):
    ventana.update_idletasks()

    x = (ventana.winfo_screenwidth() - ancho) // 2
    y = (ventana.winfo_screenheight() - alto) // 2

    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


def boton_hover(boton, normal, hover):
    boton._color_normal = normal
    boton._color_hover = hover

    boton.bind(
        "<Enter>",
        lambda evento: boton.configure(
            bg=boton._color_hover
        )
    )

    boton.bind(
        "<Leave>",
        lambda evento: boton.configure(
            bg=boton._color_normal
        )
    )

def crear_boton(
    padre,
    texto,
    comando,
    color=COLOR_AZUL,
    hover=COLOR_AZUL_HOVER,
    ancho=None
):
    opciones = {
        "text": texto,
        "command": comando,
        "font": (FUENTE, 9, "bold"),
        "bg": color,
        "fg": "#ffffff",
        "activebackground": hover,
        "activeforeground": "#ffffff",
        "relief": "flat",
        "bd": 0,
        "cursor": "hand2",
        "padx": 14,
        "pady": 9
    }

    if ancho is not None:
        opciones["width"] = ancho

    boton = tk.Button(padre, **opciones)
    boton_hover(boton, color, hover)

    return boton


def crear_encabezado(padre, titulo, subtitulo):
    encabezado = tk.Frame(
        padre,
        bg=COLOR_AZUL,
        height=112
    )
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    contenido = tk.Frame(encabezado, bg=COLOR_AZUL)
    contenido.pack(
        side="left",
        fill="both",
        expand=True,
        padx=28,
        pady=17
    )

    tk.Label(
        contenido,
        text="PAPELERÍA LUNA  /  CLIENTES",
        font=(FUENTE, 9, "bold"),
        bg=COLOR_AZUL,
        fg=COLOR_NARANJA
    ).pack(anchor="w")

    tk.Label(
        contenido,
        text=titulo,
        font=(FUENTE, 21, "bold"),
        bg=COLOR_AZUL,
        fg="#ffffff"
    ).pack(anchor="w", pady=(4, 1))

    tk.Label(
        contenido,
        text=subtitulo,
        font=(FUENTE, 10),
        bg=COLOR_AZUL,
        fg="#e2e8f0"
    ).pack(anchor="w")

    tk.Frame(
        padre,
        bg=COLOR_NARANJA,
        height=4
    ).pack(fill="x")

    return encabezado


def crear_panel(padre, padding=16):
    return tk.Frame(
        padre,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
        padx=padding,
        pady=padding
    )

# ============================================================
# VENTANAS ABIERTAS DEL MÓDULO CLIENTES
# ============================================================

VENTANAS_CLIENTES = []


def crear_ventana_hija(padre, titulo, ancho=850, alto=650):
    ventana = tk.Toplevel(padre)
    ventana.title(titulo)
    ventana.configure(bg=COLOR_FONDO)
    ventana.resizable(True, True)
    ventana.minsize(
        min(ancho, 950),
        min(alto, 680)
    )
    ventana.transient(padre)

    centrar_ventana(ventana, ancho, alto)

    if ventana not in VENTANAS_CLIENTES:
        VENTANAS_CLIENTES.append(ventana)

    def limpiar_ventana(evento):
        if evento.widget is ventana:
            if ventana in VENTANAS_CLIENTES:
                VENTANAS_CLIENTES.remove(ventana)

    ventana.bind("<Destroy>", limpiar_ventana, add="+")

    return ventana

def configurar_estilo_tabla(ventana=None):
    estilo = ttk.Style(ventana) if ventana is not None else ttk.Style()

    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    # ========================================================
    # TABLA PRINCIPAL DE CLIENTES
    # ========================================================

    estilo.configure(
        "Clientes.Treeview",
        font=(FUENTE, 9),
        rowheight=32,
        background=COLOR_PANEL,
        fieldbackground=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        bordercolor=COLOR_BORDE,
        borderwidth=1,
        relief="flat"
    )

    estilo.map(
        "Clientes.Treeview",
        background=[("selected", COLORES["SELECCION"])],
        foreground=[("selected", COLOR_TEXTO)]
    )

    estilo.configure(
        "Clientes.Treeview.Heading",
        font=(FUENTE, 9, "bold"),
        background=COLOR_AZUL,
        foreground=COLOR_PANEL,
        relief="flat",
        borderwidth=0,
        padding=(8, 8)
    )

    estilo.map(
        "Clientes.Treeview.Heading",
        background=[("active", COLOR_AZUL_SECUNDARIO)],
        foreground=[("active", COLOR_PANEL)]
    )
    
    # ========================================================
    # COMBOBOX
    # ========================================================

    estilo.configure(
        "Clientes.TCombobox",
        font=(FUENTE, 10),
        padding=6,
        fieldbackground=COLOR_PANEL,
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO
    )


# ============================================================
# ACTUALIZAR COLORES DEL MÓDULO
# ============================================================

def actualizar_colores_modulo(nuevos_colores):
    global TEMA_ACTUAL, COLORES
    global COLOR_FONDO, COLOR_PANEL
    global COLOR_AZUL, COLOR_AZUL_SECUNDARIO, COLOR_AZUL_HOVER
    global COLOR_NARANJA, COLOR_NARANJA_HOVER
    global COLOR_TEXTO, COLOR_TEXTO_SUAVE, COLOR_BORDE
    global COLOR_ROJO, COLOR_ROJO_HOVER

    COLORES = nuevos_colores.copy()

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

    TEMA_ACTUAL = obtener_tema_actual()


def recolorear_ventana(widget, anteriores, nuevos):
    """
    Reemplaza los colores conocidos en los widgets existentes.
    No modifica textos, consultas ni datos de los clientes.
    """

    # Relacionar cada color anterior con su equivalente nuevo.
    equivalencias = {
        anteriores.get(clave): nuevos.get(clave)
        for clave in nuevos
        if anteriores.get(clave) is not None
        and nuevos.get(clave) is not None
    }

    try:
        opciones = widget.configure()

        for propiedad in ("bg", "background", "fg", "foreground",
                          "insertbackground", "highlightbackground",
                          "highlightcolor", "activebackground",
                          "selectbackground", "selectforeground"):

            if propiedad not in opciones:
                continue

            try:
                actual = widget.cget(propiedad)
            except tk.TclError:
                continue

            if actual in equivalencias:
                widget.configure(
                    **{propiedad: equivalencias[actual]}
                )

        # Actualizar colores asociados a los botones con hover.
        if isinstance(widget, tk.Button):
            if hasattr(widget, "_color_normal"):
                widget._color_normal = equivalencias.get(
                    widget._color_normal,
                    widget._color_normal
                )

            if hasattr(widget, "_color_hover"):
                widget._color_hover = equivalencias.get(
                    widget._color_hover,
                    widget._color_hover
                )

        # Actualizar bordes de widgets clásicos.
        try:
            if widget.cget("highlightbackground") in equivalencias:
                widget.configure(
                    highlightbackground=equivalencias[
                        widget.cget("highlightbackground")
                    ]
                )
        except (tk.TclError, KeyError):
            pass

    except (tk.TclError, AttributeError):
        pass

    # Continuar con todos los widgets hijos.
    try:
        hijos = widget.winfo_children()
    except tk.TclError:
        hijos = []

    for hijo in hijos:
        recolorear_ventana(hijo, anteriores, nuevos)


def aplicar_tema_clientes(nuevos_colores):
    """
    Función observadora llamada cuando cambia el tema global.
    """

    anteriores = COLORES.copy()

    actualizar_colores_modulo(nuevos_colores)

    # Actualizar los estilos de las tablas y los combobox.
    try:
        for ventana in tk._default_root.winfo_children():
            pass
    except (tk.TclError, AttributeError):
        pass

    # El módulo registra sus ventanas activas en esta lista.
    for ventana in VENTANAS_CLIENTES.copy():
        try:
            if ventana.winfo_exists():
                recolorear_ventana(
                    ventana,
                    anteriores,
                    nuevos_colores
                )

                configurar_estilo_tabla(ventana)
        except tk.TclError:
            pass


# Ventanas abiertas del módulo Clientes.
VENTANAS_CLIENTES = []


def crear_tabla_clientes(padre, altura=10):

    
    columnas = (
        "id_cliente",
        "identificacion",
        "nombre",
        "apellidos",
        "telefono",
        "tipo_cliente"
    )

    # Contenedor exclusivo de la tabla y sus barras
    contenedor_tabla = tk.Frame(
        padre,
        bg=COLOR_PANEL
    )
    contenedor_tabla.pack(fill="both", expand=True)

    contenedor_tabla.grid_rowconfigure(0, weight=1)
    contenedor_tabla.grid_columnconfigure(0, weight=1)  
    contenedor_tabla.grid_columnconfigure(1, weight=0)

    tabla = ttk.Treeview(
        contenedor_tabla,
        columns=columnas,
        show="headings",
        selectmode="browse",
        height=altura,
        style="Clientes.Treeview"
    )

    encabezados = {
        "id_cliente": ("ID", 65),
        "identificacion": ("Identificación", 145),
        "nombre": ("Nombre", 145),
        "apellidos": ("Apellidos", 170),
        "telefono": ("Teléfono", 130),
        "tipo_cliente": ("Tipo de cliente", 175)
    }

    for columna in columnas:
        titulo, ancho = encabezados[columna]

        tabla.heading(
            columna,
            text=titulo,
            anchor="center"
        )

        tabla.column(
            columna,
            width=ancho,
            minwidth=80,
            anchor="center",
            stretch=True
        )

    # Barra vertical
    scroll_y = ttk.Scrollbar(
        contenedor_tabla,
        orient="vertical",
        command=tabla.yview,
        style="Clientes.Vertical.TScrollbar"
    )

    # Barra horizontal
    scroll_x = ttk.Scrollbar(
        contenedor_tabla,
        orient="horizontal",
        command=tabla.xview,
        style="Clientes.Horizontal.TScrollbar"
    )

    tabla.configure(
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set
    )

    tabla.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    scroll_y.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    scroll_x.grid(
        row=1,
        column=0,
        sticky="ew"
    )

    return tabla


# ============================================================
# CONSULTAS GENERALES
# ============================================================

def obtener_clientes_activos():
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id_cliente,
                identificacion,
                nombre,
                apellidos,
                telefono,
                direccion,
                tipo_cliente
            FROM Clientes
            WHERE estado = 0
            ORDER BY id_cliente ASC
        """)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ============================================================
# MÓDULO PRINCIPAL DE CLIENTES
# ============================================================

def abrir_clientes(raiz=None):
    ventana_independiente = raiz is None

    if ventana_independiente:
        ventana = tk.Tk()
        ventana.title("Papelería Luna | Centro de clientes")
        ventana.configure(bg=COLOR_FONDO)
        ventana.resizable(True, True)
        ventana.minsize(950, 680)
    else:
        ventana = crear_ventana_hija(
            raiz,
            "Papelería Luna | Centro de clientes",
            1180,
            800
        )

        # Registrar esta ventana para recibir cambios de tema.
    if ventana not in VENTANAS_CLIENTES:
        VENTANAS_CLIENTES.append(ventana)

    # Aplicar los colores del usuario que inició sesión.
    actualizar_colores_modulo(obtener_colores())

    centrar_ventana(ventana, 1180, 700)

    # Configurar los estilos antes de crear las tablas
    configurar_estilo_tabla(ventana)

    registrar_observador(aplicar_tema_clientes)

    def limpiar_observador(evento=None):
        if evento is not None and evento.widget is not ventana:
            return

        eliminar_observador(aplicar_tema_clientes)

        if ventana in VENTANAS_CLIENTES:
            VENTANAS_CLIENTES.remove(ventana)

    ventana.bind("<Destroy>", limpiar_observador, add="+")

    clientes_cache = []

    # --------------------------------------------------------
    # VALIDAR DATOS
    # --------------------------------------------------------

    def validar_datos(nombre, apellidos, telefono, identificacion):
        campos = [
            (nombre, "nombre"),
            (apellidos, "apellidos"),
            (telefono, "teléfono"),
            (identificacion, "identificación")
        ]

        for valor, etiqueta in campos:
            if valor is None or not str(valor).strip():
                messagebox.showwarning(
                    "Campo obligatorio",
                    f"Ingresa el {etiqueta} del cliente.",
                    parent=ventana
                )
                return False

        return True

    # --------------------------------------------------------
    # BUSCAR POR IDENTIFICACIÓN
    # --------------------------------------------------------

    def buscar_en_bd(identificacion):
        conexion = None
        cursor = None

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    id_cliente,
                    identificacion,
                    nombre,
                    apellidos,
                    telefono,
                    direccion,
                    tipo_cliente,
                    estado
                FROM Clientes
                WHERE identificacion = %s
                  AND estado = 0
            """, (identificacion.strip(),))

            return cursor.fetchone()

        except mysql.connector.Error as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudo consultar el cliente.\n\n{error}",
                parent=ventana
            )
            return False

        finally:
            if cursor is not None:
                cursor.close()

            if conexion is not None and conexion.is_connected():
                conexion.close()

    # ========================================================
    # REGISTRAR CLIENTE
    # ========================================================

    def registrar_cliente():
        registro = crear_ventana_hija(
            ventana,
            "Registrar cliente",
            760,
            660
        )

        crear_encabezado(
            registro,
            "Registrar cliente",
            "Completa la información para dar de alta un cliente."
        )

        contenedor = tk.Frame(registro, bg=COLOR_FONDO)
        contenedor.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=18
        )

        panel = crear_panel(contenedor, 20)
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="Información del cliente",
            font=(FUENTE, 13, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_AZUL
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            panel,
            text="Completa los campos obligatorios marcados con *.",
            font=(FUENTE, 9),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        ).pack(anchor="w", pady=(0, 16))

        formulario = tk.Frame(panel, bg=COLOR_PANEL)
        formulario.pack(fill="x")

        variables = {
            "nombre": tk.StringVar(master=registro),
            "apellidos": tk.StringVar(master=registro),
            "telefono": tk.StringVar(master=registro),
            "identificacion": tk.StringVar(master=registro),
            "direccion": tk.StringVar(master=registro),
            "tipo": tk.StringVar(
                master=registro,
                value=TIPOS_CLIENTE[0]
            )
        }

        def campo_formulario(etiqueta, clave, fila, columna):
            bloque = tk.Frame(formulario, bg=COLOR_PANEL)

            bloque.grid(
                row=fila,
                column=columna,
                sticky="ew",
                padx=(0, 12) if columna == 0 else (12, 0),
                pady=8
            )

            tk.Label(
                bloque,
                text=etiqueta,
                font=(FUENTE, 9, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO
            ).pack(anchor="w", pady=(0, 5))

            entrada = tk.Entry(
                bloque,
                textvariable=variables[clave],
                font=(FUENTE, 10),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO,
                relief="solid",
                bd=1,
                highlightthickness=1,
                highlightbackground=COLOR_BORDE,
                highlightcolor=COLOR_NARANJA
            )

            entrada.pack(fill="x", ipady=7)

            return entrada

        entrada_nombre = campo_formulario(
            "Nombre *", "nombre", 0, 0
        )

        campo_formulario(
            "Apellidos *", "apellidos", 0, 1
        )

        campo_formulario(
            "Teléfono *", "telefono", 1, 0
        )

        campo_formulario(
            "Identificación *", "identificacion", 1, 1
        )

        campo_formulario(
            "Dirección", "direccion", 2, 0
        )

        bloque_tipo = tk.Frame(formulario, bg=COLOR_PANEL)
        bloque_tipo.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=(12, 0),
            pady=8
        )

        tk.Label(
            bloque_tipo,
            text="Tipo de cliente",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).pack(anchor="w", pady=(0, 5))

        combo_tipo = ttk.Combobox(
            bloque_tipo,
            textvariable=variables["tipo"],
            values=TIPOS_CLIENTE,
            state="readonly",
            font=(FUENTE, 10),
            style="Clientes.TCombobox"
        )

        combo_tipo.pack(fill="x")

        formulario.columnconfigure(0, weight=1)
        formulario.columnconfigure(1, weight=1)

        tk.Label(
            panel,
            text="* Campos obligatorios",
            font=(FUENTE, 9),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        ).pack(anchor="w", pady=(12, 0))

        def guardar_cliente():
            n = variables["nombre"].get().strip()
            a = variables["apellidos"].get().strip()
            t = variables["telefono"].get().strip()
            i = variables["identificacion"].get().strip()
            d = variables["direccion"].get().strip()
            tipo = variables["tipo"].get().strip()

            # Comprobación temporal
            print("Nombre:", repr(n))
            print("Apellidos:", repr(a))
            print("Teléfono:", repr(t))
            print("Identificación:", repr(i))

            if not validar_datos(n, a, t, i):
                return

            conexion = None
            cursor = None

            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()

                # estado = 0: activo
                # estado = 1: desactivado
                cursor.execute("""
                    INSERT INTO Clientes (
                        identificacion,
                        nombre,
                        apellidos,
                        telefono,
                        direccion,
                        tipo_cliente,
                        estado
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 0)
                """, (
                    i,
                    n,
                    a,
                    t,
                    d or None,
                    tipo or None
                ))

                conexion.commit()

                messagebox.showinfo(
                    "Registro exitoso",
                    "El cliente se registró correctamente.",
                    parent=registro
                )

                registro.destroy()
                actualizar_dashboard()

            except IntegrityError as error:
                if conexion is not None:
                    conexion.rollback()

                if error.errno == 1062:
                    mensaje = (
                        "La identificación ya está registrada "
                        "en la base de datos."
                    )
                else:
                    mensaje = str(error)

                messagebox.showerror(
                    "Error al registrar",
                    mensaje,
                    parent=registro
                )

            except mysql.connector.Error as error:
                if conexion is not None:
                    conexion.rollback()

                messagebox.showerror(
                    "Error de MySQL",
                    f"No se pudo registrar el cliente.\n\n{error}",
                    parent=registro
                )

            finally:
                if cursor is not None:
                    cursor.close()

                if conexion is not None and conexion.is_connected():
                    conexion.close()

        botones = tk.Frame(panel, bg=COLOR_PANEL)
        botones.pack(fill="x", pady=(22, 0))

        crear_boton(
            botones,
            "Guardar cliente",
            guardar_cliente,
            COLOR_AZUL,
            COLOR_AZUL_HOVER
        ).pack(side="left", padx=(0, 8))

        def limpiar_formulario():
            for variable in variables.values():
                variable.set("")

            variables["tipo"].set(TIPOS_CLIENTE[0])
            entrada_nombre.focus_set()

        crear_boton(
            botones,
            "Limpiar formulario",
            limpiar_formulario,
            COLOR_AZUL_SECUNDARIO,
            COLOR_AZUL_HOVER
        ).pack(side="left", padx=8)

        crear_boton(
            botones,
            "Cancelar",
            registro.destroy,
            COLOR_NARANJA,
            COLOR_NARANJA_HOVER
        ).pack(side="right")

        entrada_nombre.focus_set()

    
    # ========================================================
    # VISUALIZAR CLIENTES
    # ========================================================

    def visualizar_clientes():
        listado = crear_ventana_hija(
            ventana,
            "Directorio de clientes",
            1100,
            660
        )

        crear_encabezado(
            listado,
            "Directorio de clientes",
            "Consulta los registros activos de Papelería Luna."
        )

        contenedor = tk.Frame(listado, bg=COLOR_FONDO)
        contenedor.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=18
        )

        panel = crear_panel(contenedor, 15)
        panel.pack(fill="both", expand=True)

        fila_superior = tk.Frame(panel, bg=COLOR_PANEL)
        fila_superior.pack(fill="x", pady=(0, 12))

        tk.Label(
            fila_superior,
            text="Clientes registrados",
            font=(FUENTE, 13, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_AZUL
        ).pack(side="left")

        total = tk.Label(
            fila_superior,
            text="Total: 0",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_AZUL_SECUNDARIO
        )
        total.pack(side="right")

        marco_tabla = tk.Frame(
            panel,
            bg=COLOR_PANEL
        )
        marco_tabla.pack(
            fill="both",
            expand=True
        )

        tabla = crear_tabla_clientes(marco_tabla, 13)

        clientes_guardados = []

        # Cargar los clientes activos en la tabla
        def cargar_clientes():
            for elemento in tabla.get_children():
                tabla.delete(elemento)

            try:
                clientes = obtener_clientes_activos()

                clientes_guardados.clear()
                clientes_guardados.extend(clientes)

                for cliente in clientes:
                    tabla.insert(
                        "",
                        "end",
                        values=(
                            cliente["id_cliente"],
                            cliente["identificacion"] or "",
                            cliente["nombre"] or "",
                            cliente["apellidos"] or "",
                            cliente["telefono"] or "",
                            cliente["tipo_cliente"] or ""
                        )
                    )

                total.config(
                    text=f"Total: {len(clientes)}"
                )

            except mysql.connector.Error as error:
                messagebox.showerror(
                    "Error de MySQL",
                    f"No se pudieron cargar los clientes.\n\n{error}",
                    parent=listado
                )

        # Abrir la modificación del cliente seleccionado
        def modificar_seleccionado(event=None):
            seleccion = tabla.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selecciona un cliente",
                    "Selecciona un registro de la tabla para modificarlo.",
                    parent=listado
                )
                return

            valores = tabla.item(
                seleccion[0],
                "values"
            )

            if not valores:
                return

            identificacion = valores[1]

            # Los datos se cargarán automáticamente
            modificar_cliente(identificacion)

        botones = tk.Frame(panel, bg=COLOR_PANEL)
        botones.pack(fill="x", pady=(14, 0))

        crear_boton(
            botones,
            "Actualizar listado",
            cargar_clientes,
            COLOR_AZUL_SECUNDARIO,
            COLOR_AZUL_HOVER
        ).pack(side="left")

        crear_boton(
            botones,
            "Modificar",
            modificar_seleccionado,
            COLOR_AZUL,
            COLOR_AZUL_HOVER
        ).pack(side="left", padx=8)

        crear_boton(
            botones,
            "Cerrar",
            listado.destroy,
            COLOR_NARANJA,
            COLOR_NARANJA_HOVER
        ).pack(side="right")

        # Doble clic sobre un cliente para modificarlo
        tabla.bind(
            "<Double-1>",
            modificar_seleccionado
        )

        cargar_clientes()

    # ========================================================
    # BUSCAR CLIENTE
    # ========================================================

    def buscar_cliente():
        busqueda = crear_ventana_hija(
            ventana,
            "Buscar clientes",
            1080,
            660
        )

        crear_encabezado(
            busqueda,
            "Buscar clientes",
            "Localiza clientes por apellidos o por teléfono."
        )

        contenedor = tk.Frame(busqueda, bg=COLOR_FONDO)
        contenedor.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=18
        )

        panel = crear_panel(contenedor, 16)
        panel.pack(fill="both", expand=True)

        filtros = tk.Frame(panel, bg=COLOR_PANEL)
        filtros.pack(fill="x", pady=(0, 12))

        tk.Label(
            filtros,
            text="Buscar por",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        tipo_busqueda = tk.StringVar(value="Apellidos")

        combo_busqueda = ttk.Combobox(
            filtros,
            textvariable=tipo_busqueda,
            values=[
                "Apellidos",
                "Últimos 4 dígitos del teléfono"
            ],
            state="readonly",
            font=(FUENTE, 10),
            width=32
        )
        combo_busqueda.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 12)
        )

        entrada = tk.Entry(
            filtros,
            font=(FUENTE, 10),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO,
            insertbackground=COLOR_TEXTO,
            relief="solid",
            bd=1,
            highlightthickness=2,
            highlightbackground=COLOR_BORDE,
            highlightcolor=COLOR_NARANJA
        )
        entrada.grid(
            row=0,
            column=2,
            sticky="ew",
            ipady=7
        )

        filtros.columnconfigure(2, weight=1)

        marco_tabla = tk.Frame(panel, bg=COLOR_PANEL)
        marco_tabla.pack(fill="both", expand=True, pady=(5, 0))

        tabla = crear_tabla_clientes(marco_tabla, 11)

        resultado = tk.Label(
            panel,
            text="Escribe un dato para comenzar la búsqueda.",
            font=(FUENTE, 9),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        )
        resultado.pack(anchor="w", pady=(10, 0))

        def ejecutar_busqueda(event=None):
            dato = entrada.get().strip()
            modo = tipo_busqueda.get()

            for elemento in tabla.get_children():
                tabla.delete(elemento)

            if not dato:
                resultado.config(
                    text="Escribe un dato para comenzar la búsqueda.",
                    fg=COLOR_TEXTO_SUAVE
                )
                return

            if modo == "Apellidos":
                consulta = """
                    SELECT
                        id_cliente,
                        identificacion,
                        nombre,
                        apellidos,
                        telefono,
                        tipo_cliente
                    FROM Clientes
                    WHERE apellidos LIKE %s
                      AND estado = 0
                    ORDER BY id_cliente ASC
                """
                parametros = (f"%{dato}%",)

            else:
                if not dato.isdigit():
                    resultado.config(
                        text="Introduce solamente números de teléfono.",
                        fg=COLOR_ROJO
                    )
                    return

                if len(dato) < 4:
                    resultado.config(
                        text="Escribe al menos los últimos 4 dígitos.",
                        fg=COLOR_TEXTO_SUAVE
                    )
                    return

                consulta = """
                    SELECT
                        id_cliente,
                        identificacion,
                        nombre,
                        apellidos,
                        telefono,
                        tipo_cliente
                    FROM Clientes
                    WHERE RIGHT(TRIM(telefono), 4) = %s
                      AND estado = 0
                    ORDER BY id_cliente ASC
                """
                parametros = (dato[-4:],)

            conexion = None
            cursor = None

            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()

                cursor.execute(consulta, parametros)
                clientes = cursor.fetchall()

                for cliente in clientes:
                    tabla.insert(
                        "",
                        "end",
                        values=tuple(
                            "" if valor is None else valor
                            for valor in cliente
                        )
                    )

                resultado.config(
                    text=(
                        f"Se encontraron {len(clientes)} cliente(s)."
                        if clientes
                        else "No se encontraron clientes coincidentes."
                    ),
                    fg=(
                        COLOR_AZUL_SECUNDARIO
                        if clientes
                        else COLOR_TEXTO_SUAVE
                    )
                )

            except mysql.connector.Error as error:
                resultado.config(
                    text="No se pudo completar la búsqueda.",
                    fg=COLOR_ROJO
                )

                messagebox.showerror(
                    "Error de MySQL",
                    str(error),
                    parent=busqueda
                )

            finally:
                if cursor is not None:
                    cursor.close()

                if conexion is not None and conexion.is_connected():
                    conexion.close()

        def limpiar_busqueda():
            entrada.delete(0, tk.END)

            for elemento in tabla.get_children():
                tabla.delete(elemento)

            resultado.config(
                text="Escribe un dato para comenzar la búsqueda.",
                fg=COLOR_TEXTO_SUAVE
            )

            entrada.focus_set()

        entrada.bind("<KeyRelease>", ejecutar_busqueda)
        combo_busqueda.bind(
            "<<ComboboxSelected>>",
            ejecutar_busqueda
        )

        botones = tk.Frame(panel, bg=COLOR_PANEL)
        botones.pack(fill="x", pady=(12, 0))

        crear_boton(
            botones,
            "Limpiar búsqueda",
            limpiar_busqueda,
            COLOR_NARANJA,
            COLOR_NARANJA_HOVER
        ).pack(side="left")

        crear_boton(
            botones,
            "Cerrar",
            busqueda.destroy,
            "#f59e0b",
            "#d97706"
        ).pack(side="right")

        entrada.focus_set()


    # ========================================================
    # MODIFICAR CLIENTE
    # ========================================================

    def modificar_cliente(identificacion_inicial=None):

        if not identificacion_inicial:
            messagebox.showwarning(
                "Selecciona un cliente",
                "Selecciona un cliente del directorio para modificarlo.",
                parent=ventana
            )
            return

        modificar = crear_ventana_hija(
            ventana,
            "Modificar cliente",
            760,
            700
        )

        crear_encabezado(
            modificar,
            "Modificar cliente",
            "Actualiza los datos del cliente seleccionado."
        )

        contenedor = tk.Frame(
            modificar,
            bg=COLOR_FONDO
        )
        contenedor.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=16
        )

        panel = crear_panel(contenedor, 18)
        panel.pack(fill="both", expand=True)

        # Consultar automáticamente al cliente seleccionado
        cliente = buscar_en_bd(identificacion_inicial)

        if cliente is False:
            modificar.destroy()
            return

        if cliente is None:
            messagebox.showwarning(
                "Cliente no encontrado",
                "No se encontró un cliente activo con esa identificación.",
                parent=modificar
            )
            modificar.destroy()
            return

        id_actual = cliente["id_cliente"]

        tk.Label(
            panel,
            text=f"Cliente ID: {id_actual}",
            font=(FUENTE, 12, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_AZUL
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            panel,
            text="Modifica los campos que necesites.",
            font=(FUENTE, 9),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        ).pack(anchor="w", pady=(0, 15))

        formulario = tk.Frame(
            panel,
            bg=COLOR_PANEL
        )
        formulario.pack(fill="x")

        variables = {
            "nombre": tk.StringVar(master=modificar),
            "apellidos": tk.StringVar(master=modificar),
            "telefono": tk.StringVar(master=modificar),
            "identificacion": tk.StringVar(master=modificar),
            "direccion": tk.StringVar(master=modificar)
        }

        campos = {}

        def crear_campo_edicion(etiqueta, clave, fila, columna):

            bloque = tk.Frame(
                formulario,
                bg=COLOR_PANEL
            )

            bloque.grid(
                row=fila,
                column=columna,
                sticky="ew",
                padx=(0, 10) if columna == 0 else (10, 0),
                pady=9
            )

            tk.Label(
                bloque,
                text=etiqueta,
                font=(FUENTE, 9, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO
            ).pack(anchor="w", pady=(0, 5))

            entrada = tk.Entry(
                bloque,
                textvariable=variables[clave],
                font=(FUENTE, 10),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO,
                relief="solid",
                bd=1,
                highlightthickness=1,
                highlightbackground=COLOR_BORDE,
                highlightcolor=COLOR_NARANJA
            )

            entrada.pack(fill="x", ipady=7)

            campos[clave] = entrada

        crear_campo_edicion(
            "Nombre *", "nombre", 0, 0
        )

        crear_campo_edicion(
            "Apellidos *", "apellidos", 0, 1
        )

        crear_campo_edicion(
            "Teléfono *", "telefono", 1, 0
        )

        crear_campo_edicion(
            "Identificación *", "identificacion", 1, 1
        )

        crear_campo_edicion(
            "Dirección", "direccion", 2, 0
        )

        formulario.columnconfigure(0, weight=1)
        formulario.columnconfigure(1, weight=1)

        # Tipo de cliente
        bloque_tipo = tk.Frame(
            formulario,
            bg=COLOR_PANEL
        )

        bloque_tipo.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=(10, 0),
            pady=9
        )

        tk.Label(
            bloque_tipo,
            text="Tipo de cliente",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).pack(anchor="w", pady=(0, 5))

        combo_tipo = ttk.Combobox(
            bloque_tipo,
            values=TIPOS_CLIENTE,
            state="readonly",
            font=(FUENTE, 10),
            style="Clientes.TCombobox"
        )

        combo_tipo.pack(fill="x", ipady=3)

        # Rellenar automáticamente todos los campos
        for clave, variable in variables.items():
            variable.set(cliente.get(clave) or "")

        tipo_actual = cliente.get("tipo_cliente") or ""

        if tipo_actual in TIPOS_CLIENTE:
            combo_tipo.set(tipo_actual)
        else:
            combo_tipo.set("")

        estado = tk.Label(
            panel,
            text="Datos cargados correctamente.",
            font=(FUENTE, 9),
            bg=COLOR_PANEL,
            fg=COLOR_AZUL_SECUNDARIO
        )

        estado.pack(anchor="w", pady=(15, 0))

        # Guardar los cambios
        def guardar_cambios():

            datos = {
                clave: variable.get().strip()
                for clave, variable in variables.items()
            }

            tipo = combo_tipo.get().strip()

            if not validar_datos(
                datos["nombre"],
                datos["apellidos"],
                datos["telefono"],
                datos["identificacion"]
            ):
                return

            if tipo and tipo not in TIPOS_CLIENTE:
                messagebox.showwarning(
                    "Tipo de cliente inválido",
                    "Selecciona un tipo de cliente de la lista.",
                    parent=modificar
                )
                return

            conexion = None
            cursor = None

            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()

                cursor.execute("""
                    UPDATE Clientes
                    SET
                        identificacion = %s,
                        nombre = %s,
                        apellidos = %s,
                        telefono = %s,
                        direccion = %s,
                        tipo_cliente = %s
                    WHERE id_cliente = %s
                      AND estado = 0
                """, (
                    datos["identificacion"],
                    datos["nombre"],
                    datos["apellidos"],
                    datos["telefono"],
                    datos["direccion"] or None,
                    tipo or None,
                    id_actual
                ))

                # Comprobar que el cliente siga activo
                if cursor.rowcount == 0:
                    cursor.execute("""
                        SELECT id_cliente
                        FROM Clientes
                        WHERE id_cliente = %s
                          AND estado = 0
                    """, (id_actual,))

                    if cursor.fetchone() is None:
                        conexion.rollback()

                        messagebox.showwarning(
                            "Cliente no disponible",
                            "El cliente ya no está activo.",
                            parent=modificar
                        )
                        return

                conexion.commit()

                estado.config(
                    text="Cambios guardados correctamente.",
                    fg=COLOR_AZUL_SECUNDARIO
                )

                messagebox.showinfo(
                    "Actualización exitosa",
                    "Los datos del cliente se actualizaron correctamente.",
                    parent=modificar
                )

                modificar.destroy()

                # Actualizar la tabla y los indicadores principales
                actualizar_dashboard()

            except IntegrityError as error:

                if conexion is not None:
                    conexion.rollback()

                if error.errno == 1062:
                    mensaje = (
                        "La identificación ya pertenece a otro cliente."
                    )
                else:
                    mensaje = str(error)

                messagebox.showerror(
                    "Error al modificar",
                    mensaje,
                    parent=modificar
                )

            except mysql.connector.Error as error:

                if conexion is not None:
                    conexion.rollback()

                messagebox.showerror(
                    "Error de MySQL",
                    f"No se pudieron guardar los cambios.\n\n{error}",
                    parent=modificar
                )

            finally:
                if cursor is not None:
                    cursor.close()

                if conexion is not None and conexion.is_connected():
                    conexion.close()

        
        # Desactivar al cliente seleccionado
        def desactivar_cliente():

            confirmar = messagebox.askyesno(
                "Confirmar desactivación",
                "¿Deseas desactivar a este cliente?\n\n"
                "Podrás recuperarlo posteriormente.",
                parent=modificar
            )

            if not confirmar:
                return

            conexion = None
            cursor = None

            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()

                cursor.execute("""
                    UPDATE Clientes
                    SET estado = 1
                    WHERE id_cliente = %s
                      AND estado = 0
                """, (id_actual,))

                if cursor.rowcount == 0:
                    conexion.rollback()

                    messagebox.showwarning(
                        "Cliente no disponible",
                        "El cliente ya está desactivado "
                        "o no se encuentra disponible.",
                        parent=modificar
                    )
                    return

                conexion.commit()

                messagebox.showinfo(
                    "Desactivación exitosa",
                    "El cliente se desactivó correctamente.",
                    parent=modificar
                )

                modificar.destroy()
                actualizar_dashboard()

            except mysql.connector.Error as error:

                if conexion is not None:
                    conexion.rollback()

                messagebox.showerror(
                    "Error de MySQL",
                    f"No se pudo desactivar al cliente.\n\n{error}",
                    parent=modificar
                )

            finally:
                if cursor is not None:
                    cursor.close()

                if conexion is not None and conexion.is_connected():
                    conexion.close()

    
        # Botones de la ventana de modificación
        botones = tk.Frame(
            panel,
            bg=COLOR_PANEL
        )
        botones.pack(fill="x", pady=(22, 0))

        crear_boton(
            botones,
            "Guardar cambios",
            guardar_cambios,
            COLOR_AZUL,
            COLOR_AZUL_HOVER
        ).pack(side="left")

        crear_boton(
            botones,
            "Eliminar",
            desactivar_cliente,
            COLOR_ROJO,
            "#dc2626"
        ).pack(side="left", padx=(10, 0))

        crear_boton(
            botones,
            "Cerrar",
            modificar.destroy,
            "#f59e0b",
            "#d97706"
        ).pack(side="right")

        campos["nombre"].focus_set()


    # ========================================================
    # DESACTIVAR Y RECUPERAR CLIENTES
    # estado = 0 activo; estado = 1 desactivado
    # ========================================================


    
    def eliminar_cliente():
        gestion = crear_ventana_hija(
            ventana,
            "Recuperar clientes",
            950,
            700
        )

        crear_encabezado(
            gestion,
            "Recuperar clientes",
            "Busca por nombre o apellidos y recupera clientes desactivados."
        )

        contenedor = tk.Frame(
            gestion,
            bg=COLOR_FONDO
        )
        contenedor.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=18
        )

        panel = crear_panel(contenedor, 16)
        panel.pack(fill="both", expand=True)

        # Buscador automático
        tk.Label(
            panel,
            text="Buscar cliente por nombre o apellidos",
            font=(FUENTE, 11, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_AZUL
        ).pack(anchor="w", pady=(0, 8))

        fila_busqueda = tk.Frame(
            panel,
            bg=COLOR_PANEL
        )
        fila_busqueda.pack(fill="x")

        entrada_busqueda = tk.Entry(
            fila_busqueda,
            font=(FUENTE, 10),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO,
            insertbackground=COLOR_TEXTO,
            relief="solid",
            bd=1,
            highlightthickness=2,
            highlightbackground=COLOR_BORDE,
            highlightcolor=COLOR_NARANJA
        )
        entrada_busqueda.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7,
            padx=(0, 10)
        )

        
        # ============================================================
        # TABLA DE CLIENTES DESACTIVADOS
        # ============================================================

        columnas = (
            "id_cliente",
            "identificacion",
            "nombre",
            "telefono",
            "direccion",
            "tipo_cliente"
        )

        estilo_tabla = ttk.Style(gestion)

        estilo_tabla.configure(
            "Luna.Treeview",
            font=(FUENTE, 9),
            rowheight=30,
            background=COLOR_PANEL,
            fieldbackground=COLOR_PANEL,
            foreground=COLOR_TEXTO,
            bordercolor=COLOR_BORDE
        )

        estilo_tabla.configure(
            "Luna.Treeview.Heading",
            font=(FUENTE, 9, "bold"),
            background=COLOR_AZUL,
            foreground=COLOR_PANEL,
            relief="flat",
            padding=(8, 8)
        )

        estilo_tabla.map(
            "Luna.Treeview",
            background=[("selected", COLORES["SELECCION"])],
            foreground=[("selected", COLOR_PANEL)]
        )

        estilo_tabla.map(
            "Luna.Treeview.Heading",
            background=[("active", COLOR_AZUL_SECUNDARIO)],
            foreground=[("active", COLOR_PANEL)]
        )

        # Contenedor de tabla y barras de desplazamiento
        contenedor_tabla = tk.Frame(
            panel,
            bg=COLOR_PANEL
        )

        contenedor_tabla.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(15, 10)
        )

        contenedor_tabla.rowconfigure(0, weight=1)
        contenedor_tabla.columnconfigure(0, weight=1)

        tabla = ttk.Treeview(
            contenedor_tabla,
            columns=columnas,
            show="headings",
            selectmode="browse",
            style="Luna.Treeview"
        )

        encabezados_tabla = {
            "id_cliente": ("ID", 55),
            "identificacion": ("Identificación", 125),
            "nombre": ("Nombre completo", 190),
            "telefono": ("Teléfono", 110),
            "direccion": ("Dirección", 190),
            "tipo_cliente": ("Tipo de cliente", 140)
        }

        for columna in columnas:
            titulo, ancho = encabezados_tabla[columna]

            tabla.heading(
                columna,
                text=titulo,
                anchor="center"
            )

            tabla.column(
                columna,
                width=ancho,
                minwidth=60,
                anchor="center"
            )

        estilo_scroll = ttk.Style(gestion)
        estilo_scroll.theme_use("clam")

        barra_vertical = ttk.Scrollbar(
            contenedor_tabla,
            orient="vertical",
            command=tabla.yview
        )

        barra_horizontal = ttk.Scrollbar(
            contenedor_tabla,
            orient="horizontal",
            command=tabla.xview
        )

        tabla.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set
        )

        tabla.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        barra_vertical.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        barra_horizontal.grid(
            row=1,
            column=0,
            sticky="ew"
        )


        etiqueta_estado = tk.Label(
            panel,
            text="Cargando clientes desactivados...",
            font=(FUENTE, 9),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        )
        etiqueta_estado.pack(anchor="w", pady=(0, 8))

        cliente_actual = {"id": None}

        # Consultar los clientes desactivados según el texto
        def cargar_clientes(filtro=""):
            conexion = None
            cursor = None

            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor(dictionary=True)

                filtro = filtro.strip()
                patron = f"%{filtro}%"

                cursor.execute("""
                    SELECT
                        id_cliente,
                        nombre,
                        apellidos,
                        identificacion,
                        telefono,
                        direccion,
                        tipo_cliente
                    FROM Clientes
                    WHERE estado = 1
                    AND (
                        nombre LIKE %s
                        OR apellidos LIKE %s
                        OR CONCAT(nombre, ' ', apellidos) LIKE %s
                    )
                    ORDER BY nombre ASC, apellidos ASC
                """, (patron, patron, patron))

                clientes = cursor.fetchall()

                # Actualizar la tabla
                for elemento in tabla.get_children():
                    tabla.delete(elemento)

                cliente_actual["id"] = None

                
                for cliente in clientes:
                    nombre_completo = (
                        f'{cliente["nombre"]} '
                        f'{cliente["apellidos"]}'
                    )

                    tabla.insert(
                        "",
                        "end",
                        iid=str(cliente["id_cliente"]),
                        values=(
                            cliente["id_cliente"],
                            cliente["identificacion"],
                            nombre_completo,
                            cliente["telefono"],
                            cliente["direccion"] or "No registrada",
                            cliente["tipo_cliente"] or "No especificado"
                        )
                    )


                if clientes:
                    etiqueta_estado.config(
                        text=f"{len(clientes)} cliente(s) desactivado(s).",
                        fg=COLOR_AZUL_SECUNDARIO
                    )
                else:
                    etiqueta_estado.config(
                        text="No se encontraron clientes desactivados.",
                        fg=COLOR_TEXTO_SUAVE
                    )

            except mysql.connector.Error as error:
                messagebox.showerror(
                    "Error de base de datos",
                    f"No se pudieron cargar los clientes.\n\n{error}",
                    parent=gestion
                )

            finally:
                if cursor is not None:
                    cursor.close()

                if conexion is not None and conexion.is_connected():
                    conexion.close()

        # Actualizar selección al elegir una fila
        def seleccionar_cliente(evento=None):
            seleccion = tabla.selection()

            if not seleccion:
                cliente_actual["id"] = None
                return

            cliente_actual["id"] = int(seleccion[0])

        tabla.bind("<<TreeviewSelect>>", seleccionar_cliente)

        # Búsqueda automática al escribir
        def buscar_automaticamente(evento=None):
            cargar_clientes(entrada_busqueda.get())

        entrada_busqueda.bind(
            "<KeyRelease>",
            buscar_automaticamente
        )

        # Limpiar búsqueda y volver a mostrar todos
        def limpiar_busqueda():
            entrada_busqueda.delete(0, tk.END)
            cargar_clientes()
            entrada_busqueda.focus_set()

        # Recuperar cliente seleccionado
        def recuperar_cliente():
            seleccion = tabla.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selecciona un cliente",
                    "Selecciona un cliente de la tabla para recuperarlo.",
                    parent=gestion
                )
                return

            id_cliente = int(seleccion[0])

            confirmar = messagebox.askyesno(
                "Confirmar recuperación",
                "¿Deseas recuperar al cliente seleccionado?\n\n"
                "Volverá a aparecer en el directorio de clientes activos.",
                parent=gestion
            )

            if not confirmar:
                return

            conexion = None
            cursor = None

            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()

                cursor.execute("""
                    UPDATE Clientes
                    SET estado = 0
                    WHERE id_cliente = %s
                      AND estado = 1
                """, (id_cliente,))

                if cursor.rowcount == 0:
                    conexion.rollback()

                    messagebox.showwarning(
                        "Cliente no disponible",
                        "El cliente ya fue recuperado o su estado cambió.",
                        parent=gestion
                    )

                    cargar_clientes(entrada_busqueda.get())
                    return

                conexion.commit()

                messagebox.showinfo(
                    "Recuperación exitosa",
                    "El cliente se recuperó correctamente.",
                    parent=gestion
                )

                cargar_clientes(entrada_busqueda.get())
                actualizar_dashboard()

            except mysql.connector.Error as error:
                if conexion is not None:
                    conexion.rollback()

                messagebox.showerror(
                    "Error de base de datos",
                    f"No se pudo recuperar al cliente.\n\n{error}",
                    parent=gestion
                )

            finally:
                if cursor is not None:
                    cursor.close()

                if conexion is not None and conexion.is_connected():
                    conexion.close()

        # Botones inferiores
        botones = tk.Frame(
            panel,
            bg=COLOR_PANEL
        )
        botones.pack(fill="x", pady=(10, 0))

        crear_boton(
            fila_busqueda,
            "Limpiar",
            limpiar_busqueda,
            COLOR_AZUL_SECUNDARIO,
            COLOR_AZUL_HOVER
        ).pack(side="right")

        crear_boton(
            botones,
            "Recuperar cliente",
            recuperar_cliente,
            COLOR_AZUL,
            COLOR_AZUL_HOVER
        ).pack(side="left")

        crear_boton(
            botones,
            "Cerrar",
            gestion.destroy,
            COLOR_NARANJA,
            COLOR_NARANJA_HOVER
        ).pack(side="right")

        # Cargar todos los clientes al abrir la ventana
        cargar_clientes()

        entrada_busqueda.focus_set()

    
    # ========================================================
    # ENCABEZADO DEL DASHBOARD
    # ========================================================

    crear_encabezado(
        ventana,
        "Centro de clientes",
        "Administra los registros y la información de tus clientes."
    )

    # ========================================================
    # PIE DE VENTANA
    # CREARLO ANTES DEL CUERPO PRINCIPAL
    # ========================================================

    pie_ventana = tk.Frame(
        ventana,
        bg=COLOR_AZUL,
        height=55
    )
    pie_ventana.pack(
        side="bottom",
        fill="x"
    )
    pie_ventana.pack_propagate(False)

    # Línea naranja superior
    tk.Frame(
        pie_ventana,
        bg=COLOR_NARANJA,
        height=4
    ).pack(
        side="top",
        fill="x"
    )

    # Texto del pie
    tk.Label(
        pie_ventana,
        text="Papelería Luna | Gestión de clientes",
        font=(FUENTE, 9),
        bg=COLOR_AZUL,
        fg="#cbd5e1"
    ).pack(
        side="left",
        padx=25
    )

    # Botón para regresar al menú
    tk.Button(
        pie_ventana,
        text="Volver al menú",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_NARANJA,
        fg=COLOR_TEXTO,
        activebackground=COLOR_NARANJA_HOVER,
        activeforeground="#ffffff",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=18,
        pady=6,
        command=ventana.destroy
    ).pack(
        side="right",
        padx=25
    )

    # ========================================================
    # CUERPO PRINCIPAL
    # ========================================================

    cuerpo = tk.Frame(
        ventana,
        bg=COLOR_FONDO
    )
    cuerpo.pack(
        side="top",
        fill="both",
        expand=True,
        padx=22,
        pady=16
    )


    # ========================================================
    # TARJETAS DE INDICADORES
    # ========================================================

    tarjetas_stats = tk.Frame(cuerpo, bg=COLOR_FONDO)
    tarjetas_stats.pack(fill="x", pady=(0, 15))

    def crear_indicador(padre, titulo, descripcion, color):
        tarjeta = tk.Frame(
            padre,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1,
            padx=16,
            pady=12
        )

        tk.Frame(
            tarjeta,
            bg=color,
            width=5
        ).pack(side="left", fill="y", padx=(0, 12))

        contenido = tk.Frame(tarjeta, bg=COLOR_PANEL)
        contenido.pack(side="left", fill="both", expand=True)

        tk.Label(
            contenido,
            text=titulo,
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        ).pack(anchor="w")

        numero = tk.Label(
            contenido,
            text="—",
            font=(FUENTE, 22, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_AZUL
        )
        numero.pack(anchor="w", pady=2)

        tk.Label(
            contenido,
            text=descripcion,
            font=(FUENTE, 8),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        ).pack(anchor="w")

        return tarjeta, numero

    tarjeta_activos, numero_activos = crear_indicador(
        tarjetas_stats,
        "CLIENTES ACTIVOS",
        "Registros disponibles",
        COLOR_AZUL
    )

    tarjeta_frecuentes, numero_frecuentes = crear_indicador(
        tarjetas_stats,
        "FRECUENTES / VIP",
        "Clientes especiales",
        COLOR_AZUL_SECUNDARIO
    )

    tarjeta_empresas, numero_empresas = crear_indicador(
        tarjetas_stats,
        "EMPRESAS",
        "Clientes empresariales",
        COLOR_NARANJA
    )

    tarjeta_activos.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 7)
    )

    tarjeta_frecuentes.pack(
        side="left",
        fill="both",
        expand=True,
        padx=7
    )

    tarjeta_empresas.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(7, 0)
    )

    # ========================================================
    # DIRECTORIO PRINCIPAL
    # ========================================================

    panel_directorio = crear_panel(cuerpo, 16)
    panel_directorio.pack(
        fill="both",
        expand=True,
        pady=(0, 5)
    )

    fila_titulo = tk.Frame(panel_directorio, bg=COLOR_PANEL)
    fila_titulo.pack(fill="x", pady=(0, 12))

    encabezado_directorio = tk.Frame(
        fila_titulo,
        bg=COLOR_PANEL
    )
    encabezado_directorio.pack(
        side="left",
        fill="x",
        expand=True
    )

    tk.Label(
        encabezado_directorio,
        text="Directorio de clientes",
        font=(FUENTE, 15, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_AZUL
    ).pack(anchor="w")

    tk.Label(
        encabezado_directorio,
        text="Busca, filtra y consulta los registros activos.",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE
    ).pack(anchor="w", pady=(3, 0))

    crear_boton(
        fila_titulo,
        "Registrar cliente",
        registrar_cliente,
        COLOR_AZUL,
        COLOR_AZUL_HOVER
    ).pack(side="right", padx=(10, 0))

    # ========================================================
    # FILTROS
    # ========================================================

    barra_filtros = tk.Frame(
        panel_directorio,
        bg=COLOR_PANEL
    )
    barra_filtros.pack(fill="x", pady=(0, 12))

    entrada_filtro = tk.Entry(
        barra_filtros,
        font=(FUENTE, 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        insertbackground=COLOR_TEXTO,
        relief="solid",
        bd=1,
        highlightthickness=2,
        highlightbackground=COLOR_BORDE,
        highlightcolor=COLOR_NARANJA
    )

    entrada_filtro.pack(
        side="left",
        fill="x",
        expand=True,
        ipady=7,
        padx=(0, 10)
    )

    entrada_filtro.insert(0, PLACEHOLDER_BUSQUEDA)
    entrada_filtro.config(fg=COLOR_TEXTO_SUAVE)

    filtro_tipo = tk.StringVar(
        master=ventana,
        value="Todos los tipos"
    )

    combo_filtro = ttk.Combobox(
        barra_filtros,
        textvariable=filtro_tipo,
        values=[
            "Todos los tipos",
            "Cliente particular",
            "Empresa",
            "Cliente frecuente",
            "Cliente VIP"
        ],
        state="readonly",
        width=22
    )

    combo_filtro.pack(side="left", padx=(0, 10))
    combo_filtro.set("Todos los tipos")

    # ========================================================
    # PIE DEL DIRECTORIO: RESULTADOS Y BOTONES
    # ========================================================
    pie = tk.Frame(
        panel_directorio,
        bg=COLOR_PANEL
    )

    pie.pack(
        side="bottom",
        fill="x",
        pady=(10, 5)
    )

    etiqueta_resultados = tk.Label(
        pie,
        text="Cargando registros...",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE
    )

    etiqueta_resultados.pack(
        side="left",
        padx=(0, 10)
    )

    boton_recuperar = crear_boton(
        pie,
        "Recuperar cliente",
        eliminar_cliente,
        COLOR_NARANJA,
        COLOR_NARANJA_HOVER
    )
    boton_recuperar.pack(
        side="right",
        padx=(8, 5),
        pady=5
    )

    boton_modificar = crear_boton(
        pie,
        "Modificar",
        lambda: modificar_seleccionado(),
        COLOR_AZUL,
        COLOR_AZUL_HOVER
    )
    boton_modificar.pack(
        side="right",
        padx=(8, 0),
        pady=5
    )

    # ========================================================
    # TABLA PRINCIPAL: UNA SOLA INSTANCIA
    # ========================================================
    marco_tabla = tk.Frame(
        panel_directorio,
        bg=COLOR_PANEL
    )

    marco_tabla.pack(
        side="top",
        fill="both",
        expand=True,
        pady=(0, 5)
    )

    tabla_principal = crear_tabla_clientes(
        marco_tabla,
        7
    )


    # ========================================================
    # FILTRAR REGISTROS
    # ========================================================
    def aplicar_filtros(event=None):
        texto = entrada_filtro.get().strip().casefold()
        tipo_seleccionado = filtro_tipo.get().strip().casefold()

        # Limpiar la tabla antes de mostrar los resultados
        for elemento in tabla_principal.get_children():
            tabla_principal.delete(elemento)

        encontrados = []

        for cliente in clientes_cache:
            nombre = str(cliente.get("nombre") or "").strip()
            apellidos = str(cliente.get("apellidos") or "").strip()
            identificacion = str(
                cliente.get("identificacion") or ""
            ).strip()
            telefono = str(cliente.get("telefono") or "").strip()
            tipo_cliente = str(
                cliente.get("tipo_cliente") or ""
            ).strip()

            nombre_completo = f"{nombre} {apellidos}".casefold()

            # Buscar por nombre, apellidos, identificación o teléfono
            coincide_texto = (
                not texto
                or texto in nombre_completo
                or texto in nombre.casefold()
                or texto in apellidos.casefold()
                or texto in identificacion.casefold()
                or texto in telefono.casefold()
            )

            # Filtrar por tipo de cliente
            coincide_tipo = (
                tipo_seleccionado == "todos los tipos"
                or tipo_cliente.casefold() == tipo_seleccionado
            )

            if coincide_texto and coincide_tipo:
                encontrados.append(cliente)

        # Mostrar los resultados filtrados
        for cliente in encontrados:
            tabla_principal.insert(
                "",
                "end",
                values=(
                    cliente.get("id_cliente", ""),
                    cliente.get("identificacion", ""),
                    cliente.get("nombre", ""),
                    cliente.get("apellidos", ""),
                    cliente.get("telefono", ""),
                    cliente.get("tipo_cliente", "")
                )
            )

        etiqueta_resultados.config(
            text=(
                f"Mostrando {len(encontrados)} de "
                f"{len(clientes_cache)} clientes activos."
            ),
            fg=COLOR_TEXTO_SUAVE
        )

    def activar_busqueda(event=None):
        if entrada_filtro.get() == PLACEHOLDER_BUSQUEDA:
            entrada_filtro.delete(0, tk.END)
            entrada_filtro.config(fg=COLOR_TEXTO)

    def restaurar_placeholder(event=None):
        if not entrada_filtro.get().strip():
            entrada_filtro.insert(0, PLACEHOLDER_BUSQUEDA)
            entrada_filtro.config(fg=COLOR_TEXTO_SUAVE)

    

        aplicar_filtros()

    def limpiar_filtros():
        # Limpiar el campo de búsqueda
        entrada_filtro.delete(0, tk.END)
        entrada_filtro.insert(0, PLACEHOLDER_BUSQUEDA)
        entrada_filtro.config(fg=COLOR_TEXTO_SUAVE)

        # Restablecer el filtro de tipo
        filtro_tipo.set("Todos los tipos")

        # Mostrar nuevamente todos los clientes activos
        aplicar_filtros()

        entrada_filtro.focus_set()

    crear_boton(
        barra_filtros,
        "Limpiar",
        limpiar_filtros,
        COLOR_NARANJA,
        COLOR_NARANJA_HOVER
    ).pack(side="right", padx=(10, 0))

    entrada_filtro.bind("<FocusIn>", activar_busqueda)
    entrada_filtro.bind("<FocusOut>", restaurar_placeholder)
    entrada_filtro.bind("<KeyRelease>", aplicar_filtros)

    combo_filtro.bind(
        "<<ComboboxSelected>>",
        aplicar_filtros
    )

    # ========================================================
    # SELECCIONAR CLIENTE PARA MODIFICAR
    # ========================================================

    def modificar_seleccionado(event=None):
        seleccion = tabla_principal.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona un cliente",
                "Selecciona un registro de la tabla para modificarlo.",
                parent=ventana
            )
            return

        valores = tabla_principal.item(
            seleccion[0],
            "values"
        )

        if not valores:
            return

        identificacion = valores[1]

        modificar_cliente(identificacion)

    tabla_principal.bind(
        "<Double-1>",
        modificar_seleccionado
    )

    # ========================================================
    # ACTUALIZAR DASHBOARD
    # ========================================================

    def actualizar_dashboard():
        nonlocal clientes_cache

        try:
            clientes_cache = obtener_clientes_activos()

            total_activos = len(clientes_cache)

            total_frecuentes = sum(
                1 for cliente in clientes_cache
                if (
                    cliente.get("tipo_cliente") or ""
                ).strip().lower()
                in ("cliente frecuente", "cliente vip")
            )

            total_empresas = sum(
                1 for cliente in clientes_cache
                if (
                    cliente.get("tipo_cliente") or ""
                ).strip().lower() == "empresa"
            )

            numero_activos.config(text=str(total_activos))
            numero_frecuentes.config(text=str(total_frecuentes))
            numero_empresas.config(text=str(total_empresas))

            aplicar_filtros()

        except mysql.connector.Error as error:
            etiqueta_resultados.config(
                text="No se pudieron cargar los registros.",
                fg=COLOR_ROJO
            )

            messagebox.showerror(
                "Error de MySQL",
                f"No se pudo actualizar el directorio.\n\n{error}",
                parent=ventana
            )

    # ========================================================
    # REGRESAR AL MENÚ
    # ========================================================

    # Carga inicial
    actualizar_dashboard()

    if ventana_independiente:
        ventana.mainloop()