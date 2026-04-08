# Dicionario de Dados -- IBGE

## 1. Populacao residente por municipio

### Visao geral

- **Fonte:** IBGE / DATASUS (Estimativas populacionais)
- **Tipo de arquivo:** `.dbf` (dBASE)
- **Cobertura:** 2020, 2021, 2022, 2023
- **Granularidade:** Municipio
- **Total de municipios:** 5.570 por ano

### Arquivos

| Arquivo | Ano | Registros | Observacao |
|---------|-----|-----------|------------|
| `POPTBR20.dbf` | 2020 | 5.570 | OK |
| `POPTBR21.dbf` | 2021 | 5.570 | OK |
| `POPTBR22.dbf` | 2022 | 11.140 | Registros duplicados -- requer deduplicacao |
| `POPTBR22/*.dbf` | 2022 | Varia | Arquivos por UF, mesmo schema |
| `POPTBR23/*.dbf` | 2023 | Varia | Arquivos por UF, mesmo schema |

### Schema (3 campos)

| Campo | Tipo | Tamanho | Descricao |
|-------|------|---------|-----------|
| MUNIC_RES | char | 7 | Codigo IBGE do municipio (6-7 digitos) |
| ANO | char | 4 | Ano de referencia |
| POPULACAO | numeric | 8 | Populacao residente estimada (referencia: 1o de julho) |

### Como ler

```python
from dbfread import DBF

table = DBF("POPTBR20.dbf", encoding="latin-1")
for record in table:
    print(record)
```

### Observacoes

- A populacao e estimada em 1o de julho do ano de referencia
- O campo `MUNIC_RES` usa o codigo IBGE sem digito verificador (6 digitos), mas em alguns arquivos aparece com 7 digitos (inclui verificador)
- O arquivo de 2022 (`POPTBR22.dbf`) contem registros duplicados (11.140 linhas para 5.570 municipios) -- necessario deduplicar antes de usar
- Os campos de 2022 tem tamanho maior (char 255, numeric 18) comparado a 2020/2021 -- nao afeta o conteudo
- Estes arquivos sao agregados: apenas populacao total por municipio, sem desagregacao por sexo, faixa etaria ou situacao domiciliar

---

## 2. PIB dos Municipios

### Visao geral

- **Fonte:** IBGE -- Produto Interno Bruto dos Municipios
- **Tipo de arquivo:** `.xlsx`
- **Arquivo:** `PIB dos Municipios - base de dados 2010-2023.xlsx`
- **Cobertura:** 2010 a 2023
- **Granularidade:** Municipio x ano
- **Total de registros:** 77.965 (5.570 municipios x 14 anos)
- **Planilhas:** "PIB dos Municipios" (dados), "Notas" (metodologia)

### Schema (43 campos)

