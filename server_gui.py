import socket
import threading
import random
import string
import tkinter as tk
from tkinter import messagebox, ttk
import os
import csv
from datetime import datetime

HOST = '0.0.0.0'
TCP_PORT = 60000
UDP_PORT = 50000
ARQUIVO_MESTRE = "Frequencia_Geral.csv"

alunos_validos = {} 
presencas_confirmadas = []
token_atual = "----"

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
    token_atual = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
    lbl_token_valor.config(text=token_atual)
    log_msg(f"Novo Token Gerado: {token_atual}")

def obter_datas_disponiveis():
    datas = []
    hoje = datetime.now().strftime("%d-%m-%Y")
    datas.append(hoje)
    
    if os.path.exists(ARQUIVO_MESTRE):
        try:
            with open(ARQUIVO_MESTRE, 'r', encoding='utf-8') as f:
                leitor = csv.DictReader(f, delimiter=';')
                colunas = leitor.fieldnames
                
                for col in colunas:
                    if col not in ['Matricula', 'Nome do Aluno'] and col != hoje:
                        datas.append(col)
        except:
            pass
            
    return sorted(datas)

def carregar_presencas_da_data_selecionada(event=None):

    data_alvo = combo_datas.get()
    if not data_alvo:
        data_alvo = datetime.now().strftime("%d-%m-%Y")

    global presencas_confirmadas
    presencas_confirmadas = [] 
    lista_presenca.delete(*lista_presenca.get_children())
    
    if not os.path.exists(ARQUIVO_MESTRE):
        return

    try:
        count = 0
        with open(ARQUIVO_MESTRE, 'r', encoding='utf-8') as f:
            leitor = csv.DictReader(f, delimiter=';')
            
            if data_alvo not in leitor.fieldnames:
                log_msg(f"Data {data_alvo} não encontrada no arquivo.")
                return

            for linha in leitor:
                status = linha.get(data_alvo)
                matr = linha['Matricula']

                nome = linha.get('Nome do Aluno')

                if status == "PRESENCA":
                    presencas_confirmadas.append({
                        'matr': matr, 
                        'nome': nome, 
                        'ip': 'Salvo'
                    })
                    count += 1

        atualizar_lista_visual()
        log_msg(f"Visualizando data: {data_alvo} ({count} presentes)")
            
    except Exception as e:
        log_msg(f"Erro ao carregar data: {e}")

def escutar_udp():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp.bind((HOST, UDP_PORT))
        while True:
            msg, addr = udp.recvfrom(1024)
            if msg.decode('utf-8').strip() == "connect with me":
                udp.sendto(b"ok", addr)
    except: pass

def iniciar_servidor_tcp():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, TCP_PORT))
        s.listen()
        
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

                if token_recebido != token_atual:
                    conn.sendall("ERRO: Token inválido.")
                    return
                
                if matr not in alunos_validos:
                    conn.sendall("ERRO: Matricula não encontrada.")
                    return

                nome = alunos_validos[matr]
                
                if matr not in [p['matr'] for p in presencas_confirmadas]:
                    presencas_confirmadas.append({'matr': matr, 'nome': nome, 'ip': addr[0]})
                    atualizar_lista_visual()
                    conn.sendall("Olá {nome}, Presença Confirmada!".encode('utf-8'))
                    log_msg("Presença: {nome} ({matr})")
                else:
                    conn.sendall("AVISO: Voce já registrou sua presença.")
            else:
                conn.sendall("ERRO: Formato inválido.")
        except Exception as e:
            print(e)


# INTERFACE GRÁFICA

def log_msg(texto):
    txt_log.insert(tk.END, texto + "\n")
    txt_log.see(tk.END)

def atualizar_lista_visual():
    lista_presenca.delete(*lista_presenca.get_children())
    for p in presencas_confirmadas:
        lista_presenca.insert("", tk.END, values=(p['matr'], p['nome'], p['ip']))

def revogar_presenca():
    selecionado = lista_presenca.selection()
    if not selecionado:
        messagebox.showwarning("Atenção", "Selecione um aluno na lista para revogar.")
        return
    
    item = lista_presenca.item(selecionado)
    matricula_alvo = str(item['values'][0]) 
    nome_alvo = item['values'][1]

    global presencas_confirmadas
    presencas_confirmadas = [p for p in presencas_confirmadas if str(p['matr']) != matricula_alvo]
    
    atualizar_lista_visual()
    
    log_msg(f"REVOGADO: {nome_alvo} (Matr: {matricula_alvo})")
    messagebox.showinfo("Sucesso", f"A presença de {nome_alvo} foi removida.")

