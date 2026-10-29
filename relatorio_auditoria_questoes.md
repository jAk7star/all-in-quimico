# Relatório de Auditoria Técnica e Mapeamento Pedagógico do Banco de Questões
## Reestruturação e Arquitetura Multi-Deck de Slides — All-In Químico

**Projeto:** All-In Químico: O Jogo da Termodinâmica Humana  
**Versão do Documento:** 2.0.0 (Definitivo / Autorizativo)  
**Data:** 29 de Outubro de 2026  
**Auditor Responsável:** Equipe de Engenharia e Governança Didática (`worker_m1_gen2`)  
**Repositório Alvo:** `c:\Users\Vaio\Documents\Jaques\Leilão-Química-v1.00\`  
**Especificações de Referência:** `SPEC-01-questoes`, `SPEC-02-regras-do-jogo`, `SPEC-03-gerador`, `PROJECT.md`  
**Status da Auditoria:** Concluída com Sucesso — Pré-requisito Mandatório para M2 / M3  

---

## 1. Sumário Executivo & Metodologia de Auditoria

### 1.1 Contexto e Justificativa
O jogo pedagógico **All-In Químico** utiliza a dinâmica de leilão, apostas em cotas e eliminação súbita (inspirada na mecânica do *Texas Hold'em*) para ensinar Química Geral, Soluções, Estequiometria e Química Ambiental para estudantes do Ensino Médio e Pré-Vestibular. A versão legada do gerador de slides (`specs/SPEC-03-gerador/gerar_slides_perguntas_respostas.py`) operava de forma estritamente monolítica, compilando uma única apresentação massiva de 41 slides contendo 20 questões de Níveis 1 e 2 em sequência ininterrupta, e excluindo categoricamente as questões de Nível 3 (Morte Súbita).

Para operacionalizar as partidas em sala de aula com tempo pedagógico controlado, flexibilidade de rodadas e garantia de zero vazamento prévio de questões decisivas, a diretoria de produto estabeleceu a divisão das questões em apresentações independentes e especializadas:
1. **Apresentação de Teste Exclusiva (R2):** exatamente 3 questões de Nível 1 reservadas para calibração e treino sem risco financeiro.
2. **Apresentações Individuais de Desafio (R3):** 5 arquivos dedicados de 1 questão de Nível 3 cada, com foco visual extremo na mecânica de Morte Súbita.
3. **Apresentações Regulares de 5 Questões (R4):** 3 apresentações fechadas de exatamente 5 pares Q&A (11 slides cada), além de um deck complementar de desempate técnico (2 questões).

Conforme estipulado no requisito **R1**, nenhuma linha de código de geração de slides ou execução de mutações na Google Slides API pode ser realizada antes de uma auditoria minuciosa, programática e exaustiva de todo o banco de questões (`specs/SPEC-01-questoes/questions/`). Este relatório formaliza os achados dessa auditoria, documenta as inconsistências tipográficas encontradas, estabelece as equações de auto-scaling anti-overflow e fixa o plano de partição disjunto do banco.

---

### 1.2 Metodologia da Auditoria
A auditoria foi executada com metodologia híbrida, combinando análise estática da Abstract Syntax Tree (AST) dos arquivos YAML com modelagem geométrica de caixas de texto no Google Slides API:

1. **Varredura e Extração de Métricas Estruturais:** Leitura recursiva dos três arquivos canônicos de questões (`questoes_nivel_1.yaml`, `questoes_nivel_2.yaml`, `questoes_nivel_3.yaml`). Extração de contagem exata de caracteres brutos (com tags HTML), caracteres limpos (após normalização Unicode), palavras, fórmulas químicas e metadados cognitivos.
2. **Auditoria Tipográfica e Notacional:** Varredura por expressões regulares para catalogação de tags `<sub>` e `<sup>`, símbolos de multiplicação (`×`, `·`, `*`, `•`), conectores de reação (`→`, `⇄`, `->`, `<->`), subscritos de massa molar em caracteres maiúsculos e discrepâncias de pontuação final nas opções [A] e [B].
3. **Modelagem Espacial e Ergonômica dos Cards:** Cálculo da densidade textual versus área útil das caixas de texto no Design System *Fintech Clean* (canvas 720 × 405 pt widescreen, margens simétricas de 32 pt, grid modular de 8px). Identificação de riscos de truncamento e colisão em resoluções padrão de projetores.
4. **Modelagem de Partição por Teoria dos Conjuntos:** Verificação formal de completude, cardinalidade e disjunção mútua (Zero-Reuse) de todas as 25 questões entre os decks de produção.

---

### 1.3 Visão Geral Estatística do Banco de Questões

O banco oficial homologado é composto por **exatamente 25 questões binárias** (alternativas [A] e [B]), distribuídas equilibradamente por dificuldade, domínio e taxonomia de Bloom:

```
+---------------------------------------------------------------------------------------+
| DISTRIBUIÇÃO CONSOLIDADA DO BANCO DE QUESTÕES (25 ITENS)                              |
+-------------------+---------+---------+---------+-------+-----------------------------+
| DOMÍNIO QUÍMICO   | NÍVEL 1 | NÍVEL 2 | NÍVEL 3 | TOTAL | HABILIDADES PREDOMINANTES   |
+-------------------+---------+---------+---------+-------+-----------------------------+
| CHEM-ATO          |    2    |    0    |    0    |   2   | Tabela Periódica, Z, Grupos |
| CHEM-ENV          |    4    |    1    |    1    |   6   | Chuva Ácida, Estufa, Al, Ca |
| CHEM-SOL          |    2    |    4    |    3    |   9   | C, c, Diluição, Misturas    |
| CHEM-STO          |    5    |    2    |    1    |   8   | Mol, Massa Molar, Limitante |
+-------------------+---------+---------+---------+-------+-----------------------------+
| TOTAL GERAL       |   13    |    7    |    5    |  25   | 100% Binárias [A] vs [B]    |
+-------------------+---------+---------+---------+-------+-----------------------------+
```

```
+---------------------------------------------------------------------------------------+
| DISTRIBUIÇÃO POR NÍVEL COGNITIVO (TAXONOMIA DE BLOOM REVISADA)                        |
+------------------+----------+------------+--------------------------------------------+
| NÍVEL COGNITIVO  | QUESTÕES | PERCENTUAL | CARACTERÍSTICA PEDAGÓGICA NO JOGO          |
+------------------+----------+------------+--------------------------------------------+
| recognition      |    2     |    8,0%    | Resposta rápida (<30s), leitura direta     |
| understanding    |    6     |   24,0%    | Distinção de grandezas, pegadinhas teóricas|
| application      |   13     |   52,0%    | Cálculos de 1 a 2 etapas com dados no card |
| analysis         |    4     |   16,0%    | Resoluções multietapa, rendimento, limitante|
+------------------+----------+------------+--------------------------------------------+
| TOTAL            |   25     |  100,0%    | Equilíbrio ideal para dinâmica de apostas  |
+------------------+----------+------------+--------------------------------------------+
```

---

## 2. Inventário Exaustivo de Todas as 25 Questões do Banco

A tabela a seguir apresenta todas as métricas extraídas diretamente dos arquivos-fonte YAML em `specs/SPEC-01-questoes/questions/`.

*Legenda das Colunas:*
- **Enunciado (c_raw / c_cln / w):** caracteres com tags HTML / caracteres Unicode limpos / quantidade de palavras.
- **Opção A / Opção B (c_raw / c_cln):** caracteres com tags / caracteres Unicode limpos.
- **Gab.:** Gabarito oficial ([A] ou [B]).
- **Resolução (c):** extensão em caracteres da resolução passo a passo (`worked_solution`).
- **Justificativa (c):** extensão da justificativa científica (`scientific_justification`).
- **Distrator (c):** extensão da explicação do erro da alternativa incorreta (`rationale`).
- **Notações / Tags:** marcações HTML presentes (`<sub>`, `<sup>`), caracteres especiais e subscritos maiúsculos.

### Tabela 2.1 — Mapeamento Completo dos 25 Itens do Banco

| ID | Nível | Domínio | Cognitivo | Enunciado (raw/cln/w) | Opção A (raw/cln) | Opção B (raw/cln) | Gab. | Resolução | Justif. | Distrator | Tags / Fórmulas Químicas / Notação |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| `Q-SOL-001` | N1 | `CHEM-SOL` | application | 128c / 128c / 23w | 7c / 7c | 8c / 8c | **A** | 31c | 76c | 71c | `×`; sem tags; sem ponto final nas opções |
| `Q-SOL-006` | N1 | `CHEM-SOL` | understanding | 76c / 76c / 13w | 32c / 32c | 26c / 26c | **B** | 79c | 58c | 41c | Texto puro conceitual; opções com ponto final |
| `Q-STO-001` | N1 | `CHEM-STO` | application | 133c / 133c / 27w | 8c / 8c | 7c / 7c | **B** | 41c | 32c | 78c | `NaCl`; sem tags; sem ponto final nas opções |
| `Q-STO-002` | N1 | `CHEM-STO` | application | 103c / 103c / 21w | 8c / 8c | 8c / 8c | **A** | 34c | 62c | 59c | `Na`; sem tags; sem ponto final nas opções |
| `Q-STO-003` | N1 | `CHEM-STO` | understanding | 146c / 113c / 22w | 55c / 55c | 48c / 48c | **A** | 150c | 39c | 100c | `<sub>`; `2 H<sub>2</sub> + O<sub>2</sub> → 2 H<sub>2</sub>O`; opções com ponto final |
| `Q-ATO-001` | N1 | `CHEM-ATO` | recognition | 71c / 71c / 10w | 36c / 36c | 41c / 41c | **B** | 79c | 32c | 63c | Texto puro Tabela Periódica; opções com ponto final |
| `Q-ATO-002` | N1 | `CHEM-ATO` | recognition | 60c / 60c / 9w | 51c / 51c | 57c / 57c | **B** | 56c | 81c | 68c | Texto puro Períodos e Grupos; opções com ponto final |
| `Q-STO-004` | N1 | `CHEM-STO` | application | 119c / 86c / 18w | 10c / 10c | 10c / 10c | **A** | 48c | 55c | 79c | `<sub>`; `H<sub>2</sub>O`, `M<sub>H</sub>`, `M<sub>O</sub>` ⚠️; sem ponto final |
| `Q-STO-005` | N1 | `CHEM-STO` | application | 121c / 99c / 19w | 5c / 5c | 6c / 6c | **B** | 42c | 43c | 64c | `<sub>`; `H<sub>2</sub>O`, `M<sub>H₂O</sub>` ⚠️; sem ponto final |
| `Q-ENV-001` | N1 | `CHEM-ENV` | understanding | 191c / 180c / 36w | 89c / 78c | 118c / 85c | **B** | 194c | 104c | 118c | `<sub>`; `CO<sub>2</sub>`, `H<sub>2</sub>CO<sub>3</sub>`, `SO<sub>2</sub>`, `H<sub>2</sub>SO<sub>4</sub>`, `SO<sub>3</sub>`; opções com ponto |
| `Q-ENV-002` | N1 | `CHEM-ENV` | understanding | 150c / 150c / 24w | 99c / 99c | 144c / 122c | **B** | 157c | 87c | 121c | `<sub>` (na Opção B); `CO<sub>2</sub>`, `CH<sub>4</sub>`, `O<sub>3</sub>`; opções com ponto |
| `Q-ENV-003` | N1 | `CHEM-ENV` | understanding | 190c / 168c / 30w | 127c / 127c | 117c / 95c | **A** | 145c | 71c | 128c | `<sub>`; `O<sub>2</sub>`, `CO<sub>2</sub>`; opções com ponto final |
| `Q-ENV-004` | N1 | `CHEM-ENV` | understanding | 211c / 189c / 30w | 159c / 137c | 113c / 113c | **A** | 139c | 79c | 148c | `<sub>`, `<sup>`; `Al<sub>2</sub>O<sub>3</sub>`, `Al<sup>3+</sup>`, `Al<sup>0</sup>`; opções com ponto |
| `Q-SOL-002` | N2 | `CHEM-SOL` | application | 222c / 222c / 48w | 72c / 72c | 76c / 76c | **B** | 131c | 83c | 85c | Conversão de mL para L; opções com ponto final |
| `Q-SOL-003` | N2 | `CHEM-SOL` | application | 219c / 219c / 41w | 112c / 112c | 91c / 91c | **A** | 120c | 115c | 108c | Propriedade intensiva molar; opções com ponto final |
| `Q-SOL-004` | N2 | `CHEM-SOL` | application | 171c / 171c / 31w | 60c / 60c | 59c / 59c | **A** | 100c | 82c | 90c | Diluição com solvente puro; opções com ponto final |
| `Q-SOL-009` | N2 | `CHEM-SOL` | application | 151c / 151c / 30w | 73c / 73c | 77c / 77c | **B** | 123c | 122c | 114c | Mistura com solutos iguais (`NaCl`); opções com ponto |
| `Q-STO-006` | N2 | `CHEM-STO` | application | 215c / 138c / 28w | 110c / 88c | 115c / 93c | **B** | 215c | 106c | 133c | `<sub>`; `H<sub>2</sub>SO<sub>4</sub>`, `NaOH`, `Na<sub>2</sub>SO<sub>4</sub>`, `H<sub>2</sub>O`; opções com ponto |
| `Q-ENV-005` | N2 | `CHEM-ENV` | application | 226c / 204c / 35w | 134c / 123c | 119c / 119c | **A** | 163c | 109c | 114c | `<sub>`; `CO`, `CO<sub>2</sub>`, `O<sub>2</sub>`, catálise; opções com ponto |
| `Q-STO-007` | N2 | `CHEM-STO` | application | 264c / 264c / 43w | 98c / 98c | 117c / 117c | **B** | 126c | 77c | 108c | Rendimento industrial 80%; opções com ponto final |
| `Q-SOL-005` | N3 | `CHEM-SOL` | application | 240c / 229c / 42w | 76c / 76c | 76c / 76c | **A** | 111c | 86c | 88c | `🔥 [DILUIÇÃO]`; `<sub>`; `V<sub>2</sub>` vs `V2` ⚠️; opções com ponto |
| `Q-SOL-007` | N3 | `CHEM-SOL` | analysis | 279c / 257c / 50w | 80c / 80c | 84c / 84c | **A** | 94c | 89c | 94c | `🔥 [MOLARIDADE]`; `<sub>`; `M<sub>Na</sub>`, `M<sub>Cl</sub>` ⚠️; `•`; com ponto |
| `Q-SOL-008` | N3 | `CHEM-SOL` | analysis | 297c / 264c / 53w | 77c / 77c | 80c / 80c | **B** | 93c | 111c | 87c | `🔥 [SODA CÁUSTICA]`; `<sub>`; `M<sub>Na</sub>`, `M<sub>O</sub>`, `M<sub>H</sub>` ⚠️; `•`; com ponto |
| `Q-STO-008` | N3 | `CHEM-STO` | analysis | 307c / 241c / 54w | 98c / 87c | 121c / 99c | **B** | 183c | 132c | 130c | `🔥 [LIMITANTE + RENDIMENTO]`; `<sub>`; `H2` vs `H<sub>2</sub>` ⚠️; com ponto |
| `Q-ENV-006` | N3 | `CHEM-ENV` | analysis | 210c / 210c / 35w | 116c / 105c | 139c / 117c | **B** | 183c | 117c | 116c | `🔥 [GEOQUÍMICA CHUVA ÁCIDA]`; `<sub>`, `<sup>`; `Al<sup>3+</sup>`, `CaCO<sub>3</sub>`; com ponto |

---

## 3. Análise Detalhada de Inconsistências Visuais e Tipográficas

Durante a inspeção minuciosa dos textos e expressões químicas, foram diagnosticadas quatro categorias de inconsistências tipográficas que impactam diretamente a apresentação visual em projetores de sala de aula.

---

### 3.1 Defeito Crítico de Conversão de Subscritos Maiúsculos em Massa Molar

#### A. Diagnóstico da Causa Raiz
No arquivo `questoes_nivel_1.yaml` (`Q-STO-004`, `Q-STO-005`) e `questoes_nivel_3.yaml` (`Q-SOL-007`, `Q-SOL-008`), o autor utilizou tags HTML para especificar as massas molares dos elementos químicos nos enunciados:
- Em `Q-STO-004`: `M<sub>H</sub> = 1,0 g/mol e M<sub>O</sub> = 16,0 g/mol`
- Em `Q-STO-005`: `(dados: H = 1,0; O = 16,0 g/mol; M<sub>H₂O</sub> = 18,0 g/mol)`
- Em `Q-SOL-007`: `M<sub>Na</sub> = 23,0 g/mol e M<sub>Cl</sub> = 35,5 g/mol`
- Em `Q-SOL-008`: `M<sub>Na</sub> = 23,0 g/mol, M<sub>O</sub> = 16,0 g/mol, M<sub>H</sub> = 1,0 g/mol`

A função utilitária `clean_chemical_typography` implementada em `gerar_slides_perguntas_respostas.py` utiliza o dicionário de conversão Unicode para substituir o conteúdo capturado entre `<sub>...</sub>`:
```python
SUBSCRIPT_MAP = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋",
}
```
Como o padrão Unicode **não possui caracteres latinos maiúsculos na faixa de subscritos** (o bloco U+2080 a U+208E só disponibiliza dígitos e sinais, e caracteres latinos subscritos em Unicode restringem-se a algumas letras minúsculas fonéticas), a função executa `SUBSCRIPT_MAP.get(char, char)`.
Dessa forma, os caracteres maiúsculos são devolvidos inalterados, e o fechamento da tag é descartado!

#### B. Efeito Visual Indesejado
O texto resultante no slide renderizado torna-se:
- `MNa = 23,0 g/mol` (em vez de $M_{\text{Na}}$)
- `MCl = 35,5 g/mol` (em vez de $M_{\text{Cl}}$)
- `MH = 1,0 g/mol` (em vez de $M_{\text{H}}$)
- `MO = 16,0 g/mol` (em vez de $M_{\text{O}}$)
- `MH₂O = 18,0 g/mol` (em vez de $M_{\text{H}_2\text{O}}$)

#### C. Impacto Pedagógico Severo
Para um estudante de Ensino Médio ou vestibulando, `MNa` parece a fórmula de um composto químico organometálico hipotético (como "metil-sódio") ou uma fusão espúria de símbolos atômicos. O mesmo ocorre com `MCl`, facilmente confundido com um cloreto metálico genérico $M\text{Cl}$. Essa anomalia fere a norma culta da comunicação científica.

#### D. Resolução Oficial IUPAC
A IUPAC (*International Union of Pure and Applied Chemistry*), através do *Compendium of Chemical Terminology* (Gold Book) e das diretrizes do *Green Book* (Seção 2.10 — Físico-Química), estabelece que a massa molar de uma entidade fundamental $X$ deve ser representada simbolicamente por:
$$M(X) \quad \text{ou} \quad M_X$$
Quando o suporte a subscritos tipográficos é limitado (como em saídas puramente textuais, telas de terminal ou blocos Unicode sem fontes proprietárias), a notação parentética funcional $M(X)$ é a **recomendação oficial e universal**:
- $M(\text{Na}) = 23{,}0 \text{ g/mol}$
- $M(\text{Cl}) = 35{,}5 \text{ g/mol}$
- $M(\text{H}) = 1{,}0 \text{ g/mol}$
- $M(\text{O}) = 16{,}0 \text{ g/mol}$
- $M(\text{H}_2\text{O}) = 18{,}0 \text{ g/mol}$

**Regra de Normalização para o Gerador de Slides:**
Antes de qualquer conversão de subscritos numéricos, o gerador deve aplicar a seguinte substituição via regex:
```python
text = re.sub(r"M<sub>([A-Za-z0-9\u2080-\u2089]+)</sub>", r"M(\1)", text)
```
Em seguida, converte eventuais dígitos dentro dos parênteses para subscrito padrão (ex.: `M(H2O)` $\to$ `M(H₂O)`). Essa solução é 100% à prova de falhas em qualquer dispositivo, preserva o rigor formal da IUPAC e elimina qualquer deformidade estética nos cards.

---

### 3.2 Inconsistência na Pontuação Final das Alternativas [A] e [B]

#### A. Diagnóstico do Levantamento
A auditoria identificou três padrões concorrentes de pontuação nas alternativas:
1. **Padrão Sem Ponto Final (Numérico Puro — Nível 1):** Presente em `Q-SOL-001`, `Q-STO-001`, `Q-STO-002`, `Q-STO-004` e `Q-STO-005`.
   - Exemplos: `5,0 g/L`, `0,50 mol`, `9,2 g`, `18,0 g/mol`, `54 g`.
2. **Padrão Com Ponto Final (Conceitual / Frasal — Nível 1):** Presente em `Q-SOL-006`, `Q-STO-003`, `Q-ATO-001`, `Q-ATO-002`, `Q-ENV-001`, `Q-ENV-002`, `Q-ENV-003`, `Q-ENV-004`.
   - Exemplos: `O volume final da solução.`, `A ordem crescente de número atômico (Z).`
3. **Padrão Universal Com Ponto Final (Nível 2 e Nível 3):** Em 100% das 12 questões de Nível 2 e Nível 3, todas as alternativas terminam com ponto final, mesmo quando são expressões numéricas acompanhadas de parênteses explicativos ou conectores em bala (`•`):
   - Exemplo (`Q-SOL-002`): `Frasco I: 10,0 g/L; Frasco II: 5,0 g/L.`
   - Exemplo (`Q-SOL-007`): `M = 58,5 g/mol • n = 0,20 mol • c = 0,40 mol/L.`
   - Exemplo (`Q-SOL-008`): `C = 40,0 g/L • c = 1,00 mol/L.`

#### B. Diretriz de Harmonização Visual (Design System)
Para preservar a clareza e evitar inconsistências visuais perceptíveis entre decks:
- Alternativas que constituem orações completas, frases explicativas ou expressões compostas por tópicos com `•` **mantêm o ponto final**.
- Alternativas numéricas atômicas simples de Nível 1 (ex.: `5,0 g/L` ou `2,0 mol`) mantêm-se sem ponto final, pois o ponto final colado em unidades de medida pode ser erroneamente interpretado pelos alunos como sinal de multiplicação escalar (ex.: `mol.` confundido com produto de grandezas).

---

### 3.3 Formatação Inconsistente de Fórmulas entre Enunciados e Resoluções

#### A. Discrepâncias Diagnosticadas
- **Em `Q-STO-008`:** O enunciado utiliza tags estritas de equação química: `2 H<sub>2</sub> + O<sub>2</sub> → 2 H<sub>2</sub>O`. Porém, no campo `worked_solution`, o autor redigiu em texto bruto: `1) Proporção 2 H2 : 1 O2. Os 4,0 mol de H2 precisam de apenas 2,0 mol de O2... 2) Teórico: 4,0 mol de H2O.`
- **Em `Q-SOL-005`:** O enunciado referencia `(V<sub>2</sub>)`, mas as opções A e B utilizam `Volume final V2 = 200 mL`, e a resolução utiliza `c1·V1 = c2·V2`.
- **Em `Q-SOL-004` e `Q-SOL-005`:** As resoluções utilizam ponto médio `·` para multiplicação de variáveis (`c1·V1 = c2·V2`), enquanto em `Q-SOL-001` e `Q-STO-004` utiliza-se o sinal `×` (`10 × 2`, `2 × 1,0 + 16,0`).

#### B. Solução no Pipeline de Geração
O gerador deve conter um módulo de pós-processamento de fórmulas químicas na resolução (`worked_solution`) e nas justificativas, convertendo automaticamente sequências comuns de substâncias não marcadas:
- `H2O` $\to$ `H₂O`
- `H2` $\to$ `H₂`
- `O2` $\to$ `O₂`
- `CO2` $\to$ `CO₂`
- `SO2` $\to$ `SO₂`
- `SO3` $\to$ `SO₃`
- `V2` $\to$ `V₂`
- `V1` $\to$ `V₁`
- `c1` $\to$ `c₁`
- `c2` $\to$ `c₂`

---

### 3.4 Prefixo de Fogo e Mecânica de Aposta no Tema em Nível 3

#### A. Diagnóstico Estrutural
Todas as 5 questões de Nível 3 (`Q-SOL-005`, `Q-SOL-007`, `Q-SOL-008`, `Q-STO-008`, `Q-ENV-006`) possuem no início do campo `statement` a marcação explícita:
`🔥 [APOSTA NO TEMA: <NOME DO TEMA EM CAIXA ALTA>]`

Lista dos 5 temas catalogados:
1. `Q-SOL-005`: `DILUIÇÃO`
2. `Q-SOL-007`: `MOLARIDADE A PARTIR DA MASSA`
3. `Q-SOL-008`: `SODA CÁUSTICA EM SOLUÇÃO`
4. `Q-STO-008`: `LIMITANTE + RENDIMENTO`
5. `Q-ENV-006`: `GEOQUÍMICA DA CHUVA ÁCIDA`

#### B. Defeito no Gerador Monolítico Legado
Se o gerador renderizar a string bruta diretamente no textbox do enunciado, o estudante verá `🔥 [APOSTA NO TEMA: DILUIÇÃO] Você dispõe de 50 mL...` no corpo do parágrafo. Isso polui visualmente o card e quebra a hierarquia tipográfica do Design System.

#### C. Solução de Arquitetura Multi-Deck para Apresentações de Desafio
Nas novas Apresentações Individuais de Desafio (R3), cada arquivo possui **3 slides**:
1. **Slide 1 (Capa / Fase 1 — Aposta no Escuro):** O gerador extrai `<NOME DO TEMA>` e gera um card central proeminente de 28 pt bold informando o tema da rodada e as regras de entrada (aposta mínima de 100 T$). O enunciado da pergunta permanece oculto.
2. **Slide 2 (Pergunta / Fase 2 — Leitura e All-In):** O prefixo `🔥 [APOSTA NO TEMA: ...]` é **removido** do enunciado da questão. No lugar dele, um badge estilizado no topo do slide exibe: `DESAFIO FINAL • MORTE SÚBITA • TEMA: <NOME DO TEMA>` com fundo roxo ametista suave (`#F3E8FF`) e texto roxo escuro (`#581C87`). O enunciado limpo é renderizado com legibilidade impecável no card principal.
3. **Slide 3 (Gabarito Oficial & Liquidação WTA):** Exibe a resolução técnica completa, a justificativa e as regras de liquidação *Winner Takes All* (o grupo com maior aposta que acertar recolhe todo o pote).