#### Campos geograficos e administrativos (32 campos)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| Ano | int | Ano de referencia |
| Codigo da Grande Regiao | int | Codigo da grande regiao (1-5) |
| Nome da Grande Regiao | str | Norte, Nordeste, Sudeste, Sul, Centro-Oeste |
| Codigo da Unidade da Federacao | int | Codigo IBGE da UF |
| Sigla da Unidade da Federacao | str | Sigla da UF (SP, RJ, etc.) |
| Nome da Unidade da Federacao | str | Nome completo da UF |
| Codigo do Municipio | int | Codigo IBGE do municipio (7 digitos) |
| Nome do Municipio | str | Nome do municipio |
| Regiao Metropolitana | str | Regiao metropolitana (quando aplicavel) |
| Codigo da Mesorregiao | int | Codigo da mesorregiao |
| Nome da Mesorregiao | str | Nome da mesorregiao |
| Codigo da Microrregiao | int | Codigo da microrregiao |
| Nome da Microrregiao | str | Nome da microrregiao |
| Codigo da Regiao Geografica Imediata | int | Codigo da regiao geografica imediata |
| Nome da Regiao Geografica Imediata | str | Nome da regiao geografica imediata |
| Municipio da Regiao Geografica Imediata | str | Papel na regiao imediata (Polo/Entorno) |
| Codigo da Regiao Geografica Intermediaria | int | Codigo da regiao geografica intermediaria |
| Nome da Regiao Geografica Intermediaria | str | Nome da regiao geografica intermediaria |
| Municipio da Regiao Geografica Intermediaria | str | Papel na regiao intermediaria |
| Codigo Concentracao Urbana | float | Codigo de concentracao urbana |
| Nome Concentracao Urbana | str | Nome da concentracao urbana |
| Tipo Concentracao Urbana | str | Tipo da concentracao urbana |
| Codigo Arranjo Populacional | float | Codigo do arranjo populacional |
| Nome Arranjo Populacional | str | Nome do arranjo populacional |
| Hierarquia Urbana | str | Hierarquia urbana (detalhada) |
| Hierarquia Urbana (principais categorias) | str | Hierarquia urbana (categorias principais) |
| Codigo da Regiao Rural | int | Codigo da regiao rural |
| Nome da Regiao Rural | str | Nome da regiao rural |
| Regiao rural (segundo classificacao do nucleo) | str | Classificacao da regiao rural |
| Amazonia Legal | str | Pertence a Amazonia Legal? (Sim/Nao) |
| Semiarido | str | Pertence ao Semiarido? (Sim/Nao) |
| Cidade-Regiao de Sao Paulo | str | Pertence a Cidade-Regiao de SP? (Sim/Nao) |

#### Campos economicos (11 campos)

| Campo | Tipo | Unidade | Descricao |
|-------|------|---------|-----------|
| VAB Agropecuaria | float | R$ 1.000 | Valor adicionado bruto -- Agropecuaria |
| VAB Industria | float | R$ 1.000 | Valor adicionado bruto -- Industria |
| VAB Servicos (excl. adm. publica) | float | R$ 1.000 | Valor adicionado bruto -- Servicos |
| VAB Administracao publica | float | R$ 1.000 | Valor adicionado bruto -- Adm. publica, defesa, educacao, saude |
| VAB Total | float | R$ 1.000 | Valor adicionado bruto total |
| Impostos liquidos de subsidios | float | R$ 1.000 | Impostos liquidos sobre produtos |
| PIB (R$ 1.000) | float | R$ 1.000 | Produto Interno Bruto a precos correntes |
| PIB per capita (R$ 1,00) | float | R$ 1,00 | PIB per capita a precos correntes |
| Atividade com maior VAB | str | -- | Atividade economica predominante |
| Atividade com 2o maior VAB | str | -- | Segunda atividade economica |
| Atividade com 3o maior VAB | str | -- | Terceira atividade economica |

### Observacoes

- Os campos VAB (desagregacao setorial) estao disponveis de 2010 a 2021; para 2022-2023 so ha PIB agregado e PIB per capita
- Valores monetarios estao a precos correntes (nominais), sem correcao inflacionaria
- O campo `Codigo do Municipio` usa 7 digitos (com verificador), diferente dos 6 digitos do DATASUS
- A planilha "Notas" informa que dados de 2022-2023 sao preliminares

---

## Estrategia de join entre as bases

### Chave de ligacao: codigo do municipio

| Base | Campo | Digitos | Exemplo |
|------|-------|---------|---------|
| SIH/SUS | MUNIC_RES | 6 | 355030 |
| Populacao | MUNIC_RES | 6-7 | 355030 ou 3550308 |
| PIB Municipal | Codigo do Municipio | 7 | 3550308 |

Para unificar: truncar o codigo de 7 digitos removendo o ultimo (digito verificador), resultando em 6 digitos compativel com o DATASUS.

```python
pib["cod_municipio_6d"] = pib["Codigo do Municipio"] // 10
```

### Periodo de sobreposicao

| Base | Periodo disponivel |
|------|--------------------|
| SIH/SUS | 2020-2023 |
| Populacao | 2020-2023 |
| PIB Municipal | 2010-2023 |
| **Intersecao completa** | **2020-2023** |
