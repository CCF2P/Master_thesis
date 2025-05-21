document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const progressBarContainer = document.getElementById("progressBarContainer");
    const progressBar = document.getElementById("progressBar");
    const progressStatus = document.getElementById("progressStatus");

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        progressBarContainer.style.display = "block";
        progressStatus.textContent = "Uploading...";
        
        const formData = new FormData(form);
        const xhr = new XMLHttpRequest();
        xhr.open("POST", form.action, true);
        xhr.upload.addEventListener("progress", function (e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBar.style.width = percentComplete + "%";
                progressStatus.textContent = "Uploaded " + percentComplete.toFixed(0) + "%";
            }
        }, false);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
                progressBar.style.width = "100%";
                progressStatus.textContent = "Upload complete!";
            }
        };
        xhr.send(formData);
    });
});
