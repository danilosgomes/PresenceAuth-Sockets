import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

TCP_PORT_LOCAL = 60000
UDP_PORT = 50000
NGROK_HOST_PADRAO = "0.tcp.sa.ngrok.io" 

def conectar_e_enviar(ip_destino, porta_destino):
    
    matricula = entry_matr.get()
    token = entry_token.get()

    if not matricula or not token:
        messagebox.showwarning("Campos Vazios", "Preencha sua Matrícula e o Token da aula antes de conectar.")
        return

    lbl_status.config(text=f"Conectando a {ip_destino}:{porta_destino}", fg="orange")
    root.update()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            
            try:
                s.connect((ip_destino, int(porta_destino)))
            except socket.timeout:
                messagebox.showerror("Tempo Esgotado", 
                    f"Não consegui conectar em:\n{ip_destino}:{porta_destino}\n\n"
                    "Verifique:\n1. Se o endereço/porta estão corretos.\n2. Se sua internet está funcionando.")
                return
            except socket.gaierror:
                messagebox.showerror("Endereço Inválido", "Não consegui encontrar esse servidor.\nO endereço do Ngrok pode estar errado.")
                return
            except ConnectionRefusedError:
                messagebox.showerror("Servidor Fechado", "O computador foi encontrado, mas o programa do professor não está aceitando conexões.")
                return
            
            s.settimeout(None) 
            mensagem = f"{matricula},{token}"
            s.sendall(mensagem.encode('utf-8'))
            
            resposta = s.recv(1024).decode('utf-8')
            
            if "Olá" in resposta or "Confirmada" in resposta or "AVISO" in resposta:
                messagebox.showinfo("Sucesso", resposta)
                lbl_status.config(text="Resposta Recebida!", fg="blue")
            else:
                messagebox.showerror("Erro de Validação", resposta)
                lbl_status.config(text="Erro na validação", fg="red")
                
    except Exception as e:
        messagebox.showerror("Erro Desconhecido", f"Ocorreu um erro técnico: {str(e)}")
        lbl_status.config(text="Erro técnico", fg="red")


def acao_enviar_local():

    ip = entry_ip_local.get()
    if not ip:
        messagebox.showwarning("Atenção", "O IP do servidor não foi encontrado.\nClique na lupa ou digite manualmente.")
        return
    
    conectar_e_enviar(ip, TCP_PORT_LOCAL)

def acao_enviar_remoto():

    porta = entry_porta_ngrok.get()
    host = entry_host_ngrok.get() 
    
    if not porta.isdigit():
        messagebox.showerror("Erro", "A porta deve conter apenas números.")
        return
    
    if not host:
        messagebox.showerror("Erro", "O endereço do Ngrok não pode estar vazio.")
        return

    conectar_e_enviar(host, porta)

def descobrir_ip_udp():
    """ O Radar Local """
    lbl_status.config(text="Escaneando rede local...", fg="orange")
    entry_ip_local.delete(0, tk.END)
    root.update()
    
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(2.0)
    
    try:
        udp.sendto("connect with me".encode('utf-8'), ('255.255.255.255', UDP_PORT))
        data, addr = udp.recvfrom(1024)
        
        if data.decode('utf-8') == "ok":
            ip_encontrado = addr[0]
            entry_ip_local.insert(0, ip_encontrado)
            lbl_status.config(text=f"Servidor Local: {ip_encontrado}", fg="green")
        else:
            lbl_status.config(text="Resposta estranha recebida.", fg="red")
            
    except socket.timeout:
        lbl_status.config(text="Servidor local não encontrado.", fg="red")
    except Exception as e:
        lbl_status.config(text=f"Erro no radar: {e}", fg="red")
    finally:
        udp.close()

root = tk.Tk()
root.title("Portal do Aluno - Híbrido")
root.geometry("400x480")
root.resizable(False, False)

frame_topo = tk.Frame(root, pady=10, padx=10)
frame_topo.pack(fill="x")

tk.Label(frame_topo, text="1. Seus Dados", font=("Arial", 10, "bold")).pack(anchor="w")

tk.Label(frame_topo, text="Sua Matrícula:").pack(anchor="w")
entry_matr = tk.Entry(frame_topo)
entry_matr.pack(fill="x")

tk.Label(frame_topo, text="Token da Aula:").pack(anchor="w")
entry_token = tk.Entry(frame_topo, justify="center", font=("Arial", 12))
entry_token.pack(fill="x")

tk.Label(root, text="2. Escolha como conectar", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(15,0))

abas = ttk.Notebook(root)
abas.pack(expand=True, fill="both", padx=10, pady=5)

tab_local = tk.Frame(abas)
abas.add(tab_local, text="IP (LAN)")

tk.Label(tab_local, text="Conexão Automática").pack(pady=10)

frame_scan = tk.Frame(tab_local)
frame_scan.pack()

tk.Label(frame_scan, text="IP Local:").pack(side=tk.LEFT)
entry_ip_local = tk.Entry(frame_scan, width=15)
entry_ip_local.pack(side=tk.LEFT, padx=5)
btn_scan = tk.Button(frame_scan, text="Buscar", command=lambda: threading.Thread(target=descobrir_ip_udp).start())
btn_scan.pack(side=tk.LEFT)

tk.Button(tab_local, text="CONFIRMAR PRESENÇA", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), 
          command=acao_enviar_local).pack(pady=20, fill="x", padx=20)

tab_remoto = tk.Frame(abas)
abas.add(tab_remoto, text="NGROK (WAN)")

tk.Label(tab_remoto, text="Conexão via Túnel").pack(pady=10)

tk.Label(tab_remoto, text="Endereço Base:").pack()
entry_host_ngrok = tk.Entry(tab_remoto, justify="center", width=30)
entry_host_ngrok.insert(0, NGROK_HOST_PADRAO)
entry_host_ngrok.pack()

tk.Label(tab_remoto, text="Porta:", font=("Arial", 9, "bold")).pack(pady=(10,0))
entry_porta_ngrok = tk.Entry(tab_remoto, justify="center", font=("Arial", 14), width=10)
entry_porta_ngrok.pack(pady=5)

tk.Button(tab_remoto, text="CONFIRMAR PRESENÇA", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), 
          command=acao_enviar_remoto).pack(pady=10, fill="x", padx=20)

lbl_status = tk.Label(root, text="Pronto.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
lbl_status.pack(side=tk.BOTTOM, fill=tk.X)

threading.Thread(target=descobrir_ip_udp, daemon=True).start()

root.mainloop()