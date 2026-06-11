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
            rect = pygame.Rect(x + c * (mini_w + mini_space), y + r * (mini_h + mini_space), mini_w, mini_h)
            if karte["offen"]:
                pygame.draw.rect(screen, (250, 250, 250), rect, border_radius=3)
                # Optional: Sehr kleine Zahl zeichnen (oft zu klein zum Lesen, daher nur Farbkodierung)
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
    SCREEN_WIDTH = 1250
    SCREEN_HEIGHT = 750
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
    GRID_START_X = 50       # Eigenes Raster links
    GRID_START_Y = 150
    ABLAGE_X = 650          # Ablage in der Mitte
    OPPONENT_START_X = 950  # Gegner auf der rechten Seite

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
                            mein_name += event.