def exportar_relatorio():
    if not alunos_validos:
        messagebox.showerror("Erro", "Não há alunos carregados na base.")
        return

    data_hoje = datetime.now().strftime("%d-%m-%Y")
 
    historico_geral = {}
    cabecalhos = ['Matricula', 'Nome do Aluno']

    if os.path.exists(ARQUIVO_MESTRE):
        try:
            with open(ARQUIVO_MESTRE, mode='r', encoding='utf-8-sig') as f:
                leitor = csv.DictReader(f, delimiter=';')
                cabecalhos = leitor.fieldnames
                
                for linha in leitor:
                    matr = linha['Matricula']
                    historico_geral[matr] = linha
        except Exception as e:
            log_msg(f"Erro ao ler histórico: {e}")

    if data_hoje not in cabecalhos:
        cabecalhos.append(data_hoje)

    matriculas_presentes = [str(p['matr']) for p in presencas_confirmadas]

    registros_finais = []

    for matr, nome in alunos_validos.items():
        
        registro_aluno = historico_geral.get(matr, {'Matricula': matr, 'Nome do Aluno': nome})
        
        status = "AUSENCIA"
        if matr in matriculas_presentes:
            status = "PRESENCA"
        
        registro_aluno[data_hoje] = status
        
        registro_aluno['Nome do Aluno'] = nome
        
        registros_finais.append(registro_aluno)

    try:
        with open(ARQUIVO_MESTRE, mode='w', newline='', encoding='utf-8-sig') as f:
            escritor = csv.DictWriter(f, fieldnames=cabecalhos, delimiter=';')
            escritor.writeheader()
            escritor.writerows(registros_finais)
        
        log_msg(f"Planilha atualizada: Coluna {data_hoje}")
        messagebox.showinfo("Sucesso", f"Frequência salva em '{ARQUIVO_MESTRE}'!")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao salvar: {e}")

root = tk.Tk()
root.title("PresenceAuth - Painel do Professor")
root.geometry("500x700")

if carregar_alunos():
    lbl_status = tk.Label(root, text=f"Banco carregado: {len(alunos_validos)} alunos.", fg="green")
else:
    lbl_status = tk.Label(root, text="ERRO: alunos.txt não encontrado!", fg="red")
lbl_status.pack()

frame_token = tk.Frame(root, pady=10)
frame_token.pack()
tk.Label(frame_token, text="Token da Aula:", font=("Arial", 12)).pack(side=tk.LEFT)
lbl_token_valor = tk.Label(frame_token, text="----", font=("Arial", 20, "bold"), fg="blue")
lbl_token_valor.pack(side=tk.LEFT, padx=10)

tk.Button(frame_token, text="Gerar Novo Token", command=gerar_novo_token).pack(side=tk.LEFT)

frame_data = tk.Frame(root, pady=5)
frame_data.pack()

tk.Label(frame_data, text="Visualizar Frequência do dia: ").pack(side=tk.LEFT)

combo_datas = ttk.Combobox(frame_data, values=obter_datas_disponiveis(), state="readonly", width=15)
combo_datas.pack(side=tk.LEFT)

data_hoje_str = datetime.now().strftime("%d-%m-%Y")
combo_datas.set(data_hoje_str)

combo_datas.bind("<<ComboboxSelected>>", carregar_presencas_da_data_selecionada)

cols = ('Matrícula', 'Nome', 'IP')
lista_presenca = ttk.Treeview(root, columns=cols, show='headings')
for col in cols: 
    lista_presenca.heading(col, text=col)
    lista_presenca.column(col, width=150)
lista_presenca.pack(expand=True, fill='both', padx=10)

btn_revogar = tk.Button(root, text="REVOGAR PRESENÇA", bg="red", fg="white", command=revogar_presenca)
btn_revogar.pack(pady=5, fill='x', padx=20)

btn_csv = tk.Button(root, text="BAIXAR PLANILHA (.CSV)", bg="green", fg="white", font=("Arial", 10, "bold"), command=exportar_relatorio)
btn_csv.pack(pady=5, fill='x', padx=20) 

tk.Label(root, text="Log do Sistema:").pack(anchor='w', padx=10)
txt_log = tk.Text(root, height=8)
txt_log.pack(fill='x', padx=10, pady=5)

t_tcp = threading.Thread(target=iniciar_servidor_tcp, daemon=True)
t_tcp.start()

t_udp = threading.Thread(target=escutar_udp, daemon=True)
t_udp.start()

gerar_novo_token()

carregar_presencas_da_data_selecionada()

root.mainloop()