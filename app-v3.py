import streamlit as st
import pandas as pd
import uuid

# Configuração da página do Streamlit
st.set_page_config(
    page_title="CRM Enterprise Management",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Lista global de meses para consistência
MESES_ANO = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Inicialização do estado da sessão para armazenar dados (simulando banco de dados)
if "collaborators" not in st.session_state:
    st.session_state.collaborators = [
        {"id": "colab-1", "nome": "Carlos Silva", "telefone": "(11) 99999-1111"},
        {"id": "colab-2", "nome": "Ana Souza", "telefone": "(11) 99999-2222"}
    ]

if "clients" not in st.session_state:
    st.session_state.clients = [
        {
            "id": "client-1",
            "nome": "Empresa XYZ Ltda",
            "cpf": "123.456.789-00",
            "cnpj": "12.345.678/0001-99",
            "endereco": "Av. Paulista, 1000 - São Paulo/SP",
            "email": "contato@xyz.com",
            "empresa": "Algar",
            "colaborador_id": "colab-1",
            "upfront": True,
            "valor_upfront": 1500.00,
            "mensalidade": 350.00,
            "material_instalado": "Roteador Gigabit, Switch de 24 portas, Cabo CAT6.",
            "is_contato": True,
            "is_venda": True,
            "mes_venda": "Agosto"
        },
        {
            "id": "client-2",
            "nome": "João de Souza",
            "cpf": "987.654.321-11",
            "cnpj": "",
            "endereco": "Rua das Flores, 123",
            "email": "joao@email.com",
            "empresa": "Orsegups",
            "colaborador_id": "colab-1",
            "upfront": False,
            "valor_upfront": 0.0,
            "mensalidade": 0.0,
            "material_instalado": "Nenhum material",
            "is_contato": True,
            "is_venda": False,
            "mes_venda": ""
        },
        {
            "id": "client-3",
            "nome": "Maria Oliveira",
            "cpf": "456.789.123-22",
            "cnpj": "",
            "endereco": "Av. Central, 456",
            "email": "maria@email.com",
            "empresa": "Algar",
            "colaborador_id": "colab-2",
            "upfront": True,
            "valor_upfront": 500.0,
            "mensalidade": 150.0,
            "material_instalado": "Kit básico de alarmes",
            "is_contato": False,
            "is_venda": True,
            "mes_venda": "Julho"
        }
    ]

# Variáveis de controle de edição no session_state
if "edit_colab_id" not in st.session_state:
    st.session_state.edit_colab_id = None
if "edit_client_id" not in st.session_state:
    st.session_state.edit_client_id = None

# Função auxiliar para buscar nome do colaborador por ID
def get_collaborator_name(colab_id):
    for colab in st.session_state.collaborators:
        if colab["id"] == colab_id:
            return colab["nome"]
    return "Não associado"

# Título Principal do Painel
st.title("💼 CRM Enterprise Management")
st.markdown("---")

# Aba lateral para navegação e operações
st.sidebar.title("Navegação")
menu = st.sidebar.radio(
    "Escolha a aba de gerenciamento:",
    ["Cadastro de Colaboradores", "Cadastro de Clientes", "Consulta de Vendas e Métricas"]
)

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
            colab_to_edit = next((c for c in st.session_state.collaborators if c["id"] == st.session_state.edit_colab_id), None)
            
            if colab_to_edit:
                nome_input = st.text_input("Nome", value=colab_to_edit["nome"], key="edit_colab_nome")
                tel_input = st.text_input("Telefone", value=colab_to_edit["telefone"], key="edit_colab_tel")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Salvar Alterações", type="primary", key="save_colab_edit"):
                        if nome_input.strip() == "":
                            st.error("O campo Nome é obrigatório.")
                        else:
                            colab_to_edit["nome"] = nome_input
                            colab_to_edit["telefone"] = tel_input
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
                    new_id = str(uuid.uuid4())
                    st.session_state.collaborators.append({
                        "id": new_id,
                        "nome": nome_input,
                        "telefone": tel_input
                    })
                    st.success("Colaborador cadastrado com sucesso!")
                    st.rerun()
                    
    with col2:
        st.subheader("📋 Colaboradores Cadastrados")
        if len(st.session_state.collaborators) == 0:
            st.info("Nenhum colaborador cadastrado.")
        else:
            df_colabs = pd.DataFrame(st.session_state.collaborators)
            df_colabs_display = df_colabs[["nome", "telefone"]].copy()
            df_colabs_display.columns = ["Nome", "Telefone"]
            
            st.dataframe(df_colabs_display, use_container_width=True)
            
            st.markdown("### Ações")
            for colab in st.session_state.collaborators:
                col_row1, col_row2, col_row3 = st.columns([2, 1, 1])
                with col_row1:
                    st.write(f"**{colab['nome']}** - {colab['telefone']}")
                with col_row2:
                    if st.button("Editar", key=f"edit_btn_{colab['id']}"):
                        st.session_state.edit_colab_id = colab["id"]
                        st.rerun()
                with col_row3:
                    if st.button("Excluir", key=f"del_btn_{colab['id']}", type="secondary"):
                        st.session_state.collaborators = [c for c in st.session_state.collaborators if c["id"] != colab["id"]]
                        for client in st.session_state.clients:
                            if client["colaborador_id"] == colab["id"]:
                                client["colaborador_id"] = ""
                        st.success(f"Colaborador {colab['nome']} excluído!")
                        st.rerun()

# ==========================================
# ABA: CADASTRO DE CLIENTES
# ==========================================
elif menu == "Cadastro de Clientes":
    st.header("🏢 Gerenciamento de Clientes")
    
    colab_options = [{"id": "", "nome": "-- Selecione um Colaborador --"}] + st.session_state.collaborators
    colab_names = [c["nome"] for c in colab_options]
    
    col1, col2 = st.columns([1.1, 1.9])
    
    with col1:
        if st.session_state.edit_client_id:
            st.subheader("📝 Editar Cliente")
            client_to_edit = next((c for c in st.session_state.clients if c["id"] == st.session_state.edit_client_id), None)
            
            if client_to_edit:
                c_nome = st.text_input("Nome", value=client_to_edit["nome"], key="edit_c_nome")
                c_cpf = st.text_input("CPF", value=client_to_edit["cpf"], key="edit_c_cpf")
                c_cnpj = st.text_input("CNPJ", value=client_to_edit["cnpj"], key="edit_c_cnpj")
                c_endereco = st.text_input("Endereço", value=client_to_edit["endereco"], key="edit_c_endereco")
                c_email = st.text_input("Email", value=client_to_edit["email"], key="edit_c_email")
                
                c_empresa = st.selectbox("Empresa", options=["Algar", "Orsegups"], index=0 if client_to_edit["empresa"] == "Algar" else 1, key="edit_c_empresa")
                
                # Colaborador
                current_colab_idx = 0
                for idx, colab in enumerate(colab_options):
                    if colab["id"] == client_to_edit["colaborador_id"]:
                        current_colab_idx = idx
                        break
                
                c_colab_name = st.selectbox("Colaborador Associado", options=colab_names, index=current_colab_idx, key="edit_c_colab")
                selected_colab_id = colab_options[colab_names.index(c_colab_name)]["id"]
                
                # --- NOVOS CAMPOS: CLASSIFICAÇÃO DE CONTATO E VENDA ---
                st.markdown("##### Classificação do Cliente")
                # Carregar estados atuais, garantindo compatibilidade retroativa
                current_is_contato = client_to_edit.get("is_contato", True)
                current_is_venda = client_to_edit.get("is_venda", False)
                current_mes_venda = client_to_edit.get("mes_venda", "")
                
                c_is_contato = st.checkbox("Contato (Prospecção/Atendimento)", value=current_is_contato, key="edit_c_is_contato")
                c_is_venda = st.checkbox("Venda (Negócio Fechado)", value=current_is_venda, key="edit_c_is_venda")
                
                # Se for marcado como venda, abre a opção de selecionar o mês da venda
                c_mes_venda = ""
                if c_is_venda:
                    default_mes_idx = 0
                    if current_mes_venda in MESES_ANO:
                        default_mes_idx = MESES_ANO.index(current_mes_venda)
                    c_mes_venda = st.selectbox("Mês da Venda", options=MESES_ANO, index=default_mes_idx, key="edit_c_mes_venda")
                
                st.markdown("---")
                
                # Campos financeiros adicionais
                c_upfront = st.checkbox("Upfront (Cobrança Inicial)", value=client_to_edit["upfront"], key="edit_c_upfront")
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
                            client_to_edit["nome"] = c_nome
                            client_to_edit["cpf"] = c_cpf
                            client_to_edit["cnpj"] = c_cnpj
                            client_to_edit["endereco"] = c_endereco
                            client_to_edit["email"] = c_email
                            client_to_edit["empresa"] = c_empresa
                            client_to_edit["colaborador_id"] = selected_colab_id
                            client_to_edit["upfront"] = c_upfront
                            client_to_edit["valor_upfront"] = c_valor_upfront if c_upfront else 0.0
                            client_to_edit["mensalidade"] = c_mensalidade
                            client_to_edit["material_instalado"] = c_material
                            client_to_edit["is_contato"] = c_is_contato
                            client_to_edit["is_venda"] = c_is_venda
                            client_to_edit["mes_venda"] = c_mes_venda if c_is_venda else ""
                            
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
            selected_colab_id = colab_options[colab_names.index(c_colab_name)]["id"]
            
            # --- NOVOS CAMPOS: CLASSIFICAÇÃO DE CONTATO E VENDA ---
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
                    new_id = str(uuid.uuid4())
                    st.session_state.clients.append({
                        "id": new_id,
                        "nome": c_nome,
                        "cpf": c_cpf,
                        "cnpj": c_cnpj,
                        "endereco": c_endereco,
                        "email": c_email,
                        "empresa": c_empresa,
                        "colaborador_id": selected_colab_id,
                        "upfront": c_upfront,
                        "valor_upfront": c_valor_upfront if c_upfront else 0.0,
                        "mensalidade": c_mensalidade,
                        "material_instalado": c_material,
                        "is_contato": c_is_contato,
                        "is_venda": c_is_venda,
                        "mes_venda": c_mes_venda if c_is_venda else ""
                    })
                    st.success("Cliente cadastrado com sucesso!")
                    st.rerun()
                    
    with col2:
        st.subheader("📋 Clientes Cadastrados")
        if len(st.session_state.clients) == 0:
            st.info("Nenhum cliente cadastrado.")
        else:
            rows = []
            for client in st.session_state.clients:
                # Obter classificações legíveis
                classificacoes = []
                if client.get("is_contato", True):
                    classificacoes.append("Contato")
                if client.get("is_venda", False):
                    mes_str = f" ({client.get('mes_venda', '')})" if client.get('mes_venda') else ""
                    classificacoes.append(f"Venda{mes_str}")
                class_label = " / ".join(classificacoes) if classificacoes else "Sem Tipo"
                
                rows.append({
                    "id": client["id"],
                    "Nome": client["nome"],
                    "Empresa": client["empresa"],
                    "Classificação": class_label,
                    "Colaborador": get_collaborator_name(client["colaborador_id"]),
                    "Mensalidade (R$)": f"R$ {client['mensalidade']:.2f}"
                })
            df_clients = pd.DataFrame(rows)
            st.dataframe(df_clients.drop(columns=["id"]), use_container_width=True)
            
            st.markdown("### Detalhes e Ações de Clientes")
            for client in st.session_state.clients:
                # Badge visual de tipos
                c_badges = []
                if client.get("is_contato", True):
                    c_badges.append("👤 Contato")
                if client.get("is_venda", False):
                    c_badges.append(f"💰 Venda ({client.get('mes_venda', 'N/A')})")
                badges_text = " | ".join(c_badges)
                
                with st.expander(f"🔍 {client['nome']} [{badges_text}] ({client['empresa']})"):
                    st.markdown(f"""
                    * **CPF:** {client['cpf']} | **CNPJ:** {client['cnpj']}
                    * **Endereço:** {client['endereco']}
                    * **Email:** {client['email']}
                    * **Colaborador Responsável:** {get_collaborator_name(client['colaborador_id'])}
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
                        if st.button("Excluir Cliente", key=f"del_cli_{client['id']}", type="secondary"):
                            st.session_state.clients = [c for c in st.session_state.clients if c["id"] != client["id"]]
                            st.success(f"Cliente {client['nome']} excluído!")
                            st.rerun()

# ==========================================
# ABA: CONSULTA DE VENDAS E MÉTRICAS
# ==========================================
elif menu == "Consulta de Vendas e Métricas":
    st.header("📈 Métricas por Colaborador")
    st.markdown("Acompanhe de forma simples os contatos e o número de vendas fechadas de cada colaborador por mês.")
    
    if len(st.session_state.collaborators) == 0:
        st.warning("Cadastre colaboradores antes de consultar as métricas.")
    else:
        # Seleção do Colaborador
        colab_names = [c["nome"] for c in st.session_state.collaborators]
        selected_colab_name = st.selectbox("Selecione o Colaborador para análise:", options=colab_names)
        selected_colab = next(c for c in st.session_state.collaborators if c["nome"] == selected_colab_name)
        colab_id = selected_colab["id"]
        
        # Filtrar clientes (contatos e vendas) do colaborador selecionado
        colab_clients = [c for c in st.session_state.clients if c["colaborador_id"] == colab_id]
        
        # Filtros de tipos de clientes
        colab_contacts = [c for c in colab_clients if c.get("is_contato", True)]
        colab_sales = [c for c in colab_clients if c.get("is_venda", False)]
        
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
            
            # Criar DataFrame apenas para os meses que possuem vendas (para limpar o visual)
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
                
        st.markdown("---")
        
        # Listagem de Contatos e Clientes Ativos deste colaborador
        st.subheader("📞 Detalhes de Contatos e Clientes sob Gestão")
        
        aba_contatos, aba_vendas = st.tabs(["👥 Lista de Contatos", "💰 Lista de Vendas"])
        
        with aba_contatos:
            if len(colab_contacts) == 0:
                st.info("Nenhum contato ativo sob responsabilidade deste colaborador.")
            else:
                rows_contacts = []
                for idx, c in enumerate(colab_contacts):
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
                for idx, s in enumerate(colab_sales):
                    rows_sales.append({
                        "Nome": s["nome"],
                        "Mês da Venda": s.get("mes_venda", "Não Definido"),
                        "Empresa": s["empresa"],
                        "Valor Upfront": f"R$ {s['valor_upfront']:.2f}",
                        "Mensalidade": f"R$ {s['mensalidade']:.2f}"
                    })
                st.dataframe(pd.DataFrame(rows_sales), use_container_width=True, hide_index=True)
