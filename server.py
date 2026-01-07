import socket

HOST = '0.0.0.0'
PORT = 65432

# --- Função para carregar alunos ---
def carregar_alunos():
    alunos = {}
    try:
        with open('alunos.txt', 'r', encoding='utf-8') as f:
            for linha in f:
                partes = linha.strip().split(',')
                if len(partes) == 2:
                    matricula = partes[0].strip()
                    nome = partes[1].strip()
                    alunos[matricula] = nome
        print(f"[*] Banco de dados carregado: {len(alunos)} alunos.")
        return alunos
    except FileNotFoundError:
        print("[!] ERRO: Arquivo alunos.txt não encontrado!")
        return {}

# --- Início do Programa ---
alunos_validos = carregar_alunos()

print(f"[*] Iniciando servidor em {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("[*] Aguardando conexões...")
    
    while True: # Loop infinito para aceitar vários alunos (um por vez por enquanto)
        conn, addr = s.accept()
        with conn:
            print(f"[*] Conexão recebida de: {addr}")
            
            data = conn.recv(1024)
            if not data:
                continue
            
            # O cliente vai mandar apenas a MATRICULA por enquanto
            matricula_recebida = data.decode('utf-8').strip()
            print(f"[*] Tentativa de registro da matrícula: {matricula_recebida}")
            
            # --- AQUI ACONTECE A MÁGICA ---
            if matricula_recebida in alunos_validos:
                nome_aluno = alunos_validos[matricula_recebida]
                print(f"[V] SUCESSO: Aluno {nome_aluno} registrado!")
                msg_resposta = f"Ola {nome_aluno}, presenca registrada!"
                conn.sendall(msg_resposta.encode('utf-8'))
            else:
                print(f"[X] FALHA: Matrícula {matricula_recebida} não existe.")
                conn.sendall(b"ERRO: Matricula nao encontrada.")