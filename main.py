import random
from typing import List, Dict, Tuple

# Constants
SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
MAX_BET = 100  # Maximum bet amount

# Card and Player classes (from eldritch.py)
class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank} of {self.suit}"

    def __repr__(self):
        return self.__str__()

class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand: List[Card] = []
        self.active = True
        self.insanity = 0  # Added insanity level

    def receive_cards(self, cards: List[Card]):
        if self.active:
            self.hand.extend(cards)

    def show_hand(self) -> List[Card]:
        return self.hand if self.active else []

    def fold(self):
        self.active = False

    def gain_insanity(self, amount: int):
        self.insanity += amount
        print(f"{self.name} gains {amount} insanity. Current insanity: {self.insanity}")

# Eldritch functions (from eldritch.py)
def cause_insanity(player: Player, money: int) -> None:
    """
    Causes a player to gain insanity. The amount of insanity is random,
    influenced by the player's remaining money. The less money a player has,
    the more severe the potential insanity.

    Args:
        player: The Player object to affect.
        money: The amount of money the player has.
    """
    # Define the base insanity amount (between 1 and 3)
    base_insanity = random.randint(1, 3)

    # Adjust insanity based on money. The multiplier increases as money decreases.
    if money > 1000:
        insanity_multiplier = 1.0  # No change
    elif 500 <= money <= 1000:
        insanity_multiplier = 1.2  # Slightly increased insanity
    elif 200 <= money < 500:
        insanity_multiplier = 1.5  # Moderately increased insanity
    elif 100 <= money < 200:
        insanity_multiplier = 2.0  # Significantly increased insanity
    else:  # money < 100
        insanity_multiplier = 3.0  # Extremely increased insanity (closer to madness)

    # Calculate the final insanity amount
    insanity_amount = int(base_insanity * insanity_multiplier)

    player.gain_insanity(insanity_amount)

# Game classes
class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num: int = 1) -> List[Card]:
        return [self.cards.pop() for _ in range(num)]

class Table:
    def __init__(self):
        self.community_cards: List[Card] = []

    def deal_flop(self, deck: Deck):
        self.community_cards.extend(deck.deal(3))

    def deal_turn(self, deck: Deck):
        self.community_cards.extend(deck.deal(1))

    def deal_river(self, deck: Deck):
        self.community_cards.extend(deck.deal(1))

    def show_community_cards(self) -> List[Card]:
        return self.community_cards

class Money:
    def __init__(self, initial_balances: Dict[str, int] = None):
        if initial_balances is None:
            self.balances = {"Player": 1000, "NPC 1": 1000, "NPC 2": 1000, "NPC 3": 1000, "NPC 4": 1000}
        else:
            self.balances = initial_balances
        self.pot = 0

    def bet(self, name: str, amount: int) -> bool:
        if self.balances.get(name, 0) >= amount:
            self.balances[name] -= amount
            self.pot += amount
            return True
        return False

    def get_balance(self, name: str) -> int:
        return self.balances.get(name, 0)

    def show_balances(self):
        return self.balances

    def show_pot(self) -> int:
        return self.pot

    def reset_pot(self):
        self.pot = 0

    def award_pot(self, winner: str):
        self.balances[winner] += self.pot
        self.reset_pot()

    def get_all_balances(self) -> Dict[str, int]:
        return self.balances

class Fold:
    def __init__(self):
        self.folded_players: List[str] = []

    def fold_player(self, player: Player):
        player.fold()
        self.folded_players.append(player.name)

    def has_folded(self, name: str) -> bool:
        return name in self.folded_players

