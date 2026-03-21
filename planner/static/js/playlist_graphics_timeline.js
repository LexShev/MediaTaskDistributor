// static/js/timeline_manager.js

class TimelineManager {
    constructor() {
        console.log('TimelineManager constructor called');

        this.canvas = null;
        this.ctx = null;
        this.width = 1370;
        this.height = 230;

        // Масштаб и панорамирование
        this.startHour = 0;
        this.endHour = 24;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartHour = 0;

        // Данные
        this.programsData = [];

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
            3: { // промо-блоки
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

        // Высоты уровней
        this.levelHeights = {
            1: 0,    // базовый уровень (программы и сегменты)
            2: 65,   // постоянная графика (сдвинута вниз)
            3: 95,   // промо-блоки (еще ниже)
            4: 125,
            5: 155
        };

        this.tooltip = null;
        this.hoveredItem = null;
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
        this.loadDataFromDOM();
        this.draw();
        this.addEventListeners();
        this.updateTimeRange();
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'timeline-tooltip';
        this.tooltip.style.display = 'none';
        document.body.appendChild(this.tooltip);
    }

    parseDateTime(dateTimeStr) {
        // Формат: "ГГГГ:ММ:ДД ЧЧ:ММ:СС"
        // Пример: "2026:03:21 14:30:00"

        if (!dateTimeStr) return 0;

        // Разделяем дату и время
        const [datePart, timePart] = dateTimeStr.split(' ');

        if (!datePart || !timePart) return 0;

        // Парсим дату: ГГГГ-ММ-ДД
        const [year, month, day] = datePart.split('-').map(Number);

        // Парсим время: ЧЧ:ММ:СС
        const [hours, minutes, seconds] = timePart.split(':').map(Number);

        // Создаем объект Date для получения timestamp
        const date = new Date(year, month - 1, day, hours, minutes, seconds);

        // Возвращаем количество секунд с начала суток
        // (часы * 3600 + минуты * 60 + секунды)
        return hours * 3600 + minutes * 60 + seconds;
    }

    loadDataFromDOM() {
        const programs = document.querySelectorAll('.program');
        this.programsData = [];

        programs.forEach(program => {
            const scheduledProgramId = program?.dataset.scheduledProgramId;
            const programStart = this.parseDateTime(program.dataset.startTime);
            const programDuration = Math.floor(parseInt(program.dataset.duration) / 25);

            const programObj = {
                scheduledProgramId: scheduledProgramId,
                name: program?.dataset.name,
                startTime: program?.dataset.startTime,
                duration: program?.dataset.duration,
                startSeconds: programStart,
                endSeconds: programStart + programDuration,
                type: 'program',
                graphicsLevel: program?.dataset.graphicsLevel || 1,
                segments: [],
                blocks: []  // блоки на уровне программы
            };

            // Сегменты внутри программы
            const segments = program.querySelectorAll('.segment');
            segments.forEach(segment => {
                const segmentStart = this.parseDateTime(segment.dataset.startTime);
                const segmentDuration = Math.floor(parseInt(segment.dataset.duration) / 25);
                const graphicsStr = segment?.dataset.graphics;
                let graphics = null;

                if (graphicsStr) {
                    try {
                        graphics = JSON.parse(graphicsStr.trim());
                    } catch (e) {
                        console.warn('Failed to parse JSON for segment', segment, e);
                    }
                }

                const segmentObj = {
                    scheduledProgramId: segment?.dataset.scheduledProgramId,
                    parentId: scheduledProgramId,
                    name: segment?.dataset.name,
                    startTime: segment?.dataset.startTime,
                    duration: segment?.dataset.duration,
                    startSeconds: segmentStart,
                    endSeconds: segmentStart + segmentDuration,
                    type: 'segment',
                    graphicsLevel: segment?.dataset.graphicsLevel || 1,
                    graphics: graphics,
                    graphicsItems: []  // графические элементы внутри сегмента
                };

                // Добавляем графику как отдельные элементы для отрисовки
                if (graphics && Array.isArray(graphics)) {
                    segmentObj.graphicsItems = [];
                    graphics.forEach(g => {
                        segmentObj.graphicsItems.push({
                            id: g.id || `${segment.dataset.scheduledProgramId}_graphic_${Date.now()}`,
                            name: g.alias || g.name || 'Графика',
                            startSeconds: segmentStart + (g.start || 0),
                            endSeconds: segmentStart + (g.end || (g.start + 10)),
                            graphicsLevel: g.level || 2,
                            type: 'graphic',
                            segmentId: segment.dataset.scheduledProgramId
                        });
                    });
                }

                programObj.segments.push(segmentObj);
            });

            // Блоки промо внутри программы
            const blocks = program.querySelectorAll('.block');
            blocks.forEach(block => {
                const blockId = block?.dataset.scheduledProgramId;
                const blockStart = this.parseDateTime(block.dataset.startTime);
                // const blockDuration = Math.floor(parseInt(block.dataset.duration) / 25);

                // Собираем все рекламные ролики внутри блока
                const adverts = block.querySelectorAll('.advert, .license');
                let totalDuration = 0;
                const blockItems = [];

                adverts.forEach(advert => {
                    const advertDuration = Math.floor(parseInt(advert.dataset.duration) / 25);
                    totalDuration += advertDuration;
                    blockItems.push({
                        scheduledProgramId: advert?.dataset.scheduledProgramId,
                        parentId: blockId,
                        name: advert?.dataset.name,
                        startTime: advert?.dataset.startTime,
                        duration: advert?.dataset.duration,
                        startSeconds: blockStart,
                        endSeconds: blockStart + totalDuration,
                        graphicsLevel: 2,
                        type: 'block'
                    });
                });

                // Добавляем блок как один элемент для отрисовки
                if (blockItems.length > 0) {
                    programObj.blocks.push({
                        scheduledProgramId: blockId,
                        parentId: scheduledProgramId,
                        name: block?.dataset.name || 'Промо-блок',
                        startTime: block?.dataset.startTime,
                        duration: block?.dataset.duration,
                        startSeconds: blockStart,
                        endSeconds: blockStart + totalDuration,
                        graphicsLevel: 2,
                        type: 'block',
                        items: blockItems  // сохраняем список реклам для тултипа
                    });
                }
            });

            this.programsData.push(programObj);
        });

        console.log('Loaded programs:', this.programsData.length);
        console.log('Programs data:', this.programsData);
    }


    draw() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        this.drawGrid();

        const totalHours = this.endHour - this.startHour;
        const baseY = this.height - 30;

        const itemsToDraw = [];

        this.programsData.forEach(program => {
            // Программа
            itemsToDraw.push({
                scheduledProgramId: program.scheduledProgramId,
                type: program.type,
                level: program.graphicsLevel,
                start: program.startSeconds,
                end: program.endSeconds,
                name: program.name,
                isProgram: true,
                zIndex: 1  // низкий приоритет
            });

            // Сегменты
            program.segments.forEach(segment => {
                itemsToDraw.push({
                    scheduledProgramId: segment.scheduledProgramId,
                    type: segment.type,
                    level: segment.graphicsLevel,
                    start: segment.startSeconds,
                    end: segment.endSeconds,
                    name: segment.name,
                    parentId: segment.parentId,
                    isSegment: true,
                    zIndex: 2  // средний приоритет (выше программы)
                });

                // Графика сегмента
                if (segment.graphicsItems) {
                    segment.graphicsItems.forEach(graphic => {
                        itemsToDraw.push({
                            scheduledProgramId: graphic.id,
                            type: graphic.type,
                            level: graphic.graphicsLevel,
                            start: graphic.startSeconds,
                            end: graphic.endSeconds,
                            name: graphic.name,
                            segmentId: segment.scheduledProgramId,
                            isGraphic: true,
                            zIndex: 3  // высокий приоритет
                        });
                    });
                }
            });

            // Блоки промо
            program.blocks.forEach(block => {
                itemsToDraw.push({
                    scheduledProgramId: block.scheduledProgramId,
                    type: block.type,
                    level: block.graphicsLevel,
                    start: block.startSeconds,
                    end: block.endSeconds,
                    name: block.name,
                    programId: program.scheduledProgramId,
                    items: block.items,
                    isBlock: true,
                    zIndex: 3  // высокий приоритет (как у графики)
                });
            });
        });

        // Сортируем по zIndex (сначала низкие, потом высокие)
        itemsToDraw.sort((a, b) => a.zIndex - b.zIndex);

        // Рисуем
        itemsToDraw.forEach(item => {
            const startX = ((item.start / 3600 - this.startHour) / totalHours) * this.width;
            const endX = ((item.end / 3600 - this.startHour) / totalHours) * this.width;
            let width = endX - startX;

            if (width < 1 && item.type !== 'graphic') return;

            const style = this.levelStyles[item.level] || this.levelStyles[2];

            let y, height;

            if (item.isProgram) {
                // Программа: высокая, 60px
                y = baseY - 60;
                height = 60;
            } else if (item.isSegment) {
                // Сегмент: 30px, прижат к низу
                y = baseY - 30;
                height = 30;
            } else {
                // Графика и блоки
                y = baseY - this.levelHeights[item.level] - 30;
                height = 30;
            }

            const MIN_WIDTH = 8;
            let finalStartX = startX;
            if ((item.type === 'graphic' || item.type === 'block') && width < MIN_WIDTH) {
                const centerX = (startX + endX) / 2;
                finalStartX = centerX - MIN_WIDTH/2;
                width = MIN_WIDTH;
            }

            this.ctx.save();

            let shouldHighlight = false;
            if (this.hoveredItem) {
                const hoveredId = this.hoveredItem.scheduledProgramId;
                const itemId = item.scheduledProgramId;
                if (hoveredId === itemId) {
                    shouldHighlight = true;
                }
            }

            if (shouldHighlight) {
                this.ctx.fillStyle = 'rgba(255, 193, 7, 0.4)';
                this.ctx.strokeStyle = '#ffc107';
                this.ctx.lineWidth = 2;
            } else {
                this.ctx.fillStyle = style.fill;
                this.ctx.strokeStyle = style.stroke;
                this.ctx.lineWidth = item.type === 'segment' ? 1 : 1.5;
            }

            const radius = item.type === 'segment' ? 3 : 4;
            this.ctx.beginPath();
            this.ctx.moveTo(finalStartX + radius, y);
            this.ctx.lineTo(finalStartX + width - radius, y);
            this.ctx.quadraticCurveTo(finalStartX + width, y, finalStartX + width, y + radius);
            this.ctx.lineTo(finalStartX + width, y + height - radius);
            this.ctx.quadraticCurveTo(finalStartX + width, y + height, finalStartX + width - radius, y + height);
            this.ctx.lineTo(finalStartX + radius, y + height);
            this.ctx.quadraticCurveTo(finalStartX, y + height, finalStartX, y + height - radius);
            this.ctx.lineTo(finalStartX, y + radius);
            this.ctx.quadraticCurveTo(finalStartX, y, finalStartX + radius, y);
            this.ctx.closePath();

            this.ctx.fill();
            this.ctx.stroke();

            // Название
            if (width > 40) {
                if (item.isProgram) {
                    // Для программы - название по центру сверху
                    this.ctx.font = 'bold 11px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
                    this.ctx.fillStyle = shouldHighlight ? '#ffc107' : style.text;
                    this.ctx.textAlign = 'center';
                    this.ctx.save();
                    this.ctx.beginPath();
                    this.ctx.rect(finalStartX, y, width, height);
                    this.ctx.clip();

                    let name = item.name;
                    const maxLen = 25;
                    if (name.length > maxLen) {
                        name = name.substring(0, maxLen - 3) + '…';
                    }
                    this.ctx.fillText(name, finalStartX + width/2, y + 18);
                    this.ctx.restore();
                    this.ctx.textAlign = 'left';
                } else if (item.isSegment) {
                    // Для сегмента - увеличил шрифт
                    this.ctx.font = '10px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
                    this.ctx.fillStyle = shouldHighlight ? '#ffc107' : style.text;
                    this.ctx.save();
                    this.ctx.beginPath();
                    this.ctx.rect(finalStartX, y, width, height);
                    this.ctx.clip();

                    let name = item.name;
                    const maxLen = 25;
                    if (name.length > maxLen) {
                        name = name.substring(0, maxLen - 3) + '…';
                    }
                    this.ctx.fillText(name, finalStartX + 5, y + 21);
                    this.ctx.restore();
                }
            }

            this.ctx.restore();
        });
    }

