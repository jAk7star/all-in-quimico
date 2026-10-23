import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))
from mechanics_models import (  # noqa: E402
    calculate_pari_mutuel_round,
    calculate_player_payout,
    settle_round_payouts,
)
from validate_rules import load_rules, validate_rules  # noqa: E402

ROOT = Path(__file__).parent.parent


def test_base_rules_are_valid():
    rules_path = ROOT / "rules" / "base_rules.yaml"
    data = load_rules(rules_path)
    rules = validate_rules(data)
    assert rules.currency_name == "Tokens"
    assert rules.initial_budget == 1000
    assert rules.pari_mutuel.enabled is True
    assert rules.pari_mutuel.options == ["A", "B"]
    assert rules.pari_mutuel.betting_protocol == "simultaneous_blind"
    assert rules.pari_mutuel.min_winning_odd == pytest.approx(1.00)
    assert rules.pari_mutuel.zero_winners_policy == "rollover_pool"
    assert rules.pari_mutuel.breakage_unit == 50
    assert rules.bidding.max_bid_phases_1_2 == 500
    assert rules.bonuses.house_funded_rebuy_only is True
    assert len(rules.blocks) == 3
    assert len(rules.round_flow) == 8


def test_pari_mutuel_scenario_1_majority_wrong():
    """Cenário 1 – Maioria erra: A maioria dos tokens vai para a resposta errada (B), odd correta (A) fica alta."""
    # T_A = 200 tokens, T_B = 800 tokens -> T = 1000, c = 10% -> P = 900
    res = calculate_pari_mutuel_round(tokens_a=200, tokens_b=800, house_cut=0.10, correct_option="A")
    assert res.total_pool == pytest.approx(1000.0)
    assert res.house_take == pytest.approx(100.0)
    assert res.net_pool == pytest.approx(900.0)
    assert res.odd_a == pytest.approx(4.5)  # 900 / 200 = 4.5x (odd alta)
    assert res.winning_odd == pytest.approx(4.5)

    p1 = calculate_player_payout(100, res.winning_odd, bet_matches_correct=True, breakage_unit=50)
    p2 = calculate_player_payout(100, res.winning_odd, bet_matches_correct=True, breakage_unit=50)
    loser = calculate_player_payout(800, res.winning_odd, bet_matches_correct=False, breakage_unit=50)
    assert p1 == 450
    assert p2 == 450
    assert p1 + p2 == pytest.approx(res.net_pool)
    assert loser == 0


def test_pari_mutuel_scenario_2_majority_right():
    """Cenário 2 – Maioria acerta: A maioria dos tokens vai para a resposta correta (A), odd fica baixa."""
    res = calculate_pari_mutuel_round(tokens_a=750, tokens_b=250, house_cut=0.10, correct_option="A")
    assert res.odd_a == pytest.approx(1.2)  # 900 / 750 = 1.2x
    assert res.winning_odd == pytest.approx(1.2)


def test_unanimity_floor_protection_prevents_winner_loss():
    """Garante que se >90% ou 100% da sala acertar, O >= 1.00x e a Casa nunca fica no prejuízo."""
    # 100% da sala aposta em A (T_A = 1000, T_B = 0) e A está correta
    res = calculate_pari_mutuel_round(tokens_a=1000, tokens_b=0, house_cut=0.10, correct_option="A")
    assert res.house_take == 0.0
    assert res.net_pool == 1000.0
    assert res.winning_odd == pytest.approx(1.00)
    assert calculate_player_payout(200, res.winning_odd, True, breakage_unit=50) == 200


def test_zero_winners_rollover_jackpot():
    """Se 100% da turma errar (T_certa = 0), a Casa retém 10% e os 90% acumulam em Rollover para a próxima rodada."""
    r1 = calculate_pari_mutuel_round(tokens_a=0, tokens_b=1000, house_cut=0.10, correct_option="A")
    assert r1.house_take == 100.0
    assert r1.carryover_out == 900.0
    assert r1.winning_odd is None

    # Na próxima rodada, T_A = 300, T_B = 300 (T = 600, Casa = 60, Líquido da rodada = 540 + 900 de rollover = 1440)
    r2 = calculate_pari_mutuel_round(
        tokens_a=300, tokens_b=300, house_cut=0.10, correct_option="A", carryover_in=r1.carryover_out
    )
    assert r2.house_take == 60.0
    assert r2.net_pool == 1440.0
    assert r2.winning_odd == pytest.approx(4.8)  # 1440 / 300 = 4.8x!


def test_breakage_50_tokens_guarantees_zero_house_loss_exhaustively():
    """
    Prova exaustiva em dezenas de combinações de apostas em múltiplos de 50 T$:
    1) A Casa NUNCA tem prejuízo (total_house_revenue >= 0).
    2) Todo pagamento é múltiplo exato de 50 T$.
    3) Nenhum vencedor recebe menos do que apostou (payout >= bet).
    """
    possible_team_bets = [
        [50],
        [100, 100, 100],
        [50, 150, 250],
        [100, 200, 300, 400],
        [50, 50, 50, 50, 50],
        [500, 500],
    ]
    for bets_win in possible_team_bets:
        for loser_total in [0, 50, 100, 150, 250, 400, 800]:
            for carry in [0, 150, 450]:
                settlement = settle_round_payouts(
                    bets_on_winner=bets_win,
                    tokens_loser=loser_total,
                    house_cut=0.10,
                    carryover_in=carry,
                    breakage_unit=50,
                )
                assert settlement["total_house_revenue"] >= 0
                assert settlement["breakage"] >= 0
                assert settlement["total_paid"] <= settlement["total_available"]
                for b, p in zip(bets_win, settlement["payouts"]):
                    assert p % 50 == 0
                    assert p >= b


def test_invalid_bidding_rules():
    data = load_rules(ROOT / "rules" / "base_rules.yaml")
    data["bidding"]["min_bid"] = -10
    with pytest.raises(ValidationError):
        validate_rules(data)


def test_invalid_house_cut():
    data = load_rules(ROOT / "rules" / "base_rules.yaml")
    data["pari_mutuel"]["house_cut"] = 0.85
    with pytest.raises(ValidationError):
        validate_rules(data)


def test_training_round_alfa_beta_gama_no_commission():
    """Valida a Rodada-Treino oficial (Alfa=200 em A, Beta=100 em B, Gama=150 em B; B correta; c=0%)."""
    settlement = settle_round_payouts(
        bets_on_winner=[100, 150],
        tokens_loser=200,
        house_cut=0.0,
        carryover_in=0,
        breakage_unit=50,
    )
    assert settlement["total_available"] == 450
    assert settlement["payouts"] == [150, 250]
    assert settlement["total_paid"] == 400
    assert settlement["house_base_take"] == 0
    assert settlement["breakage"] == 50
    assert settlement["total_house_revenue"] == 50


def test_invalid_difficulty_level():
    data = load_rules(ROOT / "rules" / "base_rules.yaml")
    data["blocks"][0]["difficulty_level"] = 6
    with pytest.raises(ValidationError):
        validate_rules(data)
