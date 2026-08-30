import streamlit as st
import pandas as pd
import sqlite3
import uuid

# Configuração da página do Streamlit
st.set_page_config(
    page_title="CRM Enterprise Management",
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
    conn.commit()
    
    # Garantir que o Colaborador ADM (fixo) exista sempre
    cursor.execute("SELECT COUNT(*) FROM collaborators WHERE id = ?", ("colab-adm",))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO collaborators (id, nome, telefone) VALUES (?, ?, ?)", ("colab-adm", "ADM", "(00) 00000-0000"))
        conn.commit()
        
    # Garantir que o Cliente CL01 (fixo) exista sempre
    cursor.execute("SELECT COUNT(*) FROM clients WHERE id = ?", ("client-cl01",))
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO clients (id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "client-cl01", "CL01", "000.000.000-00", "", "Endereço Padrão", "cl01@email.com", "Algar", "colab-adm", 0, 0.0, 150.0, "Instalação de Teste Padrão", 1, 1, "Janeiro"
        ))
        conn.commit()
    conn.close()

# Inicializar o Banco de Dados
init_db()

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
            id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, 
            upfront, valor_upfront, mensalidade, material_instalado, 
            is_contato, is_venda, mes_venda
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id,
        1 if upfront else 0, valor_upfront, mensalidade, material_instalado,
        1 if is_contato else 0, 1 if is_venda else 0, mes_venda
    ))
    conn.commit()
    conn.close()