class NPCs:
    def __init__(self, insanity_levels: Dict[str, int] = None):
        self.npc_list: List[Player] = [Player(f"NPC {i+1}") for i in range(4)]
        if insanity_levels:
            for npc in self.npc_list:
                npc.insanity = insanity_levels.get(npc.name, 0)

    def deal_to_npcs(self, deck: Deck):
        for npc in self.npc_list:
            npc.receive_cards(deck.deal(2))

    def show_npc_hands(self) -> dict:
        return {npc.name: npc.show_hand() for npc in self.npc_list}

    def take_turns(self, money: Money, stage: str, max_bet: int, fold: Fold, community_cards: List[Card]):
        bets = {}
        for npc in self.npc_list:
            if not npc.active:
                continue
            hand_strength = self.evaluate_hand(npc.hand + community_cards)
            decision = self.make_decision(hand_strength, max_bet, money.get_balance(npc.name), stage, npc.insanity)
            if decision == 'fold':
                fold.fold_player(npc)
                print(f"{npc.name} folds.")
                continue
            bet_amount = self.calculate_bet_amount(hand_strength, max_bet, money.get_balance(npc.name), npc.insanity)
            if bet_amount > 0 and money.bet(npc.name, bet_amount):
                bets[npc.name] = bet_amount
                if random.random() < 0.2:  # 20% chance to cause insanity
                    cause_insanity(npc, money.get_balance(npc.name))  # Call the function
        return bets

    def make_decision(self, hand_strength: int, max_bet: int, balance: int, stage: str, insanity: int) -> str:
        if insanity > 5:
            if random.random() < 0.5:
                return 'fold'
            elif random.random() >= 0.5:
                return 'bet'  # they might bet even with a bad hand
        if hand_strength < 3 and max_bet > 0 and random.random() < 0.2:
            return 'fold'
        elif hand_strength > 5 and random.random() < 0.2:
            return 'bet'
        elif hand_strength > 7 and random.random() < 0.5:
            return 'bet'
        elif max_bet > 0 and balance < max_bet:
            return 'fold'
        else:
            return 'bet'

    def calculate_bet_amount(self, hand_strength: int, max_bet: int, balance: int, insanity: int) -> int:
        if insanity > 5:
            if random.random() < 0.5:
                return min(balance, MAX_BET * 2)  # npcs can bet a lot more if insane
            else:
                return 0
        if hand_strength > 7:
            return min(balance, min(max_bet + random.randint(10, 50), MAX_BET))
        elif hand_strength > 5:
            return min(balance, min(max_bet + random.randint(5, 25), MAX_BET))
        else:
            return min(balance, min(max_bet, MAX_BET))

    def evaluate_hand(self, cards: List[Card]) -> int:
        ranks = [RANK_VALUES[card.rank] for card in cards]
        suits = [card.suit for card in cards]
        ranks.sort()

        if self.is_royal_flush(cards): return 10
        if self.is_straight_flush(cards): return 9
        if self.is_four_of_a_kind(ranks): return 8
        if self.is_full_house(ranks): return 7
        if self.is_flush(suits): return 6
        if self.is_straight(ranks): return 5
        if self.is_three_of_a_kind(ranks): return 4
        if self.is_two_pair(ranks): return 3
        if self.is_pair(ranks): return 2
        return 1

    # ... (rest of the hand evaluation functions)
    def is_royal_flush(self, cards: List[Card]) -> bool:
        straight_flush = self.is_straight_flush(cards)
        royal = [card.rank in ['10', 'J', 'Q', 'K', 'A'] for card in cards].count(True) == 5
        return straight_flush and royal

    def is_straight_flush(self, cards: List[Card]) -> bool:
        return self.is_flush([card.suit for card in cards]) and self.is_straight([RANK_VALUES[card.rank] for card in cards])

    def is_four_of_a_kind(self, ranks: List[int]) -> bool:
        return any(ranks.count(rank) == 4 for rank in ranks)

    def is_full_house(self, ranks: List[int]) -> bool:
        return self.is_three_of_a_kind(ranks) and self.is_pair(ranks)

    def is_flush(self, suits: List[str]) -> bool:
        return len(set(suits)) == 1

    def is_straight(self, ranks: List[int]) -> bool:
        if len(set(ranks)) < 5: return False
        ranks = sorted(list(set(ranks)))
        if ranks == [2, 3, 4, 5, 14]: return True
        for i in range(len(ranks) - 4):
            if ranks[i+4] - ranks[i] == 4: return True
        return False

    def is_three_of_a_kind(self, ranks: List[int]) -> bool:
        return any(ranks.count(rank) == 3 for rank in ranks)

    def is_two_pair(self, ranks: List[int]) -> bool:
        pairs = 0
        used = []
        for rank in ranks:
            if ranks.count(rank) == 2 and rank not in used:
                pairs += 1
                used.append(rank)
        return pairs == 2

    def is_pair(self, ranks: List[int]) -> bool:
        return any(ranks.count(rank) == 2 for rank in ranks)

    def get_hand_name(self, hand_strength: int) -> str:
        if hand_strength == 10:
            return "Royal Flush"
        elif hand_strength == 9:
            return "Straight Flush"
        elif hand_strength == 8:
            return "Four of a Kind"
        elif hand_strength == 7:
            return "Full House"
        elif hand_strength == 6:
            return "Flush"
        elif hand_strength == 5:
            return "Straight"
        elif hand_strength == 4:
            return "Three of a Kind"
        elif hand_strength == 3:
            return "Two Pair"
        elif hand_strength == 2:
            return "Pair"
        else:
            return "High Card"

