from __future__ import annotations
from functools import lru_cache
from typing import Tuple, Dict, Optional

from blackjack_ev.models.shoe import Shoe
from blackjack_ev.models.rules import Rules
from blackjack_ev.models.table import Table
from blackjack_ev.models.hand import Hand


# ---------------------------
# Yardımcılar
# ---------------------------
def _eval_total_and_soft(cards: Tuple[int, ...]) -> Tuple[int, bool]:
    total = sum(cards)
    aces = cards.count(1)
    soft = False
    while aces > 0 and total + 10 <= 21:
        total += 10
        aces -= 1
        soft = True
    return total, soft

def _is_blackjack(cards: Tuple[int, ...]) -> bool:
    t, _ = _eval_total_and_soft(cards)
    return (len(cards) == 2) and (t == 21)

def _p_dealer_blackjack(dealer_up: Optional[int], shoe: Tuple[int, ...]) -> float:
    """Up=A → hole=10; Up=10 → hole=A. (Shoe, upcard çıktıktan sonraki durum.)"""
    if dealer_up is None:
        return 0.0
    total = sum(shoe)
    if total <= 0:
        return 0.0
    if dealer_up == 1:
        tens = shoe[9]
        return tens / total
    if dealer_up == 10:
        aces = shoe[0]
        return aces / total
    return 0.0

# ---------------------------
# Dealer dağılımı (koşullu; cache'li)
# ---------------------------
@lru_cache(maxsize=None)
def _dealer_distribution_cached(
    dealer_up: int,
    shoe: Tuple[int, ...],
    s17: bool,
    forbid_bj_hole: bool,  # True: up=A için hole=10; up=10 için hole=A yasak
) -> Dict[int, float]:
    """
    Dönüş: {17: p, 18: p, 19: p, 20: p, 21: p, 22: p(bust)}
    """
    memo: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], Dict[int, float]] = {}

    def rec(curr: Tuple[int, ...], shoe_now: Tuple[int, ...]) -> Dict[int, float]:
        key = (curr, shoe_now)
        if key in memo:
            return memo[key]

        total, soft = _eval_total_and_soft(curr)
        if total > 21:
            memo[key] = {22: 1.0}
            return memo[key]

        if total >= 17:
            if total == 17 and soft and not s17:
                # H17: soft 17'de çekmeye devam
                pass
            else:
                memo[key] = {total: 1.0}
                return memo[key]

        remaining = sum(shoe_now)
        if remaining == 0:
            memo[key] = {total: 1.0}
            return memo[key]

        dist = {17: 0.0, 18: 0.0, 19: 0.0, 20: 0.0, 21: 0.0, 22: 0.0}

        for v, cnt in enumerate(shoe_now, 1):
            if cnt <= 0:
                continue

            # İlk hole çekiminde dealer BJ kombinasyonunu yasakla (koşullu dağılım)
            if forbid_bj_hole and len(curr) == 1:
                if (dealer_up == 1 and v == 10) or (dealer_up == 10 and v == 1):
                    continue

            p = cnt / remaining
            new_shoe = list(shoe_now)
            new_shoe[v - 1] -= 1
            sub = rec(curr + (v,), tuple(new_shoe))
            for k, q in sub.items():
                dist[k] += p * q

        memo[key] = dist
        return dist

    return rec((dealer_up,), shoe)

# ---------------------------
# EV(stand/hit) — cache'li çekirdekler
# ---------------------------
@lru_cache(maxsize=None)
def _ev_stand_cached(
    player_cards: Tuple[int, ...],
    dealer_up: Optional[int],
    shoe: Tuple[int, ...],
    bj_eligible: bool,
    s17: bool,
    bj_payout: float,
) -> float:
    total, _ = _eval_total_and_soft(player_cards)
    if total > 21:
        return -1.0

    # Oyuncu doğal 21 ise: EV = bj_payout * (1 - P(dealer BJ))
    if bj_eligible and _is_blackjack(player_cards):
        pd = _p_dealer_blackjack(dealer_up, shoe)
        return bj_payout * (1.0 - pd)

    # Oyuncu doğal değilse: EV = -P(dealer BJ) + EV(dealer BJ değil koşullu)
    p_dbj = _p_dealer_blackjack(dealer_up, shoe)
    ev = -p_dbj

    if dealer_up is None:
        return ev

    dist = _dealer_distribution_cached(
        dealer_up, shoe, s17, forbid_bj_hole=(p_dbj > 0.0)
    )

    for dealer_total, p in dist.items():
        if dealer_total == 22:
            ev += p * 1.0
        elif total > dealer_total:
            ev += p * 1.0
        elif total < dealer_total:
            ev -= p * 1.0
        else:
            # push
            pass
    return ev

@lru_cache(maxsize=None)
def _ev_hit_cached(
    player_cards: Tuple[int, ...],
    dealer_up: Optional[int],
    shoe: Tuple[int, ...],
    bj_eligible: bool,
    s17: bool,
    bj_payout: float,
) -> float:
    remaining = sum(shoe)
    if remaining == 0:
        return -1.0

    ev = 0.0
    for v, cnt in enumerate(shoe, 1):
        if cnt <= 0:
            continue
        p = cnt / remaining
        new_shoe = list(shoe)
        new_shoe[v - 1] -= 1
        new_cards = player_cards + (v,)

        t, _ = _eval_total_and_soft(new_cards)
        if t > 21:
            ev -= p  # bust
            continue

        ev_s = _ev_stand_cached(new_cards, dealer_up, tuple(new_shoe), bj_eligible, s17, bj_payout)
        ev_h = _ev_hit_cached  (new_cards, dealer_up, tuple(new_shoe), bj_eligible, s17, bj_payout)
        ev += p * (ev_s if ev_s >= ev_h else ev_h)
    return ev


