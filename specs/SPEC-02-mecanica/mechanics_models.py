import math
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class PariMutuelRules(BaseModel):
    """Configuração matemática e garantias de blindagem do sistema pari-mutuel (A vs B)."""

    enabled: bool = Field(True, description="Define se o cálculo de retorno usa o sistema pari-mutuel.")
    options: List[Literal["A", "B"]] = Field(
        default=["A", "B"],
        min_length=2,
        max_length=2,
        description="Duas respostas possíveis por rodada: A e B.",
    )
    betting_protocol: Literal["simultaneous_blind", "open_sequential", "hybrid"] = Field(
        "simultaneous_blind",
        description="Protocolo de apostas: simultâneas/fechadas ao sinal do professor para evitar efeito manada.",
    )
    house_cut: float = Field(
        0.10,
        ge=0.0,
        le=0.50,
        description="Percentual alvo da casa c (ex.: 0.10 = 10%, recomendado entre 5% e 15%).",
    )
    recommended_house_cut_min: float = Field(
        0.05, ge=0.0, le=1.0, description="Limite inferior recomendado para o percentual da casa (5%)."
    )
    recommended_house_cut_max: float = Field(
        0.15, ge=0.0, le=1.0, description="Limite superior recomendado para o percentual da casa (15%)."
    )
    min_winning_odd: float = Field(
        1.00,
        ge=1.00,
        description="Piso de odd vencedora (O >= 1.00x): a casa só retém taxa a partir dos tokens dos perdedores.",
    )
    zero_winners_policy: Literal["rollover_pool", "house_takes_all"] = Field(
        "rollover_pool",
        description="Se ninguém acertar (T_certa = 0), a casa retém c * T e o Pool Líquido P acumula para a próxima rodada.",
    )
    breakage_unit: int = Field(
        50,
        gt=0,
        description="Unidade mínima de cédula para truncamento para baixo dos pagamentos (50 Tokens). A sobra fica com a Casa.",
    )
    denominations: List[int] = Field(
        default=[50, 100, 500],
        description="Denominações físicas de cédulas de Tokens disponíveis no jogo.",
    )
    loser_loss_fraction: float = Field(
        1.0,
        ge=1.0,
        le=1.0,
        description="Quem perde a aposta perde 100% dos tokens apostados (1.0).",
    )
    self_sustaining_house: bool = Field(
        True,
        description="O sistema é auto-sustentável: a casa nunca tira tokens do próprio bolso.",
    )

    @model_validator(mode="after")
    def _validate_options(self) -> "PariMutuelRules":
        if list(self.options) != ["A", "B"]:
            raise ValueError("As opções do sistema pari-mutuel devem ser exatamente ['A', 'B'].")
        if self.recommended_house_cut_min > self.recommended_house_cut_max:
            raise ValueError("recommended_house_cut_min não pode ser maior que recommended_house_cut_max.")
        return self


class BiddingRules(BaseModel):
    min_bid: int = Field(..., ge=0, description="Aposta mínima em tokens (50 Tokens).")
    max_bid_phases_1_2: Optional[int] = Field(
        500, gt=0, description="Teto máximo de aposta por rodada nas Fases 1 e 2 (evita falência precoce na 1ª rodada)."
    )
    phase_3_all_in_allowed: bool = Field(
        True, description="Permite All-in (apostar até 100% da banca) na Fase 3 - Desafio Final."
    )
    bid_increment: int = Field(..., gt=0, description="Incremento mínimo da aposta em tokens (50 Tokens).")
    hit_multiplier: Optional[float] = Field(
        None, gt=0, description="Multiplicador fixo legado (opcional; no pari-mutuel a odd O = P / T_certa é dinâmica)."
    )
    miss_multiplier: float = Field(
        -1.0, le=0, description="Multiplicador em caso de erro (-1.0 significa perder 100% dos tokens apostados)."
    )
    pass_allowed: bool = Field(False, description="Define se é permitido passar a vez ou se todos apostam na rodada.")


class BonusRules(BaseModel):
    scientific_justification_bonus: int = Field(
        50,
        ge=0,
        description="Valor da Repescagem Científica (50 T$) para equipe zerada que explicar a resolução, pago apenas se o Caixa da Casa tiver saldo >= 50 T$.",
    )
    house_funded_rebuy_only: bool = Field(
        True,
        description="Garante que a repescagem científica só pode ser paga usando o lucro já acumulado no Caixa da Casa.",
    )
    steal_points: int = Field(
        0, ge=0, description="Bônus de roubo (0 no modo pari-mutuel simultâneo)."
    )


