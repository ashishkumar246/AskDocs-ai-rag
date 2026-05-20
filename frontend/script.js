const askBtn = document.getElementById("askBtn");
const questionInput = document.getElementById("questionInput");
const resultCard = document.getElementById("resultCard");
const answerText = document.getElementById("answerText");
const sourcesList = document.getElementById("sourcesList");

const API_URL = "http://127.0.0.1:8000/ask";

askBtn.addEventListener("click", async () => {
    const question = questionInput.value.trim();

    if (!question) {
        alert("Please enter a question.");
        return;
    }

    askBtn.disabled = true;
    askBtn.textContent = "Thinking...";
    resultCard.classList.add("hidden");

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        if (!response.ok) {
            throw new Error("Backend error. Please check FastAPI server.");
        }

        const data = await response.json();

        answerText.textContent = data.answer;

        sourcesList.innerHTML = "";

        if (data.sources_used && data.sources_used.length > 0) {
            data.sources_used.forEach((source) => {
                const sourceDiv = document.createElement("div");
                sourceDiv.className = "source-item";

                sourceDiv.innerHTML = `
                    <strong>PDF:</strong> ${source.source_file}<br>
                    <strong>Page:</strong> ${source.page_number}<br>
                    <strong>Relevance Distance:</strong> ${source.distance}
                `;

                sourcesList.appendChild(sourceDiv);
            });
        } else {
            sourcesList.innerHTML = "<p>No sources found.</p>";
        }

        resultCard.classList.remove("hidden");

    } catch (error) {
        alert(error.message);
    } finally {
        askBtn.disabled = false;
        askBtn.textContent = "Ask Question";
    }
});