# ===========================
# Engine
# ===========================
class Engine:
    def __init__(self, table: Table):
        self.table = table

    # Shoe (passthrough; Table/Shoe API'ne göre)
    def reset_shoe(self, decks: int | None = None) -> None:
        if decks is None:
            try:
                self.table.reset_shoe()
            except TypeError:
                # bazı sürümlerde parametre zorunlu olabilir
                self.table.reset_shoe(8)
        else:
            self.table.reset_shoe(decks)

    def shoe_counts(self) -> dict[int, int]:
        counts = tuple(self.table.shoe.get_counts())
        return {i + 1: c for i, c in enumerate(counts)}

    def shoe_percents(self) -> dict[int, float]:
        counts = tuple(self.table.shoe.get_counts())
        total = sum(counts)
        return {i + 1: (counts[i] / total if total else 0.0) for i in range(10)}

    # Kart Girişi (Oyuncu & Krupiye)
    def deal_card_to_player(self, seat: int, card: int, hand_idx: int | None = None) -> None:
        self.table.deal_card_to_player(seat, card, hand_idx)

    def deal_card_to_dealer_up(self, card: int) -> None:
        self.table.deal_card_to_dealer(card, is_upcard=True)

    def deal_card_to_dealer_down(self, card: int) -> None:
        self.table.deal_card_to_dealer(card, is_upcard=False)

    def deal_card_to_dealer(self, card: int, is_upcard: bool = False) -> None:
        self.table.deal_card_to_dealer(card, is_upcard)

    def dealer_draw(self, card: int) -> None:  # manuel çekiş
        self.table.dealer_draw(card)

    # Sorgular
    def compute_ev(self, seat: int, hand_idx: int | None = None) -> dict:
        """
        Return ONLY: { 'S': ev_stand, 'H': ev_hit, 'SP': ev_split_or_None }
        (UI 'best' ve diğerlerini kendisi hesaplayacak.)
        Tüm değerler **birim bet başına** raporlanır. (Split EV zaten /2 normalize.)
        """
        player = self.table.get_player(seat)
        idx = hand_idx if hand_idx is not None else player.active_hand_idx
        hand: Hand = player.hands[idx]

        dealer_up_card = self.table.dealer_hand.cards[0] if self.table.dealer_hand.cards else None
        cards = tuple(hand.cards)

        # Oynanabilir state yoksa EV hesaplama (ilk açılışta gereksiz EV'leri engeller)
        if dealer_up_card is None or len(cards) < 2:
            return {'S': None, 'H': None, 'SP': None}

        shoe_counts = tuple(self.table.shoe.get_counts())
        rules: Rules = self.table.rules
        s17 = bool(getattr(rules, "s17", True))
        bj_payout = float(getattr(rules, "bj_payout", 1.5))

        # Split sonrası ele gelen 21, BJ sayılmaz.
        is_bj_eligible = not player.has_split

        ev_stand = _ev_stand_cached(cards, dealer_up_card, shoe_counts, is_bj_eligible, s17, bj_payout)
        ev_hit = _ev_hit_cached(cards, dealer_up_card, shoe_counts, is_bj_eligible, s17, bj_payout)

        ev_split = None
        if player.can_split() and getattr(rules, "allow_split", True):
            ev_split = self._calculate_ev_split(hand, dealer_up_card, shoe_counts, s17, bj_payout)

        return {'S': ev_stand, 'H': ev_hit, 'SP': ev_split}

    # ---- Split EV (birim bet; /2 normalize) ----
    def _calculate_ev_split(
        self,
        hand: Hand,
        dealer_up_card: Optional[int],
        shoe_counts: Tuple[int, ...],
        s17: bool,
        bj_payout: float,
    ) -> float:
        split_card = hand.cards[0]
        total_cards = sum(shoe_counts)
        if total_cards < 2:
            return -1.0

        ev_sum = 0.0

        for c1, n1 in enumerate(shoe_counts, 1):
            if n1 <= 0:
                continue
            p1 = n1 / total_cards
            shoe1 = list(shoe_counts)
            shoe1[c1 - 1] -= 1
            total1 = total_cards - 1

            for c2, n2 in enumerate(shoe1, 1):
                if n2 <= 0:
                    continue
                p2 = n2 / total1
                shoe2 = list(shoe1)
                shoe2[c2 - 1] -= 1
                shoe2_t = tuple(shoe2)

                h1 = (split_card, c1)
                h2 = (split_card, c2)

                if split_card == 1:
                    # A-A: tek kart ve stand; splitten gelen 2-kart 21 **BJ sayılmaz**
                    ev1 = _ev_stand_cached(h1, dealer_up_card, shoe2_t, False, s17, bj_payout)
                    ev2 = _ev_stand_cached(h2, dealer_up_card, shoe2_t, False, s17, bj_payout)
                else:
                    ev1s = _ev_stand_cached(h1, dealer_up_card, shoe2_t, False, s17, bj_payout)
                    ev1h = _ev_hit_cached  (h1, dealer_up_card, shoe2_t, False, s17, bj_payout)
                    ev1  = ev1s if ev1s >= ev1h else ev1h

                    ev2s = _ev_stand_cached(h2, dealer_up_card, shoe2_t, False, s17, bj_payout)
                    ev2h = _ev_hit_cached  (h2, dealer_up_card, shoe2_t, False, s17, bj_payout)
                    ev2  = ev2s if ev2s >= ev2h else ev2h

                ev_sum += p1 * p2 * (ev1 + ev2)

        return ev_sum / 2.0  # birim bet
