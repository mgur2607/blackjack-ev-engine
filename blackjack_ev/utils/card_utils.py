def card_to_name(card: int) -> str:
    if card == 1:
        return "A"
    elif card == 11:
        return "J"
    elif card == 12:
        return "Q"
    elif card == 13:
        return "K"
    else:
        return str(card)

def name_to_card(name: str) -> int:
    if name.upper() == "A":
        return 1
    elif name.upper() == "J" or name.upper() == "Q" or name.upper() == "K":
        return 10
    else:
        return int(name)
