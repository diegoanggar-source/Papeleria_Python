
# tema.py
import mysql.connector


# ============================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "Papeleria_Luna",
    "connection_timeout": 10
}


# ============================================================
# ESTADO DEL TEMA
# ============================================================

TEMA_ACTUAL = "claro"
ID_USUARIO_ACTUAL = None
OBSERVADORES = []


# ============================================================
# PALETA DE COLORES
# ============================================================

TEMAS = {
    "claro": {
        "FONDO": "#F1F5F9",
        "PANEL": "#FFFFFF",
        "AZUL": "#172554",
        "AZUL_SECUNDARIO": "#1E3A5F",
        "NARANJA": "#F59E0B",
        "NARANJA_HOVER": "#D97706",
        "TEXTO": "#1E293B",
        "TEXTO_SUAVE": "#64748B",
        "BORDE": "#DBE3ED",
        "ROJO": "#EF4444",
        "ROJO_HOVER": "#DC2626",
        "ENTRADA": "#FFFFFF",
        "SELECCION": "#DBEAFE",
    },

    "oscuro": {
        "FONDO": "#111827",
        "PANEL": "#1F2937",
        "AZUL": "#030712",
        "AZUL_SECUNDARIO": "#374151",
        "NARANJA": "#F59E0B",
        "NARANJA_HOVER": "#D97706",
        "TEXTO": "#F9FAFB",
        "TEXTO_SUAVE": "#9CA3AF",
        "BORDE": "#374151",
        "ROJO": "#DC2626",
        "ROJO_HOVER": "#B91C1C",
        "ENTRADA": "#111827",
        "SELECCION": "#374151",
    }
}


# ============================================================
# CONEXIÓN A MYSQL
# ============================================================

def conectar_bd():
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# REGISTRAR EL USUARIO DE LA SESIÓN
# ============================================================

def establecer_usuario(id_usuario):
    """
    Establece el usuario de la sesión y carga su preferencia.

    usuarios.modo_CO:
        0 = claro
        1 = oscuro
    """
    global ID_USUARIO_ACTUAL, TEMA_ACTUAL

    try:
        ID_USUARIO_ACTUAL = int(id_usuario)
    except (TypeError, ValueError):
        ID_USUARIO_ACTUAL = None
        TEMA_ACTUAL = "claro"
        return TEMA_ACTUAL

    TEMA_ACTUAL = cargar_tema(ID_USUARIO_ACTUAL)

    return TEMA_ACTUAL


# ============================================================
# CARGAR LA PREFERENCIA DESDE MYSQL
# ============================================================

def cargar_tema(id_usuario=None):
    global TEMA_ACTUAL

    if id_usuario is None:
        id_usuario = ID_USUARIO_ACTUAL

    # Si no hay usuario, utilizar el tema claro.
    if id_usuario is None:
        TEMA_ACTUAL = "claro"
        return TEMA_ACTUAL

    conexion = None
    cursor = None

    # Valor predeterminado para este usuario.
    tema_cargado = "claro"

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT modo_CO
            FROM usuarios
            WHERE id_usuario = %s
            """,
            (id_usuario,)
        )

        resultado = cursor.fetchone()

        if resultado is not None:
            tema_cargado = (
                "oscuro"
                if resultado[0] is not None
                and int(resultado[0]) == 1
                else "claro"
            )

        else:
            print(
                "No se encontró la preferencia del usuario:",
                id_usuario
            )

    except (mysql.connector.Error, TypeError, ValueError) as error:
        print("Error al cargar el tema:", error)

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()

    # Actualizar el estado global con el resultado de esta consulta.
    TEMA_ACTUAL = tema_cargado

    return TEMA_ACTUAL


# ============================================================
# GUARDAR LA PREFERENCIA EN MYSQL
# ============================================================

def guardar_tema(tema, id_usuario=None):
    if tema not in TEMAS:
        print("El tema indicado no es válido.")
        return False

    if id_usuario is None:
        id_usuario = ID_USUARIO_ACTUAL

    if id_usuario is None:
        print("No se puede guardar el tema sin un usuario.")
        return False

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        valor_modo = 1 if tema == "oscuro" else 0

        cursor.execute(
            """
            UPDATE usuarios
            SET modo_CO = %s
            WHERE id_usuario = %s
            """,
            (valor_modo, id_usuario)
        )

        # rowcount puede ser 0 cuando el usuario ya tenía
        # guardado exactamente el mismo valor.
        if cursor.rowcount == 0:
            cursor.execute(
                """
                SELECT id_usuario
                FROM usuarios
                WHERE id_usuario = %s
                """,
                (id_usuario,)
            )

            if cursor.fetchone() is None:
                conexion.rollback()
                print(
                    "No se encontró el usuario para guardar el tema."
                )
                return False

        conexion.commit()
        return True

    except mysql.connector.Error as error:
        if conexion is not None:
            conexion.rollback()

        print("Error al guardar el tema:", error)
        return False

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ============================================================
# OBTENER EL TEMA ACTUAL Y SUS COLORES
# ============================================================

def obtener_tema_actual():
    return TEMA_ACTUAL


def obtener_colores(tema=None):
    if tema is None:
        tema = TEMA_ACTUAL

    return TEMAS.get(tema, TEMAS["claro"]).copy()


# ============================================================
# REGISTRAR Y ELIMINAR OBSERVADORES
# ============================================================

def registrar_observador(funcion):
    if funcion not in OBSERVADORES:
        OBSERVADORES.append(funcion)


def eliminar_observador(funcion):
    if funcion in OBSERVADORES:
        OBSERVADORES.remove(funcion)


# ============================================================
# CAMBIAR EL TEMA
# ============================================================

def cambiar_tema(nuevo_tema):
    global TEMA_ACTUAL

    if nuevo_tema not in TEMAS:
        print("El tema indicado no es válido.")
        return False

    if ID_USUARIO_ACTUAL is None:
        print("No hay un usuario activo para cambiar el tema.")
        return False

    # Guardar primero la preferencia del usuario.
    if not guardar_tema(nuevo_tema, ID_USUARIO_ACTUAL):
        return False

    # Actualizar el tema actual después de guardar correctamente.
    TEMA_ACTUAL = nuevo_tema

    # Notificar a los módulos que se hayan registrado.
    colores = obtener_colores(nuevo_tema)

    for funcion in OBSERVADORES.copy():
        try:
            funcion(colores.copy())
        except Exception as error:
            print(
                "Error al actualizar un módulo con el nuevo tema:",
                error
            )

    return True