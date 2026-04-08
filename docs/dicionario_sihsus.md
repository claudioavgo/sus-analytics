# Dicionario de Dados -- SIH/SUS (AIH Reduzida)

## Visao geral

- **Fonte:** DATASUS / Sistema de Informacoes Hospitalares do SUS
- **Tipo de arquivo:** RD*.dbc (DBF comprimido com PKWare blast)
- **Nomenclatura:** `RD{UF}{AA}{MM}.dbc` -- ex: `RDSP2301.dbc` = Sao Paulo, Jan/2023
- **Cobertura:** 27 UFs, Jan/2020 a Dez/2023 (todos os meses)
- **Total de arquivos:** 1.296
- **Volume estimado:** ~3.4 GB (comprimido)
- **Registros por arquivo:** varia por UF/mes (ex: AC Jan/2020 = 3.784 registros)
- **Campos por registro:** 113

## Como ler os arquivos

Os `.dbc` precisam ser descomprimidos antes da leitura:

```python
from datasus_dbc import decompress
from dbfread import DBF

decompress("RDAC2001.dbc", "RDAC2001.dbf")
table = DBF("RDAC2001.dbf", encoding="latin-1")
```

## Schema completo (113 campos)

### Identificacao administrativa

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| UF_ZI | char | 6 | Municipio gestor da AIH |
| ANO_CMPT | char | 4 | Ano de processamento (aaaa) |
| MES_CMPT | char | 2 | Mes de processamento (mm) |
| N_AIH | char | 13 | Numero da AIH |
| IDENT | char | 1 | Tipo de AIH (1=Normal, 5=Longa permanencia) |
| ESPEC | char | 2 | Especialidade do leito |
| CGC_HOSP | char | 14 | CNPJ do hospital |
| CNES | char | 7 | Codigo CNES do estabelecimento |
| CNPJ_MANT | char | 14 | CNPJ da mantenedora |
| NATUREZA | char | 2 | Natureza juridica (conteudo ate Mai/2012) |
| NAT_JUR | char | 4 | Natureza juridica conforme CONCLA |
| GESTAO | char | 1 | Tipo de gestao do hospital |
| MUNIC_MOV | char | 6 | Municipio do estabelecimento |
| SEQUENCIA | numeric | 9 | Sequencia da AIH na remessa |
| REMESSA | char | 21 | Numero da remessa |

### Dados do paciente

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| CEP | char | 8 | CEP do paciente |
| MUNIC_RES | char | 6 | Municipio de residencia do paciente (cod. IBGE) |
| NASC | char | 8 | Data de nascimento (aaaammdd) |
| SEXO | char | 1 | Sexo (1=Masculino, 3=Feminino) |
| COD_IDADE | char | 1 | Unidade de medida da idade (4=Anos) |
| IDADE | numeric | 2 | Idade do paciente |
| RACA_COR | char | 2 | Raca/cor do paciente |
| ETNIA | char | 4 | Etnia (se indigena) |
| NACIONAL | char | 3 | Codigo de nacionalidade |
| INSTRU | char | 1 | Grau de instrucao |
| CBOR | char | 6 | Ocupacao do paciente (CBO) |
| NUM_FILHOS | numeric | 2 | Numero de filhos |

### Internacao

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| DT_INTER | char | 8 | Data de internacao (aaaammdd) |
| DT_SAIDA | char | 8 | Data de saida (aaaammdd) |
| DIAS_PERM | numeric | 5 | Dias de permanencia |
| QT_DIARIAS | numeric | 3 | Quantidade de diarias |
| DIAR_ACOM | numeric | 3 | Diarias de acompanhante |
| CAR_INT | char | 2 | Carater da internacao (eletiva/urgencia) |
| COBRANCA | char | 2 | Motivo de saida/permanencia |
| MORTE | numeric | 1 | Indicador de obito (0=Nao, 1=Sim) |
| COMPLEX | char | 2 | Nivel de complexidade |
| INFEHOSP | char | 1 | Infeccao hospitalar |

### Diagnosticos (CID-10)

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| DIAG_PRINC | char | 4 | Diagnostico principal (CID-10) |
| DIAG_SECUN | char | 4 | Diagnostico secundario (zerado a partir de 201501) |
| CID_NOTIF | char | 4 | CID de notificacao |
| CID_ASSO | char | 4 | CID associada/causa |
| CID_MORTE | char | 4 | CID do obito |
| DIAGSEC1 a DIAGSEC9 | char | 4 | Diagnosticos secundarios 1 a 9 |
| TPDISEC1 a TPDISEC9 | char | 1 | Tipos dos diagnosticos secundarios 1 a 9 |

