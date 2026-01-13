
const pdfInput = document.querySelector("#pdf-input");
const uploadBtn = document.querySelector("#pdf-upload-btn");

// Event listener to upload the pdf file
// TODO: Add better error handling
uploadBtn.addEventListener("click", async () => {
    if(pdfInput.files.length == 0 ) {alert("No file given"); return;}
    const pdf      = pdfInput.files[0];
    const formData = new FormData();
    formData.append("file", pdf);

    await fetch("pdf_upload.php", {
        method: "POST",
        body: formData,
    });
});

// TODO: Add more event listeners for every input type