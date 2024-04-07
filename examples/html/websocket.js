// websocket.js

const playButton = document.getElementById("play-button");
let isPlaying = false;

const vinFilterInput = document.getElementById("vinFilter");
const table = document.getElementById("data-table");

// Create a global variable to hold the WebSocket connection
let socket;
const baseUrl = "ws://localhost:8080/telemetry"

playButton.addEventListener("click", () => {
    vinFilterInput.disabled = !isPlaying

    if (isPlaying) {
        // Pause audio (show play icon)
        playButton.textContent = "▶";
        // Fade out the table
        table.classList.remove("fadeIn");

        // Close the websocket connection
        socket.close()
    } else {
        // Play audio (show pause icon)
        playButton.textContent = "❚❚";
        // Fade in the table
        table.classList.add("fadeIn");

        // Initialize the websocket connection
        initializeWebSocket();
    }
    isPlaying = !isPlaying;
});

function initializeWebSocket() {
    let endpoint = baseUrl;

    let vinValue = vinFilterInput.value.trim().toUpperCase();
    if (vinValue.length !== 0) {
        endpoint += `?vin=${vinValue}`;
    }
    socket = new WebSocket(endpoint);

    socket.addEventListener("open", (event) => {
        console.log(`WebSocket connection to ${endpoint} opened:`, event);
    });

    socket.addEventListener("message", async (event) => {
        const data = await event.data.text();
        const sensorReading = JSON.parse(data);

        // Create a new row
        const newRow = document.createElement("tr");
        newRow.innerHTML = `
        <td>${sensorReading.timestamp}</td>
        <td>${sensorReading.vin}</td>
        <td>${sensorReading.tire_position}</td>
        <td>${sensorReading.temperature}</td>
        <td>${sensorReading.pressure}</td>
    `;

        // Append the row to the table
        const tableBody = document.querySelector("#data-table tbody");
        tableBody.appendChild(newRow);
    });

    socket.addEventListener("error", (event) => {
        console.error("WebSocket error:", event);
    });

    socket.addEventListener("close", (event) => {
        console.log("WebSocket connection closed:", event);
    });
}