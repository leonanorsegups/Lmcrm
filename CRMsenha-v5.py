import streamlit as st
import pandas as pd
import sqlite3
import uuid
import hashlib

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Novo CRM Management",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Customizados para diminuir as fontes (Título, Subtítulos e Métricas)
st.markdown("""
<style>
/* Diminuir tamanho do título principal */
h1 {
font-size: 1.8rem !important;
margin-bottom: 0.5rem !important;
font-weight: 700 !important;
}
/* Diminuir tamanho de headers (st.header) */
h2 {
font-size: 1.35rem !important;
margin-top: 1rem !important;
margin-bottom: 0.6rem !important;
font-weight: 600 !important;
}
/* Diminuir tamanho de subheaders (st.subheader) */
h3 {
font-size: 1.1rem !important;
margin-top: 0.8rem !important;
margin-bottom: 0.4rem !important;
font-weight: 600 !important;
}
/* Estilizar blocos de métricas st.metric */
div[data-testid="stMetricValue"] {
font-size: 1.5rem !important;
font-weight: bold !important;
}
div[data-testid="stMetricLabel"] {
font-size: 0.85rem !important;
color: #555555;
}
</style>
""", unsafe_allow_html=True)

# Lista global de meses para consistência
MESES_ANO = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# ==========================================
# BANCO DE DADOS (SQLITE) PERSISTÊNCIA
# ==========================================
DB_FILE = "crm.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Criar tabela de colaboradores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collaborators (
        id TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        telefone TEXT
    )
    """)
    # Criar tabela de clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        cpf TEXT,
        cnpj TEXT,
        endereco TEXT,
        email TEXT,
        empresa TEXT,
        colaborador_id TEXT,
        upfront INTEGER DEFAULT 0,
        valor_upfront REAL DEFAULT 0.0,
        mensalidade REAL DEFAULT 0.0,
        material_instalado TEXT,
        is_contato INTEGER DEFAULT 1,
        is_venda INTEGER DEFAULT 0,
        mes_venda TEXT,
        instalacao INTEGER DEFAULT 0
    )
    """)
    
    # Migração: Garantir que a coluna 'instalacao' existe na tabela 'clients'
    try:
        cursor.execute("ALTER TABLE clients ADD COLUMN instalacao INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # A coluna já existe
    # Criar tabela de usuários do sistema para autenticação de acesso
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        nome TEXT NOT NULL,
        role TEXT DEFAULT 'Usuário'
    )
    """)
    
    # Migração: Garantir que a coluna 'role' existe na tabela 'users' se o banco foi criado em versões anteriores
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Usuário'")
    except sqlite3.OperationalError:
        pass  # A coluna já existe
        
    # Inserir usuário administrador padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        salt = "crm_enterprise_secure_salt_2026"
        pwd_hash = hashlib.sha256(("admin123" + salt).encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password_hash, nome, role) VALUES (?, ?, ?, ?)", ("admin", pwd_hash, "Administrador", "ADM"))
        # Sincroniza admin na tabela de colaboradores se não existir
        cursor.execute("SELECT COUNT(*) FROM collaborators WHERE id = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO collaborators (id, nome, telefone) VALUES (?, ?, ?)", ("admin", "Administrador", "N/A"))
    else:
        # Garantir que o login master 'admin' seja sempre do nível 'ADM'
        cursor.execute("UPDATE users SET role = 'ADM' WHERE username = 'admin'")
            
    conn.commit()
    conn.close()

# Inicializar o Banco de Dados
init_db()

# --- Funções de Segurança e Autenticação de Usuários ---
def hash_password(password):
    salt = "crm_enterprise_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def add_user(username, password, nome, role="Usuário", telefone=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    try:
        # Cadastra o usuário de login com seu nível de acesso
        cursor.execute("INSERT INTO users (username, password_hash, nome, role) VALUES (?, ?, ?, ?)", (username, pwd_hash, nome, role))
        # Automaticamente cadastra e sincroniza como Colaborador com o mesmo id (username)
        cursor.execute("INSERT INTO collaborators (id, nome, telefone) VALUES (?, ?, ?)", (username, nome, telefone))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        conn.rollback()
        success = False
    conn.close()
    return success

def update_user(username, password=None, nome=None, role=None, telefone=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    # admin principal não pode perder o poder de ADM
    if username == "admin":
        role = "ADM"
    try:
        # Atualiza tabela de login
        if password:
            pwd_hash = hash_password(password)
            if nome:
                if role:
                    cursor.execute("UPDATE users SET password_hash = ?, nome = ?, role = ? WHERE username = ?", (pwd_hash, nome, role, username))
                else:
                    cursor.execute("UPDATE users SET password_hash = ?, nome = ? WHERE username = ?", (pwd_hash, nome, username))
            else:
                if role:
                    cursor.execute("UPDATE users SET password_hash = ?, role = ? WHERE username = ?", (pwd_hash, role, username))
                else:
                    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (pwd_hash, username))
        else:
            if nome:
                if role:
                    cursor.execute("UPDATE users SET nome = ?, role = ? WHERE username = ?", (nome, role, username))
                else:
                    cursor.execute("UPDATE users SET nome = ? WHERE username = ?", (nome, username))
            elif role:
                cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
            
        # Atualiza tabela de colaboradores correspondente
        if nome:
            cursor.execute("UPDATE collaborators SET nome = ?, telefone = ? WHERE id = ?", (nome, telefone, username))
        else:
            cursor.execute("UPDATE collaborators SET telefone = ? WHERE id = ?", (telefone, username))
            
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        success = False
    conn.close()
    return success

def update_collaborator_and_role(colab_id, nome, telefone, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    # admin principal não pode perder o poder de ADM
    if colab_id == "admin":
        role = "ADM"
    try:
        cursor.execute("UPDATE collaborators SET nome = ?, telefone = ? WHERE id = ?", (nome, telefone, colab_id))
        cursor.execute("UPDATE users SET nome = ?, role = ? WHERE username = ?", (nome, role, colab_id))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        success = False
    conn.close()
    return success

def delete_user(username):
    if username == "admin":
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Deleta da tabela de usuários
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        # Deleta da tabela de colaboradores correspondente
        cursor.execute("DELETE FROM collaborators WHERE id = ?", (username,))
        # Desassocia clientes vinculados a esse colaborador de forma limpa
        cursor.execute("UPDATE clients SET colaborador_id = '' WHERE colaborador_id = ?", (username,))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        success = False
    conn.close()
    return success

# --- Funções CRUD de Colaboradores ---
def get_all_collaborators():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM collaborators ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_collaborator(nome, telefone):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO collaborators (id, nome, telefone) VALUES (?, ?, ?)", (new_id, nome, telefone))
    conn.commit()
    conn.close()

def update_collaborator(colab_id, nome, telefone):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE collaborators SET nome = ?, telefone = ? WHERE id = ?", (nome, telefone, colab_id))
    # Se houver usuário de login correspondente com esse id, atualiza o nome dele também
    cursor.execute("UPDATE users SET nome = ? WHERE username = ?", (nome, colab_id))
    conn.commit()
    conn.close()

def delete_collaborator(colab_id):
    if colab_id == "admin":
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    # Remove o colaborador
    cursor.execute("DELETE FROM collaborators WHERE id = ?", (colab_id,))
    # Remove usuário correspondente se existir
    cursor.execute("DELETE FROM users WHERE username = ?", (colab_id,))
    # Desassociar clientes de forma limpa
    cursor.execute("UPDATE clients SET colaborador_id = '' WHERE colaborador_id = ?", (colab_id,))
    conn.commit()
    conn.close()

# --- Funções CRUD de Clientes ---
def get_all_clients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_client(nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda, instalacao=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO clients (
        id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda, instalacao
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, 1 if upfront else 0, valor_upfront, mensalidade, material_instalado, 1 if is_contato else 0, 1 if is_venda else 0, mes_venda, 1 if instalacao else 0
    ))
    conn.commit()
    conn.close()

def update_client(client_id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda, instalacao=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE clients SET nome = ?, cpf = ?, cnpj = ?, endereco = ?, email = ?, empresa = ?, colaborador_id = ?, upfront = ?, valor_upfront = ?, mensalidade = ?, material_instalado = ?, is_contato = ?, is_venda = ?, mes_venda = ?, instalacao = ? WHERE id = ?
    """, (
        nome, cpf, cnpj, endereco, email, empresa, colaborador_id, 1 if upfront else 0, valor_upfront, mensalidade, material_instalado, 1 if is_contato else 0, 1 if is_venda else 0, mes_venda, 1 if instalacao else 0, client_id
    ))
    conn.commit()
    conn.close()

