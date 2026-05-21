import pygame
import sys
import json
import threading
import websocket

# ==========================================
# NETZWERK EINSTELLUNGEN
# Trage hier die IP-Adresse des PCs ein, der den Server startet!
# Wenn du auf demselben PC wie der Server testest: "127.0.0.1"
# Im WLAN mit deinem Kollegen: z. B. "192.168.40.12"
# ==========================================
SERVER_IP = "127.0.0.1" 
SERVER_PORT = "8000"

server_zustand = None
ws_verbindung = None
mein_name = ""

def netzwerk_nachricht(ws, message):
    """Wird automatisch aufgerufen, wenn der Server den neuen Spielstand schickt"""
    global server_zustand
    server_zustand = json.loads(message)

def netzwerk_starten(name):
    """Baut die Verbindung auf und zeigt den Status im Terminal an"""
    global ws_verbindung
    url = f"ws://{SERVER_IP}:{SERVER_PORT}/ws"
    print(f"⏳ VERSUCHE VERBINDUNG ZU: {url}")
    
    def bei_oeffnen(ws):
        print("🟢 VERBINDUNG ERFOLGREICH! Sende Namen an die Lobby...")
        ws.send(json.dumps({"aktion": "join", "name": name}))
        
    def bei_fehler(ws, error):
        print(f"🔴 NETZWERK-FEHLER: {error}")
        
    def bei_schliessen(ws, close_status_code, close_msg):
        print("⭕ VERBINDUNG ZUM SERVER WURDE GETRENNT!")

    ws_verbindung = websocket.WebSocketApp(
        url, 
        on_message=netzwerk_nachricht,
        on_error=bei_fehler,
        on_close=bei_schliessen
    )
    ws_verbindung.on_open = bei_oeffnen
    ws_verbindung.run_forever()

def sende_aktion(aktion, row, col):
    """Schickt einen Spielzug (Klick) als JSON an den Server"""
    if ws_verbindung:
        ws_verbindung.send(json.dumps({"aktion": aktion, "row": row, "col": col}))

def main():
    global mein_name, server_zustand
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Multiplayer")

    # Farbpalette
    BG_COLOR = (20, 80, 40)
    WHITE = (255, 255, 255)
    GOLD = (255, 215, 0)
    GREEN = (50, 200, 50)
    CARD_BACK_COLOR = (200, 50, 50)
    CARD_FRONT_COLOR = (240, 240, 240)
    TEXT_COLOR = (20, 20, 20)

    # Schriften
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
            
            # =================================================
            # ZUSTAND: MENÜ (Namenseingabe)
            # =================================================
            if current_state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(mein_name) > 0:
                        # Startet das Netzwerk sauber im Hintergrund-Thread
                        threading.Thread(target=netzwerk_starten, args=(mein_name,), daemon=True).start()
                        current_state = "WAITING"
                    elif event.key == pygame.K_BACKSPACE:
                        mein_name = mein_name[:-1]
                    else:
                        if len(mein_name) < 15:
                            mein_name += event.unicode
                            
            # =================================================
            # ZUSTAND: IN GAME (Karten anklicken)
            # =================================================
            elif current_state == "GAME" and server_zustand:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # Prüfen, ob wir laut Server überhaupt an der Reihe sind
                    if server_zustand.get("am_zug") == mein_name:
                        for r in range(3):
                            for c in range(4):
                                rect = pygame.Rect(50 + c*120, 100 + r*170, 100, 150)
                                if rect.collidepoint(x, y):
                                    if event.button == 1:    # Linksklick -> Aufdecken
                                        sende_aktion("turn_card", r, c)
                                    elif event.button == 3:  # Rechtsklick -> Karte austauschen
                                        sende_aktion("change_card", r, c)

        # =================================================
        # ZEICHNEN-LOGIK (UI)
        # =================================================
        screen.fill(BG_COLOR)

        # 1. Menü zeichnen
        if current_state == "MENU":
            screen.blit(title_font.render("SKYJO - LOBBY", True, WHITE), (250, 100))
            screen.blit(info_font.render("Dein Name:", True, WHITE), (300, 260))
            pygame.draw.rect(screen, WHITE, input_box)
            screen.blit(info_font.render(mein_name, True, (0, 0, 0)), (input_box.x + 10, input_box.y + 10))

        # 2. Wartebildschirm zeichnen
        elif current_state == "WAITING":
            if server_zustand:
                if server_zustand.get("status") == "game":
                    current_state = "GAME"
                else:
                    spieler_liste = server_zustand.get("spieler", [])
                    verbunden = len(spieler_liste)
                    txt = f"Warte auf Spieler 2... ({verbunden}/2)"
                    screen.blit(title_font.render(txt, True, GOLD), (220, 250))
                    
                    # Zeigt die Namen der bereits wartenden Spieler an
                    for i, s_name in enumerate(spieler_liste):
                        screen.blit(info_font.render(f"• {s_name}", True, WHITE), (380, 340 + i * 30))
            else:
                screen.blit(title_font.render("Verbindung wird hergestellt...", True, WHITE), (120, 250))

        # 3. Laufendes Spiel zeichnen
        elif current_state == "GAME":
            am_zug = server_zustand.get("am_zug")
            meine_daten = server_zustand.get("spieler_daten", {}).get(mein_name)
            
            if meine_daten:
                # Spieler-Statusleiste oben links
                zug_text = f"Am Zug: {am_zug}"
                color = GREEN if am_zug == mein_name else WHITE
                screen.blit(info_font.render(zug_text, True, color), (20, 20))
                screen.blit(info_font.render(f"Meine Punkte: {meine_daten['punkte']}", True, WHITE), (20, 50))
                
                # Eigene Karten aus den Serverdaten zeichnen
                for r, reihe in enumerate(meine_daten["karten"]):
                    for c, karte in enumerate(reihe):
                        rect = pygame.Rect(50 + c*120, 100 + r*170, 100, 150)
                        if karte["offen"]:
                            pygame.draw.rect(screen, CARD_FRONT_COLOR, rect, border_radius=10)
                            val_surf = font.render(str(karte["nummer"]), True, TEXT_COLOR)
                            screen.blit(val_surf, val_surf.get_rect(center=rect.center))
                        else:
                            pygame.draw.rect(screen, CARD_BACK_COLOR, rect, border_radius=10)
                            pygame.draw.rect(screen, GOLD, rect, width=3, border_radius=10)

            # Ablagestapel (Pile) zeichnen
            screen.blit(info_font.render("Ablage", True, WHITE), (650, 60))
            pile_rect = pygame.Rect(650, 100, 100, 150)
            ablage_wert = server_zustand.get("ablage")
            
            if ablage_wert is not None:
                pygame.draw.rect(screen, CARD_FRONT_COLOR, pile_rect, border_radius=10)
                val_surf = font.render(str(ablage_wert), True, TEXT_COLOR)
                screen.blit(val_surf, val_surf.get_rect(center=pile_rect.center))

        pygame.display.flip()
        clock.tick(30)

    if ws_verbindung:
        ws_verbindung.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()