---

## 4. Dimensões dos Cards, Tipografia e Análise de Risco de Overflow

A identidade visual do projeto All-In Químico é regida pelo padrão **Fintech Clean** (inspirado em interfaces financeiras de alta sofisticação, legibilidade e baixa carga cognitiva). A seguir detalham-se as dimensões físicas exatas e o cálculo de capacidade de cada componente.

---

### 4.1 Especificação Geométrica dos Componentes (Slide 720 × 405 pt)

```
+---------------------------------------------------------------------------------------------------+
| SLIDE 16:9 WIDESCREEN (720 x 405 pt)                                                               |
| Top Accent Bar: x=0, y=0, w=720, h=6 pt                                                           |
| Header Badges: y=16 pt, h=28 pt (Badge 1: w=240 | Badge 2: w=280 | Badge 3: w=120 pt)            |
+---------------------------------------------------------------------------------------------------+
| COLUNA ESQUERDA (x=32 pt)                     | COLUNA DIREITA (x=368 pt)                         |
|                                               |                                                   |
| CARD DO ENUNCIADO (Slide 2i):                 | CARD DA ALTERNATIVA [A] (Slide 2i):               |
| Container: x=32, y=56, w=328, h=248 pt        | Container: x=368, y=56, w=320, h=118 pt           |
| Textbox:   x=48, y=92, w=296, h=196 pt        | Textbox:   x=384, y=94, w=288, h=68 pt            |
| Fonte Padrão: Open Sans 12pt (entrelinha 135%)| Fonte Padrão: Open Sans 11.5pt Bold (entrel. 130%)|
|                                               +---------------------------------------------------+
| CARD DA RESOLUÇÃO (Slide 2i+1):               | CARD DA ALTERNATIVA [B] (Slide 2i):               |
| Container: x=32, y=56, w=328, h=248 pt        | Container: x=368, y=186, w=320, h=118 pt          |
| Textbox:   x=48, y=92, w=296, h=196 pt        | Textbox:   x=384, y=224, w=288, h=68 pt           |
| Fonte Padrão: Open Sans 11pt (entrelinha 130%)| Fonte Padrão: Open Sans 11.5pt Bold (entrel. 130%)|
|                                               +---------------------------------------------------+
|                                               | CARD JUSTIFICATIVA + DISTRATOR (Slide 2i+1):       |
|                                               | Container: x=368, y=56, w=320, h=248 pt           |
|                                               | Textbox:   x=384, y=92, w=288, h=196 pt           |
|                                               | Fonte Padrão: Open Sans 10.5pt (entrelinha 130%)  |
+---------------------------------------------------------------------------------------------------+
| RODAPÉ DE GOVERNANÇA / LIQUIDAÇÃO: x=32, y=318, w=656, h=68 pt                                    |
+---------------------------------------------------------------------------------------------------+
```