### Procedimentos

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| PROC_SOLIC | char | 10 | Procedimento solicitado |
| PROC_REA | char | 10 | Procedimento realizado |

### Valores financeiros (R$)

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| VAL_SH | numeric | 13,2 | Valor dos servicos hospitalares |
| VAL_SP | numeric | 13,2 | Valor dos servicos profissionais |
| VAL_TOT | numeric | 14,2 | Valor total da AIH |
| VAL_UTI | numeric | 8,2 | Valor de UTI |
| US_TOT | numeric | 10,2 | Valor total em USD |
| VAL_SH_FED | numeric | 10,2 | Complemento federal - servicos hospitalares |
| VAL_SP_FED | numeric | 10,2 | Complemento federal - servicos profissionais |
| VAL_SH_GES | numeric | 10,2 | Complemento gestor - servicos hospitalares |
| VAL_SP_GES | numeric | 10,2 | Complemento gestor - servicos profissionais |
| VAL_UCI | numeric | 10,2 | Valor da unidade de cuidados intermediarios |
| FINANC | char | 2 | Tipo de financiamento |
| FAEC_TP | char | 6 | Subtipo de financiamento FAEC |
| REGCT | char | 4 | Regra contratual |

### UTI e unidades intermediarias

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| UTI_MES_TO | numeric | 3 | Dias de UTI no mes |
| UTI_INT_TO | numeric | 3 | Dias de unidade intermediaria |
| MARCA_UTI | char | 2 | Tipo de UTI utilizada |
| MARCA_UCI | char | 2 | Tipo de UCI utilizada |

### Campos legados (zerados)

Os seguintes campos existem no layout mas nao sao mais preenchidos:

`UTI_MES_IN`, `UTI_MES_AN`, `UTI_MES_AL`, `UTI_INT_IN`, `UTI_INT_AN`, `UTI_INT_AL`,
`VAL_SADT`, `VAL_RN`, `VAL_ACOMP`, `VAL_ORTP`, `VAL_SANGUE`, `VAL_SADTSR`,
`VAL_TRANSP`, `VAL_OBSANG`, `VAL_PED1AC`, `RUBRICA`, `NUM_PROC`, `TOT_PT_SP`, `CPF_AUT`

### Campos obstetricos/especificos

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| GESTRISCO | char | 1 | Gestacao de alto risco |
| INSC_PN | char | 12 | Numero de inscricao pre-natal |
| CONTRACEP1 | char | 2 | Tipo de contraceptivo 1 |
| CONTRACEP2 | char | 2 | Tipo de contraceptivo 2 |
| IND_VDRL | char | 1 | Indicador de exame VDRL |
| HOMONIMO | char | 1 | Indicador de homonimo |
| SEQ_AIH5 | char | 3 | Sequencia de longa permanencia (AIH tipo 5) |
| VINCPREV | char | 1 | Vinculo previdenciario |
| CNAER | char | 3 | Codigo de acidente de trabalho |

### Gestor/auditoria

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| GESTOR_COD | char | 5 | Motivo de autorizacao pelo gestor |
| GESTOR_TP | char | 1 | Tipo de gestor |
| GESTOR_CPF | char | 15 | CPF do gestor |
| GESTOR_DT | char | 8 | Data da autorizacao do gestor |
| AUD_JUST | char | 50 | Justificativa do auditor |
| SIS_JUST | char | 50 | Justificativa do estabelecimento |

## Campos relevantes para a pesquisa

Para a analise de internacoes x fatores socioeconomicos, os campos mais relevantes sao:

- **Chave de join com IBGE:** `MUNIC_RES` (municipio de residencia, cod. IBGE 6 digitos)
- **Temporal:** `ANO_CMPT`, `MES_CMPT`, `DT_INTER`, `DT_SAIDA`
- **Internacao:** `DIAS_PERM`, `DIAG_PRINC`, `PROC_REA`, `CAR_INT`, `COMPLEX`, `MORTE`
- **Financeiro:** `VAL_TOT`, `VAL_SH`, `VAL_SP`
- **Demografico:** `SEXO`, `IDADE`, `COD_IDADE`, `RACA_COR`
- **Geografico:** `MUNIC_MOV` (onde ocorreu), `MUNIC_RES` (onde mora)
