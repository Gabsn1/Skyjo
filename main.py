import pygame
import sys
import json
import threading
import websocket
import os

# ==========================================
# NETZWERK EINSTELLUNGEN
# ==========================================
SERVER_IP = "192.168.40.12" 
SERVER_PORT = "8000"

server_zustand = None
ws_verbindung = None
mein_name = ""

# ==========================================
# GRAFIK & ASSETS
# ==========================================
CARD_WIDTH, CARD_HEIGHT = 100, 150
CARD_IMAGES = {}

def lade_bilder():
    """Lädt die Kartenbilder aus dem Bilder-Ordner und skaliert sie."""
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
            CARD_IMAGES[wert] = pygame.transform.smoothscale(bild, (CARD_WIDTH, CARD_HEIGHT))
        except FileNotFoundError:
            print(f"WARNUNG: Konnte {pfad} nicht finden. Nutze Platzhalter für {wert}.")
            CARD_IMAGES[wert] = None

def zeichne_karten_rueckseite(screen, rect, font):
    """Zeichnet eine schicke Platzhalter-Rückseite, bis ein Bild existiert."""
    pygame.draw.rect(screen, (20, 30, 80), rect, border_radius=10) # Dunkelblau
    pygame.draw.rect(screen, (255, 215, 0), rect, width=3, border_radius=10) # Goldener Rand
    
    # Ein goldenes 'S' in der Mitte als Logo
    logo_surf = font.render("S", True, (255, 215, 0))
    screen.blit(logo_surf, logo_surf.get_rect(center=rect.center))

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
        print("🟢 VERBINDUNG ERFOLGREICH! Sende Namen...")
        ws.send(json.dumps({"aktion": "join", "name": name}))
        
    def bei_fehler(ws, error):
        print(f"🔴 NETZWERK-FEHLER: {error}")
        
    def bei_schliessen(ws, close_status_code, close_msg):
        print("⭕ VERBINDUNG WURDE GETRENNT!")

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
# HAUPTSPIEL
# ==========================================
def main():
    global mein_name, server_zustand
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT = 900, 650
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Multiplayer")

    # Farben
    BG_COLOR = (30, 110, 60) # Schönes Casino-Grün
    WHITE = (255, 255, 255)
    GOLD = (255, 215, 0)
    GREEN = (50, 200, 50)
    CARD_FRONT = (240, 240, 240)
    TEXT_COLOR = (20, 20, 20)

    # Fonts
    title_font = pygame.font.SysFont("Arial", 56, bold=True)
    font = pygame.font.SysFont("Arial", 48, bold=True)
    logo_font = pygame.font.SysFont("Georgia", 60, bold=True)
    info_font = pygame.font.SysFont("Arial", 24, bold=True)

    # Bilder laden
    lade_bilder()

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
                    if server_zustand["am_zug"] == mein_name:
                        for r in range(3):
                            for c in range(4):
                                rect = pygame.Rect(50 + c*120, 100 + r*170, CARD_WIDTH, CARD_HEIGHT)
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
            pygame.draw.rect(screen, WHITE, input_box, border_radius=5)
            screen.blit(info_font.render(mein_name, True, (0,0,0)), (input_box.x + 10, input_box.y + 10))
            screen.blit(info_font.render("Drücke ENTER zum Starten", True, GOLD), (300, 370))

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
            
            if meine_daten:
                # Infos oben anzeigen
                zug_text = f"Am Zug: {am_zug}"
                color = GOLD if am_zug == mein_name else WHITE
                screen.blit(info_font.render(zug_text, True, color), (20, 20))
                screen.blit(info_font.render(f"Meine Punkte: {meine_daten['punkte']}", True, WHITE), (20, 50))
                
                # Eigene Karten zeichnen
                for r, reihe in enumerate(meine_daten["karten"]):
                    for c, karte in enumerate(reihe):
                        rect = pygame.Rect(50 + c*120, 100 + r*170, CARD_WIDTH, CARD_HEIGHT)
                        wert = karte["nummer"]
                        
                        if karte["offen"]:
                            # Wenn Bild vorhanden, Bild zeichnen. Sonst Fallback-Rechteck
                            if wert in CARD_IMAGES and CARD_IMAGES[wert] is not None:
                                screen.blit(CARD_IMAGES[wert], rect)
                            else:
                                pygame.draw.rect(screen, CARD_FRONT, rect, border_radius=10)
                                val_surf = font.render(str(wert), True, TEXT_COLOR)
                                screen.blit(val_surf, val_surf.get_rect(center=rect.center))
                        else:
                            # Rückseite zeichnen
                            zeichne_karten_rueckseite(screen, rect, logo_font)

                # Ablagestapel zeichnen
                screen.blit(info_font.render("Ablagestapel", True, WHITE), (630, 60))
                pile_rect = pygame.Rect(650, 100, CARD_WIDTH, CARD_HEIGHT)
                ablage_wert = server_zustand.get("ablage")
                
                if ablage_wert is not None:
                    if ablage_wert in CARD_IMAGES and CARD_IMAGES[ablage_wert] is not None:
                        screen.blit(CARD_IMAGES[ablage_wert], pile_rect)
                    else:
                        pygame.draw.rect(screen, CARD_FRONT, pile_rect, border_radius=10)
                        val_surf = font.render(str(ablage_wert), True, TEXT_COLOR)
                        screen.blit(val_surf, val_surf.get_rect(center=pile_rect.center))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()