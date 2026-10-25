
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
from decimal import Decimal, InvalidOperation

from tema import (
    obtener_colores,
    obtener_tema_actual,
    registrar_observador,
    eliminar_observador
)

# ============================================================
# TEMA COMPARTIDO - PAPELERÍA LUNA
# ============================================================

TEMA_ACTUAL = obtener_tema_actual()
COLORES = obtener_colores(TEMA_ACTUAL)

COLOR_FONDO = COLORES["FONDO"]
COLOR_PANEL = COLORES["PANEL"]
COLOR_PRINCIPAL = COLORES["AZUL"]
COLOR_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
COLOR_ACENTO = COLORES["NARANJA"]
COLOR_ACENTO_HOVER = COLORES["NARANJA_HOVER"]
COLOR_TEXTO = COLORES["TEXTO"]
COLOR_TEXTO_SUAVE = COLORES["TEXTO_SUAVE"]
COLOR_BORDE = COLORES["BORDE"]
COLOR_ROJO = COLORES["ROJO"]
COLOR_ROJO_HOVER = COLORES["ROJO_HOVER"]

# Se conservan los nombres utilizados por el módulo.
# El verde se mantiene como color semántico para el stock.
COLOR_VERDE = "#16A34A"
COLOR_VERDE_HOVER = "#15803D"

FUENTE = "Arial"

# ============================================================
# ESTADOS DE LOS PRODUCTOS
# estado = 0: ACTIVO
# estado = 1: INACTIVO
# ============================================================
ESTADO_ACTIVO = 0
ESTADO_INACTIVO = 1