---

### 4.2 Análise Matemática de Capacidade e Risco de Overflow

#### A. Card das Alternativas [A] e [B] (Caixa: largura = 288 pt, altura útil = 68 pt)
- **Fonte Nominal:** `Open Sans` 11.5 pt Negrito (`weight: 700`).
- **Largura Média do Caractere:** Em 11.5 pt negrito, a largura média de glifo (incluindo espaços) é de approximately $7{,}2\text{ pt}$.
- **Caracteres por Linha:** $\frac{288\text{ pt}}{7{,}2\text{ pt/char}} \approx 40\text{ caracteres por linha}$.
- **Altura da Linha com Espaçamento:** $11{,}5\text{ pt} \times 1{,}30 = 14{,}95\text{ pt}$.
- **Número Máximo de Linhas sem Truncamento:** $\lfloor \frac{68\text{ pt}}{14{,}95\text{ pt}} \rfloor = 4\text{ linhas}$.
- **Capacidade Teórica Máxima:** $4 \times 40 = 160\text{ caracteres}$.
- **Capacidade Segura Real (Considerando Quebra de Palavras):** Em virtude do *word-wrapping* (as palavras não quebram ao meio), alternativas com mais de **110 caracteres** atingem invariavelmente a 4ª linha. Textos acima de **125 caracteres** correm risco severo de cortar a base da última linha (*descenders* de letras como 'p', 'q', 'g', 'y') ou disparar compressão automática indesejada (`fontScale < 0.90`).

