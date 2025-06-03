document.addEventListener('DOMContentLoaded', function () {
  // Функция для обновления информации о файле
  function updateFileInfo(fileInput, fileInfoElement, removeBtn) {
    if (fileInput.files && fileInput.files.length > 0) {
      const file = fileInput.files[0];
      const fileSize = (file.size / 1024 / 1024).toFixed(2); // Размер в МБ
      let tmp = file.name.split('.')[1];
      let fileType = 'UNKNOWN';
      console.log(tmp);
      if (tmp)
        fileType = tmp.toUpperCase();

      fileInfoElement.innerHTML = `
            <div class="file-details">
              <div class="file-name">${file.name}</div>
              <div class="file-meta">${fileSize} MB • ${fileType}</div>
            </div>
            <button class="remove-btn">
              <img src="/Static/Pictures/trash.png">
            </button>
          `;

      // Показываем кнопку удаления
      if (removeBtn) removeBtn.style.display = 'block';

      // Добавляем визуальную индикацию выбранного файла
      fileInfoElement.closest('.upload-area').classList.add('file-selected');

      // Добавляем обработчик для кнопки удаления
      const newRemoveBtn = fileInfoElement.querySelector('.remove-btn');
      if (newRemoveBtn) {
        newRemoveBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          resetFileInput(fileInput, fileInfoElement, removeBtn);
        });
      }
    } else {
      fileInfoElement.innerHTML = `
            <div class="file-details">
              <span class="file-name">No file selected</span>
            </div>
          `;
      fileInfoElement.closest('.upload-area').classList.remove('file-selected');
      if (removeBtn) removeBtn.style.display = 'none';
    }
  }

  // Функция для сброса выбранного файла
  function resetFileInput(fileInput, fileInfoElement, removeBtn) {
    fileInput.value = '';
    updateFileInfo(fileInput, fileInfoElement, removeBtn);
  }

  // Функция для установки обработчиков загрузки файлов
  function setupFileUpload(uploadAreaId, inputId, fileInfoId, removeBtnId) {
    const uploadArea = document.getElementById(uploadAreaId);
    const fileInput = document.getElementById(inputId);
    const fileInfo = document.getElementById(fileInfoId);
    const removeBtn = document.getElementById(removeBtnId);

    // Обработчик клика по области загрузки
    uploadArea.addEventListener('click', function (e) {
      // Не запускаем выбор файла при клике на информацию о файле или кнопке удаления
      if (!e.target.closest('.file-info') && !e.target.closest('.remove-btn')) {
        fileInput.click();
      }
    });

    // Обработчик изменения файлового ввода
    fileInput.addEventListener('change', function () {
      updateFileInfo(this, fileInfo, removeBtn);
    });

    // Обработчик для кнопки удаления в заголовке
    if (removeBtn) {
      removeBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        resetFileInput(fileInput, fileInfo, removeBtn);
      });
    }
  }

  // Drag and drop functionality
  function setupDragAndDrop(uploadAreaId, inputId, fileInfoId, removeBtnId) {
    const uploadArea = document.getElementById(uploadAreaId);
    const fileInput = document.getElementById(inputId);
    const fileInfo = document.getElementById(fileInfoId);
    const removeBtn = document.getElementById(removeBtnId);

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
        updateFileInfo(fileInput, fileInfo, removeBtn);

        // Trigger change event
        const event = new Event('change');
        fileInput.dispatchEvent(event);
      }
    }
  }

  // Установка обработчиков для всех областей загрузки
  setupFileUpload('uploadArea1', 'image1', 'fileInfo1', 'remove1');
  setupFileUpload('uploadArea2', 'image2', 'fileInfo2', 'remove2');
  setupFileUpload('dbUploadArea', 'fileInput_for_db', 'fileInfoDb', 'removeDb');

  // Также устанавливаем drag-and-drop обработчики
  setupDragAndDrop('uploadArea1', 'image1', 'fileInfo1', 'remove1');
  setupDragAndDrop('uploadArea2', 'image2', 'fileInfo2', 'remove2');
  setupDragAndDrop('dbUploadArea', 'fileInput_for_db', 'fileInfoDb', 'removeDb');

  // Progress bar simulation
  const forms = document.querySelectorAll('form');
  const progressBar = document.getElementById('progressBar');
  const progressContainer = document.getElementById('progressBarContainer');
  const progressStatus = document.getElementById('progressStatus');
  const progressPercent = document.getElementById('progressPercent');

  forms.forEach(form => {
    form.addEventListener('submit', function (e) {
      // Проверяем, что файлы выбраны
      let valid = true;
      if (form.id === 'double') {
        if (!document.getElementById('image1').files.length ||
          !document.getElementById('image2').files.length) {
          alert('Please select both images for comparison');
          valid = false;
        }
      } else if (form.id === 'uploadForm_for_db') {
        if (!document.getElementById('fileInput_for_db').files.length) {
          alert('Please select an image to find matches');
          valid = false;
        }
      }

      if (!valid) {
        e.preventDefault();
        return;
      }

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