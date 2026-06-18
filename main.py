import pygame
import sys
import json
import threading
import websocket
import os 
import math

# ==========================================
# NETZWERK EINSTELLUNGEN
# ==========================================
SERVER_IP = "10.152.59.12" 
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
    """Zeichnet ein Miniatur-Raster für die Gegner (mit Bildern!)"""
    mini_w, mini_h = 16, 22
    mini_space = 4
    for r, reihe in enumerate(karten):
        for c, karte in enumerate(reihe):
            if karte is None:
                continue
            rect = pygame.Rect(x + c * (mini_w + mini_space), y + r * (mini_h + mini_space), mini_w, mini_h)
            
            if karte["offen"]:
                wert = karte["nummer"]
                # Bild verkleinert zeichnen
                if wert in CARD_IMAGES and CARD_IMAGES[wert] is not None:
                    mini_img = pygame.transform.smoothscale(CARD_IMAGES[wert], (mini_w, mini_h))
                    screen.blit(mini_img, rect)
                else:
                    # Fallback auf reinen Text, falls das Bild fehlt
                    pygame.draw.rect(screen, (250, 250, 250), rect, border_radius=3)
                    val_surf = font.render(str(wert), True, (20, 20, 20))
                    screen.blit(val_surf, val_surf.get_rect(center=rect.center))
            else:
                pygame.draw.rect(screen, card_back_color, rect, border_radius=3)
                pygame.draw.rect(screen, (255, 215, 0), rect, width=1, border_radius=3)

def draw_card_front(surface, rect, wert, font):
    if wert in CARD_IMAGES and CARD_IMAGES[wert] is not None:
        surface.blit(CARD_IMAGES[wert], rect)
    else:
        pygame.draw.rect(surface, (250, 250, 250), rect, border_radius=10)
        val_surf = font.render(str(wert), True, (20, 20, 20))
        surface.blit(val_surf, val_surf.get_rect(center=rect.center))