    drawGrid() {
        const ctx = this.ctx;
        const totalHours = this.endHour - this.startHour;

        ctx.save();

        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        ctx.fillStyle = isDark ? '#212529' : '#f8f9fa';
        ctx.fillRect(0, 0, this.width, this.height);

        // Вертикальные линии (часы)
        ctx.strokeStyle = isDark ? '#495057' : '#dee2e6';
        ctx.lineWidth = 1;
        ctx.font = '10px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';

        const hourStep = totalHours > 12 ? 3 : (totalHours > 6 ? 2 : 1);

        for (let hour = 0; hour <= totalHours; hour += 0.5) {
            const x = (hour / totalHours) * this.width;
            const realHour = this.startHour + hour;

            if (Math.abs(hour - Math.round(hour)) < 0.01) {
                ctx.beginPath();
                ctx.strokeStyle = hour % hourStep === 0
                    ? (isDark ? '#6c757d' : '#adb5bd')
                    : (isDark ? '#343a40' : '#dee2e6');
                ctx.moveTo(x, 0);
                ctx.lineTo(x, this.height);
                ctx.stroke();

                if (hour % hourStep === 0) {
                    ctx.fillStyle = isDark ? '#dee2e6' : '#495057';
                    const hourInt = Math.floor(realHour) % 24;
                    ctx.fillText(`${hourInt.toString().padStart(2, '0')}:00`, x, 25);
                }
            }
        }

        // Базовая линия
        // const baseY = this.height - 30;
        //
        // // Подписи уровней слева
        // ctx.font = '9px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
        // ctx.fillStyle = isDark ? '#adb5bd' : '#6c757d';
        // ctx.textAlign = 'left';
        // ctx.shadowColor = 'transparent';

        // for (let level = 1; level <= 5; level++) {
        //     const y = baseY - this.levelHeights[level] - 5;
        //     ctx.fillText(`L${level}`, 10, y);
        // }

        ctx.restore();
    }

