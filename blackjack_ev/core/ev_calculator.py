from functools import lru_cache
from typing import Tuple, Dict

from blackjack_ev.models.shoe import Shoe
from blackjack_ev.models.rules import Rules
from blackjack_ev.models.table import Table
from blackjack_ev.models.hand import Hand

class Engine:
    def __init__(self, table: Table):
        self.table = table

    # Shoe
    def reset_shoe(self, decks: int | None = None) -> None:
        pass

    def shoe_counts(self) -> dict[int, int]:
        return {}

    def shoe_percents(self) -> dict[int, float]:
        return {}

    # Kart Girişi (Oyuncu & Krupiye)
    def deal_card_to_player(self, seat: int, card: int, hand_idx: int | None = None) -> None:
        pass

    def deal_card_to_dealer_up(self, card: int) -> None:
        pass

    def deal_card_to_dealer_down(self, card: int) -> None:
        pass

    def deal_card_to_dealer(self, card: int, is_upcard: bool = False) -> None:
        self.table.deal_card_to_dealer(card, is_upcard)

    def dealer_draw(self, card: int) -> None:  # manuel çekiş
        pass

    # Sorgular
    def compute_ev(self, seat: int, hand_idx: int | None = None) -> dict:
        """Return: { 'H': ev_hit, 'S': ev_stand, 'SP': ev_split_or_None, 'best': 'H'|'S'|'SP' }"""
        player = self.table.get_player(seat)
        hand = player.get_active_hand()
        dealer_up_card = self.table.dealer_hand.cards[0] if self.table.dealer_hand.cards else None
        shoe_counts = self.table.shoe.get_counts()

        ev_stand = self._calculate_ev_stand(hand, dealer_up_card, shoe_counts)
        ev_hit = self._calculate_ev_hit(hand, dealer_up_card, shoe_counts)

        ev_split = None
        if player.can_split():
            ev_split = self._calculate_ev_split(hand, dealer_up_card, shoe_counts)

        return {'S': ev_stand, 'H': ev_hit, 'SP': ev_split}

    def _calculate_ev_split(self, hand, dealer_up_card, shoe_counts):
        split_card = hand.cards[0]
        total_cards = sum(shoe_counts)

        if total_cards < 2:
            return -1.0  # Not enough cards to split

        ev = 0.0
        for card1_value, count1 in enumerate(shoe_counts, 1):
            if count1 > 0:
                prob1 = count1 / total_cards
                new_shoe_counts1 = list(shoe_counts)
                new_shoe_counts1[card1_value - 1] -= 1
                total_cards1 = total_cards - 1

                for card2_value, count2 in enumerate(new_shoe_counts1, 1):
                    if count2 > 0:
                        prob2 = count2 / total_cards1
                        new_shoe_counts2 = list(new_shoe_counts1)
                        new_shoe_counts2[card2_value - 1] -= 1

                        hand1 = Hand((split_card, card1_value))
                        hand2 = Hand((split_card, card2_value))

                        if split_card == 1:  # Split Aces
                            ev1 = self._calculate_ev_stand(
                                hand1, dealer_up_card, tuple(new_shoe_counts2)
                            )
                            ev2 = self._calculate_ev_stand(
                                hand2, dealer_up_card, tuple(new_shoe_counts2)
                            )
                        else:
                            ev1 = max(
                                self._calculate_ev_stand(
                                    hand1, dealer_up_card, tuple(new_shoe_counts2)
                                ),
                                self._calculate_ev_hit(
                                    hand1, dealer_up_card, tuple(new_shoe_counts2)
                                ),
                            )
                            ev2 = max(
                                self._calculate_ev_stand(
                                    hand2, dealer_up_card, tuple(new_shoe_counts2)
                                ),
                                self._calculate_ev_hit(
                                    hand2, dealer_up_card, tuple(new_shoe_counts2)
                                ),
                            )
                        ev += prob1 * prob2 * (ev1 + ev2)
        return ev

    def _calculate_ev_hit(self, hand, dealer_up_card, shoe_counts):
        total_cards = sum(shoe_counts)
        if total_cards == 0:
            return -1.0

        ev = 0.0
        for card_value, count in enumerate(shoe_counts, 1):
            if count > 0:
                new_shoe_counts = list(shoe_counts)
                new_shoe_counts[card_value - 1] -= 1
                probability = count / total_cards

                new_hand = hand.add_card(card_value)
                if new_hand.total > 21:
                    ev -= probability
                else:
                    # TODO: Handle split after hit
                    ev_stand = self._calculate_ev_stand(
                        new_hand, dealer_up_card, tuple(new_shoe_counts)
                    )
                    ev_hit = self._calculate_ev_hit(
                        new_hand, dealer_up_card, tuple(new_shoe_counts)
                    )
                    ev += probability * max(ev_stand, ev_hit)
        return ev

    def _calculate_ev_stand(self, hand, dealer_up_card, shoe_counts) -> float:
        player_total = hand.total
        if player_total > 21:
            return -1.0

        # Check for natural Blackjack
        is_player_blackjack = (len(hand.cards) == 2 and player_total == 21)

        dealer_distribution = self._get_dealer_distribution(
            dealer_up_card, shoe_counts, self.table.rules
        )

        ev = 0.0
        for dealer_total, probability in dealer_distribution.items():
            # Dealer busts
            if dealer_total > 21:
                if is_player_blackjack:
                    ev += probability * self.table.rules.bj_payout  # Player Blackjack wins 3:2
                else:
                    ev += probability * 1.0  # Player wins 1:1
            # Player Blackjack vs Dealer non-Blackjack
            elif is_player_blackjack and dealer_total != 21:
                ev += probability * self.table.rules.bj_payout
            # Player wins (higher score)
            elif player_total > dealer_total:
                ev += probability * 1.0
            # Player loses (lower score)
            elif player_total < dealer_total:
                ev -= probability * 1.0
            # Push (scores are equal)
            else:
                ev += probability * 0.0  # Push
        return ev

    @lru_cache(maxsize=None)
    def _get_dealer_distribution(
        self, dealer_up_card: int | None, shoe_counts: Tuple[int, ...], rules: Rules
    ) -> Dict[int, float]:
        if dealer_up_card is None:
            return {}

        memo = {}

        def _get_dealer_distribution_recursive(
            current_hand: Tuple[int, ...], current_shoe_counts: Tuple[int, ...]
        ) -> Dict[int, float]:
            state = (current_hand, current_shoe_counts)
            if state in memo:
                return memo[state]

            total = sum(current_hand)
            num_aces = current_hand.count(1)

            # Adjust for soft aces
            while total < 12 and num_aces > 0:
                total += 10
                num_aces -= 1

            if total > 21:
                return {22: 1.0}  # Bust

            # Dealer stands on 17 or more, or soft 17 if rules.s17 is True
            if total >= 17:
                if total == 17 and current_hand.count(1) > 0 and not rules.s17: # Soft 17 and H17 rule
                    pass # Dealer hits
                else:
                    return {total: 1.0}

            total_cards_in_shoe = sum(current_shoe_counts)
            if total_cards_in_shoe == 0:
                return {total: 1.0} # Should not happen if logic is correct, but as a safeguard

            distribution = {i: 0.0 for i in range(17, 23)}

            for card_value, count in enumerate(current_shoe_counts, 1):
                if count > 0:
                    new_shoe_counts = list(current_shoe_counts)
                    new_shoe_counts[card_value - 1] -= 1
                    probability = count / total_cards_in_shoe
                    
                    sub_distribution = _get_dealer_distribution_recursive(
                        current_hand + (card_value,),
                        tuple(new_shoe_counts),
                    )
                    for score, prob in sub_distribution.items():
                        distribution[score] += probability * prob

            memo[state] = distribution
            return distribution

        # Initial call to the recursive function
        # The shoe_counts already reflect the shoe after player cards and dealer upcard
        return _get_dealer_distribution_recursive((dealer_up_card,), shoe_counts)

    def end_hand(self) -> dict:
        results = {}
        dealer_total = self.table.dealer_hand.total
        for i, player in enumerate(self.table.players):
            player_total = player.get_active_hand().total
            if player_total > 21:
                results[i] = -1.0
            elif dealer_total > 21:
                results[i] = 1.0
            elif player_total > dealer_total:
                results[i] = 1.0
            elif player_total < dealer_total:
                results[i] = -1.0
            else:
                results[i] = 0.0
        return results