class BlockConfig(BaseModel):
    name: str = Field(..., description="Nome do bloco/fase.")
    difficulty_level: int = Field(..., ge=1, le=5, description="Nível de dificuldade das questões no bloco.")
    question_count: int = Field(..., gt=0, description="Número de questões no bloco.")
    max_bid: Optional[int] = Field(None, description="Teto máximo de aposta na fase (None = All-in liberado).")
    special_rules: Optional[str] = Field(None, description="Regras especiais aplicáveis a este bloco.")


class PariMutuelRoundResult(BaseModel):
    """Resultado calculado e auditado de uma rodada pari-mutuel blindada."""

    tokens_a: float = Field(..., ge=0, description="T_A: total de tokens apostados em A.")
    tokens_b: float = Field(..., ge=0, description="T_B: total de tokens apostados em B.")
    carryover_in: float = Field(0.0, ge=0, description="Pool acumulado trazido da rodada anterior (Rollover).")
    total_pool: float = Field(..., ge=0, description="T = T_A + T_B: total do pool bruto arrecadado na rodada.")
    house_cut: float = Field(..., ge=0, le=1, description="c: percentual alvo da casa.")
    house_take: float = Field(..., ge=0, description="Retenção base da casa na rodada (garantindo O >= 1.00x).")
    net_pool: float = Field(..., ge=0, description="P: pool líquido disponível para divisão (ou rollover).")
    odd_a: Optional[float] = Field(None, description="O_A = P / T_A (com piso >= 1.00x).")
    odd_b: Optional[float] = Field(None, description="O_B = P / T_B (com piso >= 1.00x).")
    correct_option: Optional[Literal["A", "B"]] = Field(None, description="Alternativa correta revelada.")
    winning_odd: Optional[float] = Field(None, description="Odd vencedora aplicada aos apostadores certos.")
    carryover_out: float = Field(
        0.0, ge=0, description="Pool acumulado transferido para a próxima rodada caso ninguém tenha acertado (T_certa = 0)."
    )