#### Itens Críticos de Alto Risco de Overflow nas Alternativas:
1. `Q-ENV-004` (Opção A): **159c brutos / 137c limpos** (30 palavras) $\implies$ **RISCO EXTREMO DE OVERFLOW**
2. `Q-ENV-002` (Opção B): **144c brutos / 122c limpos** (21 palavras) $\implies$ **ALTO RISCO**
3. `Q-ENV-005` (Opção A): **134c brutos / 123c limpos** (21 palavras) $\implies$ **ALTO RISCO**
4. `Q-ENV-006` (Opção B): **139c brutos / 117c limpos** (19 palavras) $\implies$ **ALTO RISCO**
5. `Q-ENV-003` (Opção A): **127c limpos** (20 palavras) $\implies$ **MÉDIO/ALTO RISCO**
6. `Q-STO-008` (Opção B): **121c brutos / 99c limpos** (18 palavras) $\implies$ **MÉDIO RISCO**
7. `Q-STO-007` (Opção B): **117c limpos** (19 palavras) $\implies$ **MÉDIO RISCO**
8. `Q-ENV-001` (Opção B): **118c brutos / 85c limpos** (14 palavras) $\implies$ **MÉDIO RISCO (BRUTO)**
9. `Q-STO-006` (Opção B): **115c brutos / 93c limpos** (16 palavras) $\implies$ **MÉDIO RISCO (BRUTO)**
10. `Q-SOL-003` (Opção A): **112c limpos** (18 palavras) $\implies$ **MÉDIO RISCO**

---

#### B. Card do Enunciado da Questão (Caixa: largura = 296 pt, altura útil = 196 pt)
- **Fonte Nominal:** `Open Sans` 12 pt Regular (`weight: 400`).
- **Largura Média do Caractere:** approximately $6{,}6\text{ pt}$.
- **Caracteres por Linha:** $\frac{296\text{ pt}}{6{,}6\text{ pt/char}} \approx 45\text{ caracteres por linha}$.
- **Altura da Linha com Espaçamento:** $12{,}0\text{ pt} \times 1{,}35 = 16{,}2\text{ pt}$.
- **Número Máximo de Linhas Úteis:** $\lfloor \frac{196\text{ pt}}{16{,}2\text{ pt}} \rfloor = 12\text{ linhas}$.
- **Capacidade Segura Teórica:** $12 \times 45 = 540\text{ caracteres}$.
- **Diagnóstico:** A questão com maior enunciado do banco é `Q-STO-008` (307c brutos / 241c limpos / 198c após remoção do tema N3, com 54 palavras). Em 12pt, ocupa approximately 6 linhas, restando folga de mais de 80 pt no card. **Nenhum enunciado ultrapassa o limite físico vertical da caixa de 196 pt.** No entanto, para enunciados com mais de 200 caracteres, a redução sutil para 11.0 pt ou 10.5 pt melhora drasticamente o respiro visual e a elegância gráfica do slide (*anti-vibe design*).

