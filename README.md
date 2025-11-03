# IoT Demo Prototype – Overview

## Architekturdiagramm
![](assets/Architekturdiagramm-IOT-Python-Vue-Mermaid%20Chart.png)

## Architekturdiagramm (detailliert)
![](assets/Architekturdiagramm-Detailliert-IOT-Python-Vue-Mermaid%20Chart.png)


## Sequenzdiagramm
![](assets/Sequendiagramm-IOT-Python-Vue-Mermaid%20Chart.png)

Windows-Mosquitto Service stoppen:
(ADMIN)
Stop-Service mosquitto

# Oder permanent deaktivieren:
Set-Service mosquitto -StartupType Disabled


## Dev Setup (um lokal zu entwickeln aber mqtt broker als Container):
docker compose -f compose.dev.yaml up

## Run Commands:
MQTT Broker Starten:

    docker compose up --build
    docker compose logs -f mosquitto

Shell im laufenden Container:
    docker compose exec mosquitto sh

Subscriben
    mosquitto_sub -h mosquitto -p 1883 -t 'sensors/#' -v

Publishen:
    mosquitto_pub -h mosquitto -p 1883 -t sensors/test -m '{"hello":"world"}'

im Terminal:
# 1) Telemetrie senden
mosquitto_pub -h mosquitto -p 1883 -t sensors/tor-1/telemetry -m '{"metrics":{"tempC":22.4,"doorState":"open"}}'
mosquitto_pub -h mosquitto -p 1883 -t sensors/tor-1/telemetry -m '{"metrics":{"tempC":22.4,"doorState":"closed"}}'

# 2) Zweites Gerät
mosquitto_pub -h mosquitto -p 1883 -t sensors/tor-2/telemetry -m '{"metrics":{"tempC":19.1,"doorState":"closed"}}'
mosquitto_pub -h mosquitto -p 1883 -t sensors/tor-2/telemetry -m '{"metrics":{"tempC":19.1,"doorState":"open"}}'

# 3) Drittes Gerät
mosquitto_pub -h mosquitto -p 1883 -t sensors/tor-3/telemetry -m '{"metrics":{"tempC":22.4,"doorState":"open"}}'
mosquitto_pub -h mosquitto -p 1883 -t sensors/tor-3/telemetry -m '{"metrics":{"tempC":22.4,"doorState":"closed"}}'


# 3) (optional) Retained-Status veröffentlichen
mqtt_pub -h mosquitto -p 1883 -r -t sensors/tor-1/state -m "{\"status\":\"open\",\"updated_at\":\"2025-11-03T12:40:00Z\"}"

## 🎯 Ziel
Ein einfacher End-to-End-Prototyp, der zeigt:
> "IoT-System mit **Python Middleware (aiohttp)**, **MQTT** und einem **Vue-Frontend** – asynchron und containerisiert (Docker)."

---

## ⚙️ Architekturüberblick

**Datenfluss:**
1. 🛰️ **IoT-Gerät** sendet `Telemetry` per MQTT → Broker
2. 🧠 **Middleware (Python aiohttp)** empfängt MQTT-Nachricht  
   - speichert letzten Zustand (`DeviceState`)  
   - verteilt Live-Events per **WebSocket**  
   - liefert Snapshot per **REST-API**
3. 💻 **Frontend (Vue)**  
   - zeigt alle Geräte (Snapshot)  
   - aktualisiert in Echtzeit über WebSocket

---

## 🧾 Daten-Schemas (vereinheitlicht)

```ts
// Telemetry (MQTT + WS)
{
  deviceId: "gate-001",
  ts: "2025-11-02T12:00:00Z",
  metrics: { tempC: 21.3, humidity: 48.2, doorState: "open" }
}

// DeviceState (REST + WS snapshot)
{
  deviceId: "gate-001",
  lastSeen: "2025-11-02T12:00:00Z",
  lastTelemetry: { ...Telemetry }
}

// WS Event
{ type: "snapshot", data: DeviceState[] }
{ type: "telemetry", data: Telemetry }
```

**MQTT Topics:**
```
sensors/{deviceId}/telemetry    # aktuelle Werte
sensors/{deviceId}/state        # optional retained status
```

**REST + WS:**
```
GET /api/sensors    → device_states[] (snapshot)
WS /ws/events       → WsEvent (telemetry)
```

