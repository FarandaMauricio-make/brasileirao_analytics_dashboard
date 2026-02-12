import requests 
import pandas as pd  
import streamlit as st  
import plotly.express as px 
import plotly.graph_objects as go 
from scipy.stats import poisson 
import numpy as np

# ==============================================================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
# ==============================================================================
# Aqui eu digo pro Streamlit: "Abre em tela cheia (wide) e põe um ícone de bola"
st.set_page_config(
    page_title="Brasileirão Analytics Pro",
    page_icon="⚽",
    layout="wide"
)

# CSS HACK AVANÇADO (VISUAL GLASSMORPHISM + FUNDO PERSONALIZADO)
# Substituí o CSS básico por um mais moderno com fontes e transparências.
st.markdown("""
    <style>
    /* Barra Superior Invisível */
    header[data-testid="stHeader"] {
        background-color: rgba(0, 0, 0, 0) !important; /* O último 0 é a transparência total */
    }
            
    /* Cor de Fundo da Área Principal */
    .stApp {
        background-color: #050A14; /* Cor atual (Cinza Escuro Padrão) */
    }
            
    /* Importando fonte moderna (Roboto) do Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }

    /* Cards de Métricas com efeito de "Vidro" (Glassmorphism) */
    div[data-testid="stMetric"] {
        background-color: rgba(30, 30, 30, 0.6); /* Fundo semi-transparente */
        backdrop-filter: blur(10px); /* Desfoque do fundo */
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
    }
    
    /* Efeito suave ao passar o mouse nos cards */
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #00539F; /* Azul Cruzeiro */
    }

    /* Títulos e textos mais destacados */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
    }
    
    /* Ajuste da barra lateral para ficar bem escura */
    section[data-testid="stSidebar"] {
        background-color:  #050A14;
    }
    
    /* Cor da legenda das métricas */
    div[data-testid="stMetricLabel"] > div {
        color: #B0B0B0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# MINHAS CONSTANTES
# Minha chave da API (cuidado para não vazar se for publicar no GitHub público!)
API_KEY = "7856a7ea3e43439685e366312e552301" 
BASE_URL = "https://api.football-data.org/v4"
# O cabeçalho que a API exige para saber quem eu sou
HEADERS = {"X-Auth-Token": API_KEY}

# ==============================================================================
# 2. FUNÇÕES AJUDANTES (HELPERS)
# ==============================================================================
def get_sigla(nome_time):
    """
    Função para limpar os gráficos. Em vez de "Red Bull Bragantino" (que quebra o layout),
    eu transformo em "RBB". Se o time não estiver na lista, pego as 3 primeiras letras.
    Isso é essencial para visualização em celular.
    """
    mapa = {
        "América FC": "AME", "Athletico Paranaense": "CAP", "Atlético Mineiro": "CAM",
        "Bahia": "BAH", "Botafogo FR": "BOT", "Corinthians": "COR",
        "Coritiba": "CFC", "Cruzeiro": "CRU", "Cuiabá": "CUI",
        "Flamengo": "FLA", "Fluminense FC": "FLU", "Fortaleza": "FOR",
        "Goiás": "GOI", "Grêmio": "GRE", "Internacional": "INT",
        "Palmeiras": "PAL", "Red Bull Bragantino": "RBB", "Santos": "SAN",
        "São Paulo FC": "SAO", "Vasco da Gama": "VAS", "Vitória": "VIT",
        "Juventude": "JUV", "Criciúma": "CRI", "Atlético Goianiense": "ACG"
    }
    # Tenta achar no dicionário, se não achar, corta a string.
    for key, value in mapa.items():
        if key in nome_time:
            return value
    return nome_time[:3].upper()

def formatar_grafico(fig):
    """
    Função visual: Remove o fundo cinza padrão do Plotly e as grades excessivas.
    Deixa o gráfico 'flutuando' no fundo escuro do app.
    """
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Remove fundo da área do gráfico
        paper_bgcolor='rgba(0,0,0,0)', # Remove fundo da área externa
        font=dict(color='white'),      # Força texto branco
        xaxis=dict(showgrid=False),    # Sem grades verticais
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), # Grade horizontal sutil
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# ==============================================================================
# 3. EXTRAÇÃO DE DADOS (ETL - EXTRACT, TRANSFORM, LOAD)
# ==============================================================================
# O @st.cache_data é vital! Ele salva o resultado na memória por 1 hora (3600s).
# Sem isso, cada clique recarregaria a API e eu estouraria meu limite de requisições.
@st.cache_data(ttl=3600)
def get_data_from_api():
    try:
        # Pego a classificação atual
        standings = requests.get(f"{BASE_URL}/competitions/BSA/standings", headers=HEADERS).json()
        # Pego a lista de todos os jogos (passados e futuros)
        matches = requests.get(f"{BASE_URL}/competitions/BSA/matches", headers=HEADERS).json()
        return standings, matches
    except Exception as e:
        st.error(f"Deu ruim na conexão com a API: {e}")
        return None, None

def process_data(standings_raw, matches_raw):
    """
    Transforma o JSON bagunçado da API em DataFrames bonitinhos do Pandas.
    """
    # 1. Tratando a Classificação
    if 'standings' not in standings_raw:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    lista_times = standings_raw["standings"][0]["table"]
    df_tabela = pd.DataFrame([
        {
            "Pos": t["position"],
            # ADICIONEI ISSO: Pegando a URL do escudo para mostrar na tabela
            "Escudo": t["team"]["crest"], 
            "Time": t["team"]["name"],
            "Sigla": get_sigla(t["team"]["name"]), # Já crio a sigla aqui
            "Pontos": t["points"],
            "Jogos": t["playedGames"],
            "Vitórias": t["won"],
            "Empates": t["draw"],
            "Derrotas": t["lost"],
            "Gols Pró": t["goalsFor"],
            # CORREÇÃO APLICADA: Mudei de 'Gols Contra' para 'Gols Sofridos'
            "Gols Sofridos": t["goalsAgainst"], 
            "Saldo": t["goalDifference"]
        } for t in lista_times
    ])
    
    # 2. Tratando os Jogos
    lista_jogos = []
    for jogo in matches_raw['matches']:
        lista_jogos.append({
            "Rodada": jogo['matchday'],
            "Data": jogo['utcDate'],
            "Status": jogo['status'], # Importante para saber se já acabou
            "Home": jogo['homeTeam']['name'],
            "Away": jogo['awayTeam']['name'],
            "Sigla_Home": get_sigla(jogo['homeTeam']['name']),
            "Sigla_Away": get_sigla(jogo['awayTeam']['name']),
            "Gols_Home": jogo['score']['fullTime']['home'],
            "Gols_Away": jogo['score']['fullTime']['away']
        })
    
    df_jogos = pd.DataFrame(lista_jogos)
    # Converto a data estranha da API para o horário do Brasil
    df_jogos['Data'] = pd.to_datetime(df_jogos['Data']).dt.tz_convert('America/Sao_Paulo')
    
    # Separo em dois DataFrames: o que já foi (para estatística) e o que virá (para previsão)
    df_finalizados = df_jogos[df_jogos['Status'] == 'FINISHED'].copy()
    df_agendados = df_jogos[df_jogos['Status'] != 'FINISHED'].copy()
    
    return df_tabela, df_finalizados, df_agendados

# ==============================================================================
# 4. MODELAGEM ESTATÍSTICA
# ==============================================================================
def calcular_forca_times(df_finalizados):
    """
    Calcula o 'Power Ranking' de Ataque e Defesa.
    Se a média da liga é 1.0 gol/jogo e o Flamengo faz 2.0, a força de ataque dele é 2.0.
    """
    if df_finalizados.empty: return None, 0, 0
    
    # Médias gerais do campeonato
    media_gols_mandante = df_finalizados['Gols_Home'].mean()
    media_gols_visitante = df_finalizados['Gols_Away'].mean()
    
    # Médias de cada time
    home_stats = df_finalizados.groupby('Home')['Gols_Home'].mean()
    away_stats = df_finalizados.groupby('Away')['Gols_Away'].mean()
    home_def = df_finalizados.groupby('Home')['Gols_Away'].mean() # Quanto toma em casa
    away_def = df_finalizados.groupby('Away')['Gols_Home'].mean() # Quanto toma fora
    
    # DataFrame final com os multiplicadores de força
    forcas = pd.DataFrame({
        'Ataque_Casa': home_stats / media_gols_mandante,
        'Ataque_Fora': away_stats / media_gols_visitante,
        'Defesa_Casa': home_def / media_gols_visitante,
        'Defesa_Fora': away_def / media_gols_mandante
    }).fillna(1) # Se der erro de divisão por zero, assume força média (1)
    
    return forcas, media_gols_mandante, media_gols_visitante

def prever_jogo(time_casa, time_fora, forcas, media_casa, media_fora):
    """
    Usa a Distribuição de Poisson.
    Cruza o Ataque do Mandante com a Defesa do Visitante para achar os Gols Esperados (Lambda).
    """
    if forcas is None or time_casa not in forcas.index or time_fora not in forcas.index:
        return 0, 0, 0 # Não tenho dados suficientes
        
    # Lambda = Gols Esperados
    lamb_casa = forcas.at[time_casa, 'Ataque_Casa'] * forcas.at[time_fora, 'Defesa_Fora'] * media_casa
    lamb_fora = forcas.at[time_fora, 'Ataque_Fora'] * forcas.at[time_casa, 'Defesa_Casa'] * media_fora
    
    # Simulo placares de 0x0 até 5x5
    prob_vitoria_casa, prob_empate, prob_vitoria_fora = 0, 0, 0
    for g_casa in range(6):
        for g_fora in range(6):
            # Qual a probabilidade estatística desse placar exato acontecer?
            prob = poisson.pmf(g_casa, lamb_casa) * poisson.pmf(g_fora, lamb_fora)
            
            # Somo as probabilidades nos potes certos
            if g_casa > g_fora: prob_vitoria_casa += prob
            elif g_casa == g_fora: prob_empate += prob
            else: prob_vitoria_fora += prob
                
    return prob_vitoria_casa, prob_empate, prob_vitoria_fora

# ==============================================================================
# 5. CONSTRUÇÃO DO DASHBOARD (FRONT-END)
# ==============================================================================

# Passo 1: Chamo a API
dados_classificacao, dados_jogos = get_data_from_api()

# Passo 2: Verifico se veio dado. Se a API falhar, não quebro o site.
if dados_classificacao and dados_jogos:
    # Passo 3: Limpo os dados
    df_tabela, df_finalizados, df_agendados = process_data(dados_classificacao, dados_jogos)
    # Passo 4: Calculo as forças para a IA
    forcas, media_casa, media_fora = calcular_forca_times(df_finalizados)

    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.title("Navegação")
    # Aqui defino o menu que troca o conteúdo da página principal
    opcao_menu = st.sidebar.radio("Escolha a visão:", ["Panorama Geral", "Raio-X Cruzeiro"])
    st.sidebar.info("Dica: As siglas nos gráficos facilitam a leitura no celular.")

    # ==========================================================================
    # VISÃO 1: PANORAMA GERAL DO CAMPEONATO
    # ==========================================================================
    if opcao_menu == "Panorama Geral":
        st.title("📊 Análise Tática do Brasileirão")
        st.markdown("Bem-vindo ao centro de inteligência. Aqui analisamos o campeonato de forma macro.")
        
        # Crio abas para não ficar tudo empilhado numa página quilométrica
        aba1, aba2, aba3 = st.tabs(["Classificação & Pontos", "Matriz de Eficiência (Scatter)", "Previsões IA"])
        
        # --- ABA DA TABELA ---
        with aba1:
            st.subheader("Pontuação Atual")
            st.caption("Abaixo, visualizamos rapidamente quem está acumulando mais pontos. A cor mais escura indica o líder.")
            
            # Gráfico de barras simples
            fig_pontos = px.bar(df_tabela, x="Sigla", y="Pontos", color="Pontos", text="Pontos", color_continuous_scale="Blues")
            fig_pontos.update_layout(xaxis_title="Clubes (Sigla)", yaxis_title="Total de Pontos")
            # Aplicando a formatação limpa (Função Nova)
            st.plotly_chart(formatar_grafico(fig_pontos), use_container_width=True)
            
            st.markdown("### 📋 Tabela Detalhada")
            st.markdown("Dados brutos oficiais para conferência.")
            
            # TABELA COM ESCUDOS (AQUI A MÁGICA ACONTECE)
            # Seleciono colunas específicas e ordeno
            cols_exibir = ['Escudo', 'Time', 'Pontos', 'Jogos', 'Vitórias', 'Empates', 'Derrotas', 'Saldo']
            st.dataframe(
                df_tabela.set_index("Pos")[cols_exibir], 
                use_container_width=True,
                column_config={
                    "Escudo": st.column_config.ImageColumn("Escudo", width="small"), # Renderiza imagem
                    "Pontos": st.column_config.ProgressColumn("Pontos", format="%d", min_value=0, max_value=114) # Barra de progresso
                }
            )
            
        # --- ABA DO SCATTER PLOT (AQUELE DOS QUADRANTES) ---
        with aba2:
            st.subheader("🎯 Matriz de Eficiência: Ataque vs. Defesa")
            # STORYTELLING: Explico como ler o gráfico ANTES de mostrar o gráfico.
            # Explicação crucial para o usuário entender o eixo Y invertido.
            st.markdown(
                """
                **Como ler este gráfico estratégico:**
                Imagine este gráfico como um mapa de qualidade.
                
                * ➡️ **Eixo Horizontal (Direita):** Poder de Fogo. Quanto mais à direita, mais gols o time faz.
                * ⬆️ **Eixo Vertical (Topo):** Solidez Defensiva. Quanto mais no topo, **MENOS** gols o time sofreu (melhor defesa).
                
                **Os 4 Perfis de Times:**
                1.  ↗️ **Elite (Canto Superior Direito):** O sonho de todo técnico. Ataque forte e defesa que não vaza.
                2.  ↖️ **Retranqueiros (Canto Superior Esquerdo):** Defesa forte (topo), mas ataque inoperante (esquerda).
                3.  ↘️ **Kamikazes (Canto Inferior Direito):** Fazem muitos gols, mas levam muitos. Jogos emocionantes e perigosos.
                4.  ↙️ **Zona Crítica (Canto Inferior Esquerdo):** Ataque fraco e defesa peneira. Candidatos ao Z4.
                """
            )
            
            # Scatter plot: X=Ataque, Y=Defesa (Gols Sofridos)
            # ATENÇÃO: Aqui usei a coluna corrigida "Gols Sofridos"
            fig_scatter = px.scatter(
                df_tabela, x="Gols Pró", y="Gols Sofridos", text="Sigla", size="Pontos", 
                color="Saldo", color_continuous_scale="RdYlGn", title="Mapa de Posicionamento Tático"
            )
            
            # TRUQUE VISUAL: Linhas médias para dividir os quadrantes
            fig_scatter.add_vline(x=df_tabela['Gols Pró'].mean(), line_dash="dash", line_color="gray", annotation_text="Média Ataque")
            fig_scatter.add_hline(y=df_tabela['Gols Sofridos'].mean(), line_dash="dash", line_color="gray", annotation_text="Média Defesa")
            
            # TRUQUE IMPORTANTE: Inverter o eixo Y. 
            # Porque no futebol, sofrer 0 gols (topo) é melhor que sofrer 10 gols (fundo).
            fig_scatter.update_yaxes(autorange="reversed", title="Gols Sofridos (Quanto mais no topo, melhor a defesa)")
            fig_scatter.update_xaxes(title="Gols Feitos (Quanto mais à direita, melhor o ataque)")
            
            # Destaques automáticos (Melhor Ataque e Melhor Defesa)
            melhor_atk = df_tabela.loc[df_tabela['Gols Pró'].idxmax()]
            # Aqui também atualizei para buscar o mínimo em "Gols Sofridos"
            melhor_def = df_tabela.loc[df_tabela['Gols Sofridos'].idxmin()]
            
            # Setinhas apontando os destaques
            fig_scatter.add_annotation(x=melhor_atk['Gols Pró'], y=melhor_atk['Gols Sofridos'], text="🔥 Melhor Ataque", showarrow=True, arrowhead=2, ax=0, ay=-40, bgcolor="#1E1E1E")
            fig_scatter.add_annotation(x=melhor_def['Gols Pró'], y=melhor_def['Gols Sofridos'], text="🛡️ Melhor Defesa", showarrow=True, arrowhead=2, ax=0, ay=40, bgcolor="#1E1E1E")
            
            # Aplicando a formatação limpa (Função Nova)
            st.plotly_chart(formatar_grafico(fig_scatter), use_container_width=True)
            
        # --- ABA DAS PREVISÕES (POISSON) ---
        with aba3:
            st.subheader(" 🧮​ O que diz a Matemática?")
            st.markdown(
                """
                Utilizamos um modelo estatístico chamado **Distribuição de Poisson**. 
                Ele cruza a força de ataque do mandante com a fragilidade defensiva do visitante (e vice-versa) 
                para calcular a probabilidade percentual de cada resultado nos próximos jogos.
                """
            )
            
            if not df_agendados.empty:
                # Cores para a legenda HTML e para as barras
                cor_home, cor_draw, cor_away = '#27ae60', '#95a5a6', '#c0392b'

                # Pego os próximos 5 jogos
                for _, row in df_agendados.sort_values('Rodada').head(5).iterrows():
                    # Chamo a função de previsão
                    ph, pe, pf = prever_jogo(row['Home'], row['Away'], forcas, media_casa, media_fora)
                    
                    if ph > 0: # Se o cálculo funcionou
                        st.markdown(f"**{row['Home']} (Casa) x {row['Away']} (Fora)** - Rodada {row['Rodada']}")
                        
                        # --- LEGENDA PERSONALIZADA EM HTML (SOLUÇÃO DOS QUADRADINHOS) ---
                        # Isso garante que as 3 cores apareçam sempre e o texto fique legível
                        legenda_html = f"""
                        <div style="display: flex; gap: 15px; font-size: 14px; margin-bottom: 5px;">
                            <span style="color:{cor_home}">■ <b>{row['Sigla_Home']}</b> {ph:.0%}</span>
                            <span style="color:{cor_draw}">■ <b>Empate</b> {pe:.0%}</span>
                            <span style="color:{cor_away}">■ <b>{row['Sigla_Away']}</b> {pf:.0%}</span>
                        </div>
                        """
                        st.markdown(legenda_html, unsafe_allow_html=True)

                        # --- GRÁFICO SLIM (BARRAS FINAS) ---
                        fig_prob = go.Figure()
                        # Vitória Casa
                        fig_prob.add_trace(go.Bar(
                            x=[ph], orientation='h', marker_color=cor_home, hoverinfo='x+name', name=row['Sigla_Home']
                        ))
                        # Empate
                        fig_prob.add_trace(go.Bar(
                            x=[pe], orientation='h', marker_color=cor_draw, hoverinfo='x+name', name='Empate'
                        ))
                        # Vitória Fora
                        fig_prob.add_trace(go.Bar(
                            x=[pf], orientation='h', marker_color=cor_away, hoverinfo='x+name', name=row['Sigla_Away']
                        ))
                        
                        # Configuração para remover tudo e deixar só a barra fina
                        fig_prob.update_layout(
                            barmode='stack', 
                            height=30, # Barra bem fininha e elegante
                            margin=dict(l=0,r=0,t=0,b=0), # Sem margens extras
                            showlegend=False, # Esconde a legenda do Plotly (já fizemos a nossa em HTML)
                            xaxis=dict(visible=False), # Esconde números do eixo X
                            yaxis=dict(visible=False), # Esconde eixo Y
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_prob, use_container_width=True)
                        st.divider()
            else:
                st.info("Sem jogos agendados no momento.")

    # ==========================================================================
    # VISÃO 2: ÁREA EXCLUSIVA CRUZEIRO
    # ==========================================================================
    elif opcao_menu == "Raio-X Cruzeiro":
        # Filtro só o Cruzeiro na tabela
        df_cru = df_tabela[df_tabela['Time'].str.contains("Cruzeiro", case=False)]
        
        if df_cru.empty:
            st.warning("⚠️ Dados do Cruzeiro não encontrados (o campeonato começou ou a API mudou o nome).")
        else:
            stats = df_cru.iloc[0]
            
            # HERO HEADER (CABEÇALHO BONITO COM DEGRADÊ)
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #00539F 0%, #002D58 100%); padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                <h1 style="color: white; margin:0; font-size: 2.5rem;">🦊 Cruzeiro Esporte Clube</h1>
                <p style="color: #e0e0e0; margin:0; font-size: 1.1rem;">Painel de Inteligência & Performance</p>
            </div>
            """, unsafe_allow_html=True)
            
            # --- KPI CARDS (Os cartões do topo) ---
            st.markdown("### 📊 Indicadores Chave (KPIs)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Posição na Tabela", f"{stats['Pos']}º Lugar")
            c2.metric("Pontos Conquistados", stats['Pontos'])
            # Calculo aproveitamento na hora: Pontos / (Jogos * 3)
            c3.metric("Aproveitamento Total", f"{(stats['Pontos']/(stats['Jogos']*3)*100):.1f}%")
            c4.metric("Saldo de Gols", stats['Saldo'])
            st.divider()
            
            # --- GRÁFICO 1: GOLS FEITOS x SOFRIDOS ---
            st.subheader("⚽ Equilíbrio: Ataque vs Defesa (Rodada a Rodada)")
            st.caption("Este gráfico ajuda a entender a consistência. Barras Azuis (Gols Feitos) devem ser maiores que as Vermelhas (Gols Sofridos).")
            
            # Filtro jogos do Cruzeiro (Casa ou Fora) que já acabaram
            jogos_cru = df_finalizados[(df_finalizados['Home'].str.contains('Cruzeiro')) | (df_finalizados['Away'].str.contains('Cruzeiro'))].sort_values('Rodada')
            
            if not jogos_cru.empty:
                # Preciso "derreter" os dados para o gráfico de barras agrupadas
                dados_grafico = []
                for _, row in jogos_cru.iterrows():
                    # Lógica para descobrir quem é quem
                    if 'Cruzeiro' in row['Home']:
                        gp, gs, adv, mando = row['Gols_Home'], row['Gols_Away'], row['Sigla_Away'], "(C)"
                    else:
                        gp, gs, adv, mando = row['Gols_Away'], row['Gols_Home'], row['Sigla_Home'], "(F)"
                    
                    dados_grafico.append({"Rodada": f"R{row['Rodada']} {mando}", "Tipo": "Gols Feitos", "Gols": gp, "Adv": adv})
                    # Rótulo corrigido para "Gols Sofridos"
                    dados_grafico.append({"Rodada": f"R{row['Rodada']} {mando}", "Tipo": "Gols Sofridos", "Gols": gs, "Adv": adv})
                
                # Gráfico com barras lado a lado (barmode='group')
                # Ajustei as cores para bater com os novos nomes
                fig_comp = px.bar(
                    pd.DataFrame(dados_grafico), 
                    x="Rodada", 
                    y="Gols", 
                    color="Tipo", 
                    barmode="group", 
                    color_discrete_map={"Gols Feitos":"#00539F", "Gols Sofridos":"#E74C3C"}
                )
                # Aplicando a formatação limpa (Função Nova)
                st.plotly_chart(formatar_grafico(fig_comp), use_container_width=True)
            
            st.divider()
            
            # --- INTELIGÊNCIA TÁTICA ---
            st.subheader("🧠 Inteligência Tática")
            st.markdown("Vamos aprofundar nos padrões de comportamento do time.")
            col_t1, col_t2 = st.columns(2)
            
            # Coluna 1: Desempenho por Tempo (1º vs 2º)
            with col_t1:
                st.markdown("#### ⏱️ Desempenho: 1º Tempo vs 2º Tempo")
                st.caption("O time 'acorda' tarde ou cansa no final? Barras vermelhas altas no 2º tempo indicam queda física ou desatenção.")
                g1p, g1c, g2p, g2c = 0, 0, 0, 0
                matches_cru_full = dados_jogos['matches'] # Pego o raw para ter acesso ao 'score' detalhado
                
                for m in matches_cru_full:
                    if m['status'] == 'FINISHED' and ('Cruzeiro' in m['homeTeam']['name'] or 'Cruzeiro' in m['awayTeam']['name']):
                        ishome = 'Cruzeiro' in m['homeTeam']['name']
                        # Trato nulos como 0
                        ht_h = m['score']['halfTime']['home'] or 0
                        ht_a = m['score']['halfTime']['away'] or 0
                        ft_h = m['score']['fullTime']['home'] or 0
                        ft_a = m['score']['fullTime']['away'] or 0
                        
                        # Acumulo os gols
                        if ishome:
                            g1p += ht_h; g1c += ht_a
                            g2p += (ft_h - ht_h); g2c += (ft_a - ht_a)
                        else:
                            g1p += ht_a; g1c += ht_h
                            g2p += (ft_a - ht_a); g2c += (ft_h - ht_h)
                            
                fig_tempos = go.Figure(data=[
                    go.Bar(name='Gols Pró', x=['1º Tempo', '2º Tempo'], y=[g1p, g2p], marker_color='#2ecc71'),
                    go.Bar(name='Gols Sofridos', x=['1º Tempo', '2º Tempo'], y=[g1c, g2c], marker_color='#e74c3c')
                ])
                fig_tempos.update_layout(barmode='group', height=300)
                # Aplicando a formatação limpa (Função Nova)
                st.plotly_chart(formatar_grafico(fig_tempos), use_container_width=True)
                
            # Coluna 2: Radar Chart (Casa vs Fora)
            with col_t2:
                st.markdown("#### 🏠 Fator Casa vs Visitante")
                st.caption("Aproveitamento percentual. Um gráfico 'torto' indica dependência do mando de campo. O ideal é um triângulo grande e equilibrado.")
                # Funçãozinha interna para calcular aproveitamento rápido
                def get_aprov(is_home):
                    subset = df_finalizados[df_finalizados['Home' if is_home else 'Away'].str.contains('Cruzeiro')]
                    if subset.empty: return 0
                    pts = 0
                    for _, r in subset.iterrows():
                        gh, ga = r['Gols_Home'], r['Gols_Away']
                        if is_home: pts += 3 if gh > ga else (1 if gh == ga else 0)
                        else: pts += 3 if ga > gh else (1 if ga == gh else 0)
                    return (pts / (len(subset)*3)) * 100
                
                ac, af = get_aprov(True), get_aprov(False)
                # O gráfico aranha precisa repetir o primeiro ponto no final para fechar o ciclo
                fig_radar = go.Figure(go.Scatterpolar(r=[ac, af, ac], theta=['Jogando em Casa', 'Visitante', 'Jogando em Casa'], fill='toself', line_color='#00539F'))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=300)
                # Aplicando a formatação limpa (Função Nova)
                st.plotly_chart(formatar_grafico(fig_radar), use_container_width=True)

            # --- PROJEÇÃO FINAL ---
            st.divider()
            st.subheader("🔮 Bola de Cristal: Projeção Final")
            st.markdown("Baseado na média de pontos atual, onde o Cruzeiro terminaria o campeonato?")
            
            if stats['Jogos'] > 0:
                # Regra de 3 simples: Se fiz X pontos em Y jogos, farei Z em 38 jogos.
                proj = int(stats['Pontos'] + (stats['Pontos']/stats['Jogos'] * (38 - stats['Jogos'])))
                
                # Barra de progresso visual (máximo 114 pontos)
                st.progress(min(proj/114, 1.0)) 
                
                # O Storytelling aqui é crucial: explicar POR QUE deu o alerta
                st.metric("Pontuação Projetada (Final do Campeonato)", f"{proj} Pontos")
                
                # Mensagens condicionais baseadas no histórico do Brasileirão
                if proj >= 58: 
                    st.success("🎉 **Cenário Otimista:** Com essa pontuação, brigamos por vaga na **Libertadores**!")
                elif proj >= 45: 
                    st.warning("🛡️ **Cenário Neutro:** Pontuação de vaga na **Sul-Americana** ou meio de tabela. Seguro contra o rebaixamento.")
                else: 
                    st.error(
                        """
                        🚨 **ALERTA Z-4 LIGADO!** Historicamente, times com menos de 45 pontos correm alto risco de rebaixamento. 
                        A projeção atual indica que o Cruzeiro precisa melhorar o aproveitamento urgentemente.
                        """
                    )
            else:
                st.info("Ainda temos poucos jogos para fazer uma projeção confiável.")

else:
    # Se caiu aqui, é porque a chave da API está errada ou a internet caiu.
    st.error("Falha ao carregar dados. Verifique a API Key ou sua conexão.")