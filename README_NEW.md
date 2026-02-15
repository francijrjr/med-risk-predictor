# Sistema Preditivo de Escassez de Medicamentos em PSFs

Sistema completo de Machine Learning com **autenticação de usuários** e **gerenciamento de documentos** para prever o consumo de medicamentos essenciais em Postos de Saúde da Família (PSFs) e classificar o risco de escassez, utilizando dados públicos do DATASUS.

## Objetivo

Apoiar gestores públicos de saúde na tomada de decisão proativa, prevenindo escassez de medicamentos através de previsões baseadas em dados históricos de dispensação.

## Principais Funcionalidades

### Sistema de Autenticação

- Login e registro de usuários
- Senha criptografada (SHA-256)
- Controle de sessão
- Perfis de usuário (Admin / User)
- Alteração de senha

### Gerenciamento de Documentos

- Upload de arquivos CSV
- Validação automática de formato
- Preview de dados antes do envio
- Listagem de documentos enviados
- Controle de permissões por usuário
- Admin pode visualizar todos os documentos

### Dashboard Preditivo

- 5 KPIs em tempo real
- Cards de alertas críticos com gradiente visual
- Gráficos interativos (Plotly)
- Análise histórica vs predição
- Ranking de déficit por medicamento
- Tabelas organizadas por nível de risco

## Tecnologias

- **Python 3.11+**
- **Streamlit** - Interface web interativa
- **Pandas** - Manipulação de dados
- **Scikit-learn** - Machine Learning
- **Plotly** - Visualizações interativas
- **Requests** - Consumo de dados públicos

## Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório ou extraia os arquivos

2. Navegue até o diretório do projeto:

```bash
cd med-risk-predictor
```

3. Instale as dependências:

```bash
python -m pip install streamlit pandas scikit-learn plotly matplotlib requests numpy openpyxl
```

Ou usando o arquivo requirements.txt:

```bash
pip install -r requirements.txt
```

## ▶Execução

### Versão com Autenticação (Recomendada)

Para iniciar o sistema completo com login e upload de documentos:

```bash
streamlit run app_auth.py
```

**Credenciais padrão:**

- Usuário: `admin`
- Senha: `admin123`

### Versão Simples (Sem Autenticação)

Para iniciar apenas o dashboard preditivo:

```bash
streamlit run app.py
```

O sistema será aberto automaticamente no navegador em `http://localhost:8501` ou `http://localhost:8504`

## Estrutura do Projeto

```
med-risk-predictor/
│
├── app.py                          # Dashboard Streamlit (versão simples)
├── app_auth.py                     # Dashboard com autenticação e upload
├── requirements.txt                # Dependências do projeto
├── README.md                       # Documentação principal
├── feature.md                      # Documentação de features
│
├── data/
│   ├── samples/
│   │   └── datasus_sample.csv     # Dados de exemplo
│   ├── uploads/                   # Arquivos enviados pelos usuários
│   │   └── metadata.json          # Metadados dos uploads
│   └── users.json                 # Banco de dados de usuários
│
└── src/
    ├── ingestion/                 # Ingestão de dados
    │   ├── __init__.py
    │   ├── datasus_client.py      # Cliente HTTP para DATASUS
    │   └── loader.py              # Carregamento de dados
    │
    ├── preprocessing/             # Pré-processamento
    │   ├── __init__.py
    │   └── cleaning.py            # Limpeza e agregação
    │
    ├── features/                  # Engenharia de features
    │   ├── __init__.py
    │   └── engineering.py         # Criação de variáveis
    │
    ├── models/                    # Modelos de ML
    │   ├── __init__.py
    │   ├── train.py               # Treinamento Random Forest
    │   ├── predict.py             # Predições futuras
    │   └── risk_classifier.py     # Classificação de risco
    │
    ├── visualization/             # Visualizações
    │   ├── __init__.py
    │   └── dashboard.py           # Componentes do dashboard
    │
    └── utils/                     # Utilitários
        ├── __init__.py
        ├── helpers.py             # Funções auxiliares
        ├── auth.py                # Sistema de autenticação
        └── document_manager.py    # Gerenciador de documentos
```

## Funcionalidades do Sistema de Autenticação

### Registro de Usuário

1. Acesse a opção "Registrar novo usuário" na página de login
2. Preencha:
   - Nome de usuário (único)
   - Senha (mínimo 6 caracteres)
   - Email válido
3. Usuário será criado com perfil "user"

### Login

1. Insira suas credenciais
2. Mantenha a sessão ativa enquanto usa o sistema
3. Use "Logout" para sair

### Alteração de Senha

1. Acesse "Perfil" no menu lateral
2. Preencha senha atual e nova senha
3. Confirme a alteração

### Perfis de Acesso

- **Admin**: Acesso total + visualizar documentos de todos os usuários
- **User**: Upload e visualização dos próprios documentos

## Upload de Documentos CSV

### Formato Esperado

O arquivo CSV deve conter as seguintes colunas:

```csv
medicamento,data,consumo,estoque_atual
Paracetamol,2024-01,1500,4500
Ibuprofeno,2024-01,800,2400
```

### Campos Obrigatórios

- `medicamento` - Nome do medicamento
- `data` - Período (formato: YYYY-MM)
- `consumo` - Quantidade dispensada
- `estoque_atual` - Estoque disponível

### Como Fazer Upload

1. Faça login no sistema
2. Acesse "Upload de Documentos" no menu
3. Selecione o arquivo CSV
4. Visualize os dados
5. Clique em "Enviar Arquivo"
6. O sistema valida automaticamente o formato

