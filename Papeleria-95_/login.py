
import tkinter as tk
from tkinter import messagebox
import mysql.connector
import hashlib
import hmac
import os


# ============================================================
# CONFIGURACIÓN - PAPELERÍA LUNA
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "Papeleria_Luna"
}

COLOR_FONDO = "#f1f5f9"
COLOR_PANEL = "#ffffff"
COLOR_AZUL = "#172554"
COLOR_AZUL_SECUNDARIO = "#1e3a5f"
COLOR_NARANJA = "#f59e0b"
COLOR_NARANJA_HOVER = "#d97706"
COLOR_TEXTO = "#1e293b"
COLOR_TEXTO_SUAVE = "#64748b"
COLOR_BORDE = "#dbe3ed"
COLOR_ROJO = "#ef4444"

FUENTE = "Arial"

# Empleados.estado = 0 -> activo
# usuarios.estado = 1 -> activo
EMPLEADO_ACTIVO = 0
USUARIO_ACTIVO = 1


# ============================================================
# CONEXIÓN A LA BASE DE DATOS
# ============================================================

def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# CONTRASEÑAS SEGURAS
# ============================================================

def generar_hash_contrasena(contrasena):
    """Genera un hash seguro mediante PBKDF2."""

    salt = os.urandom(16)

    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena.encode("utf-8"),
        salt,
        600000
    )

    return (
        "pbkdf2_sha256$600000$"
        + salt.hex()
        + "$"
        + hash_bytes.hex()
    )


def verificar_contrasena(contrasena_ingresada, contrasena_guardada):
    """Comprueba una contraseña almacenada mediante PBKDF2."""

    try:
        algoritmo, iteraciones, salt_hex, hash_guardado = (
            contrasena_guardada.split("$")
        )

        if algoritmo != "pbkdf2_sha256":
            return False

        salt = bytes.fromhex(salt_hex)

        hash_calculado = hashlib.pbkdf2_hmac(
            "sha256",
            contrasena_ingresada.encode("utf-8"),
            salt,
            int(iteraciones)
        ).hex()

        return hmac.compare_digest(
            hash_calculado,
            hash_guardado
        )

    except (ValueError, TypeError, AttributeError):
        return False


# ============================================================
# VALIDAR USUARIO
# ============================================================

def validar_usuario(identificacion, contrasena):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        consulta = """
            SELECT
                u.id_usuario,
                u.id_empleado,
                u.contrasena,
                u.rango,
                u.modo_CO,
                u.estado AS estado_usuario,

                e.identificacion,
                e.nombre,
                e.apellidos,
                e.puesto,
                e.estado AS estado_empleado

            FROM usuarios AS u

            INNER JOIN Empleados AS e
                ON u.id_empleado = e.id_empleado

            WHERE e.identificacion = %s
              AND u.estado = %s
              AND e.estado = %s

            LIMIT 1
        """

        cursor.execute(
            consulta,
            (
                identificacion,
                USUARIO_ACTIVO,
                EMPLEADO_ACTIVO
            )
        )

        usuario = cursor.fetchone()

        if not usuario:
            return None

        if not verificar_contrasena(
            contrasena,
            usuario["contrasena"]
        ):
            return None

        return {
            "id_usuario": usuario["id_usuario"],
            "id_empleado": usuario["id_empleado"],
            "identificacion": usuario["identificacion"],
            "nombre": usuario["nombre"],
            "apellidos": usuario["apellidos"],
            "puesto": usuario["puesto"],
            "rango": usuario["rango"],
            "modo_CO": usuario["modo_CO"]
        }

    except mysql.connector.Error as error:
        messagebox.showerror(
            "Error de conexión",
            "No fue posible validar el usuario.\n\n"
            f"Detalle: {error}"
        )
        return None

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ============================================================
# EFECTO HOVER
# ============================================================

def boton_hover(boton, normal, hover):
    boton.bind(
        "<Enter>",
        lambda evento: boton.config(bg=hover)
    )

    boton.bind(
        "<Leave>",
        lambda evento: boton.config(bg=normal)
    )


# ============================================================
# INICIO DE SESIÓN
# ============================================================

