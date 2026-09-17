# Med / Risco

Protótipo acadêmico de apoio ao planejamento do abastecimento farmacêutico na atenção básica, desenvolvido no contexto do TCC do IFCE sobre os PSFs do Crato.

O dashboard apresenta demanda prevista, saldo informado, reserva de segurança, necessidade total e prioridades por unidade e medicamento. A interface utiliza ícones SVG do Lucide, armazenados localmente, sem CDN ou JavaScript externo.

## Executar

Ambiente testado: Python 3.12. Use Python 3.11 ou 3.12 com as versões fixadas em requirements.txt.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Para contas locais e documentos persistidos:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_auth.py
```

Crie uma conta na tela inicial. Não há criação automática de administrador nem credencial padrão nova. Contas locais existentes são preservadas. A autenticação local e o armazenamento JSON são destinados ao protótipo; uma implantação multiusuário exige persistência transacional e autenticação institucional.

## Importação

Selecione **Enviar CSV** na barra lateral. Na versão autenticada, também é possível salvar um histórico em **Documentos** e selecioná-lo em **Documentos salvos**.

```csv
unidade,medicamento,data,consumo,estoque_atual
PSF Centro,PARACETAMOL 500MG COMPRIMIDO,2024-01,1500,2000
PSF Centro,PARACETAMOL 500MG COMPRIMIDO,2024-02,1600,1800
```

- Obrigatórias: medicamento, data, consumo e estoque_atual. Unidade é opcional.
- Um registro consolidado por unidade, medicamento e mês, com saldo no encerramento do mês.
- Data no formato YYYY-MM; números não negativos, sem separador de milhar.
- CSV UTF-8 separado por vírgula ou ponto e vírgula; decimais com ponto.
- Identifique dose, apresentação e unidade de medida no nome do medicamento. Não misture frascos e comprimidos na mesma série.
- Consumo ausente, mês inválido, meses faltantes e duplicidades bloqueiam a análise com uma mensagem explicativa.
- Estoque vazio significa desconhecido. Nunca é convertido automaticamente em zero.
- Picos de consumo são preservados. Não se eliminam possíveis surtos automaticamente.
- Cada série exige pelo menos 9 + horizonte meses: 12 para prever três meses. Séries curtas são identificadas e excluídas explicitamente.
- Limite de upload: 10 MB. Não inclua dados pessoais de pacientes.

## Cálculo do TCC

```text
Reserva de segurança = demanda prevista no horizonte × percentual de segurança
Necessidade total = demanda prevista + reserva de segurança
Índice de risco = necessidade total / saldo disponível
Reposição estimada = máximo(0, necessidade total - saldo disponível)
```

| Risco | Critério |
| --- | --- |
| Baixo | Índice < 1,0 |
| Médio | 1,0 ≤ índice ≤ 1,3 |
| Alto | Índice > 1,3 |
| Sem dados | Saldo desconhecido ou saldo e demanda iguais a zero |

Saldo zero com demanda positiva gera risco alto. A reserva padrão de 20% é ajustável e se aplica a toda a análise. Os limiares seguem o exemplo metodológico do TCC, **sem calibração municipal**. O horizonte começa após o último registro de cada série, não na data atual. Datas dos saldos aparecem no painel.

A demanda é acumulada no horizonte escolhido e comparada ao último saldo, sem entradas intermediárias. Quantidades de medicamentos diferentes não são somadas em um indicador geral.

## Previsão e avaliação

Um Random Forest independente é treinado por unidade/medicamento. As variáveis são calendário cíclico, consumos defasados em 1, 2 e 3 meses e médias de consumos anteriores em janelas de 3 e 6 meses.

Os últimos H meses são reservados para teste, onde H é o horizonte escolhido. As previsões de teste são recursivas: nenhuma observação real desse intervalo alimenta os meses subsequentes. A referência simples repete o último consumo do treinamento.

MAE, RMSE e R² são apresentados por série, junto ao MAE da referência e às datas dos conjuntos. R² não é acurácia e fica indisponível para um único ponto ou alvo constante. Após o teste, o modelo é reajustado com todo o histórico para prever os próximos H meses.

Trata-se de uma única janela retrospectiva, não de validação operacional. A comparação de modelos em múltiplas janelas, os intervalos de previsão e a avaliação de alertas com gestores permanecem pendentes.

## Origem e limitações

O arquivo data/samples/datasus_sample.csv é tratado exclusivamente como demonstração de procedência não validada. Seu nome não comprova extração do DATASUS.

A integração automática com DATASUS está desativada e explicitamente não implementada. Arquivos enviados têm origem declarada pelo usuário. O modelo não inclui indicadores epidemiológicos, prazo de entrega, lotes, validade, perdas ou entradas futuras. As recomendações não executam compras.

A implementação e seus testes de software não demonstram eficácia nos PSFs do Crato. Essa conclusão exige dados municipais, protocolo de avaliação e validação com gestores.

## Organização

- app.py / app_auth.py: pontos de entrada e navegação.
- src/analysis.py: coordenação da análise, sem dependência da interface.
- src/preprocessing/cleaning.py: validação dos históricos.
- src/features/engineering.py: variáveis calculadas somente com o passado.
- src/models/: treinamento, previsão e regra de risco.
- src/visualization/: dashboard compartilhado e componentes visuais.
- src/utils/: contas locais, documentos e formatação.
- assets/lucide/: SVGs do Lucide 0.468.0 e licença original.
- tests/: regressões dos cálculos, validação e fluxo Streamlit.

## Verificar

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Arquivos de usuários, uploads, ambientes virtuais e caches ficam fora do controle de versão.
