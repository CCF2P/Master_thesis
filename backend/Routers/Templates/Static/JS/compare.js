document.addEventListener('DOMContentLoaded', function () {
  // ============================================================
  // ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
  // ============================================================
  
  // Флаг, указывающий, идёт ли сейчас обработка данных на сервере.
  // Используется для блокировки ухода со страницы во время загрузки.
  let isProcessing = false;

  // ============================================================
  // ФУНКЦИИ БЛОКИРОВКИ УХОДА СО СТРАНИЦЫ
  // ============================================================
  
  // Включает блокировку: устанавливает флаг isProcessing в true
  // и добавляет обработчик события beforeunload, который показывает
  // предупреждение при попытке закрыть/перезагрузить страницу.
  function enablePageLock() {
    isProcessing = true;
    window.addEventListener('beforeunload', handleBeforeUnload);
  }

  // Отключает блокировку: сбрасывает флаг isProcessing в false
  // и удаляет обработчик события beforeunload.
  function disablePageLock() {
    isProcessing = false;
    window.removeEventListener('beforeunload', handleBeforeUnload);
  }

  // Обработчик события beforeunload. Вызывается браузером
  // при попытке пользователя закрыть вкладку или уйти со страницы.
  // Если идёт обработка (isProcessing === true), показывает
  // стандартное предупреждение браузера.
  function handleBeforeUnload(e) {
    if (isProcessing) {
      e.preventDefault();
      e.returnValue = 'Идёт обработка. Вы уверены, что хотите уйти?';
      return e.returnValue;
    }
  }

  // ============================================================
  // ФУНКЦИИ РАБОТЫ С ЗАГРУЗКОЙ ФАЙЛОВ
  // ============================================================
  
  // Обновляет информацию о выбранном файле в элементе fileInfoElement.
  // Принимает:
  //   - fileInput - элемент input[type="file"]
  //   - fileInfoElement - элемент для отображения информации о файле
  //   - removeBtn - кнопка удаления файла (может быть null)
  // Если файл выбран: отображает имя, размер и тип файла,
  // добавляет класс 'file-selected' для визуальной индикации.
  // Если файл не выбран: показывает текст "Файл не выбран".
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

  // Сбрасывает выбранный файл: очищает значение input[type="file"]
  // и обновляет отображаемую информацию.
  // Принимает те же параметры, что и updateFileInfo.
  function resetFileInput(fileInput, fileInfoElement, removeBtn) {
    fileInput.value = '';
    updateFileInfo(fileInput, fileInfoElement, removeBtn);
  }

  // Устанавливает обработчики для клика по области загрузки файла.
  // При клике на область открывается диалог выбора файла.
  // Не срабатывает при клике на информацию о файле или кнопку удаления.
  // Принимает ID элементов:
  //   - uploadAreaId - область загрузки
  //   - inputId - скрытый input[type="file"]
  //   - fileInfoId - элемент для отображения информации
  //   - removeBtnId - кнопка удаления (может отсутствовать)
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

  // ============================================================
  // ФУНКЦИИ DRAG-AND-DROP ЗАГРУЗКИ
  // ============================================================
  
  // Устанавливает обработчики событий drag-and-drop для области загрузки.
  // Поддерживает события: dragenter, dragover, dragleave, drop.
  // При перетаскивании файла на область добавляется класс 'active'.
  // При сброс�� фа��ла обновляется информация о нём.
  // Параметры аналогичны setupFileUpload.
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

  // ============================================================
  // ФУНКЦИИ ОТПРАВКИ ДАННЫХ НА СЕРВЕР
  // ============================================================
  
  // Устанавливает обработчик отправки формы на сервер.
  // При отправке:
  //   1. Проверяет наличие файлов
  //   2. Блокирует кнопки отправки
  //   3. Показывает индикатор загрузки
  //   4. Блокирует уход со страницы
  //   5. Отправляет данные на сервер
  //   6. При успехе: записывает ответ в документ
  //   7. При ошибке: отображает сообщение об ошибке
  //   8. Всегда: разблокирует кнопки и снимает блокировку
  // Параметры:
  //   - formID - ID формы
  //   - errorContainerID - ID контейнера для ошибок
  //   - loadingIndicatorID - ID индикатора загрузки
  //   - fileInputsID - массив ID input[type="file"]
  function setupSendFilesOnServer(
    formID,
    errorContainerID,
    loadingIndicatorID,
    fileInputsID
  ) {
    const form = document.getElementById(formID);
    let errorContainer = document.getElementById(errorContainerID);
    let loadingIndicator = document.getElementById(loadingIndicatorID);
    let fileInputs = new Array();
    fileInputsID.forEach((fileInputID) => {
      fileInputs.push(document.getElementById(fileInputID));
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      
      // Проверка: все ли требуемые файлы выбраны
      if (!fileInputs.every(fileInput => fileInput.files.length !== 0)) {
        errorContainer.classList.add('visible');
        errorContainer.innerHTML = 'Пожалуйста, выберите файл!';
        return;
      }

      // Очистка сообщения об ошибке
      errorContainer.classList.remove('visible');
      const formData = new FormData(form);

      // Блокируем все кнопки отправки в форме
      const allSubmitButtons = form.querySelectorAll('button[type="submit"]');
      allSubmitButtons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.6';
        btn.style.cursor = 'not-allowed';
      });

      // Показываем индикатор загрузки
      if (loadingIndicator) {
        loadingIndicator.classList.add('loading-visible');
      }

      // Блокируем уход со страницы
      enablePageLock();

      try {
        const response = await fetch(form.action, {
          method: form.method,
          body: formData,
        });

        // Проверка статуса ответа
        if (!response.ok) {
          // При ошибкеHTTP (4xx, 5xx) получаем данные об ошибке
          const errorData = await response.json();
          throw errorData;
        }

        // Получаем ответ сервера и записываем в документ
        const data = await response.text();
        document.open();
        document.writeln(data);
        document.close();

        // Снимаем блокировку страницы при успешном завершении
        disablePageLock();
      } catch (error) {
        // Обработка ошибки: выводим в консоль и показываем пользователю
        console.error('Ошибка при обработке:', error);
        
        // Формируем сообщение об ошибке
        let errorMessage = 'Произошла ошибка при обработке запроса.';
        if (error && error.detail) {
          errorMessage = error.detail;
        } else if (error && error.message) {
          errorMessage = error.message;
        }
        
        errorContainer.classList.add('visible');
        errorContainer.innerHTML = errorMessage;

        // Снимаем блокировку страницы
        disablePageLock();
      } finally {
        // Выполняется ВСЕГДА: после success или catch
        // Разблокируем кнопки отправки
        allSubmitButtons.forEach(btn => {
          btn.disabled = false;
          btn.style.opacity = '1';
          btn.style.cursor = 'pointer';
        });

        // Скрываем индикатор загрузки
        if (loadingIndicator) {
          loadingIndicator.classList.remove('loading-visible');
        }
      }
    });
  }

  // ============================================================
  // ИНИЦИАЛИЗАЦИЯ ОБРАБОТЧИКОВ
  // ============================================================
  
  // Настройка обработчиков клика для всех областей загрузки
  setupFileUpload('uploadArea1', 'image1', 'fileInfo1', 'remove1');
  setupFileUpload('uploadArea2', 'image2', 'fileInfo2', 'remove2');
  setupFileUpload('dbUploadArea', 'fileInput_for_db', 'fileInfoDb', 'removeDb');

  // Настройка drag-and-drop обработчиков
  setupDragAndDrop('uploadArea1', 'image1', 'fileInfo1', 'remove1');
  setupDragAndDrop('uploadArea2', 'image2', 'fileInfo2', 'remove2');
  setupDragAndDrop('dbUploadArea', 'fileInput_for_db', 'fileInfoDb', 'removeDb');

  // Настройка отправки форм на сервер
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
