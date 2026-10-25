import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime

from tema import (
    obtener_colores,
    obtener_tema_actual,
    registrar_observador,
    eliminar_observador
)


# ============================================================
# CONEXIÓN CON MARIADB
# ============================================================

def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Papeleria_Luna",
        connection_timeout=10
    )


# ============================================================
# MÓDULO DE VENTAS
# ============================================================


def abrir_ventas(parent=None, identificacion_empleado=None):

    ESTADO_ACTIVO = 0
    VENTA_VIGENTE = 0
    VENTA_CANCELADA = 1

    # ========================================================
    # COLORES Y TEMA
    # ========================================================

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

    # Se conservan los colores turquesa propios de ventas.
    COLOR_TURQUESA = "#0F766E"
    COLOR_TURQUESA_HOVER = "#115E59"

    FUENTE = "Arial"


    ventana = tk.Toplevel(parent) if parent else tk.Tk()
    ventana.title("Ventas | Papelería Luna")
    ventana.configure(bg=COLOR_FONDO)
    ventana.geometry("1250x800")
    ventana.minsize(1100, 700)
    ventana.resizable(True, True)

    def centrar_ventana(win, ancho, alto):
        win.update_idletasks()
        x = (win.winfo_screenwidth() - ancho) // 2
        y = (win.winfo_screenheight() - alto) // 2
        win.geometry(f"{ancho}x{alto}+{x}+{y}")

    centrar_ventana(ventana, 1250, 800)

    # ========================================================
    # ESTILOS
    # ========================================================

    estilo = ttk.Style(ventana)

    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    estilo.configure(
        "Ventas.Treeview",
        background=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        fieldbackground=COLOR_PANEL,
        rowheight=31,
        font=(FUENTE, 10),
        borderwidth=0,
        relief="flat"
    )

    estilo.configure(
        "Ventas.Treeview.Heading",
        background=COLOR_PRINCIPAL,
        foreground="white",
        font=(FUENTE, 10, "bold"),
        padding=(9, 8),
        relief="flat"
    )

    estilo.map(
        "Ventas.Treeview",
        background=[("selected", COLOR_TURQUESA)],
        foreground=[("selected", "white")]
    )

    estilo.configure(
        "Ventas.TCombobox",
        padding=6,
        font=(FUENTE, 10)
    )

    # ========================================================
    # FUNCIONES VISUALES
    # ========================================================

    
    def boton_hover(boton, normal, hover):
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


    
    def crear_boton(
        padre, texto, comando,
        color=None,
        hover=None,
        ancho=16
    ):
        if color is None:
            color = COLOR_PRINCIPAL

        if hover is None:
            hover = COLOR_SECUNDARIO

        boton = tk.Button(
            padre,
            text=texto,
            command=comando,
            width=ancho,
            height=1,
            font=(FUENTE, 10, "bold"),
            bg=color,
            fg="white",
            activebackground=hover,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            takefocus=True
        )

        boton_hover(boton, color, hover)
        return boton

    def crear_etiqueta(padre, texto, negrita=False, color=None):
        return tk.Label(
            padre,
            text=texto,
            font=(FUENTE, 10, "bold" if negrita else "normal"),
            bg=COLOR_PANEL,
            fg=color or COLOR_TEXTO
        )

    # ========================================================
    # CONEXIÓN Y UTILIDADES
    # ========================================================

    def abrir_conexion():
        try:
            return conectar_bd()
        except mysql.connector.Error as error:
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar con MariaDB.\n\n{error}",
                parent=ventana
            )
            return None

    def mostrar_error_bd(titulo, error, padre):
        messagebox.showerror(
            titulo,
            f"Ocurrió un problema con la base de datos:\n\n{error}",
            parent=padre
        )

    def revertir_transaccion(conexion):
        if conexion:
            try:
                if conexion.is_connected():
                    conexion.rollback()
            except mysql.connector.Error:
                pass

    def convertir_id(texto, nombre):
        try:
            numero = int(texto)
            if numero <= 0:
                raise ValueError
            return numero
        except (ValueError, TypeError):
            raise ValueError(
                f"{nombre} debe ser un número entero positivo."
            )

    def convertir_cantidad(texto):
        try:
            cantidad = int(texto)
            if cantidad <= 0:
                raise ValueError
            return cantidad
        except (ValueError, TypeError):
            raise ValueError(
                "La cantidad debe ser un entero mayor que cero."
            )

    def dinero(valor):
        try:
            resultado = Decimal(str(valor))

            if not resultado.is_finite():
                raise InvalidOperation

            return resultado.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Se encontró un importe monetario inválido.")

    # ========================================================
    # CATÁLOGO DE PRODUCTOS
    # ========================================================

    def obtener_productos(busqueda=""):
        conexion = abrir_conexion()

        if not conexion:
            return []

        cursor = None

        try:
            cursor = conexion.cursor()
            texto = f"%{busqueda.strip()}%"

            cursor.execute("""
                SELECT
                    id_producto,
                    nombre,
                    marca,
                    precio_venta,
                    cantidad_stock,
                    stock_minimo
                FROM Productos
                WHERE estado = %s
                  AND (
                        CAST(id_producto AS CHAR) LIKE %s
                        OR nombre LIKE %s
                        OR COALESCE(marca, '') LIKE %s
                  )
                ORDER BY nombre
                LIMIT 50
            """, (
                ESTADO_ACTIVO,
                texto,
                texto,
                texto
            ))

            return cursor.fetchall()

        except mysql.connector.Error as error:
            mostrar_error_bd(
                "Error al buscar productos", error, ventana
            )
            return []

        finally:
            if cursor:
                cursor.close()

            try:
                if conexion.is_connected():
                    conexion.close()
            except mysql.connector.Error:
                pass

    # ========================================================
    # ENCABEZADO
    # ========================================================

    encabezado = tk.Frame(
        ventana,
        bg=COLOR_PRINCIPAL,
        height=65
    )
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA",
        font=(FUENTE, 19, "bold"),
        bg=COLOR_PRINCIPAL,
        fg="white"
    ).pack(anchor="w", padx=22, pady=(5, 0))

    tk.Label(
        encabezado,
        text="VENTAS  |  Registro y control de operaciones",
        font=(FUENTE, 10),
        bg=COLOR_PRINCIPAL,
        fg="#DBEAFE"
    ).pack(anchor="w", padx=23, pady=(0, 4))

    tk.Frame(
        ventana,
        bg=COLOR_ACENTO,
        height=5
    ).pack(fill="x")

    # ========================================================
    # CONTENEDOR PRINCIPAL
    # ========================================================

    contenido = tk.Frame(ventana, bg=COLOR_FONDO)
    contenido.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=(12, 5)
    )

    contenido.columnconfigure(0, weight=1)
    contenido.rowconfigure(0, weight=0)
    contenido.rowconfigure(1, weight=1)
    contenido.rowconfigure(2, weight=0, minsize=55)

    
    
    # ========================================================
    # DATOS DE LA VENTA
    # ========================================================

    panel_datos = tk.Frame(
        contenido,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )

    # Columna izquierda: empleado y cliente.
    # Columna derecha: método de pago.
    panel_datos.columnconfigure(0, weight=0)
    panel_datos.columnconfigure(1, weight=0)
    panel_datos.columnconfigure(2, weight=0)
    panel_datos.columnconfigure(3, weight=0)
    panel_datos.columnconfigure(4, weight=1)
    panel_datos.columnconfigure(5, weight=0)

    tk.Label(
        panel_datos,
        text="Datos de la venta",
        font=(FUENTE, 13, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_PRINCIPAL
    ).grid(
        row=0, column=0, columnspan=6,
        sticky="w", padx=18, pady=(6, 5)
    )

    # Se conserva internamente para el funcionamiento existente.
    fecha_actual = tk.StringVar(
        value=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    # --------------------------------------------------------
    # EMPLEADO: IDENTIFICACIÓN REAL Y NOMBRE
    # --------------------------------------------------------

    crear_etiqueta(
        panel_datos,
        "Identificación del empleado:",
        True
    ).grid(
        row=1, column=0,
        sticky="w", padx=(18, 8), pady=5
    )

    entrada_id_empleado = tk.Entry(
        panel_datos,
        font=(FUENTE, 10),
        relief="solid",
        bd=1,
        width=15,
        justify="center",
        state="readonly",
        readonlybackground="#F1F5F9"
    )

    entrada_id_empleado.grid(
        row=1, column=1,
        sticky="w", padx=(0, 12), pady=5, ipady=3
    )

    etiqueta_empleado = tk.Label(
        panel_datos,
        text="Empleado: detectando automáticamente...",
        font=(FUENTE, 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
        anchor="w"
    )

    etiqueta_empleado.grid(
        row=1, column=2, columnspan=3,
        sticky="ew", padx=(0, 18), pady=5
    )

    # --------------------------------------------------------
    # CLIENTE: IDENTIFICACIÓN, ID INTERNO Y NOMBRE
    # --------------------------------------------------------

    crear_etiqueta(
        panel_datos,
        "Identificación del cliente:",
        True
    ).grid(
        row=2, column=0,
        sticky="w", padx=(18, 8), pady=(4, 8)
    )

    entrada_identificacion_cliente = tk.Entry(
        panel_datos,
        font=(FUENTE, 10),
        relief="solid",
        bd=1,
        width=18
    )

    entrada_identificacion_cliente.grid(
        row=2, column=1,
        sticky="ew", padx=(0, 12), pady=(4, 8), ipady=3
    )

    crear_etiqueta(
        panel_datos,
        "ID cliente:",
        True
    ).grid(
        row=2, column=2,
        sticky="w", padx=(0, 6), pady=(4, 8)
    )

    entrada_id_cliente = tk.Entry(
        panel_datos,
        font=(FUENTE, 10),
        relief="solid",
        bd=1,
        width=7,
        justify="center",
        state="readonly",
        readonlybackground="#F1F5F9"
    )

    entrada_id_cliente.grid(
        row=2, column=3,
        sticky="w", padx=(0, 10), pady=(4, 8), ipady=3
    )

    etiqueta_cliente = tk.Label(
        panel_datos,
        text="Cliente: sin identificar",
        font=(FUENTE, 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
        anchor="w",
        justify="left",
        wraplength=350
    )

    etiqueta_cliente.grid(
        row=2, column=4,
        sticky="ew", padx=(0, 18), pady=(4, 8)
    )

    # --------------------------------------------------------
    # MÉTODO DE PAGO: LADO DERECHO
    # --------------------------------------------------------

    marco_pago = tk.Frame(
        panel_datos,
        bg=COLOR_PANEL
    )

    marco_pago.grid(
        row=1, column=5, rowspan=2,
        sticky="e", padx=(0, 18), pady=5
    )

    crear_etiqueta(
        marco_pago,
        "Método de pago:",
        True
    ).pack(anchor="w", pady=(0, 4))

    combo_pago = ttk.Combobox(
        marco_pago,
        values=["Efectivo", "Tarjeta", "Transferencia", "Otro"],
        state="readonly",
        font=(FUENTE, 10),
        style="Ventas.TCombobox",
        width=18
    )

    combo_pago.pack(fill="x")
    combo_pago.set("Efectivo")

    id_cliente_verificado = None
    id_empleado_verificado = None

    # Identificador del evento de consulta automática del cliente.
    consulta_cliente_pendiente = None

    panel_datos.grid(
        row=0, column=0, sticky="ew", pady=(0, 6)
    )

    # ========================================================
    # DETECCIÓN AUTOMÁTICA DEL EMPLEADO
    # ========================================================

    def detectar_empleado():
        nonlocal id_empleado_verificado

        id_empleado_verificado = None

        identificacion = (
            str(identificacion_empleado).strip()
            if identificacion_empleado
            else ""
        )

        if not identificacion:
            etiqueta_empleado.config(
                text="Empleado: sesión no identificada",
                fg=COLOR_ROJO
            )
            return

        conexion = abrir_conexion()

        if not conexion:
            etiqueta_empleado.config(
                text="Empleado: no se pudo verificar",
                fg=COLOR_ROJO
            )
            return

        cursor = None

        try:
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT
                    id_empleado,
                    identificacion,
                    nombre,
                    apellidos,
                    estado
                FROM Empleados
                WHERE identificacion = %s
                LIMIT 1
            """, (identificacion,))

            empleado = cursor.fetchone()

            if not empleado:
                etiqueta_empleado.config(
                    text="Empleado: no encontrado",
                    fg=COLOR_ROJO
                )
                return

            if int(empleado[4]) != ESTADO_ACTIVO:
                etiqueta_empleado.config(
                    text="Empleado: cuenta desactivada",
                    fg=COLOR_ROJO
                )
                return

            # ID interno para registrar la venta en la base de datos.
            id_empleado_verificado = int(empleado[0])

            # Identificación real del empleado, no el ID interno.
            identificacion_real = empleado[1]

            entrada_id_empleado.config(state="normal")
            entrada_id_empleado.delete(0, tk.END)
            entrada_id_empleado.insert(0, str(identificacion_real))
            entrada_id_empleado.config(state="readonly")

            nombre_completo = f"{empleado[2]} {empleado[3]}".strip()

            etiqueta_empleado.config(
                text=f"Empleado: {nombre_completo}",
                fg=COLOR_TURQUESA
            )

        except mysql.connector.Error as error:
            mostrar_error_bd(
                "Error al detectar al empleado",
                error,
                ventana
            )

            etiqueta_empleado.config(
                text="Empleado: error de verificación",
                fg=COLOR_ROJO
            )

        finally:
            if cursor:
                cursor.close()

            try:
                if conexion.is_connected():
                    conexion.close()
            except mysql.connector.Error:
                pass


    
    # ========================================================
    # CONSULTA AUTOMÁTICA DEL CLIENTE
    # ========================================================

    def limpiar_id_cliente():
        entrada_id_cliente.config(state="normal")
        entrada_id_cliente.delete(0, tk.END)
        entrada_id_cliente.config(state="readonly")

    def invalidar_cliente():
        nonlocal id_cliente_verificado

        id_cliente_verificado = None
        limpiar_id_cliente()

        etiqueta_cliente.config(
            text="Cliente: buscando identificación...",
            fg=COLOR_TEXTO_SUAVE
        )

    def consultar_cliente_automatico():
        nonlocal id_cliente_verificado
        nonlocal consulta_cliente_pendiente

        consulta_cliente_pendiente = None

        identificacion = (
            entrada_identificacion_cliente.get().strip()
        )

        id_cliente_verificado = None
        limpiar_id_cliente()

        if not identificacion:
            etiqueta_cliente.config(
                text="Cliente: sin identificar",
                fg=COLOR_TEXTO_SUAVE
            )
            return

        conexion = abrir_conexion()

        if not conexion:
            etiqueta_cliente.config(
                text="Cliente: no se pudo verificar",
                fg=COLOR_ROJO
            )
            return

        cursor = None

        try:
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT id_cliente, nombre, apellidos, estado
                FROM Clientes
                WHERE identificacion = %s
                LIMIT 1
            """, (identificacion,))

            cliente = cursor.fetchone()

            # Comprobar que el texto no haya cambiado durante
            # la consulta antes de mostrar el resultado.
            if (
                entrada_identificacion_cliente.get().strip()
                != identificacion
            ):
                return

            if not cliente:
                etiqueta_cliente.config(
                    text="Cliente: no encontrado",
                    fg=COLOR_ROJO
                )
                return

            if int(cliente[3]) != ESTADO_ACTIVO:
                etiqueta_cliente.config(
                    text="Cliente: cuenta desactivada",
                    fg=COLOR_ROJO
                )
                return

            id_cliente_verificado = int(cliente[0])

            entrada_id_cliente.config(state="normal")
            entrada_id_cliente.delete(0, tk.END)
            entrada_id_cliente.insert(
                0, str(id_cliente_verificado)
            )
            entrada_id_cliente.config(state="readonly")

            nombre_completo = (
                f"{cliente[1]} {cliente[2]}".strip()
            )

            etiqueta_cliente.config(
                text=f"Cliente: {nombre_completo}",
                fg=COLOR_TURQUESA
            )

        except mysql.connector.Error as error:
            mostrar_error_bd(
                "Error al consultar cliente",
                error,
                ventana
            )

            etiqueta_cliente.config(
                text="Cliente: error de consulta",
                fg=COLOR_ROJO
            )

        finally:
            if cursor:
                cursor.close()

            try:
                if conexion.is_connected():
                    conexion.close()
            except mysql.connector.Error:
                pass

    def programar_consulta_cliente(event=None):
        nonlocal consulta_cliente_pendiente

        # Invalidar inmediatamente la verificación anterior.
        invalidar_cliente()

        if consulta_cliente_pendiente is not None:
            try:
                ventana.after_cancel(consulta_cliente_pendiente)
            except tk.TclError:
                pass

        # Esperar a que termine la escritura.
        consulta_cliente_pendiente = ventana.after(
            400,
            consultar_cliente_automatico
        )

    entrada_identificacion_cliente.bind(
        "<KeyRelease>",
        programar_consulta_cliente
    )


    # ========================================================
    # ÁREA CENTRAL: CARRITO Y BÚSQUEDA
    # ========================================================

    area_venta = tk.Frame(contenido, bg=COLOR_FONDO)
    area_venta.grid(
        row=1, column=0, sticky="nsew", pady=(0, 5)
    )

    area_venta.columnconfigure(0, weight=6, uniform="paneles")
    area_venta.columnconfigure(1, weight=5, uniform="paneles")
    area_venta.rowconfigure(0, weight=1)

    # ========================================================
    # CARRITO
    # ========================================================

    panel_carrito = tk.Frame(
        area_venta,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    panel_carrito.grid(
        row=0, column=0, sticky="nsew", padx=(0, 6)
    )

    tk.Label(
        panel_carrito,
        text="Carrito de venta",
        font=(FUENTE, 14, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_PRINCIPAL
    ).pack(anchor="w", padx=14, pady=(9, 1))

    tk.Label(
        panel_carrito,
        text="Productos agregados a esta venta",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE
    ).pack(anchor="w", padx=14, pady=(0, 5))

    columnas_carrito = (
        "id", "producto", "cantidad", "precio", "subtotal"
    )

    marco_tabla_carrito = tk.Frame(panel_carrito, bg=COLOR_PANEL)
    marco_tabla_carrito.pack(
        fill="both", expand=True, padx=10, pady=(2, 3)
    )

    marco_tabla_carrito.columnconfigure(0, weight=1)
    marco_tabla_carrito.rowconfigure(0, weight=1)

    tabla_carrito = ttk.Treeview(
        marco_tabla_carrito,
        columns=columnas_carrito,
        show="headings",
        style="Ventas.Treeview",
        selectmode="browse"
    )

    for columna, titulo, ancho in (
        ("id", "Código", 58),
        ("producto", "Producto", 180),
        ("cantidad", "Cant.", 55),
        ("precio", "Precio", 82),
        ("subtotal", "Subtotal", 90)
    ):
        tabla_carrito.heading(columna, text=titulo)
        tabla_carrito.column(
            columna,
            width=ancho,
            minwidth=45,
            stretch=(columna == "producto"),
            anchor="w" if columna == "producto" else "center"
        )

    barra_carrito_y = ttk.Scrollbar(
        marco_tabla_carrito,
        orient="vertical",
        command=tabla_carrito.yview
    )

    barra_carrito_x = ttk.Scrollbar(
        marco_tabla_carrito,
        orient="horizontal",
        command=tabla_carrito.xview
    )

    tabla_carrito.configure(
        yscrollcommand=barra_carrito_y.set,
        xscrollcommand=barra_carrito_x.set
    )

    tabla_carrito.grid(row=0, column=0, sticky="nsew")
    barra_carrito_y.grid(row=0, column=1, sticky="ns")
    barra_carrito_x.grid(row=1, column=0, sticky="ew")

    carrito = {}

    etiqueta_articulos = tk.Label(
        panel_carrito,
        text="0 unidades | 0 productos",
        font=(FUENTE, 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE
    )
    etiqueta_articulos.pack(anchor="w", padx=14, pady=(2, 2))

    tk.Frame(
        panel_carrito,
        bg=COLOR_BORDE,
        height=1
    ).pack(fill="x", padx=12, pady=3)

    fila_total = tk.Frame(panel_carrito, bg=COLOR_PANEL)
    fila_total.pack(fill="x", padx=14, pady=(2, 5))


    etiqueta_total = tk.Label(
        fila_total,
        text="$0.00",
        font=(FUENTE, 20, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TURQUESA
    )
    etiqueta_total.pack(side="right")

    crear_boton(
        fila_total,
        "Vaciar venta",
        lambda: vaciar_carrito(),
        COLOR_SECUNDARIO,
        COLOR_PRINCIPAL,
        12
    ).pack(side="left", padx=(5, 5))

    crear_boton(
        fila_total,
        "Quitar",
        lambda: quitar_producto(),
        COLOR_ROJO,
        COLOR_ROJO_HOVER,
        9
    ).pack(side="left", padx=(5, 5))

    tk.Label(
            fila_total,
            text="TOTAL",
            font=(FUENTE, 13, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_PRINCIPAL
    ).pack(side="left")
    
    botones_carrito = tk.Frame(panel_carrito, bg=COLOR_PANEL)
    botones_carrito.pack(
        side="bottom", fill="x", padx=10, pady=(2, 7)
    )

    # ========================================================
    # PANEL DE BÚSQUEDA DE PRODUCTOS
    # ========================================================

    panel_productos = tk.Frame(
        area_venta,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    panel_productos.grid(
        row=0, column=1, sticky="nsew", padx=(6, 0)
    )

    tk.Label(
        panel_productos,
        text="Buscar productos",
        font=(FUENTE, 14, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_PRINCIPAL
    ).pack(anchor="w", padx=14, pady=(9, 1))

    tk.Label(
        panel_productos,
        text="Busca por código, nombre o marca",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE
    ).pack(anchor="w", padx=14, pady=(0, 5))

    tk.Label(
        panel_productos,
        text="Producto:",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).pack(anchor="w", padx=14)

    entrada_busqueda_producto = tk.Entry(
        panel_productos, font=(FUENTE, 11), relief="solid", bd=1
    )
    entrada_busqueda_producto.pack(
        fill="x", padx=14, pady=(3, 7), ipady=4
    )

    fila_cantidad = tk.Frame(panel_productos, bg=COLOR_PANEL)
    fila_cantidad.pack(fill="x", padx=14, pady=(0, 5))

    tk.Label(
        fila_cantidad,
        text="Cantidad:",
        font=(FUENTE, 10, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO
    ).pack(side="left")

    entrada_cantidad = tk.Entry(
        fila_cantidad,
        font=(FUENTE, 11),
        relief="solid",
        bd=1,
        width=9
    )
    entrada_cantidad.insert(0, "1")
    entrada_cantidad.pack(side="right", ipady=2)

    etiqueta_stock = tk.Label(
        panel_productos,
        text="Selecciona un producto para ver su stock",
        font=(FUENTE, 9),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
        anchor="w"
    )
    etiqueta_stock.pack(fill="x", padx=14, pady=(0, 5))

    marco_resultados = tk.Frame(panel_productos, bg=COLOR_PANEL)
    marco_resultados.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(0, 5),
        side="top"
    )

    marco_resultados.columnconfigure(0, weight=1)
    marco_resultados.rowconfigure(0, weight=1)

    columnas_productos = ("id", "nombre", "marca", "precio", "stock")

    tabla_resultados_productos = ttk.Treeview(
        marco_resultados,
        columns=columnas_productos,
        show="headings",
        style="Ventas.Treeview",
        selectmode="browse"
    )

    for columna, titulo, ancho in (
        ("id", "Código", 55),
        ("nombre", "Producto", 155),
        ("marca", "Marca", 85),
        ("precio", "Precio", 75),
        ("stock", "Stock", 55)
    ):
        tabla_resultados_productos.heading(columna, text=titulo)
        tabla_resultados_productos.column(
            columna,
            width=ancho,
            minwidth=45,
            stretch=(columna == "nombre"),
            anchor="w" if columna in ("nombre", "marca") else "center"
        )

    barra_resultados_y = ttk.Scrollbar(
        marco_resultados,
        orient="vertical",
        command=tabla_resultados_productos.yview
    )

    barra_resultados_x = ttk.Scrollbar(
        marco_resultados,
        orient="horizontal",
        command=tabla_resultados_productos.xview
    )

    tabla_resultados_productos.configure(
        yscrollcommand=barra_resultados_y.set,
        xscrollcommand=barra_resultados_x.set
    )

    tabla_resultados_productos.grid(row=0, column=0, sticky="nsew")
    barra_resultados_y.grid(row=0, column=1, sticky="ns")
    barra_resultados_x.grid(row=1, column=0, sticky="ew")

    # Colores para identificar el nivel de existencias
    tabla_resultados_productos.tag_configure(
        "stock_alto",
        foreground="#16A34A"
    )

    tabla_resultados_productos.tag_configure(
        "stock_bajo",
        foreground="#D97706"
    )

    tabla_resultados_productos.tag_configure(
        "stock_agotado",
        foreground="#DC2626"
    )

    # ========================================================
    # FUNCIONES DEL CARRITO
    # ========================================================

    busqueda_pendiente = None
    mapa_productos = {}

    def calcular_total():
        total = sum(
            (
                articulo["precio"] * articulo["cantidad"]
                for articulo in carrito.values()
            ),
            Decimal("0.00")
        )
        return dinero(total)

    def actualizar_tabla_carrito():
        for item in tabla_carrito.get_children():
            tabla_carrito.delete(item)

        for id_producto, articulo in carrito.items():
            subtotal = dinero(
                articulo["precio"] * articulo["cantidad"]
            )

            tabla_carrito.insert(
                "",
                tk.END,
                iid=str(id_producto),
                values=(
                    id_producto,
                    articulo["nombre"],
                    articulo["cantidad"],
                    f"${articulo['precio']:.2f}",
                    f"${subtotal:.2f}"
                )
            )

        etiqueta_total.config(text=f"${calcular_total():.2f}")

        unidades = sum(
            articulo["cantidad"] for articulo in carrito.values()
        )

        etiqueta_articulos.config(
            text=f"{unidades} unidades | {len(carrito)} productos"
        )

    def quitar_producto():
        seleccion = tabla_carrito.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona un producto",
                "Selecciona un producto del carrito para quitarlo.",
                parent=ventana
            )
            return

        try:
            id_producto = int(seleccion[0])
        except (ValueError, TypeError):
            return

        carrito.pop(id_producto, None)
        actualizar_tabla_carrito()

    def vaciar_carrito():
        if not carrito:
            return

        if messagebox.askyesno(
            "Vaciar carrito",
            "¿Deseas quitar todos los productos de esta venta?",
            parent=ventana
        ):
            carrito.clear()
            actualizar_tabla_carrito()

    # ========================================================
    # BÚSQUEDA Y SELECCIÓN DE PRODUCTOS
    # ========================================================

    def actualizar_stock(event=None):
        seleccion = tabla_resultados_productos.selection()

        if not seleccion:
            etiqueta_stock.config(
                text="Selecciona un producto para ver su stock",
                fg=COLOR_TEXTO_SUAVE
            )
            return

        producto = mapa_productos.get(int(seleccion[0]))

        if not producto:
            return

        etiqueta_stock.config(
            text=(
                f"Stock disponible: {producto['stock']} unidades"
                f" | Precio: ${producto['precio']:.2f}"
            ),
            fg=COLOR_TURQUESA if producto["stock"] > 0 else COLOR_ROJO
        )

    def buscar_productos(event=None):
        nonlocal mapa_productos, busqueda_pendiente

        busqueda_pendiente = None
        productos = obtener_productos(
            entrada_busqueda_producto.get()
        )
        mapa_productos = {}

        for item in tabla_resultados_productos.get_children():
            tabla_resultados_productos.delete(item)

        for p in productos:
            try:
                id_producto = int(p[0])

                producto = {
                    "id": id_producto,
                    "nombre": p[1],
                    "marca": p[2] or "Sin marca",
                    "precio": dinero(p[3]),
                    "stock": int(p[4] or 0),
                    "stock_minimo": int(p[5] or 0)
                }

                mapa_productos[id_producto] = producto

                if producto["stock"] <= 0:
                    etiqueta_color = "stock_agotado"
                elif producto["stock"] <= producto["stock_minimo"]:
                    etiqueta_color = "stock_bajo"
                else:
                    etiqueta_color = "stock_alto"

                tabla_resultados_productos.insert(
                    "",
                    "end",
                    iid=str(id_producto),
                    values=(
                        id_producto,
                        producto["nombre"],
                        producto["marca"],
                        f"${producto['precio']:.2f}",
                        producto["stock"]
                    ),
                    tags=(etiqueta_color,)
                )

            except (ValueError, TypeError, InvalidOperation):
                continue

        elementos = tabla_resultados_productos.get_children()

        if elementos:
            primero = elementos[0]
            tabla_resultados_productos.selection_set(primero)
            tabla_resultados_productos.focus(primero)
            tabla_resultados_productos.see(primero)
        else:
            etiqueta_stock.config(
                text="No se encontraron productos",
                fg=COLOR_TEXTO_SUAVE
            )

        actualizar_stock()

    def programar_busqueda_productos(event=None):
        nonlocal busqueda_pendiente

        if busqueda_pendiente is not None:
            ventana.after_cancel(busqueda_pendiente)

        busqueda_pendiente = ventana.after(
            250, buscar_productos
        )

    def cargar_productos():
        entrada_busqueda_producto.delete(0, tk.END)
        buscar_productos()

    def agregar_producto():
        seleccion = tabla_resultados_productos.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona un producto",
                "Selecciona un producto de la lista.",
                parent=ventana
            )
            return

        try:
            id_producto = int(seleccion[0])
            cantidad = convertir_cantidad(
                entrada_cantidad.get().strip()
            )

        except ValueError as error:
            messagebox.showwarning(
                "Cantidad incorrecta", str(error), parent=ventana
            )
            entrada_cantidad.focus_set()
            return

        producto = mapa_productos.get(id_producto)

        if not producto:
            messagebox.showwarning(
                "Producto no disponible",
                "Vuelve a buscar el producto.",
                parent=ventana
            )
            return

        cantidad_actual = carrito.get(
            id_producto, {}
        ).get("cantidad", 0)

        cantidad_final = cantidad_actual + cantidad

        if producto["stock"] <= 0:
            messagebox.showwarning(
                "Sin existencias",
                "Este producto no tiene existencias disponibles.",
                parent=ventana
            )
            return

        if cantidad_final > producto["stock"]:
            messagebox.showwarning(
                "Stock insuficiente",
                f"Solo hay {producto['stock']} unidades disponibles.\n"
                f"Ya tienes {cantidad_actual} en el carrito.",
                parent=ventana
            )
            return

        if id_producto in carrito:
            carrito[id_producto]["cantidad"] = cantidad_final
        else:
            carrito[id_producto] = {
                "nombre": producto["nombre"],
                "precio": producto["precio"],
                "cantidad": cantidad
            }

        actualizar_tabla_carrito()

        tabla_carrito.selection_set(str(id_producto))
        tabla_carrito.focus(str(id_producto))
        tabla_carrito.see(str(id_producto))

        entrada_cantidad.delete(0, tk.END)
        entrada_cantidad.insert(0, "1")
        entrada_busqueda_producto.focus_set()

    boton_agregar_producto = crear_boton(
        panel_productos,
        "Agregar producto seleccionado",
        agregar_producto,
        COLOR_TURQUESA,
        COLOR_TURQUESA_HOVER,
        28
    )

    boton_agregar_producto.pack(
        side="bottom",
        fill="x",
        padx=14,
        pady=(5, 10),
        ipady=5
    )

    entrada_busqueda_producto.bind(
        "<KeyRelease>", programar_busqueda_productos
    )
    entrada_busqueda_producto.bind("<Return>", buscar_productos)
    entrada_cantidad.bind(
        "<Return>", lambda e: agregar_producto()
    )
    tabla_resultados_productos.bind(
        "<<TreeviewSelect>>", actualizar_stock
    )
    tabla_resultados_productos.bind(
        "<Double-1>", lambda e: agregar_producto()
    )

    # ========================================================
    # REINICIAR FORMULARIO PARA UNA NUEVA VENTA
    # ========================================================

    def reiniciar_venta():
        nonlocal id_cliente_verificado
        nonlocal consulta_cliente_pendiente
        # Cancelar la consulta automática pendiente, si existe.
        if consulta_cliente_pendiente is not None:
            try:
                ventana.after_cancel(consulta_cliente_pendiente)
            except tk.TclError:
                pass

            consulta_cliente_pendiente = None

        # Limpiar los datos del cliente.
        entrada_identificacion_cliente.delete(0, tk.END)
        id_cliente_verificado = None

        limpiar_id_cliente()

        etiqueta_cliente.config(
            text="Cliente: sin identificar",
            fg=COLOR_TEXTO_SUAVE
        )

        confirmar = messagebox.askyesno(
            "Reiniciar venta",
            "¿Deseas reiniciar la venta actual?\n\n"
            "Se quitarán todos los productos del carrito y se "
            "limpiarán los datos del cliente.\n\n"
            "El empleado detectado automáticamente se conservará.\n\n"
            "Esta acción no elimina ventas guardadas ni modifica "
            "el inventario.",
            parent=ventana
        )

        if not confirmar:
            return

        # Vaciar el carrito y actualizar la tabla y los totales.
        carrito.clear()
        actualizar_tabla_carrito()

        # Limpiar los datos del cliente
        entrada_identificacion_cliente.delete(0, tk.END)
        id_cliente_verificado = None

        limpiar_id_cliente()

        etiqueta_cliente.config(
            text="Cliente: sin identificar",
            fg=COLOR_TEXTO_SUAVE
        )

        # El empleado detectado automáticamente se conserva.

        # Restablecer el método de pago.
        combo_pago.set("Efectivo")

        # Actualizar la fecha y hora.
        fecha_actual.set(
            datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        # Restablecer la cantidad de productos.
        entrada_cantidad.delete(0, tk.END)
        entrada_cantidad.insert(0, "1")

        # Limpiar la búsqueda y la selección de productos.
        entrada_busqueda_producto.delete(0, tk.END)
        buscar_productos()

        # Dejar la venta lista para comenzar nuevamente.
        entrada_identificacion_cliente.focus_set()

        messagebox.showinfo(
            "Venta reiniciada",
            "La venta actual se ha reiniciado correctamente.\n\n"
            "El carrito está vacío y el total es $0.00.\n"
            "El empleado de la sesión se conserva.\n"
            "Puedes comenzar a registrar una nueva venta.",
            parent=ventana
        )

    # ========================================================
    # REGISTRAR VENTA
    # ========================================================

    def registrar_venta():
        conexion = None
        cursor = None
        transaccion_iniciada = False
        venta_confirmada = False

        try:
            if not carrito:
                raise ValueError(
                    "Agrega al menos un producto antes de guardar la venta."
                )

            if id_empleado_verificado is None:
                raise ValueError(
                    "No se pudo identificar automáticamente al empleado. "
                    "Verifica que hayas iniciado sesión correctamente."
                )

            identificacion_cliente = (
                entrada_identificacion_cliente.get().strip()
            )

            if (
                identificacion_cliente
                and id_cliente_verificado is None
            ):
                raise ValueError(
                    "Espera a que se verifique la identificación del cliente. "
                    "Si deseas una venta sin cliente, deja el campo vacío."
                )

            id_cliente = (
                id_cliente_verificado
                if identificacion_cliente
                else None
            )
            id_empleado = id_empleado_verificado
            metodo_pago = combo_pago.get()

            if metodo_pago not in (
                "Efectivo", "Tarjeta", "Transferencia", "Otro"
            ):
                raise ValueError(
                    "Selecciona un método de pago válido."
                )

            conexion = abrir_conexion()

            if not conexion:
                return

            conexion.start_transaction()
            transaccion_iniciada = True
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT estado
                FROM Empleados
                WHERE id_empleado = %s
                FOR UPDATE
            """, (id_empleado,))

            empleado_bd = cursor.fetchone()

            if (
                not empleado_bd
                or int(empleado_bd[0]) != ESTADO_ACTIVO
            ):
                raise ValueError("El empleado ya no está activo.")

            if id_cliente is not None:
                cursor.execute("""
                    SELECT estado
                    FROM Clientes
                    WHERE id_cliente = %s
                    FOR UPDATE
                """, (id_cliente,))

                cliente_bd = cursor.fetchone()

                if (
                    not cliente_bd
                    or int(cliente_bd[0]) != ESTADO_ACTIVO
                ):
                    raise ValueError("El cliente ya no está activo.")

            productos_confirmados = []
            total = Decimal("0.00")

            for id_producto in sorted(carrito):
                articulo = carrito[id_producto]

                cursor.execute("""
                    SELECT nombre, precio_venta, cantidad_stock, estado
                    FROM Productos
                    WHERE id_producto = %s
                    FOR UPDATE
                """, (id_producto,))

                fila = cursor.fetchone()

                if not fila:
                    raise ValueError(
                        f"El producto con ID {id_producto} ya no existe."
                    )

                nombre_bd = fila[0]
                precio_bd = dinero(fila[1])
                stock_bd = int(fila[2] or 0)
                estado_bd = int(fila[3])
                cantidad = convertir_cantidad(
                    str(articulo["cantidad"])
                )

                if estado_bd != ESTADO_ACTIVO:
                    raise ValueError(
                        f"El producto '{nombre_bd}' está desactivado."
                    )

                if precio_bd != articulo["precio"]:
                    raise ValueError(
                        f"El precio de '{nombre_bd}' cambió.\n"
                        f"Precio anterior: ${articulo['precio']:.2f}\n"
                        f"Precio actual: ${precio_bd:.2f}\n"
                        "Vuelve a agregar el producto."
                    )

                if cantidad > stock_bd:
                    raise ValueError(
                        f"Stock insuficiente para '{nombre_bd}'. "
                        f"Disponibles: {stock_bd}."
                    )

                subtotal = dinero(precio_bd * cantidad)
                total += subtotal

                productos_confirmados.append({
                    "id": id_producto,
                    "nombre": nombre_bd,
                    "cantidad": cantidad,
                    "precio": precio_bd,
                    "subtotal": subtotal
                })

            total = dinero(total)

            cursor.execute("""
                INSERT INTO Ventas (
                    id_cliente, id_empleado, fecha,
                    metodo_pago, total, estado
                )
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
            """, (
                id_cliente,
                id_empleado,
                metodo_pago,
                total,
                VENTA_VIGENTE
            ))

            id_venta = cursor.lastrowid

            for articulo in productos_confirmados:
                cursor.execute("""
                    INSERT INTO Detalle_Venta (
                        id_venta, id_producto, cantidad,
                        precio_unitario, subtotal
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    id_venta,
                    articulo["id"],
                    articulo["cantidad"],
                    articulo["precio"],
                    articulo["subtotal"]
                ))

                cursor.execute("""
                    UPDATE Productos
                    SET cantidad_stock = cantidad_stock - %s
                    WHERE id_producto = %s
                      AND estado = %s
                      AND cantidad_stock >= %s
                """, (
                    articulo["cantidad"],
                    articulo["id"],
                    ESTADO_ACTIVO,
                    articulo["cantidad"]
                ))

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"No fue posible descontar el stock de "
                        f"'{articulo['nombre']}'."
                    )

                cursor.execute("""
                    INSERT INTO Movimientos_Inventario (
                        id_producto, id_empleado, tipo_movimiento,
                        cantidad, fecha, motivo, id_venta, id_pedido
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        CURRENT_TIMESTAMP, %s, %s, NULL
                    )
                """, (
                    articulo["id"],
                    id_empleado,
                    "SALIDA",
                    articulo["cantidad"],
                    f"Salida por venta #{id_venta}",
                    id_venta
                ))

            conexion.commit()
            transaccion_iniciada = False
            venta_confirmada = True

            unidades = sum(
                articulo["cantidad"]
                for articulo in productos_confirmados
            )

            carrito.clear()
            actualizar_tabla_carrito()
            cargar_productos()

            fecha_actual.set(
                datetime.now().strftime("%d/%m/%Y %H:%M")
            )

            messagebox.showinfo(
                "Venta guardada",
                "La venta se registró correctamente.\n\n"
                f"Folio: {id_venta}\n"
                f"Unidades vendidas: {unidades}\n"
                f"Total: ${total:.2f}\n"
                f"Método de pago: {metodo_pago}\n\n"
                "El inventario se actualizó automáticamente.",
                parent=ventana
            )

        except ValueError as error:
            if transaccion_iniciada and not venta_confirmada:
                revertir_transaccion(conexion)

            messagebox.showwarning(
                "Revisa los datos", str(error), parent=ventana
            )

        except mysql.connector.Error as error:
            if transaccion_iniciada and not venta_confirmada:
                revertir_transaccion(conexion)

            mostrar_error_bd(
                "No se pudo guardar la venta", error, ventana
            )

        except Exception as error:
            if transaccion_iniciada and not venta_confirmada:
                revertir_transaccion(conexion)

            messagebox.showerror(
                "Error inesperado",
                f"Ocurrió un error al procesar la venta:\n\n{error}",
                parent=ventana
            )

        finally:
            if cursor:
                cursor.close()

            if conexion:
                try:
                    if conexion.is_connected():
                        conexion.close()
                except mysql.connector.Error:
                    pass

    # ========================================================
    # HISTORIAL DE VENTAS
    # ========================================================

    def ver_historial():
        historial = tk.Toplevel(ventana)
        historial.title("Historial de ventas")
        historial.configure(bg=COLOR_FONDO)
        historial.geometry("1120x620")
        historial.minsize(950, 500)
        historial.transient(ventana)

        encabezado_historial = tk.Frame(
            historial, bg=COLOR_PRINCIPAL
        )
        encabezado_historial.pack(fill="x")

        tk.Label(
            encabezado_historial,
            text="Historial de ventas",
            font=(FUENTE, 21, "bold"),
            bg=COLOR_PRINCIPAL,
            fg="white",
            padx=22,
            pady=10
        ).pack(anchor="w")

        tk.Label(
            encabezado_historial,
            text="Consulta, revisa o cancela ventas registradas",
            font=(FUENTE, 10),
            bg=COLOR_PRINCIPAL,
            fg="#DBEAFE",
            padx=23,
            pady=0
        ).pack(anchor="w", pady=(0, 10))

        panel = tk.Frame(
            historial,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        panel.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=10
        )

        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=0)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_rowconfigure(2, weight=0)
        panel.grid_rowconfigure(3, weight=0)

        # ----------------------------------------------------
        # FILTROS
        # ----------------------------------------------------

        filtro = tk.Frame(panel, bg=COLOR_PANEL)
        filtro.grid(
            row=0, column=0, sticky="ew",
            padx=14, pady=8
        )

        tk.Label(
            filtro,
            text="Folio:",
            font=(FUENTE, 10, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO
        ).pack(side="left", padx=(0, 8))

        entrada_filtro = tk.Entry(
            filtro,
            font=(FUENTE, 10),
            relief="solid",
            bd=1,
            width=16
        )
        entrada_filtro.pack(side="left", ipady=4)

        estado_filtro = ttk.Combobox(
            filtro,
            values=["Todas", "Vigentes", "Canceladas"],
            state="readonly",
            width=14,
            style="Ventas.TCombobox"
        )
        estado_filtro.set("Todas")
        estado_filtro.pack(side="left", padx=8)

        # ----------------------------------------------------
        # TABLA DEL HISTORIAL
        # ----------------------------------------------------

        columnas_historial = (
            "id", "fecha", "cliente", "empleado",
            "total", "pago", "estado"
        )

        marco_historial = tk.Frame(panel, bg=COLOR_PANEL)
        marco_historial.grid(
            row=1, column=0, sticky="nsew",
            padx=14, pady=(0, 4)
        )

        marco_historial.columnconfigure(0, weight=1)
        marco_historial.rowconfigure(0, weight=1)

        tabla_historial = ttk.Treeview(
            marco_historial,
            columns=columnas_historial,
            show="headings",
            style="Ventas.Treeview",
            selectmode="browse",
            height=12
        )

        encabezados_historial = {
            "id": ("Folio", 65),
            "fecha": ("Fecha", 145),
            "cliente": ("Cliente", 190),
            "empleado": ("Empleado", 190),
            "total": ("Total", 100),
            "pago": ("Método de pago", 130),
            "estado": ("Estado", 105)
        }

        for col, (titulo, ancho) in encabezados_historial.items():
            tabla_historial.heading(col, text=titulo)
            tabla_historial.column(
                col,
                width=ancho,
                minwidth=60,
                anchor="center",
                stretch=(col in ("cliente", "empleado"))
            )

        tabla_historial.tag_configure(
            "cancelada", foreground=COLOR_ROJO
        )
        tabla_historial.tag_configure(
            "vigente", foreground=COLOR_TEXTO
        )

        barra_historial = ttk.Scrollbar(
            marco_historial,
            orient="vertical",
            command=tabla_historial.yview
        )

        barra_historial_x = ttk.Scrollbar(
            marco_historial,
            orient="horizontal",
            command=tabla_historial.xview
        )

        tabla_historial.configure(
            yscrollcommand=barra_historial.set,
            xscrollcommand=barra_historial_x.set
        )

        tabla_historial.grid(row=0, column=0, sticky="nsew")
        barra_historial.grid(row=0, column=1, sticky="ns")
        barra_historial_x.grid(row=1, column=0, sticky="ew")

        # ----------------------------------------------------
        # CÁLCULO DEL TOTAL DIARIO
        # ----------------------------------------------------

        def calcular_total_ventas_dia():
            conexion = None
            cursor = None

            try:
                conexion = abrir_conexion()

                if not conexion:
                    return

                cursor = conexion.cursor()

                cursor.execute("""
                    SELECT COALESCE(SUM(total), 0)
                    FROM Ventas
                    WHERE DATE(fecha) = CURDATE()
                      AND estado = %s
                """, (VENTA_VIGENTE,))

                resultado = cursor.fetchone()
                total_dia = dinero(resultado[0] or 0)

                etiqueta_total_dia.config(
                    text=f"TOTAL VENDIDO HOY: ${total_dia:,.2f}"
                )

            except mysql.connector.Error as error:
                mostrar_error_bd(
                    "Error al calcular las ventas del día",
                    error,
                    historial
                )

            finally:
                if cursor:
                    cursor.close()

                if conexion:
                    try:
                        if conexion.is_connected():
                            conexion.close()
                    except mysql.connector.Error:
                        pass

        # ----------------------------------------------------
        # CARGAR HISTORIAL
        # ----------------------------------------------------

        def cargar_historial():
            for item in tabla_historial.get_children():
                tabla_historial.delete(item)

            conexion = abrir_conexion()

            if not conexion:
                return

            cursor = None

            try:
                cursor = conexion.cursor()

                consulta = """
                    SELECT
                        v.id_venta,
                        v.fecha,
                        COALESCE(
                            CONCAT(c.nombre, ' ', c.apellidos),
                            'Venta sin cliente'
                        ),
                        COALESCE(
                            CONCAT(e.nombre, ' ', e.apellidos),
                            'Empleado no disponible'
                        ),
                        v.total,
                        v.metodo_pago,
                        v.estado
                    FROM Ventas v
                    LEFT JOIN Clientes c
                        ON v.id_cliente = c.id_cliente
                    LEFT JOIN Empleados e
                        ON v.id_empleado = e.id_empleado
                    WHERE 1 = 1
                """

                parametros = []
                texto = entrada_filtro.get().strip()

                if texto:
                    id_busqueda = convertir_id(texto, "Folio")
                    consulta += " AND v.id_venta = %s"
                    parametros.append(id_busqueda)

                seleccion_estado = estado_filtro.get()

                if seleccion_estado == "Vigentes":
                    consulta += " AND v.estado = %s"
                    parametros.append(VENTA_VIGENTE)

                elif seleccion_estado == "Canceladas":
                    consulta += " AND v.estado = %s"
                    parametros.append(VENTA_CANCELADA)

                consulta += " ORDER BY v.id_venta ASC"

                cursor.execute(consulta, tuple(parametros))

                for fila in cursor.fetchall():
                    fecha = fila[1]

                    if isinstance(fecha, datetime):
                        fecha = fecha.strftime("%d/%m/%Y %H:%M:%S")

                    estado_venta = (
                        "Vigente"
                        if int(fila[6]) == VENTA_VIGENTE
                        else "Cancelada"
                    )

                    tabla_historial.insert(
                        "",
                        tk.END,
                        values=(
                            fila[0],
                            fecha,
                            fila[2],
                            fila[3],
                            f"${dinero(fila[4]):.2f}",
                            fila[5],
                            estado_venta
                        ),
                        tags=(
                            "vigente"
                            if estado_venta == "Vigente"
                            else "cancelada",
                        )
                    )

            except ValueError as error:
                messagebox.showwarning(
                    "Folio incorrecto",
                    str(error),
                    parent=historial
                )

            except mysql.connector.Error as error:
                mostrar_error_bd(
                    "Error al consultar historial",
                    error,
                    historial
                )

            finally:
                if cursor:
                    cursor.close()

                if conexion:
                    try:
                        if conexion.is_connected():
                            conexion.close()
                    except mysql.connector.Error:
                        pass

                calcular_total_ventas_dia()

        # ----------------------------------------------------
        # VER DETALLE DE VENTA
        # ----------------------------------------------------

        def ver_detalle():
            seleccion = tabla_historial.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selecciona una venta",
                    "Selecciona un folio del historial.",
                    parent=historial
                )
                return

            valores = tabla_historial.item(
                seleccion[0], "values"
            )

            try:
                id_venta = convertir_id(valores[0], "Folio")

            except ValueError as error:
                messagebox.showwarning(
                    "Folio incorrecto",
                    str(error),
                    parent=historial
                )
                return

            conexion = abrir_conexion()

            if not conexion:
                return

            cursor = None

            try:
                cursor = conexion.cursor()

                cursor.execute("""
                    SELECT
                        v.fecha,
                        v.total,
                        v.metodo_pago,
                        v.estado,
                        COALESCE(
                            CONCAT(c.nombre, ' ', c.apellidos),
                            'Venta sin cliente'
                        ),
                        COALESCE(
                            CONCAT(e.nombre, ' ', e.apellidos),
                            'Empleado no disponible'
                        )
                    FROM Ventas v
                    LEFT JOIN Clientes c
                        ON v.id_cliente = c.id_cliente
                    LEFT JOIN Empleados e
                        ON v.id_empleado = e.id_empleado
                    WHERE v.id_venta = %s
                """, (id_venta,))

                cabecera = cursor.fetchone()

                if not cabecera:
                    messagebox.showwarning(
                        "Venta no encontrada",
                        "No se encontró la venta seleccionada.",
                        parent=historial
                    )
                    return

                cursor.execute("""
                    SELECT
                        dv.id_producto,
                        dv.cantidad,
                        dv.precio_unitario,
                        dv.subtotal,
                        COALESCE(
                            p.nombre,
                            'Producto no disponible'
                        )
                    FROM Detalle_Venta dv
                    LEFT JOIN Productos p
                        ON dv.id_producto = p.id_producto
                    WHERE dv.id_venta = %s
                    ORDER BY dv.id_detalle
                """, (id_venta,))

                detalles = cursor.fetchall()

                detalle_win = tk.Toplevel(historial)
                detalle_win.title(f"Detalle de venta #{id_venta}")
                detalle_win.configure(bg=COLOR_FONDO)
                detalle_win.geometry("780x490")
                detalle_win.minsize(650, 400)
                detalle_win.transient(historial)

                estado_texto = (
                    "VIGENTE"
                    if int(cabecera[3]) == VENTA_VIGENTE
                    else "CANCELADA"
                )

                tk.Label(
                    detalle_win,
                    text=(
                        f"Detalle de venta #{id_venta} — "
                        f"{estado_texto}"
                    ),
                    font=(FUENTE, 18, "bold"),
                    bg=COLOR_PRINCIPAL,
                    fg="white",
                    padx=20,
                    pady=12
                ).pack(fill="x")

                info = tk.Frame(
                    detalle_win,
                    bg=COLOR_PANEL,
                    highlightbackground=COLOR_BORDE,
                    highlightthickness=1
                )
                info.pack(fill="x", padx=18, pady=10)

                fecha, total, pago, _, cliente, empleado = cabecera

                if isinstance(fecha, datetime):
                    fecha = fecha.strftime("%d/%m/%Y %H:%M:%S")

                tk.Label(
                    info,
                    text=(
                        f"Fecha: {fecha}\n"
                        f"Cliente: {cliente}\n"
                        f"Empleado: {empleado}\n"
                        f"Método de pago: {pago}"
                    ),
                    justify="left",
                    anchor="w",
                    font=(FUENTE, 10),
                    bg=COLOR_PANEL,
                    fg=COLOR_TEXTO
                ).pack(anchor="w", padx=15, pady=8)

                columnas_detalle = (
                    "producto", "cantidad", "precio", "subtotal"
                )

                tabla_detalle = ttk.Treeview(
                    detalle_win,
                    columns=columnas_detalle,
                    show="headings",
                    style="Ventas.Treeview",
                    height=8
                )

                for columna, titulo in (
                    ("producto", "Producto"),
                    ("cantidad", "Cantidad"),
                    ("precio", "Precio unitario"),
                    ("subtotal", "Subtotal")
                ):
                    tabla_detalle.heading(columna, text=titulo)

                tabla_detalle.column(
                    "producto", width=350, anchor="w"
                )
                tabla_detalle.column(
                    "cantidad", width=100, anchor="center"
                )
                tabla_detalle.column(
                    "precio", width=130, anchor="center"
                )
                tabla_detalle.column(
                    "subtotal", width=130, anchor="center"
                )

                tabla_detalle.pack(
                    fill="both",
                    expand=True,
                    padx=18,
                    pady=(0, 8)
                )

                for detalle in detalles:
                    tabla_detalle.insert(
                        "",
                        tk.END,
                        values=(
                            detalle[4],
                            detalle[1],
                            f"${dinero(detalle[2]):.2f}",
                            f"${dinero(detalle[3]):.2f}"
                        )
                    )

                tk.Label(
                    detalle_win,
                    text=(
                        f"TOTAL DE LA VENTA: "
                        f"${dinero(total):.2f}"
                    ),
                    font=(FUENTE, 15, "bold"),
                    bg=COLOR_FONDO,
                    fg=COLOR_TURQUESA
                ).pack(anchor="e", padx=22, pady=(0, 8))

                crear_boton(
                    detalle_win,
                    "Cerrar",
                    detalle_win.destroy,
                    COLOR_SECUNDARIO,
                    COLOR_PRINCIPAL,
                    14
                ).pack(pady=(0, 10))

            except mysql.connector.Error as error:
                mostrar_error_bd(
                    "Error al consultar el detalle",
                    error,
                    historial
                )

            finally:
                if cursor:
                    cursor.close()

                if conexion:
                    try:
                        if conexion.is_connected():
                            conexion.close()
                    except mysql.connector.Error:
                        pass

        # ----------------------------------------------------
        # CANCELAR VENTA Y DEVOLVER EXISTENCIAS
        # ----------------------------------------------------

        def cancelar_venta():
            seleccion = tabla_historial.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selecciona una venta",
                    "Selecciona la venta que deseas cancelar.",
                    parent=historial
                )
                return

            valores = tabla_historial.item(
                seleccion[0], "values"
            )

            try:
                id_venta = convertir_id(valores[0], "Folio")

            except ValueError as error:
                messagebox.showwarning(
                    "Folio incorrecto",
                    str(error),
                    parent=historial
                )
                return

            if valores[6] == "Cancelada":
                messagebox.showinfo(
                    "Venta ya cancelada",
                    "Esta venta ya está cancelada. No se devolverá "
                    "el stock nuevamente.",
                    parent=historial
                )
                return

            confirmar = messagebox.askyesno(
                "Confirmar cancelación",
                f"¿Deseas cancelar la venta #{id_venta}?\n\n"
                "Se marcará como cancelada y se devolverán las "
                "cantidades de sus productos al inventario.",
                parent=historial
            )

            if not confirmar:
                return

            conexion = None
            cursor = None
            transaccion_iniciada = False
            cancelacion_confirmada = False

            try:
                conexion = abrir_conexion()

                if not conexion:
                    return

                conexion.start_transaction()
                transaccion_iniciada = True
                cursor = conexion.cursor()

                cursor.execute("""
                    SELECT estado, id_empleado
                    FROM Ventas
                    WHERE id_venta = %s
                    FOR UPDATE
                """, (id_venta,))

                venta = cursor.fetchone()

                if not venta:
                    raise ValueError("La venta ya no existe.")

                if int(venta[0]) != VENTA_VIGENTE:
                    raise ValueError("La venta ya no está vigente.")

                id_empleado = int(venta[1])

                cursor.execute("""
                    SELECT id_producto, cantidad
                    FROM Detalle_Venta
                    WHERE id_venta = %s
                    ORDER BY id_producto
                """, (id_venta,))

                detalles = cursor.fetchall()

                if not detalles:
                    raise ValueError(
                        "La venta no tiene detalles. No se puede cancelar."
                    )

                for id_producto, cantidad in detalles:
                    cursor.execute("""
                        SELECT cantidad_stock
                        FROM Productos
                        WHERE id_producto = %s
                        FOR UPDATE
                    """, (id_producto,))

                    producto = cursor.fetchone()

                    if not producto:
                        raise ValueError(
                            f"No existe el producto ID {id_producto}. "
                            "No se puede devolver su existencia."
                        )

                    cursor.execute("""
                        UPDATE Productos
                        SET cantidad_stock = cantidad_stock + %s
                        WHERE id_producto = %s
                    """, (int(cantidad), id_producto))

                    if cursor.rowcount != 1:
                        raise ValueError(
                            f"No se pudo devolver el stock del producto "
                            f"ID {id_producto}."
                        )

                    cursor.execute("""
                        INSERT INTO Movimientos_Inventario (
                            id_producto, id_empleado, tipo_movimiento,
                            cantidad, fecha, motivo, id_venta, id_pedido
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            CURRENT_TIMESTAMP, %s, %s, NULL
                        )
                    """, (
                        id_producto,
                        id_empleado,
                        "ENTRADA",
                        int(cantidad),
                        f"Devolución por cancelación de venta #{id_venta}",
                        id_venta
                    ))

                cursor.execute("""
                    UPDATE Ventas
                    SET estado = %s
                    WHERE id_venta = %s
                      AND estado = %s
                """, (
                    VENTA_CANCELADA,
                    id_venta,
                    VENTA_VIGENTE
                ))

                if cursor.rowcount != 1:
                    raise ValueError(
                        "No fue posible cambiar el estado de la venta."
                    )

                conexion.commit()
                transaccion_iniciada = False
                cancelacion_confirmada = True

            except ValueError as error:
                if transaccion_iniciada and not cancelacion_confirmada:
                    revertir_transaccion(conexion)

                messagebox.showwarning(
                    "No se pudo cancelar",
                    str(error),
                    parent=historial
                )

            except mysql.connector.Error as error:
                if transaccion_iniciada and not cancelacion_confirmada:
                    revertir_transaccion(conexion)

                mostrar_error_bd(
                    "Error al cancelar la venta",
                    error,
                    historial
                )

            except Exception as error:
                if transaccion_iniciada and not cancelacion_confirmada:
                    revertir_transaccion(conexion)

                messagebox.showerror(
                    "Error inesperado",
                    f"No se pudo completar la cancelación:\n\n{error}",
                    parent=historial
                )

            finally:
                if cursor:
                    cursor.close()

                if conexion:
                    try:
                        if conexion.is_connected():
                            conexion.close()
                    except mysql.connector.Error:
                        pass

            if cancelacion_confirmada:
                cargar_historial()
                cargar_productos()

                messagebox.showinfo(
                    "Venta cancelada",
                    f"La venta #{id_venta} se canceló correctamente.\n\n"
                    "El stock fue devuelto y los movimientos quedaron "
                    "registrados en el inventario.",
                    parent=historial
                )

        # ----------------------------------------------------
        # ELIMINAR HISTORIAL COMPLETO Y REINICIAR FOLIOS
        # ----------------------------------------------------

        def reiniciar_historial():
            confirmar = messagebox.askyesno(
                "Confirmar reinicio del historial",
                "¡ATENCIÓN! Esta operación es irreversible.\n\n"
                "Se eliminarán TODAS las ventas registradas, "
                "sus detalles y los movimientos de inventario "
                "relacionados con esas ventas.\n\n"
                "El folio de la siguiente venta volverá a 1 "
                "si la operación termina correctamente.\n\n"
                "Las existencias actuales de los productos "
                "NO se modificarán.\n\n"
                "¿Deseas continuar?",
                icon="warning",
                parent=historial
            )

            if not confirmar:
                return

            confirmar_final = messagebox.askyesno(
                "Confirmación definitiva",
                "¿Confirmas que deseas borrar todo el historial "
                "de ventas y reiniciar los folios?\n\n"
                "No podrás recuperar los registros eliminados "
                "desde esta operación.",
                icon="warning",
                parent=historial
            )

            if not confirmar_final:
                return

            conexion = None
            cursor = None
            eliminacion_confirmada = False

            try:
                conexion = abrir_conexion()

                if not conexion:
                    return

                conexion.start_transaction()
                cursor = conexion.cursor()

                cursor.execute("""
                    DELETE FROM Movimientos_Inventario
                    WHERE id_venta IN (
                        SELECT id_venta
                        FROM Ventas
                    )
                """)

                cursor.execute("""
                    DELETE FROM Detalle_Venta
                    WHERE id_venta IN (
                        SELECT id_venta
                        FROM Ventas
                    )
                """)

                cursor.execute("DELETE FROM Ventas")

                conexion.commit()
                eliminacion_confirmada = True

                cursor.execute(
                    "ALTER TABLE Ventas AUTO_INCREMENT = 1"
                )

                cargar_historial()
                cargar_productos()

                messagebox.showinfo(
                    "Historial reiniciado",
                    "El historial de ventas se ha eliminado.\n\n"
                    "El folio de la siguiente venta comenzará "
                    "en 1, siempre que la tabla permanezca vacía "
                    "y no existan restricciones adicionales.\n\n"
                    "Las existencias de los productos "
                    "no fueron modificadas.",
                    parent=historial
                )

            except mysql.connector.Error as error:
                if conexion and not eliminacion_confirmada:
                    revertir_transaccion(conexion)

                if eliminacion_confirmada:
                    messagebox.showwarning(
                        "Historial eliminado",
                        "Las ventas se eliminaron, pero no fue "
                        "posible completar el reinicio del folio.\n\n"
                        "Error:\n" + str(error) +
                        "\n\nRevisa el AUTO_INCREMENT de la tabla "
                        "Ventas en MariaDB.",
                        parent=historial
                    )
                else:
                    mostrar_error_bd(
                        "No se pudo reiniciar el historial",
                        error,
                        historial
                    )

            finally:
                if cursor:
                    cursor.close()

                if conexion:
                    try:
                        if conexion.is_connected():
                            conexion.close()
                    except mysql.connector.Error:
                        pass

        # ----------------------------------------------------
        # BOTONES DEL HISTORIAL
        # ----------------------------------------------------

        botones_historial = tk.Frame(
            panel,
            bg=COLOR_PANEL,
            height=58
        )

        botones_historial.grid(
            row=2, column=0, sticky="ew",
            padx=14, pady=(4, 9)
        )

        botones_historial.grid_propagate(False)

        crear_boton(
            botones_historial,
            "Ver detalle",
            ver_detalle,
            COLOR_PRINCIPAL,
            COLOR_SECUNDARIO,
            12
        ).pack(side="left", padx=(0, 6), pady=7)

        crear_boton(
            botones_historial,
            "Cancelar venta",
            cancelar_venta,
            COLOR_ROJO,
            COLOR_ROJO_HOVER,
            15
        ).pack(side="left", padx=6, pady=7)

        crear_boton(
            botones_historial,
            "Reiniciar historial y folios",
            reiniciar_historial,
            COLOR_ROJO,
            COLOR_ROJO_HOVER,
            25
        ).pack(side="left", padx=6, pady=7)

        crear_boton(
            botones_historial,
            "Cerrar",
            historial.destroy,
            COLOR_ACENTO,
            COLOR_ACENTO_HOVER,
            10
        ).pack(side="right", padx=4, pady=7)

        # ----------------------------------------------------
        # INDICADOR DEL TOTAL DE VENTAS DEL DÍA
        # ----------------------------------------------------

        marco_total = tk.Frame(
            panel,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_ACENTO,
            highlightthickness=1
        )

        marco_total.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=14,
            pady=(0, 10)
        )

        etiqueta_total_dia = tk.Label(
            marco_total,
            text="TOTAL VENDIDO HOY: $0.00",
            font=(FUENTE, 13, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_PRINCIPAL,
            padx=12,
            pady=9
        )

        etiqueta_total_dia.pack(anchor="e")

        # ----------------------------------------------------
        # FILTROS Y CARGA INICIAL
        # ----------------------------------------------------

        entrada_filtro.bind(
            "<Return>",
            lambda event: cargar_historial()
        )

        estado_filtro.bind(
            "<<ComboboxSelected>>",
            lambda event: cargar_historial()
        )

        historial.update_idletasks()

        cargar_historial()

    # ========================================================
    # BOTONES PRINCIPALES
    # ========================================================

    botones_finales = tk.Frame(
        contenido,
        bg=COLOR_FONDO,
        height=55
    )

    botones_finales.grid(
        row=2, column=0, sticky="ew", pady=(2, 0)
    )

    botones_finales.grid_propagate(False)

    crear_boton(
        botones_finales,
        "Guardar venta",
        registrar_venta,
        COLOR_ACENTO,
        COLOR_ACENTO_HOVER,
        18
    ).pack(side="left", padx=(0, 7), pady=6)

    crear_boton(
        botones_finales,
        "Historial de ventas",
        ver_historial,
        COLOR_PRINCIPAL,
        COLOR_SECUNDARIO,
        18
    ).pack(side="left", padx=7, pady=6)

    crear_boton(
        botones_finales,
        "Salir",
        ventana.destroy,
        COLOR_ROJO,
        COLOR_ROJO_HOVER,
        12
    ).pack(side="right", padx=5, pady=6)

    # ========================================================
    # PIE DE VENTANA
    # ========================================================

    tk.Label(
        ventana,
        text="Papelería Luna | Registro y control de ventas",
        font=(FUENTE, 9),
        bg=COLOR_FONDO,
        fg=COLOR_TEXTO_SUAVE
    ).pack(anchor="w", padx=22, pady=(0, 3))

    # ========================================================
    # CARGA INICIAL
    # ========================================================

    detectar_empleado()
    cargar_productos()
    actualizar_tabla_carrito()

    if parent is None:
        ventana.mainloop()