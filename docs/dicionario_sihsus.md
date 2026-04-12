# Dicionário de Dados — SIH/SUS (AIH Reduzida)

## Visão geral

- **Fonte:** DATASUS / Sistema de Informações Hospitalares do SUS
- **Tipo de arquivo:** `RD*.dbc` (DBF comprimido com PKWare blast)
- **Nomenclatura:** `RD{UF}{AA}{MM}.dbc` — ex: `RDSP2301.dbc` = São Paulo, Jan/2023
- **Recorte deste projeto:** SP (São Paulo), Jan/2020 a Dez/2023
- **Total de arquivos:** 48
- **Registros por arquivo:** ~195k a ~216k
- **Campos por registro:** 113 (17 selecionados para este projeto)

---

## Como ler os arquivos

Os `.dbc` precisam ser descomprimidos antes da leitura:

```python
from datasus_dbc import decompress
from dbfread import DBF

decompress("RDSP2301.dbc", "RDSP2301.dbf")
table = DBF("RDSP2301.dbf", encoding="latin-1")
```

Ou via `src/ingest.py`, que faz isso automaticamente para todos os 48 arquivos.

---

## Nota sobre o CID do COVID-19

O DATASUS SIH/SUS registra internações por COVID-19 com o CID **B342**
(Infecção por coronavirus, não especificada), e **não** utiliza os códigos
U07.1/U07.2 do CID-10 oficial nos arquivos do período 2020-2023.

| CID  | Descrição                             | Uso no SIH/SUS |
| ---- | ------------------------------------- | -------------- |
| B342 | Infecção por coronavirus NE           | Sim — COVID-19 |
| U071 | COVID-19, vírus identificado (CID-10) | Não encontrado |
| U072 | COVID-19, vírus não identificado      | Não encontrado |

Volumes observados (SP):

| Mês/Ano  | Internações B342 | Contexto epidêmico         |
| -------- | ---------------- | -------------------------- |
| Mar/2020 | 29               | Início da pandemia         |
| Jun/2020 | 14.911           | Primeira onda              |
| Jan/2021 | 16.861           | Segunda onda (início)      |
| Abr/2021 | 41.360           | Pico - variante Gama (P.1) |
| Jan/2022 | 7.614            | Onda Ômicron               |
| Jun/2022 | 1.598            | Declínio pós-Ômicron       |
| Jan/2023 | 967              | COVID endêmico             |

---

## Campos selecionados para este projeto (17 de 113)

| Campo      | Tipo  | Descrição                                       |
| ---------- | ----- | ----------------------------------------------- |
| ANO_CMPT   | str   | Ano de processamento                            |
| MES_CMPT   | str   | Mês de processamento                            |
| DT_INTER   | date  | Data de internação (aaaammdd)                   |
| DT_SAIDA   | date  | Data de saída (aaaammdd)                        |
| MUNIC_RES  | str   | Município de residência do paciente (cod. IBGE) |
| MUNIC_MOV  | str   | Município do estabelecimento                    |
| DIAG_PRINC | str   | Diagnóstico principal (CID-10)                  |
| MORTE      | int   | Óbito (0=Não, 1=Sim)                            |
| DIAS_PERM  | int   | Dias de permanência                             |
| UTI_MES_TO | int   | Dias de UTI no mês                              |
| CAR_INT    | str   | Caráter da internação (eletiva/urgência)        |
| COMPLEX    | str   | Nível de complexidade                           |
| SEXO       | str   | Sexo do paciente (1=Masc, 3=Fem)                |
| IDADE      | int   | Idade do paciente                               |
| COD_IDADE  | str   | Unidade de medida da idade (4=Anos)             |
| VAL_TOT    | float | Valor total da AIH (R$)                         |
| CNES       | str   | Código CNES do estabelecimento                  |

---

## Campos derivados (gerados pelo pipeline)

| Campo        | Tipo     | Origem          | Descrição                                  |
| ------------ | -------- | --------------- | ------------------------------------------ |
| is_covid     | bool     | DIAG_PRINC      | True se DIAG_PRINC == 'B342'               |
| ano          | int      | DT_INTER        | Ano de internação                          |
| mes          | int      | DT_INTER        | Mês de internação (1-12)                   |
| ano_mes      | date     | DT_INTER        | Primeiro dia do mês (para série temporal)  |
| faixa_etaria | category | IDADE/COD_IDADE | 0-4, 5-14, 15-29, 30-44, 45-59, 60-74, 75+ |

---

## Schema completo original (113 campos — referência)

Abaixo o schema completo do SIH/SUS para referência. Os campos utilizados
neste projeto estão marcados com **(uso)**.

### Identificação administrativa

| Campo     | Tipo    | Tam | Descrição                                      |
| --------- | ------- | --- | ---------------------------------------------- |
| UF_ZI     | char    | 6   | Município gestor da AIH                        |
| ANO_CMPT  | char    | 4   | Ano de processamento **(uso)**                 |
| MES_CMPT  | char    | 2   | Mês de processamento **(uso)**                 |
| N_AIH     | char    | 13  | Número da AIH                                  |
| IDENT     | char    | 1   | Tipo de AIH (1=Normal, 5=Longa permanência)    |
| ESPEC     | char    | 2   | Especialidade do leito                         |
| CGC_HOSP  | char    | 14  | CNPJ do hospital                               |
| CNES      | char    | 7   | Código CNES do estabelecimento **(uso)**       |
| CNPJ_MANT | char    | 14  | CNPJ da mantenedora                            |
| NATUREZA  | char    | 2   | Natureza jurídica (sem conteúdo após Mai/2012) |
| NAT_JUR   | char    | 4   | Natureza jurídica conforme CONCLA              |
| GESTAO    | char    | 1   | Tipo de gestão do hospital                     |
| MUNIC_MOV | char    | 6   | Município do estabelecimento **(uso)**         |
| SEQUENCIA | numeric | 9   | Sequência da AIH na remessa                    |
| REMESSA   | char    | 21  | Número da remessa                              |

