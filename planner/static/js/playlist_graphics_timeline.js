// static/js/timeline_manager.js

class TimelineManager {
    constructor() {
        console.log('TimelineManager constructor called');

        this.canvas = null;
        this.ctx = null;
        this.width = 1200;
        this.height = 400;

        // Масштаб и панорамирование
        this.startHour = 0;
        this.endHour = 24;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartHour = 0;

        // Данные
        this.programs = [];
        this.graphics = [];

        // Цвета в стиле Bootstrap
        this.levelStyles = {
            1: { // базовый (сегменты)
                fill: 'rgba(233, 236, 239, 0.8)',
                stroke: '#adb5bd',
                text: '#495057'
            },
            2: { // постоянная графика
                fill: 'rgba(13, 110, 253, 0.15)',
                stroke: '#0d6efd',
                text: '#0a58ca'
            },
            3: {
                fill: 'rgba(25, 135, 84, 0.15)',
                stroke: '#198754',
                text: '#146c43'
            },
            4: {
                fill: 'rgba(255, 193, 7, 0.15)',
                stroke: '#ffc107',
                text: '#997404'
            },
            5: {
                fill: 'rgba(13, 202, 240, 0.15)',
                stroke: '#0dcaf0',
                text: '#087990'
            }
        };

        // Высоты уровней (прилипают друг к другу)
        this.levelHeights = {
            1: 0,    // базовый уровень
            2: 30,   // +30px
            3: 60,
            4: 90,
            5: 120
        };

        this.tooltip = null;
    }

