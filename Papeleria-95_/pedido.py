import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
import mysql.connector
from mysql.connector import Error

from tema import (
    obtener_colores,
    obtener_tema_actual,
    registrar_observador,
    eliminar_observador
)

# ============================================================
# CONFIGURACIÓN - PAPELERÍA LUNA
# ============================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "Papeleria_Luna",
    "connection_timeout": 10,
}

# Estados de productos, proveedores, empleados y movimientos.
ESTADO_ACTIVO = 0
ESTADO_INACTIVO = 1

# Estados de pedidos a proveedores.
ESTADO_PENDIENTE = 0
ESTADO_RECIBIDO = 1
ESTADO_CANCELADO = 2

# Configuración del reabastecimiento automático.
# Ejemplo: {1: 20, 2: 50}
CANTIDADES_REABASTECIMIENTO = {}
CANTIDAD_REABASTECIMIENTO_DEFAULT = 10

# ============================================================
# PALETA VISUAL - PAPELERÍA LUNA
# Compatible con modo claro y oscuro
# ============================================================

TEMA_ACTUAL = obtener_tema_actual()
COLORES = obtener_colores(TEMA_ACTUAL)

COLOR_FONDO = COLORES["FONDO"]
COLOR_PANEL = COLORES["PANEL"]
COLOR_AZUL = COLORES["AZUL"]
COLOR_AZUL_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
COLOR_NARANJA = COLORES["NARANJA"]
COLOR_VERDE = "#0F766E"
COLOR_ROJO = COLORES["ROJO"]
COLOR_TEXTO = COLORES["TEXTO"]
COLOR_SUAVE = COLORES["TEXTO_SUAVE"]
COLOR_BORDE = COLORES["BORDE"]

COLOR_HOVER_NARANJA = COLORES["NARANJA_HOVER"]
COLOR_HOVER_VERDE = "#115E59"
COLOR_HOVER_ROJO = COLORES["ROJO_HOVER"]

COLOR_SELECCION = COLORES["SELECCION"]
COLOR_ENCABEZADO_TABLA = (
    "#E2E8F0" if TEMA_ACTUAL == "claro"
    else "#374151"
)

COLOR_ENTRADA = COLORES["ENTRADA"]

FUENTE = "Arial"

# ============================================================
# CONTROL DEL TEMA DINÁMICO
# ============================================================

VENTANAS_TEMA = []

# ============================================================
# CONEXIÓN Y CONSULTAS A LA BASE DE DATOS
# ============================================================
def conectar_bd():
    """Abre una conexión con la base de datos Papeleria_Luna."""
    return mysql.connector.connect(**DB_CONFIG)


def _consultar_todos(sql, parametros=()):
    """Ejecuta una consulta y devuelve todos sus registros."""
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_empleados_activos():
    return _consultar_todos("""
        SELECT id_empleado, nombre, apellidos
        FROM Empleados
        WHERE estado = %s
        ORDER BY apellidos, nombre
    """, (ESTADO_ACTIVO,))


def obtener_productos_activos():
    return _consultar_todos("""
        SELECT
            p.id_producto,
            p.nombre,
            p.marca,
            p.precio_compra,
            p.cantidad_stock,
            p.stock_minimo,
            p.estado,
            p.id_proveedor,
            pr.nombre AS proveedor_asignado
        FROM Productos p
        LEFT JOIN Proveedores pr
            ON pr.id_proveedor = p.id_proveedor
        WHERE p.estado = %s
        ORDER BY p.nombre
    """, (ESTADO_ACTIVO,))


def obtener_proveedores_activos():
    return _consultar_todos("""
        SELECT id_proveedor, nombre
        FROM Proveedores
        WHERE estado = %s
        ORDER BY nombre
    """, (ESTADO_ACTIVO,))


def obtener_pedidos(estado):
    return _consultar_todos("""
        SELECT
            pp.id_pedido,
            pp.id_proveedor,
            pp.id_empleado,
            pp.fecha_pedido,
            pp.total,
            pp.estado,
            pr.nombre AS proveedor,
            CONCAT(e.nombre, ' ', e.apellidos) AS responsable,
            COALESCE(
                SUM(GREATEST(dp.cantidad - dp.cantidad_recibida, 0)),
                0
            ) AS unidades_pendientes
        FROM Pedidos_Proveedor pp
        JOIN Proveedores pr
            ON pr.id_proveedor = pp.id_proveedor
        JOIN Empleados e
            ON e.id_empleado = pp.id_empleado
        LEFT JOIN Detalle_Pedido dp
            ON dp.id_pedido = pp.id_pedido
        WHERE pp.estado = %s
        GROUP BY
            pp.id_pedido,
            pp.id_proveedor,
            pp.id_empleado,
            pp.fecha_pedido,
            pp.total,
            pp.estado,
            pr.nombre,
            e.nombre,
            e.apellidos
        ORDER BY pp.fecha_pedido DESC, pp.id_pedido DESC
    """, (estado,))


def obtener_detalles_pedido(id_pedido):
    return _consultar_todos("""
        SELECT
            dp.id_detalle_pedido,
            dp.id_producto,
            p.nombre,
            dp.cantidad,
            dp.cantidad_recibida,
            dp.costo_unitario,
            dp.subtotal
        FROM Detalle_Pedido dp
        JOIN Productos p
            ON p.id_producto = dp.id_producto
        WHERE dp.id_pedido = %s
        ORDER BY p.nombre
    """, (id_pedido,))


# ============================================================
# GUARDAR Y MODIFICAR PEDIDOS
# ============================================================
def guardar_pedido(id_proveedor, id_empleado, productos, id_pedido=None):
    """
    Crea un pedido o modifica un pedido pendiente sin recepciones.
    Los detalles y el total se guardan dentro de una transacción.
    """
    if not productos:
        raise ValueError("Agrega al menos un producto al pedido.")

    if len({int(p["id_producto"]) for p in productos}) != len(productos):
        raise ValueError("No agregues el mismo producto dos veces.")

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        conexion.start_transaction()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_proveedor
            FROM Proveedores
            WHERE id_proveedor = %s AND estado = %s
            FOR UPDATE
        """, (id_proveedor, ESTADO_ACTIVO))

        if cursor.fetchone() is None:
            raise ValueError("El proveedor seleccionado no está activo.")

        cursor.execute("""
            SELECT id_empleado
            FROM Empleados
            WHERE id_empleado = %s AND estado = %s
            FOR UPDATE
        """, (id_empleado, ESTADO_ACTIVO))

        if cursor.fetchone() is None:
            raise ValueError("El empleado responsable no está activo.")

        lineas = []
        total = Decimal("0.00")

        for item in productos:
            try:
                id_producto = int(item["id_producto"])
                cantidad = int(item["cantidad"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("Verifica los productos y sus cantidades.")

            if cantidad <= 0:
                raise ValueError(
                    "Las cantidades deben ser enteros mayores que cero."
                )

            cursor.execute("""
                SELECT
                    id_producto,
                    nombre,
                    precio_compra,
                    estado,
                    id_proveedor
                FROM Productos
                WHERE id_producto = %s
                FOR UPDATE
            """, (id_producto,))

            producto = cursor.fetchone()

            if producto is None or producto["estado"] != ESTADO_ACTIVO:
                raise ValueError(
                    f"El producto con ID {id_producto} no existe o está inactivo."
                )

            # Verificar que el proveedor corresponda al producto asignado.
            if (
                producto["id_proveedor"] is not None
                and int(producto["id_proveedor"]) != int(id_proveedor)
            ):
                raise ValueError(
                    f"El producto '{producto['nombre']}' está asignado a otro "
                    "proveedor. Cambia el proveedor del pedido o revisa "
                    "el proveedor asignado al producto."
                )

            costo = Decimal(str(producto["precio_compra"]))
            subtotal = (costo * cantidad).quantize(Decimal("0.01"))
            total += subtotal

            lineas.append({
                "id_producto": id_producto,
                "cantidad": cantidad,
                "costo": costo,
                "subtotal": subtotal,
            })

        if id_pedido is None:
            cursor.execute("""
                INSERT INTO Pedidos_Proveedor
                    (id_proveedor, id_empleado, total, estado)
                VALUES (%s, %s, %s, %s)
            """, (
                id_proveedor,
                id_empleado,
                total,
                ESTADO_PENDIENTE
            ))

            id_pedido = cursor.lastrowid

        else:
            cursor.execute("""
                SELECT id_pedido, estado
                FROM Pedidos_Proveedor
                WHERE id_pedido = %s
                FOR UPDATE
            """, (id_pedido,))

            pedido = cursor.fetchone()

            if (
                pedido is None
                or pedido["estado"] != ESTADO_PENDIENTE
            ):
                raise ValueError(
                    "Solo se pueden modificar pedidos pendientes."
                )

            cursor.execute("""
                SELECT COUNT(*) AS recibidos
                FROM Detalle_Pedido
                WHERE id_pedido = %s
                  AND cantidad_recibida > 0
            """, (id_pedido,))

            if int(cursor.fetchone()["recibidos"]) > 0:
                raise ValueError(
                    "No se puede modificar un pedido que ya tiene "
                    "mercancía recibida."
                )

            cursor.execute("""
                UPDATE Pedidos_Proveedor
                SET id_proveedor = %s,
                    id_empleado = %s,
                    total = %s
                WHERE id_pedido = %s
                  AND estado = %s
            """, (
                id_proveedor,
                id_empleado,
                total,
                id_pedido,
                ESTADO_PENDIENTE
            ))

            cursor.execute("""
                DELETE FROM Detalle_Pedido
                WHERE id_pedido = %s
            """, (id_pedido,))

        for linea in lineas:
            cursor.execute("""
                INSERT INTO Detalle_Pedido
                    (
                        id_pedido,
                        id_producto,
                        cantidad,
                        cantidad_recibida,
                        costo_unitario,
                        subtotal
                    )
                VALUES (%s, %s, %s, 0, %s, %s)
            """, (
                id_pedido,
                linea["id_producto"],
                linea["cantidad"],
                linea["costo"],
                linea["subtotal"]
            ))

        conexion.commit()
        return id_pedido

    except Exception:
        if conexion is not None and conexion.is_connected():
            conexion.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ============================================================
# REGISTRAR RECEPCIONES PARCIALES O COMPLETAS
# ============================================================
def registrar_recepcion(id_pedido, id_empleado, recepciones):
    """
    Registra recepciones parciales o completas.
    Actualiza los detalles, aumenta el stock y registra movimientos.
    """
    if not recepciones:
        raise ValueError("Indica al menos una cantidad recibida.")

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        conexion.start_transaction()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_pedido, estado
            FROM Pedidos_Proveedor
            WHERE id_pedido = %s
            FOR UPDATE
        """, (id_pedido,))

        pedido = cursor.fetchone()

        if (
            pedido is None
            or pedido["estado"] != ESTADO_PENDIENTE
        ):
            raise ValueError(
                "El pedido no existe o ya no está pendiente."
            )

        cursor.execute("""
            SELECT id_empleado
            FROM Empleados
            WHERE id_empleado = %s AND estado = %s
            FOR UPDATE
        """, (id_empleado, ESTADO_ACTIVO))

        if cursor.fetchone() is None:
            raise ValueError("El empleado responsable no está activo.")

        hubo_recepcion = False

        for id_producto, cantidad_recibida in recepciones.items():
            try:
                id_producto = int(id_producto)
                cantidad_recibida = int(cantidad_recibida)
            except (TypeError, ValueError):
                raise ValueError(
                    "Las cantidades recibidas deben ser números enteros."
                )

            if cantidad_recibida < 0:
                raise ValueError(
                    "La cantidad recibida no puede ser negativa."
                )

            if cantidad_recibida == 0:
                continue

            cursor.execute("""
                SELECT
                    dp.cantidad,
                    dp.cantidad_recibida,
                    p.cantidad_stock
                FROM Detalle_Pedido dp
                JOIN Productos p
                    ON p.id_producto = dp.id_producto
                WHERE dp.id_pedido = %s
                  AND dp.id_producto = %s
                FOR UPDATE
            """, (id_pedido, id_producto))

            detalle = cursor.fetchone()

            if detalle is None:
                raise ValueError(
                    f"El producto con ID {id_producto} "
                    "no pertenece al pedido."
                )

            pendiente = (
                int(detalle["cantidad"])
                - int(detalle["cantidad_recibida"])
            )

            if cantidad_recibida > pendiente:
                raise ValueError(
                    f"Solo faltan {pendiente} unidades "
                    f"del producto ID {id_producto}."
                )

            cursor.execute("""
                UPDATE Detalle_Pedido
                SET cantidad_recibida = cantidad_recibida + %s
                WHERE id_pedido = %s
                  AND id_producto = %s
            """, (
                cantidad_recibida,
                id_pedido,
                id_producto
            ))

            cursor.execute("""
                UPDATE Productos
                SET cantidad_stock = cantidad_stock + %s
                WHERE id_producto = %s
            """, (cantidad_recibida, id_producto))

            cursor.execute("""
                INSERT INTO Movimientos_Inventario
                    (
                        id_pedido,
                        id_producto,
                        id_empleado,
                        tipo_movimiento,
                        cantidad,
                        motivo
                    )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                id_pedido,
                id_producto,
                id_empleado,
                "ENTRADA",
                cantidad_recibida,
                f"Recepción del pedido #{id_pedido}"
            ))

            hubo_recepcion = True

        if not hubo_recepcion:
            raise ValueError(
                "Registra al menos una cantidad recibida mayor que cero."
            )

        cursor.execute("""
            SELECT COUNT(*) AS pendientes
            FROM Detalle_Pedido
            WHERE id_pedido = %s
              AND cantidad_recibida < cantidad
        """, (id_pedido,))

        pendientes = int(cursor.fetchone()["pendientes"])

        if pendientes == 0:
            cursor.execute("""
                UPDATE Pedidos_Proveedor
                SET estado = %s
                WHERE id_pedido = %s
                  AND estado = %s
            """, (
                ESTADO_RECIBIDO,
                id_pedido,
                ESTADO_PENDIENTE
            ))

        conexion.commit()

        if pendientes == 0:
            return "Pedido recibido completamente."

        return (
            "Recepción parcial guardada. "
            "El pedido sigue pendiente."
        )

    except Exception:
        if conexion is not None and conexion.is_connected():
            conexion.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ============================================================
# CANCELAR PEDIDOS
# ============================================================
def cancelar_pedido(id_pedido):
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        conexion.start_transaction()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT estado
            FROM Pedidos_Proveedor
            WHERE id_pedido = %s
            FOR UPDATE
        """, (id_pedido,))

        pedido = cursor.fetchone()

        if (
            pedido is None
            or pedido["estado"] != ESTADO_PENDIENTE
        ):
            raise ValueError(
                "Solo se pueden cancelar pedidos pendientes."
            )

        cursor.execute("""
            SELECT COUNT(*) AS recibidos
            FROM Detalle_Pedido
            WHERE id_pedido = %s
              AND cantidad_recibida > 0
        """, (id_pedido,))

        if int(cursor.fetchone()["recibidos"]) > 0:
            raise ValueError(
                "El pedido ya tiene mercancía recibida y no puede "
                "cancelarse completamente desde esta opción."
            )

        cursor.execute("""
            UPDATE Pedidos_Proveedor
            SET estado = %s
            WHERE id_pedido = %s
              AND estado = %s
        """, (
            ESTADO_CANCELADO,
            id_pedido,
            ESTADO_PENDIENTE
        ))

        conexion.commit()

    except Exception:
        if conexion is not None and conexion.is_connected():
            conexion.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()

