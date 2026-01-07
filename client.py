import socket

# Configurações
UDP_PORT = 50000       # Tem que ser a mesma do servidor
TCP_PORT = 65432

def descobrir_servidor():
    print("[*] Procurando servidor na rede...")
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Permite enviar Broadcast
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(5.0) # Espera só 5 segundos, se não achar, desiste
    
    try:
        # Envia o grito para TODA a rede (255.255.255.255)
        mensagem = b"ONDE_ESTA_O_PROFESSOR?"
        udp.sendto(mensagem, ('255.255.255.255', UDP_PORT))
        
        # Espera resposta
        data, addr = udp.recvfrom(1024)
        if data.decode('utf-8') == "ESTOU_AQUI":
            ip_servidor = addr[0] # Pega o IP de quem respondeu
            print(f"[*] Servidor encontrado no IP: {ip_servidor}")
            return ip_servidor
            
    except socket.timeout:
        print("[!] Ninguem respondeu. O servidor esta ligado?")
        return None
    except Exception as e:
        print(f"[!] Erro: {e}")
        return None

# --- Início do Cliente ---
ip_servidor = descobrir_servidor()

if ip_servidor:
    # Se achou, segue o fluxo normal do Dia 3
    matricula = input("Digite sua Matricula: ")
    token = input("Digite o Codigo da Sala: ")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_servidor, TCP_PORT))
            s.sendall(f"{matricula},{token}".encode('utf-8'))
            resp = s.recv(1024)
            print(f"Resposta: {resp.decode('utf-8')}")
    except:
        print("[!] Erro ao conectar no TCP.")
else:
    print("[!] Nao foi possivel encontrar o servidor automaticamente.")
    # Aqui você poderia colocar um input manual como 'backup'