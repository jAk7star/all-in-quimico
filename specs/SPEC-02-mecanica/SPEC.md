# SPEC-02 — Sistema de Apostas do Jogo (Pari-Mutuel Tokenizado e Blindado)

Este documento define o regulamento oficial e a modelagem matemática otimizada do sistema de apostas do jogo **Leilão de Química**, separando as regras econômicas e de rodadas (SPEC-02) do conhecimento químico subjacente (SPEC-00) e do banco de questões (SPEC-01).

---

## 1. Estrutura Básica da Rodada e Protocolo Simultâneo
- Uma pergunta é apresentada aos alunos/equipes com **duas respostas possíveis: A e B**.
- Os alunos não sabem qual é a alternativa correta no momento da aposta.
- **Apostas Simultâneas (Fechadas):** Todas as equipes escolhem secretamente sua alternativa (**A** ou **B**) e separam suas cédulas de **Tokens** (em múltiplos de `50 T$`), revelando simultaneamente ao sinal do professor. Isso elimina o "efeito manada" (copiar a aposta de outra equipe).
- **Quem perde a aposta perde tudo:** 100% dos tokens apostados na opção incorreta vão para o pool da rodada.

---

## 2. Mecânica de Odds (Retorno Pari-Mutuel)
- O retorno é calculado pelo sistema **pari-mutuel** (bolão proporcional mútuo).
- **Quanto menos tokens** forem apostados em uma resposta, **maior será a odd** dela.
- **Quanto mais tokens** forem apostados em uma resposta, **menor será a odd** dela.

---

## 3. Fórmula Matemática e Garantias de Blindagem da Mesa

### Variáveis
- $T_A$ = total de tokens apostados na resposta **A**
- $T_B$ = total de tokens apostados na resposta **B**
- $T = T_A + T_B$ = total do pool bruto arrecadado na rodada
- $P_{\text{ant}}$ = pool acumulado de rodada anterior sem vencedores (*Rollover / Jackpot*, padrão $0$)
- $c$ = percentual alvo da casa ($c = 0,10 = 10\%$, recomendado entre $5\%$ e $15\%$)

### 3.1. Garantia de Piso ($O \ge 1,00\times$) e Retenção Base da Casa
Para evitar que equipes que acertaram a questão tenham prejuízo quando mais de $90\%$ da sala acerta ($O < 1,00\times$), a retenção base da casa incide até o limite dos tokens perdedores ($T_{\text{errada}}$):

$$\text{Retenção Base da Casa} = \min\left(c \times T,\; T_{\text{errada}}\right)$$

$$\text{Pool Líquido } (P) = \left(T - \text{Retenção Base da Casa}\right) + P_{\text{ant}}$$

- Isso garante matematicamente que $P \ge T_{\text{certa}}$, logo **$O_{\text{certa}} \ge 1,00\times$ sempre**, e a mesa **jamais tira 1 token do próprio bolso**.

### 3.2. Cálculo das Odds (Multiplicador de Retorno Total)
- **Se A for a resposta correta ($T_A > 0$):**
  $$O_A = \frac{P}{T_A}$$
- **Se B for a resposta correta ($T_B > 0$):**
  $$O_B = \frac{P}{T_B}$$

### 3.3. Regra de Breakage (Arredondamento Físico em Múltiplos de 50 T$)
Como o jogo físico utiliza apenas cédulas de **50, 100 e 500 Tokens**, cada pagamento individual $\text{Pagamento}_i$ para uma aposta vencedora $b_i$ (já múltiplo de $50\text{ T\$}$) é **truncado para baixo no múltiplo de 50 Tokens**:

$$\text{Pagamento}_i = \left\lfloor \frac{b_i \times O}{50} \right\rfloor \times 50$$

- **Sobra de Arredondamento (*Breakage*):** A diferença fracionária não distribuída ($\text{Breakage} = P - \sum \text{Pagamento}_i$) permanece integralmente no **Caixa da Casa**.
- **Prova de Risco Zero da Mesa:** Como $O \ge 1,00\times$ e $b_i$ é múltiplo de $50$, todo vencedor recebe no mínimo sua aposta de volta ($\text{Pagamento}_i \ge b_i$), e a soma paga nunca excede o Pool Líquido ($\sum \text{Pagamento}_i \le P$). A mesa nunca precisa de cédulas menores que $50\text{ T\$}$ e nunca fica no negativo.

---

## 4. Cenários Principais

### Cenário 1 – Maioria erra
- A maioria dos tokens vai para a resposta errada.
- A Casa retém integralmente $c \times T$ ($10\%$) + *Breakage*.
- A odd da resposta correta fica **alta** ($O \gg 1,0\times$).
- Os vencedores dividem o pool líquido ($P$) proporcionalmente (truncado em múltiplos de $50\text{ T\$}$).

### Cenário 2 – Maioria acerta
- A maioria dos tokens vai para a resposta correta.
- A odd da resposta correta fica **baixa** (próxima de $1,0\times$ ou pouco acima, nunca inferior a $1,00\times$).
- A odd da resposta errada fica muito alta, mas quem apostou nela perde tudo.

### Cenário 3 – 100% da turma erra (Rollover / Pool Acumulado)
- Se nenhuma equipe apostar na alternativa correta ($T_{\text{certa}} = 0$):
  - A Casa retém sua comissão $\lfloor \frac{c \times T}{50} \rfloor \times 50$.
  - O Pool Líquido restante ($P$) **acumula integralmente ($P_{\text{ant}}$) para turbinar o Pool da próxima rodada** (*Jackpot*), gerando grande engajamento na questão seguinte sem custo para a mesa.

---

## 5. Gestão de Risco Pedagógico e Regras da Casa
- **Teto de Aposta nas Fases 1 e 2:** Aposta mínima de `50 T$` e **aposta máxima de `500 T$` por rodada** (50% da banca inicial), impedindo que uma equipe dê *All-in* e seja eliminada na 1ª rodada.
- **Fase 3 (Desafio Final):** Aposta mínima dobra (`100 T$`) e o **All-in é liberado** (até 100% da banca).
- **Repescagem Científica Auto-Sustentável:** Caso uma equipe zere seus tokens (`0 T$`), ela pode conquistar um auxílio de **`50 T$`** apresentando oralmente a justificativa científica correta de uma questão, **pago exclusivamente se o Caixa da Casa já tiver lucro acumulado $\ge 50\text{ T\$}$**. Assim, a Casa jamais fica negativa e nenhuma equipe abandona a aula.

---

## 6. Fluxo Resumido de uma Rodada (8 Passos)
1. **Pergunta + respostas A e B** são apresentadas.
2. **Apostas Simultâneas:** Equipes escolhem secretamente A ou B e separam seus Tokens (múltiplos de 50 T$), revelando juntas ao sinal do professor.
3. **Cálculo das Odds:** Soma-se $T_A$ e $T_B$ e calcula-se o Pool Líquido $P$ e as Odds $O_A$ e $O_B$.
4. **Revelação:** A resposta correta (A ou B) é revelada e explicada.
5. **Pagamento aos Vencedores:** Quem acertou recebe $\lfloor (b_i \times O) / 50 \rfloor \times 50$ Tokens (ou o Pool acumula em *Rollover* se $T_{\text{certa}} = 0$).
6. **Perda Total dos Perdedores:** Quem errou perde 100% dos tokens apostados.
7. **Caixa da Casa:** A casa retém sua comissão + a sobra de arredondamento (*Breakage*).
8. **Novo Ciclo:** O ciclo se repete para o próximo lote.
