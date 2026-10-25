import tkinter as tk
from tkinter import messagebox

from tema import (
    establecer_usuario,
    obtener_colores,
    cambiar_tema
)

# ============================================================
# CONFIGURACIÓN
# ============================================================

FUENTE = "Arial"

# ============================================================
# IMPORTACIONES DE MÓDULOS
# ============================================================

from cliente import abrir_clientes
from empleado import abrir_empleados
from proveedor import abrir_proveedores
from inventario import abrir_inventario
from ventas import abrir_ventas
from pedido import abrir_pedidos

# ============================================================
# PERMISOS POR PUESTO
# ============================================================

PERMISOS_PUESTO = {
    "gerente": [
        "clientes", "empleados", "proveedores",
        "productos", "ventas", "pedidos"
    ],
    "cajero": [
        "ventas", "clientes", "productos"
    ],
    "vendedor": [
        "clientes", "productos", "ventas"
    ],
    "encargado de inventario": [
        "productos", "proveedores", "pedidos"
    ],
    "auxiliar administrativo": [
        "clientes", "proveedores", "pedidos"
    ],
    "almacenista": [
        "productos", "pedidos"
    ]
}

# ============================================================
# CENTRAR VENTANA
# ============================================================

def centrar_ventana(ventana, ancho, alto):
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    x = (pantalla_ancho - ancho) // 2
    y = (pantalla_alto - alto) // 2

    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


# ============================================================
# MENÚ PRINCIPAL
# ============================================================

