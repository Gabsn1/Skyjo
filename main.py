import pygame
import sys
from game import Game 

def main():
    pygame.init()

    # Fenster etwas breiter für den Ablagestapel
    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Multiplayer")

    # Farben
    BG_COLOR = (20, 80, 40)
    WHITE = (255, 255, 255)
    GOLD = (255, 215, 0)
    GREEN = (50, 200, 50)
    GRAY = (150, 150, 150)
    CARD_BACK_COLOR = (200, 50, 50)
    CARD_FRONT_COLOR = (240, 240, 240)
    TEXT_COLOR = (20, 20, 20)

    # Schriften
    title_font = pygame.font.SysFont("Arial", 56, bold=True)
    font = pygame.font.SysFont("Arial", 48, bold=True)
    info_font = pygame.font.SysFont("Arial", 24)
    lobby_font = pygame.font.SysFont("Arial", 32)

    current_state = "MENU"

    player_name = ""
    lobby_players = [] 
    
    input_box = pygame.Rect(300, 300, 300, 50)
    input_active = False
    game = None 

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # =================================================
            # MENU
            # =================================================
            if current_state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    input_active = input_box.collidepoint(event.pos)
                if event.type == pygame.KEYDOWN and input_active:
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        
                        # --- SIMULATION FÜR DEN LOKALEN TEST ---
                        lobby_players = [
                            {"name": player_name, "ready": False},
                            {"name": "Gabriel", "ready": False}, 
                            {"name": "Yanik", "ready": False}    
                        ]
                        current_state = "LOBBY"
                        
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        if len(player_name) < 15:
                            player_name += event.unicode

            # =================================================
            # LOBBY
            # =================================================
            elif current_state == "LOBBY":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: 
                        # --- SIMULATION FÜR DEN LOKALEN TEST ---
                        for p in lobby_players:
                            if p["name"] == player_name:
                                p["ready"] = not p["ready"] 
                                
                            if p["name"] != player_name:
                                p["ready"] = True
                                
                # Start prüfen
                if len(lobby_players) > 0 and all(p["ready"] for p in lobby_players):
                    # Nur die Namen an das Game-Objekt übergeben (wie in deiner game.py gefordert)
                    player_names = [p["name"] for p in lobby_players]
                    game = Game(player_names)
                    current_state = "GAME"

            # =================================================
            # GAME
            # =================================================
            elif current_state == "GAME":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    button = event.button 

                    for r in range(3):
                        for c in range(4):
                            rect = pygame.Rect(50 + c*120, 100 + r*170, 100, 150)
                            if rect.collidepoint(mouse_x, mouse_y):
                                if button == 1:
                                    # Linksklick -> Aufdecken
                                    game.action("turn_card", r, c)
                                elif button == 3:
                                    # Rechtsklick -> Austauschen
                                    game.action("change_card", r, c)


        # =================================================
        # ZEICHNEN
        # =================================================
        screen.fill(BG_COLOR)

        if current_state == "MENU":
            title_surf = title_font.render("SKYJO", True, WHITE)
            screen.blit(title_surf, (450 - title_surf.get_width()//2, 100))
            pygame.draw.rect(screen, WHITE if input_active else (180, 180, 180), input_box)
            pygame.draw.rect(screen, (0, 0, 0), input_box, 2)
            screen.blit(lobby_font.render(player_name, True, (0, 0, 0)), (input_box.x + 10, input_box.y + 10))

        elif current_state == "LOBBY":
            screen.blit(title_font.render("SPIEL-LOBBY", True, GOLD), (280, 50))
            
            for i, p in enumerate(lobby_players):
                if p["ready"]:
                    status_text = "BEREIT"
                    color = GREEN
                else:
                    status_text = "WARTET"
                    color = GRAY
                    
                text_surf = lobby_font.render(f"{i+1}. {p['name']} - {status_text}", True, color)
                screen.blit(text_surf, (300, 200 + i * 40))
                
            hint = info_font.render("Drücke ENTER, um dich bereit zu melden!", True, WHITE)
            screen.blit(hint, (450 - hint.get_width()//2, 500))

        elif current_state == "GAME":
            # Spieler Info
            info_text = info_font.render(f"Am Zug: {game.current_player.name} | Punkte: {game.current_player.get_score()}", True, WHITE)
            screen.blit(info_text, (20, 20))
            controls_text = info_font.render("Linksklick: Aufdecken | Rechtsklick: Austauschen", True, GOLD)
            screen.blit(controls_text, (20, 550))

            # 1. Raster des Spielers zeichnen
            for row_idx, row in enumerate(game.current_player.cards):
                for col_idx, card in enumerate(row):
                    x, y = 50 + col_idx*120, 100 + row_idx*170
                    rect = pygame.Rect(x, y, 100, 150)
                    if card.visible:
                        pygame.draw.rect(screen, CARD_FRONT_COLOR, rect, border_radius=10)
                        val_surf = font.render(str(card.number), True, TEXT_COLOR)
                        screen.blit(val_surf, val_surf.get_rect(center=rect.center))
                    else:
                        pygame.draw.rect(screen, CARD_BACK_COLOR, rect, border_radius=10)
                        pygame.draw.rect(screen, GOLD, rect, width=3, border_radius=10)

            # 2. Ablagestapel (Pile) zeichnen
            pile_x, pile_y = 650, 100
            screen.blit(info_font.render("Ablagestapel", True, WHITE), (pile_x, pile_y - 40))
            pile_rect = pygame.Rect(pile_x, pile_y, 100, 150)
            
            if len(game.pile) > 0:
                top_card = game.pile[-1]
                pygame.draw.rect(screen, CARD_FRONT_COLOR, pile_rect, border_radius=10)
                pygame.draw.rect(screen, (100, 100, 100), pile_rect, width=3, border_radius=10)
                screen.blit(font.render(str(top_card.number), True, TEXT_COLOR), font.render(str(top_card.number), True, TEXT_COLOR).get_rect(center=pile_rect.center))
            else:
                pygame.draw.rect(screen, (50, 100, 50), pile_rect, border_radius=10)
                pygame.draw.rect(screen, (100, 150, 100), pile_rect, width=3, border_radius=10)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()