import pygame
import sys
import json
import threading
import websocket
import os 

# ==========================================
# NETZWERK EINSTELLUNGEN
# ==========================================
SERVER_IP = "192.168.224.88" 
SERVER_PORT = "8000"

server_zustand = None
ws_verbindung = None
mein_name = ""

# ==========================================
# MODERNES LAYOUT & KARTEN FORMAT (FEST)
# ==========================================
CARD_WIDTH = 110
CARD_HEIGHT = 160
SPACING = 20

CARD_IMAGES = {}

def lade_bilder():
    """Lädt die Bilder, schneidet transparente Ränder ab und streckt sie passgenau."""
    dateinamen = {
        -2: "minus_two.png", -1: "minus_one.png", 0: "zero.png",
        1: "one.png", 2: "two.png", 3: "three.png", 4: "four.png",
        5: "five.png", 6: "six.png", 7: "seven.png", 8: "eight.png",
        9: "nine.png", 10: "ten.png", 11: "eleven.png", 12: "twelve.png"
    }
    
    for wert, dateiname in dateinamen.items():
        pfad = os.path.join("Bilder", dateiname)
        try:
            bild = pygame.image.load(pfad).convert_alpha()
            bounding_rect = bild.get_bounding_rect()
            
            if bounding_rect.width > 0 and bounding_rect.height > 0:
                cropped_bild = bild.subsurface(bounding_rect)
            else:
                cropped_bild = bild
                
            CARD_IMAGES[wert] = pygame.transform.smoothscale(cropped_bild, (CARD_WIDTH, CARD_HEIGHT))
            
        except FileNotFoundError:
            print(f"WARNUNG: Konnte {pfad} nicht finden.")
            CARD_IMAGES[wert] = None

# ==========================================
# NETZWERK FUNKTIONEN
# ==========================================
def netzwerk_nachricht(ws, message):
    global server_zustand
    server_zustand = json.loads(message)

def netzwerk_starten(name):
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

def sende_aktion(aktion, row=None, col=None):
    if ws_verbindung:
        msg = {"aktion": aktion}
        if row is not None:
            msg["row"] = row
        if col is not None:
            msg["col"] = col
        ws_verbindung.send(json.dumps(msg))

# ==========================================
# GRAFIK HILFSFUNKTIONEN
# ==========================================
def draw_shadow(surface, rect):
    """Zeichnet einen leichten Schatten unter die Karte für einen 3D-Effekt"""
    shadow_rect = rect.copy()
    shadow_rect.x += 4
    shadow_rect.y += 4
    pygame.draw.rect(surface, (10, 40, 20), shadow_rect, border_radius=10)

def draw_mini_grid(screen, x, y, karten, font, color, card_back_color):
    """Zeichnet ein Miniatur-Raster für die Gegner"""
    mini_w, mini_h = 16, 22
    mini_space = 4
    for r, reihe in enumerate(karten):
        for c, karte in enumerate(reihe):
            if karte is None:
                continue
            rect = pygame.Rect(x + c * (mini_w + mini_space), y + r * (mini_h + mini_space), mini_w, mini_h)
            if karte["offen"]:
                pygame.draw.rect(screen, (250, 250, 250), rect, border_radius=3)
            else:
                pygame.draw.rect(screen, card_back_color, rect, border_radius=3)
                pygame.draw.rect(screen, (255, 215, 0), rect, width=1, border_radius=3)