### Dados do paciente

| Campo      | Tipo    | Tam | Descrição                                     |
| ---------- | ------- | --- | --------------------------------------------- |
| CEP        | char    | 8   | CEP do paciente                               |
| MUNIC_RES  | char    | 6   | Município de residência (cod. IBGE) **(uso)** |
| NASC       | char    | 8   | Data de nascimento (aaaammdd)                 |
| SEXO       | char    | 1   | Sexo (1=Masc, 3=Fem) **(uso)**                |
| COD_IDADE  | char    | 1   | Unidade de medida da idade **(uso)**          |
| IDADE      | numeric | 2   | Idade do paciente **(uso)**                   |
| RACA_COR   | char    | 2   | Raça/cor do paciente                          |
| ETNIA      | char    | 4   | Etnia (se indígena)                           |
| NACIONAL   | char    | 3   | Código de nacionalidade                       |
| INSTRU     | char    | 1   | Grau de instrução                             |
| CBOR       | char    | 6   | Ocupação do paciente (CBO)                    |
| NUM_FILHOS | numeric | 2   | Número de filhos                              |

### Internação

| Campo      | Tipo    | Tam | Descrição                                   |
| ---------- | ------- | --- | ------------------------------------------- |
| DT_INTER   | char    | 8   | Data de internação (aaaammdd) **(uso)**     |
| DT_SAIDA   | char    | 8   | Data de saída (aaaammdd) **(uso)**          |
| DIAS_PERM  | numeric | 5   | Dias de permanência **(uso)**               |
| QT_DIARIAS | numeric | 3   | Quantidade de diárias                       |
| DIAR_ACOM  | numeric | 3   | Diárias de acompanhante                     |
| CAR_INT    | char    | 2   | Caráter da internação **(uso)**             |
| COBRANCA   | char    | 2   | Motivo de saída/permanência                 |
| MORTE      | numeric | 1   | Indicador de óbito (0=Não, 1=Sim) **(uso)** |
| COMPLEX    | char    | 2   | Nível de complexidade **(uso)**             |
| INFEHOSP   | char    | 1   | Infecção hospitalar                         |

### Diagnósticos (CID-10)

| Campo      | Tipo | Tam | Descrição                                    |
| ---------- | ---- | --- | -------------------------------------------- |
| DIAG_PRINC | char | 4   | Diagnóstico principal (CID-10) **(uso)**     |
| DIAG_SECUN | char | 4   | Diagnóstico secundário (zerado desde 201501) |
| CID_NOTIF  | char | 4   | CID de notificação                           |
| CID_ASSO   | char | 4   | CID associada/causa                          |
| CID_MORTE  | char | 4   | CID do óbito                                 |
| DIAGSEC1-9 | char | 4   | Diagnósticos secundários 1 a 9               |
| TPDISEC1-9 | char | 1   | Tipos dos diagnósticos secundários 1 a 9     |

### Procedimentos

| Campo      | Tipo | Tam | Descrição               |
| ---------- | ---- | --- | ----------------------- |
| PROC_SOLIC | char | 10  | Procedimento solicitado |
| PROC_REA   | char | 10  | Procedimento realizado  |

### Valores financeiros (R$)

| Campo      | Tipo    | Tam  | Descrição                                    |
| ---------- | ------- | ---- | -------------------------------------------- |
| VAL_SH     | numeric | 13,2 | Valor dos serviços hospitalares              |
| VAL_SP     | numeric | 13,2 | Valor dos serviços profissionais             |
| VAL_TOT    | numeric | 14,2 | Valor total da AIH **(uso)**                 |
| VAL_UTI    | numeric | 8,2  | Valor de UTI                                 |
| VAL_SH_FED | numeric | 10,2 | Complemento federal — serviços hospitalares  |
| VAL_SP_FED | numeric | 10,2 | Complemento federal — serviços profissionais |
| VAL_SH_GES | numeric | 10,2 | Complemento gestor — serviços hospitalares   |
| VAL_SP_GES | numeric | 10,2 | Complemento gestor — serviços profissionais  |
| VAL_UCI    | numeric | 10,2 | Valor da unidade de cuidados intermediários  |
| FINANC     | char    | 2    | Tipo de financiamento                        |
| FAEC_TP    | char    | 6    | Subtipo de financiamento FAEC                |
| REGCT      | char    | 4    | Regra contratual                             |

### UTI e unidades intermediárias

| Campo      | Tipo    | Tam | Descrição                     |
| ---------- | ------- | --- | ----------------------------- |
| UTI_MES_TO | numeric | 3   | Dias de UTI no mês **(uso)**  |
| UTI_INT_TO | numeric | 3   | Dias de unidade intermediária |
| MARCA_UTI  | char    | 2   | Tipo de UTI utilizada         |
| MARCA_UCI  | char    | 2   | Tipo de UCI utilizada         |

### Campos legados (zerados — não utilizados)

Existem no layout mas não são preenchidos desde 2015:

`UTI_MES_IN`, `UTI_MES_AN`, `UTI_MES_AL`, `UTI_INT_IN`, `UTI_INT_AN`, `UTI_INT_AL`,
`VAL_SADT`, `VAL_RN`, `VAL_ACOMP`, `VAL_ORTP`, `VAL_SANGUE`, `VAL_SADTSR`,
`VAL_TRANSP`, `VAL_OBSANG`, `VAL_PED1AC`, `RUBRICA`, `NUM_PROC`, `TOT_PT_SP`, `CPF_AUT`