    init() {
        console.log('TimelineManager init started');

        this.canvas = document.getElementById('programTimeline');
        if (!this.canvas) {
            console.error('Canvas not found');
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width;
        this.height = this.canvas.height;

        this.createTooltip();
        this.loadDemoData();
        this.draw();
        this.addEventListeners();

        // Обновляем отображение диапазона
        this.updateTimeRange();
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'timeline-tooltip';
        this.tooltip.style.display = 'none';
        document.body.appendChild(this.tooltip);
    }

    loadDemoData() {
        const rows = document.querySelectorAll('[data-scheduled-program-id]');

        // Программы (все на уровне 1, вплотную друг к другу)
        this.programs = [
            { id: 'prog1', name: 'Утреннее шоу', start: 6*3600, end: 10*3600, level: 1, row: rows[0] },
            { id: 'prog2', name: 'Дневной фильм', start: 10*3600, end: 12*3600, level: 1, row: rows[1] },
            { id: 'prog3', name: 'Новости', start: 12*3600, end: 12.5*3600, level: 1, row: rows[2] },
            { id: 'prog4', name: 'Сериал', start: 12.5*3600, end: 14*3600, level: 1, row: rows[3] },
            { id: 'prog5', name: 'Ток-шоу', start: 14*3600, end: 16*3600, level: 1, row: rows[4] },
            { id: 'prog6', name: 'Фильм', start: 16*3600, end: 19*3600, level: 1, row: rows[5] },
            { id: 'prog7', name: 'Вечерние новости', start: 19*3600, end: 20*3600, level: 1, row: rows[6] },
            { id: 'prog8', name: 'Прайм-тайм шоу', start: 20*3600, end: 23*3600, level: 1, row: rows[7] }
        ];

        // Графика (все уровни строятся ВВЕРХ от базовой линии)
        this.graphics = [
            // Level 2 - постоянная графика
            { id: 'g1', name: 'air_now', alias: 'Сейчас в эфире', programId: 'prog1', start: 6*3600, end: 10*3600, level: 2, duration: 'постоянно' },
            { id: 'g2', name: 'air_now', alias: 'Сейчас в эфире', programId: 'prog4', start: 12.5*3600, end: 14*3600, level: 2, duration: 'постоянно' },
            { id: 'g3', name: 'air_now', alias: 'Сейчас в эфире', programId: 'prog6', start: 16*3600, end: 19*3600, level: 2, duration: 'постоянно' },
            { id: 'g4', name: 'air_now', alias: 'Сейчас в эфире', programId: 'prog8', start: 20*3600, end: 23*3600, level: 2, duration: 'постоянно' },

            // Level 3
            { id: 'g5', name: 'air_today', alias: 'Сегодня в эфире', programId: 'prog1', start: 7*3600 + 15*60, end: 7*3600 + 15*60 + 15, level: 3, duration: 15 },
            { id: 'g6', name: 'air_today', alias: 'Сегодня в эфире', programId: 'prog1', start: 8*3600 + 30*60, end: 8*3600 + 30*60 + 10, level: 3, duration: 10 },
            { id: 'g7', name: 'air_tomorrow', alias: 'Завтра в эфире', programId: 'prog2', start: 11*3600 + 15*60, end: 11*3600 + 15*60 + 12, level: 3, duration: 12 },

            // Level 4
            { id: 'g8', name: 'telegram', alias: 'Телеграм', programId: 'prog3', start: 12*3600 + 10*60, end: 12*3600 + 10*60 + 18, level: 4, duration: 18 },
            { id: 'g9', name: 'air_today', alias: 'Сегодня в эфире', programId: 'prog4', start: 13*3600 + 20*60, end: 13*3600 + 20*60 + 10, level: 4, duration: 10 },

            // Level 5
            { id: 'g10', name: 'air_tomorrow', alias: 'Завтра в эфире', programId: 'prog5', start: 15*3600 + 5*60, end: 15*3600 + 5*60 + 12, level: 5, duration: 12 },
            { id: 'g11', name: 'promo', alias: 'Промо', programId: 'prog6', start: 17*3600 + 10*60, end: 17*3600 + 10*60 + 30, level: 5, duration: 30 }
        ];
    }

    draw() {
        this.ctx.clearRect(0, 0, this.width, this.height);

        this.drawGrid();
        this.drawPrograms();
        this.drawGraphics();
    }

    drawGrid() {
        const ctx = this.ctx;
        const totalHours = this.endHour - this.startHour;

        ctx.save();

        // Фон
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        ctx.fillStyle = isDark ? '#212529' : '#f8f9fa';
        ctx.fillRect(0, 0, this.width, this.height);

        // Вертикальные линии (часы)
        ctx.strokeStyle = isDark ? '#495057' : '#dee2e6';
        ctx.lineWidth = 1;
        ctx.font = '10px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';

        for (let hour = 0; hour <= totalHours; hour++) {
            const x = (hour / totalHours) * this.width;
            const realHour = (this.startHour + hour) % 24;

            ctx.beginPath();
            ctx.strokeStyle = hour % 3 === 0
                ? (isDark ? '#6c757d' : '#adb5bd')
                : (isDark ? '#343a40' : '#dee2e6');
            ctx.moveTo(x, 0);
            ctx.lineTo(x, this.height);
            ctx.stroke();

            if (hour % 3 === 0) {
                ctx.fillStyle = isDark ? '#dee2e6' : '#495057';
                ctx.fillText(`${realHour.toString().padStart(2, '0')}:00`, x, 25);
            }
        }

        // Базовая линия (внизу, от неё всё растёт вверх)
        const baseY = this.height - 80; // Отступ снизу

        ctx.strokeStyle = isDark ? '#6c757d' : '#adb5bd';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(0, baseY);
        ctx.lineTo(this.width, baseY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Подписи уровней слева
        ctx.font = '9px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = isDark ? '#adb5bd' : '#6c757d';
        ctx.textAlign = 'left';
        ctx.shadowColor = 'transparent';

        for (let level = 1; level <= 5; level++) {
            const y = baseY - this.levelHeights[level] - 5;
            ctx.fillText(`L${level}`, 10, y);
        }

        ctx.restore();
    }

    drawPrograms() {
        const ctx = this.ctx;
        const totalHours = this.endHour - this.startHour;
        const baseY = this.height - 80;
        const style = this.levelStyles[1];

        this.programs.forEach(program => {
            const startX = ((program.start / 3600 - this.startHour) / totalHours) * this.width;
            const endX = ((program.end / 3600 - this.startHour) / totalHours) * this.width;
            const width = endX - startX;

            if (width < 1) return;

            ctx.save();

            // Программа рисуется НАД базовой линией
            ctx.fillStyle = style.fill;
            ctx.strokeStyle = style.stroke;
            ctx.lineWidth = 1.5;

            const radius = 4;
            const y = baseY - 28; // 28 высота, от baseline вверх

            ctx.beginPath();
            ctx.moveTo(startX + radius, y);
            ctx.lineTo(startX + width - radius, y);
            ctx.quadraticCurveTo(startX + width, y, startX + width, y + radius);
            ctx.lineTo(startX + width, y + 28 - radius);
            ctx.quadraticCurveTo(startX + width, y + 28, startX + width - radius, y + 28);
            ctx.lineTo(startX + radius, y + 28);
            ctx.quadraticCurveTo(startX, y + 28, startX, y + 28 - radius);
            ctx.lineTo(startX, y + radius);
            ctx.quadraticCurveTo(startX, y, startX + radius, y);
            ctx.closePath();

            ctx.fill();
            ctx.stroke();

            // Название
            if (width > 60) {
                ctx.font = '10px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
                ctx.fillStyle = style.text;
                ctx.shadowColor = 'transparent';
                ctx.save();
                ctx.beginPath();
                ctx.rect(startX, y, width, 32);
                ctx.clip();

                let name = program.name;
                if (width < 120 && name.length > 12) {
                    name = name.substring(0, 10) + '…';
                }

                ctx.fillText(name, startX + 8, y + 19);
                ctx.restore();
            }

            ctx.restore();
        });
    }

    drawGraphics() {
        const ctx = this.ctx;
        const totalHours = this.endHour - this.startHour;
        const baseY = this.height - 80;

        this.graphics.forEach(graphic => {
            const style = this.levelStyles[graphic.level];

            let startX = ((graphic.start / 3600 - this.startHour) / totalHours) * this.width;
            let endX = ((graphic.end / 3600 - this.startHour) / totalHours) * this.width;
            let width = endX - startX;

            // Минимальная ширина
            const MIN_WIDTH = graphic.duration === 'постоянно' ? 4 : 12;
            let centerX = startX;

            if (width < MIN_WIDTH) {
                startX = centerX - MIN_WIDTH/2;
                width = MIN_WIDTH;
            }

            // Графика рисуется ВВЕРХ от базовой линии
            const y = baseY - this.levelHeights[graphic.level] - 28;
            const height = 28;

            ctx.save();

            ctx.fillStyle = style.fill;
            ctx.strokeStyle = style.stroke;
            ctx.lineWidth = 1.5;

            const radius = 6;
            ctx.beginPath();
            ctx.moveTo(startX + radius, y);
            ctx.lineTo(startX + width - radius, y);
            ctx.quadraticCurveTo(startX + width, y, startX + width, y + radius);
            ctx.lineTo(startX + width, y + height - radius);
            ctx.quadraticCurveTo(startX + width, y + height, startX + width - radius, y + height);
            ctx.lineTo(startX + radius, y + height);
            ctx.quadraticCurveTo(startX, y + height, startX, y + height - radius);
            ctx.lineTo(startX, y + radius);
            ctx.quadraticCurveTo(startX, y, startX + radius, y);
            ctx.closePath();

            ctx.fill();
            ctx.stroke();

            ctx.restore();
        });
    }

    addEventListeners() {
        // Панорамирование мышью
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        this.canvas.addEventListener('mouseleave', () => this.handleMouseLeave());

        // Колесико для зума
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));

        // Обычные события
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
    }