## Funcionalidades do Dashboard

### Indicadores-Chave (KPIs)

- **Total de Medicamentos**: Quantidade total sob análise
- **Medicamentos em Risco**: Quantidade com alerta Alto/Médio
- **Taxa de Risco**: Percentual de medicamentos em risco
- **Consumo Total Previsto**: Soma das previsões (3 meses)
- **Déficit Total**: Diferença entre estoque e consumo previsto

### Alertas Críticos

Cards visuais destacando os medicamentos com maior risco de escassez, mostrando:

- Nome do medicamento
- Nível de risco (Alto/Médio/Baixo)
- Déficit estimado
- Gradiente de cores por gravidade

### Visualizações Interativas

- **Distribuição de Risco**: Gráfico de pizza com proporção por nível
- **Ranking de Déficit**: Medicamentos ordenados por maior déficit
- **Histórico vs Predição**: Série temporal com dados reais e previstos
- **Tabela de Alertas**: Dados completos organizados por risco

## Machine Learning

### Modelo Utilizado

**Random Forest Regressor**

- `n_estimators`: 100 árvores
- `max_depth`: 10 níveis
- `random_state`: 42

### Features Criadas

1. **Tendência**: Taxa de crescimento do consumo
2. **Sazonalidade**: Média móvel (3 e 6 meses)
3. **Volatilidade**: Desvio padrão móvel
4. **Coeficiente de Variação**: Estabilidade do consumo

### Predições

- **Horizonte**: 3 meses futuros
- **Output**: Consumo esperado por medicamento/mês
- **Acurácia**: Validação cross-validation disponível

### Classificação de Risco

| Nível    | Critério (Estoque / Consumo Previsto) | Cor      |
| -------- | ------------------------------------- | -------- |
| 🔴 Alto  | < 1.5 meses                           | Vermelho |
| 🟡 Médio | 1.5 - 3 meses                         | Amarelo  |
| 🟢 Baixo | > 3 meses                             | Verde    |

## Dados e Segurança

### Fonte de Dados

O sistema utiliza dados públicos do DATASUS (SIA/SUS, SIH/SUS) contendo:

- **medicamento**: Nome do medicamento
- **data**: Período de referência (YYYY-MM)
- **consumo**: Quantidade dispensada
- **estoque_atual**: Estoque disponível

Em caso de indisponibilidade do DATASUS, o sistema utiliza dados simulados para demonstração.

### Segurança e Privacidade

- **Senhas**: Criptografadas com SHA-256
- **Armazenamento**: JSON local (users.json)
- **Sessões**: Gerenciadas pelo Streamlit
- **Uploads**: Validação automática de formato
- **Conformidade LGPD**: Sistema preparado para dados de saúde pública

## Uso do Sistema

### Passo 1: Primeiro Acesso

1. Execute `streamlit run app_auth.py`
2. Faça login com credenciais admin (admin/admin123)
3. Crie novos usuários se necessário

### Passo 2: Upload de Dados

1. Prepare arquivo CSV no formato especificado
2. Acesse "Upload de Documentos"
3. Faça o upload e valide os dados

### Passo 3: Análise Preditiva

1. Acesse "Dashboard" no menu
2. Filtre por medicamento/período
3. Analise KPIs, gráficos e alertas
4. Identifique medicamentos em risco

### Passo 4: Tomada de Decisão

- Priorize compras baseado no ranking de déficit
- Monitore tendências de consumo
- Ajuste estoques proativamente
- Exporte dados para relatórios

## Personalização

### Alterar Parâmetros do Modelo

Edite [src/models/train.py](src/models/train.py):

```python
model = RandomForestRegressor(
    n_estimators=150,  # Aumentar árvores
    max_depth=15,      # Aumentar profundidade
    random_state=42
)
```

### Ajustar Classificação de Risco

Edite [src/models/risk_classifier.py](src/models/risk_classifier.py):

```python
def classify_risk(months_of_stock):
    if months_of_stock < 2:    # Era 1.5
        return "Alto"
    elif months_of_stock < 4:  # Era 3
        return "Médio"
    else:
        return "Baixo"
```

### Adicionar Novos Medicamentos

Edite o arquivo [data/samples/datasus_sample.csv](data/samples/datasus_sample.csv):

```csv
medicamento,data,consumo,estoque_atual
Nome do Medicamento,YYYY-MM,quantidade,estoque
```

## Solução de Problemas

### Erro ao instalar dependências

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Porta em uso (8501 ou 8504)

```bash
streamlit run app_auth.py --server.port 8505
```

### Dados não carregam

- Verifique a conexão com internet (para DATASUS)
- O sistema automaticamente usará dados simulados em caso de falha

### Erro de login

1. Verifique se o arquivo [data/users.json](data/users.json) existe
2. Tente criar novo usuário
3. Use credenciais admin padrão: admin/admin123

### Erro ao fazer upload

- Verifique se o CSV tem as colunas obrigatórias
- Certifique-se de que a coluna "data" está no formato YYYY-MM
- Valores numéricos devem estar corretos em "consumo" e "estoque_atual"

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

- Reportar bugs
- Sugerir novas funcionalidades
- Melhorar a documentação
- Otimizar algoritmos

## Licença

Este é um projeto de código aberto para fins educacionais e de demonstração.

## Suporte

Para dúvidas ou sugestões sobre o sistema preditivo de escassez de medicamentos, consulte a documentação em [feature.md](feature.md).


