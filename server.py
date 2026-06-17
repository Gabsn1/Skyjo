import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import game  

app = FastAPI()

class GameServer:
    def __init__(self):
        self.verbindungen = {}  
        self.spiel_instanz = None
        
        # Das Kurzzeitgedächtnis für die aufgehobene Karte
        self.gezogene_karte = None
        self.karten_quelle = None 

    async def sende_spielstand(self):
        if not self.spiel_instanz:
            spieler_liste = list(self.verbindungen.values())
            host = spieler_liste[0] if spieler_liste else None
            zustand = {"status": "lobby", "spieler": spieler_liste, "host": host}
        else:
            is_end = False
            gewinner_info = None
            
            # PRÜFEN: Hat jemand das Spiel beendet (alle Karten offen)?
            if self.spiel_instanz.check_end():
                is_end = True
                
                # Bei Spielende: Alle verbleibenden Karten aufdecken für die Endabrechnung
                for p in self.spiel_instanz.player:
                    for row in p.cards:
                        for k in row:
                            if k is not None:
                                k.visible = True
                                
                # Gewinner aus der game.py holen
                win_name, win_score = self.spiel_instanz.get_winner()
                gewinner_info = {"name": win_name, "punkte": win_score}

            spieler_daten = {}
            for p in self.spiel_instanz.player:
                # Baut das Raster (inklusive der Lücken durch gelöschte Spalten)
                raster = [[{"nummer": k.number, "offen": k.visible} if k is not None else None for k in reihe] for reihe in p.cards]
                spieler_daten[p.name] = {"punkte": p.get_score(), "karten": raster}
            
            ablage_top = self.spiel_instanz.pile[-1].number if self.spiel_instanz.pile else None
            
            # Die Karte an der Maus verpacken
            hand_karte_json = None
            if self.gezogene_karte:
                hand_karte_json = {
                    "nummer": self.gezogene_karte.number,
                    "quelle": self.karten_quelle
                }
            
            zustand = {
                "status": "end" if is_end else "game",
                "host": list(self.verbindungen.values())[0] if self.verbindungen else "",
                "am_zug": self.spiel_instanz.current_player.name,
                "spieler_daten": spieler_daten,
                "ablage": ablage_top,
                "gezogene_karte": hand_karte_json
            }
            
            # Wenn das Spiel vorbei ist, die Infos mitschicken
            if is_end:
                zustand["gewinner"] = gewinner_info

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
            
            if aktion == "join":
                name = daten.get("name")
                server.verbindungen[websocket] = name
                await server.sende_spielstand()
            
            elif aktion == "start_game" and server.spiel_instanz is None:
                if 2 <= len(server.verbindungen) <= 8:
                    namen = list(server.verbindungen.values())
                    server.spiel_instanz = game.Game(namen)
                    
                    start_karte = server.spiel_instanz.deck.give_card()
                    start_karte.visible = True
                    server.spiel_instanz.pile.append(start_karte)
                    
                await server.sende_spielstand()
                
            elif server.spiel_instanz:
                sender_name = server.verbindungen.get(websocket)
                
                if server.spiel_instanz.current_player.name == sender_name:
                    row = daten.get("row")
                    col = daten.get("col")
                    player = server.spiel_instanz.current_player
                    
                    # 1. KARTE ZIEHEN
                    if aktion == "draw_deck" and not server.gezogene_karte:
                        server.gezogene_karte = server.spiel_instanz.take_deck()
                        server.karten_quelle = "deck"
                        
                    elif aktion == "draw_pile" and not server.gezogene_karte:
                        server.gezogene_karte = server.spiel_instanz.take_pile()
                        server.karten_quelle = "pile"
                    
                    # 2. KARTE ABLEGEN (Austauschen)
                    elif aktion == "change_card" and server.gezogene_karte:
                        if row is not None and col is not None:
                            # Darf nicht in eine gelöschte Spalte gelegt werden!
                            if player.cards[row][col] is not None:
                                alte_karte, _ = player.change_card(row, col, server.gezogene_karte)
                                alte_karte.visible = True
                                server.spiel_instanz.pile.append(alte_karte)
                                server.gezogene_karte = None
                                server.karten_quelle = None
                                server.spiel_instanz.next_player()
                            
                    # 3. KARTE WEGWERFEN
                    elif aktion == "discard" and server.gezogene_karte and server.karten_quelle == "deck":
                        server.gezogene_karte.visible = True
                        server.spiel_instanz.pile.append(server.gezogene_karte)
                        server.gezogene_karte = None
                        server.karten_quelle = None
                        
                    # 4. EIGENE KARTE AUFDECKEN
                    elif aktion == "turn_card" and not server.gezogene_karte:
                        if row is not None and col is not None:
                            if player.cards[row][col] is not None and not player.cards[row][col].visible:
                                player.turn_card(row, col)
                                server.spiel_instanz.next_player()

                    await server.sende_spielstand()

    except WebSocketDisconnect:
        if websocket in server.verbindungen:
            del server.verbindungen[websocket]
        server.spiel_instanz = None  
        server.gezogene_karte = None
        await server.sende_spielstand()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)