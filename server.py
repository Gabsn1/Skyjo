from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# Ein simples Interface zum Testen, das direkt vom Server ausgeliefert wird
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Skyjo Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            ul { list-style-type: none; padding: 0; }
            li { padding: 8px; background: #f0f0f0; margin-bottom: 5px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Skyjo Server ist online! 🟢</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off" placeholder="Nachricht eingeben..."/>
            <button>Senden</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            // Verbindet sich über WebSocket mit dem Server
            var ws = new WebSocket("ws://localhost:8000/ws");
            
            // Wenn eine Nachricht vom Server kommt
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            
            // Wenn du auf "Senden" klickst
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        # Hier speichern wir alle Spieler, die aktuell verbunden sind
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Sendet die Nachricht an alle verbundenen Spieler
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Die Startseite für den Browser
@app.get("/")
async def get():
    return HTMLResponse(html)

# Der WebSocket-Kanal für die Echtzeit-Kommunikation
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Server wartet auf eine Nachricht...
            data = await websocket.receive_text()
            # ...und schickt sie sofort an alle weiter!
            await manager.broadcast(f"Spieler sagt: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("Ein Spieler hat die Verbindung getrennt.")