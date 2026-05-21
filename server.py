import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import game  

app = FastAPI()

class GameServer:
    def __init__(self):
        self.verbindungen = {}  
        self.spiel_instanz = None

    async def sende_spielstand(self):
        if not self.spiel_instanz:
            zustand = {"status": "lobby", "spieler": list(self.verbindungen.values())}
        else:
            spieler_daten = {}
            for p in self.spiel_instanz.player:
                # Baut das Raster für das Frontend (main.py)
                raster = [[{"nummer": k.number, "offen": k.visible} for k in reihe] for reihe in p.cards]
                
                # Holt die Punkte über deine get_score() Funktion aus game.py
                spieler_daten[p.name] = {"punkte": p.get_score(), "karten": raster}
            
            ablage_top = self.spiel_instanz.pile[-1].number if self.spiel_instanz.pile else None
            
            zustand = {
                "status": "game",
                "am_zug": self.spiel_instanz.current_player.name,
                "spieler_daten": spieler_daten,
                "ablage": ablage_top
            }

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
            
            # --- SPIELER TRITT BEI ---
            if aktion == "join":
                name = daten.get("name")
                server.verbindungen[websocket] = name
                
                # Wenn 2 Spieler da sind -> Start!
                if len(server.verbindungen) == 2 and server.spiel_instanz is None:
                    namen = list(server.verbindungen.values())
                    server.spiel_instanz = game.Game(namen)
                    
                    start_karte = server.spiel_instanz.deck.give_card()
                    start_karte.visible = True
                    server.spiel_instanz.pile.append(start_karte)
                    
                await server.sende_spielstand()
                
            # --- SPIELER MACHT EINEN ZUG ---
            elif aktion in ["turn_card", "change_card"] and server.spiel_instanz:
                sender_name = server.verbindungen.get(websocket)
                
                # Prüfen, ob der Spieler dran ist
                if server.spiel_instanz.current_player.name == sender_name:
                    row = daten.get("row")
                    col = daten.get("col")
                    
                    if aktion == "turn_card":
                        # Logik aus game.py aufrufen
                        server.spiel_instanz.current_player.turn_card(row, col)
                        server.spiel_instanz.next_player()
                        
                    elif aktion == "change_card":
                        # Logik aus game.py aufrufen
                        neue_karte = server.spiel_instanz.take_deck()
                        alte_karte, _ = server.spiel_instanz.current_player.change_card(row, col, neue_karte)
                        alte_karte.visible = True
                        server.spiel_instanz.pile.append(alte_karte)
                        server.spiel_instanz.next_player()
                        
                    await server.sende_spielstand()

    except WebSocketDisconnect:
        if websocket in server.verbindungen:
            del server.verbindungen[websocket]
        server.spiel_instanz = None  
        await server.sende_spielstand()

# Das hier erlaubt dir, den Server einfach über den Play-Button zu starten!
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)