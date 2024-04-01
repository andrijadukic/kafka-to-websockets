// websocket.js
const socket = new WebSocket('ws://localhost:8080/telemetry');

socket.addEventListener('message', async (event) => {
    const data = await event.data.text();
    const sensorReading = JSON.parse(data);

    // Create a new row
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td>${sensorReading.sensorId}</td>
        <td>${sensorReading.temperature}</td>
    `;

    // Append the row to the table
    const tableBody = document.querySelector('#data-table tbody');
    tableBody.appendChild(newRow);
});