class WinCondition:
    def __init__(self, player: Player, npcs: NPCs, fold: Fold, money: Money, community_cards: List[Card]):
        self.player = player
        self.npcs = npcs
        self.fold = fold
        self.money = money
        self.community_cards = community_cards

    def determine_winner(self) -> Tuple[str, str]:
        active_players = [self.player] + [npc for npc in self.npcs.npc_list if npc.active]
        active_players = [p for p in active_players if p.name not in self.fold.folded_players]

        if not active_players:
            return "No winner", "No hand"

        best_hand = None
        winner = None
        winning_hand_name = ""

        for player in active_players:
            hand_strength = self.npcs.evaluate_hand(player.hand + self.community_cards)
            if best_hand is None or hand_strength > best_hand:
                best_hand = hand_strength
                winner = player.name
                winning_hand_name = self.npcs.get_hand_name(hand_strength)

        self.money.award_pot(winner)
        return winner, winning_hand_name

class Events:
    def __init__(self, game: 'Game'):
        self.game = game

    def trigger_event(self):
        max_insanity = max(player.insanity for player in [self.game.player] + self.game.npcs.npc_list)
        if random.random() < (max_insanity / 100): # scaling chance based on max insanity, much rarer
            self.eldritch_interference()
        if random.random() < (max_insanity / 100):
            self.temporal_anomaly()
        if random.random() < (max_insanity / 100):
            self.card_mutation()
        if random.random() < (max_insanity / 100):
            self.shifting_sands()
        if random.random() < (max_insanity / 100):
            self.insanity_surge()

    def eldritch_interference(self):
        print("\n\x1B[3m\x1B[1mReality frays, and the community cards shift, replaced by new ones from the deck.\x1B[0m")
        self.game.table.community_cards = self.game.deck.deal(5)

    def temporal_anomaly(self):
        print("\n\x1B[3m\x1B[1mThe flow of time distorts; the last community card vanishes, then reappears as a different card.\x1B[0m")
        if self.game.table.community_cards:
            last_card_index = len(self.game.table.community_cards) - 1
            self.game.deck.cards.append(self.game.table.community_cards.pop(last_card_index))
            self.game.deck.shuffle()
            self.game.table.community_cards.append(self.game.deck.deal(1)[0])

    def card_mutation(self):
        print("\n\x1B[3m\x1B[1mA strange, oily aura surrounds one of the community cards, its rank and suit subtly altering.\x1B[0m")
        if self.game.table.community_cards:
            mutated_card_index = random.randint(0, len(self.game.table.community_cards) - 1)
            card = self.game.table.community_cards[mutated_card_index]
            card.rank = random.choice(RANKS)
            card.suit = random.choice(SUITS)

    def shifting_sands(self):
        print("\n\x1B[3m\x1B[1mThe table seems to ripple, and the pot is redistributed among the active players.\x1B[0m")
        active_players = [player for player in [self.game.player] + self.game.npcs.npc_list if player.active and player.name not in self.game.fold.folded_players]
        if active_players:
            split_pot = self.game.money.show_pot() // len(active_players)
            self.game.money.reset_pot()
            for player in active_players:
                self.game.money.balances[player.name] += split_pot

    def insanity_surge(self):
        print("\n\x1B[3m\x1B[1mA wave of madness washes over the room, and all players gain a random amount of insanity.\x1B[0m")
        players = [self.game.player] + self.game.npcs.npc_list
        for player in players:
            insanity_gain = random.randint(1, 5)
            player.gain_insanity(insanity_gain)

