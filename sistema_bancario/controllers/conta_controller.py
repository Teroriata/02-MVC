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
from datetime import datetime


conta_bp = Blueprint(
    "conta",
    __name__
)


# ---------------------------------------------------
# RECEBER PIX
# ---------------------------------------------------
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

            return render_template(
                "sucesso.html",
                mensagem=f"Pix de R$ {valor:.2f} recebido com sucesso!"
            )

        except ValueError as erro:

            db.session.rollback()

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
@conta_bp.route(
    "/contas/abrir",
    methods=["GET", "POST"]
)
def abrir_conta():

    if request.method == "POST":

        numero = request.form["numero"]
        cliente_id = request.form["cliente_id"]

        conta_existente = Conta.query.filter_by(
            numero=numero
        ).first()

        if conta_existente:

            flash(
                "Já existe uma conta com esse número."
            )

            return redirect(
                url_for("conta.abrir_conta")
            )

        nova_conta = Conta(
            numero=numero,
            saldo=0.0,
            cliente_id=cliente_id
        )

        db.session.add(nova_conta)

        db.session.commit()

        flash(
            "Conta criada com sucesso."
        )

        return redirect(
            url_for("conta.listar_contas")
        )

    clientes = Cliente.query.all()

    return render_template(
        "abrir_conta.html",
        clientes=clientes
    )


# ---------------------------------------------------
# VISUALIZAR UMA CONTA
# ---------------------------------------------------
@conta_bp.route(
    "/contas/<int:id>"
)
def visualizar_conta(id):

    conta = Conta.query.get_or_404(id)

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

        conta.depositar(valor)

        transacao = Transacao(
            tipo="DEPÓSITO",
            valor=valor,
            conta_id=conta.id
        )

        db.session.add(transacao)

        db.session.commit()

        flash(
            "Depósito realizado com sucesso."
        )

    except ValueError as erro:

        db.session.rollback()

        flash(str(erro))

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

        conta.sacar(valor)

        transacao = Transacao(
            tipo="SAQUE",
            valor=valor,
            conta_id=conta.id
        )

        db.session.add(transacao)

        db.session.commit()

        flash(
            "Saque realizado com sucesso."
        )

    except ValueError as erro:

        db.session.rollback()

        flash(str(erro))

    return redirect(
        url_for(
            "conta.visualizar_conta",
            id=conta.id
        )
    )


# ---------------------------------------------------
# TRANSFERÊNCIA
# ---------------------------------------------------
@conta_bp.route(
    "/transferir",
    methods=["GET", "POST"]
)
def transferir():

    if "usuario" not in session:
        return redirect(
            url_for("auth.login")
        )

    cliente_id = session["usuario"]

    cliente_origem = Cliente.query.get(
        cliente_id
    )

    conta_origem = Conta.query.filter_by(
        cliente_id=cliente_id
    ).first()

    if not conta_origem:

        flash("Conta não encontrada.")

        return redirect(
            url_for("auth.home")
        )

    if request.method == "POST":

        cpf_destino = request.form["cpf_destino"]
        valor_digitado = request.form["valor"]

        # Remove pontos e traço
        cpf_destino = cpf_destino.replace(
            ".",
            ""
        ).replace(
            "-",
            ""
        )

        # Validação básica do CPF
        if (
            not cpf_destino.isdigit()
            or len(cpf_destino) != 11
        ):

            flash("CPF inválido.")

            return redirect(
                url_for("conta.transferir")
            )

        # Procura o destinatário
        cliente_destino = Cliente.query.filter_by(
            cpf=cpf_destino
        ).first()

        if not cliente_destino:

            flash(
                "CPF não encontrado."
            )

            return redirect(
                url_for("conta.transferir")
            )

        # Impede transferência para a própria conta
        if cliente_destino.id == cliente_id:

            flash(
                "Você não pode transferir para sua própria conta."
            )

            return redirect(
                url_for("conta.transferir")
            )

        # Procura conta do destinatário
        conta_destino = Conta.query.filter_by(
            cliente_id=cliente_destino.id
        ).first()

        if not conta_destino:

            flash(
                "O destinatário não possui uma conta."
            )

            return redirect(
                url_for("conta.transferir")
            )

        try:

            valor = float(
                valor_digitado
            )

            if valor <= 0:

                raise ValueError(
                    "O valor deve ser maior que zero."
                )

            # Retira da conta de origem
            conta_origem.sacar(
                valor
            )

            # Adiciona na conta de destino
            conta_destino.depositar(
                valor
            )

            # Histórico de quem enviou
            transacao_saida = Transacao(
                tipo="Transferência enviada",
                valor=valor,
                conta_id=conta_origem.id,
                descricao=(
                    f"Enviado para "
                    f"{cliente_destino.nome}"
                )
            )

            # Histórico de quem recebeu
            transacao_entrada = Transacao(
                tipo="Transferência recebida",
                valor=valor,
                conta_id=conta_destino.id,
                descricao=(
                    f"Recebido de "
                    f"{cliente_origem.nome}"
                )
            )

            db.session.add(
                transacao_saida
            )

            db.session.add(
                transacao_entrada
            )

            db.session.commit()

            return render_template(
                "sucesso.html",
                mensagem=(
                    f"Transferência de "
                    f"R$ {valor:.2f} "
                    f"realizada com sucesso!"
                )
            )

        except ValueError as erro:

            db.session.rollback()

            flash(str(erro))

    return render_template(
        "transferir.html",
        conta=conta_origem
    )

