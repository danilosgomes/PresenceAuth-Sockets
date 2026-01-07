import socket

# Como você está testando no mesmo PC, use '127.0.0.1' (localhost).
# Se for testar em PCs diferentes, coloque o IP do PC do Servidor aqui.
HOST = '127.0.0.1' 
PORT = 65432

print(f"[*] Tentando conectar a {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    # Envia a mensagem
    # Teste com uma matrícula válida
    s.sendall(b"1001")
    
    # Espera resposta
    data = s.recv(1024)

print(f"[*] Resposta do servidor: {data.decode('utf-8')}")