# ============================================================
# CONEXIÓN A MYSQL
# ============================================================
def conectar_bd():
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

    x = max(0, (ventana.winfo_screenwidth() - ancho) // 2)
    y = max(0, (ventana.winfo_screenheight() - alto) // 2)

    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")



def boton_hover(boton, normal, hover):
    # Guardar los colores actuales en el propio botón.
    boton._color_normal = normal
    boton._color_hover = hover

    def al_entrar(evento):
        try:
            boton.configure(bg=boton._color_hover)
        except tk.TclError:
            pass

    def al_salir(evento):
        try:
            boton.configure(bg=boton._color_normal)
        except tk.TclError:
            pass

    boton.bind("<Enter>", al_entrar)
    boton.bind("<Leave>", al_salir)

# ============================================================
# ACTUALIZACIÓN VISUAL DEL TEMA
# ============================================================

def actualizar_estilos_ttk(ventana, colores):
    """Actualiza los estilos de los controles ttk de una ventana."""

    estilo = ttk.Style(ventana)

    estilo.configure(
        "Inventario.Treeview",
        background=colores["PANEL"],
        foreground=colores["TEXTO"],
        fieldbackground=colores["PANEL"],
        font=(FUENTE, 10),
        rowheight=34,
        borderwidth=0,
        relief="flat"
    )

    estilo.configure(
        "Inventario.Treeview.Heading",
        background=colores["AZUL"],
        foreground="#FFFFFF",
        font=(FUENTE, 10, "bold"),
        padding=(10, 11),
        relief="flat"
    )

    estilo.map(
        "Inventario.Treeview",
        background=[
            ("selected", colores["SELECCION"])
        ],
        foreground=[
            ("selected", colores["TEXTO"])
        ]
    )

    estilo.map(
        "Inventario.Treeview.Heading",
        background=[
            ("active", colores["AZUL_SECUNDARIO"])
        ],
        foreground=[
            ("active", "#FFFFFF")
        ]
    )

    estilo.configure(
        "TEntry",
        padding=7,
        font=(FUENTE, 10),
        fieldbackground=colores["ENTRADA"],
        foreground=colores["TEXTO"]
    )

    estilo.configure(
        "TCombobox",
        padding=7,
        font=(FUENTE, 10),
        fieldbackground=colores["ENTRADA"],
        background=colores["PANEL"],
        foreground=colores["TEXTO"],
        arrowcolor=colores["TEXTO"]
    )

    estilo.map(
        "TCombobox",
        fieldbackground=[
            ("readonly", colores["ENTRADA"])
        ],
        foreground=[
            ("readonly", colores["TEXTO"])
        ],
        selectbackground=[
            ("readonly", colores["SELECCION"])
        ],
        selectforeground=[
            ("readonly", colores["TEXTO"])
        ]
    )


def actualizar_widgets_tema(widget, mapa_colores):
    """
    Cambia únicamente los colores que corresponden a la paleta
    anterior, conservando los colores semánticos del inventario.
    """

    try:
        configuracion = widget.configure()

        for propiedad in ("bg", "background", "highlightbackground"):
            if propiedad in configuracion:
                actual = widget.cget(propiedad)

                if actual in mapa_colores:
                    widget.configure(
                        **{propiedad: mapa_colores[actual]}
                    )

        for propiedad in ("fg", "foreground", "highlightcolor"):
            if propiedad in configuracion:
                actual = widget.cget(propiedad)

                if actual in mapa_colores:
                    widget.configure(
                        **{propiedad: mapa_colores[actual]}
                    )

        
        # Actualizar los colores de los botones y su efecto hover.
        if isinstance(widget, tk.Button):
            normal_anterior = getattr(
                widget, "_color_normal", None
            )
            hover_anterior = getattr(
                widget, "_color_hover", None
            )

            if normal_anterior in mapa_colores:
                widget._color_normal = mapa_colores[normal_anterior]

            if hover_anterior in mapa_colores:
                widget._color_hover = mapa_colores[hover_anterior]

            widget.configure(
                activebackground=widget.cget("bg"),
                activeforeground=widget.cget("fg")
            )

        # Las tablas utilizan los estilos compartidos.
        if isinstance(widget, ttk.Treeview):
            widget.configure(style="Inventario.Treeview")

    except (tk.TclError, TypeError):
        pass

    for hijo in widget.winfo_children():
        actualizar_widgets_tema(hijo, mapa_colores)


def registrar_ventana_tema(ventana):
    """
    Registra una ventana para que se adapte cuando cambie
    el tema compartido de Papelería Luna.
    """

    colores_anteriores = obtener_colores()

    def aplicar_tema(colores_nuevos):
        nonlocal colores_anteriores

        
        # Mantener actualizados los colores globales del módulo.
        globales_color = {
            "COLOR_FONDO": "FONDO",
            "COLOR_PANEL": "PANEL",
            "COLOR_PRINCIPAL": "AZUL",
            "COLOR_SECUNDARIO": "AZUL_SECUNDARIO",
            "COLOR_ACENTO": "NARANJA",
            "COLOR_ACENTO_HOVER": "NARANJA_HOVER",
            "COLOR_TEXTO": "TEXTO",
            "COLOR_TEXTO_SUAVE": "TEXTO_SUAVE",
            "COLOR_BORDE": "BORDE",
            "COLOR_ROJO": "ROJO",
            "COLOR_ROJO_HOVER": "ROJO_HOVER",
        }

        for variable, clave in globales_color.items():
            if clave in colores_nuevos:
                globals()[variable] = colores_nuevos[clave]

        # Actualizar la paleta global utilizada por el módulo.
        global TEMA_ACTUAL, COLORES
        TEMA_ACTUAL = obtener_tema_actual()
        COLORES = dict(colores_nuevos)

        if not ventana.winfo_exists():
            return

        mapa_colores = {}

        for clave, color_anterior in colores_anteriores.items():
            color_nuevo = colores_nuevos.get(clave)

            if color_nuevo:
                mapa_colores[color_anterior] = color_nuevo

        # Colores históricos equivalentes de la interfaz clara.
        equivalencias = {
            "#f1f5f9": "FONDO",
            "#ffffff": "PANEL",
            "#172554": "AZUL",
            "#1e3a5f": "AZUL_SECUNDARIO",
            "#f59e0b": "NARANJA",
            "#d97706": "NARANJA_HOVER",
            "#1e293b": "TEXTO",
            "#64748b": "TEXTO_SUAVE",
            "#dbe3ed": "BORDE",
            "#ef4444": "ROJO",
            "#dc2626": "ROJO_HOVER",
        }

        for color_anterior, clave in equivalencias.items():
            if clave in colores_nuevos:
                mapa_colores[color_anterior] = colores_nuevos[clave]

        try:
            fondo_actual = ventana.cget("bg")

            if fondo_actual in mapa_colores:
                ventana.configure(bg=mapa_colores[fondo_actual])

            actualizar_widgets_tema(ventana, mapa_colores)
            actualizar_estilos_ttk(ventana, colores_nuevos)

        except tk.TclError:
            pass

        colores_anteriores = dict(colores_nuevos)

    def al_cerrar():
        eliminar_observador(aplicar_tema)

    registrar_observador(aplicar_tema)
    ventana.bind("<Destroy>", lambda evento: (
        al_cerrar() if evento.widget is ventana else None
    ), add="+")

    aplicar_tema(obtener_colores())


def crear_boton(
    padre,
    texto,
    comando,
    color,
    color_hover,
    color_texto="#FFFFFF"
):
    boton = tk.Button(
        padre,
        text=texto,
        command=comando,
        font=(FUENTE, 10, "bold"),
        bg=color,
        fg=color_texto,
        activebackground=color_hover,
        activeforeground=color_texto,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=14,
        pady=10,
        highlightthickness=0
    )

    boton_hover(boton, color, color_hover)
    return boton


def crear_titulo(padre, texto):
    return tk.Label(
        padre,
        text=texto,
        font=(FUENTE, 12, "bold"),
        bg=padre.cget("bg"),
        fg=COLOR_PRINCIPAL
    )


def mostrar_error_bd(error, padre=None):
    messagebox.showerror(
        "Error de base de datos",
        f"No fue posible completar la operación.\n\n{error}",
        parent=padre
    )


# ============================================================
# CARGAR CATEGORÍAS
# ============================================================
def obtener_catalogos():
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_categoria, nombre
            FROM Categorias
            ORDER BY nombre ASC
        """)

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()

# ============================================================
# OBTENER PROVEEDORES ACTIVOS
# ============================================================
def obtener_proveedores_activos():
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_proveedor, nombre
            FROM Proveedores
            WHERE estado = %s
            ORDER BY nombre ASC
        """, (ESTADO_ACTIVO,))

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()

# ============================================================
# GESTIÓN DE CATEGORÍAS
# ============================================================
def abrir_categorias(parent=None, al_actualizar=None):

    es_ventana_principal = parent is None
    ventana = tk.Tk() if es_ventana_principal else tk.Toplevel(parent)

    ventana.title("Papelería Luna | Gestión de categorías")
    ventana.configure(bg=COLOR_FONDO)
    registrar_ventana_tema(ventana)
    actualizar_estilos_ttk(ventana, obtener_colores())
    ventana.geometry("800x600")
    ventana.minsize(650, 500)
    centrar_ventana(ventana, 800, 600)

    if parent:
        ventana.transient(parent)

    id_seleccionado = None

    # --------------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------------
    encabezado = tk.Frame(
        ventana,
        bg=COLOR_PRINCIPAL,
        height=100
    )
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA / INVENTARIO",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PRINCIPAL,
        fg=COLOR_ACENTO
    ).pack(anchor="w", padx=24, pady=(10, 0))

    tk.Label(
        encabezado,
        text="Gestión de categorías",
        font=(FUENTE, 20, "bold"),
        bg=COLOR_PRINCIPAL,
        fg="#FFFFFF"
    ).pack(anchor="w", padx=24, pady=(0, 2))

    tk.Label(
        encabezado,
        text="Registra, consulta y modifica categorías",
        font=(FUENTE, 10),
        bg=COLOR_PRINCIPAL,
        fg="#E2E8F0"
    ).pack(anchor="w", padx=25)

    tk.Frame(
        ventana,
        bg=COLOR_ACENTO,
        height=4
    ).pack(fill="x")

    # --------------------------------------------------------
    # FORMULARIO
    # --------------------------------------------------------
    formulario = tk.Frame(
        ventana,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    formulario.pack(fill="x", padx=18, pady=15)

    tk.Label(
        formulario,
        text="Nombre de la categoría",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 3))

    entrada_nombre = ttk.Entry(formulario, font=(FUENTE, 10))
    entrada_nombre.grid(
        row=1, column=0, sticky="ew",
        padx=12, pady=(0, 10), ipady=4
    )

    tk.Label(
        formulario,
        text="Descripción",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).grid(row=0, column=1, sticky="w", padx=12, pady=(12, 3))

    entrada_descripcion = ttk.Entry(formulario, font=(FUENTE, 10))
    entrada_descripcion.grid(
        row=1, column=1, sticky="ew",
        padx=12, pady=(0, 10), ipady=4
    )

    formulario.grid_columnconfigure(0, weight=1)
    formulario.grid_columnconfigure(1, weight=2)

    # --------------------------------------------------------
    # TABLA DE CATEGORÍAS
    # --------------------------------------------------------
    panel_tabla = tk.Frame(
        ventana,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )

    tk.Label(
        panel_tabla,
        text="Categorías registradas",
        font=(FUENTE, 12, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_PRINCIPAL
    ).pack(anchor="w", padx=12, pady=10)

    columnas = ("id", "nombre", "descripcion")

    tabla = ttk.Treeview(
        panel_tabla,
        columns=columnas,
        show="headings",
        selectmode="browse",
        style="Inventario.Treeview"
    )

    tabla.heading("id", text="ID")
    tabla.heading("nombre", text="Nombre")
    tabla.heading("descripcion", text="Descripción")

    tabla.column("id", width=60, anchor="center")
    tabla.column("nombre", width=200)
    tabla.column("descripcion", width=400)

    barra_vertical = ttk.Scrollbar(
        panel_tabla,
        orient="vertical",
        command=tabla.yview
    )
    tabla.configure(yscrollcommand=barra_vertical.set)

    tabla.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(10, 0),
        pady=(0, 10)
    )

    barra_vertical.pack(
        side="right",
        fill="y",
        pady=(0, 10),
        padx=(0, 10)
    )

    # --------------------------------------------------------
    # CARGAR CATEGORÍAS EN LA TABLA
    # --------------------------------------------------------
    def cargar_categorias():
        tabla.delete(*tabla.get_children())

        conexion = None
        cursor = None

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT id_categoria, nombre, descripcion
                FROM Categorias
                ORDER BY nombre ASC
            """)

            for fila in cursor.fetchall():
                tabla.insert(
                    "",
                    "end",
                    values=(fila[0], fila[1], fila[2] or "")
                )

        except Error as error:
            mostrar_error_bd(error, ventana)

        finally:
            if cursor:
                cursor.close()

            if conexion and conexion.is_connected():
                conexion.close()

    # --------------------------------------------------------
    # LIMPIAR FORMULARIO
    # --------------------------------------------------------
    def limpiar():
        nonlocal id_seleccionado

        id_seleccionado = None
        entrada_nombre.delete(0, tk.END)
        entrada_descripcion.delete(0, tk.END)
        tabla.selection_remove(tabla.selection())

        boton_guardar.config(text="Registrar categoría")
        boton_cancelar.pack_forget()
        entrada_nombre.focus_set()

    # --------------------------------------------------------
    # SELECCIONAR CATEGORÍA
    # --------------------------------------------------------
    def seleccionar(event=None):
        nonlocal id_seleccionado

        seleccion = tabla.selection()
        if not seleccion:
            return

        valores = tabla.item(seleccion[0], "values")
        id_seleccionado = int(valores[0])

        entrada_nombre.delete(0, tk.END)
        entrada_nombre.insert(0, valores[1])

        entrada_descripcion.delete(0, tk.END)
        entrada_descripcion.insert(0, valores[2])

        boton_guardar.config(text="Guardar cambios")
        boton_cancelar.pack(side="left", padx=6)

    # --------------------------------------------------------
    # REGISTRAR O MODIFICAR CATEGORÍA
    # --------------------------------------------------------
    def guardar():
        nonlocal id_seleccionado

        nombre = entrada_nombre.get().strip()
        descripcion = entrada_descripcion.get().strip()

        if not nombre:
            messagebox.showwarning(
                "Campo obligatorio",
                "Escribe el nombre de la categoría.",
                parent=ventana
            )
            entrada_nombre.focus_set()
            return

        if len(nombre) > 50 or len(descripcion) > 255:
            messagebox.showwarning(
                "Datos demasiado largos",
                "El nombre admite 50 caracteres y la descripción 255.",
                parent=ventana
            )
            return

        conexion = None
        cursor = None

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()

            if id_seleccionado is None:
                cursor.execute("""
                    INSERT INTO Categorias (nombre, descripcion)
                    VALUES (%s, %s)
                """, (nombre, descripcion or None))

                mensaje = "Categoría registrada correctamente."

            else:
                cursor.execute("""
                    UPDATE Categorias
                    SET nombre = %s, descripcion = %s
                    WHERE id_categoria = %s
                """, (nombre, descripcion or None, id_seleccionado))

                mensaje = "Categoría modificada correctamente."

            conexion.commit()

            limpiar()
            cargar_categorias()

            messagebox.showinfo(
                "Operación exitosa",
                mensaje,
                parent=ventana
            )

            if callable(al_actualizar):
                al_actualizar()

        except Error as error:
            if conexion and conexion.is_connected():
                conexion.rollback()

            if getattr(error, "errno", None) == 1062:
                messagebox.showwarning(
                    "Categoría existente",
                    "Ya existe una categoría con ese nombre.",
                    parent=ventana
                )
            else:
                mostrar_error_bd(error, ventana)

        finally:
            if cursor:
                cursor.close()

            if conexion and conexion.is_connected():
                conexion.close()

    # --------------------------------------------------------
    # ELIMINAR CATEGORÍA
    # --------------------------------------------------------
    def eliminar():
        seleccion = tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona una categoría",
                "Selecciona una categoría de la tabla.",
                parent=ventana
            )
            return

        valores = tabla.item(seleccion[0], "values")
        id_categoria = int(valores[0])
        nombre = valores[1]

        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Deseas eliminar la categoría '{nombre}'?",
            parent=ventana
        ):
            return

        conexion = None
        cursor = None

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT COUNT(*)
                FROM Productos
                WHERE id_categoria = %s
            """, (id_categoria,))

            if cursor.fetchone()[0] > 0:
                messagebox.showwarning(
                    "Categoría en uso",
                    "No puedes eliminarla porque hay productos asociados.",
                    parent=ventana
                )
                return

            cursor.execute("""
                DELETE FROM Categorias
                WHERE id_categoria = %s
            """, (id_categoria,))

            conexion.commit()
            limpiar()
            cargar_categorias()

            messagebox.showinfo(
                "Operación exitosa",
                "Categoría eliminada correctamente.",
                parent=ventana
            )

            if callable(al_actualizar):
                al_actualizar()

        except Error as error:
            if conexion and conexion.is_connected():
                conexion.rollback()

            mostrar_error_bd(error, ventana)

        finally:
            if cursor:
                cursor.close()

            if conexion and conexion.is_connected():
                conexion.close()

    tabla.bind("<<TreeviewSelect>>", seleccionar)

    # --------------------------------------------------------
    # BOTONES DEL FORMULARIO
    # --------------------------------------------------------
    fila_botones = tk.Frame(formulario, bg=COLOR_PANEL)
    fila_botones.grid(
        row=2,
        column=0,
        columnspan=2,
        sticky="w",
        padx=12,
        pady=(0, 12)
    )

    boton_guardar = crear_boton(
        fila_botones,
        "Registrar categoría",
        guardar,
        COLOR_ACENTO,
        COLOR_ACENTO_HOVER
    )
    boton_guardar.pack(side="left")

    boton_cancelar = crear_boton(
        fila_botones,
        "Cancelar edición",
        limpiar,
        COLOR_ACENTO,
        COLOR_ACENTO_HOVER
    )

    # --------------------------------------------------------
    # PIE DE VENTANA: SALIR
    # --------------------------------------------------------
    pie = tk.Frame(
        ventana,
        bg=COLOR_PRINCIPAL,
        height=65
    )
    pie.pack_propagate(False)

    tk.Label(
        pie,
        text="Papelería Luna | Gestión de categorías",
        bg=COLOR_PRINCIPAL,
        fg="#FFFFFF",
        font=(FUENTE, 9)
    ).pack(side="left", padx=18)

    def salir_categorias():
        if messagebox.askyesno(
            "Salir de categorías",
            "¿Deseas cerrar la gestión de categorías?",
            parent=ventana
        ):
            ventana.destroy()

    boton_salir = crear_boton(
        pie,
        "Salir",
        salir_categorias,
        COLOR_ACENTO,
        COLOR_ACENTO_HOVER
    )

    boton_salir.pack(
        side="right",
        padx=18,
        pady=5
    )

        # --------------------------------------------------------
    # ORGANIZACIÓN DE LA VENTANA
    # --------------------------------------------------------
    pie.pack(
        side="bottom",
        fill="x",
        expand=False
    )

    panel_tabla.pack(
        side="top",
        fill="both",
        expand=True,
        padx=18,
        pady=(0, 8)
    )

    # Cargar los datos al abrir la ventana.
    cargar_categorias()

    if es_ventana_principal:
        ventana.mainloop()

