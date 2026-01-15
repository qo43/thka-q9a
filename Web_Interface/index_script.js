const nameInput       = document.querySelector("#name")
const nationalIdInput = document.querySelector("#national-id");
const dateInput       = document.querySelector("#date");

const fileDisplay   = document.querySelector("#chosen-files")
const pdfInput      = document.querySelector("#pdf-input");
const uploadBtn     = document.querySelector("#submit");
const mainWarning   = document.querySelector("#error-text");

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
        mainWarning.textContent = "Name missing";
        nameInput.focus();
        return false;
    }

    if (!nationalIdInput.value) {
        mainWarning.textContent = "National Id missing";
        nationalIdInput.focus();
        return false;
    }

    if (!dateInput.value) {
        mainWarning.textContent = "date not specified";
        dateInput.focus();
        return false;
    }

    if (pdfInput.files.length == 0) {
        mainWarning.textContent = "No files given";
        return false;
    }

    return true;
};

// Event listener to upload user data
uploadBtn.addEventListener("click", async () => {
    if (!checkFormData()) return;

    const formData = new FormData();
    // TODO: Readd all this later
    // formData.append("name", nameInput.textContent);
    // formData.append("national_id", nationalIdInput.textContent)
    // formData.append("date", date)
    for (let i = 0; i < pdfInput.files.length; ++i) {
        // NOTE: The key is repeated
        formData.append("file", pdfInput.files[i]);
    }


    
        const aiResponse = await fetch("http://localhost:8000/api/scan", {
            method: "POST",
            body: formData,
        });

          // Gotta check up on your aiResponse
          // He could be depressed :(
    try { if (!aiResponse.ok) throw new Error(aiResponse.status); }
    catch (e) {
        console.error("[API ERROR]: ", e);
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

    if (!apiJson.isValid) mainWarning.textContent = apiJson.reason;
});
