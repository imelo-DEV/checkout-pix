from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
import base64
import os

app = Flask(__name__, static_folder="static", template_folder="templates")

# Configurações da BlackCat via variáveis de ambiente
API_URL = 'https://api.blackcatpagamentos.com/v1/transactions'
PUBLIC_KEY = os.environ.get('PUBLIC_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')

# Validação das chaves
if not PUBLIC_KEY or not SECRET_KEY:
    raise Exception("As variáveis de ambiente PUBLIC_KEY e SECRET_KEY precisam estar definidas.")

# Credenciais base64
credentials = f"{PUBLIC_KEY}:{SECRET_KEY}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    'Authorization': f'Basic {encoded_credentials}',
    'Content-Type': 'application/json'
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/create_pix", methods=["POST"])
def create_pix():
    try:
        data = request.json
        print("[DEBUG] Payload recebido:", data)

        amount = int(data['amount'])
        if amount <= 0:
            return jsonify({"error": "Valor inválido"}), 400

        payload = {
            "amount": amount,
            "currency": "BRL",
            "paymentMethod": "pix",
            "externalRef": f"pedido-{data['docNumber']}",
            "items": [
                {
                    "title": "Compra via Checkout Pix",
                    "quantity": 1,
                    "tangible": True,
                    "unitPrice": amount,
                    "externalRef": "item-001"
                }
            ],
            "customer": {
                "name": data['name'],
                "email": data['email'],
                "document": {
                    "type": data['docType'],
                    "number": data['docNumber']
                }
            },
            "postbackUrl": "https://webhook.seudominio.com/pix"
        }

        print("[DEBUG] Enviando para BlackCat:", payload)
        response = requests.post(API_URL, json=payload, headers=headers)
        print("[DEBUG] Status code:", response.status_code)
        print("[DEBUG] Resposta BlackCat:", response.text)

        response.raise_for_status()
        resp_json = response.json()

        pix_payload = resp_json.get('pix', {}).get('qrcode')
        payment_url = resp_json.get('secureUrl') or f"https://pagamento.exemplo.com/pagar/{resp_json.get('secureId')}"

        return jsonify({
            "pixPayload": pix_payload,
            "paymentUrl": payment_url
        })

    except Exception as e:
        print("[ERRO] Exception:", str(e))
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
