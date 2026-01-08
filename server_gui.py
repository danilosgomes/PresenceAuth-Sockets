import socket
import threading
import random
import string
import tkinter as tk
import os
from tkinter import messagebox, ttk
import csv
from datetime import datetime



# --- CONFIGURAÇÕES ---
HOST = '0.0.0.0'
TCP_PORT = 65432
UDP_PORT = 50000
ARQUIVO_MESTRE = "Frequencia_Geral.csv" # Nome fixo para o semestre todo

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

def obter_datas_disponiveis():
    """ Lê o cabeçalho do CSV para saber quais datas existem """
    datas = []
    # Adiciona HOJE como opção padrão sempre
    hoje = datetime.now().strftime("%d-%m-%Y")
    datas.append(hoje)
    
    if os.path.exists(ARQUIVO_MESTRE):
        try:
            with open(ARQUIVO_MESTRE, mode='r', encoding='utf-8-sig') as f:
                leitor = csv.DictReader(f, delimiter=';')
                colunas = leitor.fieldnames
                
                # Filtra tudo que NÃO é coluna fixa (Matricula, Nome, etc)
                for col in colunas:
                    if col not in ['Matricula', 'Nome', 'Nome do Aluno'] and col != hoje:
                        datas.append(col)
        except:
            pass
            
    return sorted(datas) # Retorna ordenado

def carregar_presencas_da_data_selecionada(event=None):
    """ Limpa a tela e carrega os dados da data escolhida no menu """
    
    # 1. Descobre qual data o usuário escolheu no menu
    data_alvo = combo_datas.get()
    if not data_alvo:
        data_alvo = datetime.now().strftime("%d-%m-%Y") # Fallback para hoje
    
    # 2. Limpa a memória RAM e a Tabela Visual (Reset)
    global presencas_confirmadas
    presencas_confirmadas = [] 
    lista_presenca.delete(*lista_presenca.get_children())
    
    if not os.path.exists(ARQUIVO_MESTRE):
        return

    try:
        count = 0
        with open(ARQUIVO_MESTRE, mode='r', encoding='utf-8-sig') as f:
            leitor = csv.DictReader(f, delimiter=';')
            
            # Se a data escolhida não existe no arquivo, não faz nada
            if data_alvo not in leitor.fieldnames:
                log_msg(f"Data {data_alvo} não encontrada no arquivo.")
                return

            for linha in leitor:
                status = linha.get(data_alvo)
                matr = linha['Matricula']
                
                # Tratamento para Nome ou Nome do Aluno (da correção anterior)
                nome = linha.get('Nome') or linha.get('Nome do Aluno') or "Desconhecido"

                if status == "PRESENCA":
                    presencas_confirmadas.append({
                        'matr': matr, 
                        'nome': nome, 
                        'ip': 'Arquivo CSV' # Indica que veio do histórico
                    })
                    count += 1
        
        # Atualiza a tabela visual com os dados carregados
        atualizar_lista_visual()
        log_msg(f"📅 Visualizando data: {data_alvo} ({count} presentes)")
            
    except Exception as e:
        log_msg(f"Erro ao carregar data: {e}")

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