def update_client(client_id, nome, cpf, cnpj, endereco, email, empresa, colaborador_id, upfront, valor_upfront, mensalidade, material_instalado, is_contato, is_venda, mes_venda):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clients SET 
            nome = ?, cpf = ?, cnpj = ?, endereco = ?, email = ?, empresa = ?, colaborador_id = ?, 
            upfront = ?, valor_upfront = ?, mensalidade = ?, material_instalado = ?, 
            is_contato = ?, is_venda = ?, mes_venda = ?
        WHERE id = ?
    """, (
        nome, cpf, cnpj, endereco, email, empresa, colaborador_id,
        1 if upfront else 0, valor_upfront, mensalidade, material_instalado,
        1 if is_contato else 0, 1 if is_venda else 0, mes_venda,
        client_id
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
if "edit_colab_id" not in st.session_state:
    st.session_state.edit_colab_id = None
if "edit_client_id" not in st.session_state:
    st.session_state.edit_client_id = None

# Inicializar chaves dos campos para controle de limpeza automatizada
if "new_colab_nome" not in st.session_state:
    st.session_state.new_colab_nome = ""
if "new_colab_tel" not in st.session_state:
    st.session_state.new_colab_tel = ""

if "new_c_nome" not in st.session_state:
    st.session_state.new_c_nome = ""
if "new_c_cpf" not in st.session_state:
    st.session_state.new_c_cpf = ""
if "new_c_cnpj" not in st.session_state:
    st.session_state.new_c_cnpj = ""
if "new_c_endereco" not in st.session_state:
    st.session_state.new_c_endereco = ""
if "new_c_email" not in st.session_state:
    st.session_state.new_c_email = ""
if "new_c_material" not in st.session_state:
    st.session_state.new_c_material = ""


# Título Principal do Painel
st.title("💼 CRM Enterprise Management")
st.markdown("---")

# Aba lateral para navegação e operações
st.sidebar.title("Navegação")
menu = st.sidebar.radio(
    "Escolha a aba de gerenciamento:",
    ["Cadastro de Colaboradores", "Cadastro de Clientes", "Consulta de Vendas e Métricas"]
)

# Carregar dados atuais do Banco de Dados
collaborators_data = get_all_collaborators()
clients_data = get_all_clients()


# ==========================================
# ABA: CADASTRO DE COLABORADORES
# ==========================================
if menu == "Cadastro de Colaboradores":
    st.header("👥 Gerenciamento de Colaboradores")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Modo de edição ou novo cadastro
        if st.session_state.edit_colab_id:
            st.subheader("📝 Editar Colaborador")
            colab_to_edit = next((c for c in collaborators_data if c["id"] == st.session_state.edit_colab_id), None)
            
            if colab_to_edit:
                is_adm = (colab_to_edit["id"] == "colab-adm")
                nome_input = st.text_input(
                    "Nome", 
                    value=colab_to_edit["nome"], 
                    key="edit_colab_nome",
                    disabled=is_adm,
                    help="O nome do colaborador administrativo padrão (ADM) é fixo." if is_adm else None
                )
                tel_input = st.text_input("Telefone", value=colab_to_edit["telefone"], key="edit_colab_tel")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Salvar Alterações", type="primary", key="save_colab_edit"):
                        if nome_input.strip() == "":
                            st.error("O campo Nome é obrigatório.")
                        else:
                            update_collaborator(st.session_state.edit_colab_id, nome_input, tel_input)
                            st.session_state.edit_colab_id = None
                            st.success("Colaborador atualizado com sucesso!")
                            st.rerun()
                with col_btn2:
                    if st.button("Cancelar", key="cancel_colab_edit"):
                        st.session_state.edit_colab_id = None
                        st.rerun()
            else:
                st.session_state.edit_colab_id = None
                st.rerun()
        else:
            st.subheader("➕ Novo Colaborador")
            nome_input = st.text_input("Nome", key="new_colab_nome")
            tel_input = st.text_input("Telefone", key="new_colab_tel")
            
            if st.button("Adicionar Colaborador", type="primary", key="add_colab"):
                if nome_input.strip() == "":
                    st.error("O campo Nome é obrigatório.")
                else:
                    # Inserir no Banco de Dados
                    add_collaborator(nome_input, tel_input)
                    # Limpar as caixas de digitação setando as variáveis do session_state
                    st.session_state.new_colab_nome = ""
                    st.session_state.new_colab_tel = ""
                    st.success("Colaborador cadastrado com sucesso!")
                    st.rerun()
                    
    with col2:
        st.subheader("📋 Colaboradores Cadastrados")
        if len(collaborators_data) == 0:
            st.info("Nenhum colaborador cadastrado.")
        else:
            df_colabs = pd.DataFrame(collaborators_data)
            df_colabs_display = df_colabs[["nome", "telefone"]].copy()
            df_colabs_display.columns = ["Nome", "Telefone"]
            
            st.dataframe(df_colabs_display, use_container_width=True, hide_index=True)
            
            st.markdown("### Ações")
            for colab in collaborators_data:
                col_row1, col_row2, col_row3 = st.columns([2, 1, 1])
                with col_row1:
                    st.write(f"**{colab['nome']}** - {colab['telefone']}")
                with col_row2:
                    if st.button("Editar", key=f"edit_btn_{colab['id']}"):
                        st.session_state.edit_colab_id = colab["id"]
                        st.rerun()
                with col_row3:
                    if colab["id"] == "colab-adm":
                        st.button("Excluir", key=f"del_btn_{colab['id']}", type="secondary", disabled=True, help="O colaborador administrativo fixo (ADM) não pode ser excluído.")
                    else:
                        if st.button("Excluir", key=f"del_btn_{colab['id']}", type="secondary"):
                            delete_collaborator(colab["id"])
                            st.success(f"Colaborador {colab['nome']} excluído com sucesso!")
                            st.rerun()


# ==========================================
# ABA: CADASTRO DE CLIENTES
# ==========================================
elif menu == "Cadastro de Clientes":
    st.header("🏢 Gerenciamento de Clientes")
    
    # Criar lista dinâmica de colaboradores para a caixa de seleção
    if len(collaborators_data) == 0:
        colab_options = [{"id": "", "nome": "-- Nenhum Colaborador Cadastrado --"}]
    else:
        colab_options = [{"id": "", "nome": "-- Selecione um Colaborador --"}] + collaborators_data
        
    colab_names = [c["nome"] for c in colab_options]
    
    col1, col2 = st.columns([1.1, 1.9])
    
    with col1:
        if st.session_state.edit_client_id:
            st.subheader("📝 Editar Cliente")
            client_to_edit = next((c for c in clients_data if c["id"] == st.session_state.edit_client_id), None)
            
            if client_to_edit:
                is_cl01 = (client_to_edit["id"] == "client-cl01")
                c_nome = st.text_input(
                    "Nome", 
                    value=client_to_edit["nome"], 
                    key="edit_c_nome",
                    disabled=is_cl01,
                    help="O nome do cliente fixo (CL01) não pode ser alterado." if is_cl01 else None
                )
                c_cpf = st.text_input("CPF", value=client_to_edit["cpf"], key="edit_c_cpf")
                c_cnpj = st.text_input("CNPJ", value=client_to_edit["cnpj"], key="edit_c_cnpj")
                c_endereco = st.text_input("Endereço", value=client_to_edit["endereco"], key="edit_c_endereco")
                c_email = st.text_input("Email", value=client_to_edit["email"], key="edit_c_email")
                
                # Empresa
                emp_idx = 0 if client_to_edit["empresa"] == "Algar" else 1
                c_empresa = st.selectbox("Empresa", options=["Algar", "Orsegups"], index=emp_idx, key="edit_c_empresa")
                
                # Selecionar colaborador associado salvo no cliente
                current_colab_idx = 0
                for idx, colab in enumerate(colab_options):
                    if colab["id"] == client_to_edit["colaborador_id"]:
                        current_colab_idx = idx
                        break
                
                c_colab_name = st.selectbox("Colaborador Associated", options=colab_names, index=current_colab_idx, key="edit_c_colab")
                selected_colab_id = colab_options[colab_names.index(c_colab_name)]["id"] if c_colab_name in colab_names else ""
                
                # Classificação Contato x Venda
                st.markdown("##### Classificação do Cliente")
                c_is_contato = st.checkbox("Contato (Prospecção/Atendimento)", value=bool(client_to_edit["is_contato"]), key="edit_c_is_contato")
                c_is_venda = st.checkbox("Venda (Negócio Fechado)", value=bool(client_to_edit["is_venda"]), key="edit_c_is_venda")
                
                c_mes_venda = ""
                if c_is_venda:
                    curr_mes = client_to_edit["mes_venda"]
                    default_mes_idx = MESES_ANO.index(curr_mes) if curr_mes in MESES_ANO else 0
                    c_mes_venda = st.selectbox("Mês da Venda", options=MESES_ANO, index=default_mes_idx, key="edit_c_mes_venda")
                
                st.markdown("---")
                
                # Valores Financeiros
                c_upfront = st.checkbox("Upfront (Cobrança Inicial)", value=bool(client_to_edit["upfront"]), key="edit_c_upfront")
                c_valor_upfront = st.number_input(
                    "Valor Upfront (R$)", 
                    min_value=0.0, 
                    value=float(client_to_edit["valor_upfront"]), 
                    step=50.0,
                    disabled=not c_upfront,
                    key="edit_c_val_upfront"
                )
                
                c_mensalidade = st.number_input(
                    "Valor de Mensalidade (R$)", 
                    min_value=0.0, 
                    value=float(client_to_edit["mensalidade"]), 
                    step=50.0,
                    key="edit_c_mensalidade"
                )
                
                c_material = st.text_area("Material Instalado (Comentários)", value=client_to_edit["material_instalado"], key="edit_c_material")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Salvar Alterações", type="primary", key="save_client_edit"):
                        if c_nome.strip() == "":
                            st.error("O campo Nome é obrigatório.")
                        elif not c_is_contato and not c_is_venda:
                            st.error("Selecione pelo menos uma classificação: Contato ou Venda.")
                        else:
                            update_client(
                                st.session_state.edit_client_id, c_nome, c_cpf, c_cnpj, c_endereco, c_email, c_empresa, 
                                selected_colab_id, c_upfront, c_valor_upfront if c_upfront else 0.0, c_mensalidade, \
                                c_material, c_is_contato, c_is_venda, c_mes_venda if c_is_venda else ""
                            )
                            st.session_state.edit_client_id = None
                            st.success("Cliente atualizado com sucesso!")
                            st.rerun()
                with col_btn2:
                    if st.button("Cancelar", key="cancel_client_edit"):
                        st.session_state.edit_client_id = None
                        st.rerun()
            else:
                st.session_state.edit_client_id = None
                st.rerun()
        else:
            st.subheader("➕ Novo Cliente")
            c_nome = st.text_input("Nome", key="new_c_nome")
            c_cpf = st.text_input("CPF", key="new_c_cpf")
            c_cnpj = st.text_input("CNPJ", key="new_c_cnpj")
            c_endereco = st.text_input("Endereço", key="new_c_endereco")
            c_email = st.text_input("Email", key="new_c_email")
            
            c_empresa = st.selectbox("Empresa", options=["Algar", "Orsegups"], key="new_c_empresa")
            
            c_colab_name = st.selectbox("Colaborador Associado", options=colab_names, key="new_c_colab")
            selected_colab_id = colab_options[colab_names.index(c_colab_name)]["id"] if c_colab_name in colab_names else ""
            
            # Classificação Contato x Venda
            st.markdown("##### Classificação do Cliente")
            c_is_contato = st.checkbox("Contato (Prospecção/Atendimento)", value=True, key="new_c_is_contato")
            c_is_venda = st.checkbox("Venda (Negócio Fechado)", value=False, key="new_c_is_venda")
            
            c_mes_venda = ""
            if c_is_venda:
                c_mes_venda = st.selectbox("Mês da Venda", options=MESES_ANO, key="new_c_mes_venda")
            
            st.markdown("---")
            
            c_upfront = st.checkbox("Upfront (Cobrança Inicial)", value=False, key="new_c_upfront")
            c_valor_upfront = st.number_input(
                "Valor Upfront (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=50.0,
                disabled=not c_upfront,
                key="new_c_val_upfront"
            )
            
            c_mensalidade = st.number_input(
                "Valor de Mensalidade (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=50.0,
                key="new_c_mensalidade"
            )
            
            c_material = st.text_area("Material Instalado (Comentários)", key="new_c_material")
            
            if st.button("Adicionar Cliente", type="primary", key="add_client"):
                if c_nome.strip() == "":
                    st.error("O campo Nome é obrigatório.")
                elif not c_is_contato and not c_is_venda:
                    st.error("Selecione pelo menos uma classificação: Contato ou Venda.")
                else:
                    # Salvar no banco
                    add_client(
                        c_nome, c_cpf, c_cnpj, c_endereco, c_email, c_empresa, selected_colab_id, \
                        c_upfront, c_valor_upfront if c_upfront else 0.0, c_mensalidade, c_material, \
                        c_is_contato, c_is_venda, c_mes_venda if c_is_venda else ""
                    )
                    
                    # Limpar inputs (esvaziar caixas de digitação no session_state)
                    st.session_state.new_c_nome = ""
                    st.session_state.new_c_cpf = ""
                    st.session_state.new_c_cnpj = ""
                    st.session_state.new_c_endereco = ""
                    st.session_state.new_c_email = ""
                    st.session_state.new_c_material = ""
                    st.session_state.new_c_is_contato = True
                    st.session_state.new_c_is_venda = False
                    st.session_state.new_c_upfront = False
                    
                    st.success("Cliente cadastrado com sucesso!")
                    st.rerun()
                    
    with col2:
        st.subheader("📋 Clientes Cadastrados")
        if len(clients_data) == 0:
            st.info("Nenhum cliente cadastrado.")
        else:
            rows = []
            for client in clients_data:
                # Obter classificações de forma dinâmica e segura
                classificacoes = []
                if client.get("is_contato"):
                    classificacoes.append("Contato")
                if client.get("is_venda"):
                    mes_str = f" ({client.get('mes_venda', '')})" if client.get('mes_venda') else ""
                    classificacoes.append(f"Venda{mes_str}")
                class_label = " / " .join(classificacoes) if classificacoes else "Não Definido"
                
                rows.append({
                    "id": client["id"],
                    "Nome": client["nome"],
                    "Empresa": client["empresa"],
                    "Classificação": class_label,
                    "Colaborador": get_collaborator_name(client["colaborador_id"], collaborators_data),
                    "Mensalidade (R$)": f"R$ {client['mensalidade']:.2f}"
                })
            df_clients = pd.DataFrame(rows)
            st.dataframe(df_clients.drop(columns=["id"]), use_container_width=True, hide_index=True)
            
            st.markdown("### Detalhes e Ações de Clientes")
            for client in clients_data:
                c_badges = []
                if client.get("is_contato"):
                    c_badges.append("👤 Contato")
                if client.get("is_venda"):
                    c_badges.append(f"💰 Venda ({client.get('mes_venda', 'N/A')})")
                badges_text = " | ".join(c_badges) if c_badges else "Sem Classificação"
                
                with st.expander(f"🔍 {client['nome']} [{badges_text}] ({client['empresa']})"):
                    st.markdown(f"""
                    * **CPF:** {client['cpf']} | **CNPJ:** {client['cnpj']}
                    * **Endereço:** {client['endereco']}
                    * **Email:** {client['email']}
                    * **Colaborador Responsável:** {get_collaborator_name(client['colaborador_id'], collaborators_data)}
                    * **Valor Upfront:** R$ {client['valor_upfront']:.2f} | **Mensalidade:** R$ {client['mensalidade']:.2f}
                    * **Material Instalado:**
                    """)
                    st.info(client['material_instalado'] if client['material_instalado'] else "Nenhum material listado.")
                    
                    col_row1, col_row2 = st.columns(2)
                    with col_row1:
                        if st.button("Editar Cliente", key=f"edit_cli_{client['id']}", type="primary"):
                            st.session_state.edit_client_id = client["id"]
                            st.rerun()
                    with col_row2:
                        if client["id"] == "client-cl01":
                            st.button("Excluir Cliente", key=f"del_cli_{client['id']}", type="secondary", disabled=True, help="O cliente padrão do sistema (CL01) não pode ser excluído.")
                        else:
                            if st.button("Excluir Cliente", key=f"del_cli_{client['id']}", type="secondary"):
                                delete_client(client["id"])
                                st.success(f"Cliente {client['nome']} excluído com sucesso!")
                                st.rerun()


# ==========================================
# ABA: CONSULTA DE VENDAS E MÉTRICAS
# ==========================================
elif menu == "Consulta de Vendas e Métricas":
    st.header("📈 Métricas por Colaborador")
    st.markdown("Acompanhe de forma simples os contatos e o número de vendas fechadas de cada colaborador por mês.")
    
    if len(collaborators_data) == 0:
        st.info("Nenhum colaborador cadastrado para exibir métricas. Adicione colaboradores na aba de cadastro.")
    else:
        # Selecionar colaborador
        colab_names = [c["nome"] for c in collaborators_data]
        selected_colab_name = st.selectbox("Selecione o Colaborador para análise:", options=colab_names)
        selected_colab = next(c for c in collaborators_data if c["nome"] == selected_colab_name)
        colab_id = selected_colab["id"]
        
        # Filtrar clientes (contatos e vendas) do colaborador selecionado de forma segura
        colab_clients = [c for c in clients_data if c["colaborador_id"] == colab_id]
        
        colab_contacts = [c for c in colab_clients if c.get("is_contato") == 1]
        colab_sales = [c for c in colab_clients if c.get("is_venda") == 1]
        
        # Métricas simples no topo
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric(label="Total de Contatos (Prospecção)", value=len(colab_contacts))
        with m_col2:
            st.metric(label="Total de Vendas Concluídas", value=len(colab_sales))
            
        st.markdown("---")
        
        # Divisão de Vendas por Mês
        st.subheader("🗓️ Vendas Realizadas por Mês")
        if len(colab_sales) == 0:
            st.info("Este colaborador ainda não possui vendas cadastradas.")
        else:
            # Contagem de vendas por mês usando os meses cadastrados
            sales_by_month = {m: 0 for m in MESES_ANO}
            for sale in colab_sales:
                mes = sale.get("mes_venda", "")
                if mes in sales_by_month:
                    sales_by_month[mes] += 1
            
            # Criar DataFrame apenas para os meses que possuem vendas
            sales_month_data = [{"Mês": m, "Quantidade de Vendas": v} for m, v in sales_by_month.items() if v > 0]
            
            if sales_month_data:
                df_month = pd.DataFrame(sales_month_data)
                col_tab, col_chart = st.columns([1, 1])
                
                with col_tab:
                    st.dataframe(df_month, use_container_width=True, hide_index=True)
                with col_chart:
                    # Gráfico simples das vendas mensais
                    st.bar_chart(df_month.set_index("Mês"))
            else:
                st.info("Vendas registradas sem indicação de mês.")
                
        st.markdown("-----")
        
        # Listagem de Contatos e Clientes Ativos deste colaborador
        st.subheader("📞 Detalhes de Contatos e Clientes sob Gestão")
        
        aba_contatos, aba_vendas = st.tabs(["👥 Lista de Contatos", "💰 Lista de Vendas"])
        
        with aba_contatos:
            if len(colab_contacts) == 0:
                st.info("Nenhum contato ativo sob responsabilidade deste colaborador.")
            else:
                rows_contacts = []
                for c in colab_contacts:
                    rows_contacts.append({
                        "Nome": c["nome"],
                        "Empresa": c["empresa"],
                        "Email": c["email"],
                        "Endereço": c["endereco"],
                        "Telefone/CPF": c["cpf"] if c["cpf"] else "N/A"
                    })
                st.dataframe(pd.DataFrame(rows_contacts), use_container_width=True, hide_index=True)
                
        with aba_vendas:
            if len(colab_sales) == 0:
                st.info("Nenhuma venda concluída sob responsabilidade deste colaborador.")
            else:
                rows_sales = []
                for s in colab_sales:
                    rows_sales.append({
                        "Nome": s["nome"],
                        "Mês da Venda": s.get("mes_venda", "Não Definido"),
                        "Empresa": s["empresa"],
                        "Valor Upfront": f"R$ {s['valor_upfront']:.2f}",
                        "Mensalidade": f"R$ {s['mensalidade']:.2f}"
                    })
                st.dataframe(pd.DataFrame(rows_sales), use_container_width=True, hide_index=True)
