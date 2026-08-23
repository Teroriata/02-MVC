from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from models.cliente import Cliente
from models.conta import Conta
from models.transacao import Transacao


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        cpf = request.form["cpf"]
        senha = request.form["senha"]

        # Remove pontos e traço
        cpf = cpf.replace(".", "").replace("-", "")

        cliente = Cliente.query.filter_by(
            cpf=cpf
        ).first()

        if cliente and cliente.verificar_senha(senha):

            session["usuario"] = cliente.id

            return redirect(
                url_for("auth.home")
            )

        flash("CPF ou senha inválidos.")

    return render_template(
        "login.html"
    )


@auth_bp.route("/home")
def home():

    if "usuario" not in session:
        return redirect(
            url_for("auth.login")
        )

    cliente_id = session["usuario"]

    cliente = Cliente.query.get(cliente_id)

    conta = Conta.query.filter_by(
        cliente_id=cliente_id
    ).first()

    movimentacoes = []

    if conta:
        movimentacoes = Transacao.query.filter_by(
            conta_id=conta.id
        ).order_by(
            Transacao.data.desc()
        ).limit(5).all()

    return render_template(
        "index.html",
        cliente=cliente,
        conta=conta,
        movimentacoes=movimentacoes
    )


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )