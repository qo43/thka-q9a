const nameInput       = document.querySelector("#name")
const nationalIdInput = document.querySelector("#national-id");
const dateInput       = document.querySelector("#date");

const fileDisplay  = document.querySelector("#chosen-files")
const pdfInput     = document.querySelector("#pdf-input");
const uploadBtn    = document.querySelector("#submit");
const mainWarning  = document.querySelector("#error-text");

pdfInput.addEventListener("change", (event) => {
    fileDisplay.textContent = "Selected files: ";
    for(let i = 0; i < pdfInput.files.length; ++i){
        fileDisplay.textContent += pdfInput.files[i].name + " ";
    }
});


// Returns false if not all form data is complete
// and sets the warning message
const checkFormData = () => {
    if(!nameInput.value){
        mainWarning.textContent = "Name missing";
        return false;
    }

    if(!nationalIdInput.value){
        mainWarning.textContent = "National Id missing";
        return false;
    }
    
    if(!dateInput.value){
        mainWarning.textContent = "date not specified";
        return false;
    }

    if(pdfInput.files.length == 0){
        mainWarning.textContent = "No files given";
        return false;
    }

    return true;
};

// Event listener to upload user data
uploadBtn.addEventListener("click", async () => {
    if(!checkFormData()) return;
    
    formData.append("name", nameInput.textContent);
    formData.append("national_id", nationalIdInput.textContent)
    formData.append("date", date)

    const formData = new FormData();
    for(let i = 0; i < pdfInput.files.length; ++i){
        // NOTE: The key is repeated
        formData.append("files", pdfInput.files[i]);
    }


    const response = await fetch("http://localhost:8000/api/scan", {
        method: "POST",
        body: formData,
    });

    // Gotta check up on your response
    // He could be depressed :(
    if(!response.ok) throw new Error(response.status);
});