# ==========================================
# HAUPTSPIEL
# ==========================================
def main():
    global mein_name, server_zustand
    pygame.init()

    # Fenster etwas breiter gemacht, um 8 Spieler unterzubringen
    SCREEN_WIDTH = 1350
    SCREEN_HEIGHT = 850
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Multiplayer (Bis zu 8 Spieler)")

    lade_bilder()

    # Moderne Farbpalette
    TABLE_COLOR = (17, 75, 36)
    HEADER_COLOR = (12, 55, 26)
    WHITE = (250, 250, 250)
    GOLD = (255, 215, 0)
    ACCENT_GREEN = (100, 255, 100)
    CARD_BACK = (160, 25, 35)
    HOVER_COLOR = (255, 235, 100)

    # Schriften
    title_font = pygame.font.SysFont("Segoe UI", 48, bold=True)
    font = pygame.font.SysFont("Segoe UI", 36, bold=True)
    info_font = pygame.font.SysFont("Segoe UI", 22)
    large_info_font = pygame.font.SysFont("Segoe UI", 26, bold=True)
    mini_font = pygame.font.SysFont("Segoe UI", 14)

    current_state = "MENU"
    input_box = pygame.Rect(475, 300, 300, 50)
    clock = pygame.time.Clock()
    running = True

    # Layout-Berechnungen
    GRID_START_X = 50       
    GRID_START_Y = 150
    ABLAGE_X = 650          
    OPPONENT_START_X = 950  

    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # --- MENÜ ---
            elif current_state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(mein_name) > 0:
                        threading.Thread(target=netzwerk_starten, args=(mein_name,), daemon=True).start()
                        current_state = "WAITING"
                    elif event.key == pygame.K_BACKSPACE:
                        mein_name = mein_name[:-1]
                    else:
                        if len(mein_name) < 15:
                            mein_name += event.unicode
            
            # --- WAITING / START BUTTON ---
            elif current_state == "WAITING" and server_zustand:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    host = server_zustand.get("host")
                    # Nur der Host darf den Klick auslösen!
                    if mein_name == host:
                        spieler_liste = server_zustand.get("spieler", [])
                        if len(spieler_liste) >= 2:
                            start_button = pygame.Rect(450, 600, 350, 60)
                            if start_button.collidepoint(event.pos):
                                sende_aktion("start_game")
            
            # --- IN GAME ---
            elif current_state == "GAME" and server_zustand:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if server_zustand.get("am_zug") == mein_name:
                        meine_daten = server_zustand.get("spieler_daten", {}).get(mein_name, {})
                        karten = meine_daten.get("karten", [])
                        for r in range(len(karten)):
                            for c in range(len(karten[r])):
                                rect = pygame.Rect(GRID_START_X + c * (CARD_WIDTH + SPACING), 
                                                   GRID_START_Y + r * (CARD_HEIGHT + SPACING), 
                                                   CARD_WIDTH, CARD_HEIGHT)
                                if rect.collidepoint(event.pos):
                                    if event.button == 1: # Linksklick -> Ablage
                                        sende_aktion("take_pile", r, c)
                                    elif event.button == 3: # Rechtsklick -> Deck
                                        sende_aktion("take_deck", r, c)

        # --- ZEICHNEN ---
        screen.fill(TABLE_COLOR)

        if current_state == "MENU":
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 100))
            screen.blit(title_font.render("SKYJO - LOBBY", True, WHITE), (460, 25))
            
            screen.blit(large_info_font.render("Bitte gib deinen Namen ein:", True, WHITE), (475, 250))
            pygame.draw.rect(screen, WHITE, input_box, border_radius=8)
            pygame.draw.rect(screen, GOLD, input_box, width=3, border_radius=8)
            screen.blit(large_info_font.render(mein_name, True, (20, 20, 20)), (input_box.x + 15, input_box.y + 8))

        elif current_state == "WAITING":
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 100))
            screen.blit(title_font.render("SKYJO - LOBBY", True, WHITE), (460, 25))
            if server_zustand:
                if server_zustand.get("status") == "game":
                    current_state = "GAME"
                else:
                    spieler_liste = server_zustand.get("spieler", [])
                    host = server_zustand.get("host")
                    txt = f"Spieler in der Lobby: {len(spieler_liste)}/8"
                    screen.blit(title_font.render(txt, True, GOLD), (420, 150))
                    
                    for i, s_name in enumerate(spieler_liste):
                        # Markiert den Host in der Liste
                        mark = " (Host)" if s_name == host else ""
                        screen.blit(large_info_font.render(f"• {s_name}{mark}", True, WHITE), (550, 250 + i * 40))
                    
                    # Start-Button (nur für den Host sichtbar)
                    if mein_name == host:
                        start_button = pygame.Rect(450, 600, 350, 60)
                        button_color = ACCENT_GREEN if len(spieler_liste) >= 2 else (100, 100, 100)
                        pygame.draw.rect(screen, button_color, start_button, border_radius=10)
                        pygame.draw.rect(screen, GOLD, start_button, width=3, border_radius=10)
                        
                        btn_text = "SPIEL STARTEN" if len(spieler_liste) >= 2 else "Warte auf 2. Spieler..."
                        txt_surf = large_info_font.render(btn_text, True, (20,20,20) if len(spieler_liste) >= 2 else WHITE)
                        screen.blit(txt_surf, txt_surf.get_rect(center=start_button.center))
                    else:
                        # Das sehen alle Mitspieler
                        screen.blit(large_info_font.render("Warte auf Host...", True, HOVER_COLOR), (530, 620))
            else:
                screen.blit(title_font.render("Verbindung wird hergestellt...", True, WHITE), (350, 250))

        elif current_state == "GAME":
            am_zug = server_zustand.get("am_zug")
            alle_daten = server_zustand.get("spieler_daten", {})
            meine_daten = alle_daten.get(mein_name)
            
            # Header Leiste zeichnen
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 80))
            pygame.draw.line(screen, GOLD, (0, 80), (SCREEN_WIDTH, 80), 2)
            
            # Zug-Info oben mittig
            zug_text = "DU BIST DRAN!" if am_zug == mein_name else f"Am Zug: {am_zug}"
            color = ACCENT_GREEN if am_zug == mein_name else WHITE
            screen.blit(title_font.render(zug_text, True, color), (480, 15))
            
            if meine_daten:
                screen.blit(large_info_font.render(f"Deine Punkte: {meine_daten['punkte']}", True, WHITE), (50, 25))
                
                # EIGENE KARTEN (Groß)
                screen.blit(large_info_font.render("Dein Raster:", True, GOLD), (GRID_START_X, GRID_START_Y - 40))
                for r, reihe in enumerate(meine_daten["karten"]):
                    for c, karte in enumerate(reihe):
                        rect = pygame.Rect(GRID_START_X + c * (CARD_WIDTH + SPACING), 
                                           GRID_START_Y + r * (CARD_HEIGHT + SPACING), 
                                           CARD_WIDTH, CARD_HEIGHT)
                        
                        if karte is None:
                            continue
                            
                        draw_shadow(screen, rect)
                        
                        if karte["offen"]:
                            wert = karte["nummer"]
                            if wert in CARD_IMAGES and CARD_IMAGES[wert] is not None:
                                screen.blit(CARD_IMAGES[wert], rect)
                            else:
                                pygame.draw.rect(screen, WHITE, rect, border_radius=10)
                                val_surf = font.render(str(wert), True, (20, 20, 20))
                                screen.blit(val_surf, val_surf.get_rect(center=rect.center))
                        else:
                            pygame.draw.rect(screen, CARD_BACK, rect, border_radius=10)
                            pygame.draw.rect(screen, GOLD, rect, width=2, border_radius=10)
                            inner_rect = rect.inflate(-16, -16)
                            pygame.draw.rect(screen, GOLD, inner_rect, width=1, border_radius=5)
                            
                        # Hover-Effekt
                        if am_zug == mein_name and rect.collidepoint(mouse_pos):
                            pygame.draw.rect(screen, HOVER_COLOR, rect, width=4, border_radius=10)

            # ABLAGESTAPEL (Mitte)
            screen.blit(large_info_font.render("Ablagestapel", True, GOLD), (ABLAGE_X - 10, GRID_START_Y - 40))
            pile_rect = pygame.Rect(ABLAGE_X, GRID_START_Y, CARD_WIDTH, CARD_HEIGHT)
            draw_shadow(screen, pile_rect)
            
            ablage_wert = server_zustand.get("ablage")
            if ablage_wert is not None:
                if ablage_wert in CARD_IMAGES and CARD_IMAGES[ablage_wert] is not None:
                    screen.blit(CARD_IMAGES[ablage_wert], pile_rect)
                else:
                    pygame.draw.rect(screen, WHITE, pile_rect, border_radius=10)
                    val_surf = font.render(str(ablage_wert), True, (20, 20, 20))
                    screen.blit(val_surf, val_surf.get_rect(center=pile_rect.center))
            else:
                pygame.draw.rect(screen, (30, 90, 50), pile_rect, border_radius=10)
                pygame.draw.rect(screen, HEADER_COLOR, pile_rect, width=2, border_radius=10)

            # GEGNER SCOREBOARD (Rechts)
            pygame.draw.line(screen, GOLD, (OPPONENT_START_X - 30, 80), (OPPONENT_START_X - 30, SCREEN_HEIGHT), 2)
            screen.blit(large_info_font.render("Mitspieler", True, GOLD), (OPPONENT_START_X, 100))
            
            y_offset = 150
            for spieler_name, daten in alle_daten.items():
                if spieler_name != mein_name:
                    # Hervorheben, wenn der Gegner dran ist
                    g_color = ACCENT_GREEN if am_zug == spieler_name else WHITE
                    
                    # Name und Punkte
                    screen.blit(info_font.render(f"{spieler_name}", True, g_color), (OPPONENT_START_X, y_offset))
                    screen.blit(info_font.render(f"Punkte: {daten['punkte']}", True, WHITE), (OPPONENT_START_X + 150, y_offset))
                    
                    # Miniatur-Raster zeichnen
                    draw_mini_grid(screen, OPPONENT_START_X, y_offset + 30, daten["karten"], mini_font, g_color, CARD_BACK)
                    
                    # Nächster Gegner rutscht weiter nach unten (100px Abstand reicht für Mini-Raster)
                    y_offset += 100 

        pygame.display.flip()
        clock.tick(30)

    if ws_verbindung:
        ws_verbindung.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()