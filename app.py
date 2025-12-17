from flask import Flask, request, render_template_string
from decimal import Decimal, ROUND_HALF_UP, getcontext
import os

getcontext().prec = 28

app = Flask(__name__)

# ===== REGRAS SHOPEE =====
MARGEM = Decimal("0.15")
IMPOSTO = Decimal("0.09")
COMISSAO_PCT = Decimal("0.20")
TETO_COMISSAO = Decimal("100.00")
TAXA_FIXA = Decimal("4.00")

DESCONTO_PROMO = Decimal("0.10")
DESCONTO_CUPOM = Decimal("0.10")
FATOR_DESCONTO = (Decimal("1") - DESCONTO_PROMO) * (Decimal("1") - DESCONTO_CUPOM)

# ===== CÁLCULO =====
def calcular(custo):
    custo = Decimal(str(custo).replace(",", "."))

    preco_final_pct = (custo + TAXA_FIXA) / (
        Decimal("1") - COMISSAO_PCT - IMPOSTO - MARGEM
    )

    if (preco_final_pct * COMISSAO_PCT) <= TETO_COMISSAO:
        preco_final = preco_final_pct
    else:
        preco_final = (custo + TAXA_FIXA + TETO_COMISSAO) / (
            Decimal("1") - IMPOSTO - MARGEM
        )

    preco_final = preco_final.quantize(Decimal("0.01"), ROUND_HALF_UP)
    lucro = (preco_final * MARGEM).quantize(Decimal("0.01"), ROUND_HALF_UP)
    preco_cadastro = (preco_final / FATOR_DESCONTO).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )

    return preco_cadastro, preco_final, lucro

# ===== HTML =====
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Calculadora Shopee</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        input, button { padding: 8px; font-size: 16px; }
        .box { margin-top: 20px; }
    </style>
</head>
<body>
    <h2>Calculadora de Preço Shopee</h2>

    <form method="post">
        <label>Custo do produto:</label><br><br>
        <input name="custo" required>
        <br><br>
        <button type="submit">Calcular</button>
    </form>

    {% if resultado %}
    <div class="box">
        <p><strong>Preço para cadastrar:</strong> R$ {{ resultado[0] }}</p>
        <p><strong>Preço final cliente:</strong> R$ {{ resultado[1] }}</p>
        <p><strong>Lucro:</strong> R$ {{ resultado[2] }}</p>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        custo = request.form["custo"]
        preco_cad, preco_final, lucro = calcular(custo)
        resultado = (
            f"{preco_cad:.2f}".replace(".", ","),
            f"{preco_final:.2f}".replace(".", ","),
            f"{lucro:.2f}".replace(".", ",")
        )
    return render_template_string(HTML, resultado=resultado)

# ===== START CORRETO PARA RENDER =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import jsonify, request

@app.route("/api/calcular", methods=["GET"])
def api_calcular():
    try:
        custo = request.args.get("custo")

        if not custo:
            return jsonify({"erro": "custo_nao_informado"}), 400

        custo = Decimal(str(custo).replace(",", "."))

        preco_cadastro, preco_final, lucro = calcular(custo)

        return jsonify({
            "preco_cadastro": float(preco_cadastro),
            "preco_final": float(preco_final),
            "lucro": float(lucro)
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
