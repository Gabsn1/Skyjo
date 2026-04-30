import random

class Card():

    def __init__(self, number):
        self.number = number
        self.visible = False

    def return_number(self):
        return self.number
    
    def change_visibility(self):
        self.visible = not self.visible

    def return_visibility(self):
        return self.visible

class Deck():
    
    def __init__(self):
        self.cards = [Card(i-3) for _ in range(10) for i in range(1, 16)]
        random.shuffle(self.cards)


    def return_cards(self):
        return self.cards
    
    def give_card(self):
        return self.cards.pop()

