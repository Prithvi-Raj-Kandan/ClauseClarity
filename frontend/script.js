const chatBox = document.getElementById("chatBox");
const analysisBox = document.getElementById("analysisBox");

// Send Message
function sendMessage() {
    const input = document.getElementById("userInput");
    const text = input.value.trim();

    if (text === "") return;

    addMessage(text, "user");
    input.value = "";

    // Dummy AI response (replace with API later)
    setTimeout(() => {
        addMessage("Analyzing your query...", "bot");

        // Show something in analysis panel
        updateAnalysis("AI is processing your request...\n\nKey points will appear here.");
    }, 500);
}

// Add chat message
function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerText = text;

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Update right panel
function updateAnalysis(content) {
    analysisBox.innerText = content;
}

// File Upload Handling
document.getElementById("fileInput").addEventListener("change", function () {
    const file = this.files[0];

    if (!file) return;

    addMessage(`Uploaded file: ${file.name}`, "user");

    // Placeholder logic
    updateAnalysis(`Analyzing file: ${file.name}...\n\n- Extracting clauses\n- Checking risks\n- Generating summary`);

    // Later → send to backend
    /*
    const formData = new FormData();
    formData.append("file", file);

    fetch("UPLOAD_API_URL", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        updateAnalysis(data.analysis);
    });
    */
});