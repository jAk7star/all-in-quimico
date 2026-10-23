# SPEC-02 — Sistema de Apostas do Jogo (Pari-Mutuel de Risco Zero & Fase 3 Texas Hold'em)

Este documento define o regulamento oficial e a modelagem matemática do sistema de apostas do jogo **Leilão de Química**, separando as regras econômicas e de rodadas (SPEC-02) do conhecimento químico subjacente (SPEC-00) e do banco de questões (SPEC-01).

---

## 1. Estrutura Básica da Rodada e Protocolo Simultâneo
- Cada equipe inicia o jogo com **`1.000 T$` (Tokens)** em cédulas de `50`, `100` e `500 T$`, além de duas placas de decisão (**A** e **B**).
- Antes do início oficial, o professor conduz **1 Rodada-Treino (valendo `0 T$`)** para que todas as equipes pratiquem a mecânica sem risco de perder fichas.
- **Calibração de Risco pelo Tema:** Em todas as rodadas, o professor anuncia primeiro o **Tema e Subtema** da carta (ex.: *"Soluções — Diluição"*).
- **Fases 1 e 2 (Aposta Direta):** O professor lê a pergunta e as duas alternativas (**A** e **B**). Todas as equipes escolhem secretamente sua alternativa e separam suas cédulas (entre `50 T$` e `500 T$`), revelando simultaneamente ao sinal do professor.
- **Fase 3 — Morte Súbita (Estilo Texas Hold'em — Aposta no Tema no Escuro):**
  1. **Aposta no Escuro (Pré-Leitura):** O professor anuncia **apenas o Tema** da carta. Sem ver a pergunta, cada equipe coloca na mesa uma aposta obrigatória (mínimo `100 T$`) confiando no quanto domina aquele assunto.
  2. **Leitura + Check ou Raise (Showdown):** O professor lê a pergunta completa e as alternativas A e B. Cada equipe escolhe secretamente sua placa (**A** ou **B**) e decide se apenas **mantém** a aposta inicial (**Check**) ou se **aumenta / dá All-in** (**Raise**) colocando mais fichas antes da revelação simultânea.
- **Quem perde a aposta perde tudo:** 100% dos tokens apostados na opção incorreta vão para o pote da rodada.

---

## 2. Mecânica de Multiplicador (Pari-Mutuel Direto Sem Comissão)
- O retorno é calculado pelo sistema **pari-mutuel puro** (bolão proporcional mútuo sem taxa percentual da casa, $c = 0\%$).
- **100% do pote dos perdedores** vai para o cálculo do multiplicador dos vencedores, tornando a conta mental rápida em sala de aula.
- **Quanto menos tokens** forem apostados na alternativa certa, **maior será o multiplicador** dela.
- **Quanto mais tokens** forem apostados na alternativa certa, **menor será o multiplicador** dela.

---

## 3. Fórmula Matemática e Garantias de Blindagem da Mesa

### Variáveis
- $T_A$ = total de tokens apostados na resposta **A**
- $T_B$ = total de tokens apostados na resposta **B**
- $T = T_A + T_B$ = total do pote arrecadado na rodada
- $P_{\text{ant}}$ = pote acumulado de rodada anterior sem vencedores (*Rollover / Jackpot*, padrão $0$)
- $P = T + P_{\text{ant}}$ = Pote Total disponível na rodada

### 3.1. Cálculo do Multiplicador (Odd de Retorno Total)
- **Se A for a resposta correta ($T_A > 0$):**
  $$O_A = \frac{P}{T_A}$$
- **Se B for a resposta correta ($T_B > 0$):**
  $$O_B = \frac{P}{T_B}$$
- Como $P \ge T_{\text{certa}}$, garante-se matematicamente que **$O_{\text{certa}} \ge 1,00\times$ sempre**, e a mesa **jamais tira 1 token do próprio bolso**.

### 3.2. Regra do Troco da Casa (*Breakage* em Múltiplos de 50 T$)
Como o jogo físico utiliza apenas cédulas de **50, 100 e 500 Tokens**, cada pagamento individual $\text{Pagamento}_i$ para uma aposta vencedora $b_i$ (já múltiplo de $50\text{ T\$}$) é **arredondado para baixo no múltiplo de 50 Tokens**:

$$\text{Pagamento}_i = \left\lfloor \frac{b_i \times O}{50} \right\rfloor \times 50$$

- **Troco da Casa (*Breakage*):** A sobra indivisível menor que `50 T$` por equipe ($\text{Breakage} = P - \sum \text{Pagamento}_i$) permanece no **Caixa da Casa**.
- **Rodada-Treino de Referência (3 Equipes):**
  - Equipe Alfa aposta `200 T$` em **A**; Equipe Beta aposta `100 T$` em **B**; Equipe Gama aposta `150 T$` em **B**.
  - Gabarito correto: **B**. Pote Total $P = 200 + 100 + 150 = 450\text{ T\$}$. Total apostado na certa ($T_B$) = $250\text{ T\$}$.
  - Multiplicador: $O_B = \frac{450}{250} = 1,80\times$.
  - **Beta:** $100 \times 1,80 = 180 \rightarrow$ recebe **`150 T$`** (lucro líquido de $+50\text{ T\$}$).
  - **Gama:** $150 \times 1,80 = 270 \rightarrow$ recebe **`250 T$`** (lucro líquido de $+100\text{ T\$}$).
  - **Alfa:** perde seus `200 T$`.
  - **Caixa da Casa:** retém os **`50 T$`** de troco ($450 - 400 = 50\text{ T\$}$).

---

## 4. Casos Especiais e Critério de Vitória

### 4.1. Todos acertam ($100\%$ na alternativa correta)
- O multiplicador é $O = 1,00\times$. Ninguém ganha e ninguém perde: cada equipe recebe de volta exatamente o que apostou.

### 4.2. Todos erram (*Rollover / Pote Acumulado*)
- Se nenhuma equipe apostar na alternativa correta ($T_{\text{certa}} = 0$), o Pote Total ($P$) **acumula integralmente ($P_{\text{ant}}$) para turbinar o Pote da próxima rodada** (*Jackpot*).

### 4.3. Repescagem Científica Auto-Sustentável (Quando uma equipe zera)
- Caso uma equipe perca tudo (`0 T$`), ela pode conquistar um auxílio de **`50 T$`** apresentando oralmente a justificativa científica correta de uma questão, **pago exclusivamente se o Caixa da Casa já tiver saldo acumulado de troco $\ge 50\text{ T\$}$**.

### 4.4. Critério de Vitória e Desempate Final (Duelo Oral Relâmpago)
- Ao final da última questão da Fase 3, vence a equipe que acumular **mais Tokens (`T$`)**.
- **Desempate de 1º Lugar:** Se duas ou mais equipes terminarem empatadas na liderança, sorteia-se uma carta extra de **Morte Súbita com All-in Automático**. Se o empate persistir (ambas acertarem ou ambas errarem), vence a equipe que **explicar oralmente primeiro o porquê científico da resposta correta**!
