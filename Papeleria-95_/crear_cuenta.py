
import tkinter as tk
from tkinter import messagebox
import mysql.connector
import hashlib
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

EMPLEADO_ACTIVO = 0
USUARIO_ACTIVO = 1

def determinar_rango(puesto):
    puesto = (puesto or "").strip().casefold()

    if puesto == "gerente":
        return "gerente"

    return "empleado"

# ============================================================
# CONEXIÓN A LA BASE DE DATOS
# ============================================================

def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# CONTRASEÑAS SEGURAS
# ============================================================

def generar_hash_contrasena(contrasena):
    """Guarda un hash PBKDF2, nunca la contraseña original."""

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
# FORMULARIO DE CREACIÓN DE CUENTA
# ============================================================

def abrir_crear_cuenta(ventana_padre=None):

    ventana = tk.Toplevel(ventana_padre)
    ventana.title("Papelería Luna | Crear cuenta")
    ventana.configure(bg=COLOR_FONDO)
    ventana.resizable(False, False)

    ancho = 510
    alto = 750

    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    x = (pantalla_ancho - ancho) // 2
    y = (pantalla_alto - alto) // 2

    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    if ventana_padre is not None:
        ventana.transient(ventana_padre)

    # --------------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------------

    encabezado = tk.Frame(
        ventana,
        bg=COLOR_AZUL,
        height=145
    )

    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="PAPELERÍA LUNA",
        bg=COLOR_AZUL,
        fg=COLOR_NARANJA,
        font=(FUENTE, 11, "bold")
    ).pack(pady=(18, 5))

    tk.Label(
        encabezado,
        text="Crear cuenta",
        bg=COLOR_AZUL,
        fg=COLOR_PANEL,
        font=(FUENTE, 23, "bold")
    ).pack()

    tk.Label(
        encabezado,
        text="Registra tu acceso al sistema",
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
    # PANEL PRINCIPAL
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
        padx=30,
        pady=18
    )

    tk.Label(
        panel,
        text="Verificación del empleado",
        bg=COLOR_PANEL,
        fg=COLOR_AZUL,
        font=(FUENTE, 17, "bold")
    ).pack(anchor="w", padx=22, pady=(15, 4))

    tk.Label(
        panel,
        text=(
            "Ingresa los mismos datos que proporcionaste "
            "al gerente."
        ),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
        font=(FUENTE, 9),
        wraplength=390,
        justify="left"
    ).pack(anchor="w", padx=22, pady=(0, 13))

    # --------------------------------------------------------
    # FUNCIÓN PARA CREAR CAMPOS
    # --------------------------------------------------------

    entradas = {}

    def crear_campo(nombre, etiqueta, ocultar=False):

        tk.Label(
            panel,
            text=etiqueta,
            bg=COLOR_PANEL,
            fg=COLOR_TEXTO,
            font=(FUENTE, 10, "bold")
        ).pack(anchor="w", padx=22, pady=(7, 5))

        entrada = tk.Entry(
            panel,
            font=(FUENTE, 11),
            bg="#ffffff",
            fg=COLOR_TEXTO,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=COLOR_BORDE,
            highlightcolor=COLOR_NARANJA,
            show="*" if ocultar else ""
        )

        entrada.pack(
            fill="x",
            padx=22,
            ipady=6
        )

        entradas[nombre] = entrada

    # --------------------------------------------------------
    # DATOS DEL EMPLEADO
    # --------------------------------------------------------

    crear_campo(
        "identificacion",
        "Identificación del empleado"
    )

    crear_campo(
        "nombre",
        "Nombre"
    )

    crear_campo(
        "apellidos",
        "Apellidos"
    )

    # --------------------------------------------------------
    # CONTRASEÑA
    # --------------------------------------------------------

    tk.Label(
        panel,
        text="Crea tu contraseña",
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        font=(FUENTE, 10, "bold")
    ).pack(anchor="w", padx=22, pady=(13, 5))

    crear_campo(
        "contrasena",
        "Contraseña",
        ocultar=True
    )

    crear_campo(
        "confirmar",
        "Confirmar contraseña",
        ocultar=True
    )

    tk.Label(
        panel,
        text="Utiliza al menos 8 caracteres.",
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO_SUAVE,
        font=(FUENTE, 9)
    ).pack(anchor="w", padx=22, pady=(7, 0))

    # ========================================================
    # VALIDAR Y CREAR LA CUENTA
    # ========================================================

    def crear_cuenta():

        identificacion = entradas["identificacion"].get().strip()
        nombre = entradas["nombre"].get().strip()
        apellidos = entradas["apellidos"].get().strip()
        contrasena = entradas["contrasena"].get()
        confirmar = entradas["confirmar"].get()

        # ----------------------------------------------------
        # VALIDACIONES BÁSICAS
        # ----------------------------------------------------

        if not all([
            identificacion,
            nombre,
            apellidos,
            contrasena,
            confirmar
        ]):
            messagebox.showwarning(
                "Campos obligatorios",
                "Completa todos los campos.",
                parent=ventana
            )
            return

        if len(contrasena) < 8:
            messagebox.showwarning(
                "Contraseña no válida",
                "La contraseña debe tener al menos 8 caracteres.",
                parent=ventana
            )
            entradas["contrasena"].focus_set()
            return

        if contrasena != confirmar:
            messagebox.showerror(
                "Contraseñas diferentes",
                "Las contraseñas no coinciden.",
                parent=ventana
            )
            entradas["confirmar"].delete(0, tk.END)
            entradas["confirmar"].focus_set()
            return

        conexion = None
        cursor = None

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            # -----------------------------------------------
            # 1. COMPROBAR EL REGISTRO DEL EMPLEADO
            # -----------------------------------------------

            consulta_empleado = """
                SELECT
                    id_empleado,
                    identificacion,
                    nombre,
                    apellidos,
                    puesto,
                    estado
                FROM Empleados
                WHERE identificacion = %s
                LIMIT 1
            """

            cursor.execute(
                consulta_empleado,
                (identificacion,)
            )

            empleado = cursor.fetchone()

            if empleado is None:
                messagebox.showerror(
                    "Empleado no encontrado",
                    "No existe un empleado con esa identificación.\n\n"
                    "Verifica los datos o consulta al gerente.",
                    parent=ventana
                )
                return

            # -----------------------------------------------
            # 2. COMPROBAR QUE ESTÉ ACTIVO
            # -----------------------------------------------

            if empleado["estado"] != EMPLEADO_ACTIVO:
                messagebox.showerror(
                    "Empleado inactivo",
                    "No puedes crear una cuenta porque el empleado "
                    "no está activo.",
                    parent=ventana
                )
                return

            # -----------------------------------------------
            # 3. COMPARAR NOMBRE Y APELLIDOS
            # -----------------------------------------------

            nombre_bd = (empleado["nombre"] or "").strip().casefold()
            apellidos_bd = (
                empleado["apellidos"] or ""
            ).strip().casefold()

            if (
                nombre.casefold() != nombre_bd
                or apellidos.casefold() != apellidos_bd
            ):
                messagebox.showerror(
                    "Datos no coincidentes",
                    "El nombre o los apellidos no coinciden con "
                    "el registro del empleado.\n\n"
                    "Revisa los datos e inténtalo nuevamente.",
                    parent=ventana
                )
                return

            # -----------------------------------------------
            # 4. COMPROBAR QUE NO TENGA OTRA CUENTA
            # -----------------------------------------------

            cursor.execute(
                """
                SELECT id_usuario
                FROM usuarios
                WHERE id_empleado = %s
                LIMIT 1
                """,
                (empleado["id_empleado"],)
            )

            cuenta_existente = cursor.fetchone()

            if cuenta_existente is not None:
                messagebox.showwarning(
                    "Cuenta existente",
                    "Este empleado ya tiene una cuenta registrada.\n\n"
                    "Si necesita recuperar su acceso, debe utilizar "
                    "un procedimiento de recuperación de contraseña.",
                    parent=ventana
                )
                return

            # -----------------------------------------------
            # 5. GENERAR HASH Y CREAR LA CUENTA
            # -----------------------------------------------

            hash_contrasena = generar_hash_contrasena(contrasena)
            rango_cuenta = determinar_rango(empleado["puesto"])

            cursor.execute(
                """
                INSERT INTO usuarios (
                    id_empleado,
                    contrasena,
                    rango,
                    modo_CO,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    empleado["id_empleado"],
                    hash_contrasena,
                    rango_cuenta,
                    0,
                    USUARIO_ACTIVO
                )
            )

            conexion.commit()

            # -----------------------------------------------
            # 6. CONFIRMAR Y VOLVER AL LOGIN
            # -----------------------------------------------

            ventana.destroy()

            messagebox.showinfo(
                "Cuenta creada",
                "¡Tu cuenta se creó correctamente!\n\n"
                "Ahora puedes iniciar sesión con tu identificación "
                "y la contraseña que acabas de crear.",
                parent=ventana_padre
            )

        except mysql.connector.IntegrityError as error:
            if conexion is not None and conexion.is_connected():
                conexion.rollback()

            messagebox.showerror(
                "No se pudo crear la cuenta",
                "La cuenta no pudo registrarse porque existe "
                "un registro duplicado o se incumplió una "
                "restricción de la base de datos.\n\n"
                f"Detalle: {error}",
                parent=ventana
            )

        except mysql.connector.Error as error:
            if conexion is not None and conexion.is_connected():
                conexion.rollback()

            messagebox.showerror(
                "Error de base de datos",
                "No fue posible crear la cuenta.\n\n"
                f"Detalle: {error}",
                parent=ventana
            )

        except Exception as error:
            if conexion is not None and conexion.is_connected():
                conexion.rollback()

            messagebox.showerror(
                "Error inesperado",
                "Ocurrió un problema al crear la cuenta.\n\n"
                f"Detalle: {error}",
                parent=ventana
            )

        finally:
            if cursor is not None:
                cursor.close()

            if conexion is not None and conexion.is_connected():
                conexion.close()

    # --------------------------------------------------------
    # BOTÓN CREAR CUENTA
    # --------------------------------------------------------

    boton_crear = tk.Button(
        panel,
        text="Crear cuenta",
        command=crear_cuenta,
        bg=COLOR_AZUL,
        fg=COLOR_PANEL,
        activebackground=COLOR_AZUL_SECUNDARIO,
        activeforeground=COLOR_PANEL,
        font=(FUENTE, 11, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        pady=9
    )

    boton_crear.pack(
        fill="x",
        padx=22,
        pady=(16, 7)
    )

    boton_hover(
        boton_crear,
        COLOR_AZUL,
        COLOR_AZUL_SECUNDARIO
    )

    # --------------------------------------------------------
    # BOTÓN CANCELAR
    # --------------------------------------------------------

    boton_cancelar = tk.Button(
        panel,
        text="Cancelar y volver",
        command=ventana.destroy,
        bg=COLOR_NARANJA,
        fg=COLOR_AZUL,
        activebackground=COLOR_NARANJA_HOVER,
        activeforeground=COLOR_AZUL,
        font=(FUENTE, 10, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        pady=8
    )

    boton_cancelar.pack(
        fill="x",
        padx=22,
        pady=(0, 12)
    )

    boton_hover(
        boton_cancelar,
        COLOR_NARANJA,
        COLOR_NARANJA_HOVER
    )

    entradas["identificacion"].focus_set()

    # Evita que se interactúe con el login mientras se
    # completa o se cancela el formulario de creación.
    ventana.grab_set()
    ventana.focus_set()