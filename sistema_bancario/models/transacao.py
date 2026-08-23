from datetime import datetime
from extensions import db


class Transacao(db.Model):
    __tablename__ = "transacoes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tipo = db.Column(
        db.String(30),
        nullable=False
    )

    valor = db.Column(
        db.Float,
        nullable=False
    )

    descricao = db.Column(
        db.String(150),
        nullable=True
    )

    data = db.Column(
        db.DateTime,
        default=datetime.now
    )

    conta_id = db.Column(
        db.Integer,
        db.ForeignKey("contas.id"),
        nullable=False
    )

    def __repr__(self):
        return f"<Transacao {self.tipo} - R$ {self.valor}>"