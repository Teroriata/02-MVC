from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class Cliente(db.Model):

    __tablename__ = "clientes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    cpf = db.Column(
        db.String(14),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    def definir_senha(self, senha):
        self.senha = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(
            self.senha,
            senha
        )