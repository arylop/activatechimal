
# Activate + Chimal

Aplicación web para promover la actividad física y una vida saludable.

## Funciones

- Registro de usuarios.
- Inicio de sesión.
- Menú principal.
- Registro de actividad física.
- Deportes favoritos.
- Alimentación.
- Consulta del progreso.
- Actualización del perfil.
- Base de datos SQLite y PostgreSQL.
- Diseño adaptable a celulares.

## Tecnologías utilizadas

- Python
- Flask
- HTML
- CSS
- JavaScript
- SQLite
- PostgreSQL
- Gunicorn

## Instalación local

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar el proyecto:

```bash
python app.py
```

Abrir en el navegador:

http://127.0.0.1:5000

## Publicación

El proyecto está preparado para conectarse a GitHub y Render.

Para Render se necesita configurar:

- SECRET_KEY
- DATABASE_URL

El servicio utiliza Gunicorn para ejecutarse.
