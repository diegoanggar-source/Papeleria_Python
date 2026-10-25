# Sistema CRUD Papelería - Python + MySQL

Sistema de gestión de inventario y ventas para papelería desarrollado en Python con base de datos MySQL. Permite administrar productos, proveedores, clientes y ventas mediante operaciones CRUD.

## 🚀 Funcionalidades

**Módulo Productos:**
- Crear, listar, actualizar y eliminar productos
- Control de stock y stock mínimo
- Categorías (cuadernos, plumas, mochilas, papelería, etc.)
- Código de barras / SKU

**Módulo Clientes y Ventas:**
- Registro de clientes
- Generación de tickets de venta
- Historial de ventas

**Módulo Extra:**
- Búsqueda por nombre o código
- Reporte de productos con bajo stock
- Login de administrador

## 🛠️ Tecnologías

- **Lenguaje:** Python 3.10+
- **Base de Datos:** MySQL 8.0 / MariaDB
- **Librerías:** `mysql-connector-python`, `tabulate`, `python-dotenv`

## 📋 Requisitos Previos

```bash
sudo apt install python3 python3-pip mysql-server -y
