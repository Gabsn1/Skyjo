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
    
    


