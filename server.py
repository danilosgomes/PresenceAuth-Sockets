<<<<<<< HEAD
import socket

# Configurações
HOST = '0.0.0.0'  # 0.0.0.0 permite conexões de outros PCs
PORT = 65432      # Porta que vamos escutar (acima de 1024)

print(f"[*] Iniciando servidor em {HOST}:{PORT}")

# Criação do Socket TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("[*] Aguardando conexão...")
    
    # O código para aqui até alguém conectar
    conn, addr = s.accept()
    
    with conn:
        print(f"[*] Conectado por: {addr}")
        while True:
            # Recebe dados (max 1024 bytes)
            data = conn.recv(1024)
            if not data:
                break
            
            mensagem = data.decode('utf-8')
            print(f"[*] Recebido: {mensagem}")
            
            # Responde ao cliente
=======
import socket

# Configurações
HOST = '0.0.0.0'  # 0.0.0.0 permite conexões de outros PCs
PORT = 65432      # Porta que vamos escutar (acima de 1024)

print(f"[*] Iniciando servidor em {HOST}:{PORT}")

# Criação do Socket TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("[*] Aguardando conexão...")
    
    # O código para aqui até alguém conectar
    conn, addr = s.accept()
    
    with conn:
        print(f"[*] Conectado por: {addr}")
        while True:
            # Recebe dados (max 1024 bytes)
            data = conn.recv(1024)
            if not data:
                break
            
            mensagem = data.decode('utf-8')
            print(f"[*] Recebido: {mensagem}")
            
            # Responde ao cliente
>>>>>>> be481868f1c041cd493071f00ca18d8fc6766f33
            conn.sendall(b"Recebido pelo servidor!")