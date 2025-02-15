from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.getcwd(), "templates"), static_folder=os.path.join(os.getcwd(), "static"))

    from app.index import index_bp
    app.register_blueprint(index_bp)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.student import student_bp
    app.register_blueprint(student_bp)

    from app.caretaker import caretaker_bp
    app.register_blueprint(caretaker_bp)

    from app.faculty import faculty_bp
    app.register_blueprint(faculty_bp)

    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    return app