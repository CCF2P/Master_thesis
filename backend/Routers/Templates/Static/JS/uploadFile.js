document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm_for_db");
  const fileInput = document.getElementById("fileInput_for_db");
  const progressBarContainer = document.getElementById("progressBarContainer");
  const progressBar = document.getElementById("progressBar");
  const progressStatus = document.getElementById("progressStatus");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    
    if (!fileInput.files.length) {
      progressStatus.textContent = "Пожалуйста, выберите файл";
      return;
    }

    progressBarContainer.style.display = "block";
    progressStatus.textContent = "Загрузка файла...";

    const formData = new FormData(form);

    try {
      const response = await fetch(form.action, {
        method: form.method,
        body: formData,
      });

      if (!response.ok) {
        throw response.json();
      }

      progressBar.style.backgroundColor = "#e63946";
      progressBar.style.width = "100%";
      progressStatus.textContent = "Upload complete!";

      // additional processing if necessary
      const data = await response.text().then((data) => {
        document.open();
        document.writeln(data);
        document.close();
      });
      // console.log("Server response:", response);
    } catch (error) {
      console.error("Ошибка загрузки:", error.then((value) => {
        progressStatus.textContent = `Ошибка загрузки! ${value.detail}`
      }));
      progressBar.style.backgroundColor = "#ff4444";
    }
  });
});