# ============================================================
# CONSULTAR PRODUCTOS
# estado = 0: ACTIVOS
# estado = 1: INACTIVOS
#
# Productos no tiene id_proveedor.
# Se consultan proveedores mediante:
# Detalle_Pedido -> Pedidos_Proveedor -> Proveedores.
# ============================================================
def consultar_productos(estado=ESTADO_ACTIVO):
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.id_producto,
                p.nombre,
                p.descripcion,
                p.marca,
                p.precio_compra,
                p.precio_venta,
                p.cantidad_stock,
                p.stock_minimo,
                p.id_categoria,
                p.id_proveedor,
                p.estado,
                c.nombre AS categoria,
                COALESCE(pr.nombre, 'Sin proveedor asignado') AS proveedor
            FROM Productos p
            INNER JOIN Categorias c
                ON p.id_categoria = c.id_categoria
            LEFT JOIN Proveedores pr
                ON p.id_proveedor = pr.id_proveedor
            WHERE p.estado = %s
            ORDER BY p.id_producto ASC
                    """, (estado,))

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# ============================================================
# OBTENER UN PRODUCTO ACTIVO
# ============================================================
def obtener_producto(id_producto):
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id_producto,
                nombre,
                marca,
                descripcion,
                precio_compra,
                precio_venta,
                cantidad_stock,
                stock_minimo,
                id_categoria,
                id_proveedor,
                estado
            FROM Productos
            WHERE id_producto = %s
            AND estado = %s
        """, (id_producto, ESTADO_ACTIVO))

        return cursor.fetchone()

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()
            
# ============================================================
# GUARDAR O MODIFICAR PRODUCTO
#
# Productos nuevos: stock inicial = 0.
# Productos existentes: el stock no se modifica aquí.
# ============================================================
def guardar_producto(datos, id_producto=None):
    conexion = None
    cursor = None

    try:
        if len(datos) != 8:
            raise ValueError(
                "Los datos del producto deben contener exactamente 8 valores."
            )

        conexion = conectar_bd()
        cursor = conexion.cursor()

        if id_producto is None:
            cursor.execute("""
                INSERT INTO Productos (
                    nombre,
                    marca,
                    descripcion,
                    precio_compra,
                    precio_venta,
                    cantidad_stock,
                    stock_minimo,
                    id_categoria,
                    id_proveedor,
                    estado
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    0,
                    %s, %s, %s, %s
                )
            """, tuple(datos) + (ESTADO_ACTIVO,))

        else:
            cursor.execute("""
                UPDATE Productos
                SET
                    nombre = %s,
                    marca = %s,
                    descripcion = %s,
                    precio_compra = %s,
                    precio_venta = %s,
                    stock_minimo = %s,
                    id_categoria = %s,
                    id_proveedor = %s
                WHERE id_producto = %s
                  AND estado = %s
            """, tuple(datos) + (id_producto, ESTADO_ACTIVO))

            if cursor.rowcount == 0:
                cursor.execute("""
                    SELECT id_producto
                    FROM Productos
                    WHERE id_producto = %s
                      AND estado = %s
                """, (id_producto, ESTADO_ACTIVO))

                if cursor.fetchone() is None:
                    raise ValueError(
                        "El producto no existe o está desactivado."
                    )

        conexion.commit()
        return True

    except ValueError as error:
        if conexion and conexion.is_connected():
            conexion.rollback()

        messagebox.showwarning(
            "Revisa los datos",
            str(error)
        )
        return False

    except Error as error:
        if conexion and conexion.is_connected():
            conexion.rollback()

        messagebox.showerror(
            "Error de base de datos",
            f"No se pudo guardar el producto:\n\n{error}"
        )
        return False

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()