def calculate_pari_mutuel_round(
    tokens_a: float,
    tokens_b: float,
    house_cut: float = 0.10,
    correct_option: Optional[Literal["A", "B"]] = None,
    carryover_in: float = 0.0,
    enforce_min_odd_floor: bool = True,
    breakage_unit: int = 50,
) -> PariMutuelRoundResult:
    """
    Calcula o pool bruto (T), a retenção da casa, o pool líquido (P), as odds (O_A, O_B)
    e eventual rollover (carryover_out), garantindo:
    1. Piso O >= 1.00x quando enforce_min_odd_floor=True (a casa só retém taxa a partir dos tokens perdedores).
    2. Rollover automático para a próxima rodada se T_certa == 0.
    3. Risco ZERO de prejuízo para a mesa em 100% dos cenários.
    """
    if tokens_a < 0 or tokens_b < 0 or carryover_in < 0:
        raise ValueError("Os tokens apostados e o carryover não podem ser negativos.")
    if not (0.0 <= house_cut <= 0.50):
        raise ValueError("O percentual da casa (c) deve estar entre 0.0 e 0.50.")

    total_pool = float(tokens_a + tokens_b)
    target_house_take = round(total_pool * house_cut, 6)

    # Odds pré-revelação para A e B considerando a proteção de piso (O >= 1.00x)
    if enforce_min_odd_floor:
        take_if_a_wins = min(target_house_take, float(tokens_b))
        take_if_b_wins = min(target_house_take, float(tokens_a))
    else:
        take_if_a_wins = target_house_take
        take_if_b_wins = target_house_take

    net_pool_if_a = round(total_pool - take_if_a_wins + carryover_in, 6)
    net_pool_if_b = round(total_pool - take_if_b_wins + carryover_in, 6)

    odd_a = round(net_pool_if_a / tokens_a, 6) if tokens_a > 0 else None
    odd_b = round(net_pool_if_b / tokens_b, 6) if tokens_b > 0 else None

    # Se a alternativa correta já foi revelada, consolida house_take, net_pool e carryover_out
    carryover_out = 0.0
    winning_odd = None

    if correct_option == "A":
        if tokens_a == 0:
            # 100% da turma errou: Casa retém comissão (em múltiplos de breakage_unit se aplicável) e resto vai para Rollover
            house_take = float((int(target_house_take) // breakage_unit) * breakage_unit) if breakage_unit > 0 else target_house_take
            net_pool = round(total_pool - house_take + carryover_in, 6)
            carryover_out = net_pool
            winning_odd = None
        else:
            house_take = take_if_a_wins
            net_pool = net_pool_if_a
            winning_odd = odd_a
    elif correct_option == "B":
        if tokens_b == 0:
            house_take = float((int(target_house_take) // breakage_unit) * breakage_unit) if breakage_unit > 0 else target_house_take
            net_pool = round(total_pool - house_take + carryover_in, 6)
            carryover_out = net_pool
            winning_odd = None
        else:
            house_take = take_if_b_wins
            net_pool = net_pool_if_b
            winning_odd = odd_b
    else:
        house_take = target_house_take
        net_pool = round(total_pool - house_take + carryover_in, 6)

    return PariMutuelRoundResult(
        tokens_a=tokens_a,
        tokens_b=tokens_b,
        carryover_in=carryover_in,
        total_pool=total_pool,
        house_cut=house_cut,
        house_take=house_take,
        net_pool=net_pool,
        odd_a=odd_a,
        odd_b=odd_b,
        correct_option=correct_option,
        winning_odd=winning_odd,
        carryover_out=carryover_out,
    )


def calculate_player_payout(
    bet_tokens: float,
    winning_odd: Optional[float],
    bet_matches_correct: bool,
    breakage_unit: int = 50,
) -> int:
    """
    Retorna o pagamento físico em Tokens (valor original + lucro) truncado para baixo
    no múltiplo de `breakage_unit` (50 Tokens).
    Quem erra perde 100% dos tokens apostados (retorno = 0).
    """
    if bet_tokens < 0:
        raise ValueError("A aposta não pode ser negativa.")
    if not bet_matches_correct or winning_odd is None or bet_tokens == 0:
        return 0
    raw_payout = bet_tokens * winning_odd
    if breakage_unit <= 1:
        return int(math.floor(raw_payout + 1e-9))
    return int(math.floor((raw_payout + 1e-9) / breakage_unit) * breakage_unit)


def settle_round_payouts(
    bets_on_winner: List[int],
    tokens_loser: int,
    house_cut: float = 0.10,
    carryover_in: int = 0,
    breakage_unit: int = 50,
) -> dict:
    """
    Liquida uma rodada completa com lista de apostas vencedoras e retorna:
    - payouts individuais (em múltiplos de 50 Tokens)
    - total_paid (soma paga aos vencedores)
    - total_house_revenue (retenção base + breakage de arredondamento)
    - carryover_out (se não houver vencedores)
    Garante invariante: total_paid + total_house_revenue + carryover_out == total_pool + carryover_in.
    """
    tokens_winner = sum(bets_on_winner)
    res = calculate_pari_mutuel_round(
        tokens_a=tokens_winner,
        tokens_b=tokens_loser,
        house_cut=house_cut,
        correct_option="A",
        carryover_in=carryover_in,
        enforce_min_odd_floor=True,
        breakage_unit=breakage_unit,
    )
    total_available = int(tokens_winner + tokens_loser + carryover_in)
    if tokens_winner == 0:
        return {
            "payouts": [],
            "total_paid": 0,
            "house_base_take": int(res.house_take),
            "breakage": 0,
            "total_house_revenue": int(res.house_take),
            "carryover_out": int(res.carryover_out),
            "total_available": total_available,
        }

    payouts = [
        calculate_player_payout(b, res.winning_odd, bet_matches_correct=True, breakage_unit=breakage_unit)
        for b in bets_on_winner
    ]
    total_paid = sum(payouts)
    total_house_revenue = total_available - total_paid
    breakage = int(round(res.net_pool - total_paid))

    return {
        "payouts": payouts,
        "total_paid": total_paid,
        "house_base_take": int(round(res.house_take)),
        "breakage": breakage,
        "total_house_revenue": total_house_revenue,
        "carryover_out": 0,
        "total_available": total_available,
    }


class AuctionRules(BaseModel):
    version: int = Field(2, ge=1)
    currency_name: str = Field("Tokens", description="Nome da moeda tokenizada do jogo.")
    initial_budget: int = Field(..., gt=0, description="Saldo inicial de tokens de cada aluno/equipe.")
    pari_mutuel: PariMutuelRules = Field(
        default_factory=PariMutuelRules,
        description="Parâmetros oficiais do sistema de apostas pari-mutuel.",
    )
    bidding: BiddingRules
    bonuses: BonusRules
    blocks: List[BlockConfig] = Field(..., description="Blocos do jogo, em dificuldade crescente.")
    round_flow: List[str] = Field(
        default_factory=list,
        description="Fluxo resumido de uma rodada do sistema de apostas.",
    )
    tiebreaker: Literal["sudden_death", "highest_accuracy", "shared_victory"] = Field(
        ..., description="Método de desempate."
    )
