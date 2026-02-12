# ⚽ Brasileirão Analytics Pro

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow)

> **Dashboard de Inteligência de Dados** para análise tática e estatística do Campeonato Brasileiro, focado em visualização de dados moderna (Glassmorphism) e modelagem preditiva.

## 📋 Sobre o Projeto

Este projeto é uma aplicação web interativa desenvolvida em **Python** e **Streamlit** que consome dados em tempo real da [Football-Data.org API](https://www.football-data.org/). 

O objetivo é ir além da tabela tradicional, oferecendo métricas avançadas como **Gols Esperados (xG)** baseados em distribuição de Poisson e análise de desempenho detalhada por tempos de jogo.

---

## 🚀 Funcionalidades Principais

### 1. 📊 Panorama Geral
- **Tabela Interativa:** Classificação atualizada com escudos, barras de progresso para pontos e visualização limpa.
- **Matriz de Eficiência (Scatter Plot):** Gráfico de quadrantes cruzando *Ataque (Gols Pró)* vs *Defesa (Gols Sofridos)* para identificar o perfil tático dos times.
- **Visualização Glassmorphism:** Interface moderna com CSS personalizado, transparências e modo escuro nativo.

### 2. 🧠 Modelo Preditivo (IA)
- **Cálculo de Força:** Algoritmo que calcula o "Power Ranking" de ataque e defesa (Casa/Fora) de cada time em relação à média da liga.
- **Distribuição de Poisson:** Simulação matemática das probabilidades de vitória, empate e derrota para os próximos jogos agendados.

### 3. 🦊 Raio-X Cruzeiro (Módulo Exclusivo)
- **Dashboard Dedicado:** KPIs específicos do Cruzeiro Esporte Clube.
- **Análise Temporal:** Comparativo de desempenho entre o 1º e 2º tempo (gols feitos x sofridos).
- **Radar Chart:** Gráfico aranha para visualizar o aproveitamento como Mandante vs Visitante.
- **Projeção de Pontos:** Estimativa final de pontuação baseada no aproveitamento atual e histórico do campeonato.

---

## 🛠️ Tecnologias Utilizadas

* **[Streamlit](https://streamlit.io/):** Framework para construção do Web App.
* **[Pandas](https://pandas.pydata.org/):** Manipulação e limpeza de dados (ETL).
* **[Plotly Express & GO](https://plotly.com/python/):** Gráficos interativos e responsivos.
* **[SciPy](https://scipy.org/):** Cálculos estatísticos (Distribuição de Poisson).
* **[NumPy](https://numpy.org/):** Operações matemáticas de alta performance.

---

## 📦 Como Rodar o Projeto Localmente

Siga os passos abaixo para executar o dashboard na sua máquina:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SEU-USUARIO/brasileirao-analytics-pro.git](https://github.com/SEU-USUARIO/brasileirao-analytics-pro.git)
    cd brasileirao-analytics-pro
    ```

2.  **Crie um ambiente virtual (Opcional, mas recomendado):**
    ```bash
    python -m venv venv
    # No Windows:
    venv\Scripts\activate
    # No Mac/Linux:
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a API Key:**
    * O código utiliza uma chave da [Football-Data.org](https://www.football-data.org/).
    * Edite o arquivo `app.py` (ou use `st.secrets` para produção) e insira sua chave na variável `API_KEY`.

5.  **Execute o Streamlit:**
    ```bash
    streamlit run app.py
    ```
   ## 📂 Estrutura de Arquivos
   ---

## ⚠️ Nota Importante sobre a API

Este projeto utiliza a **Tier Gratuita** da API Football-Data.org. 
* **Limite:** 10 requisições por minuto.
* **Cache:** O sistema utiliza `@st.cache_data` com TTL de 1 hora para evitar bloqueios e economizar requisições.

---
## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma _issue_ ou enviar um _pull request_.

1.  Faça um Fork do projeto
2.  Crie uma Branch para sua Feature (`git checkout -b feature/IncrívelFeature`)
3.  Faça o Commit (`git commit -m 'Add some IncrívelFeature'`)
4.  Push para a Branch (`git push origin feature/IncrívelFeature`)
5.  Abra um Pull Request

---

**Desenvolvido com 💙 e Python.**
---




