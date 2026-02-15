# Funcionalidades do Sistema Preditivo de Escassez de Medicamentos

## Funcionalidades Implementadas

### 1. Ingestão de Dados

- **Conexão com DATASUS**: Consumo automático de dados públicos via HTTP/FTP
- **Fallback com dados simulados**: Sistema resiliente que funciona mesmo sem conexão
- **Loader configurável**: Suporte para múltiplas fontes de dados

### 2. Pré-processamento

- **Limpeza automática**: Remoção de valores nulos e inconsistentes
- **Agregação mensal**: Consolidação de dados por medicamento e período
- **Normalização**: Padronização de formatos de data e nomes de medicamentos

### 3. Engenharia de Features

- **Tendência histórica**: Cálculo de tendência linear dos últimos 12 meses
- **Sazonalidade**: Detecção de padrões sazonais mensais
- **Média móvel**: Cálculo de médias móveis de 3 e 6 meses
- **Features derivadas**: Taxa de crescimento, desvio padrão, coeficiente de variação

### 4. Modelo Preditivo

- **Algoritmo**: Random Forest Regressor
- **Horizon de previsão**: 3 meses à frente
- **Validação**: Split temporal train/test
- **Métricas**: MAE, RMSE, R²

### 5. Classificação de Risco

- **Risco Alto**: Estoque < Previsão (vermelho)
- **Risco Médio**: Previsão ≤ Estoque < Previsão × 1.2 (amarelo)
- **Risco Baixo**: Estoque ≥ Previsão × 1.2 (verde)

### 6. Dashboard Interativo

- **KPIs principais**:
  - Total de medicamentos monitorados
  - Alertas de risco alto
  - Alertas de risco médio
  - Acurácia do modelo

- **Visualizações**:
  - Gráfico de série temporal (histórico vs previsão)
  - Tabela de alertas colorida por nível de risco
  - Gráfico de distribuição de riscos
  - Métricas de performance do modelo

- **Filtros**:
  - Seleção por medicamento
  - Filtro por nível de risco
  - Período de análise

### 7. Conformidade e Segurança

- **LGPD**: Uso exclusivo de dados agregados (sem informações pessoais)
- **Dados públicos**: Fonte oficial DATASUS
- **Open source**: Todas as bibliotecas são de código aberto

## Casos de Uso

1. **Gestão Proativa**: Identificar medicamentos com risco de escassez antes que aconteça
2. **Otimização de Estoque**: Ajustar níveis de estoque baseado em previsões
3. **Tomada de Decisão**: Priorizar compras e distribuição de medicamentos
4. **Monitoramento Contínuo**: Acompanhar tendências de consumo em tempo real
5. **Planejamento Estratégico**: Análise de padrões sazonais para planejamento anual

## Fluxo de Dados

```
DATASUS → Ingestão → Limpeza → Engenharia de Features → Modelo ML → Classificação de Risco → Dashboard
```

## Roadmap Futuro

- [ ] Integração com API do DATASUS em tempo real
- [ ] Alertas automáticos via email/SMS
- [ ] Modelos específicos por região geográfica
- [ ] Análise de fatores externos (epidemias, sazonalidade climática)
- [ ] Exportação de relatórios em PDF
- [ ] API REST para integração com outros sistemas
