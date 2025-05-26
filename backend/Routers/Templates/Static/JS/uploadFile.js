document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  const fileInput = document.getElementById("fileInput");
  const progressBarContainer = document.getElementById("progressBarContainer");
  const progressBar = document.getElementById("progressBar");
  const progressStatus = document.getElementById("progressStatus");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    
    if (!fileInput.files.length) {
      progressStatus.textContent = "Please select a file!";
      return;
    }

    progressBarContainer.style.display = "block";
    progressStatus.textContent = "Uploading...";

    const formData = new FormData(form);

    try {
      const response = await fetch(form.action, {
        method: form.method,
        body: formData,
      });

      if (!response.ok) {
        throw response.json();
      }

      progressBar.style.width = "100%";
      progressStatus.textContent = "Upload complete!";

      // additional processing if necessary
      // const result = await response.json();
      console.log("Server response:", response);

    } catch (error) {
      console.error("Upload failed:", error.keys);
      progressStatus.textContent = "Upload failed!";
      progressBar.style.backgroundColor = "#ff4444";
    }
  });
});