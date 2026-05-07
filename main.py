import pygame
import sys
import json
import threading
import websocket

# ==========================================
# NETZWERK EINSTELLUNGEN
# Trage hier die IP-Adresse des PCs ein, der den Server startet!
# ==========================================
SERVER_IP = " 10.10.209.115" 
SERVER_PORT = "8000"

server_zustand = None
ws_verbindung = None
mein_name = ""

def netzwerk_nachricht(ws, message):
    """Wird automatisch aufgerufen, wenn der Server den neuen Spielstand schickt"""
    global server_zustand
    server_zustand = json.loads(message)

def netzwerk_starten(name):
    """Baut die Verbindung auf und meldet sich in der Lobby an"""
    global ws_verbindung
    url = f"ws://{SERVER_IP}:{SERVER_PORT}/ws"
    ws_verbindung = websocket.WebSocketApp(url, on_message=netzwerk_nachricht)
    
    # Sobald Verbindung steht, Name an Server schicken
    ws_verbindung.on_open = lambda ws: ws.send(json.dumps({"aktion": "join", "name": name}))
    ws_verbindung.run_forever()

def sende_aktion(aktion, row, col):
    """Schickt einen Klick an den Server"""
    if ws_verbindung:
        ws_verbindung.send(json.dumps({"aktion": aktion, "row": row, "col": col}))

def main():
    global mein_name, server_zustand
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Multiplayer")

    BG_COLOR, WHITE, GOLD, GREEN = (20, 80, 40), (255, 255, 255), (255, 215, 0), (50, 200, 50)
    CARD_BACK, CARD_FRONT, TEXT_COLOR = (200, 50, 50), (240, 240, 240), (20, 20, 20)

    title_font = pygame.font.SysFont("Arial", 56, bold=True)
    font = pygame.font.SysFont("Arial", 48, bold=True)
    info_font = pygame.font.SysFont("Arial", 24)

    current_state = "MENU"
    input_box = pygame.Rect(300, 300, 300, 50)
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # --- NAMENSEINGABE ---
            if current_state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(mein_name) > 0:
                        # Netzwerk-Thread starten, damit das Spiel nicht einfriert
                        threading.Thread(target=netzwerk_starten, args=(mein_name,), daemon=True).start()
                        current_state = "WAITING"
                    elif event.key == pygame.K_BACKSPACE:
                        mein_name = mein_name[:-1]
                    else:
                        if len(mein_name) < 15:
                            mein_name += event.unicode
                            
            # --- SPIEL & KLICKS ---
            elif current_state == "GAME" and server_zustand:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # Prüfen, ob wir am Zug sind
                    if server_zustand["am_zug"] == mein_name:
                        for r in range(3):
                            for c in range(4):
                                rect = pygame.Rect(50 + c*120, 100 + r*170, 100, 150)
                                if rect.collidepoint(x, y):
                                    if event.button == 1:
                                        sende_aktion("turn_card", r, c)
                                    elif event.button == 3:
                                        sende_aktion("change_card", r, c)

        # --- ZEICHNEN ---
        screen.fill(BG_COLOR)

        if current_state == "MENU":
            screen.blit(title_font.render("SKYJO - LOBBY", True, WHITE), (250, 100))
            screen.blit(info_font.render("Dein Name:", True, WHITE), (300, 260))
            pygame.draw.rect(screen, WHITE, input_box)
            screen.blit(info_font.render(mein_name, True, (0,0,0)), (input_box.x + 10, input_box.y + 10))

        # Zustand des Servers auswerten
        elif current_state == "WAITING":
            if server_zustand and server_zustand.get("status") == "game":
                current_state = "GAME"
            else:
                verbunden = len(server_zustand["spieler"]) if server_zustand else 0
                txt = f"Warte auf Spieler 2... ({verbunden}/2 verbunden)"
                screen.blit(title_font.render(txt, True, GOLD), (100, 250))

        elif current_state == "GAME":
            am_zug = server_zustand["am_zug"]
            meine_daten = server_zustand["spieler_daten"].get(mein_name)
            
            # Infos oben anzeigen
            zug_text = f"Am Zug: {am_zug}"
            color = GREEN if am_zug == mein_name else WHITE
            screen.blit(info_font.render(zug_text, True, color), (20, 20))
            screen.blit(info_font.render(f"Meine Punkte: {meine_daten['punkte']}", True, WHITE), (20, 50))
            
            # Eigene Karten zeichnen
            for r, reihe in enumerate(meine_daten["karten"]):
                for c, karte in enumerate(reihe):
                    rect = pygame.Rect(50 + c*120, 100 + r*170, 100, 150)
                    if karte["offen"]:
                        pygame.draw.rect(screen, CARD_FRONT, rect, border_radius=10)
                        val_surf = font.render(str(karte["nummer"]), True, TEXT_COLOR)
                        screen.blit(val_surf, val_surf.get_rect(center=rect.center))
                    else:
                        pygame.draw.rect(screen, CARD_BACK, rect, border_radius=10)
                        pygame.draw.rect(screen, GOLD, rect, width=3, border_radius=10)

            # Ablagestapel zeichnen
            screen.blit(info_font.render("Ablage", True, WHITE), (650, 60))
            pile_rect = pygame.Rect(650, 100, 100, 150)
            ablage_wert = server_zustand.get("ablage")
            if ablage_wert is not None:
                pygame.draw.rect(screen, CARD_FRONT, pile_rect, border_radius=10)
                val_surf = font.render(str(ablage_wert), True, TEXT_COLOR)
                screen.blit(val_surf, val_surf.get_rect(center=pile_rect.center))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()