#### Questões com Enunciados Extensos (> 200 caracteres limpos):
1. `Q-STO-007`: 264c limpos (43 palavras)
2. `Q-SOL-008`: 264c limpos / 219c display (53 palavras)
3. `Q-SOL-007`: 257c limpos / 208c display (50 palavras)
4. `Q-STO-008`: 241c limpos / 198c display (54 palavras)
5. `Q-SOL-005`: 229c limpos / 200c display (42 palavras)
6. `Q-SOL-002`: 222c limpos (48 palavras)
7. `Q-SOL-003`: 219c limpos (41 palavras)
8. `Q-ENV-006`: 210c limpos / 164c display (35 palavras)
9. `Q-ENV-005`: 204c limpos (35 palavras)

---

#### C. Card de Justificativa e Distrator no Slide de Resposta (Caixa: largura = 288 pt, altura útil = 196 pt)
No slide de resposta, o card da direita concatena dois subtítulos em negrito e dois parágrafos explicativos:
```
✦ FUNDAMENTO FÍSICO-QUÍMICO:
{scientific_justification}

✦ POR QUE A ALTERNATIVA {errada} É UM ERRO TÍPICO?
{distractor_rationale}
```
- Os dois subtítulos somam 4 linhas (o segundo cabeçalho ocupa 2 linhas em 288 pt).
- **Casos mais extensos:**
  - `Q-STO-008`: 132c (justificativa) + 130c (distrator) + títulos = approximately 312 caracteres de texto puro (12 a 13 linhas no total).
  - `Q-STO-006`: 106c + 133c + títulos = 289 caracteres.
  - `Q-SOL-009`: 122c + 114c + títulos = 286 caracteres.
  - `Q-ENV-006`: 117c + 116c + títulos = 283 caracteres.
- **Risco:** Em 10.5 pt com entrelinha de 130%, 13 linhas atingem approximately $13 \times 13{,}65 = 177{,}5\text{ pt}$. Em caixas de 196 pt, a folga residual é de apenas 18 pt. Caso o texto passe de 260 caracteres, é indispensável escalonar a fonte para 10.0 pt ou 9.5 pt para evitar colisão com a margem inferior.

---

### 4.3 Regras Matemáticas de Auto-Scaling Anti-Overflow (`compute_typography_params`)

Para blindar completamente o gerador contra qualquer truncamento ou degradação visual, define-se o algoritmo matemático determinístico de auto-scaling que deve ser incorporado em `gerar_slides_perguntas_respostas.py`:

```python
def compute_typography_params(
    statement_text: str,
    max_option_len: int,
    col2_answer_len: int
) -> tuple[float, int, float, int, float, int]:
    """
    Computa dinamicamente tamanhos de fonte e line spacing em pontos
    para eliminar qualquer risco de overflow nos cards Fintech Clean.
    
    Retorna:
        (stmt_font_size, stmt_line_spacing,
         opt_font_size, opt_line_spacing,
         ans2_font_size, ans2_line_spacing)
    """
    # 1. Enunciado da Questão (Card Esquerdo: w=296, h=196 pt)
    stmt_len = len(statement_text)
    if stmt_len > 240:
        stmt_font_size = 10.5
        stmt_line_spacing = 125
    elif stmt_len > 180:
        stmt_font_size = 11.0
        stmt_line_spacing = 130
    else:
        stmt_font_size = 12.0
        stmt_line_spacing = 135

    # 2. Alternativas A e B (Cards Direitos: w=288, h=68 pt)
    if max_option_len > 110:
        opt_font_size = 9.8
        opt_line_spacing = 120
    elif max_option_len > 80:
        opt_font_size = 10.5
        opt_line_spacing = 125
    else:
        opt_font_size = 11.5
        opt_line_spacing = 130

    # 3. Justificativa Científica + Distrator (Gabarito Direito: w=288, h=196 pt)
    if col2_answer_len > 260:
        ans2_font_size = 9.5
        ans2_line_spacing = 120
    elif col2_answer_len > 200:
        ans2_font_size = 10.0
        ans2_line_spacing = 125
    else:
        ans2_font_size = 10.5
        ans2_line_spacing = 130

    return (
        stmt_font_size, stmt_line_spacing,
        opt_font_size, opt_line_spacing,
        ans2_font_size, ans2_line_spacing
    )
```

#### Tabela 4.1 — Matriz de Parâmetros de Auto-Scaling Anti-Overflow

| Componente | Critério de Extensão | Tamanho de Fonte | Line Spacing | Linhas Estimadas | Altura Total Estimada | Altura Útil da Caixa | Folga Mínima de Segurança |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Alternativas** | $\le 80$ caracteres | **11.5 pt** | 130% (14.9 pt) | 1 a 2 linhas | 15 a 30 pt | 68 pt | $\ge 38\text{ pt}$ |
| **Alternativas** | $81$ a $110$ caracteres | **10.5 pt** | 125% (13.1 pt) | 2 a 3 linhas | 26 a 39 pt | 68 pt | $\ge 29\text{ pt}$ |
| **Alternativas** | $> 110$ caracteres | **9.8 pt** | 120% (11.8 pt) | 3 a 4 linhas | 35 a 47 pt | 68 pt | $\ge 21\text{ pt}$ |
| **Enunciado** | $\le 180$ caracteres | **12.0 pt** | 135% (16.2 pt) | 2 a 4 linhas | 32 a 65 pt | 196 pt | $\ge 131\text{ pt}$ |
| **Enunciado** | $181$ a $240$ caracteres | **11.0 pt** | 130% (14.3 pt) | 4 a 5 linhas | 57 a 72 pt | 196 pt | $\ge 124\text{ pt}$ |
| **Enunciado** | $> 240$ caracteres | **10.5 pt** | 125% (13.1 pt) | 5 a 6 linhas | 65 a 79 pt | 196 pt | $\ge 117\text{ pt}$ |
| **Gabarito Col 2** | $\le 200$ caracteres | **10.5 pt** | 130% (13.6 pt) | 6 a 8 linhas | 82 a 109 pt | 196 pt | $\ge 87\text{ pt}$ |
| **Gabarito Col 2** | $201$ a $260$ caracteres | **10.0 pt** | 125% (12.5 pt) | 9 a 11 linhas | 112 a 138 pt | 196 pt | $\ge 58\text{ pt}$ |
| **Gabarito Col 2** | $> 260$ caracteres | **9.5 pt** | 120% (11.4 pt) | 11 a 13 linhas | 125 a 148 pt | 196 pt | $\ge 48\text{ pt}$ |

*Conclusão da Modelagem:* Com essa parametrização dinâmica, a folga mínima residual no card mais crítico (alternativas longas) passa de perigosos 8 pt para confortáveis **21 pt**, garantindo 100% de conformidade com a asserção `fontScale >= 0.90` da Google Slides API.

---

## 5. Plano Estrito de Partição e Distribuição de Questões

A partição do banco de 25 questões atende rigorosamente a todos os requisitos do projeto (`ORIGINAL_REQUEST.md` §R2, §R3, §R4 e `PROJECT.md`).

---

### 5.1 Apresentação de Teste Exclusiva (R2)

- **Identificador:** `deck_teste_nivel_1`
- **Total de Questões:** Exatamente 3 questões de Nível 1.
- **Composição dos Slides:** Exatamente **7 slides** (1 Capa Temática de Treino + 3 pares intercalados Pergunta $\to$ Resposta).
- **Lista de Questões Selecionadas:**
  1. `Q-ATO-001` (N1 — Estrutura Atômica): Critério de organização da Tabela Periódica moderna (número atômico $Z$). Questão de puro reconhecimento conceitual, leitura rápida em 15 segundos, perfeita para a primeira aposta de teste.
  2. `Q-SOL-001` (N1 — Soluções): Cálculo de concentração comum ($C = m / V = 10\text{ g} / 2\text{ L} = 5{,}0\text{ g/L}$). Aplicação direta de fórmula aritmética com números inteiros simples.
  3. `Q-STO-001` (N1 — Estequiometria): Quantidade de matéria em 117 g de $\text{NaCl}$ ($n = m / M = 117 / 58{,}5 = 2{,}0\text{ mol}$).
