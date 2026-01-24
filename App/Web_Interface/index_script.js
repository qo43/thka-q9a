const nameInput       = document.querySelector("#name");
const nationalIdInput = document.querySelector("#national-id");
const dateInput       = document.querySelector("#date");

const fileDisplay   = document.querySelector("#chosen-files");
const pdfInput      = document.querySelector("#pdf-input");
const previewImg    = document.querySelector("#preview-image");
const uploadBtn     = document.querySelector("#submit");
const mainStatusDiv = document.querySelector(".status");
const mainStatus    = document.querySelector("#status-text");
const loading       = document.querySelector(".loading");
const nextBtn       = document.querySelector("#next");

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
        const file = pdfInput.files[i];
        if(file.size === 0){
            displayStatus("File is empty");
            return;
        }

        // if the file size is larger than 10 MBs
        if (file.size > 10 * 1024 * 1024){
            displayStatus("File is too big");
            return;
        }
        
        formData.append("file", pdfInput.files[i]);
    }

    loading.hidden = false;
    
    try { 
        const aiResponse = await fetch("/api/scan", {
            method: "POST",
            body: formData,
        });

        if (!aiResponse.ok) throw new Error(aiResponse.status);
        
        const apiJson = await aiResponse.json();

        if (!apiJson.isValid) {
            displayStatus(apiJson.reason);
            return;
        }
        // ========== If the file is valid ==========
        displayStatus(apiJson.reason, true);
        previewImg.src = window.location.origin + "\\" + apiJson.thumbnailPath;
        nextBtn.hidden = false;

    } catch (e) {
        console.error("[API ERROR]: ", e);
        displayStatus("Internal server error");
        return;
    } finally {
        loading.hidden = true;
    }
});

nextBtn.addEventListener("click", () => {
    window.location.href = "/U_R_F";
});
