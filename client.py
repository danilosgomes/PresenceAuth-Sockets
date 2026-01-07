<<<<<<< HEAD
import socket

# Como você está testando no mesmo PC, use '127.0.0.1' (localhost).
# Se for testar em PCs diferentes, coloque o IP do PC do Servidor aqui.
HOST = '127.0.0.1' 
PORT = 65432

print(f"[*] Tentando conectar a {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    # Envia a mensagem
    s.sendall(b"Ola Servidor, sou o Danilo!")
    
    # Espera resposta
    data = s.recv(1024)

=======
import socket

# Como você está testando no mesmo PC, use '127.0.0.1' (localhost).
# Se for testar em PCs diferentes, coloque o IP do PC do Servidor aqui.
HOST = '127.0.0.1' 
PORT = 65432

print(f"[*] Tentando conectar a {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    # Envia a mensagem
    s.sendall(b"Ola Servidor, sou o Danilo!")
    
    # Espera resposta
    data = s.recv(1024)

>>>>>>> be481868f1c041cd493071f00ca18d8fc6766f33
print(f"[*] Resposta do servidor: {data.decode('utf-8')}")