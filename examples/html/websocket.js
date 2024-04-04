// websocket.js

const playButton = document.getElementById("play-button");
let isPlaying = false;

const table = document.getElementById("data-table");

// Create a global variable to hold the WebSocket connection
let socket;

playButton.addEventListener("click", () => {
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
        initializeWebSocket()
    }
    isPlaying = !isPlaying;
});

function initializeWebSocket() {
    socket = new WebSocket("ws://localhost:8080/telemetry");

    socket.addEventListener("open", (event) => {
        console.log("WebSocket connection opened:", event);
    });

    socket.addEventListener("message", async (event) => {
        const data = await event.data.text();
        const sensorReading = JSON.parse(data);

        // Create a new row
        const newRow = document.createElement("tr");
        newRow.innerHTML = `
        <td>${sensorReading.sensorId}</td>
        <td>${sensorReading.temperature}</td>
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