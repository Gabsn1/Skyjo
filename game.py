import random

class Card():
    def __init__(self, number):
        self.number = number
        self.visible = False
    
    def change_visibility(self):
        self.visible = not self.visible

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

    def turn_card(self, row, column):
        self.cards[row][column].change_visibility()

    def get_score(self):
        score = 0
        for row in self.cards:
            for card in row:
                if card.visible:
                    score += card.number
        return score
    
    def change_card(self, row, column, new_card):
        old_card = self.cards[row][column]
        self.cards[row][column] = new_card
        new_card.visible = True 
        return old_card

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
        old_card = player.change_card(row, column, new_card)
        self.pile.append(old_card)

if __name__ == "__main__":
    player_names = ["yanik","martini"]
    game = Game(player_names)
    Game