def iniciar_sesion():

    ventana = tk.Tk()
    ventana.title("Papelería Luna | Inicio de sesión")
    ventana.configure(bg=COLOR_FONDO)
    ventana.resizable(False, False)

    ancho = 460
    alto = 630

    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    x = (pantalla_ancho - ancho) // 2
    y = (pantalla_alto - alto) // 2

    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    # --------------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------------

    encabezado = tk.Frame(
        ventana,
        bg=COLOR_AZUL,
        height=155
    )

    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA",
        bg=COLOR_AZUL,
        fg=COLOR_NARANJA,
        font=(FUENTE, 11, "bold")
    ).pack(pady=(22, 5))

    tk.Label(
        encabezado,
        text="Inicio de sesión",
        bg=COLOR_AZUL,
        fg=COLOR_PANEL,
        font=(FUENTE, 24, "bold")
    ).pack()

    tk.Label(
        encabezado,
        text="Sistema de gestión y administración",
        bg=COLOR_AZUL,
        fg="#dbe3ed",
        font=(FUENTE, 10)
    ).pack(pady=(5, 0))

    tk.Frame(
        ventana,
        bg=COLOR_NARANJA,
        height=5
    ).pack(fill="x")

    # --------------------------------------------------------
    # FORMULARIO
    # --------------------------------------------------------

    panel = tk.Frame(
        ventana,
        bg=COLOR_PANEL,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )

    panel.pack(
        fill="both",
        expand=True,
        padx=35,
        pady=20
    )

    tk.Label(
        panel,
        text="Bienvenido",
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
        font=(FUENTE, 19, "bold")
    ).pack(anchor="w", padx=25, pady=(18, 4))

    tk.Label(
        panel,
        text="Ingresa tus credenciales para continuar.",
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
        font=(FUENTE, 10)
    ).pack(anchor="w", padx=25, pady=(0, 16))

    # Identificación
    tk.Label(
        panel,
        text="Identificación del empleado",
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        font=(FUENTE, 10, "bold")
    ).pack(anchor="w", padx=25, pady=(0, 6))

    entrada_identificacion = tk.Entry(
        panel,
        font=(FUENTE, 11),
        bg="#ffffff",
        fg=COLOR_TEXTO,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=COLOR_BORDE,
        highlightcolor=COLOR_NARANJA
    )

    entrada_identificacion.pack(
        fill="x",
        padx=25,
        ipady=8
    )

    # Contraseña
    tk.Label(
        panel,
        text="Contraseña",
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        font=(FUENTE, 10, "bold")
    ).pack(anchor="w", padx=25, pady=(14, 6))

    entrada_contrasena = tk.Entry(
        panel,
        font=(FUENTE, 11),
        show="*",
        bg="#ffffff",
        fg=COLOR_TEXTO,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=COLOR_BORDE,
        highlightcolor=COLOR_NARANJA
    )

    entrada_contrasena.pack(
        fill="x",
        padx=25,
        ipady=8
    )

    # --------------------------------------------------------
    # ACCIÓN DE INICIO DE SESIÓN
    # --------------------------------------------------------

    def acceder(evento=None):

        identificacion = entrada_identificacion.get().strip()
        contrasena = entrada_contrasena.get()

        if not identificacion or not contrasena:
            messagebox.showwarning(
                "Campos obligatorios",
                "Escribe tu identificación y contraseña.",
                parent=ventana
            )
            return

        usuario = validar_usuario(
            identificacion,
            contrasena
        )

        if usuario is None:
            entrada_contrasena.delete(0, tk.END)
            entrada_contrasena.focus_set()

            messagebox.showerror(
                "Acceso denegado",
                "Las credenciales son incorrectas, "
                "la cuenta está inactiva o el empleado "
                "no está habilitado.",
                parent=ventana
            )
            return

        ventana.destroy()

        from menu import iniciar_menu
        iniciar_menu(usuario)

    # --------------------------------------------------------
    # ABRIR FORMULARIO PARA CREAR CUENTA
    # --------------------------------------------------------

    def abrir_creacion_cuenta():

        # Importación dentro de la función para evitar
        # problemas de importación circular.
        from crear_cuenta import abrir_crear_cuenta

        abrir_crear_cuenta(ventana)

    # --------------------------------------------------------
    # BOTÓN INICIAR SESIÓN
    # --------------------------------------------------------

    boton_ingresar = tk.Button(
        panel,
        text="Iniciar sesión",
        command=acceder,
        bg=COLOR_AZUL,
        fg=COLOR_PANEL,
        activebackground=COLOR_AZUL_SECUNDARIO,
        activeforeground=COLOR_PANEL,
        font=(FUENTE, 11, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        pady=10
    )

    boton_ingresar.pack(
        fill="x",
        padx=25,
        pady=(20, 8)
    )

    boton_hover(
        boton_ingresar,
        COLOR_AZUL,
        COLOR_AZUL_SECUNDARIO
    )

    # --------------------------------------------------------
    # BOTÓN CREAR CUENTA
    # --------------------------------------------------------

    boton_crear_cuenta = tk.Button(
        panel,
        text="Crear cuenta",
        command=abrir_creacion_cuenta,
        bg=COLOR_NARANJA,
        fg=COLOR_AZUL,
        activebackground=COLOR_NARANJA_HOVER,
        activeforeground=COLOR_AZUL,
        font=(FUENTE, 11, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        pady=10
    )

    boton_crear_cuenta.pack(
        fill="x",
        padx=25,
        pady=(0, 12)
    )

    boton_hover(
        boton_crear_cuenta,
        COLOR_NARANJA,
        COLOR_NARANJA_HOVER
    )

    tk.Label(
        panel,
        text="Acceso exclusivo para personal autorizado",
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
        font=(FUENTE, 9)
    ).pack(pady=(0, 12))

    # Permite iniciar sesión con Enter.
    ventana.bind("<Return>", acceder)

    entrada_identificacion.focus_set()

    ventana.mainloop()
