// Функция для получения актуальных цветов из Bootstrap
function getBootstrapColor(cssVar) {
  return getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
}

// Объект для хранения экземпляров графиков
const charts = {
  daily: null,
  week: null
};

// Функция инициализации/обновления круговой диаграммы
function initDailyChart() {
  const ctx = document.getElementById('dailyChart');

  if (charts.daily) charts.daily.destroy();

  charts.daily = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Не выполнено', 'Выполнено', 'На доработке'],
      datasets: [{
        label: 'Статистика за день',
        data: [300, 50, 100],
        backgroundColor: [
          getBootstrapColor('--bs-danger-bg-subtle'),
          getBootstrapColor('--bs-success-bg-subtle'),
          getBootstrapColor('--bs-warning-bg-subtle')
        ],
        borderColor: [
          getBootstrapColor('--bs-danger-border-subtle'),
          getBootstrapColor('--bs-success-border-subtle'),
          getBootstrapColor('--bs-warning-border-subtle')
        ],
        borderWidth: 2,
        hoverOffset: 3
      }]
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: { boxPadding: 2 }
      }
    }
  });
}

// Функция инициализации/обновления линейного графика
function initWeekChart() {
  const ctx = document.getElementById('weekChart');

  if (charts.week) charts.week.destroy();

  charts.week = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'],
      datasets: [{
        fill: true,
        data: [158, 162, 159, 160, 161],
        lineTension: 0.2,
        backgroundColor: getBootstrapColor('--bs-info-bg-subtle'),
        borderColor: getBootstrapColor('--bs-info-border-subtle'),
        borderWidth: 3,
        pointBackgroundColor: getBootstrapColor('--bs-info-border-subtle')
      }]
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: { boxPadding: 3 }
      }
    }
  });
}

// Инициализация всех графиков
function initCharts() {
  initDailyChart();
  initWeekChart();
}

// Отслеживание смены темы
function setupThemeObserver() {
  const observer = new MutationObserver(() => {
    initCharts(); // Пересоздаём графики при смене темы
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-bs-theme']
  });
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  setupThemeObserver();
});
