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
        mes_venda TEXT
    )
    """)
    # Criar tabela de usuários do sistema para autenticação de acesso
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        nome TEXT NOT NULL
    )
    """)
    # Inserir usuário administrador padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        salt = "crm_enterprise_secure_salt_2026"
        pwd_hash = hashlib.sha256(("admin123" + salt).encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password_hash, nome) VALUES (?, ?, ?)", ("admin", pwd_hash, "Administrador"))
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

def add_user(username, password, nome):
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash, nome) VALUES (?, ?, ?)", (username, pwd_hash, nome))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
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
    conn.commit()
    conn.close()

def delete_collaborator(colab_id):
    # Impedir exclusão do ADM por segurança adicional no back-end
    if colab_id == "colab-adm":
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM collaborators WHERE id = ?", (colab_id,))
    # Desassociar colaborador dos clientes de forma limpa (evita quebrar as consultas)
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

def add_client(nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO clients (
        id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, 1 if upfront else 0, valor_upfront, mensalidade, material_instalado, 1 if is_contato else 0, 1 if is_venda else 0, mes_venda
    ))
    conn.commit()
    conn.close()

def update_client(client_id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE clients SET nome = ?, cpf = ?, cnpj = ?, endereco = ?, email = ?, empresa = ?, colaborador_id = ?, upfront = ?, valor_upfront = ?, mensalidade = ?, material_instalado = ?, is_contato = ?, is_venda = ?, mes_venda = ? WHERE id = ?
    """, (
        nome, cpf, cnpj, endereco, email, empresa, colaborador_id, 1 if upfront else 0, valor_upfront, mensalidade, material_instalado, 1 if is_contato else 0, 1 if is_venda else 0, mes_venda, client_id
    ))
    conn.commit()
    conn.close()

def delete_client(client_id):
    # Impedir exclusão do CL01 por segurança adicional no back-end
    if client_id == "client-cl01":
        return
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

if "edit_colab_id" not in st.session_state:
    st.session_state.edit_colab_id = None
if "edit_client_id" not in st.session_state:
    st.session_state.edit_client_id = None

# Inicializar chaves dos formulários para controle de limpeza automatizada (Form Key Resetting)
if "colab_form_key" not in st.session_state:
    st.session_state.colab_form_key = "colab_form_0"
if "client_form_key" not in st.session_state:
    st.session_state.client_form_key = "client_form_0"

# ==========================================
# FLUXO DE NAVEGAÇÃO E AUTENTICAÇÃO
# ==========================================

# Se o usuário não estiver autenticado, exibe a tela de login centalizada
if not st.session_state.autenticado:
    # Cabeçalho da tela de login
    st.markdown("<h1 style='text-align: center; margin-top: 3rem;'>💼 Novo CRM</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #666; margin-bottom: 2rem;'>Controle de Acesso Corporativo</h3>", unsafe_allow_html=True)
    
    # Formulário centralizado usando colunas do Streamlit
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuário", placeholder="Digite seu usuário (ex: admin)")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Acessar Painel")
            
            if submit:
                if not username or not password:
                    st.error("Por favor, preencha todos os campos.")
                else:
                    user = verify_user(username, password)
                    if user:
                        st.session_state.autenticado = True
                        st.session_state.usuario_logado = user["nome"]
                        st.success(f"Bem-vindo(a), {user['nome']}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
        
        st.info("💡 **Acesso padrão do administrador:**\n*   **Usuário:** `admin`\n*   **Senha:** `admin123`\n\n*(Você poderá cadastrar novos usuários e senhas na aba de Gerenciamento de Usuários após logar.)*")
else:
    # Título Principal do Painel
    st.title("💼 Novo CRM - Enterprise Management")
    st.markdown("---")

    # Aba lateral para navegação e operações
    st.sidebar.title("Navegação")
    menu = st.sidebar.radio(
        "Escolha a aba de gerenciamento:",
        ["Cadastro de Colaboradores", "Cadastro de Clientes", "Consulta de Vendas e Métricas", "Gerenciamento de Usuários"]
    )
    
    # Informações do Usuário Logado e Logout na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 Conectado como: **{st.session_state.usuario_logado}**")
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.rerun()

    # Carregar dados atuais do Banco de Dados
    collaborators_data = get_all_collaborators()
    clients_data = get_all_clients()

    # ==========================================
    # ABA: CADASTRO DE COLABORADORES
    # ==========================================
    if menu == "Cadastro de Colaboradores":
        st.header("👥 Gerenciamento de Colaboradores")
        st.info("Substitua esta linha pelo código original do formulário e tabela de colaboradores.")
        
        # Estrutura padrão para facilitar reinserção do seu código original:
        # Exemplo:
        # with st.form(key=st.session_state.colab_form_key):
        #     ...

    # ==========================================
    # ABA: CADASTRO DE CLIENTES
    # ==========================================
    elif menu == "Cadastro de Clientes":
        st.header("🏢 Gerenciamento de Clientes")
        st.info("Substitua esta linha pelo código original do formulário e tabela de clientes.")
        
        # Estrutura padrão para facilitar reinserção do seu código original:
        # Exemplo:
        # with st.form(key=st.session_state.client_form_key):
        #     ...

    # ==========================================
    # ABA: CONSULTA DE VENDAS E MÉTRICAS
    # ==========================================
    elif menu == "Consulta de Vendas e Métricas":
        st.header("📈 Métricas por Colaborador")
        st.markdown("Acompanhe de forma simples os contatos e o número de vendas fechadas de cada colaborador por mês.")
        st.info("Substitua esta linha pelo código original das métricas e gráficos.")

    # ==========================================
    # ABA: GERENCIAMENTO DE USUÁRIOS
    # ==========================================
    elif menu == "Gerenciamento de Usuários":
        st.header("🔑 Usuários do Sistema")
        st.markdown("Cadastre novos usuários para conceder acesso restrito ao Novo CRM.")
        
        col_form, col_list = st.columns([1.2, 1])
        
        with col_form:
            with st.form("add_user_form", clear_on_submit=True):
                st.subheader("Novo Usuário do Painel")
                new_name = st.text_input("Nome Completo", placeholder="Ex: João Silva")
                new_username = st.text_input("Nome de Usuário (login)", placeholder="Ex: joao.silva")
                new_password = st.text_input("Senha de Acesso", type="password", placeholder="Digite uma senha forte")
                user_submit = st.form_submit_button("Cadastrar Usuário")
                
                if user_submit:
                    if not new_name or not new_username or not new_password:
                        st.error("Todos os campos são obrigatórios para cadastro.")
                    else:
                        success = add_user(new_username, new_password, new_name)
                        if success:
                            st.success(f"Usuário '{new_username}' cadastrado com sucesso!")
                        else:
                            st.error("Erro: Este Nome de Usuário já está sendo utilizado por outro membro.")
        
        with col_list:
            st.subheader("Usuários Ativos no Sistema")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username, nome FROM users ORDER BY nome")
            users_list = cursor.fetchall()
            conn.close()
            
            # Exibir como DataFrame simples para controle visual
            df_users = pd.DataFrame([dict(u) for u in users_list])
            if not df_users.empty:
                df_users.columns = ["Usuário (Login)", "Nome Completo"]
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.write("Nenhum usuário cadastrado.")