def delete_client(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()

# --- Função Auxiliar de nomes ---
def get_collaborator_name(colab_id, collaborators_list):
    for colab in collaborators_list:
        if colab["id"] == colab_id:
            return colab["nome"]
    return "Não associado"

# ==========================================
# VARIÁVEIS DE SESSÃO DO STREAMLIT
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "username" not in st.session_state:
    st.session_state.username = None
if "usuario_role" not in st.session_state:
    st.session_state.usuario_role = None

if "edit_colab_id" not in st.session_state:
    st.session_state.edit_colab_id = None
if "edit_client_id" not in st.session_state:
    st.session_state.edit_client_id = None
if "edit_username" not in st.session_state:
    st.session_state.edit_username = None

# Inicializar chaves dos formulários para controle de limpeza automatizada (Form Key Resetting)
if "colab_form_key" not in st.session_state:
    st.session_state.colab_form_key = "colab_form_0"
if "client_form_key" not in st.session_state:
    st.session_state.client_form_key = "client_form_0"

# ==========================================
# FLUXO DE NAVEGAÇÃO E AUTENTICAÇÃO
# ==========================================

# Se o usuário não estiver autenticado, exibe a tela de login centralizada
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; margin-top: 3rem;'>💼 Novo CRM</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #666; margin-bottom: 2rem;'>Controle de Acesso Corporativo</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuário (Login)", placeholder="Digite seu usuário (ex: admin)")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Acessar Painel")
            
            if submit:
                if not username or not password:
                    st.error("Por favor, preencha todos os campos.")
                else:
                    # Normalizar para letras minúsculas o login
                    user = verify_user(username.strip().lower(), password)
                    if user:
                        st.session_state.autenticado = True
                        st.session_state.usuario_logado = user["nome"]
                        st.session_state.username = user["username"]
                        st.session_state.usuario_role = user.get("role", "Usuário")
                        st.success(f"Bem-vindo(a), {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
        

else:
    # Título Principal do Painel
    st.title("💼 Novo CRM - Enterprise Management")
    st.markdown("---")

    # Definir se é administrador logado (role == 'ADM')
    is_admin = (st.session_state.usuario_role == "ADM")

    # Abas laterais para navegação e operações
    st.sidebar.title("Navegação")
    
    # Montar menu de navegação lateral (Gerenciamento de Usuários apenas visível para perfis ADM)
    menu_options = ["Cadastro de Colaboradores", "Cadastro de Clientes", "Consulta de Vendas e Métricas"]
    if is_admin:
        menu_options.append("Gerenciamento de Usuários")
        
    menu = st.sidebar.radio("Escolha a aba de gerenciamento:", menu_options)
    
    # Informações do Usuário Logado e Logout na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 Conectado como: **{st.session_state.usuario_logado}**")
    st.sidebar.write(f"Nível de Acesso: **{'Administrador (ADM)' if is_admin else 'Colaborador (Usuário)'}**")
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.session_state.username = None
        st.session_state.usuario_role = None
        st.rerun()

    # Carregar dados atuais do Banco de Dados
    all_collaborators_raw = get_all_collaborators()
    all_clients_raw = get_all_clients()

    # ==========================================
    # ENFORCAR REGRA DE ISOLAMENTO DE DADOS (ROW-LEVEL SECURITY)
    # ==========================================
    if is_admin:
        # Administradores enxergam TODOS os colaboradores e clientes
        collaborators_data = all_collaborators_raw
        clients_data = all_clients_raw
    else:
        # Colaboradores comuns só enxergam seu próprio perfil
        collaborators_data = [c for c in all_collaborators_raw if c["id"] == st.session_state.username]
        # Colaboradores comuns só enxergam seus próprios clientes
        clients_data = [c for c in all_clients_raw if c["colaborador_id"] == st.session_state.username]

    # ==========================================
    # ABA: CADASTRO DE COLABORADORES
    # ==========================================
    if menu == "Cadastro de Colaboradores":
        st.header("👥 Gerenciamento de Colaboradores")
        
        col_form, col_table = st.columns([1, 1.5])
        
        with col_form:
            if st.session_state.edit_colab_id:
                st.subheader("Editar Perfil de Colaborador")
                colab_to_edit = next((c for c in collaborators_data if c["id"] == st.session_state.edit_colab_id), None)
                if colab_to_edit:
                    with st.form("edit_colab_form"):
                        nome_colab = st.text_input("Nome", value=colab_to_edit["nome"], disabled=not is_admin)
                        tel_colab = st.text_input("Telefone", value=colab_to_edit["telefone"])
                        
                        # Se for ADM, permite alterar o nível de acesso (Usuário vs ADM) do colaborador
                        if is_admin:
                            role_atual = "Usuário"
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT role FROM users WHERE username = ?", (colab_to_edit["id"],))
                            row_u = cursor.fetchone()
                            if row_u:
                                role_atual = row_u["role"]
                            conn.close()
                            
                            is_main_admin = (colab_to_edit["id"] == "admin")
                            role_colab = st.selectbox(
                                "Nível de Acesso",
                                ["Usuário", "ADM"],
                                index=0 if role_atual == "Usuário" else 1,
                                disabled=is_main_admin,
                                help="Usuários ADM podem gerenciar logins e ver clientes de todos os colaboradores."
                            )
                        else:
                            role_colab = "Usuário"
                            
                        sub_btn = st.form_submit_button("Salvar Alterações")
                        if sub_btn:
                            if is_admin:
                                update_collaborator_and_role(st.session_state.edit_colab_id, nome_colab, tel_colab, role_colab)
                            else:
                                update_collaborator(st.session_state.edit_colab_id, nome_colab, tel_colab)
                            
                            st.session_state.edit_colab_id = None
                            st.success("Perfil de colaborador atualizado com sucesso!")
                            st.rerun()
                    if st.button("Cancelar Edição"):
                        st.session_state.edit_colab_id = None
                        st.rerun()
            else:
                if is_admin:
                    st.subheader("Novo Colaborador")
                    st.info("Para manter a integridade, **novos colaboradores devem ser cadastrados criando um usuário de acesso** na aba 'Gerenciamento de Usuários'.")
                else:
                    st.subheader("Seu Perfil Profissional")
                    colab_self = next((c for c in collaborators_data if c["id"] == st.session_state.username), None)
                    if colab_self:
                        with st.form("edit_self_colab"):
                            st.text_input("Nome", value=colab_self["nome"], disabled=True)
                            tel_colab = st.text_input("Telefone de Contato", value=colab_self["telefone"])
                            sub_btn = st.form_submit_button("Atualizar Meu Telefone")
                            if sub_btn:
                                update_collaborator(st.session_state.username, colab_self["nome"], tel_colab)
                                st.success("Seu telefone foi atualizado com sucesso!")
                                st.rerun()

        with col_table:
            st.subheader("Colaboradores Ativos no Sistema" if is_admin else "Suas Credenciais de Cadastro")
            if collaborators_data:
                for colab in collaborators_data:
                    col_n, col_t, col_actions = st.columns([3, 2, 1.5])
                    
                    # Buscar o nível do colaborador para exibir uma tag visual informativa
                    role_info = ""
                    if is_admin:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT role FROM users WHERE username = ?", (colab["id"],))
                        row_r = cursor.fetchone()
                        conn.close()
                        if row_r:
                            role_info = f" | [**{row_r['role']}**]"
                            
                    col_n.write(f"👤 **{colab['nome']}** (`{colab['id']}`){role_info}")
                    col_t.write(colab['telefone'] if colab['telefone'] else "Sem telefone cadastrado")
                    
                    # Permite edição
                    with col_actions:
                        c1, c2 = st.columns(2)
                        if c1.button("📝", key=f"edit_col_{colab['id']}_v3"):
                            st.session_state.edit_colab_id = colab["id"]
                            st.rerun()
                        # Apenas ADM pode excluir perfis (exclui o login simultaneamente)
                        if is_admin and colab["id"] != "admin":
                            if c2.button("❌", key=f"del_col_{colab['id']}_v3"):
                                delete_collaborator(colab["id"])
                                st.success("Colaborador removido com sucesso!")
                                st.rerun()
                    st.markdown("<hr style='margin: 0.3rem 0; border: 0.5px solid #eee;'>", unsafe_allow_html=True)
            else:
                st.write("Nenhum colaborador localizado.")

    # ==========================================
    # ABA: CADASTRO DE CLIENTES
    # ==========================================
    elif menu == "Cadastro de Clientes":
        st.header("🏢 Gerenciamento de Clientes (Contatos e Vendas)")
        
        col_form, col_table = st.columns([1.2, 2])
        
        with col_form:
            if st.session_state.edit_client_id:
                st.subheader("Editar Cadastro de Cliente")
                client_to_edit = next((c for c in clients_data if c["id"] == st.session_state.edit_client_id), None)
                if client_to_edit:
                    with st.form("edit_client_form"):
                        nome_cl = st.text_input("Nome do Cliente", value=client_to_edit["nome"])
                        cpf_cl = st.text_input("CPF", value=client_to_edit["cpf"])
                        cnpj_cl = st.text_input("CNPJ", value=client_to_edit["cnpj"])
                        end_cl = st.text_input("Endereço", value=client_to_edit["endereco"])
                        email_cl = st.text_input("E-mail", value=client_to_edit["email"])
                        emp_cl = st.text_input("Empresa", value=client_to_edit["empresa"])
                        
                        # Se for ADM, permite alterar a atribuição do cliente para outro colaborador
                        if is_admin:
                            colab_options = {c["id"]: c["nome"] for c in get_all_collaborators()}
                            current_id = client_to_edit["colaborador_id"]
                            try:
                                colab_idx = list(colab_options.keys()).index(current_id)
                            except ValueError:
                                colab_idx = 0
                            selected_colab_id = st.selectbox(
                                "Colaborador Responsável",
                                options=list(colab_options.keys()),
                                format_func=lambda x: colab_options[x],
                                index=colab_idx
                            )
                        else:
                            selected_colab_id = st.session_state.username
                            st.text_input("Colaborador Responsável", value=st.session_state.usuario_logado, disabled=True)
                            
                        upfront_cl = st.checkbox("Teve pagamento Upfront?", value=bool(client_to_edit["upfront"]))
                        val_upfront_cl = st.number_input("Valor Upfront (R$)", value=float(client_to_edit["valor_upfront"]), min_value=0.0)
                        
                        # Opção de Instalação (Sim ou Não)
                        instalacao_val = client_to_edit.get("instalacao", 0)
                        instalacao_cl = st.radio("Instalação Realizada?", ["Não", "Sim"], index=1 if instalacao_val else 0, horizontal=True)
                        
                        # Informativo da Regra de Faturamento
                        st.info("💡 **Faturamento Mensal Calculado (Vendas):**\n"
                                "* Base: **R$ 500,00**\n"
                                "* Upfront: **+ 50% do valor do Upfront** (se houver)\n"
                                "* Instalação: **+ R$ 150,00** (se Sim)")
                                
                        mat_instalado = st.text_input("Material Instalado", value=client_to_edit["material_instalado"])
                        
                        is_contato_cl = st.checkbox("É apenas Contato?", value=bool(client_to_edit["is_contato"]))
                        is_venda_cl = st.checkbox("É uma Venda Fechada?", value=bool(client_to_edit["is_venda"]))
                        mes_venda_cl = st.selectbox("Mês da Venda", options=MESES_ANO, index=MESES_ANO.index(client_to_edit["mes_venda"]) if client_to_edit["mes_venda"] in MESES_ANO else 0)
                        
                        sub_btn = st.form_submit_button("Salvar Alterações")
                        if sub_btn:
                            # Calcular faturamento (mensalidade) automaticamente
                            if is_venda_cl:
                                mensal_cl_calc = 500.0
                                if upfront_cl:
                                    mensal_cl_calc += (0.5 * val_upfront_cl)
                                if instalacao_cl == "Sim":
                                    mensal_cl_calc += 150.0
                            else:
                                mensal_cl_calc = 0.0
                                
                            update_client(
                                st.session_state.edit_client_id, nome_cl, cpf_cl, cnpj_cl, end_cl, email_cl, emp_cl,
                                selected_colab_id, upfront_cl, val_upfront_cl, mensal_cl_calc, mat_instalado,
                                is_contato_cl, is_venda_cl, mes_venda_cl, 1 if instalacao_cl == "Sim" else 0
                            )
                            st.session_state.edit_client_id = None
                            st.success("Cliente atualizado com sucesso!")
                            st.rerun()
                    if st.button("Cancelar Edição"):
                        st.session_state.edit_client_id = None
                        st.rerun()
            else:
                st.subheader("Novo Cliente / Lead")
                with st.form("add_client_form"):
                    nome_cl = st.text_input("Nome do Cliente *", placeholder="Ex: Maria Oliveira")
                    cpf_cl = st.text_input("CPF", placeholder="000.000.000-00")
                    cnpj_cl = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
                    end_cl = st.text_input("Endereço Completo")
                    email_cl = st.text_input("E-mail corporativo")
                    emp_cl = st.text_input("Nome da Empresa")
                    
                    # Se for ADM, permite atribuir o cliente cadastrado para qualquer colaborador
                    if is_admin:
                        colab_options = {c["id"]: c["nome"] for c in get_all_collaborators()}
                        selected_colab_id = st.selectbox(
                            "Colaborador Responsável",
                            options=list(colab_options.keys()),
                            format_func=lambda x: colab_options[x]
                        )
                    else:
                        selected_colab_id = st.session_state.username
                        st.text_input("Colaborador Responsável", value=st.session_state.usuario_logado, disabled=True)
                        
                    upfront_cl = st.checkbox("Teve Upfront?")
                    val_upfront_cl = st.number_input("Valor Upfront (R$)", min_value=0.0)
                    
                    # Opção de Instalação (Sim ou Não)
                    instalacao_cl = st.radio("Instalação Realizada?", ["Não", "Sim"], index=0, horizontal=True)
                    
                    # Informativo da Regra de Faturamento
                    st.info("💡 **Faturamento Mensal Calculado (Vendas):**\n"
                            "* Base: **R$ 500,00**\n"
                            "* Upfront: **+ 50% do valor do Upfront** (se houver)\n"
                            "* Instalação: **+ R$ 150,00** (se Sim)")
                            
                    mat_instalado = st.text_input("Material de Apoio/Instalação")
                    
                    is_contato_cl = st.checkbox("Marcar como Contato ativo", value=True)
                    is_venda_cl = st.checkbox("Marcar como Venda fechada", value=False)
                    mes_venda_cl = st.selectbox("Mês da Venda", options=MESES_ANO)
                    
                    sub_btn = st.form_submit_button("Cadastrar Cliente")
                    if sub_btn:
                        if not nome_cl:
                            st.error("Por favor, informe ao menos o Nome do Cliente.")
                        else:
                            # Calcular faturamento (mensalidade) automaticamente
                            if is_venda_cl:
                                mensal_cl_calc = 500.0
                                if upfront_cl:
                                    mensal_cl_calc += (0.5 * val_upfront_cl)
                                if instalacao_cl == "Sim":
                                    mensal_cl_calc += 150.0
                            else:
                                mensal_cl_calc = 0.0
                                
                            add_client(
                                nome_cl, cpf_cl, cnpj_cl, end_cl, email_cl, emp_cl,
                                selected_colab_id, upfront_cl, val_upfront_cl, mensal_cl_calc, mat_instalado,
                                is_contato_cl, is_venda_cl, mes_venda_cl, 1 if instalacao_cl == "Sim" else 0
                            )
                            st.success(f"Cliente '{nome_cl}' adicionado com sucesso!")
                            st.rerun()

        with col_table:
            st.subheader("Clientes sob sua responsabilidade" if not is_admin else "Todas as Contas do CRM")
            if clients_data:
                for cl in clients_data:
                    col_info, col_act = st.columns([4, 1.5])
                    with col_info:
                        status_tag = "🟢 Venda Fechada" if cl["is_venda"] else "🟡 Apenas Contato"
                        responsavel_nome = get_collaborator_name(cl["colaborador_id"], get_all_collaborators())
                        instal_status = "✅ Sim" if cl.get("instalacao", 0) else "❌ Não"
                        st.markdown(f"🏢 **{cl['nome']}** ({cl['empresa'] if cl['empresa'] else 'Pessoa Física'})")
                        st.caption(f"Status: **{status_tag}** | Instalação: **{instal_status}** | Responsável: **{responsavel_nome}** | E-mail: {cl['email'] if cl['email'] else 'Não informado'}")
                        if cl["is_venda"]:
                            st.caption(f"Faturamento: **R$ {cl['mensalidade']:.2f}/mês** | Upfront: **R$ {cl['valor_upfront']:.2f}** | Mês: **{cl['mes_venda']}**")
                    with col_act:
                        c1, c2 = st.columns(2)
                        if c1.button("📝", key=f"edit_cli_{cl['id']}_v3"):
                            st.session_state.edit_client_id = cl["id"]
                            st.rerun()
                        # Exclusão direta permitida para o ADM ou o colaborador dono do registro
                        if c2.button("❌", key=f"del_cli_{cl['id']}_v3"):
                            delete_client(cl["id"])
                            st.success("Cliente removido!")
                            st.rerun()
                    st.markdown("<hr style='margin: 0.5rem 0; border: 0.5px solid #eee;'>", unsafe_allow_html=True)
            else:
                st.info("Nenhum cliente cadastrado no momento.")

    # ==========================================\n    # ABA: CONSULTA DE VENDAS E MÉTRICAS\n    # ==========================================\n    elif menu == "Consulta de Vendas e Métricas":
        st.header("📈 Dashboard de Métricas & Vendas")
        st.markdown("Acompanhe o faturamento, os contatos e os fechamentos mensais dos usuários cadastrados.")
        
        vendas_fechadas = [c for c in clients_data if c["is_venda"] == 1]
        contatos_ativos = [c for c in clients_data if c["is_contato"] == 1]
        
        total_mrr = sum(float(v["mensalidade"]) for v in vendas_fechadas)
        total_upfront = sum(float(v["valor_upfront"]) for v in vendas_fechadas)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Contatos Registrados", len(contatos_ativos))
        m2.metric("Vendas Concluídas", len(vendas_fechadas))
        m3.metric("Faturamento Mensal (MRR)", f"R$ {total_mrr:,.2f}")
        m4.metric("Total de Upfront", f"R$ {total_upfront:,.2f}")
        
        st.markdown("---")
        
        # Visão mensal das vendas
        st.subheader("Desempenho de Fechamento por Mês")
        if vendas_fechadas:
            df_vendas = pd.DataFrame([dict(v) for v in vendas_fechadas])
            # Contar vendas agrupando pelos meses do ano
            vendas_por_mes = df_vendas.groupby("mes_venda").size().reindex(MESES_ANO, fill_value=0).reset_index()
            vendas_por_mes.columns = ["Mês", "Quantidade de Vendas"]
            
            # Somar faturamento mensal agrupado por meses
            fat_por_mes = df_vendas.groupby("mes_venda")["mensalidade"].sum().reindex(MESES_ANO, fill_value=0.0).reset_index()
            vendas_por_mes["Valor de Contrato (Mensalidade)"] = fat_por_mes["mensalidade"].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(vendas_por_mes, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma venda concluída para gerar indicadores mensais.")

    # ==========================================
    # ABA: GERENCIAMENTO DE USUÁRIOS (RESTRICTED TO ADMIN)
    # ==========================================
    elif menu == "Gerenciamento de Usuários":
        if not is_admin:
            st.error("Acesso negado. Apenas administradores do sistema possuem permissão para gerenciar logins.")
        else:
            st.header("🔑 Central de Controle de Usuários e Acessos")
            st.markdown("Como **Administrador**, registre novos membros, altere senhas e gerencie os níveis de acesso (Usuário vs ADM).")
            
            col_form, col_list = st.columns([1.2, 1])
            
            with col_form:
                if st.session_state.edit_username:
                    st.subheader(f"Alterar Credenciais: {st.session_state.edit_username}")
                    # Obter dados de login e contato atuais
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT u.username, u.nome, u.role, c.telefone 
                        FROM users u 
                        LEFT JOIN collaborators c ON u.username = c.id 
                        WHERE u.username = ?
                    """, (st.session_state.edit_username,))
                    u_to_edit = cursor.fetchone()
                    conn.close()
                    
                    if u_to_edit:
                        with st.form("edit_user_form"):
                            edit_name = st.text_input("Nome Completo", value=u_to_edit["nome"])
                            edit_tel = st.text_input("Telefone", value=u_to_edit["telefone"] if u_to_edit["telefone"] else "")
                            
                            is_main_admin = (st.session_state.edit_username == "admin")
                            edit_role = st.selectbox(
                                "Nível de Acesso",
                                ["Usuário", "ADM"],
                                index=0 if u_to_edit["role"] == "Usuário" else 1,
                                disabled=is_main_admin,
                                help="Usuários ADM possuem acessos irrestritos ao CRM."
                            )
                            
                            edit_pwd = st.text_input("Nova Senha de Acesso (deixe vazio se não quiser mudar)", type="password")
                            
                            user_edit_submit = st.form_submit_button("Confirmar Alteração")
                            if user_edit_submit:
                                if not edit_name:
                                    st.error("O campo Nome Completo não pode ficar em branco.")
                                else:
                                    success = update_user(
                                        st.session_state.edit_username, 
                                        edit_pwd if edit_pwd else None, 
                                        edit_name, 
                                        edit_role, 
                                        edit_tel
                                    )
                                    if success:
                                        st.success(f"Cadastro de '{st.session_state.edit_username}' atualizado com sucesso!")
                                        st.session_state.edit_username = None
                                        st.rerun()
                                    else:
                                        st.error("Ocorreu um erro ao atualizar os dados.")
                        if st.button("Cancelar Alteração"):
                            st.session_state.edit_username = None
                            st.rerun()
                else:
                    st.subheader("Registrar Usuário e Colaborador")
                    with st.form("add_user_form", clear_on_submit=True):
                        new_name = st.text_input("Nome Completo *", placeholder="Ex: Roberto Carlos")
                        new_tel = st.text_input("Telefone", placeholder="Ex: (11) 98765-4321")
                        
                        # Permite definir o nível de acesso ao cadastrar um novo usuário
                        new_role = st.selectbox(
                            "Nível de Acesso *",
                            ["Usuário", "ADM"],
                            help="Selecione ADM para conceder permissão de edição em contatos e vendas de outros membros."
                        )
                        
                        new_username = st.text_input("Nome de Login (Usuário) *", placeholder="Ex: roberto.carlos")
                        new_password = st.text_input("Senha Inicial de Acesso *", type="password")
                        
                        user_submit = st.form_submit_button("Cadastrar Usuário")
                        if user_submit:
                            if not new_name or not new_username or not new_password:
                                st.error("Todos os campos marcados com * são obrigatórios.")
                            elif new_username.strip().lower() == "admin":
                                st.error("O identificador 'admin' é restrito do sistema.")
                            else:
                                login_clean = new_username.strip().lower()
                                success = add_user(login_clean, new_password, new_name, new_role, new_tel)
                                if success:
                                    st.success(f"Excelente! Usuário '{login_clean}' foi criado com nível '{new_role}' e adicionado à lista de colaboradores.")
                                    st.rerun()
                                else:
                                    st.error("Este nome de login já está em uso por outro membro.")
            
            with col_list:
                st.subheader("Acessos Ativos")
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.username, u.nome, u.role, c.telefone 
                    FROM users u 
                    LEFT JOIN collaborators c ON u.username = c.id 
                    ORDER BY u.nome
                """)
                users_list = cursor.fetchall()
                conn.close()
                
                for u in users_list:
                    u_dict = dict(u)
                    col_info, col_act = st.columns([3, 1.5])
                    with col_info:
                        level_badge = "🔴 ADM" if u_dict['role'] == "ADM" else "🔵 Usuário"
                        st.markdown(f"👤 **{u_dict['nome']}** ({level_badge})")
                        st.caption(f"Login: `{u_dict['username']}` | Tel: {u_dict['telefone'] if u_dict['telefone'] else 'N/A'}")
                    with col_act:
                        c1, c2 = st.columns(2)
                        if c1.button("📝", key=f"edit_usr_{u_dict['username']}_v3"):
                            st.session_state.edit_username = u_dict["username"]
                            st.rerun()
                        if u_dict["username"] != "admin":
                            if c2.button("❌", key=f"del_usr_{u_dict['username']}_v3"):
                                delete_user(u_dict["username"])
                                st.success("Usuário e Colaborador excluídos com sucesso!")
                                st.rerun()
                    st.markdown("<hr style='margin: 0.3rem 0; border: 0.5px solid #eee;'>", unsafe_allow_html=True)
