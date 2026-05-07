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
    

class Game():

    def __init__(self, player_names):
        self.deck = Deck()
        self.player = []
        for i in player_names:
            self.player.append(Player(i, self.deck))
        self.current_player = self.player[0]

    def next_player(self):
        for i in self.player:
            if self.player[i] == self.current_player:
                self.current_player = self.player[(self.player.index(i)+1) % len(self.player)]
                break
        
    
    
if __name__ == "__main__":
    game = Game(["Martini", "Gabriel", "Yanik"])
    print(game.player["Martini"].get_score())
    game.player["Martini"].turn_card(0, 0)
    print(game.player["Martini"].get_score())