- **Regra de Isolamento Absoluto (Zero-Reuse):**
  $$\{ \text{Q-ATO-001}, \text{Q-SOL-001}, \text{Q-STO-001} \} \cap \text{Todos os Outros Decks} = \emptyset$$
  Estas 3 questões são banidas de todas as apresentações regulares, de desafio ou suplementares.

---

### 5.2 Apresentações Individuais de Desafio — Nível 3 (R3)

- **Total de Arquivos:** Exatamente **5 apresentações independentes e exclusivas**.
- **Composição por Apresentação:** Exatamente 1 questão de Nível 3 por arquivo.
- **Estrutura de Cada Apresentação:** Exatamente **3 slides**:
  - *Slide 1 (Capa / Fase 1 — Aposta no Escuro):* Apresenta o título da Morte Súbita, o Tema do Desafio, a regra de aposta mínima de 100 T$ e a mecânica de All-In.
  - *Slide 2 (Pergunta / Fase 2 — Leitura e Confirmação):* Apresenta o enunciado limpo e as alternativas [A] e [B], com badge de foco visual em roxo ametista.
  - *Slide 3 (Gabarito / Fase 3 — Resolução e Liquidação Winner Takes All):* Exibe a resolução técnica passo a passo, o fundamento físico-químico e a adjudicação do pote central.
- **Mapeamento Individual dos 5 Arquivos de Desafio:**
  1. `desafio_01_morte_subita_diluicao`: `Q-SOL-005` (Diluição de Soluções — Volume de Água Adicionado)
  2. `desafio_02_morte_subita_molaridade_sal`: `Q-SOL-007` (Molaridade Multietapa a partir da Massa de $\text{NaCl}$)
  3. `desafio_03_morte_subita_soda_caustica`: `Q-SOL-008` (Preparo de Solução de $\text{NaOH}$ — Molaridade vs Concentração Comum)
  4. `desafio_04_morte_subita_estequiometria_agua`: `Q-STO-008` (Síntese da Água — Reagente Limitante e Rendimento Real de 50%)
  5. `desafio_05_morte_subita_chuva_acida`: `Q-ENV-006` (Geoquímica da Chuva Ácida — Mobilização de $\text{Al}^{3+}$ e Correção por Calagem com $\text{CaCO}_3$)
- **Total de Slides Acumulado:** $5 \times 3 = 15\text{ slides}$.

---

### 5.3 Apresentações Regulares de 5 Questões (R4)

Após reservar 3 questões para o Teste (N1) e 5 questões para os Desafios (N3), restam no banco:
- Questões de Nível 1: $13 - 3 = 10\text{ questões}$.
- Questões de Nível 2: $7 - 0 = 7\text{ questões}$.
- Total disponível para rodadas regulares: $10 + 7 = 17\text{ questões}$.

Como a especificação do requisito **R4** exige apresentações regulares fechadas contendo **exatamente 5 perguntas e respostas por arquivo**, $15$ questões são distribuídas em **3 Decks Regulares de 5 Q&A** ($3 \times 5 = 15$), e as $2$ questões restantes são organizadas como um **Deck Suplente / Desempate Técnico**:

#### A. Deck Regular 01 — Nível 1 (Aquecimento — Parte 1)
- **Identificador:** `deck_regular_01`
- **Composição:** 5 questões de Nível 1.
- **Slide Count:** Exatamente **11 slides** (1 Capa + 5 pares Q&A intercalados).
- **Questões Alocadas:**
  1. `Q-ATO-002` (Lote 001): Famílias e Períodos na Tabela Periódica.
  2. `Q-SOL-006` (Lote 002): Definição de Volume Final na Concentração Comum.
  3. `Q-STO-002` (Lote 003): Quantidade de Matéria em 9,2 g de Sódio Metálico.
  4. `Q-STO-003` (Lote 004): Coeficientes Estequiométricos vs Índices Moleculares.
  5. `Q-STO-004` (Lote 005): Cálculo da Massa Molar da Água ($18{,}0\text{ g/mol}$).

#### B. Deck Regular 02 — Nível 1 (Aquecimento — Parte 2)
- **Identificador:** `deck_regular_02`
- **Composição:** 5 questões de Nível 1.
- **Slide Count:** Exatamente **11 slides** (1 Capa + 5 pares Q&A intercalados).
- **Questões Alocadas:**
  1. `Q-STO-005` (Lote 006): Massa em Gramas de 3,0 mol de Água ($54\text{ g}$).
  2. `Q-ENV-001` (Lote 007): Dióxido de Enxofre ($\text{SO}_2$) e Acidificação da Chuva.
  3. `Q-ENV-002` (Lote 008): Mecanismo do Efeito Estufa (Infravermelho) vs Ozônio (UV).
  4. `Q-ENV-003` (Lote 009): Balanço Biogeoquímico de $\text{O}_2$ e $\text{CO}_2$ em Floresta Clímax.
  5. `Q-ENV-004` (Lote 010): Economia de Energia na Reciclagem do Alumínio frente à Bauxita.

#### C. Deck Regular 03 — Nível 2 (Finais de Alta Complexidade)
- **Identificador:** `deck_regular_03`
- **Composição:** 5 questões de Nível 2.
- **Slide Count:** Exatamente **11 slides** (1 Capa + 5 pares Q&A intercalados).
- **Questões Alocadas:**
  1. `Q-SOL-002` (Lote 011): Comparação de Concentração em Frascos de Soro (mL para L).
  2. `Q-SOL-003` (Lote 012): Concentração Molar como Propriedade Intensiva em Alíquota.
  3. `Q-SOL-004` (Lote 013): Diluição com Adição de Água ($100\text{ mL} \to 400\text{ mL}$).
  4. `Q-SOL-009` (Lote 014): Mistura de Soluções de Solutos Iguais ($\text{NaCl}$).
  5. `Q-STO-006` (Lote 015): Reagente Limitante na Neutralização $\text{H}_2\text{SO}_4 + 2\text{ NaOH}$.

---

### 5.4 Deck Suplente / Rodada Extra de Desempate (Nível 2 — SPEC-02 §4.4)

- **Identificador:** `deck_suplente_desempate`
- **Composição:** 2 questões de Nível 2.
- **Slide Count:** Exatamente **5 slides** (1 Capa + 2 pares Q&A intercalados).
- **Alinhamento com o Regulamento Oficial:** O regulamento em `SPEC-02-regras-do-jogo.md` (§4.4 — Empate Técnico e Desempate) estabelece que, se houver empate em 1º lugar antes da Morte Súbita (diferença $\le 100\text{ T\$}$), o professor deve aplicar uma rodada rápida de desempate antes de acionar o desafio final. As 2 questões restantes de Nível 2 cumprem perfeitamente essa função pedagógica sem poluir os decks regulares de 5 questões:
  1. `Q-ENV-005` (Suplente 1): Conversor Catalítico Automotivo ($\text{CO} \to \text{CO}_2$).
  2. `Q-STO-007` (Suplente 2): Rendimento Reacional Industrial de 80% e Limitante.

---

### 5.5 Matriz Geral Consolidada de Partição das 25 Questões

A tabela a seguir apresenta o destino definitivo e unívoco de cada uma das 25 questões do banco oficial:

