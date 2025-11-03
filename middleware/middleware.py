import sys, asyncio
import json
from typing import Any, Dict
from aiohttp import web, WSMsgType
from datetime import datetime, timezone
from aiomqtt import Client as MQTTClient, MqttError

import os
from pathlib import Path

# ---- Windows only: Event-Loop-Policy umstellen ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# -------------------- Konfig --------------------
BROKER_HOST = os.environ.get("BROKER_HOST", "localhost")
BROKER_PORT = int(os.environ.get("BROKER_PORT", "1883"))
MQTT_TOPIC = "sensors/+/telemetry"  # + = deviceId

STATIC_DIR = Path(os.environ.get("STATIC_DIR", "./static")).resolve()
INDEX_FILE = STATIC_DIR / "index.html"

# -------------------- In-Memory State --------------------
device_states = {
    "tor-1": {"temperature": 21.5, "status": "open", "updated_at": "2025-11-02T12:00:00Z"},
    "tor-2": {"temperature": 19.8, "status": "closed", "updated_at": "2025-11-02T12:01:00Z"},
    #"tor-3": {"temperature": 20.3, "status": "open", "updated_at": "2025-11-02T12:01:00Z"},
}

# -------------------- Web App --------------------
app = web.Application()

#async def hello(request): # GET /
#    return web.Response(text="Hello from my Python Middleware aiohttp server!")

async def get_devices(request): # GET /api/devices
    return web.json_response(device_states)

async def get_device(request: web.Request):  # GET /api/devices/{deviceId}
    device_id = request.match_info['deviceId']
    if device_id not in device_states:
        raise web.HTTPNotFound(text=f"Device {device_id} not found")
    return web.json_response(device_states[device_id])

app.add_routes([
 #   web.get("/", hello),
    web.get("/api/devices", get_devices),
    web.get("/api/devices/{deviceId}", get_device),
])

# ---- Static + SPA ----
if STATIC_DIR.exists():                    # Vite-Assets
    app.router.add_static("/assets", STATIC_DIR / "assets", show_index=False)

async def _index(_):
    if INDEX_FILE.exists():
        return web.FileResponse(INDEX_FILE)
    return web.Response(text="Frontend build not found", status=404)

app.router.add_get("/", _index)            # Startseite

# SPA-Fallback: nach allen API/WS-Routen registrieren!
async def _spa_fallback(request):
    p = request.path
    if p.startswith("/api") or p.startswith("/ws"):
        raise web.HTTPNotFound()
    return await _index(request)

app.router.add_get("/{tail:.*}", _spa_fallback)


#--------------------- WEBSOCKET ------------------------

CLIENTS: set[web.WebSocketResponse] = set()

async def websocket_handler(request):
    ws = web.WebSocketResponse(
        heartbeat=25,   # hält die Verbindung frisch (Ping/Pong)
        compress=True,  # spart Bandbreite
        max_msg_size=2**20)
    await ws.prepare(request)

    CLIENTS.add(ws)

    # optional: einfache Begrüßung
    await ws.send_json({"v": 1, "type": "hello", "ts": None, "data": {"server": "aiohttp", "version": "0.1.0"}})

    #Empfangsschleife
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    await ws.send_str(msg.data + '/answer')
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
    finally:
        CLIENTS.discard(ws)

    print('websocket connection closed')

    return ws

app.add_routes([web.get('/ws', websocket_handler)])

async def broadcast(event: dict):
    if not CLIENTS:
        return
    deadConnections = []
    for client in CLIENTS:
        try:
            await client.send_json(event)
        except Exception:
            deadConnections.append(client)

    for d in deadConnections:
            CLIENTS.discard(d)

# ------------------------------- MQTT ---------------------------------

# -------------------- MQTT Normalisierung + device_states aktualisieren --------------------
def normalize_and_apply(device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Erwartet:
    {
      "ts": "2025-11-03T12:34:56Z",
      "deviceId": "tor-1",
      "metrics": {"tempC": 22.4, "doorState": "open"}
    }
    """
    ts = payload.get("ts") or datetime.now(timezone.utc).isoformat()
    m = payload.get("metrics") or {}
    temp = m.get("tempC")
    door = m.get("doorState")

    current = device_states.get(device_id, {})
    if temp is not None:
        current["temperature"] = float(temp)
    if door is not None:
        current["status"] = str(door)
    current["updated_at"] = ts

    device_states[device_id] = current
    return current

# -------------------- MQTT Subscriber (mit Reconnect) --------------------
async def mqtt_consumer_task(_app):
    print(f"[MQTT] Connecting to {BROKER_HOST}:{BROKER_PORT}")

    while True:
        try:
            async with MQTTClient(BROKER_HOST, BROKER_PORT) as client:
                await client.subscribe(MQTT_TOPIC)
                print(f"[MQTT] ✓ Subscribed to {MQTT_TOPIC}")

                async for msg in client.messages:
                    topic = str(msg.topic)
                    payload = msg.payload.decode("utf-8")
                    print(f"[MQTT] {topic} => {payload}")

                    # Device ID extrahieren
                    device_id = topic.split("/")[1]

                    # JSON parsen
                    data = json.loads(payload)
                    delta = normalize_and_apply(device_id, data)

                    # An WebSocket-Clients senden
                    await broadcast({"type": "telemetry", "deviceId": device_id, "data": delta})

        except Exception as e:
            print(f"[MQTT] Error: {e} → retry in 3s")
            await asyncio.sleep(3)

# -------------------- Startup / Cleanup --------------------
async def on_startup(app: web.Application):
    print("[APP] on_startup -> MQTT-Task wird gestartet")
    app["mqtt_task"] = asyncio.create_task(mqtt_consumer_task(app))


async def on_cleanup(app: web.Application):
    t = app.get("mqtt_task")
    if t:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

# -------------------- Run --------------------
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)