# ============================================================
# GENERAR PEDIDOS AUTOMÁTICOS DE REABASTECIMIENTO
# ============================================================
def generar_pedidos_automaticos(id_empleado, id_proveedor):
    """
    Crea pedidos de productos activos con stock inferior al mínimo.

    Los productos asignados a otro proveedor no se incluyen.
    Los productos sin proveedor asignado pueden incluirse en el pedido.
    Si hay una cantidad configurada en CANTIDADES_REABASTECIMIENTO,
    se utiliza esa cantidad; de lo contrario, se calcula lo necesario
    para alcanzar el stock mínimo.
    """
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        conexion.start_transaction()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_proveedor
            FROM Proveedores
            WHERE id_proveedor = %s AND estado = %s
            FOR UPDATE
        """, (id_proveedor, ESTADO_ACTIVO))

        if cursor.fetchone() is None:
            raise ValueError("El proveedor seleccionado no está activo.")

        cursor.execute("""
            SELECT id_empleado
            FROM Empleados
            WHERE id_empleado = %s AND estado = %s
            FOR UPDATE
        """, (id_empleado, ESTADO_ACTIVO))

        if cursor.fetchone() is None:
            raise ValueError("El empleado responsable no está activo.")

        cursor.execute("""
            SELECT
                p.id_producto,
                p.nombre,
                p.cantidad_stock,
                p.stock_minimo,
                p.precio_compra
            FROM Productos p
            WHERE p.estado = %s
              AND p.cantidad_stock < p.stock_minimo
              AND (
                    p.id_proveedor = %s
                    OR p.id_proveedor IS NULL
              )
            ORDER BY p.nombre
            FOR UPDATE
        """, (ESTADO_ACTIVO, id_proveedor))

        productos = cursor.fetchall()

        lineas = []
        total = Decimal("0.00")

        for producto in productos:
            id_producto = int(producto["id_producto"])

            # Evitar crear otro pedido para un producto
            # que ya tiene mercancía pendiente de recibir.
            cursor.execute("""
                SELECT COUNT(*) AS pendientes
                FROM Pedidos_Proveedor pp
                JOIN Detalle_Pedido dp
                    ON dp.id_pedido = pp.id_pedido
                WHERE pp.estado = %s
                  AND dp.id_producto = %s
                  AND dp.cantidad_recibida < dp.cantidad
            """, (
                ESTADO_PENDIENTE,
                id_producto
            ))

            if int(cursor.fetchone()["pendientes"]) > 0:
                continue

            cantidad_configurada = CANTIDADES_REABASTECIMIENTO.get(
                id_producto
            )

            if cantidad_configurada is not None:
                cantidad = int(cantidad_configurada)
            else:
                cantidad = max(
                    int(producto["stock_minimo"])
                    - int(producto["cantidad_stock"]),
                    0
                )

            if cantidad <= 0:
                continue

            costo = Decimal(str(producto["precio_compra"]))
            subtotal = (costo * cantidad).quantize(Decimal("0.01"))
            total += subtotal

            lineas.append({
                "id_producto": id_producto,
                "cantidad": cantidad,
                "costo": costo,
                "subtotal": subtotal
            })

        if not lineas:
            conexion.commit()
            return None, 0

        cursor.execute("""
            INSERT INTO Pedidos_Proveedor
                (id_proveedor, id_empleado, total, estado)
            VALUES (%s, %s, %s, %s)
        """, (
            id_proveedor,
            id_empleado,
            total,
            ESTADO_PENDIENTE
        ))

        id_pedido = cursor.lastrowid

        for linea in lineas:
            cursor.execute("""
                INSERT INTO Detalle_Pedido
                    (
                        id_pedido,
                        id_producto,
                        cantidad,
                        cantidad_recibida,
                        costo_unitario,
                        subtotal
                    )
                VALUES (%s, %s, %s, 0, %s, %s)
            """, (
                id_pedido,
                linea["id_producto"],
                linea["cantidad"],
                linea["costo"],
                linea["subtotal"]
            ))

        conexion.commit()
        return id_pedido, len(lineas)

    except Exception:
        if conexion is not None and conexion.is_connected():
            conexion.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()

# ============================================================
# INTERFAZ PRINCIPAL DE PEDIDOS
# ============================================================
def abrir_pedidos(
    raiz=None,
    id_empleado_sesion=None,
    nombre_empleado_sesion=None,
    apellidos_empleado_sesion=None
):
    ventana = tk.Toplevel(raiz) if raiz else tk.Tk()

    ventana.title("Gestión de pedidos - Papelería Luna")
    ventana.geometry("1180x760")
    ventana.minsize(980, 650)
    ventana.configure(bg=COLOR_FONDO)

    
    if ventana not in VENTANAS_TEMA:
        VENTANAS_TEMA.append(ventana)

    # --------------------------------------------------------
    # ESTILOS GENERALES DE TKINTER
    # --------------------------------------------------------
    estilo = ttk.Style(ventana)

    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    estilo.configure(
        "TNotebook",
        background=COLOR_FONDO,
        borderwidth=0,
        tabmargins=(0, 0, 0, 0)
    )

    estilo.configure(
        "TNotebook.Tab",
        background=COLOR_ENCABEZADO_TABLA,
        foreground=COLOR_TEXTO,
        font=(FUENTE, 10, "bold"),
        padding=(17, 10),
        borderwidth=0
    )

    estilo.map(
        "TNotebook.Tab",
        background=[
            ("selected", COLOR_AZUL),
            ("active", "#CBD5E1")
        ],
        foreground=[
            ("selected", "#FFFFFF"),
            ("active", COLOR_AZUL)
        ]
    )

    estilo.configure(
        "Treeview",
        rowheight=34,
        font=(FUENTE, 9),
        background=COLOR_PANEL,
        fieldbackground=COLOR_PANEL,
        foreground=COLOR_TEXTO,
        borderwidth=0,
        relief="flat"
    )

    estilo.configure(
        "Treeview.Heading",
        font=(FUENTE, 9, "bold"),
        background=COLOR_ENCABEZADO_TABLA,
        foreground=COLOR_AZUL,
        padding=(9, 10),
        relief="flat"
    )

    estilo.map(
        "Treeview",
        background=[("selected", COLOR_SELECCION)],
        foreground=[("selected", COLOR_AZUL)]
    )

    estilo.map(
        "Treeview.Heading",
        background=[("active", "#CBD5E1")]
    )


    
    # --------------------------------------------------------
    # ESTILO DE LOS COMBOBOX - PAPELERÍA LUNA
    # --------------------------------------------------------
    estilo.configure(
        "TCombobox",
        font=(FUENTE, 10),
        padding=(10, 8),
        foreground=COLOR_TEXTO,
        fieldbackground=COLOR_PANEL,
        background=COLOR_PANEL,
        arrowcolor=COLOR_AZUL,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
        relief="flat",
        arrowsize=15
    )

    estilo.map(
        "TCombobox",
        foreground=[
            ("disabled", COLOR_SUAVE),
            ("readonly", COLOR_TEXTO)
        ],
        fieldbackground=[
            ("disabled", COLOR_FONDO),
            ("readonly", COLOR_PANEL)
        ],
        background=[
            ("active", COLOR_ENCABEZADO_TABLA),
            ("readonly", COLOR_PANEL)
        ],
        arrowcolor=[
            ("active", COLOR_NARANJA),
            ("readonly", COLOR_AZUL)
        ],
        bordercolor=[
            ("focus", COLOR_NARANJA)
        ],
        lightcolor=[
            ("focus", COLOR_NARANJA)
        ],
        darkcolor=[
            ("focus", COLOR_NARANJA)
        ]
    )

    # Apariencia de la lista desplegable.
    ventana.option_add(
        "*TCombobox*Listbox.background",
        COLOR_PANEL
    )
    ventana.option_add(
        "*TCombobox*Listbox.foreground",
        COLOR_TEXTO
    )
    ventana.option_add(
        "*TCombobox*Listbox.selectBackground",
        COLOR_SELECCION
    )
    ventana.option_add(
        "*TCombobox*Listbox.selectForeground",
        COLOR_AZUL
    )
    ventana.option_add(
        "*TCombobox*Listbox.font",
        (FUENTE, 10)
    )

    
    # --------------------------------------------------------
    # ACTUALIZACIÓN DINÁMICA DEL TEMA
    # --------------------------------------------------------
    

    def actualizar_tema(nuevos_colores=None):
        global TEMA_ACTUAL, COLORES
        global COLOR_FONDO, COLOR_PANEL
        global COLOR_AZUL, COLOR_AZUL_SECUNDARIO
        global COLOR_NARANJA, COLOR_ROJO
        global COLOR_TEXTO, COLOR_SUAVE, COLOR_BORDE
        global COLOR_HOVER_NARANJA, COLOR_HOVER_ROJO
        global COLOR_SELECCION, COLOR_ENCABEZADO_TABLA
        global COLOR_ENTRADA, COLOR_VERDE, COLOR_HOVER_VERDE

        TEMA_ACTUAL = obtener_tema_actual()
        COLORES = (
            nuevos_colores
            if isinstance(nuevos_colores, dict)
            else obtener_colores(TEMA_ACTUAL)
        )

        COLOR_FONDO = COLORES["FONDO"]
        COLOR_PANEL = COLORES["PANEL"]
        COLOR_AZUL = COLORES["AZUL"]
        COLOR_AZUL_SECUNDARIO = COLORES["AZUL_SECUNDARIO"]
        COLOR_NARANJA = COLORES["NARANJA"]
        COLOR_ROJO = COLORES["ROJO"]
        COLOR_TEXTO = COLORES["TEXTO"]
        COLOR_SUAVE = COLORES["TEXTO_SUAVE"]
        COLOR_BORDE = COLORES["BORDE"]
        COLOR_HOVER_NARANJA = COLORES["NARANJA_HOVER"]
        COLOR_HOVER_ROJO = COLORES["ROJO_HOVER"]
        COLOR_VERDE = COLORES.get("VERDE", "#0F766E")
        COLOR_HOVER_VERDE = COLORES.get("VERDE_HOVER", "#115E59")
        COLOR_SELECCION = COLORES["SELECCION"]
        COLOR_ENTRADA = COLORES["ENTRADA"]

        COLOR_ENCABEZADO_TABLA = (
            "#E2E8F0" if TEMA_ACTUAL == "claro"
            else "#374151"
        )

        
        # Traducir colores de AMBAS paletas al tema actual. Es importante
        # incluir los valores oscuros también: de lo contrario, al volver
        # de oscuro a claro algunos widgets conservan sus colores anteriores.
        equivalencias_fondo = {
            "#F1F5F9": COLOR_FONDO,
            "#F8FAFC": COLOR_FONDO,
            "#FFFFFF": COLOR_PANEL,
            "#E2E8F0": COLOR_ENCABEZADO_TABLA,
            "#CBD5E1": COLOR_BORDE,
            "#DBE3ED": COLOR_BORDE,
            "#172554": COLOR_AZUL,
            "#1E3A5F": COLOR_AZUL_SECUNDARIO,
            "#111827": COLOR_FONDO,
            "#1F2937": COLOR_PANEL,
            "#030712": COLOR_AZUL,
            # También se usa como encabezado de tabla en modo oscuro.
            # Los botones secundarios se vuelven a ajustar con su callback.
            "#374151": COLOR_ENCABEZADO_TABLA,
            "#DBEAFE": COLOR_SELECCION,
            "#F9FAFB": COLOR_FONDO,
            "#0F766E": COLORES.get("VERDE", "#0F766E"),
            "#115E59": COLORES.get("VERDE_HOVER", "#115E59"),
            "#475569": COLOR_SUAVE,
        }

        equivalencias_texto = {
            "#1E293B": COLOR_TEXTO,
            "#64748B": COLOR_SUAVE,
            "#172554": COLOR_AZUL,
            "#030712": COLOR_AZUL,
            "#374151": COLOR_AZUL_SECUNDARIO,
            "#9CA3AF": COLOR_SUAVE,
            "#F9FAFB": COLOR_TEXTO,
        }

        try:
            estilo.configure(
                "TNotebook",
                background=COLOR_FONDO,
                borderwidth=0
            )

            estilo.configure(
                "TNotebook.Tab",
                background=COLOR_ENCABEZADO_TABLA,
                foreground=COLOR_TEXTO
            )

            estilo.map(
                "TNotebook.Tab",
                background=[
                    ("selected", COLOR_AZUL),
                    ("active", COLOR_BORDE)
                ],
                foreground=[
                    ("selected", "#FFFFFF"),
                    ("active", COLOR_TEXTO)
                ]
            )

            estilo.configure(
                "Treeview",
                background=COLOR_PANEL,
                fieldbackground=COLOR_PANEL,
                foreground=COLOR_TEXTO
            )

            estilo.configure(
                "Treeview.Heading",
                background=COLOR_ENCABEZADO_TABLA,
                foreground=COLOR_AZUL
            )

            estilo.map(
                "Treeview",
                background=[("selected", COLOR_SELECCION)],
                foreground=[("selected", COLOR_AZUL)]
            )

            # Estilos propios de los diálogos de detalle y recepción.
            # ttk.Style comparte estos estilos entre ventanas, por lo que
            # también se actualizan si el diálogo ya estaba abierto.
            for nombre_estilo in (
                "DetallePedido.Treeview",
                "Recepcion.Treeview"
            ):
                estilo.configure(
                    nombre_estilo,
                    background=COLOR_PANEL,
                    fieldbackground=COLOR_PANEL,
                    foreground=COLOR_TEXTO
                )
                estilo.map(
                    nombre_estilo,
                    background=[("selected", COLOR_SELECCION)],
                    foreground=[("selected", COLOR_AZUL)]
                )

            for nombre_estilo in (
                "DetallePedido.Treeview.Heading",
                "Recepcion.Treeview.Heading"
            ):
                estilo.configure(
                    nombre_estilo,
                    background=COLOR_ENCABEZADO_TABLA,
                    foreground=COLOR_AZUL
                )

            estilo.configure(
                "Recepcion.TEntry",
                foreground=COLOR_TEXTO,
                fieldbackground=COLOR_ENTRADA,
                background=COLOR_ENTRADA
            )

            estilo.configure(
                "TCombobox",
                foreground=COLOR_TEXTO,
                fieldbackground=COLOR_ENTRADA,
                background=COLOR_PANEL,
                arrowcolor=COLOR_AZUL,
                bordercolor=COLOR_BORDE,
                lightcolor=COLOR_BORDE,
                darkcolor=COLOR_BORDE
            )

            ventana.option_add(
                "*TCombobox*Listbox.background", COLOR_PANEL
            )
            ventana.option_add(
                "*TCombobox*Listbox.foreground", COLOR_TEXTO
            )
            ventana.option_add(
                "*TCombobox*Listbox.selectBackground", COLOR_SELECCION
            )
            ventana.option_add(
                "*TCombobox*Listbox.selectForeground", COLOR_AZUL
            )

        except tk.TclError:
            pass

        # Recolorear la ventana principal y los diálogos registrados.
        for ventana_registrada in list(VENTANAS_TEMA):
            try:
                if not ventana_registrada.winfo_exists():
                    VENTANAS_TEMA.remove(ventana_registrada)
                    continue

                pendientes = [ventana_registrada]

                while pendientes:
                    widget = pendientes.pop()

                    try:
                        opciones = widget.configure()

                        # Tkinter devuelve los nombres canónicos de las
                        # opciones ("background" y "foreground"), no siempre
                        # los alias cortos ("bg" y "fg"). Revisar ambos evita
                        # que los widgets clásicos se queden con el tema anterior.
                        if "background" in opciones or "bg" in opciones:
                            fondo = widget.cget("background")
                            fondo_normalizado = str(fondo).upper()
                            mapa_fondos = {
                                str(clave).upper(): valor
                                for clave, valor in equivalencias_fondo.items()
                            }
                            if fondo_normalizado in mapa_fondos:
                                widget.configure(
                                    background=mapa_fondos[fondo_normalizado]
                                )

                        if "foreground" in opciones or "fg" in opciones:
                            texto = widget.cget("foreground")
                            texto_normalizado = str(texto).upper()
                            mapa_textos = {
                                str(clave).upper(): valor
                                for clave, valor in equivalencias_texto.items()
                            }
                            if (
                                texto_normalizado != "#FFFFFF"
                                and texto_normalizado in mapa_textos
                            ):
                                widget.configure(
                                    foreground=mapa_textos[texto_normalizado]
                                )

                        if "highlightbackground" in opciones:
                            borde = widget.cget("highlightbackground")
                            if borde in equivalencias_fondo:
                                widget.configure(
                                    highlightbackground=equivalencias_fondo[borde]
                                )

                    except (tk.TclError, TypeError):
                        pass

                    try:
                        pendientes.extend(widget.winfo_children())
                    except tk.TclError:
                        pass

                    # Actualizar botones con colores dinámicos.
                    actualizar_boton = getattr(
                        widget, "_actualizar_color_tema", None
                    )
                    if callable(actualizar_boton):
                        actualizar_boton()

            except tk.TclError:
                pass

        try:
            ventana.update_idletasks()
        except tk.TclError:
            pass

    # --------------------------------------------------------
    # FUNCIONES AUXILIARES VISUALES
    # --------------------------------------------------------
    
    ventanas_tema_local = [ventana]

    def registrar_ventana_tema(ventana_secundaria):
        if ventana_secundaria not in ventanas_tema_local:
            ventanas_tema_local.append(ventana_secundaria)

        if ventana_secundaria not in VENTANAS_TEMA:
            VENTANAS_TEMA.append(ventana_secundaria)

    def al_cambiar_tema(*args, **kwargs):
        colores_nuevos = next(
            (arg for arg in args if isinstance(arg, dict)),
            None
        )

        actualizar_tema(colores_nuevos)

    registrar_observador(al_cambiar_tema)

    def limpiar_registro_tema(evento=None):
        if evento is not None and evento.widget is not ventana:
            return

        try:
            eliminar_observador(al_cambiar_tema)
        except (tk.TclError, TypeError):
            pass

        for ventana_registrada in ventanas_tema_local:
            while ventana_registrada in VENTANAS_TEMA:
                VENTANAS_TEMA.remove(ventana_registrada)

    ventana.bind("<Destroy>", limpiar_registro_tema, add="+")

    
    def crear_boton(
        parent,
        texto,
        color,
        funcion,
        color_hover=None,
        ancho=None
    ):
        # Identificar el tipo de botón para poder actualizar
        # sus colores cuando cambie el tema.
        if color == COLOR_NARANJA:
            tipo_color = "NARANJA"
        elif color == COLOR_ROJO:
            tipo_color = "ROJO"
        elif color == COLOR_VERDE:
            tipo_color = "VERDE"
        elif color == COLOR_AZUL:
            tipo_color = "AZUL"
        elif color == COLOR_AZUL_SECUNDARIO:
            tipo_color = "AZUL_SECUNDARIO"
        elif color == COLOR_SUAVE:
            tipo_color = "SUAVE"
        else:
            tipo_color = "PERSONALIZADO"

        # Guardar los colores originales y el tipo de botón.
        # Estos atributos permitirán actualizarlo después.
        boton = tk.Button(
            parent,
            text=texto,
            bg=color,
            fg="#FFFFFF",
            activebackground=color_hover or COLOR_AZUL_SECUNDARIO,
            activeforeground="#FFFFFF",
            relief="flat",
            font=(FUENTE, 9, "bold"),
            padx=14,
            pady=8,
            command=funcion,
            cursor="hand2",
            bd=0,
            highlightthickness=0,
            takefocus=True
        )

        boton._tipo_color_tema = tipo_color
        boton._color_personalizado = color
        boton._hover_personalizado = color_hover
        boton._hover_activo = False

        if ancho is not None:
            boton.configure(width=ancho)

        def obtener_colores_boton():
            tema = obtener_tema_actual()
            colores = obtener_colores(tema)

            if tipo_color == "NARANJA":
                base = colores["NARANJA"]
                hover = colores["NARANJA_HOVER"]

            elif tipo_color == "ROJO":
                base = colores["ROJO"]
                hover = colores["ROJO_HOVER"]

            elif tipo_color == "AZUL":
                base = colores["AZUL"]
                hover = colores["AZUL_SECUNDARIO"]

            elif tipo_color == "AZUL_SECUNDARIO":
                base = colores["AZUL_SECUNDARIO"]
                hover = colores["AZUL"]

            elif tipo_color == "VERDE":
                # Conservar el color verde propio del proyecto.
                base = COLOR_VERDE
                hover = COLOR_HOVER_VERDE

            elif tipo_color == "SUAVE":
                base = colores["TEXTO_SUAVE"]
                hover = "#475569"

            else:
                base = boton._color_personalizado
                hover = (
                    boton._hover_personalizado
                    or colores["AZUL_SECUNDARIO"]
                )

            return base, hover

        def actualizar_color_boton():
            try:
                if not boton.winfo_exists():
                    return

                base, hover = obtener_colores_boton()

                boton.configure(
                    bg=hover if boton._hover_activo else base,
                    activebackground=hover,
                    fg="#FFFFFF",
                    activeforeground="#FFFFFF"
                )

            except tk.TclError:
                pass

        def al_entrar(evento):
            boton._hover_activo = True
            actualizar_color_boton()

        def al_salir(evento):
            boton._hover_activo = False
            actualizar_color_boton()

        boton.bind("<Enter>", al_entrar)
        boton.bind("<Leave>", al_salir)

        # Facilitar la actualización posterior del botón.
        boton._actualizar_color_tema = actualizar_color_boton

        return boton


    def crear_panel(parent, padx=16, pady=14):
        return tk.Frame(
            parent,
            bg=COLOR_PANEL,
            padx=padx,
            pady=pady,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

    
    # --------------------------------------------------------
    # CARGAR AUTOMÁTICAMENTE AL EMPLEADO DE LA SESIÓN
    # --------------------------------------------------------
    if id_empleado_sesion is None:
        messagebox.showerror(
            "Sesión no identificada",
            "No se recibió el empleado que inició sesión. "
            "Cierra esta ventana y vuelve a entrar desde el menú.",
            parent=ventana
        )
        ventana.destroy()
        return

    try:
        registros_empleado = _consultar_todos("""
            SELECT id_empleado, nombre, apellidos
            FROM Empleados
            WHERE id_empleado = %s
              AND estado = %s
        """, (id_empleado_sesion, ESTADO_ACTIVO))

        if not registros_empleado:
            messagebox.showerror(
                "Empleado no disponible",
                "El empleado de la sesión no existe o está inactivo.",
                parent=ventana
            )
            ventana.destroy()
            return

        empleado_sesion = registros_empleado[0]

        id_empleado_sesion = int(
            empleado_sesion["id_empleado"]
        )

        nombre_completo_sesion = (
            f"{empleado_sesion['nombre']} "
            f"{empleado_sesion['apellidos']}"
        ).strip()

    except Exception as error:
        messagebox.showerror(
            "Base de datos",
            f"No fue posible identificar al empleado.\n\n{error}",
            parent=ventana
        )
        ventana.destroy()
        return

    # ============================================================
    # ENCABEZADO PRINCIPAL - PAPELERÍA LUNA / PEDIDOS
    # ============================================================
    encabezado = tk.Frame(
        ventana,
        bg=COLOR_AZUL
    )
    encabezado.pack(fill="x", side="top")

    # Línea naranja superior
    tk.Frame(
        encabezado,
        bg=COLOR_NARANJA,
        height=5
    ).pack(side="top", fill="x")

    # Contenido del encabezado
    contenido_encabezado = tk.Frame(
        encabezado,
        bg=COLOR_AZUL,
        padx=25,
        pady=12
    )
    contenido_encabezado.pack(fill="x")

    tk.Label(
        contenido_encabezado,
        text="PAPELERÍA LUNA / PEDIDOS",
        bg=COLOR_AZUL,
        fg=COLOR_NARANJA,
        font=(FUENTE, 11, "bold"),
        anchor="w"
    ).pack(anchor="w")

    tk.Label(
        contenido_encabezado,
        text="CONTROL DE PEDIDOS",
        bg=COLOR_AZUL,
        fg="#FFFFFF",
        font=(FUENTE, 20, "bold"),
        anchor="w"
    ).pack(anchor="w", pady=(2, 0))

    tk.Label(
        contenido_encabezado,
        text="Gestión de pedidos a proveedores",
        bg=COLOR_AZUL,
        fg="#DBEAFE",
        font=(FUENTE, 9),
        anchor="w"
    ).pack(anchor="w", pady=(2, 0))

    # --------------------------------------------------------
    # ZONA PRINCIPAL
    # --------------------------------------------------------
    zona = tk.Frame(
        ventana,
        bg=COLOR_FONDO,
        padx=18,
        pady=14
    )
    zona.pack(fill="both", expand=True)

    # --------------------------------------------------------
    # RESPONSABLE DEL PEDIDO
    # --------------------------------------------------------
    tarjeta_responsable = crear_panel(zona, padx=18, pady=13)
    tarjeta_responsable.pack(fill="x", pady=(0, 14))

    tk.Label(
        tarjeta_responsable,
        text="RESPONSABLE DEL PEDIDO",
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
        font=(FUENTE, 10, "bold")
    ).pack(anchor="w")

    
    tk.Label(
        tarjeta_responsable,
        text="Empleado identificado automáticamente desde la sesión.",
        bg=COLOR_PANEL,
        fg=COLOR_SUAVE,
        font=(FUENTE, 9)
    ).pack(anchor="w", pady=(3, 9))

    fila_resp = tk.Frame(
        tarjeta_responsable,
        bg=COLOR_PANEL
    )
    fila_resp.pack(fill="x")

    tk.Label(
        fila_resp,
        text="Empleado responsable:",
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        font=(FUENTE, 10, "bold")
    ).pack(side="left", padx=(0, 12))

    tk.Label(
        fila_resp,
        text=nombre_completo_sesion,
        bg="#F1F5F9",
        fg=COLOR_AZUL,
        font=(FUENTE, 10, "bold"),
        padx=12,
        pady=7,
        relief="flat"
    ).pack(side="left")


    # --------------------------------------------------------
    # INDICADORES RESUMIDOS
    # --------------------------------------------------------
    tarjetas_resumen = tk.Frame(
        zona,
        bg=COLOR_FONDO
    )
    tarjetas_resumen.pack(fill="x", pady=(0, 14))

    def crear_tarjeta_resumen(parent, titulo, color):
        tarjeta = tk.Frame(
            parent,
            bg=COLOR_PANEL,
            padx=17,
            pady=12,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        tarjeta.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        tk.Frame(
            tarjeta,
            bg=color,
            height=4
        ).pack(fill="x", pady=(0, 10))

        tk.Label(
            tarjeta,
            text=titulo.upper(),
            bg=COLOR_PANEL,
            fg=COLOR_SUAVE,
            font=(FUENTE, 9, "bold")
        ).pack(anchor="w")

        valor = tk.Label(
            tarjeta,
            text="0",
            bg=COLOR_PANEL,
            fg=color,
            font=(FUENTE, 23, "bold")
        )
        valor.pack(anchor="w", pady=(5, 0))

        return valor

    resumen_pendientes = crear_tarjeta_resumen(
        tarjetas_resumen,
        "Pedidos pendientes",
        COLOR_AZUL
    )

    resumen_recibidos = crear_tarjeta_resumen(
        tarjetas_resumen,
        "Pedidos recibidos",
        COLOR_VERDE
    )

    resumen_unidades = crear_tarjeta_resumen(
        tarjetas_resumen,
        "Unidades por recibir",
        COLOR_NARANJA
    )

    tarjetas_resumen.winfo_children()[-1].pack_configure(
        padx=(0, 0)
    )

    # --------------------------------------------------------
    # PANEL INFERIOR DE ACCIONES
    # --------------------------------------------------------
    marco_acciones = tk.Frame(
        zona,
        bg=COLOR_FONDO
    )
    marco_acciones.pack(
        side="bottom",
        fill="x",
        expand=False,
        pady=(10, 0)
    )

    # Grupo izquierdo.
    marco_pedidos = tk.LabelFrame(
        marco_acciones,
        text="  Gestión de pedidos  ",
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
        font=(FUENTE, 9, "bold"),
        padx=10,
        pady=9,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
        relief="flat",
        bd=0
    )
    marco_pedidos.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 5)
    )

    fila_acciones_pedido = tk.Frame(
        marco_pedidos,
        bg=COLOR_PANEL
    )
    fila_acciones_pedido.pack(fill="x", expand=True)

    # Grupo derecho.
    marco_inventario = tk.LabelFrame(
        marco_acciones,
        text="  Recepción e inventario  ",
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
        font=(FUENTE, 9, "bold"),
        padx=10,
        pady=9,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
        relief="flat",
        bd=0
    )
    marco_inventario.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(5, 0)
    )

    fila_acciones_inventario = tk.Frame(
        marco_inventario,
        bg=COLOR_PANEL
    )
    fila_acciones_inventario.pack(fill="x", expand=True)

    # --------------------------------------------------------
    # ÁREA DE SEGUIMIENTO
    # --------------------------------------------------------
    marco_seguimiento = tk.Frame(
        zona,
        bg=COLOR_PANEL,
        padx=9,
        pady=9,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    marco_seguimiento.pack(
        side="top",
        fill="both",
        expand=True,
        pady=(0, 0)
    )

    tk.Label(
        marco_seguimiento,
        text="Seguimiento de pedidos",
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
        font=(FUENTE, 12, "bold")
    ).pack(anchor="w", padx=5, pady=(3, 9))

    notebook = ttk.Notebook(marco_seguimiento)
    notebook.pack(fill="both", expand=True)

    
    tab_pendientes = tk.Frame(
        notebook,
        bg=COLOR_PANEL,
        padx=8,
        pady=8
    )

    tab_recibidos = tk.Frame(
        notebook,
        bg=COLOR_PANEL,
        padx=8,
        pady=8
    )

    tab_cancelados = tk.Frame(
        notebook,
        bg=COLOR_PANEL,
        padx=8,
        pady=8
    )

    notebook.add(
        tab_pendientes,
        text="Pendientes de recibir"
    )

    notebook.add(
        tab_recibidos,
        text="Historial de recibidos"
    )

    notebook.add(
        tab_cancelados,
        text="Pedidos cancelados"
    )

    columnas = (
        "id",
        "proveedor",
        "fecha",
        "responsable",
        "total",
        "pendientes"
    )

    titulos = (
        "N.º pedido",
        "Proveedor",
        "Fecha del pedido",
        "Responsable",
        "Total",
        "Unidades pendientes"
    )

    def crear_tabla(parent):
        contenedor = tk.Frame(
            parent,
            bg=COLOR_PANEL
        )
        contenedor.pack(fill="both", expand=True)

        tabla = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        for col, titulo in zip(columnas, titulos):
            tabla.heading(col, text=titulo)
            tabla.column(
                col,
                width=125,
                anchor="center",
                stretch=True
            )

        tabla.column(
            "id",
            width=85,
            anchor="center",
            stretch=False
        )

        tabla.column(
            "proveedor",
            width=190,
            anchor="w"
        )

        tabla.column(
            "fecha",
            width=155,
            anchor="center"
        )

        tabla.column(
            "responsable",
            width=175,
            anchor="w"
        )

        tabla.column(
            "total",
            width=115,
            anchor="e"
        )

        tabla.column(
            "pendientes",
            width=145,
            anchor="center"
        )

        scroll_y = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=tabla.yview
        )

        scroll_x = ttk.Scrollbar(
            parent,
            orient="horizontal",
            command=tabla.xview
        )

        tabla.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        tabla.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll_y.pack(
            side="right",
            fill="y"
        )

        scroll_x.pack(
            fill="x",
            pady=(5, 0)
        )

        return tabla

    tabla_pendientes = crear_tabla(tab_pendientes)
    tabla_recibidos = crear_tabla(tab_recibidos)
    tabla_cancelados = crear_tabla(tab_cancelados)

    # --------------------------------------------------------
    # FUNCIONES DE APOYO DE LA INTERFAZ
    # --------------------------------------------------------
    def responsable_id():
        return id_empleado_sesion

    def pedido_seleccionado(tabla):
        seleccion = tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona un pedido",
                "Primero selecciona un pedido de la tabla.",
                parent=ventana
            )
            return None

        return int(
            tabla.item(seleccion[0], "values")[0]
        )

    # --------------------------------------------------------
    # ACTUALIZAR TABLAS E INDICADORES
    # --------------------------------------------------------
    
    def actualizar_tablas():
        try:
            pedidos_pendientes = obtener_pedidos(
                ESTADO_PENDIENTE
            )

            pedidos_recibidos = obtener_pedidos(
                ESTADO_RECIBIDO
            )

            pedidos_cancelados = obtener_pedidos(
                ESTADO_CANCELADO
            )

            tablas_pedidos = (
                (tabla_pendientes, pedidos_pendientes),
                (tabla_recibidos, pedidos_recibidos),
                (tabla_cancelados, pedidos_cancelados)
            )

            for tabla, pedidos in tablas_pedidos:
                tabla.delete(*tabla.get_children())

                for pedido in pedidos:
                    fecha = pedido["fecha_pedido"]

                    tabla.insert(
                        "",
                        "end",
                        values=(
                            pedido["id_pedido"],
                            pedido["proveedor"],
                            fecha,
                            pedido["responsable"],
                            f"${Decimal(str(pedido['total'])):,.2f}",
                            pedido["unidades_pendientes"]
                        )
                    )

            total_unidades_pendientes = sum(
                int(pedido["unidades_pendientes"] or 0)
                for pedido in pedidos_pendientes
            )

            resumen_pendientes.config(
                text=str(len(pedidos_pendientes))
            )

            resumen_recibidos.config(
                text=str(len(pedidos_recibidos))
            )

            resumen_unidades.config(
                text=str(total_unidades_pendientes)
            )

        except Exception as error:
            messagebox.showerror(
                "Base de datos",
                str(error),
                parent=ventana
            )

    # --------------------------------------------------------
    # VER DETALLE DE UN PEDIDO - INTERFAZ MEJORADA
    # --------------------------------------------------------
    def mostrar_detalle(id_pedido):
        try:
            detalles = obtener_detalles_pedido(id_pedido)

            # ================================================
            # VENTANA
            # ================================================
            dialogo = tk.Toplevel(ventana)
            dialogo.title(f"Detalle del pedido #{id_pedido}")
            dialogo.geometry("780x540")
            dialogo.minsize(620, 420)
            dialogo.configure(bg=COLOR_FONDO)
            registrar_ventana_tema(dialogo)
            dialogo.transient(ventana)
            dialogo.grab_set()

            # Centrar respecto a la ventana principal.
            dialogo.update_idletasks()

            ancho = 780
            alto = 540

            x = ventana.winfo_rootx() + (
                ventana.winfo_width() - ancho
            ) // 2

            y = ventana.winfo_rooty() + (
                ventana.winfo_height() - alto
            ) // 2

            dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")

            # ================================================
            # ENCABEZADO AZUL
            # ================================================
            encabezado_detalle = tk.Frame(
                dialogo,
                bg=COLOR_AZUL,
                padx=24,
                pady=17
            )
            encabezado_detalle.pack(fill="x")

            tk.Label(
                encabezado_detalle,
                text="PAPELERÍA LUNA / PEDIDOS",
                bg=COLOR_AZUL,
                fg=COLOR_NARANJA,
                font=(FUENTE, 9, "bold")
            ).pack(anchor="w")

            tk.Label(
                encabezado_detalle,
                text="Detalle del pedido",
                bg=COLOR_AZUL,
                fg="#FFFFFF",
                font=(FUENTE, 20, "bold")
            ).pack(anchor="w", pady=(4, 0))

            tk.Label(
                encabezado_detalle,
                text=f"Consulta de productos del pedido #{id_pedido}",
                bg=COLOR_AZUL,
                fg="#DBEAFE",
                font=(FUENTE, 9)
            ).pack(anchor="w", pady=(4, 0))

            tk.Frame(
                dialogo,
                bg=COLOR_NARANJA,
                height=5
            ).pack(fill="x")

            # ================================================
            # ÁREA DE CONTENIDO
            # ================================================
            contenido = tk.Frame(
                dialogo,
                bg=COLOR_FONDO,
                padx=18,
                pady=16
            )
            contenido.pack(fill="both", expand=True)

            tarjeta = crear_panel(
                contenido,
                padx=16,
                pady=14
            )
            tarjeta.pack(fill="both", expand=True)

            # ================================================
            # IDENTIFICACIÓN DEL PEDIDO
            # ================================================
            fila_titulo = tk.Frame(
                tarjeta,
                bg=COLOR_PANEL
            )
            fila_titulo.pack(fill="x", pady=(0, 5))

            tk.Label(
                fila_titulo,
                text=f"Pedido #{id_pedido}",
                bg=COLOR_PANEL,
                fg=COLOR_AZUL,
                font=(FUENTE, 13, "bold")
            ).pack(side="left")

            tk.Label(
                fila_titulo,
                text=f"{len(detalles)} producto(s)",
                bg=COLOR_PANEL,
                fg=COLOR_SUAVE,
                font=(FUENTE, 9)
            ).pack(side="right")

            tk.Label(
                tarjeta,
                text=(
                    "Consulta las cantidades solicitadas, recibidas "
                    "y las unidades que aún faltan por recibir."
                ),
                bg=COLOR_PANEL,
                fg=COLOR_SUAVE,
                font=(FUENTE, 9),
                wraplength=680,
                justify="left"
            ).pack(anchor="w", pady=(0, 12))

            # ================================================
            # ESTILO DE LA TABLA DE DETALLE
            # ================================================
            estilo_detalle = ttk.Style(dialogo)

            estilo_detalle.configure(
                "DetallePedido.Treeview",
                rowheight=35,
                font=(FUENTE, 9),
                background=COLOR_PANEL,
                fieldbackground=COLOR_PANEL,
                foreground=COLOR_TEXTO,
                borderwidth=0
            )

            estilo_detalle.configure(
                "DetallePedido.Treeview.Heading",
                font=(FUENTE, 9, "bold"),
                background=COLOR_ENCABEZADO_TABLA,
                foreground=COLOR_AZUL,
                padding=(9, 10),
                relief="flat"
            )

            estilo_detalle.map(
                "DetallePedido.Treeview",
                background=[("selected", COLOR_SELECCION)],
                foreground=[("selected", COLOR_AZUL)]
            )

            # ================================================
            # TABLA
            # ================================================
            contenedor_tabla = tk.Frame(
                tarjeta,
                bg=COLOR_PANEL,
                highlightbackground=COLOR_BORDE,
                highlightthickness=1
            )
            contenedor_tabla.pack(
                fill="both",
                expand=True
            )

            columnas_detalle = (
                "producto",
                "solicitados",
                "recibidos",
                "faltan"
            )

            tabla = ttk.Treeview(
                contenedor_tabla,
                columns=columnas_detalle,
                show="headings",
                style="DetallePedido.Treeview",
                selectmode="browse"
            )

            encabezados = (
                ("producto", "Producto"),
                ("solicitados", "Solicitados"),
                ("recibidos", "Recibidos"),
                ("faltan", "Pendientes")
            )

            for columna, titulo in encabezados:
                tabla.heading(columna, text=titulo)

            tabla.column(
                "producto",
                width=310,
                minwidth=180,
                anchor="w",
                stretch=True
            )

            tabla.column(
                "solicitados",
                width=115,
                minwidth=85,
                anchor="center",
                stretch=False
            )

            tabla.column(
                "recibidos",
                width=105,
                minwidth=85,
                anchor="center",
                stretch=False
            )

            tabla.column(
                "faltan",
                width=105,
                minwidth=85,
                anchor="center",
                stretch=False
            )

            scroll_y = ttk.Scrollbar(
                contenedor_tabla,
                orient="vertical",
                command=tabla.yview
            )

            tabla.configure(
                yscrollcommand=scroll_y.set
            )

            tabla.pack(
                side="left",
                fill="both",
                expand=True
            )

            scroll_y.pack(
                side="right",
                fill="y"
            )

            # Colores para diferenciar el estado de las cantidades.
            tabla.tag_configure(
                "completo",
                foreground=COLOR_VERDE
            )

            tabla.tag_configure(
                "pendiente",
                foreground=COLOR_TEXTO
            )

            # ================================================
            # CARGAR DETALLES
            # ================================================
            total_solicitado = 0
            total_recibido = 0
            total_faltante = 0

            for detalle in detalles:
                solicitados = int(detalle["cantidad"])
                recibidos = int(detalle["cantidad_recibida"])
                faltan = max(solicitados - recibidos, 0)

                total_solicitado += solicitados
                total_recibido += recibidos
                total_faltante += faltan

                etiqueta_fila = (
                    "completo" if faltan == 0 else "pendiente"
                )

                tabla.insert(
                    "",
                    "end",
                    values=(
                        detalle["nombre"],
                        solicitados,
                        recibidos,
                        faltan
                    ),
                    tags=(etiqueta_fila,)
                )

            # ================================================
            # RESUMEN DE UNIDADES
            # ================================================
            resumen = tk.Frame(
                tarjeta,
                bg=COLOR_PANEL
            )
            resumen.pack(fill="x", pady=(12, 0))

            def crear_dato_resumen(parent, titulo, valor, color):
                bloque = tk.Frame(
                    parent,
                    bg=COLOR_PANEL
                )
                bloque.pack(
                    side="left",
                    fill="x",
                    expand=True,
                    padx=(0, 8)
                )

                tk.Label(
                    bloque,
                    text=titulo.upper(),
                    bg=COLOR_PANEL,
                    fg=COLOR_SUAVE,
                    font=(FUENTE, 8, "bold")
                ).pack(anchor="w")

                tk.Label(
                    bloque,
                    text=str(valor),
                    bg=COLOR_PANEL,
                    fg=color,
                    font=(FUENTE, 15, "bold")
                ).pack(anchor="w", pady=(3, 0))

            crear_dato_resumen(
                resumen,
                "Solicitadas",
                total_solicitado,
                COLOR_AZUL
            )

            crear_dato_resumen(
                resumen,
                "Recibidas",
                total_recibido,
                COLOR_VERDE
            )

            crear_dato_resumen(
                resumen,
                "Por recibir",
                total_faltante,
                COLOR_NARANJA if total_faltante > 0 else COLOR_VERDE
            )

            # ================================================
            # PIE Y BOTÓN CERRAR
            # ================================================
            pie_detalle = tk.Frame(
                contenido,
                bg=COLOR_FONDO
            )
            pie_detalle.pack(
                fill="x",
                pady=(12, 0)
            )

            if not detalles:
                tk.Label(
                    pie_detalle,
                    text="Este pedido no tiene productos registrados.",
                    bg=COLOR_FONDO,
                    fg=COLOR_SUAVE,
                    font=(FUENTE, 9)
                ).pack(side="left")

            crear_boton(
                pie_detalle,
                "Cerrar",
                COLOR_AZUL,
                dialogo.destroy,
                color_hover=COLOR_AZUL_SECUNDARIO,
                ancho=12
            ).pack(side="right")

            dialogo.bind(
                "<Escape>",
                lambda evento: dialogo.destroy()
            )

        except Exception as error:
            messagebox.showerror(
                "Detalle del pedido",
                f"No fue posible mostrar el detalle.\n\n{error}",
                parent=ventana
            )

    
    # --------------------------------------------------------
    # CREAR O MODIFICAR PEDIDO
    # --------------------------------------------------------
    def dialogo_pedido(id_pedido=None):
        try:
            proveedores = obtener_proveedores_activos()
            productos = obtener_productos_activos()

            print("PROVEEDORES ACTIVOS:", len(proveedores), proveedores)
            print("PRODUCTOS ACTIVOS:", len(productos), productos)

        except Exception as error:
            messagebox.showerror(
                "Base de datos",
                str(error),
                parent=ventana
            )
            return

        if not proveedores:
            messagebox.showwarning(
                "Proveedores",
                "Necesitas al menos un proveedor activo.",
                parent=ventana
            )
            return

        if not productos:
            messagebox.showwarning(
                "Productos",
                "Necesitas al menos un producto activo.",
                parent=ventana
            )
            return

        pedido_original = None

        if id_pedido is not None:
            try:
                registros = _consultar_todos("""
                    SELECT id_proveedor, id_empleado, estado
                    FROM Pedidos_Proveedor
                    WHERE id_pedido = %s
                """, (id_pedido,))

                pedido_original = registros[0] if registros else None

                if (
                    not pedido_original
                    or pedido_original["estado"] != ESTADO_PENDIENTE
                ):
                    messagebox.showerror(
                        "Pedido",
                        "Solo se pueden modificar pedidos pendientes.",
                        parent=ventana
                    )
                    return

                if any(
                    int(d["cantidad_recibida"]) > 0
                    for d in obtener_detalles_pedido(id_pedido)
                ):
                    messagebox.showerror(
                        "Pedido",
                        "No puedes editar un pedido que ya tiene mercancía recibida.",
                        parent=ventana
                    )
                    return

            except Exception as error:
                messagebox.showerror(
                    "Base de datos",
                    str(error),
                    parent=ventana
                )
                return

        # ====================================================
        # VENTANA PRINCIPAL DEL FORMULARIO
        # ====================================================
        dialogo = tk.Toplevel(ventana)

        dialogo.title(
            "Modificar pedido"
            if id_pedido is not None
            else "Nuevo pedido"
        )

        dialogo.geometry("900x780")
        dialogo.minsize(760, 680)
        dialogo.configure(bg=COLOR_FONDO)
        registrar_ventana_tema(dialogo)
        dialogo.transient(ventana)
        dialogo.grab_set()

        # ====================================================
        # ENCABEZADO AZUL
        # ====================================================
        encabezado_pedido = tk.Frame(
            dialogo,
            bg=COLOR_AZUL,
            padx=24,
            pady=15
        )
        encabezado_pedido.pack(fill="x")

        tk.Label(
            encabezado_pedido,
            text="PAPELERÍA LUNA / PEDIDOS",
            bg=COLOR_AZUL,
            fg=COLOR_NARANJA,
            font=(FUENTE, 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            encabezado_pedido,
            text=(
                "Modificar pedido"
                if id_pedido is not None
                else "Nuevo pedido"
            ),
            bg=COLOR_AZUL,
            fg="#FFFFFF",
            font=(FUENTE, 19, "bold")
        ).pack(anchor="w", pady=(5, 0))

        tk.Label(
            encabezado_pedido,
            text="Registro de compras a proveedores",
            bg=COLOR_AZUL,
            fg="#DBEAFE",
            font=(FUENTE, 9)
        ).pack(anchor="w", pady=(3, 0))

        # Línea naranja de ancho completo.
        tk.Frame(
            dialogo,
            bg=COLOR_NARANJA,
            height=5
        ).pack(fill="x")

        # ====================================================
        # ÁREA GENERAL DEL FORMULARIO
        # ====================================================
        panel = tk.Frame(
            dialogo,
            bg=COLOR_FONDO,
            padx=18,
            pady=14
        )
        panel.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # TARJETA: DATOS DEL PEDIDO
        # ====================================================
        tarjeta_datos = crear_panel(
            panel,
            padx=16,
            pady=13
        )
        tarjeta_datos.pack(
            fill="x",
            pady=(0, 12)
        )

        tk.Label(
            tarjeta_datos,
            text="DATOS DEL PEDIDO",
            bg=COLOR_PANEL,
            fg=COLOR_AZUL,
            font=(FUENTE, 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            tarjeta_datos,
            text="Selecciona el proveedor y agrega los productos necesarios.",
            bg=COLOR_PANEL,
            fg=COLOR_SUAVE,
            font=(FUENTE, 9)
        ).pack(anchor="w", pady=(3, 10))

        proveedor_map = {
            f"{p['id_proveedor']} - {p['nombre']}": p
            for p in proveedores
        }

        producto_map = {
            f"{p['id_producto']} - {p['nombre']}": p
            for p in productos
        }

        # ====================================================
        # PROVEEDOR
        # ====================================================
        fila = tk.Frame(
            tarjeta_datos,
            bg=COLOR_PANEL
        )
        fila.pack(
            fill="x",
            pady=5
        )

        tk.Label(
            fila,
            text="Proveedor:",
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO,
            font=(FUENTE, 10, "bold"),
            width=12,
            anchor="w"
        ).pack(side="left")

        proveedor_var = tk.StringVar()

        combo_proveedor = ttk.Combobox(
            fila,
            textvariable=proveedor_var,
            values=list(proveedor_map),
            state="readonly",
            style="TCombobox",
            font=(FUENTE, 10)
        )
        combo_proveedor.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=3
        )

        # ====================================================
        # PRODUCTO
        # ====================================================
        fila_prod = tk.Frame(
            tarjeta_datos,
            bg=COLOR_PANEL
        )
        fila_prod.pack(
            fill="x",
            pady=(10, 5)
        )

        tk.Label(
            fila_prod,
            text="Producto:",
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO,
            font=(FUENTE, 10, "bold"),
            width=12,
            anchor="w"
        ).pack(side="left")

        producto_var = tk.StringVar()

        combo_producto = ttk.Combobox(
            fila_prod,
            textvariable=producto_var,
            values=list(producto_map),
            state="readonly",
            style="TCombobox",
            font=(FUENTE, 10)
        )
        combo_producto.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=3
        )

        if productos:
            combo_producto.current(0)

        # ====================================================
        # CANTIDAD
        # ====================================================
        fila_cant = tk.Frame(
            tarjeta_datos,
            bg=COLOR_PANEL
        )
        fila_cant.pack(
            fill="x",
            pady=5
        )

        tk.Label(
            fila_cant,
            text="Cantidad:",
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO,
            font=(FUENTE, 10, "bold"),
            width=12,
            anchor="w"
        ).pack(side="left")

        cantidad_var = tk.StringVar(value="1")

        entrada_cantidad = ttk.Entry(
            fila_cant,
            textvariable=cantidad_var,
            width=12
        )
        entrada_cantidad.pack(
            side="left",
            ipady=3
        )

        tk.Label(
            fila_cant,
            text="Unidades solicitadas",
            bg=COLOR_PANEL,
            fg=COLOR_SUAVE,
            font=(FUENTE, 9)
        ).pack(
            side="left",
            padx=10
        )

        # ====================================================
        # TARJETA: PRODUCTOS DEL PEDIDO
        # ====================================================
        carrito = {}

        tarjeta_carrito = crear_panel(
            panel,
            padx=16,
            pady=13
        )
        tarjeta_carrito.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            tarjeta_carrito,
            text="PRODUCTOS DEL PEDIDO",
            bg=COLOR_PANEL,
            fg=COLOR_AZUL,
            font=(FUENTE, 10, "bold")
        ).pack(
            anchor="w",
            pady=(0, 9)
        )

        contenedor_carrito = tk.Frame(
            tarjeta_carrito,
            bg=COLOR_PANEL
        )
        contenedor_carrito.pack(
            fill="both",
            expand=True
        )

        tabla_carrito = ttk.Treeview(
            contenedor_carrito,
            columns=(
                "producto",
                "cantidad",
                "costo",
                "subtotal"
            ),
            show="headings",
            height=7,
            selectmode="browse"
        )

        for col, texto in (
            ("producto", "Producto"),
            ("cantidad", "Cantidad"),
            ("costo", "Costo unitario"),
            ("subtotal", "Subtotal")
        ):
            tabla_carrito.heading(
                col,
                text=texto
            )

        tabla_carrito.column(
            "producto",
            width=260,
            minwidth=150,
            anchor="w"
        )
        tabla_carrito.column(
            "cantidad",
            width=90,
            minwidth=70,
            anchor="center"
        )
        tabla_carrito.column(
            "costo",
            width=120,
            minwidth=100,
            anchor="e"
        )
        tabla_carrito.column(
            "subtotal",
            width=130,
            minwidth=100,
            anchor="e"
        )

        scroll_carrito = ttk.Scrollbar(
            contenedor_carrito,
            orient="vertical",
            command=tabla_carrito.yview
        )

        tabla_carrito.configure(
            yscrollcommand=scroll_carrito.set
        )

        tabla_carrito.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll_carrito.pack(
            side="right",
            fill="y"
        )

        
        # ====================================================
        # FILA INFERIOR: BOTONES Y TOTAL DEL PEDIDO
        # ====================================================
        separador_total = tk.Frame(
            tarjeta_carrito,
            bg=COLOR_BORDE,
            height=1
        )
        separador_total.pack(
            side="bottom",
            fill="x",
            pady=(16, 12)
        )

        fila_total_acciones = tk.Frame(
            tarjeta_carrito,
            bg=COLOR_PANEL
        )
        fila_total_acciones.pack(
            side="bottom",
            fill="x",
            pady=(0, 2)
        )

        crear_boton(
            fila_total_acciones,
            "Agregar producto",
            COLOR_AZUL_SECUNDARIO,
            lambda: agregar_producto(),
            color_hover=COLOR_AZUL
        ).pack(
            side="left",
            padx=(0, 8)
        )

        crear_boton(
            fila_total_acciones,
            "Quitar producto",
            COLOR_ROJO,
            lambda: quitar_producto()
        ).pack(
            side="left"
        )

        crear_boton(
            fila_total_acciones,
            "Agregar pedido",
            COLOR_VERDE,
            lambda: guardar(),
            color_hover=COLOR_HOVER_VERDE
        ).pack(side="left", padx=5)

        crear_boton(
            fila_total_acciones,
            "Salir",
            COLOR_NARANJA,
            dialogo.destroy,
            color_hover=COLOR_HOVER_NARANJA
        ).pack(side="left", padx=5)

        etiqueta_total = tk.Label(
            fila_total_acciones,
            text="Total del pedido: $0.00",
            bg=COLOR_PANEL,
            fg=COLOR_AZUL,
            font=(FUENTE, 13, "bold")
        )
        etiqueta_total.pack(
            side="right",
            anchor="e",
            padx=(8, 0)
        )

        
        def refrescar_carrito():
            tabla_carrito.delete(
                *tabla_carrito.get_children()
            )

            total = Decimal("0.00")

            for id_prod, cantidad in carrito.items():
                producto = next(
                    (
                        p for p in productos
                        if int(p["id_producto"]) == int(id_prod)
                    ),
                    None
                )

                if producto is None:
                    continue

                costo = Decimal(
                    str(producto["precio_compra"])
                )

                subtotal = (
                    costo * cantidad
                ).quantize(
                    Decimal("0.01")
                )

                total += subtotal

                tabla_carrito.insert(
                    "",
                    "end",
                    iid=str(id_prod),
                    values=(
                        producto["nombre"],
                        cantidad,
                        f"${costo:,.2f}",
                        f"${subtotal:,.2f}"
                    )
                )

            etiqueta_total.config(
                text=f"Total del pedido: ${total:,.2f}"
            )

        # ====================================================
        # CARGAR DATOS DEL PEDIDO EXISTENTE
        # ====================================================
        if id_pedido is not None:
            proveedor_original = next(
                (
                    k for k, v in proveedor_map.items()
                    if int(v["id_proveedor"])
                    == int(pedido_original["id_proveedor"])
                ),
                None
            )

            if proveedor_original is not None:
                combo_proveedor.set(
                    proveedor_original
                )

            else:
                messagebox.showwarning(
                    "Proveedor inactivo",
                    "El proveedor anterior está inactivo. "
                    "Selecciona uno activo para guardar el pedido.",
                    parent=dialogo
                )

                combo_proveedor.current(0)

            detalles_originales = obtener_detalles_pedido(
                id_pedido
            )

            productos_inactivos = [
                detalle
                for detalle in detalles_originales
                if not any(
                    int(p["id_producto"])
                    == int(detalle["id_producto"])
                    for p in productos
                )
            ]

            if productos_inactivos:
                nombres = ", ".join(
                    d["nombre"] for d in productos_inactivos
                )

                messagebox.showwarning(
                    "Producto inactivo",
                    "No se puede modificar este pedido porque contiene "
                    f"productos inactivos: {nombres}. Activa esos productos "
                    "o gestiona el pedido desde la base de datos.",
                    parent=dialogo
                )

                dialogo.destroy()
                return

            for detalle in detalles_originales:
                carrito[int(detalle["id_producto"])] = int(
                    detalle["cantidad"]
                )

        elif proveedores:
            combo_proveedor.current(0)

        # ====================================================
        # AGREGAR PRODUCTO
        # ====================================================
        def agregar_producto():
            producto = producto_map.get(
                combo_producto.get().strip()
            )

            if producto is None:
                messagebox.showwarning(
                    "Producto",
                    "Selecciona un producto de la lista.",
                    parent=dialogo
                )
                combo_producto.focus_set()
                return

            texto_cantidad = entrada_cantidad.get().strip()

            try:
                cantidad = int(texto_cantidad)

                if cantidad <= 0:
                    raise ValueError

            except ValueError:
                messagebox.showerror(
                    "Cantidad",
                    "Escribe una cantidad entera mayor que cero.",
                    parent=dialogo
                )
                entrada_cantidad.focus_set()
                entrada_cantidad.selection_range(
                    0,
                    tk.END
                )
                return

            indice_proveedor_actual = combo_proveedor.current()

            if (
                indice_proveedor_actual < 0
                or indice_proveedor_actual >= len(proveedores)
            ):
                messagebox.showwarning(
                    "Proveedor",
                    "Selecciona primero un proveedor para el pedido.",
                    parent=dialogo
                )
                combo_proveedor.focus_set()
                return

            proveedor_actual = proveedores[
                indice_proveedor_actual
            ]

            if (
                producto.get("id_proveedor") is not None
                and int(producto["id_proveedor"])
                != int(proveedor_actual["id_proveedor"])
            ):
                messagebox.showwarning(
                    "Proveedor del producto",
                    f"El producto '{producto['nombre']}' está asignado "
                    "a otro proveedor. Selecciona el proveedor correspondiente "
                    "o modifica el proveedor asignado al producto en el módulo "
                    "de inventario.",
                    parent=dialogo
                )
                return

            id_prod = int(
                producto["id_producto"]
            )

            # Se conserva el comportamiento original:
            # la cantidad escrita reemplaza la cantidad anterior.
            carrito[id_prod] = cantidad

            refrescar_carrito()

            entrada_cantidad.focus_set()
            entrada_cantidad.selection_range(
                0,
                tk.END
            )

        # ====================================================
        # QUITAR PRODUCTO
        # ====================================================
        def quitar_producto():
            seleccion = tabla_carrito.selection()

            if seleccion:
                carrito.pop(
                    int(seleccion[0]),
                    None
                )
                refrescar_carrito()

            else:
                messagebox.showwarning(
                    "Producto",
                    "Selecciona un producto del pedido para quitarlo.",
                    parent=dialogo
                )

        
        # ====================================================
        # GUARDAR PEDIDO
        # ====================================================
        def guardar():
            indice_proveedor = combo_proveedor.current()

            if (
                indice_proveedor < 0
                or indice_proveedor >= len(proveedores)
            ):
                messagebox.showwarning(
                    "Proveedor",
                    "Selecciona un proveedor activo de la lista "
                    "antes de guardar el pedido.",
                    parent=dialogo
                )
                combo_proveedor.focus_set()
                return

            proveedor = proveedores[indice_proveedor]

            if not carrito:
                messagebox.showwarning(
                    "Pedido",
                    "Agrega al menos un producto.",
                    parent=dialogo
                )
                return

            try:
                id_guardado = guardar_pedido(
                    proveedor["id_proveedor"],
                    responsable_id(),
                    [
                        {
                            "id_producto": id_prod,
                            "cantidad": cantidad
                        }
                        for id_prod, cantidad in carrito.items()
                    ],
                    id_pedido
                )

                dialogo.destroy()
                actualizar_tablas()

                messagebox.showinfo(
                    "Pedido guardado",
                    f"El pedido #{id_guardado} se guardó correctamente.",
                    parent=ventana
                )

            except Exception as error:
                messagebox.showerror(
                    "No se pudo guardar",
                    str(error),
                    parent=dialogo
                )
    
    # --------------------------------------------------------
    # REGISTRAR RECEPCIÓN DE UN PEDIDO - INTERFAZ MEJORADA
    # --------------------------------------------------------
    def recibir_pedido():
        id_pedido = pedido_seleccionado(tabla_pendientes)

        if id_pedido is None:
            return

        try:
            detalles = obtener_detalles_pedido(id_pedido)

        except Exception as error:
            messagebox.showerror(
                "Base de datos",
                str(error),
                parent=ventana
            )
            return

        if not detalles:
            messagebox.showwarning(
                "Pedido",
                "Este pedido no tiene productos registrados.",
                parent=ventana
            )
            return

        # ====================================================
        # VENTANA Y CENTRADO
        # ====================================================
        dialogo = tk.Toplevel(ventana)
        dialogo.title(f"Recepción del pedido #{id_pedido}")
        dialogo.geometry("850x650")
        dialogo.minsize(680, 480)
        dialogo.configure(bg=COLOR_FONDO)
        registrar_ventana_tema(dialogo)
        dialogo.transient(ventana)
        dialogo.grab_set()

        dialogo.update_idletasks()

        ancho = 850
        alto = 650

        x = ventana.winfo_rootx() + (
            ventana.winfo_width() - ancho
        ) // 2

        y = ventana.winfo_rooty() + (
            ventana.winfo_height() - alto
        ) // 2

        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")

        # ====================================================
        # ENCABEZADO AZUL Y LÍNEA NARANJA
        # ====================================================
        encabezado_recepcion = tk.Frame(
            dialogo,
            bg=COLOR_AZUL,
            padx=24,
            pady=16
        )
        encabezado_recepcion.pack(fill="x")

        tk.Label(
            encabezado_recepcion,
            text="PAPELERÍA LUNA / PEDIDOS",
            bg=COLOR_AZUL,
            fg=COLOR_NARANJA,
            font=(FUENTE, 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            encabezado_recepcion,
            text="Recepción de pedido",
            bg=COLOR_AZUL,
            fg="#FFFFFF",
            font=(FUENTE, 20, "bold")
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            encabezado_recepcion,
            text=f"Registro de mercancía del pedido #{id_pedido}",
            bg=COLOR_AZUL,
            fg="#DBEAFE",
            font=(FUENTE, 9)
        ).pack(anchor="w", pady=(4, 0))

        tk.Frame(
            dialogo,
            bg=COLOR_NARANJA,
            height=5
        ).pack(fill="x")

        # ====================================================
        # CONTENIDO GENERAL
        # ====================================================
        contenido = tk.Frame(
            dialogo,
            bg=COLOR_FONDO,
            padx=18,
            pady=14
        )
        contenido.pack(fill="both", expand=True)

        tarjeta = crear_panel(
            contenido,
            padx=16,
            pady=13
        )
        tarjeta.pack(fill="both", expand=True)

        # ====================================================
        # TÍTULO E INDICACIONES
        # ====================================================
        fila_titulo = tk.Frame(
            tarjeta,
            bg=COLOR_PANEL
        )
        fila_titulo.pack(fill="x", pady=(0, 5))

        tk.Label(
            fila_titulo,
            text=f"Pedido #{id_pedido}",
            bg=COLOR_PANEL,
            fg=COLOR_AZUL,
            font=(FUENTE, 13, "bold")
        ).pack(side="left")

        productos_pendientes = sum(
            1 for detalle in detalles
            if (
                int(detalle["cantidad"])
                - int(detalle["cantidad_recibida"])
            ) > 0
        )

        tk.Label(
            fila_titulo,
            text=f"{productos_pendientes} producto(s) pendiente(s)",
            bg=COLOR_PANEL,
            fg=COLOR_SUAVE,
            font=(FUENTE, 9)
        ).pack(side="right")

        tk.Label(
            tarjeta,
            text=(
                "Captura las unidades que llegaron en esta entrega. "
                "Puedes registrar una recepción parcial. "
                "Escribe 0 si un producto no llegó."
            ),
            bg=COLOR_PANEL,
            fg=COLOR_SUAVE,
            font=(FUENTE, 9),
            wraplength=740,
            justify="left"
        ).pack(anchor="w", pady=(2, 12))

        # ====================================================
        # ESTILOS DE LA TABLA Y LOS CAMPOS
        # ====================================================
        estilo_recepcion = ttk.Style(dialogo)

        estilo_recepcion.configure(
            "Recepcion.Treeview",
            rowheight=34,
            font=(FUENTE, 9),
            background=COLOR_PANEL,
            fieldbackground=COLOR_PANEL,
            foreground=COLOR_TEXTO,
            borderwidth=0
        )

        estilo_recepcion.configure(
            "Recepcion.Treeview.Heading",
            font=(FUENTE, 9, "bold"),
            background=COLOR_ENCABEZADO_TABLA,
            foreground=COLOR_AZUL,
            padding=(8, 9),
            relief="flat"
        )

        estilo_recepcion.map(
            "Recepcion.Treeview",
            background=[("selected", COLOR_SELECCION)],
            foreground=[("selected", COLOR_AZUL)]
        )

        estilo_recepcion.configure(
            "Recepcion.TEntry",
            padding=(6, 5),
            font=(FUENTE, 10)
        )

        # ====================================================
        # ENCABEZADOS DE LAS COLUMNAS
        # ====================================================
        marco_tabla = tk.Frame(
            tarjeta,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        marco_tabla.pack(fill="both", expand=True)

        encabezados_tabla = tk.Frame(
            marco_tabla,
            bg=COLOR_ENCABEZADO_TABLA
        )
        encabezados_tabla.pack(fill="x")

        encabezados_tabla.grid_columnconfigure(
            0, weight=4, minsize=150
        )
        encabezados_tabla.grid_columnconfigure(
            1, weight=1, minsize=75
        )
        encabezados_tabla.grid_columnconfigure(
            2, weight=1, minsize=75
        )
        encabezados_tabla.grid_columnconfigure(
            3, weight=1, minsize=75
        )
        encabezados_tabla.grid_columnconfigure(
            4, weight=1, minsize=100
        )

        for columna, titulo in enumerate((
            "Producto",
            "Solicitadas",
            "Recibidas",
            "Pendientes",
            "Recibir ahora"
        )):
            tk.Label(
                encabezados_tabla,
                text=titulo,
                bg=COLOR_ENCABEZADO_TABLA,
                fg=COLOR_AZUL,
                font=(FUENTE, 8, "bold"),
                padx=5,
                pady=10,
                anchor="w" if columna == 0 else "center"
            ).grid(
                row=0,
                column=columna,
                sticky="ew"
            )

        # ====================================================
        # TABLA DESPLAZABLE DE PRODUCTOS
        # ====================================================
        contenedor_filas = tk.Frame(
            marco_tabla,
            bg=COLOR_PANEL
        )
        contenedor_filas.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            contenedor_filas,
            bg=COLOR_PANEL,
            highlightthickness=0,
            bd=0
        )

        scroll = ttk.Scrollbar(
            contenedor_filas,
            orient="vertical",
            command=canvas.yview
        )

        formulario = tk.Frame(
            canvas,
            bg=COLOR_PANEL
        )

        ventana_canvas = canvas.create_window(
            (0, 0),
            window=formulario,
            anchor="nw"
        )

        formulario.bind(
            "<Configure>",
            lambda evento: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.bind(
            "<Configure>",
            lambda evento: canvas.itemconfigure(
                ventana_canvas,
                width=evento.width
            )
        )

        canvas.configure(
            yscrollcommand=scroll.set
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.pack(
            side="right",
            fill="y"
        )

        # ====================================================
        # REGISTRO DE CAMPOS DE RECEPCIÓN
        # ====================================================
        entradas = {}

        total_solicitado = sum(
            int(detalle["cantidad"])
            for detalle in detalles
        )

        total_recibido_anterior = sum(
            int(detalle["cantidad_recibida"])
            for detalle in detalles
        )

        total_pendiente = sum(
            max(
                int(detalle["cantidad"])
                - int(detalle["cantidad_recibida"]),
                0
            )
            for detalle in detalles
        )

        if not productos_pendientes:
            tk.Label(
                formulario,
                text="Este pedido ya no tiene unidades pendientes.",
                bg=COLOR_PANEL,
                fg=COLOR_VERDE,
                font=(FUENTE, 10, "bold"),
                padx=12,
                pady=18
            ).pack(anchor="w")

        else:
            formulario.grid_columnconfigure(
                0, weight=4, minsize=150
            )
            formulario.grid_columnconfigure(
                1, weight=1, minsize=75
            )
            formulario.grid_columnconfigure(
                2, weight=1, minsize=75
            )
            formulario.grid_columnconfigure(
                3, weight=1, minsize=75
            )
            formulario.grid_columnconfigure(
                4, weight=1, minsize=100
            )

            fila_actual = 0

            for detalle in detalles:
                solicitados = int(detalle["cantidad"])
                recibidos = int(detalle["cantidad_recibida"])
                faltan = max(solicitados - recibidos, 0)

                # No mostrar productos que ya se recibieron por completo.
                if faltan <= 0:
                    continue

                color_fila = (
                    COLOR_PANEL
                    if fila_actual % 2 == 0
                    else "#F8FAFC"
                )

                linea = tk.Frame(
                    formulario,
                    bg=color_fila,
                    highlightbackground=COLOR_BORDE,
                    highlightthickness=1
                )
                linea.grid(
                    row=fila_actual,
                    column=0,
                    columnspan=5,
                    sticky="ew"
                )

                linea.grid_columnconfigure(
                    0, weight=4, minsize=150
                )
                linea.grid_columnconfigure(
                    1, weight=1, minsize=75
                )
                linea.grid_columnconfigure(
                    2, weight=1, minsize=75
                )
                linea.grid_columnconfigure(
                    3, weight=1, minsize=75
                )
                linea.grid_columnconfigure(
                    4, weight=1, minsize=100
                )

                tk.Label(
                    linea,
                    text=detalle["nombre"],
                    bg=color_fila,
                    fg=COLOR_TEXTO,
                    font=(FUENTE, 9, "bold"),
                    anchor="w",
                    justify="left",
                    wraplength=210,
                    padx=9,
                    pady=11
                ).grid(
                    row=0,
                    column=0,
                    sticky="ew"
                )

                tk.Label(
                    linea,
                    text=str(solicitados),
                    bg=color_fila,
                    fg=COLOR_TEXTO,
                    font=(FUENTE, 9),
                    padx=3
                ).grid(
                    row=0,
                    column=1,
                    sticky="ew"
                )

                tk.Label(
                    linea,
                    text=str(recibidos),
                    bg=color_fila,
                    fg=COLOR_VERDE,
                    font=(FUENTE, 9, "bold"),
                    padx=3
                ).grid(
                    row=0,
                    column=2,
                    sticky="ew"
                )

                tk.Label(
                    linea,
                    text=str(faltan),
                    bg=color_fila,
                    fg=COLOR_NARANJA,
                    font=(FUENTE, 9, "bold"),
                    padx=3
                ).grid(
                    row=0,
                    column=3,
                    sticky="ew"
                )

                entrada = ttk.Entry(
                    linea,
                    width=8,
                    justify="center",
                    style="Recepcion.TEntry"
                )

                # Mantener el comportamiento original:
                # proponer todas las unidades pendientes.
                entrada.insert(0, str(faltan))
                entrada.grid(
                    row=0,
                    column=4,
                    sticky="ew",
                    padx=8,
                    pady=7
                )

                entradas[int(detalle["id_producto"])] = entrada

                fila_actual += 1

        # ====================================================
        # RESUMEN VISUAL DE LA RECEPCIÓN
        # ====================================================
        resumen = tk.Frame(
            tarjeta,
            bg=COLOR_PANEL
        )
        resumen.pack(fill="x", pady=(12, 0))

        def crear_dato_recepcion(parent, titulo, valor, color):
            bloque = tk.Frame(
                parent,
                bg=COLOR_PANEL
            )
            bloque.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 8)
            )

            tk.Label(
                bloque,
                text=titulo.upper(),
                bg=COLOR_PANEL,
                fg=COLOR_SUAVE,
                font=(FUENTE, 8, "bold")
            ).pack(anchor="w")

            tk.Label(
                bloque,
                text=str(valor),
                bg=COLOR_PANEL,
                fg=color,
                font=(FUENTE, 15, "bold")
            ).pack(anchor="w", pady=(3, 0))

        crear_dato_recepcion(
            resumen,
            "Solicitadas",
            total_solicitado,
            COLOR_AZUL
        )

        crear_dato_recepcion(
            resumen,
            "Recibidas anteriormente",
            total_recibido_anterior,
            COLOR_VERDE
        )

        resumen_actual = tk.Frame(
            resumen,
            bg=COLOR_PANEL
        )
        resumen_actual.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Label(
            resumen_actual,
            text="PENDIENTES ANTES DE ESTA ENTREGA",
            bg=COLOR_PANEL,
            fg=COLOR_SUAVE,
            font=(FUENTE, 8, "bold")
        ).pack(anchor="w")

        tk.Label(
            resumen_actual,
            text=str(total_pendiente),
            bg=COLOR_PANEL,
            fg=COLOR_NARANJA if total_pendiente else COLOR_VERDE,
            font=(FUENTE, 15, "bold")
        ).pack(anchor="w", pady=(3, 0))

        # ====================================================
        # PIE Y BOTONES
        # ====================================================
        pie_recepcion = tk.Frame(
            contenido,
            bg=COLOR_FONDO
        )
        pie_recepcion.pack(
            fill="x",
            pady=(12, 0)
        )

        tk.Label(
            pie_recepcion,
            text="Verifica las cantidades antes de confirmar.",
            bg=COLOR_FONDO,
            fg=COLOR_SUAVE,
            font=(FUENTE, 9)
        ).pack(side="left")

        # ====================================================
        # CONFIRMAR RECEPCIÓN
        # ====================================================
        def confirmar_recepcion():
            try:
                recepciones = {}

                for id_prod, entrada in entradas.items():
                    texto = entrada.get().strip()

                    if not texto:
                        raise ValueError(
                            "Completa las cantidades o escribe 0."
                        )

                    cantidad = int(texto)

                    if cantidad < 0:
                        raise ValueError(
                            "Las cantidades no pueden ser negativas."
                        )

                    recepciones[id_prod] = cantidad

                if not any(recepciones.values()):
                    raise ValueError(
                        "Registra al menos una cantidad mayor que cero."
                    )

                resultado = registrar_recepcion(
                    id_pedido,
                    responsable_id(),
                    recepciones
                )

                dialogo.destroy()
                actualizar_tablas()

                messagebox.showinfo(
                    "Recepción registrada",
                    resultado,
                    parent=ventana
                )

            except Exception as error:
                messagebox.showerror(
                    "Error en recepción",
                    str(error),
                    parent=dialogo
                )

        crear_boton(
            pie_recepcion,
            "Confirmar recepción",
            COLOR_VERDE,
            confirmar_recepcion,
            color_hover=COLOR_HOVER_VERDE
        ).pack(side="right", padx=(8, 0))

        crear_boton(
            pie_recepcion,
            "Cerrar",
            COLOR_NARANJA,
            dialogo.destroy,
            color_hover=COLOR_HOVER_NARANJA
        ).pack(side="right")

        # Permitir cerrar con Escape.
        dialogo.bind(
            "<Escape>",
            lambda evento: dialogo.destroy()
        )

    # --------------------------------------------------------
    # CANCELAR PEDIDO DESDE LA INTERFAZ
    # --------------------------------------------------------
    def cancelar_pedido_ui():
        id_pedido = pedido_seleccionado(tabla_pendientes)

        if id_pedido is None:
            return

        confirmar = messagebox.askyesno(
            "Cancelar pedido",
            f"¿Deseas cancelar el pedido #{id_pedido}?",
            parent=ventana
        )

        if not confirmar:
            return

        try:
            cancelar_pedido(id_pedido)
            actualizar_tablas()

            messagebox.showinfo(
                "Pedido cancelado",
                f"El pedido #{id_pedido} quedó cancelado.",
                parent=ventana
            )

        except Exception as error:
            messagebox.showerror(
                "No se pudo cancelar",
                str(error),
                parent=ventana
            )

    # --------------------------------------------------------
    # CONSULTAR DETALLES DESDE LAS TABLAS
    # --------------------------------------------------------
    def ver_detalle_pendiente():
        id_pedido = pedido_seleccionado(tabla_pendientes)

        if id_pedido is not None:
            mostrar_detalle(id_pedido)

    def ver_detalle_recibido():
        id_pedido = pedido_seleccionado(tabla_recibidos)

        if id_pedido is not None:
            mostrar_detalle(id_pedido)

    
    def ver_detalle_cancelado():
        id_pedido = pedido_seleccionado(tabla_cancelados)

        if id_pedido is not None:
            mostrar_detalle(id_pedido)

    # --------------------------------------------------------
    # DETECTAR PRODUCTOS CON STOCK BAJO
    # --------------------------------------------------------
    def detectar_stock():
        try:
            id_empleado = responsable_id()

            proveedores = obtener_proveedores_activos()
            productos = obtener_productos_activos()

            bajos = [
                producto
                for producto in productos
                if int(producto["cantidad_stock"])
                < int(producto["stock_minimo"])
            ]

            if not bajos:
                messagebox.showinfo(
                    "Reabastecimiento",
                    "No hay productos con stock bajo.",
                    parent=ventana
                )
                return

            if not proveedores:
                messagebox.showwarning(
                    "Proveedores",
                    "No hay proveedores activos para crear el pedido.",
                    parent=ventana
                )
                return

            selector = tk.Toplevel(ventana)
            selector.title("Proveedor para reabastecimiento")
            selector.geometry("560x330")
            selector.minsize(480, 300)
            selector.configure(bg=COLOR_FONDO)
            registrar_ventana_tema(selector)
            selector.transient(ventana)
            selector.grab_set()

            panel_selector = crear_panel(
                selector,
                padx=20,
                pady=18
            )
            panel_selector.pack(
                fill="both",
                expand=True,
                padx=14,
                pady=14
            )

            tk.Label(
                panel_selector,
                text="Reabastecimiento automático",
                bg=COLOR_PANEL,
                fg=COLOR_AZUL,
                font=(FUENTE, 15, "bold")
            ).pack(anchor="w")

            tk.Label(
                panel_selector,
                text=f"Se detectaron {len(bajos)} productos con stock bajo.",
                bg=COLOR_PANEL,
                fg=COLOR_NARANJA,
                font=(FUENTE, 10, "bold")
            ).pack(anchor="w", pady=(7, 10))

            tk.Label(
                panel_selector,
                text=(
                    "Selecciona el proveedor. Se incluirán los productos "
                    "activos con stock bajo asignados a ese proveedor, así como "
                    "los que todavía no tienen proveedor asignado. La cantidad "
                    "sugerida cubrirá lo necesario para alcanzar el stock mínimo."
                ),
                bg=COLOR_PANEL,
                fg=COLOR_TEXTO,
                wraplength=470,
                justify="left",
                font=(FUENTE, 9)
            ).pack(anchor="w")

            proveedor_map_local = {
                f"{p['id_proveedor']} - {p['nombre']}": p
                for p in proveedores
            }

            proveedor_auto_var = tk.StringVar(
                value=next(iter(proveedor_map_local), "")
            )

            combo_auto = ttk.Combobox(
                panel_selector,
                textvariable=proveedor_auto_var,
                values=list(proveedor_map_local),
                state="readonly"
            )
            combo_auto.pack(fill="x", pady=(13, 12))

            if proveedores:
                combo_auto.current(0)

            def confirmar_automatico():
                indice_proveedor = combo_auto.current()

                if (
                    indice_proveedor < 0
                    or indice_proveedor >= len(proveedores)
                ):
                    messagebox.showwarning(
                        "Proveedor",
                        "Selecciona un proveedor activo de la lista.",
                        parent=selector
                    )
                    combo_auto.focus_set()
                    return

                proveedor = proveedores[indice_proveedor]

                try:
                    id_pedido, cantidad_productos = (
                        generar_pedidos_automaticos(
                            id_empleado,
                            proveedor["id_proveedor"]
                        )
                    )

                    selector.destroy()
                    actualizar_tablas()

                    if id_pedido is None:
                        messagebox.showinfo(
                            "Reabastecimiento",
                            "No se creó un pedido nuevo para ese proveedor. "
                            "Comprueba que tenga productos activos asignados "
                            "con stock bajo, que no tengan otro pedido pendiente "
                            "y que las cantidades de reabastecimiento sean válidas.",
                            parent=ventana
                        )
                    else:
                        messagebox.showinfo(
                            "Reabastecimiento automático",
                            f"Se creó el pedido #{id_pedido} "
                            f"con {cantidad_productos} producto(s).",
                            parent=ventana
                        )

                except Exception as error:
                    messagebox.showerror(
                        "Reabastecimiento",
                        str(error),
                        parent=selector
                    )

            crear_boton(
                panel_selector,
                "Crear pedido automático",
                COLOR_NARANJA,
                confirmar_automatico
            ).pack(anchor="e", pady=(4, 0))

        except Exception as error:
            messagebox.showerror(
                "Error de reabastecimiento",
                f"No se pudo detectar el stock bajo:\n{error}",
                parent=ventana
            )

    # --------------------------------------------------------
    # MODIFICAR PEDIDO SELECCIONADO
    # --------------------------------------------------------
    def modificar_pedido_seleccionado():
        id_pedido = pedido_seleccionado(tabla_pendientes)

        if id_pedido is not None:
            dialogo_pedido(id_pedido)

    # --------------------------------------------------------
    # BOTONES DE GESTIÓN DE PEDIDOS
    # --------------------------------------------------------
    crear_boton(
        fila_acciones_pedido,
        "Nuevo pedido",
        COLOR_AZUL_SECUNDARIO,
        lambda: dialogo_pedido()
    ).pack(side="left", padx=(0, 6), pady=3)

    crear_boton(
        fila_acciones_pedido,
        "Modificar",
        COLOR_NARANJA,
        modificar_pedido_seleccionado
    ).pack(side="left", padx=(0, 6), pady=3)

    
    crear_boton(
        fila_acciones_pedido,
        "Ver detalle",
        COLOR_AZUL_SECUNDARIO,
        ver_detalle_pendiente
    ).pack(side="left", padx=(0, 14), pady=3)


    crear_boton(
            fila_acciones_pedido,
            "Cancelar",
            COLOR_ROJO,
            cancelar_pedido_ui
    ).pack(side="left", padx=(0, 6), pady=3)

    # --------------------------------------------------------
    # BOTONES DE RECEPCIÓN E INVENTARIO
    # --------------------------------------------------------
    crear_boton(
        fila_acciones_inventario,
        "Registrar recepción",
        COLOR_VERDE,
        recibir_pedido
    ).pack(side="left", padx=(0, 6), pady=3)

    crear_boton(
        fila_acciones_inventario,
        "Reabastecer stock",
        COLOR_AZUL_SECUNDARIO,
        detectar_stock
    ).pack(side="left", padx=(0, 6), pady=3)

    crear_boton(
        fila_acciones_inventario,
        "Detalle recibido",
        COLOR_NARANJA,
        ver_detalle_recibido
    ).pack(side="left", padx=(0, 6), pady=3)
    
    crear_boton(
        fila_acciones_inventario,
        "Detalle cancelado",
        COLOR_AZUL_SECUNDARIO,
        ver_detalle_cancelado
    ).pack(side="left", padx=(0, 6), pady=3)

    boton_salir = crear_boton(
        fila_acciones_inventario,
        "Salir",
        COLOR_ROJO,
        ventana.destroy,
        color_hover=COLOR_HOVER_ROJO
    )
    boton_salir.pack(
        side="left",
        padx=5,
        pady=5
    )
    
    # --------------------------------------------------------
    # CARGA INICIAL
    # --------------------------------------------------------
    actualizar_tablas()

    if not raiz:
        ventana.mainloop()
