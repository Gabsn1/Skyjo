import pygame
import sys
import json
import threading
import websocket
import os 

# ==========================================
# NETZWERK EINSTELLUNGEN
# ==========================================
SERVER_IP = "10.229.96.88" 
SERVER_PORT = "8000"

server_zustand = None
ws_verbindung = None
mein_name = ""

# ==========================================
# MODERNES LAYOUT & KARTEN FORMAT (FEST)
# ==========================================
CARD_WIDTH = 110   # Perfekte Spielkarten-Breite
CARD_HEIGHT = 160  # Perfekte Spielkarten-Höhe
SPACING = 20       # Abstand zwischen den Karten

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
            
            # MAGIE: Findet den Bereich im Bild, der NICHT transparent ist.
            # Dadurch werden leere Seitenränder ignoriert.
            bounding_rect = bild.get_bounding_rect()
            
            if bounding_rect.width > 0 and bounding_rect.height > 0:
                # Bild auf den sichtbaren Teil zuschneiden
                cropped_bild = bild.subsurface(bounding_rect)
            else:
                cropped_bild = bild
                
            # Jetzt wird das zugeschnittene Bild exakt und satt auf 110x160 gestreckt!
            CARD_IMAGES[wert] = pygame.transform.smoothscale(cropped_bild, (CARD_WIDTH, CARD_HEIGHT))
            
        except FileNotFoundError:
            print(f"WARNUNG: Konnte {pfad} nicht finden.")
            CARD_IMAGES[wert] = None

# ==========================================
# NETZWERK FUNKTIONEN (UNVERÄNDERT)
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

def sende_aktion(aktion, row, col):
    if ws_verbindung:
        ws_verbindung.send(json.dumps({"aktion": aktion, "row": row, "col": col}))

# ==========================================
# GRAFIK HILFSFUNKTIONEN
# ==========================================
def draw_shadow(surface, rect):
    """Zeichnet einen leichten Schatten unter die Karte für einen 3D-Effekt"""
    shadow_rect = rect.copy()
    shadow_rect.x += 4
    shadow_rect.y += 4
    pygame.draw.rect(surface, (10, 40, 20), shadow_rect, border_radius=10) # Dunkles Grün/Schwarz

