/* globals Chart:false */

(() => {
  'use strict'

  const dailyChart = document.getElementById('dailyChart')
  const myDailyChart = new Chart(dailyChart, {
      type: 'doughnut',
      data: {
      labels: [
        'Не выполнено',
        'Выполнено',
        'На доработке'
      ],
      datasets: [{
        label: 'Статистика за день',
        data: [300, 50, 100],
        backgroundColor: [
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(254, 62, 235)'
        ],
        hoverOffset: 3
      }]
    },
    options: {
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          boxPadding: 2
        }
      }
    }
  });

  // Graphs
  const weekChart = document.getElementById('weekChart')
  // eslint-disable-next-line no-unused-vars
  const myWeekChart = new Chart(weekChart, {
    type: 'line',
    data: {
      labels: [
        'Пн',
        'Вт',
        'Ср',
        'Чт',
        'Пт',
        'Сб',
        'Вс',

      ],
      datasets: [{
        data: [
          150,
          180,
          145,
          160,
          160,
          140,
          150
        ],
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff'
      }]
    },
    options: {
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          boxPadding: 3
        }
      }
    }
  })
})();

