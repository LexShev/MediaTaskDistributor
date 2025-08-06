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
  const dailyChart = document.getElementById('dailyChart');
  const dailyChartContainer = document.getElementById('dailyChartContainer');

  if (charts.daily) charts.daily.destroy();

  fetch(`/load_daily_kpi_chart/`)
    .then(response => response.json())
    .then(data => {
    console.log(data);
      if (data.values && data.values.every(item => item === 0)) {
        dailyChartContainer.innerHTML = `<h4 class="text-center">Нет распределённых задач</div>`;
        return
      };
      charts.daily = new Chart(dailyChart, {
        type: 'doughnut',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Всего сегодня',
            data: data.values,
            backgroundColor: [
              getBootstrapColor('--bs-danger-bg-subtle'),
              getBootstrapColor('--bs-success-bg-subtle'),
              getBootstrapColor('--bs-warning-bg-subtle'),
              getBootstrapColor('--bs-info-bg-subtle')
            ],
            borderColor: [
              getBootstrapColor('--bs-danger-border-subtle'),
              getBootstrapColor('--bs-success-border-subtle'),
              getBootstrapColor('--bs-warning-border-subtle'),
              getBootstrapColor('--bs-info-border-subtle')
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
    })
    .catch(error => {
      dailyChartContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки данных</div>`;
    });
}

// Функция инициализации/обновления линейного графика
function initWeekChart() {
  const weekChart = document.getElementById('weekChart');
  const weekChartContainer = document.getElementById('weekChartContainer');

  if (charts.week) charts.week.destroy();

  fetch(`/load_kpi_chart/`)
    .then(response => response.json())
    .then(data => {
      charts.week = new Chart(weekChart, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [{
            fill: true,
            data: data.kpis,
            lineTension: 0.2,
            backgroundColor: getBootstrapColor('--bs-info-bg-subtle'),
            borderColor: getBootstrapColor('--bs-info-border-subtle'),
            borderWidth: 3,
            pointBackgroundColor: getBootstrapColor('--bs-info-border-subtle')
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { boxPadding: 3 }
          }
        }
      });
    })
    .catch(error => {
        weekChartContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки данных</div>`;
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