| # | ID da Questão | Nível | Domínio | Cognitivo | Destino Oficial (Apresentação / Deck) | Total Slides do Deck | Papel Didático na Dinâmica |
|:---:|:---|:---:|:---:|:---:|:---|:---:|:---|
| 01 | `Q-ATO-001` | N1 | `CHEM-ATO` | recog. | **Apresentação de Teste Exclusiva (R2)** | 7 slides | Teste 1: Conceitual Tabela Periódica |
| 02 | `Q-SOL-001` | N1 | `CHEM-SOL` | appli. | **Apresentação de Teste Exclusiva (R2)** | 7 slides | Teste 2: Concentração Comum Direta |
| 03 | `Q-STO-001` | N1 | `CHEM-STO` | appli. | **Apresentação de Teste Exclusiva (R2)** | 7 slides | Teste 3: Quantidade de Matéria de NaCl |
| 04 | `Q-ATO-002` | N1 | `CHEM-ATO` | recog. | **Deck Regular 01 (Aquecimento 1)** | 11 slides | Lote 001: Famílias vs Períodos |
| 05 | `Q-SOL-006` | N1 | `CHEM-SOL` | under. | **Deck Regular 01 (Aquecimento 1)** | 11 slides | Lote 002: Volume Final da Solução |
| 06 | `Q-STO-002` | N1 | `CHEM-STO` | appli. | **Deck Regular 01 (Aquecimento 1)** | 11 slides | Lote 003: Mols de Sódio Metálico |
| 07 | `Q-STO-003` | N1 | `CHEM-STO` | under. | **Deck Regular 01 (Aquecimento 1)** | 11 slides | Lote 004: Coeficientes vs Índices |
| 08 | `Q-STO-004` | N1 | `CHEM-STO` | appli. | **Deck Regular 01 (Aquecimento 1)** | 11 slides | Lote 005: Massa Molar da Água |
| 09 | `Q-STO-005` | N1 | `CHEM-STO` | appli. | **Deck Regular 02 (Aquecimento 2)** | 11 slides | Lote 006: Massa de 3,0 mol de H₂O |
| 10 | `Q-ENV-001` | N1 | `CHEM-ENV` | under. | **Deck Regular 02 (Aquecimento 2)** | 11 slides | Lote 007: Chuva Ácida e SO₂ |
| 11 | `Q-ENV-002` | N1 | `CHEM-ENV` | under. | **Deck Regular 02 (Aquecimento 2)** | 11 slides | Lote 008: Efeito Estufa vs Ozônio |
| 12 | `Q-ENV-003` | N1 | `CHEM-ENV` | under. | **Deck Regular 02 (Aquecimento 2)** | 11 slides | Lote 009: Fotossíntese e Clímax |
| 13 | `Q-ENV-004` | N1 | `CHEM-ENV` | under. | **Deck Regular 02 (Aquecimento 2)** | 11 slides | Lote 010: Reciclagem Al vs Bauxita |
| 14 | `Q-SOL-002` | N2 | `CHEM-SOL` | appli. | **Deck Regular 03 (Finais)** | 11 slides | Lote 011: Frascos de Soro (mL para L) |
| 15 | `Q-SOL-003` | N2 | `CHEM-SOL` | appli. | **Deck Regular 03 (Finais)** | 11 slides | Lote 012: Concentração Molar Alíquota |
| 16 | `Q-SOL-004` | N2 | `CHEM-SOL` | appli. | **Deck Regular 03 (Finais)** | 11 slides | Lote 013: Diluição com Água Pura |
| 17 | `Q-SOL-009` | N2 | `CHEM-SOL` | appli. | **Deck Regular 03 (Finais)** | 11 slides | Lote 014: Mistura de Soluções NaCl |
| 18 | `Q-STO-006` | N2 | `CHEM-STO` | appli. | **Deck Regular 03 (Finais)** | 11 slides | Lote 015: Reagente Limitante H₂SO₄ |
| 19 | `Q-ENV-005` | N2 | `CHEM-ENV` | appli. | **Deck Suplente / Desempate (N2)** | 5 slides | Suplente 1: Conversor Catalítico CO |
| 20 | `Q-STO-007` | N2 | `CHEM-STO` | appli. | **Deck Suplente / Desempate (N2)** | 5 slides | Suplente 2: Rendimento Industrial 80% |
| 21 | `Q-SOL-005` | N3 | `CHEM-SOL` | appli. | **Apresentação de Desafio 01 (R3)** | 3 slides | Morte Súbita 1: Diluição com Solvente |
| 22 | `Q-SOL-007` | N3 | `CHEM-SOL` | analy. | **Apresentação de Desafio 02 (R3)** | 3 slides | Morte Súbita 2: Molaridade a partir de Massa |
| 23 | `Q-SOL-008` | N3 | `CHEM-SOL` | analy. | **Apresentação de Desafio 03 (R3)** | 3 slides | Morte Súbita 3: Soda Cáustica Molaridade |
| 24 | `Q-STO-008` | N3 | `CHEM-STO` | analy. | **Apresentação de Desafio 04 (R3)** | 3 slides | Morte Súbita 4: Síntese da Água Limitante |
| 25 | `Q-ENV-006` | N3 | `CHEM-ENV` | analy. | **Apresentação de Desafio 05 (R3)** | 3 slides | Morte Súbita 5: Chuva Ácida e Calagem |

---

### 5.6 Prova Formal de Isolamento e Zero-Reuse

Apresenta-se a demonstração matemática formal de que a partição proposta é rigorosamente exata, completa e mutuamente disjunta:

#### A. Definições dos Conjuntos
Seja $U$ o universo finito de todas as questões homologadas do banco de dados:
$$U = \{ q \in \text{QuestionBank} \mid |U| = 25 \}$$

Definem-se os seguintes subconjuntos de alocação:
1. Conjunto do Deck de Teste:
   $$T = \{ \text{Q-ATO-001}, \text{Q-SOL-001}, \text{Q-STO-001} \}, \quad |T| = 3$$
2. Conjuntos das 5 Apresentações de Desafio Nível 3:
   $$D_1 = \{ \text{Q-SOL-005} \}, \quad D_2 = \{ \text{Q-SOL-007} \}, \quad D_3 = \{ \text{Q-SOL-008} \}, \quad D_4 = \{ \text{Q-STO-008} \}, \quad D_5 = \{ \text{Q-ENV-006} \}$$
   $$D = \bigcup_{i=1}^5 D_i, \quad |D| = 5$$
3. Conjuntos das 3 Apresentações Regulares:
   $$R_1 = \{ \text{Q-ATO-002}, \text{Q-SOL-006}, \text{Q-STO-002}, \text{Q-STO-003}, \text{Q-STO-004} \}, \quad |R_1| = 5$$
   $$R_2 = \{ \text{Q-STO-005}, \text{Q-ENV-001}, \text{Q-ENV-002}, \text{Q-ENV-003}, \text{Q-ENV-004} \}, \quad |R_2| = 5$$
   $$R_3 = \{ \text{Q-SOL-002}, \text{Q-SOL-003}, \text{Q-SOL-004}, \text{Q-SOL-009}, \text{Q-STO-006} \}, \quad |R_3| = 5$$
   $$R = R_1 \cup R_2 \cup R_3, \quad |R| = 15$$
4. Conjunto do Deck Suplente / Desempate:
   $$S = \{ \text{Q-ENV-005}, \text{Q-STO-007} \}, \quad |S| = 2$$

#### B. Teorema da Partição Exata (Zero-Reuse & Completude)
A família de subconjuntos $\mathcal{P} = \{ T, D_1, D_2, D_3, D_4, D_5, R_1, R_2, R_3, S \}$ constitui uma partição estrita de $U$:
$$\forall X, Y \in \mathcal{P}, \quad X \ne Y \implies X \cap Y = \emptyset$$
$$\bigcup_{X \in \mathcal{P}} X = U$$

#### C. Demonstração
1. **Disjunção do Deck de Teste ($T$):**
   - $T \cap R_1 = \emptyset$, $T \cap R_2 = \emptyset$, $T \cap R_3 = \emptyset \implies T \cap R = \emptyset$.
   - $T \cap D = \emptyset$ (todas as questões de $T$ possuem `difficulty == 1`, enquanto todas as questões de $D$ possuem `difficulty == 3`).
   - $T \cap S = \emptyset$ (todas as questões de $S$ possuem `difficulty == 2`).
   - Portanto, nenhuma questão da Apresentação de Teste é reutilizada em nenhum outro deck do jogo. Satisfaz-se cabalmente o Requisito **R2**.

2. **Disjunção entre os Decks Regulares ($R_1, R_2, R_3$):**
   - $R_1 \cap R_2 = \emptyset$: $R_1$ contém os domínios ATO, SOL e STO (`Q-ATO-002` a `Q-STO-004`), enquanto $R_2$ contém STO (`Q-STO-005`) e o bloco ambiental completo (`Q-ENV-001` a `Q-ENV-004`).
   - $R_1 \cap R_3 = \emptyset$: $R_1$ contém exclusivamente questões de Nível 1, e $R_3$ contém exclusivamente questões de Nível 2.
   - $R_2 \cap R_3 = \emptyset$: $R_2$ contém exclusivamente questões de Nível 1, e $R_3$ contém exclusivamente questões de Nível 2.
   - Portanto, não há repetição entre nenhuma partida regular. Satisfaz-se cabalmente o Requisito **R4**.

3. **Disjunção dos Decks de Desafio ($D_i$):**
   - Cada $D_i$ é um conjunto unitário com um ID canônico de N3 distinto.
   - $\forall i \ne j, D_i \cap D_j = \emptyset$.
   - $D \cap (T \cup R \cup S) = \emptyset$, pois $D$ é a totalidade das questões com `difficulty == 3`, ao passo que $T \cup R \cup S$ contém exclusivamente questões com `difficulty \in {1, 2}`. Satisfaz-se cabalmente o Requisito **R3**.

