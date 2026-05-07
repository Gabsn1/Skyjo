import pygame
import sys

# Lade das Game-Objekt aus dem Backend!
from game import Game 

def main():
    pygame.init()

    # Fenster einrichten
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Eigenes Spielfeld")

    # Farben
    BG_COLOR = (20, 80, 40)             # Tisch-Grün
    CARD_BACK_COLOR = (200, 50, 50)     # Rot (verdeckt)
    CARD_FRONT_COLOR = (240, 240, 240)  # Weiß (offen)
    TEXT_COLOR = (20, 20, 20)

    # Layout-Maße für das 3x4 Raster
    CARD_WIDTH = 100
    CARD_HEIGHT = 150
    MARGIN_X = 20
    MARGIN_Y = 20
    START_X = 150 
    START_Y = 100

    font = pygame.font.SysFont("Arial", 48, bold=True)
    info_font = pygame.font.SysFont("Arial", 24)

    # Spiel starten über die importierte Backend-Klasse
    game = Game(["Martini", "Gabriel", "Yanik"])
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Klick-Erkennung für die Karten
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                
                for row_idx in range(3):
                    for col_idx in range(4):
                        card_x = START_X + col_idx * (CARD_WIDTH + MARGIN_X)
                        card_y = START_Y + row_idx * (CARD_HEIGHT + MARGIN_Y)
                        
                        # Wenn auf eine Karte geklickt wird -> Backend updaten
                        if card_x <= mouse_x <= card_x + CARD_WIDTH and card_y <= mouse_y <= card_y + CARD_HEIGHT:
                            game.current_player.turn_card(row_idx, col_idx)

        # Spielfeld zeichnen
        screen.fill(BG_COLOR)

        info_text = info_font.render(f"Am Zug: {game.current_player.name} | Offene Punkte: {game.current_player.get_score()}", True, (255, 255, 255))
        screen.blit(info_text, (20, 20))

        # Raster des aktuellen Spielers aufbauen
        for row_idx, row in enumerate(game.current_player.cards):
            for col_idx, card in enumerate(row):
                card_x = START_X + col_idx * (CARD_WIDTH + MARGIN_X)
                card_y = START_Y + row_idx * (CARD_HEIGHT + MARGIN_Y)
                card_rect = pygame.Rect(card_x, card_y, CARD_WIDTH, CARD_HEIGHT)

                if card.visible:
                    # Vorderseite zeichnen
                    pygame.draw.rect(screen, CARD_FRONT_COLOR, card_rect, border_radius=10)
                    pygame.draw.rect(screen, (100, 100, 100), card_rect, width=3, border_radius=10) 
                    
                    text_surface = font.render(str(card.number), True, TEXT_COLOR)
                    text_rect = text_surface.get_rect(center=card_rect.center)
                    screen.blit(text_surface, text_rect)
                else:
                    # Rückseite zeichnen
                    pygame.draw.rect(screen, CARD_BACK_COLOR, card_rect, border_radius=10)
                    pygame.draw.rect(screen, (255, 200, 100), card_rect, width=3, border_radius=10) 

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()