def iniciar_menu(usuario):

    ventana = tk.Tk()
    ventana.title("Papelería Luna | Menú principal")

    centrar_ventana(ventana, 1000, 760)
    ventana.resizable(False, False)

    # ========================================================
    # TEMA PERSONAL DEL USUARIO
    # ========================================================

    id_usuario = usuario.get("id_usuario")

    if id_usuario is None:
        messagebox.showerror(
            "Error de sesión",
            "No se encontró el identificador del usuario.\n"
            "Revisa los datos que entrega el inicio de sesión.",
            parent=ventana
        )
        ventana.destroy()
        return

    tema_actual = {
        "nombre": establecer_usuario(id_usuario)
    }

    colores = obtener_colores(tema_actual["nombre"])

    nombre_completo = (
        f"{usuario['nombre']} {usuario['apellidos']}"
    )

    puesto = usuario.get("puesto") or ""
    rango = str(
        usuario.get("rango") or ""
    ).strip().casefold()

    puesto_normalizado = puesto.strip().casefold()

    if rango == "administrador":
        permisos = [
            "clientes",
            "empleados",
            "proveedores",
            "productos",
            "ventas",
            "pedidos"
        ]
    else:
        permisos = PERMISOS_PUESTO.get(
            puesto_normalizado,
            []
        )

    # ========================================================
    # REFERENCIAS A WIDGETS
    # ========================================================

    widgets_fondo = []
    widgets_panel = []
    widgets_texto = []
    widgets_texto_suave = []
    widgets_encabezado = []
    widgets_bordes = []
    botones_modulo = []
    botones_especiales = []

    etiquetas_encabezado = []
    etiquetas_footer = []

    # Se asignan después de crear el panel de usuario.
    etiqueta_sesion = None
    etiqueta_puesto = None

    # ========================================================
    # FUNCIONES DE COLOR
    # ========================================================

    def aplicar_colores():

        c = obtener_colores(tema_actual["nombre"])

        colores.clear()
        colores.update(c)

        # Fondo de la ventana principal
        ventana.configure(bg=c["FONDO"])

        # Fondos generales
        for widget in widgets_fondo:
            try:
                widget.configure(bg=c["FONDO"])
            except tk.TclError:
                pass

        # Paneles
        for widget in widgets_panel:
            try:
                widget.configure(
                    bg=c["PANEL"],
                    highlightbackground=c["BORDE"]
                )
            except tk.TclError:
                pass

        # Textos principales
        for widget in widgets_texto:
            try:
                widget.configure(
                    bg=c["FONDO"],
                    fg=c["TEXTO"]
                )
            except tk.TclError:
                pass

        # Etiquetas dentro del panel del usuario
        if etiqueta_sesion is not None:
            etiqueta_sesion.configure(
                bg=c["PANEL"],
                fg=c["TEXTO"]
            )

        if etiqueta_puesto is not None:
            etiqueta_puesto.configure(
                bg=c["PANEL"],
                fg=c["TEXTO_SUAVE"]
            )

        # Etiquetas secundarias
        for widget in widgets_texto_suave:
            try:
                widget.configure(
                    bg=c["FONDO"],
                    fg=c["TEXTO_SUAVE"]
                )
            except tk.TclError:
                pass

        # Encabezado y pie de página
        for widget in widgets_encabezado:
            try:
                widget.configure(bg=c["AZUL"])
            except tk.TclError:
                pass

        # Franjas naranjas
        for widget in widgets_bordes:
            try:
                widget.configure(bg=c["NARANJA"])
            except tk.TclError:
                pass

        # Etiquetas del encabezado
        for widget in etiquetas_encabezado:
            try:
                widget.configure(
                    bg=c["AZUL"],
                    fg=(
                        c["NARANJA"]
                        if getattr(widget, "_es_marca", False)
                        else "#FFFFFF"
                    )
                )
            except tk.TclError:
                pass

        # Etiquetas del pie de página
        for widget in etiquetas_footer:
            try:
                widget.configure(
                    bg=c["AZUL"],
                    fg="#D1D5DB"
                )
            except tk.TclError:
                pass

        # Tarjetas de los módulos
        for tarjeta, boton, franja in botones_modulo:
            try:
                tarjeta.configure(
                    bg=c["PANEL"],
                    highlightbackground=c["BORDE"]
                )

                franja.configure(
                    bg=c["NARANJA"]
                )

                boton.configure(
                    bg=c["PANEL"],
                    fg=c["TEXTO"],
                    activebackground=c["BORDE"],
                    activeforeground=c["TEXTO"]
                )

            except tk.TclError:
                pass

        # Botones del pie de página
        for boton, tipo in botones_especiales:
            try:

                if tipo == "tema":

                    es_oscuro = (
                        tema_actual["nombre"] == "oscuro"
                    )

                    boton.configure(
                        text=(
                            "Tema claro"
                            if es_oscuro
                            else "Tema oscuro"
                        ),
                        bg=c["AZUL_SECUNDARIO"],
                        fg="#FFFFFF",
                        activebackground=c["AZUL"],
                        activeforeground="#FFFFFF",
                        font=(FUENTE, 9, "bold"),
                        relief="flat",
                        bd=0,
                        width=13,
                        anchor="center"
                    )

                elif tipo == "salir":

                    boton.configure(
                        bg=c["ROJO"],
                        fg="#FFFFFF",
                        activebackground=c["ROJO_HOVER"],
                        activeforeground="#FFFFFF"
                    )

            except tk.TclError:
                pass

    # ========================================================
    # ALTERNAR TEMA
    # ========================================================

    def alternar_tema():

        nuevo_tema = (
            "oscuro"
            if tema_actual["nombre"] == "claro"
            else "claro"
        )

        if cambiar_tema(nuevo_tema):

            tema_actual["nombre"] = nuevo_tema
            aplicar_colores()

        else:

            messagebox.showerror(
                "Error al cambiar el tema",
                "No se pudo guardar tu preferencia en la "
                "base de datos.",
                parent=ventana
            )

    # ========================================================
    # ENCABEZADO
    # ========================================================

    encabezado = tk.Frame(
        ventana,
        height=165
    )

    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    widgets_encabezado.append(encabezado)

    etiqueta_marca = tk.Label(
        encabezado,
        text="PAPELERÍA LUNA",
        font=(FUENTE, 11, "bold")
    )

    etiqueta_marca._es_marca = True
    etiqueta_marca.pack(pady=(15, 4))

    etiquetas_encabezado.append(etiqueta_marca)

    etiqueta_titulo = tk.Label(
        encabezado,
        text="Sistema de Gestión",
        font=(FUENTE, 24, "bold")
    )

    etiqueta_titulo.pack()
    etiquetas_encabezado.append(etiqueta_titulo)

    etiqueta_subtitulo = tk.Label(
        encabezado,
        text="Administración de las operaciones del negocio",
        font=(FUENTE, 10)
    )

    etiqueta_subtitulo.pack(pady=(3, 0))
    etiquetas_encabezado.append(etiqueta_subtitulo)

    franja_superior = tk.Frame(
        ventana,
        height=5
    )

    franja_superior.pack(fill="x")
    widgets_bordes.append(franja_superior)

    # ========================================================
    # INFORMACIÓN DEL USUARIO
    # ========================================================

    panel_usuario = tk.Frame(
        ventana,
        highlightthickness=1
    )

    panel_usuario.pack(
        fill="x",
        padx=45,
        pady=(15, 0)
    )

    widgets_panel.append(panel_usuario)

    etiqueta_sesion = tk.Label(
        panel_usuario,
        text=f"Sesión: {nombre_completo}",
        font=(FUENTE, 10, "bold")
    )

    etiqueta_sesion.pack(
        side="left",
        padx=15,
        pady=10
    )

    etiqueta_puesto = tk.Label(
        panel_usuario,
        text=f"Puesto: {puesto}  |  Rango: {rango}",
        font=(FUENTE, 9)
    )

    etiqueta_puesto.pack(
        side="right",
        padx=15,
        pady=10
    )

    # ========================================================
    # CONTENIDO
    # ========================================================

    contenido = tk.Frame(ventana)

    contenido.pack(
        fill="both",
        expand=True,
        padx=45,
        pady=15
    )

    widgets_fondo.append(contenido)

    etiqueta_pregunta = tk.Label(
        contenido,
        text="¿Qué deseas administrar?",
        font=(FUENTE, 19, "bold")
    )

    etiqueta_pregunta.pack(pady=(0, 4))
    widgets_texto.append(etiqueta_pregunta)

    etiqueta_descripcion = tk.Label(
        contenido,
        text=(
            "Accede a los módulos disponibles "
            "según tu rango y puesto."
        ),
        font=(FUENTE, 10)
    )

    etiqueta_descripcion.pack(pady=(0, 12))
    widgets_texto_suave.append(etiqueta_descripcion)

    contenedor = tk.Frame(contenido)
    contenedor.pack()

    widgets_fondo.append(contenedor)

    for columna in range(3):
        contenedor.grid_columnconfigure(
            columna,
            minsize=275
        )

    # ========================================================
    # TARJETAS DE MÓDULOS
    # ========================================================

    def crear_boton_modulo(parent, texto, comando):

        tarjeta = tk.Frame(
            parent,
            highlightthickness=1,
            bd=0,
            width=245,
            height=105
        )

        tarjeta.pack_propagate(False)

        franja = tk.Frame(
            tarjeta,
            height=5
        )

        franja.pack(fill="x")

        boton = tk.Button(
            tarjeta,
            text=texto,
            command=comando,
            font=(FUENTE, 13, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            wraplength=200,
            justify="center"
        )

        boton.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        def entrar(evento):

            c = obtener_colores(tema_actual["nombre"])

            boton.configure(
                bg=c["BORDE"]
            )

        def salir(evento):

            c = obtener_colores(tema_actual["nombre"])

            boton.configure(
                bg=c["PANEL"]
            )

        boton.bind("<Enter>", entrar)
        boton.bind("<Leave>", salir)

        botones_modulo.append(
            (tarjeta, boton, franja)
        )

        return tarjeta

    # ========================================================
    # MÓDULOS DISPONIBLES
    # ========================================================

    modulos = [
        (
            "clientes",
            "Clientes",
            abrir_clientes
        ),
        (
            "empleados",
            "Empleados",
            lambda: abrir_empleados(ventana, usuario)
        ),
        (
            "proveedores",
            "Proveedores",
            abrir_proveedores
        ),
        (
            "productos",
            "Productos",
            abrir_inventario
        ),
        (
            "ventas",
            "Ventas",
            lambda: abrir_ventas(
                ventana,
                identificacion_empleado=usuario.get(
                    "identificacion"
                )
            )
        ),
        (
            "pedidos",
            "Pedidos a proveedores",
            lambda: abrir_pedidos(
                ventana,
                usuario.get("id_empleado")
            )
        )
    ]

    columna = 0
    fila = 0

    for clave, nombre, funcion in modulos:

        if clave not in permisos:
            continue

        tarjeta = crear_boton_modulo(
            contenedor,
            nombre,
            funcion
        )

        tarjeta.grid(
            row=fila,
            column=columna,
            padx=10,
            pady=8
        )

        columna += 1

        if columna == 3:
            columna = 0
            fila += 1

    if not permisos:

        etiqueta_sin_permisos = tk.Label(
            contenido,
            text=(
                "Tu puesto todavía no tiene módulos asignados. "
                "Contacta al administrador."
            ),
            font=(FUENTE, 10, "bold")
        )

        etiqueta_sin_permisos.pack(pady=15)
        widgets_texto.append(etiqueta_sin_permisos)

    # ========================================================
    # PIE DE PÁGINA
    # ========================================================

    footer = tk.Frame(
        ventana,
        height=58
    )

    footer.pack(
        side="bottom",
        fill="x"
    )

    footer.pack_propagate(False)

    widgets_encabezado.append(footer)

    franja_footer = tk.Frame(
        footer,
        height=3
    )

    franja_footer.pack(fill="x")
    widgets_bordes.append(franja_footer)

    etiqueta_footer = tk.Label(
        footer,
        text="Papelería Luna | Sistema de Gestión",
        font=(FUENTE, 9)
    )

    etiqueta_footer.pack(
        side="left",
        padx=25,
        pady=12
    )

    etiquetas_footer.append(etiqueta_footer)

    # ========================================================
    # BOTONES DEL PIE DE PÁGINA
    # ========================================================

    contenedor_botones = tk.Frame(footer)

    contenedor_botones.pack(
        side="right",
        padx=25,
        pady=8
    )

    # --------------------------------------------------------
    # CERRAR SESIÓN
    # --------------------------------------------------------

    def cerrar_sesion():

        if messagebox.askyesno(
            "Cerrar sesión",
            "¿Deseas cerrar tu sesión y volver al inicio?",
            parent=ventana
        ):

            ventana.destroy()

            from login import iniciar_sesion
            iniciar_sesion()

    boton_salir = tk.Button(
        contenedor_botones,
        text="Cerrar sesión",
        command=cerrar_sesion,
        font=(FUENTE, 10, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=18,
        pady=6
    )

    boton_salir.pack(
        side="right",
        padx=(8, 0)
    )

    botones_especiales.append(
        (boton_salir, "salir")
    )

    # --------------------------------------------------------
    # CAMBIAR TEMA
    # --------------------------------------------------------

    boton_tema = tk.Button(
        contenedor_botones,
        text="Tema oscuro",
        command=alternar_tema,
        font=(FUENTE, 9, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=14,
        pady=7,
        width=13,
        anchor="center"
    )

    boton_tema.pack(
        side="right",
        padx=(0, 8)
    )

    botones_especiales.append(
        (boton_tema, "tema")
    )

    # ========================================================
    # APLICAR TEMA INICIAL
    # ========================================================

    aplicar_colores()

    ventana.mainloop()