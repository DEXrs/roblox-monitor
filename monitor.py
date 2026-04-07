#!/usr/bin/env python3
import requests
import time
import json
import os
from datetime import datetime
import sys

# Configurações
USERNAME = "RafaelaBR672"
USER_ID = 2501301843
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:3000' )
MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', 300))  # 5 minutos em segundos
STATE_FILE = '/tmp/roblox_state.json'

def log_message(message):
    """Log com timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def get_user_presence(user_id):
    """Obter status de presença do usuário via API Roblox"""
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": [user_id]}
    try:
        response = requests.post(url, json=payload, timeout=10 )
        if response.status_code == 200:
            data = response.json()
            if data.get('userPresences'):
                return data['userPresences'][0]
    except Exception as e:
        log_message(f"Erro ao acessar API Roblox: {e}")
    return None

def read_last_state():
    """Ler o último estado salvo"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log_message(f"Erro ao ler estado: {e}")
    return {'presence_type': None}

def save_state(state):
    """Salvar o estado atual"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        log_message(f"Erro ao salvar estado: {e}")

def send_to_backend(endpoint, data):
    """Enviar dados para o backend"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            return True
        else:
            log_message(f"Erro ao enviar para {endpoint}: {response.status_code}")
    except Exception as e:
        log_message(f"Erro ao conectar ao backend: {e}")
    return False

def monitor_user():
    """Monitorar o usuário e registrar mudanças"""
    log_message("Iniciando monitoramento...")
    
    while True:
        try:
            presence = get_user_presence(USER_ID)
            
            if presence:
                current_presence_type = presence.get('userPresenceType', 0)
                last_state = read_last_state()
                last_presence_type = last_state.get('presence_type')
                
                # Status map
                status_map = {
                    0: 'Offline',
                    1: 'Online',
                    2: 'No Jogo',
                    3: 'No Studio'
                }
                current_status = status_map.get(current_presence_type, 'Desconhecido')
                
                # Atualizar estado no backend
                send_to_backend('/api/status', {
                    'presence_type': current_presence_type
                })
                
                # Verificar mudança de status
                if current_presence_type != last_presence_type:
                    log_message(f"Mudança detectada: {current_status}")
                    
                    # Determinar tipo de evento
                    if current_presence_type == 0:
                        event = 'Saída'
                    elif last_presence_type == 0 or last_presence_type is None:
                        event = 'Entrada'
                    else:
                        event = 'Mudança de Atividade'
                    
                    # Registrar evento
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    send_to_backend('/api/activity-log', {
                        'data_hora': now,
                        'evento': event,
                        'status': current_status
                    })
                    
                    # Salvar novo estado
                    save_state({'presence_type': current_presence_type})
                else:
                    log_message(f"Status: {current_status} (sem mudanças)")
            else:
                log_message("Não foi possível obter o status do usuário")
            
            # Aguardar antes de próxima verificação
            log_message(f"Próxima verificação em {MONITOR_INTERVAL} segundos...")
            time.sleep(MONITOR_INTERVAL)
            
        except KeyboardInterrupt:
            log_message("Monitoramento interrompido pelo usuário")
            break
        except Exception as e:
            log_message(f"Erro no loop de monitoramento: {e}")
            time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    log_message(f"Monitorando usuário: {USERNAME} (ID: {USER_ID})")
    log_message(f"Backend URL: {BACKEND_URL}")
    log_message(f"Intervalo de monitoramento: {MONITOR_INTERVAL} segundos")
    monitor_user()
