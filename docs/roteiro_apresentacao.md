# Roteiro da apresentação final (AV2)

**Disciplina:** Fundamentos de Big Data
**Equipe:** Bruno Ribeiro, Cláudio Alves e Vinícius Ventura
**Duração alvo:** até 20 minutos
**Foco (critério oficial):** resultados e demonstração do projeto funcionando.

## Antes de começar (checklist de sala)

- [ ] Abrir `output/dashboard.html` no navegador **antes** da fala, em modo offline (desligar o Wi-Fi para confirmar que abre sem internet).
- [ ] Ter o arquivo `dashboard.html` em **pendrive/local**, não só no GitHub (não depender de download na hora).
- [ ] Deixar aberto, em abas, o `notebook 03` já executado e a pasta `output/figuras/` como **plano B**.
- [ ] Testar o projetor: tamanho de fonte e cores dos gráficos legíveis ao fundo da sala.

## Divisão de blocos e tempo

| Tempo | Bloco | Quem fala | Apoio visual |
| ----- | ----- | --------- | ------------ |
| 0-2 min | Contexto e pergunta de pesquisa | Cláudio | README (Introdução) |
| 2-7 min | Pipeline: bronze, silver e gold | Bruno | Notebook 00 + diagrama do README |
| 7-10 min | Metodologia e decisões técnicas | Bruno | README (Metodologia) |
| 10-18 min | Demonstração ao vivo dos resultados | Vinícius | `dashboard.html` (6 gráficos) |
| 18-20 min | Conclusões, limitações e perguntas | Cláudio | README (Conclusões) |

## Roteiro detalhado

### 1. Contexto e pergunta de pesquisa (2 min), Cláudio

- Problema: o impacto da COVID-19 nas internações do SUS em São Paulo, 2020 a 2023.
- Pergunta central: como as ondas da COVID-19 impactaram o volume de internações e a
  mortalidade hospitalar no SUS-SP?
- Fonte: SIH/SUS (DATASUS), quase 10 milhões de internações.

### 2. Pipeline de dados, com evidências (5 min), Bruno

> Este bloco responde diretamente ao feedback da AV1 (mostrar as camadas com saídas visuais).

- Arquitetura medalhão: bronze, silver, gold.
- Abrir o **notebook 00** e mostrar:
  - como os dados chegaram (volume de ingestão por mês);
  - o funil de limpeza: 9,85 milhões → 9,60 milhões de linhas (47.701 duplicatas e
    204.380 registros fora do período removidos);
  - redução de 113 campos para 26 colunas;
  - as 5 tabelas geradas na camada gold.

### 3. Metodologia e decisões técnicas (3 min), Bruno

- Ferramentas por etapa: `datasus-dbc`/`dbfread` (ingestão), `pandas`/`pyarrow`
  (processamento e armazenamento em Parquet), `plotly` (dashboard).
- Decisões: CID **B342** para COVID no SIH/SUS; janelas das ondas definidas pelos picos
  reais da série; auditoria de qualidade que aborta o pipeline em caso de falha.

### 4. Demonstração ao vivo dos resultados (8 min), Vinícius

Percorrer o `dashboard.html` na ordem das sub-perguntas, narrando pergunta → gráfico →
leitura (o dashboard não tem texto de ligação entre os gráficos; a narração faz essa
ponte):

1. **Volume mensal:** três ondas; pico em março de 2021 (Gama, 45.180 internações).
2. **Mortalidade mensal:** letalidade da COVID muito acima da dos demais motivos.
3. **Perfil por onda:** Gama com maior volume; letalidade subindo de 21,9% para 24,0%.
4. **COVID vs outros:** 23,0% vs 5,5% de óbito, mais que o triplo de UTI.
5. **Demografia:** letalidade cresce com a idade; homens 75+ com 40,1%.
6. **Geografia:** concentração na capital.

Mostrar a interatividade: hover, zoom e ligar/desligar séries.

**Aprofundamento (modelo probabilístico).** Fechar com o `notebook 04`: a regressão
logística de risco de óbito. Mostrar o gráfico de odds ratios (UTI ~5,2x, COVID ~2,6x,
idade ~1,6x por década) e a AUC ~0,85. Mensagem: o modelo confirma e quantifica os achados
descritivos, e mostra que a COVID tem efeito próprio no óbito mesmo controlando por idade
e UTI.

### 5. Conclusões e limitações (2 min), Cláudio

- Síntese dos achados principais.
- Limitações: base administrativa (só SUS), CID B342 pode subnotificar, janelas de onda
  são convenção analítica.
- Trabalhos futuros: outros estados, cruzamento com vacinação e população, previsão de
  demanda por leitos.
- Abertura para perguntas.

## Plano B (se algo falhar na sala)

1. Se o `dashboard.html` não abrir: usar as 6 imagens em `output/figuras/` (PNG estático).
2. Se faltar o equipamento: apresentar pelo **notebook 03**, que já tem os gráficos e os
   blocos de leitura executados.
3. Se o tempo apertar: priorizar os gráficos 1, 2 e 4 (volume, mortalidade e COVID vs
   outros), que carregam a mensagem central.

## Ensaio (pendente, atividade da equipe)

- [ ] Ensaio 1 cronometrado, com o dashboard aberto offline.
- [ ] Ensaio 2 cronometrado, ajustando o tempo de cada bloco para caber em 20 minutos.
- [ ] Confirmar quem fala cada parte e a transição entre os integrantes.
