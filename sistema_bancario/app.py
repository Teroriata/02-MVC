from flask import Flask, render_template
from controllers.auth_controller import auth_bp
from extensions import db
from controllers.cliente_controller import cliente_bp
from controllers.conta_controller import conta_bp


def create_app():
    app = Flask(
        __name__,
        template_folder="views"
    )

    # Necessário para utilizar flash()
    app.config["SECRET_KEY"] = "sistema-bancario-chave"

    # Banco SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banco.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializa o banco
    db.init_app(app)

    # Registra os Controllers
    app.register_blueprint(auth_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(conta_bp)

    # Cria as tabelas caso ainda não existam
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)