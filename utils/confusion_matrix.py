import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

cm = np.array([[946, 424],
               [85, 189]])

sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Предсказан 0', 'Предсказан 1'],
            yticklabels=['Истинный 0', 'Истинный 1'])
plt.xlabel('Предсказанный класс')
plt.ylabel('Истинный класс')
plt.title('Матрица ошибок')
plt.show()

