import os

from flask import Flask, flash, redirect, render_template, request
from flask_login import LoginManager

from config import (
    BASE_DIR,
    SECRET_KEY,
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    UPLOAD_FOLDER,
)
from routes.auth import auth_bp
from routes.student import student_bp
from routes.admin import admin_bp


from models import User, db


DB_PATH = os.path.join(BASE_DIR, "placement.db")
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def create_app():
    """Create and configure the Flask application and register all extensions/routes."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def request_too_large(error):
        flash("Uploaded data is too large. Maximum file size is 2 MB.", "danger")
        return redirect(request.referrer or "/"), 413

    with app.app_context():
        db.create_all()
        # Lightweight SQLite compatibility for an existing placement.db.
        with db.engine.connect() as connection:
            resource_columns = connection.exec_driver_sql("PRAGMA table_info(resources)").fetchall()
            if resource_columns and not any(column[1] == "added_on" for column in resource_columns):
                connection.exec_driver_sql(
                    "ALTER TABLE resources ADD COLUMN added_on DATETIME"
                )
                connection.exec_driver_sql(
                    "UPDATE resources SET added_on = CURRENT_TIMESTAMP WHERE added_on IS NULL"
                )
                connection.commit()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
