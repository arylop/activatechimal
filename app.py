
import os
from datetime import date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "solo-desarrollo-cambia-esta-clave"
)

# PostgreSQL en Render y SQLite en computadora
database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///activate_chimal.db"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# MODELOS DE LA BASE DE DATOS
# =========================

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(40), unique=True, nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Actividad(db.Model):
    __tablename__ = "actividades"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )
    actividad = db.Column(db.String(80), nullable=False)
    minutos = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    notas = db.Column(db.String(250), nullable=True)


class Deporte(db.Model):
    __tablename__ = "deportes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )
    deporte = db.Column(db.String(40), nullable=False)


# =========================
# PROTECCIÓN DE RUTAS
# =========================

def requiere_login(funcion):
    @wraps(funcion)
    def verificar(*args, **kwargs):

        if "usuario_id" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))

        return funcion(*args, **kwargs)

    return verificar


# =========================
# PÁGINA PRINCIPAL
# =========================

@app.route("/")
def index():

    if session.get("usuario_id"):
        return redirect(url_for("inicio"))

    return redirect(url_for("login"))


# =========================
# REGISTRO DE USUARIOS
# =========================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        usuario = request.form.get("usuario", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        if not all([nombre, usuario, correo, password]):
            flash("Completa todos los campos.", "error")

        elif len(password) < 8:
            flash(
                "La contraseña debe tener al menos 8 caracteres.",
                "error"
            )

        else:

            nuevo = Usuario(
                nombre=nombre,
                usuario=usuario,
                correo=correo,
                password=generate_password_hash(password)
            )

            try:
                db.session.add(nuevo)
                db.session.commit()

                flash(
                    "Cuenta creada. Ahora inicia sesión.",
                    "success"
                )

                return redirect(url_for("login"))

            except Exception:
                db.session.rollback()
                flash(
                    "Ese usuario o correo ya está registrado.",
                    "error"
                )

    return render_template("register.html")


# =========================
# INICIO DE SESIÓN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        identidad = request.form.get("identidad", "").strip()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter(
            or_(
                Usuario.usuario == identidad,
                Usuario.correo == identidad.lower()
            )
        ).first()

        if usuario and check_password_hash(
            usuario.password,
            password
        ):

            session.clear()
            session["usuario_id"] = usuario.id

            return redirect(url_for("inicio"))

        flash(
            "Usuario/correo o contraseña incorrectos.",
            "error"
        )

    return render_template("login.html")


# =========================
# MENÚ PRINCIPAL
# =========================

@app.route("/inicio")
@requiere_login
def inicio():

    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    actividades = (
        Actividad.query
        .filter_by(usuario_id=usuario.id)
        .order_by(
            Actividad.fecha.desc(),
            Actividad.id.desc()
        )
        .all()
    )

    deportes = [
        d.deporte
        for d in Deporte.query.filter_by(
            usuario_id=usuario.id
        ).all()
    ]

    total_minutos = (
        db.session.query(
            func.coalesce(func.sum(Actividad.minutos), 0)
        )
        .filter_by(usuario_id=usuario.id)
        .scalar()
    )

    return render_template(
        "dashboard.html",
        usuario=usuario,
        actividades=actividades,
        deportes=deportes,
        total_minutos=total_minutos,
        hoy=date.today().isoformat()
    )


# =========================
# REGISTRAR ACTIVIDAD
# =========================

@app.route("/actividad", methods=["POST"])
@requiere_login
def actividad():

    nombre = request.form.get(
        "actividad", ""
    ).strip()

    fecha_texto = request.form.get("fecha", "")
    notas = request.form.get("notas", "").strip()

    try:
        minutos = int(request.form.get("minutos", "0"))
        fecha = date.fromisoformat(fecha_texto)

    except (ValueError, TypeError):

        flash(
            "Escribe una fecha y una duración válidas.",
            "error"
        )

        return redirect(url_for("inicio") + "#actividad")

    if not nombre or minutos < 1 or minutos > 1440:

        flash(
            "La actividad es obligatoria y los minutos deben estar entre 1 y 1440.",
            "error"
        )

    else:

        registro = Actividad(
            usuario_id=session["usuario_id"],
            actividad=nombre,
            minutos=minutos,
            fecha=fecha,
            notas=notas
        )

        db.session.add(registro)
        db.session.commit()

        flash(
            "Actividad registrada correctamente.",
            "success"
        )

    return redirect(url_for("inicio") + "#actividad")


# =========================
# ELIMINAR ACTIVIDAD
# =========================

@app.route("/eliminar/<int:actividad_id>", methods=["POST"])
@requiere_login
def eliminar(actividad_id):

    registro = Actividad.query.filter_by(
        id=actividad_id,
        usuario_id=session["usuario_id"]
    ).first()

    if registro:

        db.session.delete(registro)
        db.session.commit()

        flash("Actividad eliminada.", "success")

    return redirect(url_for("inicio") + "#actividad")


# =========================
# DEPORTES FAVORITOS
# =========================

@app.route("/deportes", methods=["POST"])
@requiere_login
def guardar_deportes():

    permitidos = {
        "Fútbol",
        "Básquetbol",
        "Voleibol",
        "Natación",
        "Atletismo",
        "Ciclismo",
        "Baile",
        "Tenis"
    }

    seleccionados = [
        deporte
        for deporte in request.form.getlist("deportes")
        if deporte in permitidos
    ]

    Deporte.query.filter_by(
        usuario_id=session["usuario_id"]
    ).delete()

    for deporte in seleccionados:

        db.session.add(
            Deporte(
                usuario_id=session["usuario_id"],
                deporte=deporte
            )
        )

    db.session.commit()

    flash(
        "Deportes favoritos guardados.",
        "success"
    )

    return redirect(url_for("inicio") + "#deportes")


# =========================
# ACTUALIZAR PERFIL
# =========================

@app.route("/perfil", methods=["POST"])
@requiere_login
def perfil():

    nombre = request.form.get(
        "nombre", ""
    ).strip()

    correo = request.form.get(
        "correo", ""
    ).strip().lower()

    if not nombre or not correo:

        flash(
            "El nombre y el correo son obligatorios.",
            "error"
        )

        return redirect(url_for("inicio") + "#perfil")

    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    usuario.nombre = nombre
    usuario.correo = correo

    try:

        db.session.commit()

        flash(
            "Perfil actualizado.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Ese correo ya está registrado por otra cuenta.",
            "error"
        )

    return redirect(url_for("inicio") + "#perfil")


# =========================
# CERRAR SESIÓN
# =========================

@app.route("/salir")
def salir():

    session.clear()

    flash("Sesión cerrada.", "success")

    return redirect(url_for("login"))


# =========================
# CREAR TABLAS
# =========================

with app.app_context():
    db.create_all()


# =========================
# EJECUTAR APLICACIÓN
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
