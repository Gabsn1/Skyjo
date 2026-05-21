import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import game  # Importiert eure originale, unveränderte Spiellogik

app = FastAPI()

class GameServer:
    def __init__(self):
        self.verbindungen = {}  # Speichert: {websocket_objekt: "SpielerName"}
        self.spiel_instanz = None

    async def sende_spielstand(self):
        """Übersetzt die Python-Objekte aus game.py in JSON und sendet sie an alle"""
        if not self.spiel_instanz:
            zustand = {"status": "lobby", "spieler": list(self.verbindungen.values())}
        else:
            spieler_daten = {}
            for p in self.spiel_instanz.player:
                # Baut das 3x4 Raster des Spielers nach
                raster = [[{"nummer": k.number, "offen": k.visible} for k in reihe] for reihe in p.cards]
                
                # TRICK: Wir greifen mit "_Player__get_score()" auf eure private Funktion zu!
                punkte = p._Player__get_score()
                spieler_daten[p.name] = {"punkte": punkte, "karten": raster}
            
            ablage_top = self.spiel_instanz.pile[-1].number if self.spiel_instanz.pile else None
            
            # Prüfen, ob das Spiel zu Ende ist
            ist_ende = self.spiel_instanz.check_end()
            gewinner_name = None
            gewinner_punkte = None
            
            if ist_ende:
                gewinner_name, gewinner_punkte = self.spiel_instanz.get_winner()

            zustand = {
                "status": "game" if not ist_ende else "game_over",
                "am_zug": self.spiel_instanz.current_player.name,
                "spieler_daten": spieler_daten,
                "ablage": ablage_top,
                "gewinner": gewinner_name,
                "gewinner_punkte": gewinner_punkte
            }

        # An alle verbundenen PCs schicken
        for ws in self.verbindungen.keys():
            await ws.send_json(zustand)

server = GameServer()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            daten = await websocket.receive_json()
            aktion = daten.get("aktion")
            
            # 1. Ein Spieler betritt die Lobby
            if aktion == "join":
                name = daten.get("name")
                server.verbindungen[websocket] = name
                
                # Wenn 2 Spieler in der Lobby sind -> Spiel starten!
                if len(server.verbindungen) == 2 and server.spiel_instanz is None:
                    namen = list(server.verbindungen.values())
                    server.spiel_instanz = game.Game(namen)
                    
                    # Erste Startkarte für den Ablagestapel aufdecken
                    start_karte = server.spiel_instanz.deck.give_card()
                    start_karte.visible = True
                    server.spiel_instanz.pile.append(start_karte)
                    
                await server.sende_spielstand()
                
            # 2. Ein Spieler macht einen Zug im Spiel
            elif aktion in ["turn_card", "change_card"] and server.spiel_instanz:
                sender_name = server.verbindungen.get(websocket)
                
                # Nur ausführen, wenn dieser Spieler auch wirklich dran ist
                if server.spiel_instanz.current_player.name == sender_name:
                    row = daten.get("row")
                    col = daten.get("col")
                    
                    # Da die action()-Funktion in game.py fehlt, übernimmt der Server die Logik:
                    if aktion == "turn_card":
                        server.spiel_instanz.current_player.turn_card(row, col)
                        server.spiel_instanz.next_player()
                        
                    elif aktion == "change_card":
                        # Karte vom Deck ziehen
                        neue_karte = server.spiel_instanz.take_deck()
                        # Karte im Raster des Spielers austauschen
                        alte_karte, _ = server.spiel_instanz.current_player.change_card(row, col, neue_karte)
                        # Alte Karte offen auf den Ablagestapel werfen
                        alte_karte.visible = True
                        server.spiel_instanz.pile.append(alte_karte)
                        
                        server.spiel_instanz.next_player()
                        
                    await server.sende_spielstand()

    except WebSocketDisconnect:
        # Spieler hat das Spiel geschlossen
        if websocket in server.verbindungen:
            del server.verbindungen[websocket]
        server.spiel_instanz = None  # Spiel abbrechen
        await server.sende_spielstand()