const askBtn = document.getElementById("askBtn");
const uploadBtn = document.getElementById("uploadBtn");
const clearUploadBtn = document.getElementById("clearUploadBtn");

const questionInput = document.getElementById("questionInput");
const pdfInput = document.getElementById("pdfInput");

const resultCard = document.getElementById("resultCard");
const answerText = document.getElementById("answerText");
const sourcesList = document.getElementById("sourcesList");
const uploadStatus = document.getElementById("uploadStatus");

const ASK_API_URL = "http://127.0.0.1:8000/ask";
const UPLOAD_API_URL = "http://127.0.0.1:8000/upload-pdfs";
const CLEAR_UPLOAD_API_URL = "http://127.0.0.1:8000/clear-upload";
const ACTIVE_COLLECTION_API_URL = "http://127.0.0.1:8000/active-collection";


let activeCollectionName = sessionStorage.getItem("collection_name");
let activeUploadedFiles = JSON.parse(sessionStorage.getItem("uploaded_files") || "[]");
let uploadStateVersion = 0;

async function clearCollection(collectionName) {
    await fetch(CLEAR_UPLOAD_API_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            collection_name: collectionName
        })
    });
}

function updateUploadMode() {
    if (activeCollectionName) {
        clearUploadBtn.classList.remove("hidden");
        if (activeUploadedFiles.length > 0) {
            uploadStatus.textContent = `The current PDF is: ${activeUploadedFiles.join(", ")}`;
        } else {
            uploadStatus.textContent = "The current PDF is loading...";
        }
    } else {
        clearUploadBtn.classList.add("hidden");
        uploadStatus.textContent = "Using default Harvard/WHO nutrition PDFs.";
    }
}

updateUploadMode();

function clearUploadMode() {
    uploadStateVersion += 1;
    activeCollectionName = null;
    activeUploadedFiles = [];
    sessionStorage.removeItem("collection_name");
    sessionStorage.removeItem("uploaded_files");
    updateUploadMode();
}

async function syncActiveCollection() {
    const syncVersion = uploadStateVersion;

    try {
        const response = await fetch(ACTIVE_COLLECTION_API_URL);

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        if (syncVersion !== uploadStateVersion) {
            return;
        }

        if (data.using_uploaded_pdf) {
            activeCollectionName = data.collection_name;
            activeUploadedFiles = data.uploaded_files || [];
            sessionStorage.setItem("collection_name", activeCollectionName);
            sessionStorage.setItem("uploaded_files", JSON.stringify(activeUploadedFiles));
        } else {
            clearUploadMode();
        }

        updateUploadMode();
    } catch (error) {
        console.log("Could not sync active collection:", error);
    }
}

syncActiveCollection();


uploadBtn.addEventListener("click", async () => {
    const files = pdfInput.files;

    if (!files || files.length === 0) {
        alert("Please select at least one PDF file.");
        return;
    }

    const formData = new FormData();

    for (const file of files) {
        formData.append("files", file);
    }

    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading...";
    uploadStatus.textContent = "Uploading and processing PDFs. Please wait...";
    uploadStateVersion += 1;

    try {
        const response = await fetch(UPLOAD_API_URL, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "PDF upload failed. Please check FastAPI server.");
        }

        if (!data.uploaded_files || data.uploaded_files.length === 0) {
            throw new Error("No readable PDF text was found. Please upload a text-based PDF.");
        }

        const previousCollectionName = activeCollectionName;

        activeCollectionName = data.collection_name;
        activeUploadedFiles = data.uploaded_files || [];
        uploadStateVersion += 1;

        sessionStorage.setItem(
            "collection_name",
            activeCollectionName
        );
        sessionStorage.setItem("uploaded_files", JSON.stringify(activeUploadedFiles));

        uploadStatus.textContent =
            `Uploaded successfully. Asking will use only: ${data.uploaded_files.join(", ")} (${data.chunk_count} chunks loaded).`;

        updateUploadMode();

        console.log("ACTIVE COLLECTION:", activeCollectionName);

        if (previousCollectionName && previousCollectionName !== activeCollectionName) {
            await clearCollection(previousCollectionName);
        }

    } catch (error) {
        uploadStatus.textContent = error.message;
        await syncActiveCollection();
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = "Upload PDFs";
    }
});


clearUploadBtn.addEventListener("click", async () => {
    if (!activeCollectionName) {
        return;
    }

    clearUploadBtn.disabled = true;
    clearUploadBtn.textContent = "Clearing...";

    try {
        await clearCollection(activeCollectionName);
    } finally {
        clearUploadMode();
        pdfInput.value = "";
        clearUploadBtn.disabled = false;
        clearUploadBtn.textContent = "Done With Uploaded PDFs";
    }
});

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

        const requestBody = {
            question: question
        };

        // Send uploaded collection if available
        if (activeCollectionName) {
            requestBody.collection_name = activeCollectionName;
        }

        console.log("ASK REQUEST:", requestBody);

        const response = await fetch(ASK_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error("Backend error. Please check FastAPI server.");
        }

        const data = await response.json();

        if (data.collection_name && data.collection_name.startsWith("user_upload_")) {
            activeCollectionName = data.collection_name;
            sessionStorage.setItem("collection_name", activeCollectionName);
            updateUploadMode();
        }

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
