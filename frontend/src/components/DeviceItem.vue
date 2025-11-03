<script setup lang="ts">
const props = defineProps(['device'])

function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';

    const date = new Date(timestamp);

    // Intl.DateTimeFormat für ein schönes lokales Format
    return new Intl.DateTimeFormat('de-DE', {
        dateStyle: 'short',     // z.B. 02.11.25
        timeStyle: 'short',    // z.B. 12:05:00
    }).format(date);
}
</script>

<template>
    <div class="deviceItem">
        <span>Gerät: {{ device.id }}</span>
        <span>Temp: {{ device.temperature.toFixed(1) }}°C</span>
        <!-- <span>Luftf.: {{ device.humidity }}°C</span> -->
        <span>Status: <span :class="device.status === 'open' ? 'statusOpen' : 'statusClosed'">{{ device.status }}</span>
        </span>
        <!-- <span :class="{
            'statusOpen': device.status === 'open',
            'statusClosed': device.status === 'closed',
        }">Status: {{ device.status }}</span> -->
        <span>Letztes Update: {{ formatTimestamp(device.updated_at) }}</span>
    </div>
</template>

<style scoped>
.deviceItem {
    background-color: rgb(2, 47, 47);
    border: 1px solid rgb(6, 40, 108);
    display: flex;
    justify-content: space-around;
    width: 60vw;

    margin: 10px 2vw;
    padding: 20px 0;
    border-radius: 10px;
}

.deviceItem span {
    padding: 0 20px;
}

span.statusOpen {
    background-color: green;
    border-radius: 5px;
    padding: 6px 12px;
    border: 1px solid white;
    margin-left: 2px;
}

span.statusClosed {
    background-color: red;
    border-radius: 5px;
    padding: 6px;
    border: 1px solid white;
    margin-left: 2px;

}
</style>