def exportar_relatorio():
    if not alunos_validos:
        messagebox.showerror("Erro", "Não há alunos carregados na base.")
        return

    data_hoje = datetime.now().strftime("%d-%m-%Y")
    
    # Dicionário para guardar o histórico lido do arquivo
    # Estrutura: { '1001': {'Nome': 'Danilo', '01-01-2026': 'PRESENCA', ...} }
    historico_geral = {}
    cabecalhos = ['Matricula', 'Nome do Aluno']

    # --- PASSO 1: LER O ARQUIVO MESTRE (SE EXISTIR) ---
    if os.path.exists(ARQUIVO_MESTRE):
        try:
            with open(ARQUIVO_MESTRE, mode='r', encoding='utf-8-sig') as f:
                leitor = csv.DictReader(f, delimiter=';')
                cabecalhos = leitor.fieldnames # Recupera as datas antigas
                
                for linha in leitor:
                    matr = linha['Matricula']
                    historico_geral[matr] = linha
        except Exception as e:
            log_msg(f"Erro ao ler histórico: {e}")

    # --- PASSO 2: ADICIONAR COLUNA DE HOJE (SE NECESSÁRIO) ---
    if data_hoje not in cabecalhos:
        cabecalhos.append(data_hoje)

    # --- PASSO 3: ATUALIZAR/INSERIR DADOS DE HOJE ---
    # Cria conjunto de presentes para acesso rápido
    matriculas_presentes = [str(p['matr']) for p in presencas_confirmadas]

    registros_finais = []

    # Percorre a lista oficial de alunos (do txt) para garantir que todos apareçam
    for matr, nome in alunos_validos.items():
        # Pega o registro antigo desse aluno ou cria um novo vazio
        registro_aluno = historico_geral.get(matr, {'Matricula': matr, 'Nome do Aluno': nome})
        
        # Define o status de hoje
        status = "AUSENCIA"
        if matr in matriculas_presentes:
            status = "PRESENCA"
        
        # Atualiza a coluna de hoje
        registro_aluno[data_hoje] = status
        
        # Garante que o nome esteja atualizado (caso tenha mudado no txt)
        registro_aluno['Nome do Aluno'] = nome
        
        registros_finais.append(registro_aluno)

    # --- PASSO 4: SALVAR ARQUIVO ATUALIZADO ---
    try:
        with open(ARQUIVO_MESTRE, mode='w', newline='', encoding='utf-8-sig') as f:
            escritor = csv.DictWriter(f, fieldnames=cabecalhos, delimiter=';')
            escritor.writeheader()
            escritor.writerows(registros_finais)
        
        log_msg(f"Planilha atualizada: Coluna {data_hoje}")
        messagebox.showinfo("Sucesso", f"Frequência salva em '{ARQUIVO_MESTRE}'!")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao salvar: {e}")

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

# ... (código existente do frame_token) ...
tk.Button(frame_token, text="Gerar Novo Token", command=gerar_novo_token).pack(side=tk.LEFT)

# --- NOVO CÓDIGO: SELETOR DE DATAS ---
frame_data = tk.Frame(root, pady=5)
frame_data.pack()

tk.Label(frame_data, text="Visualizar Frequência do dia: ").pack(side=tk.LEFT)

# Cria a caixinha de seleção
combo_datas = ttk.Combobox(frame_data, values=obter_datas_disponiveis(), state="readonly", width=15)
combo_datas.pack(side=tk.LEFT)

# Seleciona o dia de hoje por padrão
data_hoje_str = datetime.now().strftime("%d-%m-%Y")
combo_datas.set(data_hoje_str)

# Quando o usuário mudar a data, chama a função de carregar
combo_datas.bind("<<ComboboxSelected>>", carregar_presencas_da_data_selecionada)
# -------------------------------------

# Tabela de Presenças
cols = ('Matrícula', 'Nome', 'IP')
lista_presenca = ttk.Treeview(root, columns=cols, show='headings')
for col in cols: 
    lista_presenca.heading(col, text=col)
    lista_presenca.column(col, width=150)
lista_presenca.pack(expand=True, fill='both', padx=10)

# Botão Revogar
btn_revogar = tk.Button(root, text="REVOGAR PRESENÇA", bg="red", fg="white", command=revogar_presenca)
btn_revogar.pack(pady=5, fill='x', padx=20)

# --- NOVO BOTÃO ---
btn_csv = tk.Button(root, text="BAIXAR PLANILHA (.CSV)", bg="green", fg="white", font=("Arial", 10, "bold"), command=exportar_relatorio)
btn_csv.pack(pady=5, fill='x', padx=20) # fill='x' faz o botão ficar larguinho

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

carregar_presencas_da_data_selecionada()

# Inicia a Janela (Loop Principal)
root.mainloop()