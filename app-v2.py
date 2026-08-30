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
            "material_instalado": "Roteador Gigabit, Switch de 24 portas, Cabo CAT6."
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
            # Encontra os dados atuais do colaborador para edição
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
            # Criar DataFrame para exibição limpa
            df_colabs = pd.DataFrame(st.session_state.collaborators)
            # Reorganizar colunas
            df_colabs_display = df_colabs[["nome", "telefone"]].copy()
            df_colabs_display.columns = ["Nome", "Telefone"]
            
            # Exibir como tabela formatada
            st.dataframe(df_colabs_display, use_container_width=True)
            
            # Ações de editar e excluir individuais
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
                        # Remover colaborador e limpar referências dele nos clientes
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
    
    # Criar lista de opções de colaboradores
    colab_options = [{"id": "", "nome": "-- Selecione um Colaborador --"}] + st.session_state.collaborators
    colab_names = [c["nome"] for c in colab_options]
    
    col1, col2 = st.columns([1, 2])
    
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
                
                # Seleção de Empresa (Algar ou Orsegups)
                current_empresa_idx = 0 if client_to_edit["empresa"] == "Algar" else 1
                c_empresa = st.selectbox("Empresa", options=["Algar", "Orsegups"], index=current_empresa_idx, key="edit_c_empresa")
                
                # Seleção do Colaborador cadastrado no sistema
                current_colab_idx = 0
                for idx, colab in enumerate(colab_options):
                    if colab["id"] == client_to_edit["colaborador_id"]:
                        current_colab_idx = idx
                        break
                
                c_colab_name = st.selectbox("Colaborador Associado", options=colab_names, index=current_colab_idx, key="edit_c_colab")
                selected_colab_id = colab_options[colab_names.index(c_colab_name)]["id"]
                
                # Caixa Upfront (Sim/Não - Checkbox)
                c_upfront = st.checkbox("Upfront (Cobrança Inicial)", value=client_to_edit["upfront"], key="edit_c_upfront")
                
                # Campo para o valor de upfront
                c_valor_upfront = st.number_input(
                    "Valor Upfront (R$)", 
                    min_value=0.0, 
                    value=float(client_to_edit["valor_upfront"]), 
                    step=50.0,
                    disabled=not c_upfront,
                    key="edit_c_val_upfront"
                )
                
                # Outro campo para valor de mensalidades
                c_mensalidade = st.number_input(
                    "Valor de Mensalidade (R$)", 
                    min_value=0.0, 
                    value=float(client_to_edit["mensalidade"]), 
                    step=50.0,
                    key="edit_c_mensalidade"
                )
                
                # Local para comentários chamado material instalado
                c_material = st.text_area("Material Instalado (Comentários)", value=client_to_edit["material_instalado"], key="edit_c_material")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Salvar Alterações", type="primary", key="save_client_edit"):
                        if c_nome.strip() == "":
                            st.error("O campo Nome é obrigatório.")
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
                            
                            st.session_state.edit_client_id = None
                            st.success("Cliente updated successfully!")
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
            
            # Seleção de Empresa (Algar ou Orsegups)
            c_empresa = st.selectbox("Empresa", options=["Algar", "Orsegups"], key="new_c_empresa")
            
            # Seleção do Colaborador cadastrado no sistema
            c_colab_name = st.selectbox("Colaborador Associado", options=colab_names, key="new_c_colab")
            selected_colab_id = colab_options[colab_names.index(c_colab_name)]["id"]
            
            # Caixa Upfront (Sim/Não - Checkbox)
            c_upfront = st.checkbox("Upfront (Cobrança Inicial)", value=False, key="new_c_upfront")
            
            # Campo para o valor de upfront
            c_valor_upfront = st.number_input(
                "Valor Upfront (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=50.0,
                disabled=not c_upfront,
                key="new_c_val_upfront"
            )
            
            # Outro campo para valor de mensalidades
            c_mensalidade = st.number_input(
                "Valor de Mensalidade (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=50.0,
                key="new_c_mensalidade"
            )
            
            # Local para comentários chamado material instalado
            c_material = st.text_area("Material Instalado (Comentários)", key="new_c_material")
            
            if st.button("Adicionar Cliente", type="primary", key="add_client"):
                if c_nome.strip() == "":
                    st.error("O campo Nome é obrigatório.")
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
                        "material_instalado": c_material
                    })
                    st.success("Cliente cadastrado com sucesso!")
                    st.rerun()
                    
    with col2:
        st.subheader("📋 Clientes Cadastrados")
        if len(st.session_state.clients) == 0:
            st.info("Nenhum cliente cadastrado.")
        else:
            # Criar DataFrame para exibição resumida na tabela principal
            rows = []
            for client in st.session_state.clients:
                rows.append({
                    "id": client["id"],
                    "Nome": client["nome"],
                    "Empresa": client["empresa"],
                    "Colaborador": get_collaborator_name(client["colaborador_id"]),
                    "Upfront": "Sim" if client["upfront"] else "Não",
                    "Valor Upfront (R$)": f"R$ {client['valor_upfront']:.2f}",
                    "Mensalidade (R$)": f"R$ {client['mensalidade']:.2f}"
                })
            df_clients = pd.DataFrame(rows)
            st.dataframe(df_clients.drop(columns=["id"]), use_container_width=True)
            
            # Detalhes completos e ações individuais
            st.markdown("### Detalhes e Ações de Clientes")
            for client in st.session_state.clients:
                with st.expander(f"🔍 {client['nome']} ({client['empresa']})"):
                    st.markdown(f"""
                    * **CPF:** {client['cpf']} | **CNPJ:** {client['cnpj']}
                    * **Endereço:** {client['endereco']}
                    * **Email:** {client['email']}
                    * **Colaborador Responsável:** {get_collaborator_name(client['colaborador_id'])}
                    * **Tem Upfront?** {"Sim" if client['upfront'] else "Não"} | **Valor Upfront:** R$ {client['valor_upfront']:.2f}
                    * **Mensalidade:** R$ {client['mensalidade']:.2f}
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
    st.header("📊 Consulta de Vendas e Métricas por Colaborador")
    
    if len(st.session_state.collaborators) == 0:
        st.info("Nenhum colaborador cadastrado ainda. Acesse a aba de Colaboradores para realizar os cadastros.")
    else:
        # 1. VISÃO GERAL DO TIME DE VENDAS (KPIs consolidados)
        st.subheader("📈 Visão Geral Consolidada")
        
        total_clientes = len(st.session_state.clients)
        total_mrr = sum(float(c["mensalidade"]) for c in st.session_state.clients)
        total_upfront = sum(float(c["valor_upfront"]) for c in st.session_state.clients)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Total de Clientes Ativos", total_clientes)
        with m_col2:
            st.metric("Mensalidade Recorrente Total (MRR)", f"R$ {total_mrr:,.2f}")
        with m_col3:
            st.metric("Receita Upfront Acumulada", f"R$ {total_upfront:,.2f}")
        
        st.markdown("---")
        
        # 2. FILTRO INDIVIDUAL DE COLABORADOR
        st.subheader("👤 Análise Individual por Colaborador")
        
        colab_names = [colab["nome"] for colab in st.session_state.collaborators]
        selected_colab_name = st.selectbox("Selecione o Colaborador para detalhar:", colab_names)
        
        selected_colab = next(c for c in st.session_state.collaborators if c["nome"] == selected_colab_name)
        colab_id = selected_colab["id"]
        
        # Filtragem de carteira do colaborador
        colab_clients = [c for c in st.session_state.clients if c["colaborador_id"] == colab_id]
        num_clients = len(colab_clients)
        colab_mrr = sum(float(c["mensalidade"]) for c in colab_clients)
        colab_upfront = sum(float(c["valor_upfront"]) for c in colab_clients)
        
        st.markdown(f"### Desempenho Comercial: **{selected_colab_name}**")
        
        ind_col1, ind_col2, ind_col3 = st.columns(3)
        with ind_col1:
            st.metric("Clientes Ativos na Carteira", num_clients)
        with ind_col2:
            st.metric("Receita Mensal sob Gestão (MRR)", f"R$ {colab_mrr:,.2f}")
        with ind_col3:
            st.metric("Upfront Total Gerado", f"R$ {colab_upfront:,.2f}")
            
        st.markdown("#### Lista de Clientes Atendidos")
        if num_clients == 0:
            st.warning(f"O colaborador **{selected_colab_name}** ainda não possui clientes associados em sua carteira.")
        else:
            rows_colab = []
            for client in colab_clients:
                rows_colab.append({
                    "Nome do Cliente": client["nome"],
                    "Empresa": client["empresa"],
                    "Email": client["email"],
                    "Mensalidade": f"R$ {client['mensalidade']:.2f}",
                    "Valor Upfront": f"R$ {client['valor_upfront']:.2f}",
                    "Material Instalado": client["material_instalado"] if client["material_instalado"] else "Nenhum material cadastrado"
                })
            df_colab_clients = pd.DataFrame(rows_colab)
            st.dataframe(df_colab_clients, use_container_width=True)
            
        st.markdown("---")
        
        # 3. COMPARAÇÕES VISUAIS ENTRE COLABORADORES
        st.subheader("📊 Comparativo de Performance")
        
        data_charts = []
        for colab in st.session_state.collaborators:
            clients_under = [c for c in st.session_state.clients if c["colaborador_id"] == colab["id"]]
            data_charts.append({
                "Colaborador": colab["nome"],
                "Clientes": len(clients_under),
                "Mensalidades (MRR)": sum(float(c["mensalidade"]) for c in clients_under),
                "Upfront Acumulado": sum(float(c["valor_upfront"]) for c in clients_under)
            })
        
        df_charts = pd.DataFrame(data_charts)
        
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("**Número de Clientes por Colaborador**")
            st.bar_chart(df_charts.set_index("Colaborador")[["Clientes"]], use_container_width=True)
            
        with chart_col2:
            st.markdown("**Receita Mensal (MRR) Gerada por Colaborador (R$)**")
            st.bar_chart(df_charts.set_index("Colaborador")[["Mensalidades (MRR)"]], use_container_width=True)
