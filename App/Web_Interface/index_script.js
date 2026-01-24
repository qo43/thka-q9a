const nameInput       = document.querySelector("#name");
const nationalIdInput = document.querySelector("#national-id");
const dateInput       = document.querySelector("#date");

const fileDisplay   = document.querySelector("#chosen-files");
const pdfInput      = document.querySelector("#pdf-input");
const uploadBtn     = document.querySelector("#submit");
const mainStatusDiv = document.querySelector(".status");
const mainStatus    = document.querySelector("#status-text");
const loading       = document.querySelector(".loading");

$(function () {
    $("#date").hijriDatePicker({
        hijri: true,
        format: 'iYYYY-iMM-iDD',
        showTodayButton: true,
        showClear: true,
        showClose: true,
        allowInputToggle: true,
        locale: 'ar-sa'
    });
});

pdfInput.addEventListener("change", (event) => {
    fileDisplay.textContent = "Selected files: ";
    for (let i = 0; i < pdfInput.files.length; ++i) {
        fileDisplay.textContent += pdfInput.files[i].name + " ";
    }
});

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

uploadBtn.addEventListener("click", async () => {
    displayStatus("");

    if (!checkFormData()) return;

    const formData = new FormData();
    formData.append("name", nameInput.value);
    formData.append("national_id", nationalIdInput.value);
    formData.append("date", dateInput.value);

    for (let i = 0; i < pdfInput.files.length; ++i) {
        formData.append("file", pdfInput.files[i]);
    }

    loading.hidden = false;
    
    try { 
        const aiResponse = await fetch("http://localhost:8000/api/scan", {
            method: "POST",
            body: formData,
        });

        if (!aiResponse.ok) throw new Error(aiResponse.status);
        
        const apiJson = await aiResponse.json();

        if (!apiJson.isValid) {
            loading.hidden = true;
            displayStatus(apiJson.reason);
            return;
        }
        
        loading.hidden = true;
        displayStatus(apiJson.reason, true);

    } catch (e) {
        loading.hidden = true;
        console.error("[API ERROR]: ", e);
        displayStatus("Internal server error");
        return;
    }
});
