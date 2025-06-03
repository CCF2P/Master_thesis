document.addEventListener('DOMContentLoaded', function () {
  // Функция для обновления информации о файле
  function updateFileInfo(fileInput, fileInfoElement) {
    if (fileInput.files && fileInput.files.length > 0) {
      const file = fileInput.files[0];
      const fileSize = (file.size / 1024 / 1024).toFixed(2); // Размер в МБ
      console.log(file.name);
      console.log(file.type);
      fileInfoElement.innerHTML = `
            <i class="fas fa-file-medical-alt"></i>
            <div>
              <strong>${file.name}</strong>
              <div>${fileSize} MB • ${file.name.split('.')[1].toUpperCase()}</div>
            </div>
          `;

      // Добавляем визуальную индикацию выбранного файла
      fileInfoElement.closest('.upload-area').classList.add('file-selected');
    } else {
      fileInfoElement.innerHTML = `
            <i class="fas fa-info-circle"></i>
            <span>No file selected</span>
          `;
      fileInfoElement.closest('.upload-area').classList.remove('file-selected');
    }
  }

  // Функция для установки обработчиков загрузки файлов
  function setupFileUpload(uploadAreaId, inputId, fileInfoId) {
    const uploadArea = document.getElementById(uploadAreaId);
    const fileInput = document.getElementById(inputId);
    const fileInfo = document.getElementById(fileInfoId);

    // Обработчик клика по области загрузки
    uploadArea.addEventListener('click', function (e) {
      // Не запускаем выбор файла при клике на информацию о файле
      if (!e.target.closest('.file-info')) {
        fileInput.click();
      }
    });

    // Обработчик изменения файлового ввода
    fileInput.addEventListener('change', function () {
      updateFileInfo(this, fileInfo);
    });
  }

  // Drag and drop functionality
  function setupDragAndDrop(uploadAreaId, inputId, fileInfoId) {
    const uploadArea = document.getElementById(uploadAreaId);
    const fileInput = document.getElementById(inputId);
    const fileInfo = document.getElementById(fileInfoId);

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
      uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
      uploadArea.classList.add('active');
    }

    function unhighlight() {
      uploadArea.classList.remove('active');
    }

    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
      const dt = e.dataTransfer;
      const files = dt.files;

      if (files.length > 0) {
        fileInput.files = files;
        updateFileInfo(fileInput, fileInfo);

        // Trigger change event
        const event = new Event('change');
        fileInput.dispatchEvent(event);
      }
    }
  }

  // Установка обработчиков для всех областей загрузки
  setupFileUpload('uploadArea1', 'image1', 'fileInfo1');
  setupFileUpload('uploadArea2', 'image2', 'fileInfo2');
  setupFileUpload('dbUploadArea', 'fileInput_for_db', 'fileInfoDb');

  // Также устанавливаем drag-and-drop обработчики
  setupDragAndDrop('uploadArea1', 'image1', 'fileInfo1');
  setupDragAndDrop('uploadArea2', 'image2', 'fileInfo2');
  setupDragAndDrop('dbUploadArea', 'fileInput_for_db', 'fileInfoDb');

  // Progress bar simulation
  const forms = document.querySelectorAll('form');
  const progressBar = document.getElementById('progressBar');
  const progressContainer = document.getElementById('progressBarContainer');
  const progressStatus = document.getElementById('progressStatus');
  const progressPercent = document.getElementById('progressPercent');

  forms.forEach(form => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      progressContainer.style.display = 'block';
      progressStatus.textContent = 'Starting analysis...';

      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 5;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          progressStatus.textContent = 'Analysis complete! Generating results...';
          setTimeout(() => {
            progressStatus.innerHTML = '<i class="fas fa-check-circle" style="color: #4CAF50;"></i> Analysis complete! Results are ready.';
            progressBar.style.backgroundColor = '#4CAF50';
          }, 1000);
        }

        progressBar.style.width = progress + '%';
        progressPercent.textContent = Math.round(progress) + '%';

        // Update status messages
        if (progress < 30) {
          progressStatus.textContent = 'Uploading images to server...';
        } else if (progress < 60) {
          progressStatus.textContent = 'Processing image features...';
        } else if (progress < 90) {
          progressStatus.textContent = 'Comparing images and finding matches...';
        }
      }, 200);
    });
  });
});