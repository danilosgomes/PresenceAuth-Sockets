import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

TCP_PORT = 60000
UDP_PORT = 50000

def descobrir_ip_servidor():
    
    lbl_status.config(text="Buscando servidor", fg="orange")
    root.update()
    
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(2.0)
    
    try:
        udp.sendto("connect with me", ('255.255.255.255', UDP_PORT))
        
        data, addr = udp.recvfrom(1024)
        if data.decode('utf-8') == "ok":
            ip_encontrado = addr[0]
            entry_ip.delete(0, tk.END)
            entry_ip.insert(0, ip_encontrado)
            lbl_status.config(text=f"Servidor encontrado: {ip_encontrado}", fg="green")
            return
            
    except socket.timeout:
        lbl_status.config(text="Servidor não encontrado automaticamente. Digite o IP.", fg="red")
    except Exception as e:
        lbl_status.config(text=f"Erro na busca: {str(e)}", fg="red")
    finally:
        udp.close()

def enviar_presenca():
    ip = entry_ip.get()
    matricula = entry_matr.get()
    token = entry_token.get()
    
    if not ip or not matricula or not token:
        messagebox.showwarning("Campos vazios", "Por favor, preencha todos os campos.")
        return
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2) 
            
            try:
                s.connect((ip, TCP_PORT))
            except socket.timeout:
                messagebox.showerror("IP incorreto ou inacessível", 
                    f"O sistema tentou conectar em '{ip}' mas não obteve resposta.\n"
                    "Verifique se:\n"
                    "1. O IP está digitado corretamente.\n"
                    "2. Você e o professor estão na mesma rede.")
                return
            except socket.gaierror:
                messagebox.showerror("IP inválido", "O formato do IP está errado.\nUse o formato numérico (ex: 192.168.0.10).")
                return
            except ConnectionRefusedError:
                messagebox.showerror("Servidor desligado", "Encontramos uma máquina com esse IP, porém pode ser que seja ou não do professor.\nCaso seja, peça para ele iniciar o servidor.")
                return
            
            s.settimeout(None) 

            mensagem = f"{matricula},{token}"
            s.sendall(mensagem.encode('utf-8'))
            
            resposta = s.recv(1024).decode('utf-8')
            
            if "SUCESSO" in resposta or "Ola" in resposta:
                messagebox.showinfo("Sucesso", resposta)
                lbl_status.config(text="Presença Registrada!", fg="blue")
            else:
                messagebox.showerror("Erro de Validação", resposta)
                
    except Exception as e:
        messagebox.showerror("Erro Desconhecido", f"Ocorreu um erro inesperado: {str(e)}")

# --- INTERFACE GRÁFICA (GUI) ---

root = tk.Tk()
root.title("Portal do Aluno - Chamada")
root.geometry("350x400")
root.resizable(False, False)

# Estilo e Título
tk.Label(root, text="Registrar Presença", font=("Arial", 16, "bold")).pack(pady=15)

# Campo IP (Preenchido auto, mas editável)
frame_ip = tk.Frame(root)
frame_ip.pack(pady=5)
tk.Label(frame_ip, text="IP do Professor:").pack(anchor="w")
entry_ip = tk.Entry(frame_ip, width=30)
entry_ip.pack(side=tk.LEFT)
# Botãozinho de "Re-scan" ao lado do IP
btn_scan = tk.Button(frame_ip, text="🔍", command=lambda: threading.Thread(target=descobrir_ip_servidor).start())
btn_scan.pack(side=tk.LEFT, padx=5)

# Campo Matrícula
tk.Label(root, text="Sua Matrícula:").pack(pady=(10, 0))
entry_matr = tk.Entry(root, width=35)
entry_matr.pack()

# Campo Token
tk.Label(root, text="Código da Sala (Token):").pack(pady=(10, 0))
entry_token = tk.Entry(root, width=15, font=("Arial", 14), justify='center')
entry_token.pack()

# Botão Principal
btn_enviar = tk.Button(root, text="CONFIRMAR PRESENÇA", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), height=2, width=25, command=enviar_presenca)
btn_enviar.pack(pady=25)

# Barra de Status (Rodapé)
lbl_status = tk.Label(root, text="Pronto.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
lbl_status.pack(side=tk.BOTTOM, fill=tk.X)

# --- INICIALIZAÇÃO ---

# Tenta descobrir o servidor assim que abre a janela (em uma thread para não travar)
threading.Thread(target=descobrir_ip_servidor, daemon=True).start()

root.mainloop()