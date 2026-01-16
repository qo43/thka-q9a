const nameInput       = document.querySelector("#name")
const nationalIdInput = document.querySelector("#national-id");
const dateInput       = document.querySelector("#date");

const fileDisplay   = document.querySelector("#chosen-files")
const pdfInput      = document.querySelector("#pdf-input");
const uploadBtn     = document.querySelector("#submit");
const mainStatusDiv = document.querySelector(".status");
const mainStatus    = document.querySelector("#status-text");
const loading       = document.querySelector(".loading");


// === When files are picked, display their names ===
pdfInput.addEventListener("change", (event) => {
    fileDisplay.textContent = "Selected files: ";
    for (let i = 0; i < pdfInput.files.length; ++i) {
        fileDisplay.textContent += pdfInput.files[i].name + " ";
    }
});


// Returns false if not all form data is complete
// and sets focus + the warning message
const checkFormData = () => {
    if (!nameInput.value) {
        mainStatus.textContent = "Name missing";
        nameInput.focus();
        return false;
    }

    if (!nationalIdInput.value) {
        mainStatus.textContent = "National Id missing";
        nationalIdInput.focus();
        return false;
    }

    if (!dateInput.value) {
        mainStatus.textContent = "date not specified";
        dateInput.focus();
        return false;
    }

    if (pdfInput.files.length == 0) {
        mainStatus.textContent = "No files given";
        return false;
    }

    return true;
};

const changeStatusColor = (isSuccess) => {
    mainStatusDiv.classList.toggle("error", !isSuccess);
    mainStatusDiv.classList.toggle("success", isSuccess);
};

const displayStatus = (text, isSuccess = false) => {
    mainStatus.textContent = text;
    changeStatusColor(isSuccess);
};


// Event listener to upload user data
uploadBtn.addEventListener("click", async () => {
    displayStatus("") // Reset status and color

    if (!checkFormData()) return;

    const formData = new FormData();
    // TODO: Readd all this later
    formData.append("name", nameInput.textContent);
    formData.append("national_id", nationalIdInput.textContent)
    formData.append("date", date)

    for (let i = 0; i < pdfInput.files.length; ++i) {
        // NOTE: The key is repeated
        formData.append("file", pdfInput.files[i]);
    }

    loading.hidden = false;
    const aiResponse = await fetch("http://localhost:8000/api/scan", {
        method: "POST",
        body: formData,
    });

    // Gotta check up on your aiResponse
    // He could be depressed :(
    try { 
        if (!aiResponse.ok) throw new Error(aiResponse.status);
    } catch (e) {
        loading.hidden = true;
        console.error("[API ERROR]: ", e);
        displayStatus("Internal server error");
        return;
    }

    /* ============= JSON FIELDS =============
        caseYear
        debugScore
        isValid 
        reason
        text
    */

    const apiJson = await aiResponse.json();

    if (!apiJson.isValid) {
        loading.hidden = true;
        displayStatus(apiJson.reason);
        return;
    }
    
    // SUCCESS!
    loading.hidden = true;
    displayStatus(apiJson.reason, true);

});
