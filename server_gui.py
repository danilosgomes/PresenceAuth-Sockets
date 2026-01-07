import socket
import threading
import random
import string
import tkinter as tk
from tkinter import messagebox, ttk

# --- CONFIGURAÇÕES ---
HOST = '0.0.0.0'
TCP_PORT = 65432
UDP_PORT = 50000

# Variáveis Globais
alunos_validos = {}     # Dicionário lido do arquivo
presencas_confirmadas = [] # Lista de matrículas que já marcaram presença
token_atual = "----"

# --- LÓGICA DE REDE (Igual ao Dia 4, mas adaptada para GUI) ---

def carregar_alunos():
    global alunos_validos
    try:
        with open('alunos.txt', 'r', encoding='utf-8') as f:
            for linha in f:
                partes = linha.strip().split(',')
                if len(partes) == 2: alunos_validos[partes[0].strip()] = partes[1].strip()
        return True
    except FileNotFoundError: return False

def gerar_novo_token():
    global token_atual
    token_atual = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    lbl_token_valor.config(text=token_atual) # Atualiza na tela
    log_msg(f"Novo Token Gerado: {token_atual}")

def escutar_udp():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp.bind(('0.0.0.0', UDP_PORT))
        while True:
            msg, addr = udp.recvfrom(1024)
            if msg.decode('utf-8').strip() == "ONDE_ESTA_O_PROFESSOR?":
                udp.sendto(b"ESTOU_AQUI", addr)
    except: pass

def iniciar_servidor_tcp():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, TCP_PORT))
        s.listen()
        log_msg(f"Servidor ouvindo na porta {TCP_PORT}...")
        
        while True:
            conn, addr = s.accept()
            threading.Thread(target=tratar_cliente, args=(conn, addr)).start()

def tratar_cliente(conn, addr):
    with conn:
        try:
            data = conn.recv(1024)
            if not data: return
            msg = data.decode('utf-8').strip().split(',')
            
            if len(msg) == 2:
                matr, token_recebido = msg
                
                # Validações
                if token_recebido != token_atual:
                    conn.sendall(b"ERRO: Token invalido.")
                    return
                
                if matr not in alunos_validos:
                    conn.sendall(b"ERRO: Matricula nao encontrada.")
                    return

                # Sucesso
                nome = alunos_validos[matr]
                
                # Verifica duplicidade
                if matr not in [p['matr'] for p in presencas_confirmadas]:
                    presencas_confirmadas.append({'matr': matr, 'nome': nome, 'ip': addr[0]})
                    atualizar_lista_visual()
                    conn.sendall(f"Ola {nome}, Presenca Confirmada!".encode('utf-8'))
                    log_msg(f"Presença: {nome} ({matr})")
                else:
                    conn.sendall(b"AVISO: Voce ja registrou presenca.")
            else:
                conn.sendall(b"ERRO: Formato invalido.")
        except Exception as e:
            print(e)

# --- INTERFACE GRÁFICA (GUI) ---

def log_msg(texto):
    txt_log.insert(tk.END, texto + "\n")
    txt_log.see(tk.END)

def atualizar_lista_visual():
    # Limpa a lista e recria
    lista_presenca.delete(*lista_presenca.get_children())
    for p in presencas_confirmadas:
        lista_presenca.insert("", tk.END, values=(p['matr'], p['nome'], p['ip']))

def revogar_presenca():
    # Pega o item selecionado na tabela
    selecionado = lista_presenca.selection()
    if not selecionado:
        messagebox.showwarning("Atenção", "Selecione um aluno na lista para revogar.")
        return
    
    # Pega os dados da linha selecionada
    item = lista_presenca.item(selecionado)
    matricula_alvo = str(item['values'][0]) # Precisamos da matrícula para a lógica (excluir o certo)
    nome_alvo = item['values'][1]           # Pegamos o NOME para mostrar na mensagem
    
    # Filtra a lista removendo o aluno (Usamos a matrícula para garantir que é o aluno único)
    global presencas_confirmadas
    presencas_confirmadas = [p for p in presencas_confirmadas if str(p['matr']) != matricula_alvo]
    
    # Atualiza a tela
    atualizar_lista_visual()
    
    # Mostra o NOME no log e no pop-up
    log_msg(f"REVOGADO: {nome_alvo} (Matr: {matricula_alvo})")
    messagebox.showinfo("Sucesso", f"A presença de {nome_alvo} foi removida.")

# Configuração da Janela
root = tk.Tk()
root.title("PresenceAuth - Painel do Professor")
root.geometry("600x500")

# Carrega alunos ao abrir
if carregar_alunos():
    lbl_status = tk.Label(root, text=f"Banco carregado: {len(alunos_validos)} alunos.", fg="green")
else:
    lbl_status = tk.Label(root, text="ERRO: alunos.txt não encontrado!", fg="red")
lbl_status.pack()

# Área do Token
frame_token = tk.Frame(root, pady=10)
frame_token.pack()
tk.Label(frame_token, text="Token da Aula:", font=("Arial", 12)).pack(side=tk.LEFT)
lbl_token_valor = tk.Label(frame_token, text="----", font=("Arial", 20, "bold"), fg="blue")
lbl_token_valor.pack(side=tk.LEFT, padx=10)
tk.Button(frame_token, text="Gerar Novo Token", command=gerar_novo_token).pack(side=tk.LEFT)

# Tabela de Presenças
cols = ('Matrícula', 'Nome', 'IP')
lista_presenca = ttk.Treeview(root, columns=cols, show='headings')
for col in cols: 
    lista_presenca.heading(col, text=col)
    lista_presenca.column(col, width=150)
lista_presenca.pack(expand=True, fill='both', padx=10)

# Botão Revogar
btn_revogar = tk.Button(root, text="REVOGAR PRESENÇA", bg="red", fg="white", command=revogar_presenca)
btn_revogar.pack(pady=5)

# Log do Sistema
tk.Label(root, text="Log do Sistema:").pack(anchor='w', padx=10)
txt_log = tk.Text(root, height=8)
txt_log.pack(fill='x', padx=10, pady=5)

# --- INICIALIZAÇÃO DAS THREADS ---
# Inicia as redes em threads para não travar a janela
t_tcp = threading.Thread(target=iniciar_servidor_tcp, daemon=True)
t_tcp.start()

t_udp = threading.Thread(target=escutar_udp, daemon=True)
t_udp.start()

# Inicia o Token
gerar_novo_token()

# Inicia a Janela (Loop Principal)
root.mainloop()