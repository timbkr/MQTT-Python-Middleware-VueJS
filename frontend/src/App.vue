<script setup lang="ts">
import { onMounted, ref } from 'vue';
import DeviceItem from './components/DeviceItem.vue';

// const devices = (await res.json()) as import("../contracts/types").DeviceState[];

// interface Device {
//   deviceID: string;
//   [key: string]: any;
// }

const devices = ref<unknown[]>([]);
const isLoading = ref(true);
const error = ref<string | undefined>()

onMounted(async () => {
  // Fetche API (Snapshot aller Geräte)
  try {
    const res = await fetch("/api/devices");
    if (!res.ok) {
      throw new Error("HTTP Fehler! Status: " + res.status)
    }
    const devicesObj = await res.json();
    devices.value = Object.entries(devicesObj).map(([id, details]) => ({
      id,
      ...details
    }))
  } catch (err) {
    console.error("Fehler beim Abrufen der Geräte: ", err);
    if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = 'Unbekannter Fehler beim Laden der Daten.';
    }
  }
  finally {
    // await new Promise(resolve => { setTimeout(resolve, 500) })
    isLoading.value = false;
  }

  // Websocket Connection für Echtzeitupdates (nur geänderte Werte)
  const ws = new WebSocket("ws://localhost:8080/ws");

  ws.onopen = () => console.log("wsOnopen");

  ws.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data)
      console.log(data);

      //finde und überschreibe Gerät mit neuen Werten
      const index = devices.value.findIndex(elem => elem.id === data.deviceId)
      if (data.type === 'telemetry') {
        if (index !== -1) {
          Object.assign(devices.value[index], data.data)
        }
        else {
          devices.value.push({ id: data.deviceId, ...data.data })
        }
      }
    } catch (e) {
      console.error("Fehler beim Parsen der WS-Nachricht:", e)
    }
  }

  ws.onclose = (ev) => console.log("wsOnclose " + ev);


})
</script>

<template>
  <h1>MQTT ➡ Python Middleware (REST + WS) ➡ Vue.js Frontend</h1>
  <p v-if="isLoading">⏳ Lade Geräte..</p>
  <p v-else-if="error" class="error">❌ Fehler: {{ error }}</p>
  <div v-else>
    <!-- <pre>devices: {{ devices }} </pre> -->
    <div v-for="device in devices" :key="device.id" class="deviceList">
      <DeviceItem :device="device"></DeviceItem>
    </div>
  </div>




</template>

<style scoped>
h1 {
  text-align: center;
  padding-bottom: 10px;
}

.error {
  color: red;
  font-weight: bold;
}

.deviceList {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* justify-content: center; */
}
</style>