    addEventListeners() {
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        this.canvas.addEventListener('mouseleave', () => this.handleMouseLeave());
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // Подсветка при наведении на строки таблицы
        document.querySelectorAll('[data-scheduled-program-id]').forEach(row => {
            row.addEventListener('mouseenter', () => {
                const elementId = row.dataset.scheduledProgramId;
                this.highlightChartElement(elementId);
            });

            row.addEventListener('mouseleave', () => {
                this.clearChartHighlight();
            });
        });
    }


    highlightChartElement(elementId) {
        let foundItem = null;

        for (const program of this.programsData) {
            // Проверяем программу
            if (program.scheduledProgramId === elementId) {
                foundItem = program;
                break;
            }

            // Проверяем сегменты и их графику
            for (const segment of program.segments) {
                if (segment.scheduledProgramId === elementId) {
                    foundItem = segment;
                    break;
                }

                if (segment.graphicsItems && segment.graphicsItems.length) {
                    const graphic = segment.graphicsItems.find(g => g.id === elementId);
                    if (graphic) {
                        foundItem = graphic;
                        break;
                    }
                }
            }

            if (foundItem) break;

            // Проверяем блоки программы
            if (program.blocks && program.blocks.length) {
                // Ищем сам блок
                const block = program.blocks.find(b => b.scheduledProgramId === elementId);
                if (block) {
                    foundItem = block;
                    break;
                }

                // Ищем advert внутри блока - если нашли, подсвечиваем сам блок
                for (const block of program.blocks) {
                    const advert = block.items.find(i => i.scheduledProgramId === elementId);
                    if (advert) {
                        foundItem = block;
                        break;
                    }
                }
            }

            if (foundItem) break;
        }

        if (foundItem) {
            this.hoveredItem = foundItem;
            this.draw();
        } else {
            console.log('No item found for id:', elementId);
        }
    }

    programsData() {
        // Собираем все элементы для отрисовки (аналогично тому, как в draw)
        const items = [];

        this.programsData.forEach(program => {
            const programStart = this.parseDateTime(program.startTime);
            const programDuration = Math.floor(parseInt(program.duration) / 25);

            items.push({
                id: program.scheduledProgramId,
                type: 'program',
                level: 1,
                start: programStart,
                end: programStart + programDuration,
                name: program.name,
                originalData: program
            });

            program.segments.forEach(segment => {
                const segmentStart = this.parseDateTime(segment.startTime);
                const segmentDuration = Math.floor(parseInt(segment.duration) / 25);

                items.push({
                    id: segment.scheduledProgramId,
                    type: 'segment',
                    level: 1,
                    start: segmentStart,
                    end: segmentStart + segmentDuration,
                    name: segment.name,
                    parentId: program.scheduledProgramId,
                    originalData: segment
                });

                // Графика
                if (program.graphics && Array.isArray(program.graphics)) {
                    program.graphics.forEach(graphic => {
                        const graphicStart = segmentStart + (graphic.start || 0);
                        const graphicEnd = segmentStart + (graphic.end || (graphic.start + 10));

                        items.push({
                            id: graphic.id || `${segment.scheduledProgramId}_graphic_${Date.now()}`,
                            type: 'graphic',
                            level: graphic.level || 2,
                            start: graphicStart,
                            end: graphicEnd,
                            name: graphic.alias || graphic.name || 'Графика',
                            segmentId: segment.scheduledProgramId,
                            originalData: graphic
                        });
                    });
                }

                // Блоки
                program.blocks.forEach(block => {
                    const blockStart = this.parseDateTime(block.startTime);
                    const blockDuration = Math.floor(parseInt(block.duration) / 25);

                    items.push({
                        id: block.scheduledProgramId,
                        type: 'block',
                        level: 3,
                        start: blockStart,
                        end: blockStart + blockDuration,
                        name: block.name || 'Промо-блок',
                        segmentId: segment.scheduledProgramId,
                        originalData: block
                    });
                });
            });
        });

        return items;
    }