class Game:
    def __init__(self, initial_balances: Dict[str, int] = None, initial_insanity: Dict[str, int] = None):
        self.deck = Deck()
        self.table = Table()
        self.player = Player("Player")
        self.npcs = NPCs(initial_insanity)
        self.money = Money(initial_balances)  # Use the provided balances
        self.fold = Fold()
        self.game_tracker = Games()
        self.initial_balances = initial_balances
        self.initial_insanity = initial_insanity
        self.events = Events(self)

    def start_game(self):
        print("\n\"A rainbow is one of the most fantastic phenomena of our natural experience. It symbolizes our insignificance and our dreams of fulfillment. There can be gold at the end of our Rainbows.\"\n- Ronnie James Dio\n")
        input("Press Enter to begin the game...")

        while True:
            print(f"\n--- Starting Game {self.game_tracker.games_played + 1} ---")
            self.deck = Deck()  # reset deck and table.
            self.table = Table()
            self.player = Player("Player")
            self.npcs = NPCs({npc.name: npc.insanity for npc in self.npcs.npc_list}) # carry over insanity
            self.fold = Fold()
            self.game_tracker.games_played += 1

            self.deal_hole_cards()
            self.display_player_hands()

            if self.check_instant_win():
                if not self.game_tracker.play_again(self.money.get_all_balances(), {npc.name: npc.insanity for npc in self.npcs.npc_list}):
                    break
                continue

            self.betting_round("pre-flop")
            self.display_all_hands()  # show hands
            if self.check_instant_win():
                if not self.game_tracker.play_again(self.money.get_all_balances(), {npc.name: npc.insanity for npc in self.npcs.npc_list}):
                    break
                continue

            self.table.deal_flop(self.deck)
            self.display_community_cards("Flop")
            self.betting_round("flop")
            self.display_all_hands()  # show hands
            self.events.trigger_event() # trigger events after flop betting
            if self.check_instant_win():
                if not self.game_tracker.play_again(self.money.get_all_balances(), {npc.name: npc.insanity for npc in self.npcs.npc_list}):
                    break
                continue

            self.table.deal_turn(self.deck)
            self.display_community_cards("Turn")
            self.events.trigger_event() # trigger events after turn
            self.betting_round("turn")
            self.display_all_hands()  # show hands
            self.events.trigger_event() # trigger events after turn betting
            if self.check_instant_win():
                if not self.game_tracker.play_again(self.money.get_all_balances(), {npc.name: npc.insanity for npc in self.npcs.npc_list}):
                    break
                continue

            self.table.deal_river(self.deck)
            self.display_community_cards("River")
            self.events.trigger_event() # trigger events after river
            self.betting_round("river")
            self.display_all_hands()  # show hands

            print("\nFinal pot: $", self.money.show_pot())

            winner, winning_hand_name = WinCondition(self.player, self.npcs, self.fold, self.money, self.table.community_cards).determine_winner()
            print(f"\nWinner: {winner} with a {winning_hand_name}")
            if random.random() < 0.1:  # 10% chance of insanity
                cause_insanity(self.player, self.money.get_balance("Player"))  # Pass the players money

            if not self.game_tracker.play_again(self.money.get_all_balances(), {npc.name: npc.insanity for npc in self.npcs.npc_list}):
                break
    # ... (rest of the game functions)
    def check_instant_win(self) -> bool:
        active_npcs = [npc for npc in self.npcs.npc_list if npc.active]
        if self.player.active and not active_npcs:
            self.money.award_pot(self.player.name)
            print(f"All NPCs folded. Player win's the pot!")  # changed wins to win
            return True
        elif not self.player.active and len(active_npcs) == 1:
            self.money.award_pot(active_npcs[0].name)
            print(f"Only {active_npcs[0].name} remains. They win the pot!")
            return True
        return False

    def deal_hole_cards(self):
        self.player.receive_cards(self.deck.deal(2))
        self.npcs.deal_to_npcs(self.deck)

    def display_player_hands(self):
        if self.player.active:
            print(f"{self.player.name}'s Hand: {self.player.show_hand()}  Insanity: {self.player.insanity}")
        for name, hand in self.npcs.show_npc_hands().items():
            print(f"{name}'s Hand: {hand}  Insanity: {self.npcs.npc_list[int(name[-1])-1].insanity}")

    def display_all_hands(self):
        if self.player.active:
            print(f"{self.player.name}'s Hand: {self.player.show_hand()}  Insanity: {self.player.insanity}")
        for name, hand in self.npcs.show_npc_hands().items():
            print(f"{name}'s Hand: {hand}  Insanity: {self.npcs.npc_list[int(name[-1])-1].insanity}")

    def display_community_cards(self, stage: str):
        print(f"\n{stage} Community Cards: {self.table.show_community_cards()}")

    def betting_round(self, stage: str):
        print(f"\n--- {stage.capitalize()} Betting Round ---")

        max_bet = 0
        player_bet = 0
        if self.player.active:
            while True:  # Loop until a valid bet or fold
                try:
                    response = input(f"\nYour balance: ${self.money.get_balance('Player')}. Enter bet amount (max ${MAX_BET}) or 'fold': ")
                    if response.strip().lower() == 'fold':
                        self.fold.fold_player(self.player)
                        print("Player folded. Press Enter to continue.")
                        input()
                        return  # Return from betting round
                    else:
                        player_bet = int(response)
                        if player_bet > MAX_BET:
                            print(f"Bet exceeds the maximum of ${MAX_BET}. Please enter a valid bet.")
                            continue  # Go back to the beginning of the loop
                        if player_bet < 0:
                            print(f"Bet is below zero. Please enter a valid bet.")
                            continue  # Go back to the beginning of the loop
                        if self.money.bet("Player", player_bet):
                            print(f"Player bet ${player_bet}. Remaining balance: ${self.money.get_balance('Player')}")
                            max_bet = player_bet
                            break  # Exit the loop on a valid bet
                        else:
                            print("Insufficient funds. Player checks.")
                            player_bet = 0  # set player_bet to 0 to avoid issues with calling
                            break  # exit loop, player checks.
                except ValueError:
                    print("Invalid input. Please enter a valid number or 'fold'.")
                    # No continue, the loop will restart automatically
            if random.random() < 0.2:  # 20% chance to cause insanity
                cause_insanity(self.player, self.money.get_balance("Player"))  # pass the players money
        npc_bets = self.npcs.take_turns(self.money, stage, max_bet, self.fold, self.table.community_cards)
        for name, amount in npc_bets.items():
            print(f"{name} bets ${amount}. Remaining balance: ${self.money.get_balance(name)}")
            max_bet = max(max_bet, amount)

        if self.player.active:
            while True:
                try:
                    if self.money.get_balance("Player") >= max_bet and player_bet < max_bet:
                        response = input(
                            f"\nCurrent bet is ${max_bet}.  Your balance is ${self.money.get_balance('Player')}.  "
                            f"Call {max_bet - player_bet}, raise (max raise to ${MAX_BET}), or fold? (c/r/f) "
                        ).lower()
                        if response == 'c':
                            self.money.bet("Player", max_bet - player_bet)
                            print(f"Player call the bet of ${max_bet}. Your balance is now ${self.money.get_balance('Player')}")
                            break
                        elif response == 'r':
                            raise_amount = int(input("Enter raise amount: "))
                            if raise_amount > MAX_BET:
                                print(f"Raise amount exceeds the maximum of ${MAX_BET}. Please enter a valid raise.")
                                continue  # restart the loop
                            if self.money.bet("Player", max_bet - player_bet + raise_amount):
                                print(f"Player raised to ${max_bet + raise_amount}. Your balance is now ${self.money.get_balance('Player')}")
                                max_bet += raise_amount
                                player_bet = max_bet
                                break
                            else:
                                print("Insufficient Funds.  Player Checks.")
                                break
                        elif response == 'f':
                            self.fold.fold_player(self.player)
                            print("Player Folds.")
                            return
                    elif player_bet == max_bet:
                        print("Player checks.")
                        break
                    else:
                        print("invalid input")
                except ValueError:
                    print("Invalid input. Please enter 'c', 'r', or 'f'.")

        print(f"\nCurrent Pot: ${self.money.show_pot()}")
        print("\nBalances:")
        for name, balance in self.money.show_balances().items():
            print(f"{name}: ${balance}")

class Games:
    def __init__(self, games_played=0):
        self.games_played = games_played

    def play_again(self, balances: Dict[str, int], insanity_levels: Dict[str, int]) -> bool:
        print("\nCurrent Balances:")
        for name, balance in balances.items():
            print(f"{name}: ${balance}")
        print("\nCurrent Insanity Levels:")
        for name, insanity in insanity_levels.items():
            print(f"{name}: {insanity}")
        choice = input("\nWould you like to play another game? (yes/no): ").strip().lower()
        if choice == 'yes':
            return True
        else:
            return False

if __name__ == "__main__":
    initial_balances = None
    initial_insanity = None
    game = Game(initial_balances, initial_insanity)  # Pass initial balances
    game.start_game()
    