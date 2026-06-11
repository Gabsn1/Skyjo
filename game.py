import random

class Card():
    def __init__(self, number):
        self.number = number
        self.visible = False
    
    def change_visibility(self):
        if not self.visible:
            self.visible = True
            return True
        return False

class Deck():
    def __init__(self):
        self.cards = [Card(i-3) for _ in range(10) for i in range(1, 16)]
        random.shuffle(self.cards)
    
    def give_card(self):
        return self.cards.pop()

class Player():
    def __init__(self, name, deck):
        self.name = name
        self.cards = [[deck.give_card() for _ in range(4)] for _ in range(3)]

    def __check_columns(self):
        for i in range(4):
            if any(self.cards[j][i] is None for j in range(3)):
                continue

            if all(self.cards[j][i].number == self.cards[0][i].number and self.cards[j][i].visible for j in range(3)):
                for j in range(3):
                    self.cards[j][i] = None

    def get_score(self):
        score = 0
        for row in self.cards:
            for card in row:
                if card is not None and card.visible:
                    score += card.number
        return score

    def turn_card(self, row, column):
        self.cards[row][column].change_visibility()
        self.__check_columns()
        score = self.get_score()
        return score

    
    def change_card(self, row, column, new_card):
        old_card = self.cards[row][column]
        self.cards[row][column] = new_card
        new_card.visible = True
        self.__check_columns()
        score = self.get_score()
        return old_card, score

class Game():
    def __init__(self, player_names):
        self.deck = Deck()
        self.pile = [self.deck.give_card()]
        self.player = []
        
        for name in player_names:
            self.player.append(Player(name, self.deck))
            
        self.current_player = self.player[0]

    def next_player(self):
        for p in self.player:
            if p == self.current_player:
                self.current_player = self.player[(self.player.index(p) + 1) % len(self.player)]
                break
    
    def take_pile(self):
        card = self.pile.pop()
        return card

    def take_deck(self):
        card = self.deck.give_card()
        return card

    def change_card(self, player, row, column, new_card):
        old_card, score = player.change_card(row, column, new_card)
        self.pile.append(old_card)
        return score
    
    def check_end(self):
        for p in self.player:
            all_open_or_deleted = True
            for row in p.cards:
                for card in row:
                    if card is not None and not card.visible:
                        all_open_or_deleted = False
            if all_open_or_deleted:
                return True
        return False
    
    def get_winner(self):
        winner = self.player[0]
        for p in self.player:
            if p.get_score() < winner.get_score():
                winner = p
        return winner.name, winner.get_score()

if __name__ == "__main__":
    player_names = ["yanik","max"]
    game = Game(player_names)
    print(game.change_card(game.player[0], 0, 0, game.take_deck()))
    print(game.change_card(game.player[0], 0, 1, game.take_pile()))