# ==========================================
# HAUPTSPIEL
# ==========================================
def main():
    global mein_name, server_zustand
    pygame.init()

    SCREEN_WIDTH = 1350
    SCREEN_HEIGHT = 850
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Skyjo - Multiplayer")

    lade_bilder()

    TABLE_COLOR = (17, 75, 36)
    HEADER_COLOR = (12, 55, 26)
    WHITE = (250, 250, 250)
    GOLD = (255, 215, 0)
    ACCENT_GREEN = (100, 255, 100)
    CARD_BACK = (160, 25, 35)
    HOVER_COLOR = (255, 235, 100)

    title_font = pygame.font.SysFont("Segoe UI", 56, bold=True)
    font = pygame.font.SysFont("Segoe UI", 36, bold=True)
    info_font = pygame.font.SysFont("Segoe UI", 22)
    large_info_font = pygame.font.SysFont("Segoe UI", 26, bold=True)
    mini_font = pygame.font.SysFont("Segoe UI", 14)

    current_state = "MENU"
    input_box = pygame.Rect(525, 300, 300, 50)
    clock = pygame.time.Clock()
    running = True
    
    # Animationszustand für Karte, die vom Feld zur Ablage fliegt
    animating = False
    anim_start = 0
    anim_duration = 200  # Millisekunden
    anim_src_rect = None
    anim_card_number = None
    pending_change = None  # (row, col)

    GRID_START_X = 50       
    GRID_START_Y = 150
    STAPEL_X = 650         
    DECK_Y = 150           
    ABLAGE_Y = 350         
    OPPONENT_START_X = 950 

    while running:
        mouse_pos = pygame.mouse.get_pos()
        deck_rect = pygame.Rect(STAPEL_X, DECK_Y, CARD_WIDTH, CARD_HEIGHT)
        pile_rect = pygame.Rect(STAPEL_X, ABLAGE_Y, CARD_WIDTH, CARD_HEIGHT)
        
        # --- ZUSTANDS-WECHSEL VOM SERVER PRÜFEN ---
        if server_zustand:
            if server_zustand.get("status") == "end":
                current_state = "END"
            elif server_zustand.get("status") == "game" and current_state == "WAITING":
                current_state = "GAME"
        
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
            
            # --- WAITING ---
            elif current_state == "WAITING" and server_zustand:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    host = server_zustand.get("host")
                    if mein_name == host:
                        spieler_liste = server_zustand.get("spieler", [])
                        if len(spieler_liste) >= 2:
                            start_button = pygame.Rect(500, 600, 350, 60)
                            if start_button.collidepoint(event.pos):
                                sende_aktion("start_game")
            
            # --- IN GAME ---
            elif current_state == "GAME" and server_zustand:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if server_zustand.get("am_zug") == mein_name:
                        # Während einer laufenden Animation keine weiteren Klicks verarbeiten
                        if animating:
                            continue
                        gezogene_karte = server_zustand.get("gezogene_karte")
                        
                        # LINKS-KLICK: Ziehen oder Tauschen
                        if event.button == 1:
                            if not gezogene_karte:
                                if deck_rect.collidepoint(event.pos):
                                    sende_aktion("draw_deck")
                                elif pile_rect.collidepoint(event.pos) and server_zustand.get("ablage") is not None:
                                    sende_aktion("draw_pile")
                            else:
                                if pile_rect.collidepoint(event.pos) and gezogene_karte.get("quelle") == "deck":
                                    sende_aktion("discard")
                                else:
                                    # Tauschen: starte Animation der Feldkarte zur Ablage, dann sende Aktion
                                    for r in range(3):
                                        for c in range(4):
                                            rect = pygame.Rect(GRID_START_X + c * (CARD_WIDTH + SPACING), 
                                                               GRID_START_Y + r * (CARD_HEIGHT + SPACING), 
                                                               CARD_WIDTH, CARD_HEIGHT)
                                            if rect.collidepoint(event.pos):
                                                if not animating:
                                                    try:
                                                        kartendaten = meine_daten['karten'][r][c]
                                                        if kartendaten is None:
                                                            continue
                                                        anim_card_number = kartendaten['nummer']
                                                    except Exception:
                                                        anim_card_number = None

                                                    animating = True
                                                    anim_start = pygame.time.get_ticks()
                                                    anim_src_rect = rect.copy()
                                                    pending_change = (r, c)

                        # RECHTS-KLICK: Wenn Deckkarte gezogen wurde, ablegen und gedrückte Feldkarte umdrehen
                        elif event.button == 3:
                            if gezogene_karte and gezogene_karte.get("quelle") == "deck":
                                for r in range(3):
                                    for c in range(4):
                                        rect = pygame.Rect(GRID_START_X + c * (CARD_WIDTH + SPACING), 
                                                           GRID_START_Y + r * (CARD_HEIGHT + SPACING), 
                                                           CARD_WIDTH, CARD_HEIGHT)
                                        if rect.collidepoint(event.pos):
                                            sende_aktion("discard")
                                            sende_aktion("turn_card", r, c)

        # --- ZEICHNEN ---
        screen.fill(TABLE_COLOR)

        if current_state == "MENU":
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 100))
            screen.blit(title_font.render("SKYJO - LOBBY", True, WHITE), (480, 20))
            screen.blit(large_info_font.render("Bitte gib deinen Namen ein:", True, WHITE), (525, 250))
            pygame.draw.rect(screen, WHITE, input_box, border_radius=8)
            pygame.draw.rect(screen, GOLD, input_box, width=3, border_radius=8)
            screen.blit(large_info_font.render(mein_name, True, (20, 20, 20)), (input_box.x + 15, input_box.y + 8))

        elif current_state == "WAITING":
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 100))
            screen.blit(title_font.render("SKYJO - LOBBY", True, WHITE), (480, 20))
            if server_zustand:
                spieler_liste = server_zustand.get("spieler", [])
                host = server_zustand.get("host")
                txt = f"Spieler in der Lobby: {len(spieler_liste)}/8"
                screen.blit(title_font.render(txt, True, GOLD), (440, 150))
                
                for i, s_name in enumerate(spieler_liste):
                    mark = " (Host)" if s_name == host else ""
                    screen.blit(large_info_font.render(f"• {s_name}{mark}", True, WHITE), (580, 250 + i * 40))
                
                if mein_name == host:
                    start_button = pygame.Rect(500, 600, 350, 60)
                    button_color = ACCENT_GREEN if len(spieler_liste) >= 2 else (100, 100, 100)
                    pygame.draw.rect(screen, button_color, start_button, border_radius=10)
                    pygame.draw.rect(screen, GOLD, start_button, width=3, border_radius=10)
                    btn_text = "SPIEL STARTEN" if len(spieler_liste) >= 2 else "Warte auf 2. Spieler..."
                    txt_surf = large_info_font.render(btn_text, True, (20,20,20) if len(spieler_liste) >= 2 else WHITE)
                    screen.blit(txt_surf, txt_surf.get_rect(center=start_button.center))
                else:
                    screen.blit(large_info_font.render("Warte auf Host...", True, HOVER_COLOR), (580, 620))
            else:
                screen.blit(title_font.render("Verbindung wird hergestellt...", True, WHITE), (380, 250))

        elif current_state == "GAME":
            am_zug = server_zustand.get("am_zug")
            alle_daten = server_zustand.get("spieler_daten", {})
            meine_daten = alle_daten.get(mein_name)
            gezogene_karte = server_zustand.get("gezogene_karte")
            
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 80))
            pygame.draw.line(screen, GOLD, (0, 80), (SCREEN_WIDTH, 80), 2)
            
            zug_text = "DU BIST DRAN!" if am_zug == mein_name else f"Am Zug: {am_zug}"
            color = ACCENT_GREEN if am_zug == mein_name else WHITE
            screen.blit(title_font.render(zug_text, True, color), (480, 10))
            
            if meine_daten:
                screen.blit(large_info_font.render(f"Deine Punkte: {meine_daten['punkte']}", True, WHITE), (50, 25))
                
                screen.blit(large_info_font.render("Dein Raster:", True, GOLD), (GRID_START_X, GRID_START_Y - 40))
                for r, reihe in enumerate(meine_daten["karten"]):
                    for c, karte in enumerate(reihe):
                        if karte is None: continue 
                        
                        rect = pygame.Rect(GRID_START_X + c * (CARD_WIDTH + SPACING), 
                                           GRID_START_Y + r * (CARD_HEIGHT + SPACING), 
                                           CARD_WIDTH, CARD_HEIGHT)
                        
                        draw_shadow(screen, rect)
                        
                        if karte["offen"]:
                            draw_card_front(screen, rect, karte["nummer"], font)
                        else:
                            pygame.draw.rect(screen, CARD_BACK, rect, border_radius=10)
                            pygame.draw.rect(screen, GOLD, rect, width=2, border_radius=10)
                            inner_rect = rect.inflate(-16, -16)
                            pygame.draw.rect(screen, GOLD, inner_rect, width=1, border_radius=5)
                            
                        if am_zug == mein_name and not gezogene_karte and rect.collidepoint(mouse_pos):
                            pygame.draw.rect(screen, HOVER_COLOR, rect, width=4, border_radius=10)
                        elif am_zug == mein_name and gezogene_karte and rect.collidepoint(mouse_pos):
                            pygame.draw.rect(screen, ACCENT_GREEN, rect, width=4, border_radius=10)

            screen.blit(large_info_font.render("Deck", True, GOLD), (STAPEL_X + 25, DECK_Y - 40))
            draw_shadow(screen, deck_rect)
            pygame.draw.rect(screen, CARD_BACK, deck_rect, border_radius=10)
            pygame.draw.rect(screen, GOLD, deck_rect, width=2, border_radius=10)
            inner_rect = deck_rect.inflate(-16, -16)
            pygame.draw.rect(screen, GOLD, inner_rect, width=1, border_radius=5)
            
            if am_zug == mein_name and not gezogene_karte and deck_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, HOVER_COLOR, deck_rect, width=4, border_radius=10)

            if am_zug == mein_name and not gezogene_karte and pile_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, HOVER_COLOR, pile_rect, width=4, border_radius=10)
                
            screen.blit(large_info_font.render("Ablage", True, GOLD), (STAPEL_X - 10, ABLAGE_Y - 40))
            draw_shadow(screen, pile_rect)
            ablage_wert = server_zustand.get("ablage")
            
            if ablage_wert is not None:
                draw_card_front(screen, pile_rect, ablage_wert, font)
            else:
                pygame.draw.rect(screen, (30, 90, 50), pile_rect, border_radius=10)
                pygame.draw.rect(screen, HEADER_COLOR, pile_rect, width=2, border_radius=10)

            if am_zug == mein_name and gezogene_karte and gezogene_karte.get("quelle") == "deck" and pile_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 100, 100), pile_rect, width=4, border_radius=10) 

            # Zeichne fliegende Karte (Animation vom Feld zur Ablage)
            if animating and anim_src_rect is not None and anim_card_number is not None:
                now = pygame.time.get_ticks()
                t = (now - anim_start) / float(anim_duration)
                if t >= 1.0:
                    t = 1.0
                # Lineare Interpolation plus leichter Bogen
                sx, sy = anim_src_rect.x, anim_src_rect.y
                tx, ty = pile_rect.x, pile_rect.y
                ix = int(sx + (tx - sx) * t)
                iy = int(sy + (ty - sy) * t - 40 * math.sin(t * math.pi))
                moving_rect = pygame.Rect(ix, iy, CARD_WIDTH, CARD_HEIGHT)
                draw_shadow(screen, moving_rect)
                draw_card_front(screen, moving_rect, anim_card_number, font)

                if t >= 1.0:
                    animating = False
                    if pending_change:
                        r, c = pending_change
                        sende_aktion("change_card", r, c)
                        pending_change = None

            pygame.draw.line(screen, GOLD, (OPPONENT_START_X - 30, 80), (OPPONENT_START_X - 30, SCREEN_HEIGHT), 2)
            screen.blit(large_info_font.render("Mitspieler", True, GOLD), (OPPONENT_START_X, 100))
            
            alle_daten = server_zustand.get("spieler_daten", {})
            y_offset = 150
            for spieler_name, daten in alle_daten.items():
                if spieler_name != mein_name:
                    g_color = ACCENT_GREEN if am_zug == spieler_name else WHITE
                    screen.blit(info_font.render(f"{spieler_name}", True, g_color), (OPPONENT_START_X, y_offset))
                    screen.blit(info_font.render(f"Punkte: {daten['punkte']}", True, WHITE), (OPPONENT_START_X + 150, y_offset))
                    draw_mini_grid(screen, OPPONENT_START_X, y_offset + 30, daten["karten"], mini_font, g_color, CARD_BACK)
                    y_offset += 100 

            if gezogene_karte and am_zug == mein_name:
                hand_rect = pygame.Rect(mouse_pos[0] - CARD_WIDTH//2, mouse_pos[1] - CARD_HEIGHT//2, CARD_WIDTH, CARD_HEIGHT)
                draw_shadow(screen, hand_rect)
                draw_card_front(screen, hand_rect, gezogene_karte["nummer"], font)

        # --- ENDBILDCHIRM (SCOREBOARD) ---
        elif current_state == "END":
            pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 120))
            pygame.draw.line(screen, GOLD, (0, 120), (SCREEN_WIDTH, 120), 4)
            screen.blit(title_font.render("SPIELENDE!", True, GOLD), (520, 25))
            
            gewinner = server_zustand.get("gewinner", {})
            win_txt = f"Gewinner: {gewinner.get('name')} mit {gewinner.get('punkte')} Punkten!"
            win_surf = title_font.render(win_txt, True, ACCENT_GREEN)
            screen.blit(win_surf, win_surf.get_rect(center=(SCREEN_WIDTH//2, 200)))
            
            alle_daten = server_zustand.get("spieler_daten", {})
            sortierte_spieler = sorted(alle_daten.items(), key=lambda x: x[1]['punkte'])
            
            y_offset = 300
            for platz, (s_name, daten) in enumerate(sortierte_spieler):
                txt = f"{platz + 1}. Platz:  {s_name}   -   {daten['punkte']} Punkte"
                color = GOLD if platz == 0 else WHITE
                txt_surf = font.render(txt, True, color)
                screen.blit(txt_surf, txt_surf.get_rect(center=(SCREEN_WIDTH//2, y_offset)))
                y_offset += 60

        pygame.display.flip()
        clock.tick(30)

    if ws_verbindung:
        ws_verbindung.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()