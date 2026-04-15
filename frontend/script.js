const chatBox = document.getElementById("chatBox");
const analysisBox = document.getElementById("analysisBox");

const API_BASE = "http://127.0.0.1:8000";

let currentAgreementText = "";
let currentAnalysis = "";

// Send Message to Chat API
async function sendMessage() {
    const input = document.getElementById("userInput");
    const text = input.value.trim();

    if (text === "") return;

    if (!currentAgreementText) {
        addMessage("Please upload an agreement first.", "bot");
        return;
    }

    addMessage(text, "user");
    input.value = "";

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: text,
                agreement_text: currentAgreementText,
                analysis_summary: currentAnalysis,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            addMessage(`Error: ${error.detail || "Unknown error"}`, "bot");
            return;
        }

        const data = await response.json();
        addMessage(data.answer, "bot");
    } catch (error) {
        addMessage(`Connection error: ${error.message}`, "bot");
    }
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
document.getElementById("fileInput").addEventListener("change", async function () {
    const file = this.files[0];

    if (!file) return;

    addMessage(`Uploading file: ${file.name}...`, "user");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            addMessage(`Upload failed: ${error.detail || "Unknown error"}`, "bot");
            return;
        }

        const data = await response.json();

        // Store for chat
        currentAgreementText = data.agreement_text;
        currentAnalysis = JSON.stringify(data.analysis.summary);

        addMessage(`✅ File analyzed successfully!`, "bot");

        // Display analysis
        const analysis = data.analysis;
        const riskLevel = analysis.summary.risk_level.toUpperCase();
        const missingCount = analysis.summary.total_missing_count;
        const avgSim = analysis.summary.average_similarity;

        const analysisText = `
📋 ANALYSIS REPORT
━━━━━━━━━━━━━━━━
Risk Level: ${riskLevel}
Missing Categories: ${missingCount}
Average Similarity: ${avgSim}
High-Risk Flags: ${analysis.summary.high_risk_flag_count || 0}

Missing Categories:
${analysis.missing_categories.length > 0 ? analysis.missing_categories.join("\n") : "None - All categories found!"}

High-Risk Flags:
${analysis.high_risk_flags && analysis.high_risk_flags.length > 0
    ? analysis.high_risk_flags.map((f) => `- ${f.flag}: ${f.reason}`).join("\n")
    : "None"}

Semantic Similarity Scores:
${Object.entries(analysis.semantic_similarity)
    .map(([cat, score]) => `${cat}: ${score}`)
    .join("\n")}
        `.trim();

        updateAnalysis(analysisText);
    } catch (error) {
        addMessage(`Connection error: ${error.message}`, "bot");
    }
});