import socket
import threading
import random
import string

# Configurações
HOST = '0.0.0.0'
TCP_PORT = 65432       # Porta para Presença (TCP)
UDP_PORT = 50000       # Porta para Descoberta (UDP) - O "Grito"

# --- Funções Auxiliares (Carregar Alunos / Gerar Token) ---
# (Mantenha igual ao dia anterior, só copiei o básico aqui pra não ficar gigante)
def carregar_alunos():
    alunos = {}
    try:
        with open('alunos.txt', 'r', encoding='utf-8') as f:
            for linha in f:
                partes = linha.strip().split(',')
                if len(partes) == 2: alunos[partes[0].strip()] = partes[1].strip()
        return alunos
    except FileNotFoundError: return {}

def gerar_token():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

# --- NOVA FUNÇÃO: O Ouvido do UDP ---
def escutar_broadcast():
    # Cria socket UDP
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('0.0.0.0', UDP_PORT))
    print(f"[*] Thread UDP iniciada. Escutando gritos na porta {UDP_PORT}...")
    
    while True:
        try:
            # Espera receber "ONDE_ESTA_O_PROFESSOR?"
            msg, cliente_addr = udp.recvfrom(1024)
            mensagem = msg.decode('utf-8').strip()
            
            if mensagem == "ONDE_ESTA_O_PROFESSOR?":
                print(f"[*] Broadcast recebido de {cliente_addr[0]}. Respondendo...")
                # Responde: "ESTOU_AQUI"
                udp.sendto(b"ESTOU_AQUI", cliente_addr)
        except Exception as e:
            print(f"[!] Erro no UDP: {e}")

# --- Início do Programa ---
alunos_validos = carregar_alunos()
token_atual = gerar_token()

print(f"==========================================")
print(f" SEGREDO DA AULA: {token_atual}")
print(f"==========================================")

# 1. Inicia o UDP em segundo plano (Thread)
thread_udp = threading.Thread(target=escutar_broadcast, daemon=True)
thread_udp.start()

# 2. Inicia o TCP principal (Bloqueia o terminal esperando alunos)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, TCP_PORT))
    s.listen()
    print(f"[*] Servidor TCP rodando na porta {TCP_PORT}")
    
    while True:
        conn, addr = s.accept()
        with conn:
            data = conn.recv(1024)
            if not data: continue
            try:
                msg = data.decode('utf-8').strip().split(',')
                if len(msg) == 2:
                    matr, token = msg
                    if token == token_atual and matr in alunos_validos:
                        print(f"[V] {alunos_validos[matr]} registrado!")
                        conn.sendall(f"Ola {alunos_validos[matr]}, SUCESSO!".encode('utf-8'))
                    else:
                        conn.sendall(b"ERRO: Dados invalidos.")
                else:
                    conn.sendall(b"ERRO: Formato incorreto.")
            except:
                continue