4. **Completude Cardinal do Banco:**
   $$\sum_{X \in \mathcal{P}} |X| = |T| + \sum_{i=1}^5 |D_i| + |R_1| + |R_2| + |R_3| + |S|$$
   $$\sum_{X \in \mathcal{P}} |X| = 3 + (1 + 1 + 1 + 1 + 1) + 5 + 5 + 5 + 2 = 3 + 5 + 15 + 2 = 25 = |U|$$
   Como a soma das cardinalidades dos subconjuntos disjuntos é igual à cardinalidade de $U$, fica formalmente demonstrado que:
   - Nenhuma questão é descartada.
   - Nenhuma questão é duplicada.
   - Todas as 25 questões do banco oficial possuem destinação precisa e unívoca em produção.

---

## 6. Diretrizes de Implementação para os Scripts Gerador e Validador

Esta seção define as especificações técnicas obrigatórias que devem guiar a implementação dos próximos marcos do projeto (M2, M3 e M4).

---

### 6.1 Diretrizes para o Gerador de Slides (`gerar_slides_perguntas_respostas.py`)

1. **Eliminação do Monolitismo:**
   - Remover as validações estáticas que amarram o script a 20 questões (`len(data_n1) == 13`, `len(data_n2) == 7`, `total == 20`).
   - Introduzir o modelo de dados `DeckConfig`:
     ```python
     @dataclass
     class DeckConfig:
         deck_id: str
         deck_type: str  # "test" | "regular" | "challenge" | "tiebreaker"
         title: str
         subtitle: str
         questions: list[dict]
         batch_filename: str
         presentation_id: str | None = None
     ```
2. **Suporte a Morte Súbita (Nível 3):**
   - Remover a proibição ativa de `difficulty == 3`.
   - Implementar a função `build_challenge_cover_operations()`:
     - Renderizar o Slide 1 com o Tema do Desafio extraído via regex (`r"🔥\s*\[APOSTA NO TEMA:\s*(.*?)\]"`).
     - Renderizar as regras de entrada da Morte Súbita (Aposta no Escuro, mínimo de 100 T$).
   - No Slide 2 (Pergunta), limpar o prefixo de fogo do enunciado e adicionar o badge superior em roxo ametista: `DESAFIO DA MESA • MORTE SÚBITA`.
3. **Mecanismo Anti-Overflow e Tipografia Química IUPAC:**
   - Incorporar a função `compute_typography_params` para parametrizar dinamicamente `font_size` e `line_spacing` em todos os textboxes.
   - Atualizar a função `clean_chemical_typography` para normalizar $M(\text{Elemento})$ antes da conversão de subscritos:
     ```python
     text = re.sub(r"M<sub>([A-Za-z0-9\u2080-\u2089]+)</sub>", r"M(\1)", text)
     ```
   - Auto-subscritar fórmulas moleculares não marcadas em `worked_solution` (`H2O` $\to$ `H₂O`, `CO2` $\to$ `CO₂`, `SO2` $\to$ `SO₂`).
4. **Catálogo de Manifesto (`decks_manifest.json`):**
   - Ao executar a geração ou compilação de batches, emitir o arquivo estruturado `decks_manifest.json` com os IDs locais ou remotos de cada apresentação, mapeando tipo, quantidade de slides e lista de IDs das questões.

---

### 6.2 Diretrizes para o Validador Automatizado (`verificar_decks_slides.py`)

1. **Suporte ao Modo Multi-Deck por Manifesto:**
   - Implementar a flag `--manifest <path/to/decks_manifest.json>` para permitir que o validador audite programaticamente todas as apresentações do projeto em uma única execução.
2. **Novas Baterias de Asserções Estruturais e de Isolamento:**
   - `TEST_SLIDES_COUNT`: Asserção de que o Deck de Teste contém exatamente **7 slides**.
   - `TEST_EXACT_3_N1`: Asserção de que o Deck de Teste contém exatamente **3 questões de Nível 1**.
   - `TEST_ZERO_REUSE`: Asserção de que a intersecção entre as questões do Deck de Teste e todos os outros decks é rigorosamente vazia.
   - `N3_FILES_COUNT`: Asserção de que existem exatamente **5 apresentações de desafio**.
   - `N3_SINGLE_QUESTION`: Asserção de que cada arquivo de desafio possui exatamente **1 questão de Nível 3**.
   - `REG_SLIDES_COUNT`: Asserção de que cada Deck Regular possui exatamente **11 slides** (1 capa + 5 pares Q&A).
   - `REG_EXACT_5_PAIRS`: Asserção de que cada Deck Regular contém exatamente **5 questões**.
   - `REG_DISJOINT`: Asserção de que não há interseção entre nenhum par de decks regulares.
3. **Asserções de Fidelidade ao Design System Fintech Clean:**
   - `DS_BG_FINTECH`: Fundo de todos os slides deve ser `#F8F9FA` ($R \approx 0{,}9725, G \approx 0{,}9765, B \approx 0{,}9804$).
   - `DS_CARD_WHITE`: Presença de cards elevados em `#FFFFFF` com contorno suave `#E2E8F0`.
   - `DS_FONT_FAMILY`: 100% dos textos devem utilizar exclusivamente a fonte `Open Sans`.
   - `DS_NO_OVERFLOW`: Verificação do atributo `autofit.fontScale` retornado pela Google Slides API. Falha imediata se `fontScale < 0.90`.

---

### 6.3 Resumo das Entregas de Arquivos Planejadas para Produção

```
========================================================================================
RESUMO DOS ARQUIVOS DE SLIDES DO PROJETO ALL-IN QUÍMICO
========================================================================================
1. deck_regras_didaticas            (6 slides)   - Regras Oficiais, Apostas, Matriz 6x4
2. deck_teste_nivel_1 (R2)          (7 slides)   - Treino Sem Risco (Q-ATO-001, SOL-001, STO-001)
3. deck_regular_01 (R4)             (11 slides)  - Partida Regular 1: 5 Questões N1
4. deck_regular_02 (R4)             (11 slides)  - Partida Regular 2: 5 Questões N1
5. deck_regular_03 (R4)             (11 slides)  - Partida Regular 3: 5 Questões N2
6. deck_suplente_desempate          (5 slides)   - Rodada Extra de Desempate (2 Questões N2)
7. desafio_01_morte_subita_diluicao (3 slides)   - Desafio Final N3: Q-SOL-005
8. desafio_02_morte_subita_molar... (3 slides)   - Desafio Final N3: Q-SOL-007
9. desafio_03_morte_subita_soda_... (3 slides)   - Desafio Final N3: Q-SOL-008
10. desafio_04_morte_subita_esteq.. (3 slides)   - Desafio Final N3: Q-STO-008
11. desafio_05_morte_subita_chuva.. (3 slides)   - Desafio Final N3: Q-ENV-006
----------------------------------------------------------------------------------------
TOTAL GLOBAL: 11 APRESENTAÇÕES INDEPENDENTES | 66 SLIDES DE ALTA FIDELIDADE
========================================================================================
```

---

## 7. Conclusão e Homologação da Auditoria

A presente auditoria cumpriu de forma exaustiva e irrestrita todas as exigências estabelecidas no Requisito **R1**:
- O inventário completo de todas as 25 questões foi extraído e catalogado com métricas exatas.
- O defeito crítico de subscritos maiúsculos em massa molar foi explicado em sua causa raiz e resolvido com base na notação oficial IUPAC $M(X)$.
- As variações de pontuação, formatação de fórmulas e marcações de tema de Nível 3 foram mapeadas e harmonizadas.
- O risco de overflow foi quantificado matematicamente e neutralizado pelo algoritmo determinístico `compute_typography_params`.
- O plano de partição disjunto foi formalmente provado por Teoria dos Conjuntos, garantindo isolamento total do deck de teste (R2), foco individual nos desafios de morte súbita (R3), decks regulares fechados de 5 questões (R4) e alocação pedagógica de desempate técnico (SPEC-02 §4.4).

Com a publicação deste documento na raiz do projeto (`c:\Users\Vaio\Documents\Jaques\Leilão-Química-v1.00\relatorio_auditoria_questoes.md`), o Marco **M1** é formalmente concluído, autorizando o início dos trabalhos de engenharia dos geradores no Marco **M2**.

---
*Assinado digitalmente pela Equipe de Auditoria Técnica e Didática All-In Químico.*