# ==========================================
# HAUPTSPIEL
# ==========================================
def main():
    global mein_name, server_zustand
    pygame.init()

    # Fenstergröße großzügig und modern gestaltet
    SCREEN_WIDTH = 1050
    SCREEN_HEIGHT = 700
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Multiplayer")

    lade_bilder()

    # Moderne Farbpalette
    TABLE_COLOR = (17, 75, 36)      # Edles, dunkles Billard-Grün
    HEADER_COLOR = (12, 55, 26)     # Etwas dunkler für die obere Leiste
    WHITE = (250, 250, 250)
    GOLD = (255, 215, 0)
    ACCENT_GREEN = (100, 255, 100)  # Leuchtendes Grün für "Am Zug"
    CARD_BACK = (160, 25, 35)       # Elegantes Dunkelrot
    HOVER_COLOR = (255, 235, 100)   # Helles Gelb für Hover-Effekt

    # Schriften (Versuche moderne Systemschriften zu nutzen)
    title_font = pygame.font.SysFont("Segoe UI", 48, bold=True)
    font = pygame.font.SysFont("Segoe UI", 36, bold=True)
    info_font = pygame.font.SysFont("Segoe UI", 22)
    large_info_font = pygame.font.SysFont("Segoe UI", 26, bold=True)

    current_state = "MENU"
    input_box = pygame.Rect(375, 300, 300, 50)
    clock = pygame.time.Clock()
    running = True

    # Layout-Berechnungen (Zentriert das 4x3 Raster)
    GRID_START_X = 80
    GRID_START_Y = 130
    ABLAGE_X = 800

    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # --- MENÜ ---
            if current_state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(mein_name) > 0:
                        threading.Thread(target=netzwerk_starten, args=(mein_name,), daemon=True).start()
                        current_state = "WAITING"
                    elif event.key == pygame.K_BACKSPACE:
                        mein_name = mein_name[:-1]
                    else:
                        if len(mein_name) < 15:
                            mein_name += event.unicode
                            
            # --- IN GAME ---
            elif current_state == "GAME" and server_zustand:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if server_zustand.get("am_zug") == mein_name:
                        for r in range(3):
                            for c in range(4):
                                rect = pygame.Rect(GRID_START_X + c * (CARD_WIDTH + SPACING), 
                                                   GRID_START_Y + r * (CARD_HEIGHT + SPACING), 
                                                   CARD_WIDTH, CARD_HEIGHT)
                                if rect.collidepoint(event.pos):
                                    if event.button == 1: # Linksklick
                                        sende_aktion("turn_card", r, c)
                                    elif event.button == 3: # Rechtsklick
                                        sende_aktion("change_card", r, c)

        # --- ZEICHNEN ---
        screen.fill(TABLE_COLOR)

        if current_state == "MENU":
            # Elegantes Menü
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 100))
            screen.blit(title_font.render("SKYJO - LOBBY", True, WHITE), (360, 25))
            
            screen.blit(large_info_font.render("Bitte gib deinen Namen ein:", True, WHITE), (375, 250))
            pygame.draw.rect(screen, WHITE, input_box, border_radius=8)
            pygame.draw.rect(screen, GOLD, input_box, width=3, border_radius=8)
            screen.blit(large_info_font.render(mein_name, True, (20, 20, 20)), (input_box.x + 15, input_box.y + 8))

        elif current_state == "WAITING":
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 100))
            if server_zustand:
                if server_zustand.get("status") == "game":
                    current_state = "GAME"
                else:
                    spieler_liste = server_zustand.get("spieler", [])
                    txt = f"Warte auf Spieler 2... ({len(spieler_liste)}/2)"
                    screen.blit(title_font.render(txt, True, GOLD), (280, 250))
                    
                    for i, s_name in enumerate(spieler_liste):
                        screen.blit(large_info_font.render(f"• {s_name}", True, WHITE), (450, 340 + i * 40))
            else:
                screen.blit(title_font.render("Verbindung wird hergestellt...", True, WHITE), (250, 250))

        elif current_state == "GAME":
            am_zug = server_zustand.get("am_zug")
            meine_daten = server_zustand.get("spieler_daten", {}).get(mein_name)
            
            # Header Leiste zeichnen
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 80))
            pygame.draw.line(screen, GOLD, (0, 80), (SCREEN_WIDTH, 80), 2)
            
            if meine_daten:
                # Spieler-Status
                zug_text = f"Am Zug: {am_zug}"
                color = ACCENT_GREEN if am_zug == mein_name else WHITE
                screen.blit(large_info_font.render(zug_text, True, color), (30, 25))
                screen.blit(large_info_font.render(f"Meine Punkte: {meine_daten['punkte']}", True, WHITE), (300, 25))
                
                # Eigene Karten zeichnen
                for r, reihe in enumerate(meine_daten["karten"]):
                    for c, karte in enumerate(reihe):
                        rect = pygame.Rect(GRID_START_X + c * (CARD_WIDTH + SPACING), 
                                           GRID_START_Y + r * (CARD_HEIGHT + SPACING), 
                                           CARD_WIDTH, CARD_HEIGHT)
                        
                        # Schatten zeichnen
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
                            # Elegante Rückseite
                            pygame.draw.rect(screen, CARD_BACK, rect, border_radius=10)
                            pygame.draw.rect(screen, GOLD, rect, width=2, border_radius=10)
                            inner_rect = rect.inflate(-16, -16)
                            pygame.draw.rect(screen, GOLD, inner_rect, width=1, border_radius=5)
                            
                        # Hover-Effekt, wenn man dran ist und über eine Karte fährt
                        if am_zug == mein_name and rect.collidepoint(mouse_pos):
                            pygame.draw.rect(screen, HOVER_COLOR, rect, width=4, border_radius=10)

            # Ablagestapel (Pile) zeichnen
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
                # Leerer Platzhalter für die Ablage
                pygame.draw.rect(screen, (30, 90, 50), pile_rect, border_radius=10)
                pygame.draw.rect(screen, HEADER_COLOR, pile_rect, width=2, border_radius=10)

        pygame.display.flip()
        clock.tick(30)

    if ws_verbindung:
        ws_verbindung.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()