# ---------------------------------------------------
# EXTRATO
# ---------------------------------------------------
@conta_bp.route("/extrato")
def extrato():

    if "usuario" not in session:
        return redirect(
            url_for("auth.login")
        )

    cliente_id = session["usuario"]

    cliente = Cliente.query.get(
        cliente_id
    )

    conta = Conta.query.filter_by(
        cliente_id=cliente_id
    ).first()

    if not conta:

        flash("Conta não encontrada.")

        return redirect(
            url_for("auth.home")
        )

    # -----------------------------------------
    # GERA OS ÚLTIMOS 12 MESES DINAMICAMENTE
    # -----------------------------------------

    hoje = datetime.now()

    nomes_meses = [
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Out",
        "Nov",
        "Dez"
    ]

    meses = []

    ano = hoje.year
    mes = hoje.month

    for _ in range(12):

        meses.append({
            "valor": f"{ano}-{mes:02d}",
            "nome": f"{nomes_meses[mes - 1]}/{str(ano)[2:]}"
        })

        mes -= 1

        if mes == 0:
            mes = 12
            ano -= 1


    # -----------------------------------------
    # MÊS SELECIONADO
    # -----------------------------------------

    periodo = request.args.get(
        "periodo"
    )

    # Se nenhum mês foi informado,
    # usa o mês atual
    if not periodo:
        periodo = meses[0]["valor"]


    ano_selecionado, mes_selecionado = map(
        int,
        periodo.split("-")
    )


    # -----------------------------------------
    # INÍCIO E FIM DO MÊS
    # -----------------------------------------

    inicio = datetime(
        ano_selecionado,
        mes_selecionado,
        1
    )

    if mes_selecionado == 12:

        fim = datetime(
            ano_selecionado + 1,
            1,
            1
        )

    else:

        fim = datetime(
            ano_selecionado,
            mes_selecionado + 1,
            1
        )


    # -----------------------------------------
    # BUSCA AS TRANSAÇÕES
    # -----------------------------------------

    transacoes = Transacao.query.filter(
        Transacao.conta_id == conta.id,
        Transacao.data >= inicio,
        Transacao.data < fim
    ).order_by(
        Transacao.data.desc()
    ).all()


    return render_template(
        "extrato.html",
        cliente=cliente,
        conta=conta,
        transacoes=transacoes,
        meses=meses,
        periodo_selecionado=periodo
    )