from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from extensions import db
from models.cliente import Cliente


cliente_bp = Blueprint(
    "cliente",
    __name__
)


# -----------------------------------
# LISTAR CLIENTES
# -----------------------------------
@cliente_bp.route("/clientes")
def listar_clientes():

    clientes = Cliente.query.all()

    return render_template(
        "clientes.html",
        clientes=clientes
    )


# -----------------------------------
# CADASTRAR CLIENTE
# -----------------------------------
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.conta import Conta
from models.cliente import Cliente
from models.transacao import Transacao



conta_bp = Blueprint(
    "conta",
    __name__
)

@conta_bp.route(
    "/receber-pix",
    methods=["GET", "POST"]
)
def receber_pix():

    if "usuario" not in session:
        return redirect(
            url_for("auth.login")
        )

    cliente_id = session["usuario"]

    conta = Conta.query.filter_by(
        cliente_id=cliente_id
    ).first()

    if not conta:
        flash("Conta não encontrada.")

        return redirect(
            url_for("auth.home")
        )

    if request.method == "POST":

        try:
            valor = float(
                request.form["valor"]
            )

            conta.depositar(valor)

            transacao = Transacao(
                tipo="Pix recebido",
                valor=valor,
                conta_id=conta.id
            )

            db.session.add(transacao)
            db.session.commit()

            flash("Pix recebido com sucesso!")

            return redirect(
                url_for("auth.home")
            )

        except ValueError as erro:

            flash(str(erro))

    return render_template(
        "receber_pix.html",
        conta=conta
    )
# ---------------------------------------------------
# LISTAR TODAS AS CONTAS
# ---------------------------------------------------
@conta_bp.route("/contas")
def listar_contas():

    contas = Conta.query.all()

    return render_template(
        "contas.html",
        contas=contas
    )


# ---------------------------------------------------
# ABRIR NOVA CONTA
# ---------------------------------------------------
@cliente_bp.route(
    "/clientes/cadastrar",
    methods=["GET", "POST"]
)
def cadastrar_cliente():

    if request.method == "POST":

        nome = request.form["nome"]
        cpf = request.form["cpf"]
        email = request.form["email"]
        senha = request.form["senha"]
        confirmar_senha = request.form["confirmar_senha"]

        # Remove pontos e traço do CPF
        cpf = cpf.replace(".", "").replace("-", "")

        # Verifica se as senhas são iguais
        if senha != confirmar_senha:

            flash("As senhas não coincidem.")

            return redirect(
                url_for("cliente.cadastrar_cliente")
            )

        # Verifica se o CPF já está cadastrado
        cliente_cpf = Cliente.query.filter_by(
            cpf=cpf
        ).first()

        if cliente_cpf:

            flash("CPF já cadastrado.")

            return redirect(
                url_for("cliente.cadastrar_cliente")
            )

        # Verifica se o e-mail já está cadastrado
        cliente_email = Cliente.query.filter_by(
            email=email
        ).first()

        if cliente_email:

            flash("E-mail já cadastrado.")

            return redirect(
                url_for("cliente.cadastrar_cliente")
            )

        try:

            # Cria o cliente
            cliente = Cliente(
                nome=nome,
                cpf=cpf,
                email=email
            )

            # Criptografa a senha
            cliente.definir_senha(senha)

            db.session.add(cliente)

            # Gera o ID antes do commit
            db.session.flush()

            # Cria automaticamente uma conta
            conta = Conta(
                numero=str(cliente.id).zfill(6),
                saldo=0.0,
                cliente_id=cliente.id
            )

            db.session.add(conta)

            # Salva cliente e conta
            db.session.commit()

            flash(
                "Cadastro realizado com sucesso!"
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Não foi possível realizar o cadastro."
            )

            return redirect(
                url_for("cliente.cadastrar_cliente")
            )

    return render_template(
        "cadastrar_cliente.html"
    )

# ---------------------------------------------------
# VISUALIZAR UMA CONTA
# ---------------------------------------------------
@conta_bp.route(
    "/contas/<int:id>"
)
def visualizar_conta(id):

    conta = Conta.query.get_or_404(id)

    # Busca as transações da conta
    transacoes = Transacao.query.filter_by(
        conta_id=conta.id
    ).order_by(
        Transacao.data.desc()
    ).all()

    return render_template(
        "conta.html",
        conta=conta,
        transacoes=transacoes
    )


# ---------------------------------------------------
# REALIZAR DEPÓSITO
# ---------------------------------------------------
@conta_bp.route(
    "/contas/<int:id>/depositar",
    methods=["POST"]
)
def depositar(id):

    conta = Conta.query.get_or_404(id)

    try:

        valor = float(
            request.form["valor"]
        )

        # Chama a regra de negócio
        # presente no Model Conta
        conta.depositar(valor)

        # Registra a transação
        transacao = Transacao(
            tipo="DEPÓSITO",
            valor=valor,
            conta_id=conta.id
        )

        db.session.add(transacao)

        # Salva conta e transação
        db.session.commit()

        flash(
            "Depósito realizado com sucesso."
        )

    except ValueError as erro:

        db.session.rollback()

        flash(
            str(erro)
        )

    return redirect(
        url_for(
            "conta.visualizar_conta",
            id=conta.id
        )
    )


# ---------------------------------------------------
# REALIZAR SAQUE
# ---------------------------------------------------
@conta_bp.route(
    "/contas/<int:id>/sacar",
    methods=["POST"]
)
def sacar(id):

    conta = Conta.query.get_or_404(id)

    try:

        valor = float(
            request.form["valor"]
        )

        # Chama a regra de negócio
        # do Model Conta
        conta.sacar(valor)

        # Cria registro da transação
        transacao = Transacao(
            tipo="SAQUE",
            valor=valor,
            conta_id=conta.id
        )

        db.session.add(transacao)

        # Salva as alterações
        db.session.commit()

        flash(
            "Saque realizado com sucesso."
        )

    except ValueError as erro:

        db.session.rollback()

        flash(
            str(erro)
        )

    return redirect(
        url_for(
            "conta.visualizar_conta",
            id=conta.id
        )
    )