    clearChartHighlight() {
        this.hoveredItem = null;
        this.draw();
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
            const deltaX = e.clientX - this.dragStartX;
            const deltaHours = (deltaX / this.width) * (this.endHour - this.startHour);

            let newStartHour = this.dragStartHour - deltaHours;
            newStartHour = Math.round(newStartHour * 6) / 6;

            const range = this.endHour - this.startHour;
            this.startHour = Math.max(0, Math.min(24 - range, newStartHour));
            this.endHour = this.startHour + range;

            this.draw();
            this.updateTimeRange();
        } else {
            const hoveredItem = this.findItemAt(mouseX, mouseY);

            if (hoveredItem) {
                const isSameItem = this.hoveredItem &&
                    this.hoveredItem.scheduledProgramId === hoveredItem.scheduledProgramId &&
                    this.hoveredItem.type === hoveredItem.type;

                if (!isSameItem) {
                    this.hoveredItem = hoveredItem;
                    this.showTooltip(hoveredItem, e.clientX, e.clientY);
                    this.highlightRow(hoveredItem);
                    this.canvas.style.cursor = 'pointer';
                    this.draw();
                }
            } else {
                if (this.hoveredItem) {
                    this.hoveredItem = null;
                    this.hideTooltip();
                    this.clearRowHighlight();
                    this.canvas.style.cursor = 'grab';
                    this.draw();
                }
            }
        }
    }

    handleMouseUp() {
        this.isDragging = false;
        this.canvas.style.cursor = 'grab';
    }

    handleMouseLeave() {
        this.isDragging = false;
        this.hoveredItem = null;
        this.hideTooltip();
        this.clearRowHighlight();
        this.canvas.style.cursor = 'default';
        this.draw();
    }

    handleWheel(e) {
        e.preventDefault();

        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseXRatio = mouseX / rect.width;

        const centerHour = this.startHour + mouseXRatio * (this.endHour - this.startHour);

        const delta = e.deltaY > 0 ? 1.1 : 0.9;
        let newRange = (this.endHour - this.startHour) * delta;

        newRange = Math.max(2, Math.min(24, newRange));
        newRange = Math.round(newRange * 2) / 2;

        let newStartHour = centerHour - newRange * mouseXRatio;
        newStartHour = Math.max(0, Math.min(24 - newRange, newStartHour));
        newStartHour = Math.round(newStartHour * 6) / 6;

        this.startHour = newStartHour;
        this.endHour = this.startHour + newRange;

        this.draw();
        this.updateTimeRange();
    }

    findItemAt(x, y) {
        const totalHours = this.endHour - this.startHour;
        const baseY = this.height - 30;

        const items = [];

        this.programsData.forEach(program => {
            // Сегменты (zIndex 2) - добавляем первыми для приоритета
            program.segments.forEach(segment => {
                items.push({
                    scheduledProgramId: segment.scheduledProgramId,
                    type: segment.type,
                    level: segment.graphicsLevel,
                    start: segment.startSeconds,
                    end: segment.endSeconds,
                    yStart: baseY - 30,
                    yEnd: baseY,
                    zIndex: 2,
                    isSegment: true
                });

                // Графика сегмента (zIndex 3)
                if (segment.graphicsItems && segment.graphicsItems.length) {
                    segment.graphicsItems.forEach(graphic => {
                        const graphicY = baseY - this.levelHeights[graphic.graphicsLevel] - 30;
                        items.push({
                            scheduledProgramId: graphic.id,
                            type: graphic.type,
                            level: graphic.graphicsLevel,
                            start: graphic.startSeconds,
                            end: graphic.endSeconds,
                            yStart: graphicY,
                            yEnd: graphicY + 30,
                            zIndex: 3,
                            isGraphic: true
                        });
                    });
                }
            });

            // Блоки (zIndex 3)
            program.blocks.forEach(block => {
                const blockY = baseY - this.levelHeights[block.graphicsLevel] - 30;
                items.push({
                    scheduledProgramId: block.scheduledProgramId,
                    type: block.type,
                    level: block.graphicsLevel,
                    start: block.startSeconds,
                    end: block.endSeconds,
                    yStart: blockY,
                    yEnd: blockY + 30,
                    zIndex: 3,
                    isBlock: true
                });
            });

            // Программы (zIndex 1) - добавляем последними
            items.push({
                scheduledProgramId: program.scheduledProgramId,
                type: program.type,
                level: program.graphicsLevel,
                start: program.startSeconds,
                end: program.endSeconds,
                yStart: baseY - 60,
                yEnd: baseY,
                zIndex: 1,
                isProgram: true
            });
        });

        // Сортируем по zIndex (от большего к меньшему - сначала верхние)
        const sortedItems = [...items].sort((a, b) => b.zIndex - a.zIndex);

        for (const item of sortedItems) {
            const startX = ((item.start / 3600 - this.startHour) / totalHours) * this.width;
            const endX = ((item.end / 3600 - this.startHour) / totalHours) * this.width;
            let width = endX - startX;

            let checkStartX = startX;
            let checkWidth = width;

            const MIN_WIDTH = 8;
            if ((item.type === 'graphic' || item.type === 'block') && width < MIN_WIDTH) {
                const centerX = (startX + endX) / 2;
                checkStartX = centerX - MIN_WIDTH/2;
                checkWidth = MIN_WIDTH;
            }

            if (x >= checkStartX && x <= checkStartX + checkWidth &&
                y >= item.yStart && y <= item.yEnd) {
                return this.findFullItemById(item.scheduledProgramId);
            }
        }

        return null;
    }

    findFullItemById(scheduledProgramId) {
        for (const program of this.programsData) {
            if (program.scheduledProgramId === scheduledProgramId) return program;

            // Поиск в сегментах
            for (const segment of program.segments) {
                if (segment.scheduledProgramId === scheduledProgramId) return segment;

                // Поиск в графике сегмента
                if (segment.graphicsItems) {
                    const graphic = segment.graphicsItems.find(g => g.id === scheduledProgramId);
                    if (graphic) return graphic;
                }
            }

            // Поиск в блоках программы
            const block = program.blocks.find(b => b.scheduledProgramId === scheduledProgramId);
            if (block) return block;
        }
        return null;
    }

    handleClick(e) {
        if (this.isDragging) return;

        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.width / rect.width;
        const scaleY = this.height / rect.height;

        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;

        const clickedItem = this.findItemAt(mouseX, mouseY);

        if (clickedItem) {
            let selector = null;

            if (clickedItem.type === 'block') {
                // Для блока - ищем элемент с классом block
                selector = `[data-scheduled-program-id="${clickedItem.scheduledProgramId}"]`;
            } else if (clickedItem.type === 'segment') {
                selector = `[data-scheduled-program-id="${clickedItem.scheduledProgramId}"]`;
            } else if (clickedItem.type === 'program') {
                selector = `[data-scheduled-program-id="${clickedItem.scheduledProgramId}"]`;
            } else if (clickedItem.type === 'graphic') {
                selector = `[data-scheduled-program-id="${clickedItem.segmentId}"]`;
            }

            if (selector) {
                const row = document.querySelector(selector);
                if (row) {
                    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    row.classList.add('timeline-hover');

                    setTimeout(() => {
                    row.classList.remove('timeline-hover');
                    row.style.backgroundColor = '';
                }, 2000);
                }
            }
        }
    }

    showTooltip(item, clientX, clientY) {
        const style = this.levelStyles[item.level] || this.levelStyles[2];
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';

        let content = '';
        if (item.type === 'block') {
            // Для блока показываем список рекламных роликов
            let itemsList = '';
            if (item.originalData) {
                itemsList = `<div>• ${item.name || 'Промо-блок'}</div>`;
            }

            content = `
                <div style="color: ${style.stroke}; font-weight: 600; margin-bottom: 6px;">📦 ${item.name || 'Промо-блок'}</div>
                <hr style="margin: 6px 0;">
                <div style="font-size: 11px;">🕐 ${this.formatTime(item.start)} - ${this.formatTime(item.end)}</div>
                <div style="font-size: 11px;">⏱ Длительность: ${this.formatTime(item.duration)}</div>
            `;
        } else if (item.type === 'segment') {
            content = `
                <div style="font-weight: 600; margin-bottom: 4px;">📺 ${item.name}</div>
                <hr style="margin: 4px 0;">
                <div style="font-size: 11px;">🕐 ${this.formatTime(item.start)} - ${this.formatTime(item.end)}</div>
                <div style="font-size: 11px;">⏱ Длительность: ${this.formatTime(item.duration)}</div>
            `;
        } else if (item.type === 'program') {
            content = `
                <div style="font-weight: 600; margin-bottom: 4px;">🎬 ${item.name}</div>
                <hr style="margin: 4px 0;">
                <div style="font-size: 11px;">🕐 ${this.formatTime(item.start)} - ${this.formatTime(item.end)}</div>
                <div style="font-size: 11px;">⏱ Длительность: ${this.formatTime(item.duration)}</div>
            `;
        } else if (item.type === 'graphic') {
            content = `
                <div style="color: ${style.stroke}; font-weight: 600; margin-bottom: 4px;">✨ ${item.name}</div>
                <hr style="margin: 4px 0;">
                <div style="font-size: 11px;">🕐 ${this.formatTime(item.start)} - ${this.formatTime(item.end)}</div>
                <div style="font-size: 11px;">⏱ Длительность: ${this.formatTime(item.duration)}</div>
            `;
        }

        this.tooltip.innerHTML = content;
        this.tooltip.style.display = 'block';

        // Адаптивное позиционирование
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let left = clientX + 15;
        let top = clientY - tooltipRect.height - 10;

        if (left + tooltipRect.width > viewportWidth) {
            left = clientX - tooltipRect.width - 15;
        }

        if (top < 0) {
            top = clientY + 15;
        }

        if (top + tooltipRect.height > viewportHeight) {
            top = viewportHeight - tooltipRect.height - 10;
        }

        this.tooltip.style.left = left + 'px';
        this.tooltip.style.top = top + 'px';
    }

    hideTooltip() {
        this.tooltip.style.display = 'none';
    }

    highlightRow(item) {
        this.clearRowHighlight();

        let selector = null;

        if (item.type === 'block') {
            selector = `[data-scheduled-program-id="${item.scheduledProgramId}"]`;
        } else if (item.type === 'segment') {
            selector = `[data-scheduled-program-id="${item.scheduledProgramId}"]`;
        } else if (item.type === 'program') {
            selector = `[data-scheduled-program-id="${item.scheduledProgramId}"]`;
        } else if (item.type === 'graphic') {
            selector = `[data-scheduled-program-id="${item.segmentId}"]`;
        }

        if (selector) {
            const rows = document.querySelectorAll(selector);
            rows.forEach(row => {
                row.classList.add('timeline-hover');
                row.classList.add('bg-warning-subtle');
                row.classList.add('border-start');
                row.classList.add('border-warning');
                row.classList.add('border-3');
            });
        }
    }

    clearRowHighlight() {
        document.querySelectorAll('.timeline-hover').forEach(el => {
            el.classList.remove('timeline-hover');
            el.classList.remove('bg-warning-subtle');
            el.classList.remove('border-start');
            el.classList.remove('border-warning');
            el.classList.remove('border-3');
            el.style.backgroundColor = ''; // сбрасываем фон
        });
    }

    formatTime(seconds) {
        const totalSeconds = Math.floor(seconds);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const secs = totalSeconds % 60;

        if (hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else if (minutes > 0) {
            return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `00:${secs.toString().padStart(2, '0')}`;
        }
    }

    zoomIn() {
        const range = this.endHour - this.startHour;
        if (range > 2) {
            const center = (this.startHour + this.endHour) / 2;
            let newRange = Math.max(2, range - 4);
            newRange = Math.round(newRange * 2) / 2;

            this.startHour = Math.max(0, center - newRange/2);
            this.startHour = Math.round(this.startHour * 6) / 6;
            this.endHour = this.startHour + newRange;

            this.draw();
            this.updateTimeRange();
        }
    }

    zoomOut() {
        const range = this.endHour - this.startHour;
        if (range < 24) {
            const center = (this.startHour + this.endHour) / 2;
            let newRange = Math.min(24, range + 4);
            newRange = Math.round(newRange * 2) / 2;

            this.startHour = Math.max(0, center - newRange/2);
            this.startHour = Math.round(this.startHour * 6) / 6;
            this.endHour = this.startHour + newRange;

            this.draw();
            this.updateTimeRange();
        }
    }

    setZoom(hours) {
        const center = (this.startHour + this.endHour) / 2;
        let newRange = Math.max(2, Math.min(24, hours));
        newRange = Math.round(newRange * 2) / 2;

        this.startHour = Math.max(0, center - newRange/2);
        this.startHour = Math.round(this.startHour * 6) / 6;
        this.endHour = this.startHour + newRange;

        this.draw();
        this.updateTimeRange();
    }

    updateTimeRange() {
        const rangeElement = document.getElementById('timelineTimeRange');
        if (rangeElement) {
            const startStr = this.formatTime(this.startHour * 3600);
            const endStr = this.formatTime(this.endHour * 3600);
            rangeElement.textContent = `${startStr} - ${endStr}`;
        }
    }
}

// Создаём экземпляр
window.timelineManager = new TimelineManager();
console.log('TimelineManager instance created');