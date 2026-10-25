# empleado.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error



# ============================================================
# TEMA COMPARTIDO - PAPELERÍA LUNA
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
COLOR_PRINCIPAL = COLORES["AZUL"]
COLOR_PRINCIPAL_HOVER = COLORES["AZUL_SECUNDARIO"]
COLOR_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
COLOR_ACENTO = COLORES["NARANJA"]
COLOR_ACENTO_HOVER = COLORES["NARANJA_HOVER"]
COLOR_TEXTO = COLORES["TEXTO"]
COLOR_TEXTO_SUAVE = COLORES["TEXTO_SUAVE"]
COLOR_BORDE = COLORES["BORDE"]
COLOR_ENTRADA = COLORES["ENTRADA"]
COLOR_SELECCION = COLORES["SELECCION"]
COLOR_ROJO = COLORES["ROJO"]
COLOR_ROJO_HOVER = COLORES["ROJO_HOVER"]

# Color semántico para identificar empleados activos.
COLOR_VERDE = "#10B981"

FUENTE = "Arial"


def actualizar_colores_iniciales():
    global TEMA_ACTUAL, COLORES
    global COLOR_FONDO, COLOR_PANEL
    global COLOR_PRINCIPAL, COLOR_PRINCIPAL_HOVER
    global COLOR_SECUNDARIO, COLOR_ACENTO, COLOR_ACENTO_HOVER
    global COLOR_TEXTO, COLOR_TEXTO_SUAVE, COLOR_BORDE
    global COLOR_ENTRADA, COLOR_SELECCION
    global COLOR_ROJO, COLOR_ROJO_HOVER

    TEMA_ACTUAL = obtener_tema_actual()
    COLORES = obtener_colores(TEMA_ACTUAL)

    COLOR_FONDO = COLORES["FONDO"]
    COLOR_PANEL = COLORES["PANEL"]
    COLOR_PRINCIPAL = COLORES["AZUL"]
    COLOR_PRINCIPAL_HOVER = COLORES["AZUL_SECUNDARIO"]
    COLOR_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
    COLOR_ACENTO = COLORES["NARANJA"]
    COLOR_ACENTO_HOVER = COLORES["NARANJA_HOVER"]
    COLOR_TEXTO = COLORES["TEXTO"]
    COLOR_TEXTO_SUAVE = COLORES["TEXTO_SUAVE"]
    COLOR_BORDE = COLORES["BORDE"]
    COLOR_ENTRADA = COLORES["ENTRADA"]
    COLOR_SELECCION = COLORES["SELECCION"]
    COLOR_ROJO = COLORES["ROJO"]
    COLOR_ROJO_HOVER = COLORES["ROJO_HOVER"]


# ============================================================
# CONEXIÓN A MYSQL
# ============================================================
def conectar_bd():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="Papeleria_Luna"
        )
    except Error as error:
        messagebox.showerror(
            "Error de conexión",
            f"No se pudo conectar a la base de datos.\n\n{error}"
        )
        return None