    handleMouseDown(e) {
        this.isDragging = true;
        this.dragStartX = e.clientX;
        this.dragStartHour = this.startHour;
        this.canvas.style.cursor = 'grabbing';
    }

    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.width / rect.width;
        const scaleY = this.height / rect.height;

        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;

        if (this.isDragging) {
            // Панорамирование
            const deltaX = e.clientX - this.dragStartX;
            const deltaHours = (deltaX / this.width) * (this.endHour - this.startHour);

            this.startHour = Math.max(0, Math.min(24 - (this.endHour - this.startHour),
                                       this.dragStartHour - deltaHours));
            this.endHour = this.startHour + (this.dragStartHour + (this.endHour - this.startHour) - this.dragStartHour);

            this.draw();
            this.updateTimeRange();
        } else {
            // Обычный hover
            const hoveredItem = this.findItemAt(mouseX, mouseY);

            if (hoveredItem) {
                this.showTooltip(hoveredItem, e.clientX, e.clientY);
                this.highlightRow(hoveredItem.programId || hoveredItem.id);
                this.canvas.style.cursor = 'pointer';
            } else {
                this.hideTooltip();
                this.clearRowHighlight();
                this.canvas.style.cursor = 'grab';
            }
        }
    }

    handleMouseUp() {
        this.isDragging = false;
        this.canvas.style.cursor = 'grab';
    }

    handleMouseLeave() {
        this.isDragging = false;
        this.hideTooltip();
        this.clearRowHighlight();
        this.canvas.style.cursor = 'default';
    }

    handleWheel(e) {
        e.preventDefault();

        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseXRatio = mouseX / rect.width;

        // Центрируем зум на позиции мыши
        const centerHour = this.startHour + mouseXRatio * (this.endHour - this.startHour);

        const delta = e.deltaY > 0 ? 1.1 : 0.9; // Увеличиваем или уменьшаем
        const newRange = Math.max(2, Math.min(24, (this.endHour - this.startHour) * delta));

        this.startHour = Math.max(0, Math.min(24 - newRange, centerHour - newRange * mouseXRatio));
        this.endHour = this.startHour + newRange;

        this.draw();
        this.updateTimeRange();
    }

    findItemAt(x, y) {
        const totalHours = this.endHour - this.startHour;
        const baseY = this.height - 80;

        // Сначала графику (чем выше уровень, тем приоритетнее)
        for (let level = 5; level >= 2; level--) {
            const levelGraphics = this.graphics.filter(g => g.level === level);

            for (let graphic of levelGraphics) {
                const startX = ((graphic.start / 3600 - this.startHour) / totalHours) * this.width;
                const endX = ((graphic.end / 3600 - this.startHour) / totalHours) * this.width;
                let width = endX - startX;

                const MIN_WIDTH = graphic.duration === 'постоянно' ? 4 : 12;
                let checkStartX = startX;

                if (width < MIN_WIDTH) {
                    checkStartX = startX - MIN_WIDTH/2;
                    width = MIN_WIDTH;
                }

                const graphicY = baseY - this.levelHeights[graphic.level] - 20;

                if (x >= checkStartX && x <= checkStartX + width &&
                    y >= graphicY && y <= graphicY + 20) {
                    return graphic;
                }
            }
        }

        // Затем программы
        for (let program of this.programs) {
            const startX = ((program.start / 3600 - this.startHour) / totalHours) * this.width;
            const endX = ((program.end / 3600 - this.startHour) / totalHours) * this.width;
            const programY = baseY - 28;

            if (x >= startX && x <= endX && y >= programY && y <= programY + 28) {
                return program;
            }
        }

        return null;
    }

    handleClick(e) {
        if (this.isDragging) return; // Не обрабатываем клик после драга

        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.width / rect.width;
        const scaleY = this.height / rect.height;

        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;

        const clickedItem = this.findItemAt(mouseX, mouseY);

        if (clickedItem) {
            const rowId = clickedItem.programId || clickedItem.id;
            const row = document.querySelector(`[data-scheduled-program-id="${rowId}"]`);
            if (row) {
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });

                row.style.backgroundColor = 'rgba(255, 193, 7, 0.2)';
                row.style.transition = 'background-color 0.5s';
                setTimeout(() => {
                    row.style.backgroundColor = '';
                }, 1000);
            }
        }
    }

    showTooltip(item, clientX, clientY) {
        const style = this.levelStyles[item.level || 1];
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';

        let content = '';
        if (item.alias) {
            content = `
                <div style="color: ${style.stroke}; font-weight: 600; margin-bottom: 4px;">
                    ● ${item.alias}
                </div>
                <div>Начало: ${this.formatTime(item.start)}</div>
                <div>Длительность: ${item.duration === 'постоянно' ? 'весь сегмент' : item.duration + ' сек'}</div>
                <div style="color: ${isDark ? '#adb5bd' : '#6c757d'}; font-size: 10px; margin-top: 4px;">
                    Уровень ${item.level}
                </div>
            `;
        } else {
            content = `
                <div style="font-weight: 600; margin-bottom: 4px;">${item.name}</div>
                <div>Начало: ${this.formatTime(item.start)}</div>
                <div>Конец: ${this.formatTime(item.end)}</div>
            `;
        }

        this.tooltip.innerHTML = content;
        this.tooltip.style.display = 'block';
        this.tooltip.style.left = (clientX + 15) + 'px';
        this.tooltip.style.top = (clientY - 40) + 'px';
    }

    hideTooltip() {
        this.tooltip.style.display = 'none';
    }

    highlightRow(programId) {
        this.clearRowHighlight();

        const row = document.querySelector(`[data-scheduled-program-id="${programId}"]`);
        if (row) {
            row.classList.add('timeline-hover');
        }
    }

    clearRowHighlight() {
        document.querySelectorAll('.timeline-hover').forEach(el => {
            el.classList.remove('timeline-hover');
        });
    }

    formatTime(seconds) {
        const h = Math.floor(seconds / 3600) % 24;
        const m = Math.floor((seconds % 3600) / 60);
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    }

    zoomIn() {
        const range = this.endHour - this.startHour;
        if (range > 4) {
            const center = (this.startHour + this.endHour) / 2;
            const newRange = range - 4;
            this.startHour = Math.max(0, center - newRange/2);
            this.endHour = Math.min(24, center + newRange/2);
            this.draw();
            this.updateTimeRange();
        }
    }

    zoomOut() {
        const range = this.endHour - this.startHour;
        if (range < 24) {
            const center = (this.startHour + this.endHour) / 2;
            const newRange = Math.min(24, range + 4);
            this.startHour = Math.max(0, center - newRange/2);
            this.endHour = Math.min(24, center + newRange/2);
            this.draw();
            this.updateTimeRange();
        }
    }

    setZoom(hours) {
        const center = (this.startHour + this.endHour) / 2;
        this.startHour = Math.max(0, center - hours/2);
        this.endHour = Math.min(24, center + hours/2);
        this.draw();
        this.updateTimeRange();
    }

    updateTimeRange() {
        const rangeElement = document.getElementById('timelineTimeRange');
        if (rangeElement) {
            rangeElement.textContent =
                `${this.startHour.toString().padStart(2, '0')}:00 - ${this.endHour.toString().padStart(2, '0')}:00`;
        }
    }
}

// Создаём экземпляр
window.timelineManager = new TimelineManager();
console.log('TimelineManager instance created');