import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import game  # Importiert eure Spiellogik

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
                spieler_daten[p.name] = {"punkte": p.get_score(), "karten": raster}
            
            ablage_top = self.spiel_instanz.pile[-1].number if self.spiel_instanz.pile else None
            
            zustand = {
                "status": "game",
                "am_zug": self.spiel_instanz.current_player.name,
                "spieler_daten": spieler_daten,
                "ablage": ablage_top
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
                    server.spiel_instanz.action(aktion, daten.get("row"), daten.get("col"))
                    await server.sende_spielstand()

    except WebSocketDisconnect:
        # Spieler hat das Spiel geschlossen
        if websocket in server.verbindungen:
            del server.verbindungen[websocket]
        server.spiel_instanz = None  # Spiel abbrechen
        await server.sende_spielstand()