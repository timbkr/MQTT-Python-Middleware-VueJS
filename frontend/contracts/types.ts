//für Orientierung + fürs Frontend nutzbar

export type DoorState = "open" | "closed" | "moving" | "error";

export type Telemetry = {
  deviceId: string;       // z.B. "gate-001"
  ts: string;             // ISO 8601, z.B. "2025-11-02T12:00:00Z"
  metrics: {
    tempC?: number;
    humidity?: number;    // 0..100
    doorState?: DoorState;
  };
};

export type DeviceState = {
  deviceId: string;
  lastSeen: string;       // ISO 8601
  lastTelemetry: Telemetry;
};

export type WsEvent =
  | { type: "snapshot"; data: DeviceState[] }
  | { type: "telemetry"; data: Telemetry };
