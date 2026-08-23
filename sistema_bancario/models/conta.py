from extensions import db


class Conta(db.Model):
    __tablename__ = "contas"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    saldo = db.Column(db.Float, default=0.0)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=False
    )

    transacoes = db.relationship(
        "Transacao",
        backref="conta",
        lazy=True
    )

    def depositar(self, valor):
        if valor <= 0:
            raise ValueError("O valor do depósito deve ser maior que zero.")

        self.saldo += valor

    def sacar(self, valor):
        if valor <= 0:
            raise ValueError("O valor do saque deve ser maior que zero.")

        if valor > self.saldo:
            raise ValueError("Saldo insuficiente.")

        self.saldo -= valor

    def __repr__(self):
        return f"<Conta {self.numero}>"