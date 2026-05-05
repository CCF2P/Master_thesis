document.addEventListener('DOMContentLoaded', function () {
  // Глобальное состояние обработки
  let isProcessing = false;

  // Блокировка ухода со страницы
  function enablePageLock() {
    isProcessing = true;
    window.addEventListener('beforeunload', handleBeforeUnload);
  }

  function disablePageLock() {
    isProcessing = false;
    window.removeEventListener('beforeunload', handleBeforeUnload);
  }

  function handleBeforeUnload(e) {
    if (isProcessing) {
      e.preventDefault();
      e.returnValue = 'Идёт обработка. Вы уверены, что хотите уйти?';
      return e.returnValue;
    }
  }

  // Функция для обновления информации о файле
  function updateFileInfo(fileInput, fileInfoElement, removeBtn) {
    if (fileInput.files && fileInput.files.length > 0) {
      const file = fileInput.files[0];
      const fileSize = (file.size / 1024 / 1024).toFixed(2); // Размер в МБ
      let tmp = file.name.split('.');
      tmp = tmp[tmp.length - 1];
      let fileType = 'UNKNOWN';
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
          <span class="file-name">Файл не выбран</span>
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

  // Установка обработчиков для отправки данных на сервер
  // и отображения инидикатора обработки до тех пор, пока сервер обрабатывает
  function setupSendFilesOnServer(
    formID,
    errorContainerID,
    loadingIndicatorID,
    fileInputsID
  ) {
    const form = document.getElementById(formID);
    let errorContainer = document.getElementById(errorContainerID);
    let loadingIndicator = document.getElementById(loadingIndicatorID)
    let fileInputs = new Array();
    fileInputsID.forEach((fileInputID) => {
      fileInputs.push(document.getElementById(fileInputID));
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!fileInputs.every(fileInput => fileInput.files.length !== 0)) {
        errorContainer.classList.add('visible');
        errorContainer.innerHTML = 'Пожалуйста, выберите файл!';
        return;
      }

      errorContainer.classList.remove('visible');
      const formData = new FormData(form);

      // Блокируем все кнопки отправки в форме
      const allSubmitButtons = form.querySelectorAll('button[type="submit"]');
      allSubmitButtons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.6';
        btn.style.cursor = 'not-allowed';
      });

      if (loadingIndicator) {
        loadingIndicator.classList.add('loading-visible');
      }

      enablePageLock();

      try {
        const response = await fetch(form.action, {
          method: form.method,
          body: formData,
        });

        if (!response.ok) {
          throw response.json();
        }

        // additional processing if necessary
        const data = await response.text().then((data) => {
          document.open();
          document.writeln(data);
          document.close();
        });
        // console.log("Server response:", response);
      } catch (error) {
        error.then((value) => {
          console.log(value);
          errorContainer.classList.add('visible');
          errorContainer.innerHTML = `${value.detail}`;
        });

        disablePageLock();

        // Разблокируем кнопки
        allSubmitButtons.forEach(btn => {
          btn.disabled = false;
          btn.style.opacity = '1';
          btn.style.cursor = 'pointer';
        });

        if (loadingIndicator) {
          loadingIndicator.classList.remove('loading-visible');
        }
      }
    });
  }

  // Установка обработчиков для всех областей загрузки
  setupFileUpload('uploadArea1', 'image1', 'fileInfo1', 'remove1');
  setupFileUpload('uploadArea2', 'image2', 'fileInfo2', 'remove2');
  setupFileUpload('dbUploadArea', 'fileInput_for_db', 'fileInfoDb', 'removeDb');

  // Также устанавливаем drag-and-drop обработчики
  setupDragAndDrop('uploadArea1', 'image1', 'fileInfo1', 'remove1');
  setupDragAndDrop('uploadArea2', 'image2', 'fileInfo2', 'remove2');
  setupDragAndDrop('dbUploadArea', 'fileInput_for_db', 'fileInfoDb', 'removeDb');

  // Также устанавливаем обработчики для загрузки файлов
  setupSendFilesOnServer(
    'double',
    'errorContainerDouble',
    'loadingIndicatorDouble',
    ['image1', 'image2']
  );
  setupSendFilesOnServer(
    'uploadForm_for_db',
    'errorContainerDB',
    'loadingIndicatorDB',
    ['fileInput_for_db']
  );
});
