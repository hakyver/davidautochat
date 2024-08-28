# views.py
import json
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from .utils import get_history_parse, handle_history, get_current_date, generate_timer, get_current_calendar
from .ai_service import AIService
from .layers import conversational_layer, main_layer

# Configuración de la API de WhatsApp
WHATSAPP_TOKEN = config('WHATSAPP_TOKEN')
WHATSAPP_PHONE_NUMBER = config('WHATSAPP_PHONE_NUMBER')
API_URL = f"https://graph.facebook.com/v12.0/{WHATSAPP_PHONE_NUMBER}/messages"

# Función para enviar un mensaje de WhatsApp
def send_whatsapp_message(to, message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {WHATSAPP_TOKEN}'
    }
    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {'body': message}
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    return response.json()

# Vista para manejar el envío de mensajes
@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            to = data.get('to')
            message = data.get('message')
            
            if not to or not message:
                return JsonResponse({"error": "Faltan parámetros 'to' o 'message'"}, status=400)
            
            response = send_whatsapp_message(to, message)
            return JsonResponse(response)
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=500)
    return JsonResponse({"error": "Solicitud inválida"}, status=400)

# Prompts
PROMPT_SCHEDULE = """
... (contenido omitido para brevedad)
"""

PROMPT_SELLER = """
... (contenido omitido para brevedad)
"""

# Generar prompts
def generate_prompt(template, summary, history):
    now_date = get_current_date()
    return template.replace('{AGENDA_ACTUAL}', summary).replace('{HISTORIAL_CONVERSACION}', history).replace('{CURRENT_DAY}', now_date)

# Función principal para manejar el flujo
@csrf_exempt
def handle_flow(request, prompt_template):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            state = request.session.get('state', {})
            history = get_history_parse(state)
            summary = ', '.join(get_current_calendar()) if prompt_template == PROMPT_SCHEDULE else 'ninguna'
            prompt = generate_prompt(prompt_template, summary, history)

            ai = AIService(api_key='YOUR_OPENAI_API_KEY', model='gpt-3.5-turbo-16k')
            text = ai.create_chat([
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': f"Cliente pregunta: {data.get('message')}"}
            ], 'gpt-4')

            handle_history({'content': text, 'role': 'assistant'}, state)

            chunks = text.split('. ')
            responses = [{'body': chunk.strip(), 'delay': generate_timer(150, 250)} for chunk in chunks]

            return JsonResponse({"responses": responses})
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=500)
    return JsonResponse({"error": "Solicitud inválida"}, status=400)

# Vistas para manejar los diferentes flujos
@csrf_exempt
def flow_schedule(request):
    return handle_flow(request, PROMPT_SCHEDULE)

@csrf_exempt
def flow_seller(request):
    return handle_flow(request, PROMPT_SELLER)

@csrf_exempt
def welcome_flow(request):
    if request.method == 'POST':
        try:
            state = request.session.get('state', {})
            conversational_response = conversational_layer(state)
            main_response = main_layer(state)
            
            return JsonResponse({
                "responses": [
                    {"body": conversational_response, "delay": 0},
                    {"body": main_response, "delay": 0}
                ]
            })
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=500)
    return JsonResponse({"error": "Solicitud inválida"}, status=400)

@csrf_exempt
def flow_confirm(request):
    response = "Confirmando tu cita... Por favor, espera un momento."
    return JsonResponse({"response": response})

VERIFY_TOKEN = config('VERIFY_TOKEN')

@csrf_exempt
def handle_intent(request):
    if request.method == 'GET':
        # Verificación del Webhook
        token_sent = request.GET.get('hub.verify_token')
        if token_sent == VERIFY_TOKEN:
            return HttpResponse(request.GET.get('hub.challenge'))
        return HttpResponse('Token de verificación incorrecto', status=403)

    elif request.method == 'POST':
        try:
            # Procesar el mensaje recibido
            data = json.loads(request.body)
            if 'entry' in data and data['entry'][0]['changes'][0]['value']:
                message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
                message_text = message_data['text']['body']  # El texto del mensaje enviado por el usuario
                sender_id = message_data['from']  # El número de WhatsApp del usuario
                
                # Manejo de la conversación
                state = request.session.get('state', {})
                ai = AIService(api_key='YOUR_OPENAI_API_KEY', model='gpt-3.5-turbo-16k')
                history = get_history_parse(state)
                
                prompt = f"""
                Como una inteligencia artificial avanzada, tu tarea es analizar el contexto de una conversación y determinar cuál de las siguientes acciones es más apropiada para realizar:
                --------------------------------------------------------
                Historial de conversación:
                {history}
                
                Posibles acciones a realizar:
                1. AGENDAR: Esta acción se debe realizar cuando el cliente expresa su deseo de programar una cita.
                2. HABLAR: Esta acción se debe realizar cuando el cliente desea hacer una pregunta o necesita más información.
                3. CONFIRMAR: Esta acción se debe realizar cuando el cliente y el vendedor llegaron a un acuerdo mutuo proporcionando una fecha, día y hora exacta sin conflictos de hora.
                -----------------------------
                Tu objetivo es comprender la intención del cliente y seleccionar la acción más adecuada en respuesta a su declaración.
                
                Respuesta ideal (AGENDAR|HABLAR|CONFIRMAR):"""

                text = ai.create_chat([
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': f"Cliente pregunta: {message_text}"}
                ], 'gpt-4')

                # Determinar la acción a tomar
                if 'HABLAR' in text:
                    response = flow_seller(request)
                elif 'AGENDAR' in text:
                    response = flow_schedule(request)
                elif 'CONFIRMAR' in text:
                    response = flow_confirm(request)
                else:
                    response = JsonResponse({"error": "No se pudo determinar la acción adecuada."})

                return response
            else:
                return JsonResponse({"error": "Mensaje no válido"}, status=400)
        except Exception as err:
            return JsonResponse({"error": str(err)}, status=500)

    return JsonResponse({"error": "Solicitud inválida"}, status=400)