# ============================================================
# VENTANA PRINCIPAL
# ============================================================
def abrir_empleados(raiz=None, usuario=None):

        # ========================================================
    # CARGAR EL TEMA ACTUAL AL ABRIR EMPLEADOS
    # ========================================================
    global TEMA_ACTUAL, COLORES
    global COLOR_FONDO, COLOR_PANEL
    global COLOR_PRINCIPAL, COLOR_SECUNDARIO
    global COLOR_NARANJA, COLOR_NARANJA_HOVER
    global COLOR_TEXTO, COLOR_TEXTO_SUAVE
    global COLOR_BORDE, COLOR_ROJO, COLOR_ROJO_HOVER
    global COLOR_ENTRADA, COLOR_SELECCION

    TEMA_ACTUAL = obtener_tema_actual()
    COLORES = obtener_colores(TEMA_ACTUAL)

    COLOR_FONDO = COLORES["FONDO"]
    COLOR_PANEL = COLORES["PANEL"]
    COLOR_PRINCIPAL = COLORES["AZUL"]
    COLOR_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
    COLOR_NARANJA = COLORES["NARANJA"]
    COLOR_NARANJA_HOVER = COLORES["NARANJA_HOVER"]
    COLOR_TEXTO = COLORES["TEXTO"]
    COLOR_TEXTO_SUAVE = COLORES["TEXTO_SUAVE"]
    COLOR_BORDE = COLORES["BORDE"]
    COLOR_ROJO = COLORES["ROJO"]
    COLOR_ROJO_HOVER = COLORES["ROJO_HOVER"]
    COLOR_ENTRADA = COLORES["ENTRADA"]
    COLOR_SELECCION = COLORES["SELECCION"]
    
    # ========================================================
    # PERMISOS SEGÚN usuarios.rango
    # Administrador y gerente pueden administrar empleados.
    # ========================================================
    rango_usuario = (
        str(usuario.get("rango") or "").strip().casefold()
        if isinstance(usuario, dict)
        else ""
    )

    puede_administrar = rango_usuario in (
        "administrador",
        "gerente"
    )

    print("Usuario recibido:", usuario)
    print("Rango detectado:", rango_usuario)
    print("Puede administrar:", puede_administrar)

    if raiz is None:
        ventana = tk.Tk()
    else:
        ventana = tk.Toplevel(raiz)

    
    # ========================================================
    # VENTANAS REGISTRADAS PARA EL CAMBIO DE TEMA
    # ========================================================
    ventanas_tema = [ventana]
    observador_registrado = False

    def registrar_ventana_tema(ventana_hija):
        """Registra una ventana secundaria para recolorearla."""

        nonlocal observador_registrado

        if ventana_hija not in ventanas_tema:
            ventanas_tema.append(ventana_hija)

        def al_destruir(event):
            nonlocal observador_registrado

            if event.widget is not ventana_hija:
                return

            if ventana_hija in ventanas_tema:
                ventanas_tema.remove(ventana_hija)

            if not ventanas_tema and observador_registrado:
                eliminar_observador(aplicar_tema_empleados)
                observador_registrado = False

        ventana_hija.bind("<Destroy>", al_destruir, add="+")

    def configurar_estilos_tema(ventana_estilo=None):
        """Actualiza los estilos compartidos de ttk."""

        estilo = (
            ttk.Style(ventana_estilo)
            if ventana_estilo is not None
            else ttk.Style()
        )

        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "Luna.Treeview",
            background=COLOR_PANEL,
            fieldbackground=COLOR_PANEL,
            foreground=COLOR_TEXTO,
            rowheight=32,
            font=(FUENTE, 10)
        )

        estilo.configure(
            "Luna.Treeview.Heading",
            background=COLOR_PRINCIPAL,
            foreground="#FFFFFF",
            font=(FUENTE, 10, "bold"),
            relief="flat",
            padding=(8, 10)
        )

        estilo.map(
            "Luna.Treeview",
            background=[("selected", COLOR_SELECCION)],
            foreground=[("selected", COLOR_TEXTO)]
        )

        estilo.map(
            "Luna.Treeview.Heading",
            background=[("active", COLOR_PRINCIPAL_HOVER)],
            foreground=[("active", "#FFFFFF")]
        )

        estilo.configure(
            "Luna.TCombobox",
            fieldbackground=COLOR_ENTRADA,
            background=COLOR_PANEL,
            foreground=COLOR_TEXTO,
            arrowcolor=COLOR_TEXTO
        )

        estilo.map(
            "Luna.TCombobox",
            fieldbackground=[
                ("readonly", COLOR_ENTRADA),
                ("disabled", COLOR_FONDO)
            ],
            foreground=[
                ("readonly", COLOR_TEXTO),
                ("disabled", COLOR_TEXTO_SUAVE)
            ]
        )

        estilo.configure(
            "Vertical.TScrollbar",
            background=COLOR_PANEL,
            troughcolor=COLOR_FONDO,
            arrowcolor=COLOR_TEXTO
        )

        estilo.configure(
            "Horizontal.TScrollbar",
            background=COLOR_PANEL,
            troughcolor=COLOR_FONDO,
            arrowcolor=COLOR_TEXTO
        )

    
    
    def recolorear_widget(widget, anteriores):
        """Actualiza los colores de los widgets al cambiar de tema."""

        try:
            clase = widget.winfo_class()
            opciones = widget.configure()

            # Colores de fondo que pertenecen al tema.
            equivalencias_fondo = {
                anteriores["FONDO"]: COLOR_FONDO,
                anteriores["PANEL"]: COLOR_PANEL,
                anteriores["AZUL"]: COLOR_PRINCIPAL,
                anteriores["AZUL_SECUNDARIO"]: COLOR_SECUNDARIO,
                anteriores["NARANJA"]: COLOR_ACENTO,
                anteriores["NARANJA_HOVER"]: COLOR_ACENTO_HOVER,
                anteriores["ROJO"]: COLOR_ROJO,
                anteriores["ROJO_HOVER"]: COLOR_ROJO_HOVER,
                anteriores["ENTRADA"]: COLOR_ENTRADA,
                anteriores["SELECCION"]: COLOR_SELECCION,
            }

            # Actualizar el fondo cuando coincide con el tema anterior.
            if "background" in opciones:
                fondo_actual = widget.cget("background")

                if fondo_actual in equivalencias_fondo:
                    widget.configure(
                        background=equivalencias_fondo[fondo_actual]
                    )

                        # Actualizar también los bordes y resaltados.
            equivalencias_bordes = {
                anteriores["BORDE"]: COLOR_BORDE,
                anteriores["FONDO"]: COLOR_FONDO,
                anteriores["NARANJA"]: COLOR_ACENTO,
            }

            for opcion in (
                "highlightbackground",
                "highlightcolor",
                "highlightthickness"
            ):
                if opcion in opciones and opcion != "highlightthickness":
                    valor_actual = widget.cget(opcion)

                    if valor_actual in equivalencias_bordes:
                        widget.configure(
                            **{
                                opcion: equivalencias_bordes[valor_actual]
                            }
                        )

            # Los campos de texto siempre usan los colores de entrada.
            if clase in ("Entry", "Text", "Spinbox"):
                widget.configure(
                    background=COLOR_ENTRADA,
                    foreground=COLOR_TEXTO,
                    insertbackground=COLOR_TEXTO,
                    selectbackground=COLOR_SELECCION,
                    selectforeground=COLOR_TEXTO,
                    highlightbackground=COLOR_BORDE,
                    highlightcolor=COLOR_ACENTO
                )

            # Mantener el efecto de los botones al pasar el cursor.
            if clase == "Button":
                fondo_boton = widget.cget("background")

                if fondo_boton == COLOR_PRINCIPAL:
                    widget.configure(
                        activebackground=COLOR_PRINCIPAL_HOVER
                    )
                elif fondo_boton == COLOR_ACENTO:
                    widget.configure(
                        activebackground=COLOR_ACENTO_HOVER
                    )
                elif fondo_boton == COLOR_ROJO:
                    widget.configure(
                        activebackground=COLOR_ROJO_HOVER
                    )

        except (tk.TclError, KeyError, TypeError):
            pass

        # Procesar también los elementos que están dentro de cada widget.
        try:
            for hijo in widget.winfo_children():
                recolorear_widget(hijo, anteriores)
        except tk.TclError:
            pass

    def aplicar_tema_empleados(nuevos_colores):
        """Aplica el nuevo tema a todas las ventanas del módulo."""

        global TEMA_ACTUAL, COLORES
        global COLOR_FONDO, COLOR_PANEL
        global COLOR_PRINCIPAL, COLOR_PRINCIPAL_HOVER
        global COLOR_SECUNDARIO, COLOR_ACENTO, COLOR_ACENTO_HOVER
        global COLOR_TEXTO, COLOR_TEXTO_SUAVE, COLOR_BORDE
        global COLOR_ENTRADA, COLOR_SELECCION
        global COLOR_ROJO, COLOR_ROJO_HOVER

        anteriores = COLORES.copy()
        COLORES = nuevos_colores.copy()

        COLOR_FONDO = COLORES["FONDO"]
        COLOR_PANEL = COLORES["PANEL"]
        COLOR_PRINCIPAL = COLORES["AZUL"]
        COLOR_PRINCIPAL_HOVER = COLORES["AZUL_SECUNDARIO"]
        COLOR_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
        COLOR_ACENTO = COLORES["NARANJA"]
        COLOR_ACENTO_HOVER = COLORES["NARANJA_HOVER"]
        COLOR_TEXTO = COLORES["TEXTO"]
        COLOR_TEXTO_SUAVE = COLORES["TEXTO_SUAVE"]
        COLOR_BORDE = COLORES["BORDE"]
        COLOR_ENTRADA = COLORES["ENTRADA"]
        COLOR_SELECCION = COLORES["SELECCION"]
        COLOR_ROJO = COLORES["ROJO"]
        COLOR_ROJO_HOVER = COLORES["ROJO_HOVER"]
        TEMA_ACTUAL = obtener_tema_actual()

        configurar_estilos_tema(ventana)

        for ventana_abierta in ventanas_tema[:]:
            try:
                if not ventana_abierta.winfo_exists():
                    ventanas_tema.remove(ventana_abierta)
                    continue

                # Cambiar primero el fondo de la ventana.
                ventana_abierta.configure(bg=COLOR_FONDO)

                # Actualizar sus widgets.
                recolorear_widget(ventana_abierta, anteriores)

            except tk.TclError:
                continue

        # Refresca los estilos de ttk después de recorrer las ventanas.
        configurar_estilos_tema(ventana)

    
    def cerrar_observador_empleados(event=None):
        nonlocal observador_registrado

        if event is not None and event.widget is not ventana:
            return

        if ventana in ventanas_tema:
            ventanas_tema.remove(ventana)

        if not ventanas_tema and observador_registrado:
            eliminar_observador(aplicar_tema_empleados)
            observador_registrado = False

    configurar_estilos_tema(ventana)
    registrar_observador(aplicar_tema_empleados)
    observador_registrado = True

    ventana.bind(
        "<Destroy>",
        cerrar_observador_empleados,
        add="+"
    )


    ventana.title("Gestión de empleados")
    ventana.geometry("1050x700")
    ventana.minsize(850, 600)
    ventana.configure(bg=COLOR_FONDO)

    if raiz is not None:
        ventana.transient(raiz)

    ventana.update_idletasks()
    ancho = 1050
    alto = 700
    x = (ventana.winfo_screenwidth() - ancho) // 2
    y = (ventana.winfo_screenheight() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ========================================================
    # CONSULTAR BASE DE DATOS
    # ========================================================
    def consultar(sql, valores=()):
        conexion = conectar_bd()

        if conexion is None:
            return None

        cursor = None

        try:
            cursor = conexion.cursor()
            cursor.execute(sql, valores)
            return cursor.fetchall()

        except Error as error:
            messagebox.showerror(
                "Error de consulta",
                f"No se pudo realizar la consulta.\n\n{error}",
                parent=ventana
            )
            return None

        finally:
            if cursor is not None:
                cursor.close()

            if conexion.is_connected():
                conexion.close()

    # ========================================================
    # VALIDAR PERMISOS ADMINISTRATIVOS
    # ========================================================
    def validar_permiso(mensaje="No tienes permisos para realizar esta operación.",
                        parent=None):

        if puede_administrar:
            return True

        messagebox.showwarning(
            "Acceso restringido",
            mensaje,
            parent=parent or ventana
        )
        return False

    # ========================================================
    # EJECUTAR INSERT, UPDATE, ETC.
    # Las operaciones que modifican datos requieren permisos.
    # ========================================================
    def ejecutar(sql, valores=(), requiere_admin=False, parent=None):

        if requiere_admin and not validar_permiso(parent=parent):
            return False

        conexion = conectar_bd()

        if conexion is None:
            return False

        cursor = None

        try:
            cursor = conexion.cursor()
            cursor.execute(sql, valores)
            conexion.commit()
            return True

        except Error as error:
            conexion.rollback()

            if getattr(error, "errno", None) == 1062:
                mensaje = (
                    "La identificación ingresada ya pertenece "
                    "a otro empleado. Utiliza una identificación diferente."
                )
                titulo = "Identificación duplicada"
            else:
                mensaje = (
                    "No se pudo completar la operación.\n\n"
                    f"{error}"
                )
                titulo = "Error de operación"

            messagebox.showerror(
                titulo,
                mensaje,
                parent=parent or ventana
            )
            return False

        finally:
            if cursor is not None:
                cursor.close()

            if conexion.is_connected():
                conexion.close()

    # ========================================================
    # ENCABEZADO PRINCIPAL
    # ========================================================
    encabezado = tk.Frame(
        ventana,
        bg=COLOR_PRINCIPAL,
        height=115
    )
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA / EMPLEADOS",
        font=(FUENTE, 9, "bold"),
        bg=COLOR_PRINCIPAL,
        fg=COLOR_ACENTO
    ).pack(
        anchor="w",
        padx=28,
        pady=(10, 0)
    )

    tk.Label(
        encabezado,
        text="Gestión de empleados",
        font=(FUENTE, 22, "bold"),
        bg=COLOR_PRINCIPAL,
        fg="white"
    ).pack(
        anchor="w",
        padx=28,
        pady=(2, 1)
    )

    tk.Label(
        encabezado,
        text="Consulta y administra la información del personal",
        font=(FUENTE, 10),
        bg=COLOR_PRINCIPAL,
        fg="white"
    ).pack(
        anchor="w",
        padx=29,
        pady=(0, 8)
    )

    tk.Frame(
        encabezado,
        bg=COLOR_ACENTO,
        height=5
    ).pack(
        side="bottom",
        fill="x"
    )

    # ========================================================
    # TEXTO DE AYUDA PARA LA BÚSQUEDA
    # ========================================================
    tk.Label(
        ventana,
        text="Busca empleados por nombre, apellido o identificación:",
        font=(FUENTE, 9),
        bg=COLOR_FONDO,
        fg=COLOR_TEXTO_SUAVE
    ).pack(
        anchor="w",
        padx=25,
        pady=(12, 0)
    )

    # ========================================================
    # BARRA DE BÚSQUEDA
    # ========================================================
    barra = tk.Frame(
        ventana,
        bg=COLOR_FONDO
    )
    barra.pack(
        fill="x",
        padx=25,
        pady=(6, 18)
    )

    
    entrada_busqueda = tk.Entry(
        barra,
        font=(FUENTE, 11),
        bg=COLOR_ENTRADA,
        fg=COLOR_TEXTO,
        insertbackground=COLOR_TEXTO,
        selectbackground=COLOR_SELECCION,
        selectforeground=COLOR_TEXTO,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=COLOR_BORDE,
        highlightcolor=COLOR_ACENTO
    )

    entrada_busqueda.pack(
        side="left",
        fill="x",
        expand=True,
        ipady=9,
        padx=(0, 12)
    )

    texto_busqueda = ""

    def limpiar_busqueda(event=None):
        if entrada_busqueda.get() == texto_busqueda:
            entrada_busqueda.delete(0, "end")

    def restaurar_busqueda(event=None):
        if not entrada_busqueda.get().strip():
            entrada_busqueda.insert(0, texto_busqueda)
            cargar_empleados()

    entrada_busqueda.bind("<FocusIn>", limpiar_busqueda)
    entrada_busqueda.bind("<FocusOut>", restaurar_busqueda)

    # ========================================================
    # TÍTULO DEL DIRECTORIO
    # ========================================================
    marco_titulo = tk.Frame(
        ventana,
        bg=COLOR_FONDO
    )
    marco_titulo.pack(
        fill="x",
        padx=25
    )

    tk.Label(
        marco_titulo,
        text="Personal registrado",
        font=(FUENTE, 15, "bold"),
        bg=COLOR_FONDO,
        fg=COLOR_TEXTO
    ).pack(side="left")

    etiqueta_total = tk.Label(
        marco_titulo,
        text="",
        font=(FUENTE, 10),
        bg=COLOR_FONDO,
        fg=COLOR_TEXTO_SUAVE
    )
    etiqueta_total.pack(side="right")

    # ========================================================
    # ÁREA DE FICHAS
    # ========================================================
    contenedor = tk.Frame(
        ventana,
        bg=COLOR_FONDO
    )
    contenedor.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(12, 10)
    )

    estilo_scroll = ttk.Style(ventana)
    estilo_scroll.theme_use("clam")

    contenedor_directorio = tk.Frame(
        contenedor,
        bg=COLOR_FONDO
    )
    contenedor_directorio.pack(
        fill="both",
        expand=True
    )

    lienzo = tk.Canvas(
        contenedor_directorio,
        bg=COLOR_FONDO,
        highlightthickness=0
    )

    estilo_scroll = ttk.Style(ventana)
    estilo_scroll.theme_use("clam")

    barra_vertical = ttk.Scrollbar(
        contenedor_directorio,
        orient="vertical",
        command=lienzo.yview
    )

    lienzo.configure(yscrollcommand=barra_vertical.set)

    lienzo.pack(
        side="left",
        fill="both",
        expand=True
    )

    barra_vertical.pack(
        side="right",
        fill="y"
    )

    marco_fichas = tk.Frame(
        lienzo,
        bg=COLOR_FONDO
    )

    ventana_fichas = lienzo.create_window(
        (0, 0),
        window=marco_fichas,
        anchor="nw"
    )

    def actualizar_area_desplazamiento(event=None):
        lienzo.configure(
            scrollregion=lienzo.bbox("all")
        )

    marco_fichas.bind(
        "<Configure>",
        actualizar_area_desplazamiento
    )

    lienzo.bind(
        "<Configure>",
        lambda event: lienzo.itemconfigure(
            ventana_fichas,
            width=event.width
        )
    )

    # ========================================================
    # CARGAR EMPLEADOS ACTIVOS
    # ========================================================
    def cargar_empleados(filtro=""):

        for widget in marco_fichas.winfo_children():
            widget.destroy()

        if filtro:
            sql = """
                SELECT id_empleado, identificacion, nombre, apellidos,
                       telefono, puesto, turno, salario, estado
                FROM Empleados
                WHERE estado = 0
                  AND (
                      nombre LIKE %s
                      OR apellidos LIKE %s
                      OR identificacion LIKE %s
                  )
                ORDER BY id_empleado ASC
            """
            patron = f"%{filtro}%"
            datos = consultar(sql, (patron, patron, patron))
        else:
            sql = """
                SELECT id_empleado, identificacion, nombre, apellidos,
                       telefono, puesto, turno, salario, estado
                FROM Empleados
                WHERE estado = 0
                ORDER BY id_empleado ASC
            """
            datos = consultar(sql)

        if datos is not None:
            datos = [
                empleado for empleado in datos
                if empleado[0] != 0
            ]

        if datos is None:
            etiqueta_total.config(
                text="No se pudo cargar la información"
            )
            return

        etiqueta_total.config(
            text=f"{len(datos)} empleado(s) activo(s)"
        )

        if not datos:
            tk.Label(
                marco_fichas,
                text="No se encontraron empleados.",
                font=(FUENTE, 12),
                bg=COLOR_FONDO,
                fg=COLOR_TEXTO_SUAVE
            ).grid(
                row=0,
                column=0,
                padx=20,
                pady=30
            )
            return

        for columna in range(2):
            marco_fichas.grid_columnconfigure(
                columna,
                weight=1,
                uniform="fichas"
            )

        for indice, empleado in enumerate(datos):
            fila = indice // 2
            columna = indice % 2

            ficha = tk.Frame(
                marco_fichas,
                bg=COLOR_PANEL,
                highlightbackground=COLOR_BORDE,
                highlightthickness=1
            )
            ficha.grid(
                row=fila,
                column=columna,
                sticky="nsew",
                padx=7,
                pady=7
            )

            tk.Label(
                ficha,
                text=f"{empleado[2]} {empleado[3]}",
                font=(FUENTE, 13, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO,
                anchor="w",
                wraplength=350
            ).pack(
                fill="x",
                padx=16,
                pady=(15, 8)
            )

            tk.Label(
                ficha,
                text=f"Identificación: {empleado[1] or 'No registrada'}",
                font=(FUENTE, 10),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO_SUAVE,
                anchor="w",
                wraplength=350
            ).pack(fill="x", padx=16, pady=3)

            tk.Label(
                ficha,
                text=f"Puesto: {empleado[5] or 'Sin asignar'}",
                font=(FUENTE, 10),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO_SUAVE,
                anchor="w"
            ).pack(fill="x", padx=16, pady=3)

            tk.Label(
                ficha,
                text=f"Teléfono: {empleado[4] or 'No registrado'}",
                font=(FUENTE, 10),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO_SUAVE,
                anchor="w"
            ).pack(fill="x", padx=16, pady=3)

            tk.Label(
                ficha,
                text=f"Turno: {empleado[6] or 'Sin asignar'}",
                font=(FUENTE, 10),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO_SUAVE,
                anchor="w"
            ).pack(fill="x", padx=16, pady=3)

            tk.Label(
                ficha,
                text="ACTIVO",
                font=(FUENTE, 9, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_VERDE,
                anchor="w"
            ).pack(fill="x", padx=16, pady=(5, 10))

            tk.Button(
                ficha,
                text="Ver ficha",
                font=(FUENTE, 10, "bold"),
                bg=COLOR_PRINCIPAL,
                fg="white",
                activebackground=COLOR_PRINCIPAL_HOVER,
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                pady=7,
                command=lambda e=empleado: seleccionar_empleado(*e)
            ).pack(
                fill="x",
                padx=16,
                pady=(0, 15)
            )

    # ========================================================
    # VER INFORMACIÓN DEL EMPLEADO
    # ========================================================
    def seleccionar_empleado(*datos):

        ventana_detalles = tk.Toplevel(ventana)
        registrar_ventana_tema(ventana_detalles)
        ventana_detalles.title("Ficha del empleado")
        ventana_detalles.geometry("540x680")
        ventana_detalles.minsize(540, 680)
        ventana_detalles.resizable(False, False)
        ventana_detalles.configure(bg=COLOR_FONDO)
        ventana_detalles.transient(ventana)

        ventana_detalles.update_idletasks()
        ancho = 540
        alto = 680
        x = (ventana_detalles.winfo_screenwidth() - ancho) // 2
        y = (ventana_detalles.winfo_screenheight() - alto) // 2
        ventana_detalles.geometry(f"{ancho}x{alto}+{x}+{y}")

        ventana_detalles.grab_set()

        # ----------------------------------------------------
        # ENCABEZADO
        # ----------------------------------------------------
        encabezado_detalles = tk.Frame(
            ventana_detalles,
            bg=COLOR_PRINCIPAL,
            height=115
        )
        encabezado_detalles.pack(fill="x")
        encabezado_detalles.pack_propagate(False)

        tk.Label(
            encabezado_detalles,
            text="PAPELERÍA LUNA / EMPLEADOS",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PRINCIPAL,
            fg=COLOR_ACENTO
        ).pack(
            anchor="w",
            padx=28,
            pady=(8, 0)
        )

        tk.Label(
            encabezado_detalles,
            text="Ficha del empleado",
            font=(FUENTE, 21, "bold"),
            bg=COLOR_PRINCIPAL,
            fg="white"
        ).pack(
            anchor="w",
            padx=28,
            pady=(5, 3)
        )

        tk.Label(
            encabezado_detalles,
            text="Información y administración del personal",
            font=(FUENTE, 10),
            bg=COLOR_PRINCIPAL,
            fg="white"
        ).pack(
            anchor="w",
            padx=29
        )

        tk.Frame(
            ventana_detalles,
            bg=COLOR_ACENTO,
            height=5
        ).pack(fill="x")

        # ----------------------------------------------------
        # CONTENIDO PRINCIPAL
        # ----------------------------------------------------
        contenido = tk.Frame(
            ventana_detalles,
            bg=COLOR_FONDO
        )
        contenido.pack(
            fill="both",
            expand=True,
            padx=24,
            pady=15
        )

        panel = tk.Frame(
            contenido,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="DATOS GENERALES",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_PRINCIPAL
        ).pack(
            anchor="w",
            padx=20,
            pady=(12, 5)
        )

        tk.Frame(
            panel,
            bg=COLOR_BORDE,
            height=1
        ).pack(fill="x", padx=20, pady=(0, 5))

        campos_detalle = [
            ("ID de empleado", datos[0]),
            ("Identificación", datos[1]),
            ("Nombre", datos[2]),
            ("Apellidos", datos[3]),
            ("Teléfono", datos[4]),
            ("Puesto", datos[5]),
            ("Turno", datos[6]),
            (
                "Salario",
                f"${float(datos[7]):,.2f}"
                if datos[7] is not None else "$0.00"
            ),
            ("Estado", "ACTIVO")
        ]

        for etiqueta, valor in campos_detalle:
            fila = tk.Frame(
                panel,
                bg=COLOR_PANEL
            )
            fila.pack(
                fill="x",
                padx=20,
                pady=4
            )

            tk.Label(
                fila,
                text=f"{etiqueta}:",
                font=(FUENTE, 9, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO,
                width=17,
                anchor="w"
            ).pack(side="left")

            tk.Label(
                fila,
                text=str(valor if valor is not None else ""),
                font=(FUENTE, 10),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO_SUAVE,
                anchor="w",
                justify="left",
                wraplength=220
            ).pack(
                side="left",
                fill="x",
                expand=True
            )

        # ----------------------------------------------------
        # BOTONES ADMINISTRATIVOS
        # Solo visibles para rangos 0 y 1.
        # ----------------------------------------------------
        botones = tk.Frame(
            ventana_detalles,
            bg=COLOR_FONDO
        )
        botones.pack(
            fill="x",
            padx=24,
            pady=(0, 20)
        )

        if puede_administrar:
            tk.Button(
                botones,
                text="Modificar",
                font=(FUENTE, 10, "bold"),
                bg=COLOR_PRINCIPAL,
                fg="white",
                activebackground=COLOR_PRINCIPAL_HOVER,
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                padx=15,
                pady=10,
                command=lambda: abrir_edicion_desde_ficha(
                    ventana_detalles,
                    datos
                )
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 5)
            )

            tk.Button(
                botones,
                text="Desactivar",
                font=(FUENTE, 10, "bold"),
                bg=COLOR_ROJO,
                fg="white",
                activebackground=COLOR_ROJO_HOVER,
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                padx=15,
                pady=10,
                command=lambda: desactivar_desde_ficha(
                    ventana_detalles,
                    datos[0]
                )
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=5
            )

        tk.Button(
            botones,
            text="Cerrar",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_ACENTO,
            fg="white",
            activebackground=COLOR_ACENTO_HOVER,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=10,
            command=ventana_detalles.destroy
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(5, 0) if puede_administrar else 0
        )

    # ========================================================
    # ABRIR EDICIÓN DESDE LA FICHA
    # ========================================================
    def abrir_edicion_desde_ficha(ficha, datos):

        if not validar_permiso(
            "No tienes permisos para modificar empleados.",
            ficha
        ):
            return

        ficha.destroy()
        abrir_formulario(datos)

    # ========================================================
    # DESACTIVAR DESDE LA FICHA
    # ========================================================
    def desactivar_desde_ficha(ficha, id_empleado):

        if not validar_permiso(
            "No tienes permisos para desactivar empleados.",
            ficha
        ):
            return

        ficha.destroy()
        desactivar_empleado(id_empleado)

    # ========================================================
    # REGISTRAR EMPLEADO
    # ========================================================
    def registrar_empleado():

        if not validar_permiso(
            "No tienes permisos para registrar empleados."
        ):
            return

        abrir_formulario()

    # ========================================================
    # REGISTRAR Y MODIFICAR EMPLEADO
    # ========================================================
    def abrir_formulario(datos=None):

        if not validar_permiso(
            "No tienes permisos para registrar ni modificar empleados."
        ):
            return

        es_edicion = datos is not None

        formulario = tk.Toplevel(ventana)
        registrar_ventana_tema(formulario)
        formulario.title(
            "Modificar empleado" if es_edicion else "Registrar empleado"
        )
        formulario.configure(bg=COLOR_FONDO)
        formulario.geometry("540x760")
        formulario.minsize(540, 760)
        formulario.resizable(False, True)
        formulario.transient(ventana)

        formulario.update_idletasks()
        ancho = 540
        alto = 760
        x = (formulario.winfo_screenwidth() - ancho) // 2
        y = (formulario.winfo_screenheight() - alto) // 2
        formulario.geometry(f"{ancho}x{alto}+{x}+{y}")

        formulario.grab_set()

        # ----------------------------------------------------
        # ENCABEZADO DEL FORMULARIO
        # ----------------------------------------------------
        encabezado_formulario = tk.Frame(
            formulario,
            bg=COLOR_PRINCIPAL,
            height=105
        )
        encabezado_formulario.pack(fill="x")
        encabezado_formulario.pack_propagate(False)

        tk.Label(
            encabezado_formulario,
            text="PAPELERÍA LUNA / EMPLEADOS",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PRINCIPAL,
            fg=COLOR_ACENTO
        ).pack(
            anchor="w",
            padx=25,
            pady=(7, 0)
        )

        tk.Label(
            encabezado_formulario,
            text="Modificar empleado" if es_edicion else "Registrar empleado",
            font=(FUENTE, 20, "bold"),
            bg=COLOR_PRINCIPAL,
            fg="white"
        ).pack(
            anchor="w",
            padx=25,
            pady=(4, 2)
        )

        tk.Label(
            encabezado_formulario,
            text=(
                "Actualiza la información del personal"
                if es_edicion
                else "Introduce los datos del nuevo empleado"
            ),
            font=(FUENTE, 9),
            bg=COLOR_PRINCIPAL,
            fg="white"
        ).pack(
            anchor="w",
            padx=26,
            pady=(0, 8)
        )

        tk.Frame(
            formulario,
            bg=COLOR_ACENTO,
            height=4
        ).pack(fill="x")

        # ----------------------------------------------------
        # PANEL PRINCIPAL
        # ----------------------------------------------------
        panel = tk.Frame(
            formulario,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        panel.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=(12, 8)
        )

        panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            panel,
            text="INFORMACIÓN DEL EMPLEADO",
            font=(FUENTE, 11, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_PRINCIPAL
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(16, 2)
        )

        tk.Label(
            panel,
            text="Completa los campos correspondientes",
            font=(FUENTE, 9),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=20,
            pady=(0, 12)
        )

        # ----------------------------------------------------
        # CAMPOS DEL FORMULARIO
        # ----------------------------------------------------
        campos = [
            ("Identificación", "identificacion"),
            ("Nombre", "nombre"),
            ("Apellidos", "apellidos"),
            ("Teléfono", "telefono"),
            ("Puesto", "puesto"),
            ("Turno", "turno"),
            ("Salario", "salario")
        ]

        opciones_puesto = [
            "Gerente",
            "Cajero",
            "Vendedor",
            "Encargado de inventario",
            "Auxiliar administrativo",
            "Almacenista"
        ]

        opciones_turno = [
            "Matutino",
            "Vespertino",
            "Mixto",
            "Tiempo completo"
        ]

        entradas = {}

        for fila, (etiqueta, clave) in enumerate(campos, start=2):

            grupo = tk.Frame(
                panel,
                bg=COLOR_PANEL
            )
            grupo.grid(
                row=fila,
                column=0,
                sticky="ew",
                padx=20,
                pady=5
            )
            grupo.grid_columnconfigure(0, weight=1)

            tk.Label(
                grupo,
                text=etiqueta,
                font=(FUENTE, 9, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO
            ).grid(
                row=0,
                column=0,
                sticky="w",
                pady=(0, 4)
            )

            if clave == "puesto":
                entrada = ttk.Combobox(
                    grupo,
                    font=(FUENTE, 10),
                    values=opciones_puesto,
                    state="readonly",
                    style="Luna.TCombobox"
                )

            elif clave == "turno":
                entrada = ttk.Combobox(
                    grupo,
                    font=(FUENTE, 10),
                    values=opciones_turno,
                    state="readonly",
                    style="Luna.TCombobox"
                )
                entrada.set("Matutino")

            else:
                entrada = tk.Entry(
                    grupo,
                    font=(FUENTE, 10),
                    bg=COLOR_ENTRADA,
                    fg=COLOR_TEXTO,
                    insertbackground=COLOR_TEXTO,
                    relief="solid",
                    bd=1,
                    highlightthickness=1,
                    highlightbackground=COLOR_BORDE,
                    highlightcolor=COLOR_ACENTO
                )

            entrada.grid(
                row=1,
                column=0,
                sticky="ew",
                ipady=5
            )

            entradas[clave] = entrada

        # ----------------------------------------------------
        # CARGAR DATOS PARA MODIFICAR
        # ----------------------------------------------------
        if es_edicion:

            valores_actuales = {
                "identificacion": datos[1],
                "nombre": datos[2],
                "apellidos": datos[3],
                "telefono": datos[4],
                "puesto": datos[5],
                "turno": datos[6],
                "salario": datos[7]
            }

            for clave, valor in valores_actuales.items():
                valor = str(valor if valor is not None else "")

                if isinstance(entradas[clave], ttk.Combobox):
                    entradas[clave].set(valor)
                else:
                    entradas[clave].insert(0, valor)

        # ----------------------------------------------------
        # GUARDAR REGISTRO O CAMBIOS
        # ----------------------------------------------------
        def guardar():

            if not validar_permiso(
                "No tienes permisos para guardar cambios en empleados.",
                formulario
            ):
                return

            identificacion = entradas["identificacion"].get().strip()
            nombre = entradas["nombre"].get().strip()
            apellidos = entradas["apellidos"].get().strip()
            telefono = entradas["telefono"].get().strip()
            puesto = entradas["puesto"].get().strip()
            turno = entradas["turno"].get().strip()
            salario_texto = entradas["salario"].get().strip()

            if not identificacion:
                messagebox.showwarning(
                    "Datos incompletos",
                    "La identificación es obligatoria.",
                    parent=formulario
                )
                entradas["identificacion"].focus_set()
                return

            if not nombre or not apellidos:
                messagebox.showwarning(
                    "Datos incompletos",
                    "El nombre y los apellidos son obligatorios.",
                    parent=formulario
                )
                return

            if not puesto or not turno:
                messagebox.showwarning(
                    "Datos incompletos",
                    "Selecciona un puesto y un turno.",
                    parent=formulario
                )
                return

            try:
                salario = float(salario_texto)

                if salario < 0:
                    raise ValueError

            except ValueError:
                messagebox.showwarning(
                    "Salario incorrecto",
                    "Ingresa un salario válido, igual o mayor que cero.",
                    parent=formulario
                )
                entradas["salario"].focus_set()
                return

            valores = (
                identificacion,
                nombre,
                apellidos,
                telefono,
                puesto,
                turno,
                salario
            )

            if es_edicion:
                correcto = ejecutar(
                    """
                    UPDATE Empleados
                    SET identificacion = %s,
                        nombre = %s,
                        apellidos = %s,
                        telefono = %s,
                        puesto = %s,
                        turno = %s,
                        salario = %s
                    WHERE id_empleado = %s
                    """,
                    valores + (datos[0],),
                    requiere_admin=True,
                    parent=formulario
                )
                mensaje = "Empleado actualizado correctamente."

            else:
                correcto = ejecutar(
                    """
                    INSERT INTO Empleados
                    (
                        identificacion,
                        nombre,
                        apellidos,
                        telefono,
                        puesto,
                        turno,
                        salario
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    valores,
                    requiere_admin=True,
                    parent=formulario
                )
                mensaje = "Empleado registrado correctamente."

            if correcto:
                messagebox.showinfo(
                    "Operación completada",
                    mensaje,
                    parent=formulario
                )

                formulario.destroy()

                filtro = entrada_busqueda.get().strip()

                if filtro == texto_busqueda:
                    filtro = ""

                cargar_empleados(filtro)

        # ----------------------------------------------------
        # BOTONES DEL FORMULARIO
        # ----------------------------------------------------
        contenedor_botones = tk.Frame(
            formulario,
            bg=COLOR_FONDO
        )
        contenedor_botones.pack(
            fill="x",
            padx=22,
            pady=(0, 15)
        )

        boton_guardar = tk.Button(
            contenedor_botones,
            text="Guardar cambios" if es_edicion else "Registrar empleado",
            command=guardar,
            bg=COLOR_PRINCIPAL,
            fg="white",
            activebackground=COLOR_PRINCIPAL_HOVER,
            activeforeground="white",
            font=(FUENTE, 10, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        )
        boton_guardar.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6)
        )

        boton_cancelar = tk.Button(
            contenedor_botones,
            text="Cancelar",
            command=formulario.destroy,
            bg=COLOR_ACENTO,
            fg="white",
            activebackground=COLOR_ACENTO_HOVER,
            activeforeground="white",
            font=(FUENTE, 10, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        )
        boton_cancelar.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(6, 0)
        )

    # ========================================================
    # DESACTIVAR EMPLEADO
    # ========================================================
    def desactivar_empleado(id_empleado):

        if not validar_permiso(
            "No tienes permisos para desactivar empleados."
        ):
            return

        confirmar = messagebox.askyesno(
            "Desactivar empleado",
            "¿Deseas desactivar a este empleado?\n\n"
            "Su registro y su historial se conservarán.",
            parent=ventana
        )

        if not confirmar:
            return

        correcto = ejecutar(
            """
            UPDATE Empleados
            SET estado = 1
            WHERE id_empleado = %s
              AND estado = 0
            """,
            (id_empleado,),
            requiere_admin=True
        )

        if correcto:
            messagebox.showinfo(
                "Operación completada",
                "El empleado ha sido desactivado.",
                parent=ventana
            )

            filtro = entrada_busqueda.get().strip()

            if filtro == texto_busqueda:
                filtro = ""

            cargar_empleados(filtro)

    # ========================================================
    # VER Y RECUPERAR EMPLEADOS DESACTIVADOS
    # ========================================================
    def ver_empleados_desactivados():

        if not validar_permiso(
            "No tienes permisos para consultar empleados desactivados."
        ):
            return

        ventana_inactivos = tk.Toplevel(ventana)
        registrar_ventana_tema(ventana_inactivos)
        ventana_inactivos.title("Empleados desactivados")
        ventana_inactivos.geometry("1000x650")
        ventana_inactivos.minsize(800, 560)
        ventana_inactivos.configure(bg=COLOR_FONDO)
        ventana_inactivos.transient(ventana)

        # ----------------------------------------------------
        # ENCABEZADO
        # ----------------------------------------------------
        encabezado_inactivos = tk.Frame(
            ventana_inactivos,
            bg=COLOR_PRINCIPAL,
            height=105
        )
        encabezado_inactivos.pack(fill="x")
        encabezado_inactivos.pack_propagate(False)

        tk.Label(
            encabezado_inactivos,
            text="PAPELERÍA LUNA / EMPLEADOS",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PRINCIPAL,
            fg=COLOR_ACENTO
        ).pack(
            anchor="w",
            padx=25,
            pady=(7, 0)
        )

        tk.Label(
            encabezado_inactivos,
            text="Empleados desactivados",
            font=(FUENTE, 20, "bold"),
            bg=COLOR_PRINCIPAL,
            fg="white"
        ).pack(
            anchor="w",
            padx=25,
            pady=(5, 3)
        )

        tk.Label(
            encabezado_inactivos,
            text="Consulta, busca y recupera empleados inactivos",
            font=(FUENTE, 10),
            bg=COLOR_PRINCIPAL,
            fg="white"
        ).pack(anchor="w", padx=26)

        tk.Frame(
            encabezado_inactivos,
            bg=COLOR_ACENTO,
            height=5
        ).pack(side="bottom", fill="x")

        # ----------------------------------------------------
        # BARRA DE BÚSQUEDA
        # ----------------------------------------------------
        barra_busqueda_inactivos = tk.Frame(
            ventana_inactivos,
            bg=COLOR_FONDO
        )
        barra_busqueda_inactivos.pack(
            fill="x",
            padx=22,
            pady=(12, 5)
        )

        tk.Label(
            barra_busqueda_inactivos,
            text="Busca empleados por nombre, apellidos o identificación:",
            font=(FUENTE, 9),
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO_SUAVE
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        fila_busqueda = tk.Frame(
            barra_busqueda_inactivos,
            bg=COLOR_FONDO
        )
        fila_busqueda.pack(fill="x")

        
        entrada_busqueda_inactivos = tk.Entry(
            fila_busqueda,
            font=(FUENTE, 10),
            bg=COLOR_ENTRADA,
            fg=COLOR_TEXTO,
            insertbackground=COLOR_TEXTO,
            selectbackground=COLOR_SELECCION,
            selectforeground=COLOR_TEXTO,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=COLOR_BORDE,
            highlightcolor=COLOR_ACENTO
        )
        entrada_busqueda_inactivos.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7,
            padx=(0, 10)
        )

        # ----------------------------------------------------
        # TABLA DE EMPLEADOS DESACTIVADOS
        # ----------------------------------------------------
        marco_tabla = tk.Frame(
            ventana_inactivos,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        marco_tabla.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=(5, 8)
        )

        columnas = (
            "id", "identificacion", "nombre", "apellidos",
            "telefono", "puesto", "turno"
        )

        estilo_tabla = ttk.Style(ventana_inactivos)
        estilo_tabla.theme_use("clam")

        estilo_tabla.configure(
            "Luna.Treeview",
            background=COLOR_PANEL,
            fieldbackground=COLOR_PANEL,
            foreground=COLOR_TEXTO,
            rowheight=32,
            font=(FUENTE, 10)
        )

        configurar_estilos_tema(ventana_inactivos)

        tabla = ttk.Treeview(
            marco_tabla,
            columns=columnas,
            show="headings",
            style="Luna.Treeview"
        )

        encabezados_tabla = {
            "id": "ID",
            "identificacion": "Identificación",
            "nombre": "Nombre",
            "apellidos": "Apellidos",
            "telefono": "Teléfono",
            "puesto": "Puesto",
            "turno": "Turno"
        }

        anchos = {
            "id": 55,
            "identificacion": 140,
            "nombre": 130,
            "apellidos": 150,
            "telefono": 125,
            "puesto": 165,
            "turno": 130
        }

        for columna in columnas:
            tabla.heading(
                columna,
                text=encabezados_tabla[columna],
                anchor="center"
            )
            tabla.column(
                columna,
                width=anchos[columna],
                minwidth=50 if columna == "id" else 80,
                anchor="center",
                stretch=True
            )

        barra_tabla = ttk.Scrollbar(
            marco_tabla,
            orient="vertical",
            command=tabla.yview
        )
        tabla.configure(yscrollcommand=barra_tabla.set)
        
        tabla.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(10, 0),
            pady=10
        )
        barra_tabla.pack(
            side="right",
            fill="y",
            padx=(0, 10),
            pady=10
        )

        etiqueta_resultados = tk.Label(
            ventana_inactivos,
            text="",
            font=(FUENTE, 9),
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO_SUAVE
        )
        etiqueta_resultados.pack(
            anchor="w",
            padx=24,
            pady=(0, 2)
        )

        # ----------------------------------------------------
        # CARGAR Y BUSCAR EMPLEADOS DESACTIVADOS
        # ----------------------------------------------------
        def cargar_desactivados(event=None):

            filtro = entrada_busqueda_inactivos.get().strip()
            patron = f"%{filtro}%"

            sql = """
                SELECT
                    id_empleado,
                    identificacion,
                    nombre,
                    apellidos,
                    telefono,
                    puesto,
                    turno
                FROM Empleados
                WHERE estado = 1
                  AND (
                      nombre LIKE %s
                      OR apellidos LIKE %s
                      OR identificacion LIKE %s
                  )
                ORDER BY nombre, apellidos
            """

            empleados = consultar(
                sql,
                (patron, patron, patron)
            )

            for elemento in tabla.get_children():
                tabla.delete(elemento)

            if empleados is None:
                etiqueta_resultados.config(
                    text="No se pudo cargar la información."
                )
                return

            for empleado in empleados:
                tabla.insert("", "end", values=empleado)

            etiqueta_resultados.config(
                text=f"{len(empleados)} empleado(s) desactivado(s) encontrado(s)"
            )

        def limpiar_busqueda_inactivos():
            entrada_busqueda_inactivos.delete(0, tk.END)
            cargar_desactivados()
            entrada_busqueda_inactivos.focus_set()

        tk.Button(
            fila_busqueda,
            text="Limpiar",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_PRINCIPAL,
            fg="white",
            activebackground=COLOR_PRINCIPAL_HOVER,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=6,
            command=limpiar_busqueda_inactivos
        ).pack(side="right")

        # ----------------------------------------------------
        # VER FICHA DE UN EMPLEADO DESACTIVADO
        # ----------------------------------------------------
        def ver_ficha_desactivado():

            seleccion = tabla.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selecciona un empleado",
                    "Primero selecciona al empleado cuya información deseas consultar.",
                    parent=ventana_inactivos
                )
                return

            datos = tabla.item(seleccion[0], "values")

            ficha = tk.Toplevel(ventana_inactivos)
            registrar_ventana_tema(ficha)
            ficha.title("Información del empleado")
            ficha.geometry("440x420")
            ficha.resizable(False, False)
            ficha.configure(bg=COLOR_FONDO)
            ficha.transient(ventana_inactivos)
            ficha.grab_set()

            encabezado_ficha = tk.Frame(
                ficha,
                bg=COLOR_PRINCIPAL,
                height=72
            )
            encabezado_ficha.pack(fill="x")
            encabezado_ficha.pack_propagate(False)

            tk.Label(
                encabezado_ficha,
                text="Información del empleado",
                font=(FUENTE, 16, "bold"),
                bg=COLOR_PRINCIPAL,
                fg="white"
            ).pack(
                anchor="w",
                padx=20,
                pady=(12, 2)
            )

            tk.Label(
                encabezado_ficha,
                text="Registro actualmente inactivo",
                font=(FUENTE, 9),
                bg=COLOR_PRINCIPAL,
                fg="white"
            ).pack(anchor="w", padx=21)

            tk.Frame(
                ficha,
                bg=COLOR_ACENTO,
                height=4
            ).pack(fill="x")

            panel_ficha = tk.Frame(
                ficha,
                bg=COLOR_PANEL,
                highlightbackground=COLOR_BORDE,
                highlightthickness=1
            )
            panel_ficha.pack(
                fill="both",
                expand=True,
                padx=20,
                pady=18
            )

            etiquetas_ficha = (
                ("ID", datos[0]),
                ("Identificación", datos[1]),
                ("Nombre", datos[2]),
                ("Apellidos", datos[3]),
                ("Teléfono", datos[4]),
                ("Puesto", datos[5]),
                ("Turno", datos[6]),
                ("Estado", "INACTIVO")
            )

            for etiqueta, valor in etiquetas_ficha:
                fila_ficha = tk.Frame(
                    panel_ficha,
                    bg=COLOR_PANEL
                )
                fila_ficha.pack(
                    fill="x",
                    padx=12,
                    pady=5
                )

                tk.Label(
                    fila_ficha,
                    text=f"{etiqueta}:",
                    font=(FUENTE, 9, "bold"),
                    bg=COLOR_PANEL,
                    fg=COLOR_TEXTO,
                    width=15,
                    anchor="w"
                ).pack(side="left")

                tk.Label(
                    fila_ficha,
                    text=str(valor if valor is not None else ""),
                    font=(FUENTE, 9),
                    bg=COLOR_PANEL,
                    fg=COLOR_TEXTO_SUAVE,
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)

            tk.Button(
                ficha,
                text="Cerrar ficha",
                font=(FUENTE, 10, "bold"),
                bg=COLOR_SECUNDARIO,
                fg="white",
                activebackground=COLOR_PRINCIPAL_HOVER,
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                padx=18,
                pady=7,
                command=ficha.destroy
            ).pack(
                anchor="e",
                padx=20,
                pady=(0, 15)
            )

        # ----------------------------------------------------
        # RECUPERAR EMPLEADO
        # ----------------------------------------------------
        def recuperar_empleado():

            if not validar_permiso(
                "No tienes permisos para recuperar empleados.",
                ventana_inactivos
            ):
                return

            seleccion = tabla.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selecciona un empleado",
                    "Primero selecciona al empleado que deseas recuperar.",
                    parent=ventana_inactivos
                )
                return

            datos = tabla.item(seleccion[0], "values")
            id_empleado = datos[0]
            nombre_completo = f"{datos[2]} {datos[3]}"

            confirmar = messagebox.askyesno(
                "Recuperar empleado",
                f"¿Deseas recuperar a {nombre_completo}?",
                parent=ventana_inactivos
            )

            if not confirmar:
                return

            correcto = ejecutar(
                """
                UPDATE Empleados
                SET estado = 0
                WHERE id_empleado = %s
                  AND estado = 1
                """,
                (id_empleado,),
                requiere_admin=True,
                parent=ventana_inactivos
            )

            if correcto:
                messagebox.showinfo(
                    "Empleado recuperado",
                    f"{nombre_completo} ahora está activo.",
                    parent=ventana_inactivos
                )

                cargar_desactivados()

                filtro_principal = entrada_busqueda.get().strip()

                if filtro_principal == texto_busqueda:
                    filtro_principal = ""

                cargar_empleados(filtro_principal)

        # ----------------------------------------------------
        # BOTONES INFERIORES
        # ----------------------------------------------------
        marco_botones = tk.Frame(
            ventana_inactivos,
            bg=COLOR_PRINCIPAL,
            height=105
        )
        marco_botones.pack(
            side="bottom",
            fill="x"
        )
        marco_botones.pack_propagate(False)

        tk.Frame(
            marco_botones,
            bg=COLOR_ACENTO,
            height=4
        ).pack(
            side="top",
            fill="x"
        )

        fila_botones = tk.Frame(
            marco_botones,
            bg=COLOR_PRINCIPAL
        )
        fila_botones.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=5
        )

        tk.Button(
            fila_botones,
            text="Recuperar empleado",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_PRINCIPAL_HOVER,
            fg="white",
            activebackground=COLOR_SECUNDARIO,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=7,
            command=recuperar_empleado
        ).pack(side="left")

        tk.Button(
            fila_botones,
            text="Ver ficha",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_PRINCIPAL_HOVER,
            fg="white",
            activebackground=COLOR_SECUNDARIO,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=7,
            command=ver_ficha_desactivado
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            fila_botones,
            text="Cerrar",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_ACENTO,
            fg="white",
            activebackground=COLOR_ACENTO_HOVER,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=7,
            command=ventana_inactivos.destroy
        ).pack(side="right")

        entrada_busqueda_inactivos.bind(
            "<KeyRelease>",
            cargar_desactivados
        )

        cargar_desactivados()

    # ========================================================
    # BOTONES DE LA BARRA SUPERIOR
    # Solo visibles para Administrador y Gerente.
    # ========================================================
    if puede_administrar:

        tk.Button(
            barra,
            text="Ver desactivados",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_SECUNDARIO,
            fg="white",
            activebackground=COLOR_PRINCIPAL_HOVER,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=9,
            command=ver_empleados_desactivados
        ).pack(side="right", padx=(0, 10))

        tk.Button(
            barra,
            text="Registrar empleado",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_ACENTO,
            fg="white",
            activebackground=COLOR_ACENTO_HOVER,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=9,
            command=registrar_empleado
        ).pack(side="right")

    # ========================================================
    # BÚSQUEDA DEL DIRECTORIO
    # ========================================================
    def buscar_empleados(event=None):

        filtro = entrada_busqueda.get().strip()

        if filtro == texto_busqueda:
            filtro = ""

        cargar_empleados(filtro)

    entrada_busqueda.bind(
        "<KeyRelease>",
        buscar_empleados
    )

    # ========================================================
    # PIE DE VENTANA
    # ========================================================
    pie = tk.Frame(
        ventana,
        bg=COLOR_PRINCIPAL,
        height=55
    )
    pie.pack(
        fill="x",
        side="bottom"
    )
    pie.pack_propagate(False)

    tk.Frame(
        pie,
        bg=COLOR_ACENTO,
        height=4
    ).pack(
        side="top",
        fill="x"
    )

    tk.Label(
        pie,
        text="Papelería Luna | Gestión de empleados",
        font=(FUENTE, 9),
        bg=COLOR_PRINCIPAL,
        fg=COLOR_TEXTO_SUAVE
    ).pack(
        side="left",
        padx=25,
        pady=8
    )

    tk.Button(
        pie,
        text="Volver al menú",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_ACENTO,
        fg=COLOR_TEXTO,
        activebackground=COLOR_ACENTO_HOVER,
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=6,
        command=ventana.destroy
    ).pack(
        side="right",
        padx=25,
        pady=6
    )

    # ========================================================
    # INICIAR DIRECTORIO
    # ========================================================
    cargar_empleados()

    if raiz is None:
        ventana.mainloop()