# ============================================================
# DESACTIVAR PRODUCTO
# ============================================================
def eliminar_producto_bd(id_producto):
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE Productos
            SET estado = %s
            WHERE id_producto = %s
              AND estado = %s
        """, (ESTADO_INACTIVO, id_producto, ESTADO_ACTIVO))

        if cursor.rowcount == 0:
            raise ValueError(
                "El producto no existe o ya está desactivado."
            )

        conexion.commit()

    except Exception:
        if conexion and conexion.is_connected():
            conexion.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# ============================================================
# RECUPERAR PRODUCTO
# ============================================================
def recuperar_producto_bd(id_producto):
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE Productos
            SET estado = %s
            WHERE id_producto = %s
              AND estado = %s
        """, (ESTADO_ACTIVO, id_producto, ESTADO_INACTIVO))

        if cursor.rowcount == 0:
            raise ValueError(
                "El producto no existe o ya está activo."
            )

        conexion.commit()

    except Exception:
        if conexion and conexion.is_connected():
            conexion.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# ============================================================
# VENTANA PRINCIPAL DEL INVENTARIO
# ============================================================
def abrir_inventario(parent=None):
    if parent is None:
        ventana = tk.Tk()
        es_ventana_principal = True
    else:
        ventana = tk.Toplevel(parent)
        es_ventana_principal = False

    ventana.title("Papelería Luna | Control de inventario")
    ventana.configure(bg=COLOR_FONDO)
    registrar_ventana_tema(ventana)
    actualizar_estilos_ttk(ventana, obtener_colores())
    ventana.minsize(950, 600)
    centrar_ventana(ventana, 1150, 760)

    if parent:
        ventana.transient(parent)

    
    # --------------------------------------------------------
    # ESTILOS
    # --------------------------------------------------------
    estilo = ttk.Style(ventana)
    estilo.theme_use("clam")
    actualizar_estilos_ttk(ventana, obtener_colores())


    # --------------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------------
    encabezado = tk.Frame(
        ventana,
        bg=COLOR_PRINCIPAL,
        height=112
    )
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA / INVENTARIO",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PRINCIPAL,
        fg=COLOR_ACENTO
    ).pack(anchor="w", padx=27, pady=(12, 2))

    tk.Label(
        encabezado,
        text="Control de inventario",
        font=(FUENTE, 23, "bold"),
        bg=COLOR_PRINCIPAL,
        fg="#FFFFFF"
    ).pack(anchor="w", padx=27, pady=(0, 2))

    tk.Label(
        encabezado,
        text="Consulta y administra los productos de Papelería Luna",
        font=(FUENTE, 10),
        bg=COLOR_PRINCIPAL,
        fg="#E2E8F0"
    ).pack(anchor="w", padx=28)

    tk.Frame(
        ventana,
        bg=COLOR_ACENTO,
        height=4
    ).pack(fill="x")

    # --------------------------------------------------------
    # CONTENIDO
    # --------------------------------------------------------
    contenido = tk.Frame(ventana, bg=COLOR_FONDO)

    # Se coloca inicialmente. Al final se reorganiza para reservar
    # espacio al pie de la ventana.
    contenido.pack(
        fill="both",
        expand=True,
        padx=23,
        pady=14
    )

    # --------------------------------------------------------
    # RESUMEN DEL INVENTARIO
    # --------------------------------------------------------
    crear_titulo(
        contenido,
        "Resumen del inventario"
    ).pack(anchor="w", pady=(0, 8))

    frame_resumen = tk.Frame(contenido, bg=COLOR_FONDO)
    frame_resumen.pack(fill="x", pady=(0, 14))

    for columna in range(3):
        frame_resumen.grid_columnconfigure(
            columna,
            weight=1,
            uniform="resumen"
        )

    def crear_tarjeta(columna, titulo, color):
        tarjeta = tk.Frame(
            frame_resumen,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1,
            bd=0
        )
        tarjeta.grid(
            row=0,
            column=columna,
            sticky="nsew",
            padx=6,
            pady=3
        )

        tk.Frame(tarjeta, bg=color, height=4).pack(fill="x")

        tk.Label(
            tarjeta,
            text=titulo,
            font=(FUENTE, 10),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE
        ).pack(anchor="w", padx=15, pady=(12, 3))

        numero = tk.Label(
            tarjeta,
            text="0",
            font=(FUENTE, 23, "bold"),
            bg=COLOR_PANEL,
            fg=color
        )
        numero.pack(anchor="w", padx=15, pady=(0, 12))

        return numero

    etiqueta_total = crear_tarjeta(
        0, "Productos registrados", COLOR_PRINCIPAL
    )
    etiqueta_bajo = crear_tarjeta(
        1, "Productos con stock bajo", COLOR_ACENTO_HOVER
    )
    etiqueta_agotados = crear_tarjeta(
        2, "Productos agotados", COLOR_ROJO
    )

    # --------------------------------------------------------
    # PANEL DE BOTONES DE ACCIÓN
    # --------------------------------------------------------
    panel_acciones = tk.Frame(
        contenido,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    panel_acciones.pack(fill="x", pady=(0, 12))

    panel_acciones.grid_columnconfigure(
        0, weight=1, uniform="acciones"
    )
    panel_acciones.grid_columnconfigure(
        1, weight=1, uniform="acciones"
    )

    # --------------------------------------------------------
    # PANEL DE TABLA
    # --------------------------------------------------------
    panel_tabla = tk.Frame(
        contenido,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    panel_tabla.pack(fill="both", expand=True)

    encabezado_tabla = tk.Frame(panel_tabla, bg=COLOR_PANEL)
    encabezado_tabla.pack(fill="x", padx=13, pady=10)

    tk.Label(
        encabezado_tabla,
        text="Inventario de productos",
        font=(FUENTE, 13, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_PRINCIPAL
    ).pack(side="left")

    etiqueta_resultados = tk.Label(
        encabezado_tabla,
        text="0 productos",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE
    )
    etiqueta_resultados.pack(side="right")

    # --------------------------------------------------------
    # BÚSQUEDA Y FILTRO
    # --------------------------------------------------------
    frame_filtros = tk.Frame(panel_tabla, bg=COLOR_PANEL)
    frame_filtros.pack(fill="x", padx=13, pady=(0, 12))

    tk.Label(
        frame_filtros,
        text="Buscar producto:",
        font=(FUENTE, 9, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).pack(side="left", padx=(0, 8))

    entrada_busqueda = ttk.Entry(frame_filtros, font=(FUENTE, 10))
    entrada_busqueda.pack(
        side="left",
        fill="x",
        expand=True,
        ipady=4,
        padx=(0, 15)
    )

    tk.Label(
        frame_filtros,
        text="Categoría:",
        font=(FUENTE, 9, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).pack(side="left", padx=(0, 8))

    variable_filtro_categoria = tk.StringVar(
        value="Todas las categorías"
    )

    combo_filtro_categoria = ttk.Combobox(
        frame_filtros,
        textvariable=variable_filtro_categoria,
        state="readonly",
        width=22
    )
    combo_filtro_categoria.pack(side="left")
    combo_filtro_categoria["values"] = ("Todas las categorías",)

    # --------------------------------------------------------
    # TABLA DE PRODUCTOS
    # --------------------------------------------------------
    frame_tabla = tk.Frame(panel_tabla, bg=COLOR_PANEL)
    frame_tabla.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(0, 10)
    )

    columnas = (
        "id", "nombre", "marca", "categoria",
        "compra", "venta", "stock", "proveedor", "estado"
    )

    tabla = ttk.Treeview(
        frame_tabla,
        columns=columnas,
        show="headings",
        style="Inventario.Treeview",
        selectmode="browse"
    )

    # --------------------------------------------------------
    # COLORES DEL TEXTO SEGÚN EL NIVEL DE STOCK
    # --------------------------------------------------------
    tabla.tag_configure(
        "disponible",
        foreground=COLOR_VERDE
    )

    tabla.tag_configure(
        "bajo",
        foreground=COLOR_ACENTO_HOVER
    )

    tabla.tag_configure(
        "agotado",
        foreground=COLOR_ROJO
    )

    encabezados_tabla = {
        "id": "ID",
        "nombre": "Nombre",
        "marca": "Marca",
        "categoria": "Categoría",
        "compra": "Precio compra",
        "venta": "Precio venta",
        "stock": "Stock",
        "proveedor": "Proveedor(es)",
        "estado": "Estado"
    }

    for columna, titulo in encabezados_tabla.items():
        tabla.heading(columna, text=titulo)

    anchos = {
        "id": 48,
        "nombre": 155,
        "marca": 90,
        "categoria": 110,
        "compra": 100,
        "venta": 100,
        "stock": 60,
        "proveedor": 180,
        "estado": 95
    }

    for columna, ancho in anchos.items():
        tabla.column(
            columna,
            width=ancho,
            minwidth=45,
            anchor=(
                "center"
                if columna in ("id", "stock", "estado")
                else "w"
            )
        )

    barra_y = ttk.Scrollbar(
        frame_tabla,
        orient="vertical",
        command=tabla.yview
    )
    barra_x = ttk.Scrollbar(
        frame_tabla,
        orient="horizontal",
        command=tabla.xview
    )

    tabla.configure(
        yscrollcommand=barra_y.set,
        xscrollcommand=barra_x.set
    )

    tabla.grid(row=0, column=0, sticky="nsew")
    barra_y.grid(row=0, column=1, sticky="ns")
    barra_x.grid(row=1, column=0, sticky="ew")

    frame_tabla.grid_rowconfigure(0, weight=1)
    frame_tabla.grid_columnconfigure(0, weight=1)

    # ========================================================
    # FILTRO DE CATEGORÍAS
    # ========================================================
    categorias_por_id_filtro = {}

    def actualizar_filtro_categorias():
        try:
            categorias = obtener_catalogos()
            categoria_actual = variable_filtro_categoria.get().strip()

            categorias_por_id_filtro.clear()

            for categoria in categorias:
                nombre = str(categoria["nombre"]).strip()
                id_categoria = int(categoria["id_categoria"])
                categorias_por_id_filtro[nombre] = id_categoria

            opciones = (
                ["Todas las categorías"]
                + list(categorias_por_id_filtro.keys())
            )
            combo_filtro_categoria["values"] = opciones

            if categoria_actual in opciones:
                combo_filtro_categoria.set(categoria_actual)
            else:
                combo_filtro_categoria.set("Todas las categorías")

        except Error as error:
            mostrar_error_bd(error, ventana)

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar las categorías.\n\n{error}",
                parent=ventana
            )

    # ========================================================
    # CARGAR PRODUCTOS EN LA TABLA
    # ========================================================
    def cargar_productos():
        try:
            productos = consultar_productos(estado=ESTADO_ACTIVO)

            texto_busqueda = entrada_busqueda.get().strip().casefold()
            categoria_seleccionada = combo_filtro_categoria.get().strip()

            productos_filtrados = []

            for producto in productos:
                nombre_producto = str(
                    producto.get("nombre") or ""
                ).strip().casefold()

                marca_producto = str(
                    producto.get("marca") or ""
                ).strip().casefold()

                id_producto = str(
                    producto.get("id_producto") or ""
                ).strip()

                proveedor_producto = str(
                    producto.get("proveedor") or ""
                ).strip().casefold()

                if (
                    categoria_seleccionada == "Todas las categorías"
                    or not categoria_seleccionada
                ):
                    coincide_categoria = True
                else:
                    id_categoria_seleccionada = (
                        categorias_por_id_filtro.get(
                            categoria_seleccionada
                        )
                    )

                    try:
                        id_categoria_producto = int(
                            producto["id_categoria"]
                        )
                    except (ValueError, TypeError, KeyError):
                        id_categoria_producto = None

                    coincide_categoria = (
                        id_categoria_seleccionada is not None
                        and id_categoria_producto
                        == int(id_categoria_seleccionada)
                    )

                coincide_busqueda = (
                    not texto_busqueda
                    or texto_busqueda in id_producto.casefold()
                    or texto_busqueda in nombre_producto
                    or texto_busqueda in marca_producto
                    or texto_busqueda in proveedor_producto
                )

                if coincide_categoria and coincide_busqueda:
                    productos_filtrados.append(producto)

            tabla.delete(*tabla.get_children())

            total = len(productos_filtrados)
            stock_bajo = 0
            agotados = 0

            for producto in productos_filtrados:
                cantidad = int(producto["cantidad_stock"] or 0)
                minimo = int(producto["stock_minimo"] or 0)

                if cantidad <= 0:
                    estado_texto = "Agotado"
                    etiqueta = "agotado"
                    agotados += 1
                elif cantidad <= minimo:
                    estado_texto = "Stock bajo"
                    etiqueta = "bajo"
                    stock_bajo += 1
                else:
                    estado_texto = "Disponible"
                    etiqueta = "disponible"

                compra = f"${Decimal(str(producto['precio_compra'])):,.2f}"
                venta = f"${Decimal(str(producto['precio_venta'])):,.2f}"

                tabla.insert(
                    "",
                    "end",
                    iid=str(producto["id_producto"]),
                    values=(
                        producto["id_producto"],
                        producto["nombre"],
                        producto["marca"] or "",
                        producto["categoria"] or "",
                        compra,
                        venta,
                        cantidad,
                        producto["proveedor"],
                        estado_texto
                    ),
                    tags=(etiqueta,)
                )

            etiqueta_total.config(text=str(total))
            etiqueta_bajo.config(text=str(stock_bajo))
            etiqueta_agotados.config(text=str(agotados))

            etiqueta_resultados.config(
                text=f"{total} producto{'s' if total != 1 else ''}"
            )

        except Error as error:
            messagebox.showerror(
                "Error al consultar productos",
                "No se pudieron consultar los productos de la base de datos.\n\n"
                "Verifica que las tablas y columnas utilizadas coincidan "
                "con tu esquema.\n\n"
                f"{error}",
                parent=ventana
            )

        except Exception as error:
            messagebox.showerror(
                "Error al cargar el inventario",
                f"No se pudo cargar el inventario.\n\n{error}",
                parent=ventana
            )

    def probar_filtro_categoria(event=None):
        variable_filtro_categoria.set(
            combo_filtro_categoria.get().strip()
        )
        cargar_productos()

    combo_filtro_categoria.bind(
        "<<ComboboxSelected>>",
        probar_filtro_categoria
    )

    # ========================================================
    # FORMULARIO DE PRODUCTOS
    # ========================================================
    def formulario_producto(id_producto=None):
        producto = None

        if id_producto is not None:
            try:
                producto = obtener_producto(id_producto)
            except Error as error:
                mostrar_error_bd(error, ventana)
                return

            if not producto:
                messagebox.showwarning(
                    "Producto no encontrado",
                    "El producto seleccionado ya no existe o está desactivado.",
                    parent=ventana
                )
                cargar_productos()
                return

        try:
            categorias = obtener_catalogos()
            proveedores = obtener_proveedores_activos()

        except Error as error:
            mostrar_error_bd(error, ventana)
            return

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar los catálogos.\n\n{error}",
                parent=ventana
            )
            return

        if not categorias:
            messagebox.showwarning(
                "Categorías necesarias",
                "Primero registra al menos una categoría.",
                parent=ventana
            )
            return

        if not proveedores:
            messagebox.showwarning(
                "Proveedores necesarios",
                "Primero registra y activa al menos un proveedor.",
                parent=ventana
            )
            return

        formulario = tk.Toplevel(ventana)
        formulario.title(
            "Modificar producto" if producto else "Registrar producto"
        )
        formulario.configure(bg=COLOR_FONDO)
        registrar_ventana_tema(formulario)
        formulario.resizable(False, False)
        formulario.transient(ventana)
        formulario.grab_set()
        centrar_ventana(formulario, 620, 720)

        cabecera = tk.Frame(
            formulario,
            bg=COLOR_PRINCIPAL,
            height=100
        )
        cabecera.pack(fill="x")
        cabecera.pack_propagate(False)

        tk.Label(
            cabecera,
            text="PAPELERÍA LUNA / INVENTARIO",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PRINCIPAL,
            fg=COLOR_ACENTO
        ).pack(anchor="w", padx=22, pady=(9, 0))

        tk.Label(
            cabecera,
            text="Modificar producto" if producto else "Registrar producto",
            font=(FUENTE, 18, "bold"),
            bg=COLOR_PRINCIPAL,
            fg="#FFFFFF"
        ).pack(anchor="w", padx=22, pady=(0, 2))

        tk.Label(
            cabecera,
            text="Completa los datos del producto",
            font=(FUENTE, 9),
            bg=COLOR_PRINCIPAL,
            fg="#E2E8F0"
        ).pack(anchor="w", padx=23)

        tk.Frame(
            formulario,
            bg=COLOR_ACENTO,
            height=4
        ).pack(fill="x")

        contenedor = tk.Frame(
            formulario,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        contenedor.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=14
        )
        contenedor.grid_columnconfigure(1, weight=1)

        variables = {}
        fila = 0

        def campo(clave, texto, valor=""):
            nonlocal fila

            tk.Label(
                contenedor,
                text=texto,
                font=(FUENTE, 9, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO
            ).grid(
                row=fila,
                column=0,
                sticky="w",
                padx=(12, 10),
                pady=6
            )

            entrada = ttk.Entry(contenedor, font=(FUENTE, 10))
            entrada.grid(
                row=fila,
                column=1,
                sticky="ew",
                padx=(0, 12),
                pady=6,
                ipady=3
            )

            if valor is not None and str(valor) != "":
                entrada.insert(0, str(valor))

            variables[clave] = entrada
            fila += 1

        # ----------------------------------------------------
        # PROVEEDOR
        # ----------------------------------------------------
        tk.Label(
            contenedor,
            text="Proveedor",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).grid(
            row=fila,
            column=0,
            sticky="w",
            padx=(12, 10),
            pady=6
        )

        # Mostrar nombre e identificador para distinguir
        # proveedores que tengan nombres iguales.
        proveedores_por_opcion = {
            f"{p['nombre']} (ID: {p['id_proveedor']})":
                int(p["id_proveedor"])
            for p in proveedores
        }

        combo_proveedor = ttk.Combobox(
            contenedor,
            values=list(proveedores_por_opcion.keys()),
            state="readonly",
            font=(FUENTE, 10)
        )

        combo_proveedor.grid(
            row=fila,
            column=1,
            sticky="ew",
            padx=(0, 12),
            pady=6,
            ipady=3
        )

        # Al modificar, seleccionar el proveedor que ya tiene.
        if producto and producto.get("id_proveedor") is not None:
            proveedor_actual = int(producto["id_proveedor"])

            opcion_actual = next(
                (
                    opcion
                    for opcion, id_proveedor
                    in proveedores_por_opcion.items()
                    if id_proveedor == proveedor_actual
                ),
                None
            )

            if opcion_actual:
                combo_proveedor.set(opcion_actual)
            else:
                combo_proveedor.current(0)

        else:
            # Al registrar, seleccionar el primer proveedor.
            combo_proveedor.current(0)

        fila += 1

        if producto:
            tk.Label(
                contenedor,
                text="ID del producto",
                font=(FUENTE, 9, "bold"),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO
            ).grid(
                row=fila,
                column=0,
                sticky="w",
                padx=(12, 10),
                pady=6
            )

            tk.Label(
                contenedor,
                text=str(producto["id_producto"]),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO_SUAVE,
                font=(FUENTE, 10)
            ).grid(
                row=fila,
                column=1,
                sticky="w",
                padx=(0, 12),
                pady=6
            )
            fila += 1

        campo("nombre", "Nombre", producto["nombre"] if producto else "")
        campo("marca", "Marca", producto["marca"] if producto else "")
        campo(
            "compra",
            "Precio de compra",
            producto["precio_compra"] if producto else ""
        )
        campo(
            "venta",
            "Precio de venta",
            producto["precio_venta"] if producto else ""
        )
        # ----------------------------------------------------
        # STOCK ACTUAL: SOLO LECTURA
        # ----------------------------------------------------
        stock_actual = (
            int(producto["cantidad_stock"] or 0)
            if producto else 0
        )

        tk.Label(
            contenedor,
            text="Stock actual (solo lectura)",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).grid(
            row=fila,
            column=0,
            sticky="w",
            padx=(12, 10),
            pady=6
        )

        tk.Label(
            contenedor,
            text=f"{stock_actual} unidades",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO_SUAVE,
            anchor="w",
            padx=8,
            relief="solid",
            bd=1
        ).grid(
            row=fila,
            column=1,
            sticky="ew",
            padx=(0, 12),
            pady=6,
            ipady=4
        )

        fila += 1

        campo(
            "minimo",
            "Stock mínimo",
            producto["stock_minimo"] if producto else "50"
        )

        tk.Label(
            contenedor,
            text="Categoría",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).grid(
            row=fila,
            column=0,
            sticky="w",
            padx=(12, 10),
            pady=6
        )

        categorias_por_nombre = {
            c["nombre"]: int(c["id_categoria"])
            for c in categorias
        }

        categoria_actual = ""

        if producto:
            id_categoria_actual = producto.get("id_categoria")

            for categoria in categorias:
                if int(categoria["id_categoria"]) == int(id_categoria_actual):
                    categoria_actual = categoria["nombre"]
                    break

        combo_categoria = ttk.Combobox(
            contenedor,
            values=list(categorias_por_nombre.keys()),
            state="readonly",
            font=(FUENTE, 10)
        )
        combo_categoria.grid(
            row=fila,
            column=1,
            sticky="ew",
            padx=(0, 12),
            pady=6,
            ipady=3
        )

        if categoria_actual:
            combo_categoria.set(categoria_actual)
        elif categorias:
            combo_categoria.current(0)

        fila += 1

        tk.Label(
            contenedor,
            text="Descripción",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).grid(
            row=fila,
            column=0,
            sticky="nw",
            padx=(12, 10),
            pady=6
        )

        entrada_descripcion = tk.Text(
            contenedor,
            height=3,
            font=(FUENTE, 10),
            wrap="word",
            relief="solid",
            bd=1,
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        entrada_descripcion.grid(
            row=fila,
            column=1,
            sticky="ew",
            padx=(0, 12),
            pady=6
        )

        if producto and producto["descripcion"]:
            entrada_descripcion.insert("1.0", producto["descripcion"])

        # ----------------------------------------------------
        # VALIDACIÓN Y GUARDADO DEL PRODUCTO
        # ----------------------------------------------------
        def guardar():
            try:
                nombre = variables["nombre"].get().strip()
                marca = variables["marca"].get().strip()
                descripcion = entrada_descripcion.get(
                    "1.0", "end-1c"
                ).strip()

                if not nombre:
                    messagebox.showwarning(
                        "Campo obligatorio",
                        "El campo Nombre está vacío. Escribe el nombre del producto.",
                        parent=formulario
                    )
                    variables["nombre"].focus_set()
                    return

                if len(nombre) > 100:
                    raise ValueError("El nombre admite 100 caracteres.")

                if len(marca) > 50:
                    raise ValueError("La marca admite 50 caracteres.")

                if len(descripcion) > 255:
                    raise ValueError("La descripción admite 255 caracteres.")

                categoria_seleccionada = combo_categoria.get().strip()

                if not categoria_seleccionada:
                    messagebox.showwarning(
                        "Categoría obligatoria",
                        "Selecciona una categoría antes de guardar.",
                        parent=formulario
                    )
                    combo_categoria.focus_set()
                    return

                categoria_id = categorias_por_nombre.get(
                    categoria_seleccionada
                )

                if categoria_id is None:
                    messagebox.showwarning(
                        "Categoría inválida",
                        "La categoría seleccionada no se encuentra en la lista.",
                        parent=formulario
                    )
                    combo_categoria.focus_set()
                    return

                # ------------------------------------------------
                # VALIDAR PROVEEDOR
                # ------------------------------------------------
                opcion_proveedor = combo_proveedor.get().strip()

                proveedor_id = proveedores_por_opcion.get(
                    opcion_proveedor
                )

                if proveedor_id is None:
                    messagebox.showwarning(
                        "Proveedor obligatorio",
                        "Selecciona un proveedor para el producto.",
                        parent=formulario
                    )
                    combo_proveedor.focus_set()
                    return

                try:
                    compra = Decimal(variables["compra"].get().strip())
                    venta = Decimal(variables["venta"].get().strip())
                except (InvalidOperation, ValueError):
                    raise ValueError(
                        "Los precios deben ser números válidos."
                    )

                if not compra.is_finite() or not venta.is_finite():
                    raise ValueError("Los precios no son válidos.")

                if compra < 0 or venta < 0:
                    raise ValueError("Los precios no pueden ser negativos.")

                limite_precio = Decimal("99999999.99")

                if compra > limite_precio or venta > limite_precio:
                    raise ValueError("El precio supera el límite permitido.")

                if (
                    compra.as_tuple().exponent < -2
                    or venta.as_tuple().exponent < -2
                ):
                    raise ValueError(
                        "Los precios admiten máximo dos decimales."
                    )

                # ------------------------------------------------
                # VALIDAR STOCK MÍNIMO
                # El stock actual no se modifica aquí.
                # ------------------------------------------------
                try:
                    minimo = int(
                        variables["minimo"].get().strip()
                    )
                except ValueError:
                    raise ValueError(
                        "El stock mínimo debe ser un número entero."
                    )

                if minimo < 0:
                    raise ValueError(
                        "El stock mínimo no puede ser negativo."
                    )

                # Productos no contiene id_proveedor.
                # La relación con proveedores se consulta mediante pedidos.
                datos = (
                    nombre,
                    marca or None,
                    descripcion or None,
                    compra,
                    venta,
                    minimo,
                    categoria_id,
                    proveedor_id
                )

                resultado = guardar_producto(
                    datos,
                    producto["id_producto"] if producto else None
                )

                if not resultado:
                    return

                formulario.destroy()
                cargar_productos()

                messagebox.showinfo(
                    "Operación completada",
                    (
                        "El producto se modificó correctamente."
                        if producto
                        else "El producto se registró correctamente."
                    ),
                    parent=ventana
                )

            except ValueError as error:
                messagebox.showwarning(
                    "Revisa los datos",
                    str(error),
                    parent=formulario
                )

            except Error as error:
                mostrar_error_bd(error, formulario)

            except Exception as error:
                messagebox.showerror(
                    "Error al guardar",
                    f"No se pudo guardar el producto.\n\n{error}",
                    parent=formulario
                )

        # ----------------------------------------------------
        # DESACTIVAR DESDE EL FORMULARIO
        # ----------------------------------------------------
        def desactivar_desde_formulario():
            if not producto:
                return

            if not messagebox.askyesno(
                "Desactivar producto",
                f"¿Deseas desactivar '{producto['nombre']}'?\n\n"
                "El producto dejará de aparecer en el inventario activo, "
                "pero podrás recuperarlo después.",
                parent=formulario
            ):
                return

            try:
                eliminar_producto_bd(producto["id_producto"])
                formulario.destroy()
                cargar_productos()

                messagebox.showinfo(
                    "Producto desactivado",
                    "El producto se desactivó correctamente. "
                    "Puedes recuperarlo desde «Productos desactivados».",
                    parent=ventana
                )

            except Error as error:
                mostrar_error_bd(error, formulario)

            except ValueError as error:
                messagebox.showwarning(
                    "No se pudo desactivar",
                    str(error),
                    parent=formulario
                )

            except Exception as error:
                messagebox.showerror(
                    "Error",
                    f"No se pudo desactivar el producto.\n\n{error}",
                    parent=formulario
                )

        # ----------------------------------------------------
        # BOTONES DEL FORMULARIO
        # ----------------------------------------------------
        botones_form = tk.Frame(formulario, bg=COLOR_FONDO)
        botones_form.pack(fill="x", padx=18, pady=(0, 14))

        if producto:
            crear_boton(
                botones_form,
                "Desactivar producto",
                desactivar_desde_formulario,
                COLOR_ROJO,
                COLOR_ROJO_HOVER
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 5)
            )

        crear_boton(
            botones_form,
            "Guardar cambios" if producto else "Guardar producto",
            guardar,
            COLOR_PRINCIPAL,
            COLOR_SECUNDARIO
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        crear_boton(
            botones_form,
            "Cancelar",
            formulario.destroy,
            COLOR_ACENTO,
            COLOR_ACENTO_HOVER
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(5, 0)
        )

    # ========================================================
    # ACCIONES DE PRODUCTOS
    # ========================================================
    def registrar_producto():
        formulario_producto()

    def obtener_id_seleccionado():
        seleccion = tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona un producto",
                "Primero selecciona un producto de la tabla.",
                parent=ventana
            )
            return None

        return int(seleccion[0])

    def modificar_producto():
        id_producto = obtener_id_seleccionado()

        if id_producto is not None:
            formulario_producto(id_producto)

    def eliminar_producto():
        id_producto = obtener_id_seleccionado()

        if id_producto is None:
            return

        try:
            producto = obtener_producto(id_producto)

            if not producto:
                messagebox.showwarning(
                    "Producto no encontrado",
                    "El producto ya no existe o está desactivado.",
                    parent=ventana
                )
                cargar_productos()
                return

            if not messagebox.askyesno(
                "Confirmar desactivación",
                f"¿Deseas desactivar el producto '{producto['nombre']}'?\n\n"
                "Podrás recuperarlo posteriormente.",
                parent=ventana
            ):
                return

            eliminar_producto_bd(id_producto)
            cargar_productos()

            messagebox.showinfo(
                "Producto desactivado",
                "El producto se desactivó correctamente.",
                parent=ventana
            )

        except Error as error:
            if getattr(error, "errno", None) == 1451:
                messagebox.showwarning(
                    "No se puede completar la operación",
                    "El producto tiene registros relacionados con ventas, "
                    "pedidos o movimientos de inventario.",
                    parent=ventana
                )
            else:
                mostrar_error_bd(error, ventana)

        except ValueError as error:
            messagebox.showwarning(
                "No se pudo desactivar",
                str(error),
                parent=ventana
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudo desactivar el producto.\n\n{error}",
                parent=ventana
            )

    # ========================================================
    # GESTIÓN DE CATEGORÍAS
    # ========================================================
    def gestionar_categorias():
        abrir_categorias(
            ventana,
            al_actualizar=actualizar_despues_de_categorias
        )

    def actualizar_despues_de_categorias():
        actualizar_filtro_categorias()
        cargar_productos()

    # ========================================================
    # PRODUCTOS DESACTIVADOS
    # ========================================================
    def ver_productos_desactivados():
        ventana_inactivos = tk.Toplevel(ventana)
        ventana_inactivos.title(
            "Papelería Luna | Productos desactivados"
        )
        ventana_inactivos.configure(bg=COLOR_FONDO)
        registrar_ventana_tema(ventana_inactivos)
        ventana_inactivos.minsize(650, 400)
        centrar_ventana(ventana_inactivos, 850, 500)
        ventana_inactivos.transient(ventana)

        # ----------------------------------------------------
        # ENCABEZADO
        # ----------------------------------------------------
        encabezado_inactivos = tk.Frame(
            ventana_inactivos,
            bg=COLOR_PRINCIPAL,
            height=100
        )
        encabezado_inactivos.pack(fill="x")
        encabezado_inactivos.pack_propagate(False)

        tk.Label(
            encabezado_inactivos,
            text="PAPELERÍA LUNA / INVENTARIO",
            font=(FUENTE, 9, "bold"),
            bg=COLOR_PRINCIPAL,
            fg=COLOR_ACENTO
        ).pack(anchor="w", padx=20, pady=(9, 0))

        tk.Label(
            encabezado_inactivos,
            text="Productos desactivados",
            font=(FUENTE, 18, "bold"),
            bg=COLOR_PRINCIPAL,
            fg="#FFFFFF"
        ).pack(anchor="w", padx=20, pady=(0, 2))

        tk.Label(
            encabezado_inactivos,
            text="Selecciona un producto para recuperarlo",
            font=(FUENTE, 9),
            bg=COLOR_PRINCIPAL,
            fg="#E2E8F0"
        ).pack(anchor="w", padx=21)

        tk.Frame(
            ventana_inactivos,
            bg=COLOR_ACENTO,
            height=4
        ).pack(fill="x")

        # ----------------------------------------------------
        # PIE: SE EMPAQUETA ANTES DE LA TABLA
        # ----------------------------------------------------
        pie_inactivos = tk.Frame(
            ventana_inactivos,
            bg=COLOR_FONDO
        )
        pie_inactivos.pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # TABLA DE PRODUCTOS DESACTIVADOS
        # ----------------------------------------------------
        contenedor_inactivos = tk.Frame(
            ventana_inactivos,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        contenedor_inactivos.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(15, 10)
        )

        columnas_inactivos = ("id", "nombre", "categoria", "stock")

        tabla_inactivos = ttk.Treeview(
            contenedor_inactivos,
            columns=columnas_inactivos,
            show="headings",
            selectmode="browse",
            style="Inventario.Treeview"
        )

        tabla_inactivos.heading("id", text="ID")
        tabla_inactivos.heading("nombre", text="Producto")
        tabla_inactivos.heading("categoria", text="Categoría")
        tabla_inactivos.heading("stock", text="Stock")

        tabla_inactivos.column("id", width=60, anchor="center")
        tabla_inactivos.column("nombre", width=280)
        tabla_inactivos.column("categoria", width=200)
        tabla_inactivos.column("stock", width=90, anchor="center")

        barra_inactivos = ttk.Scrollbar(
            contenedor_inactivos,
            orient="vertical",
            command=tabla_inactivos.yview
        )
        tabla_inactivos.configure(
            yscrollcommand=barra_inactivos.set
        )

        tabla_inactivos.pack(
            side="left",
            fill="both",
            expand=True
        )
        barra_inactivos.pack(side="right", fill="y")

        # ----------------------------------------------------
        # CARGAR PRODUCTOS DESACTIVADOS
        # ----------------------------------------------------
        def cargar_inactivos():
            tabla_inactivos.delete(
                *tabla_inactivos.get_children()
            )

            try:
                productos = consultar_productos(
                    estado=ESTADO_INACTIVO
                )

                for producto in productos:
                    tabla_inactivos.insert(
                        "",
                        "end",
                        iid=str(producto["id_producto"]),
                        values=(
                            producto["id_producto"],
                            producto["nombre"],
                            producto["categoria"] or "",
                            producto["cantidad_stock"]
                        )
                    )

            except Error as error:
                mostrar_error_bd(error, ventana_inactivos)

            except Exception as error:
                messagebox.showerror(
                    "Error",
                    f"No se pudieron cargar los productos desactivados.\n\n{error}",
                    parent=ventana_inactivos
                )

        # ----------------------------------------------------
        # RECUPERAR PRODUCTO SELECCIONADO
        # ----------------------------------------------------
        def recuperar_seleccionado():
            seleccion = tabla_inactivos.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selecciona un producto",
                    "Selecciona el producto que deseas recuperar.",
                    parent=ventana_inactivos
                )
                return

            id_producto = int(seleccion[0])
            valores = tabla_inactivos.item(seleccion[0], "values")
            nombre = valores[1]

            if not messagebox.askyesno(
                "Confirmar recuperación",
                f"¿Deseas recuperar el producto '{nombre}'?",
                parent=ventana_inactivos
            ):
                return

            try:
                recuperar_producto_bd(id_producto)
                cargar_inactivos()
                cargar_productos()

                messagebox.showinfo(
                    "Producto recuperado",
                    f"'{nombre}' volvió al inventario activo.",
                    parent=ventana_inactivos
                )

            except Error as error:
                mostrar_error_bd(error, ventana_inactivos)

            except ValueError as error:
                messagebox.showwarning(
                    "No se pudo recuperar",
                    str(error),
                    parent=ventana_inactivos
                )

            except Exception as error:
                messagebox.showerror(
                    "Error",
                    f"No se pudo recuperar el producto.\n\n{error}",
                    parent=ventana_inactivos
                )

        crear_boton(
            pie_inactivos,
            "Recuperar producto",
            recuperar_seleccionado,
            COLOR_PRINCIPAL,
            COLOR_SECUNDARIO
        ).pack(side="left")

        crear_boton(
            pie_inactivos,
            "Cerrar",
            ventana_inactivos.destroy,
            COLOR_ACENTO,
            COLOR_ACENTO_HOVER
        ).pack(side="right")

        cargar_inactivos()

    # ========================================================
    # BOTONES DE ACCIÓN DEL INVENTARIO
    # ========================================================
    crear_boton(
        panel_acciones,
        "Registrar producto",
        registrar_producto,
        COLOR_SECUNDARIO,
        COLOR_PRINCIPAL
    ).grid(
        row=0,
        column=0,
        sticky="ew",
        padx=(10, 5),
        pady=(10, 5)
    )

    crear_boton(
        panel_acciones,
        "Modificar producto",
        modificar_producto,
        COLOR_ACENTO,
        COLOR_ACENTO_HOVER,
        color_texto="#FFFFFF"
    ).grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(5, 10),
        pady=(10, 5)
    )

    crear_boton(
        panel_acciones,
        "Productos desactivados",
        ver_productos_desactivados,
        COLOR_ACENTO,
        COLOR_ACENTO_HOVER
    ).grid(
        row=1,
        column=0,
        sticky="ew",
        padx=(10, 5),
        pady=(5, 10)
    )

    crear_boton(
        panel_acciones,
        "Gestionar categorías",
        gestionar_categorias,
        COLOR_SECUNDARIO,
        COLOR_PRINCIPAL
    ).grid(
        row=1,
        column=1,
        sticky="ew",
        padx=(5, 10),
        pady=(5, 10)
    )

    # ========================================================
    # PIE DEL INVENTARIO
    # ========================================================
    pie = tk.Frame(
        ventana,
        bg=COLOR_FONDO,
        height=55
    )
    pie.pack_propagate(False)

    tk.Frame(
        pie,
        bg=COLOR_ACENTO,
        height=3
    ).pack(side="top", fill="x")

    def salir():
        if messagebox.askyesno(
            "Salir del inventario",
            "¿Deseas cerrar la ventana del inventario?",
            parent=ventana
        ):
            ventana.destroy()

    boton_salir = crear_boton(
        pie,
        "Salir",
        salir,
        COLOR_SECUNDARIO,
        COLOR_ACENTO_HOVER
    )
    boton_salir.pack(side="right", padx=15, pady=2)

    tk.Label(
        pie,
        text="Papelería Luna | Sistema de inventario",
        bg=COLOR_FONDO,
        fg=COLOR_TEXTO_SUAVE,
        font=(FUENTE, 9)
    ).pack(side="left", padx=15, pady=2)

    # IMPORTANTE: reservar el espacio inferior para el pie.
    # Se reempaqueta el contenido después del pie para que este
    # no quede oculto por el área expandible.
    # Reservar espacio para el pie de ventana
    pie.pack(
        side="bottom",
        fill="x",
        expand=False
    )

    contenido.pack(
        side="top",
        fill="both",
        expand=True,
        padx=23,
        pady=14
    )
    
    # ========================================================
    # CARGA INICIAL Y EVENTOS
    # ========================================================
    actualizar_filtro_categorias()

    entrada_busqueda.bind(
        "<KeyRelease>",
        lambda evento: cargar_productos()
    )

    cargar_productos()

    # Iniciar el bucle principal únicamente si esta función creó Tk.
    if es_ventana_principal:
        ventana.mainloop()

