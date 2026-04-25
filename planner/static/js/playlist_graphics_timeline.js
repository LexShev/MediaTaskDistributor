// static/js/timeline_manager.js

class TimelineManager {
    constructor() {
        console.log('TimelineManager constructor called');

        this.canvas = null;
        this.ctx = null;
        this.width = 1370;
        this.height = 230;

        this.paddingLeft = 1;   // отступ в часах
        this.paddingRight = 1;

        // Минимальный и максимальный диапазон
        this.minHour = -this.paddingLeft;
        this.maxHour = 24 + this.paddingRight;

        // Масштаб и панорамирование
        this.startHour = this.minHour;
        this.endHour = this.maxHour;
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
                fill: 'rgba(255, 193, 7, 0.15)',
                stroke: '#ffc107',
                text: '#997404'
            },
            4: {
                fill: 'rgba(25, 135, 84, 0.15)',
                stroke: '#198754',
                text: '#146c43'
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

        // Проверяем, есть ли данные
        if (this.programsData.length === 0) {
            console.log('No data to display');
            this.clear();
            return;
        }

        this.draw();
        this.addEventListeners();
        this.updateTimeRange();
    }

    destroy() {
        console.log('TimelineManager destroy started');

        // Очищаем canvas
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.width, this.height);
        }

        // Очищаем данные
        this.programsData = [];
        this.hoveredItem = null;
        this.currentTimeLine = null;
        this.isHoveringCurrentTime = false;
        this.drawCurrentTimeLineHighlight = false;

        // Удаляем tooltip, если он существует
        if (this.tooltip && this.tooltip.parentNode) {
            this.tooltip.parentNode.removeChild(this.tooltip);
            this.tooltip = null;
        }

        // Удаляем обработчики событий с canvas
        if (this.canvas) {
            const newCanvas = this.canvas.cloneNode(true);
            this.canvas.parentNode.replaceChild(newCanvas, this.canvas);
            this.canvas = newCanvas;
        }

        console.log('TimelineManager destroyed');
    }

    isInitialized() {
        // Проверяем, инициализирован ли менеджер
        return this.canvas !== null &&
               this.ctx !== null &&
               this.programsData !== null &&
               this.programsData.length > 0;
    }

    clear() {
        // Очищаем данные без полного уничтожения
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.width, this.height);
        }

        this.programsData = [];
        this.hoveredItem = null;
        this.currentTimeLine = null;

        // Очищаем canvas белым фоном
        if (this.ctx) {
            const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
            this.ctx.fillStyle = isDark ? '#212529' : '#f8f9fa';
            this.ctx.fillRect(0, 0, this.width, this.height);
        }

        // Скрываем tooltip
        if (this.tooltip) {
            this.tooltip.style.display = 'none';
        }

    }

    reinit() {
        // Переинициализация
        this.destroy();
        this.init();
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

         return new Date(dateTimeStr.replace(' ', 'T'));
    }

    // parseStartTime(startTimeStr) {
    //     // Формат: число в кадрах (может быть отрицательным для прошлых суток)
    //     // Возвращаем количество секунд от 00:00 с учетом перехода через сутки
    //     const frames = parseInt(startTimeStr);
    //     if (isNaN(frames)) return 0;
    //
    //     // Переводим кадры в секунды (25 кадров = 1 секунда)
    //     return frames / 25;
    // }

    loadDataFromDOM() {
        const programs = document.querySelectorAll('.program');
        this.programsData = [];

        programs.forEach(program => {
            const scheduledProgramId = program?.dataset.scheduledProgramId;
            const programStartFrame = parseInt(program.dataset.startTime);
            const programDateTime = this.parseDateTime(program.dataset.dateTime);

            let totalFrames  = 0;

            const programObj = {
                scheduledProgramId: scheduledProgramId,
                name: program?.dataset.name,
                startFrame: programStartFrame,
                endFrame: 0,
                startDateTime: programDateTime,
                endDateTime: null,
                duration: program?.dataset.duration,
                totalProgramDuration: 0,
                type: 'program',
                graphicsLevel: program?.dataset.graphicsLevel || 1,
                segments: [],
                blocks: []  // блоки на уровне программы
            };

            // Сегменты внутри программы
            const segments = program.querySelectorAll('.segment');
            segments.forEach(segment => {
                const segmentDuration = parseInt(segment.dataset.duration);
                totalFrames += segmentDuration;

                const segmentStartFrame = parseInt(segment.dataset.startTime);
                const segmentEndFrame = segmentStartFrame + segmentDuration;
                const segmentDateTime = this.parseDateTime(segment.dataset.dateTime);
                // const graphicsStr = segment?.dataset.graphics;
                // let graphics = null;

                // if (graphicsStr) {
                //     try {
                //         graphics = JSON.parse(graphicsStr.trim());
                //     } catch (e) {
                //         console.warn('Failed to parse JSON for segment', segment, e);
                //     }
                // }

                const segmentObj = {
                    scheduledProgramId: segment?.dataset.scheduledProgramId,
                    parentId: scheduledProgramId,
                    name: segment?.dataset.name,
                    startFrame: segmentStartFrame,
                    endFrame: segmentEndFrame,
                    startDateTime: segmentDateTime,
                    endDateTime: new Date(segmentDateTime.getTime() + (segmentDuration / 25) * 1000),
                    duration: segment?.dataset.duration,
                    type: 'segment',
                    graphicsLevel: segment?.dataset.graphicsLevel || 1,
                    graphicsItems: [],  // графические элементы внутри сегмента
                    segmentId: segment.dataset.scheduledProgramId
                };

                // Получаем общее количество сегментов
                const totalSegments = segments.length;

                // Генерируем графику для сегмента
                const generatedGraphics = this.generateGraphicsForSegment(
                    segmentObj,
                    programObj,
                    Array.from(segments).indexOf(segment),
                    totalSegments
                );

                // Добавляем сгенерированную графику
                generatedGraphics.forEach(g => {
                    const absoluteStartFrame = segmentObj.startFrame + g.startFrameOffset;
                    const absoluteEndFrame = segmentObj.startFrame + g.endFrameOffset;

                    segmentObj.graphicsItems.push({
                        id: g.id,
                        name: g.name,
                        startFrame: absoluteStartFrame,
                        endFrame: absoluteEndFrame,
                        startDateTime: new Date(segmentObj.startDateTime.getTime() + (g.startFrameOffset / 25) * 1000),
                        endDateTime: new Date(segmentObj.startDateTime.getTime() + (g.endFrameOffset / 25) * 1000),
                        graphicsLevel: g.level,
                        type: 'graphic',
                        segmentId: segmentObj.scheduledProgramId
                    });
                });

                programObj.segments.push(segmentObj);
            });

            // Блоки промо внутри программы
            const blocks = program.querySelectorAll('.block');
            blocks.forEach(block => {
                const blockId = block?.dataset.scheduledProgramId;
                const blockStartFrame = parseInt(block.dataset.startTime);
                const blockDateTime = this.parseDateTime(block.dataset.dateTime);

                // Собираем все рекламные ролики внутри блока
                const adverts = block.querySelectorAll('.advert, .license');
                let blockTotalFrames = 0;
                const blockItems = [];

                adverts.forEach(advert => {
                    const advertFrames = parseInt(advert.dataset.duration);
                    blockTotalFrames += advertFrames;
                    totalFrames += advertFrames;
                    const advertStartFrame = parseInt(advert.dataset.startTime);
                    const advertEndFrame = advertStartFrame + advertFrames;
                    const advertDateTime = this.parseDateTime(advert.dataset.dateTime);

                    blockItems.push({
                        scheduledProgramId: advert?.dataset.scheduledProgramId,
                        parentId: blockId,
                        name: advert?.dataset.name,
                        startFrame: advertStartFrame,
                        endFrame: advertEndFrame,
                        startDateTime: advertDateTime,
                        endDateTime: new Date(advertDateTime.getTime() + (advertFrames / 25) * 1000),
                        duration: advert?.dataset.duration,
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
                        duration: block?.dataset.duration,
                        startFrame: blockStartFrame,
                        endFrame: blockStartFrame + blockTotalFrames,
                        startDateTime: blockDateTime,
                        endDateTime: new Date(blockDateTime.getTime() + (blockTotalFrames / 25) * 1000),
                        graphicsLevel: 2,
                        type: 'block',
                        items: blockItems  // сохраняем список реклам для тултипа
                    });
                }
            });
            programObj.totalProgramDuration = totalFrames;
            programObj.endFrame = programObj.startFrame + totalFrames;
            programObj.endDateTime = new Date(programDateTime.getTime() + (totalFrames / 25) * 1000);
            this.programsData.push(programObj);
        });

    }

    generateGraphicsForSegment(segment, program, segmentIndex, totalSegments) {
        const graphics = [];

        // Работаем только с кадрами
        const segmentStartFrame = segment.startFrame;
        const segmentEndFrame = segment.endFrame;
        const segmentDurationFrames = segmentEndFrame - segmentStartFrame;
        const segmentDurationSeconds = segmentDurationFrames / 25;

        // Получаем данные из DOM элемента сегмента
        const segmentElement = document.querySelector(`[data-scheduled-program-id="${segment.scheduledProgramId}"]`);
        const isNarc = segmentElement?.dataset.isNarc === 'true' || true;
        const isInoagent = segmentElement?.dataset.isInoagent === 'true';
        const isMeta = segmentElement?.dataset.isMeta === 'true';

        // Определяем тип контента по названию программы или сегмента
        const isMovie = program.name?.toLowerCase().includes('фильм') ||
                        segment.name?.toLowerCase().includes('фильм');
        const isSeries = program.name?.toLowerCase().includes('сериал') ||
                         segment.name?.toLowerCase().includes('сериал');
        const isKids = program.name?.toLowerCase().includes('детский') ||
                       segment.name?.toLowerCase().includes('детский');
        const isCinemaChannel = program.name?.toLowerCase().includes('кино+') ||
                                program.name?.toLowerCase().includes('крепкий') ||
                                program.name?.toLowerCase().includes('мировой');

        // Определяем канал
        const channelName = document.getElementById('current_schedule')?.textContent || '';

        // 1. Возрастные 0+, 6+, 12+ (всегда в начале сегмента)
        graphics.push({
            id: `age_${segment.scheduledProgramId}`,
            name: 'Возрастная маркировка 0+/6+/12+',
            alias: 'Возрастная',
            startFrameOffset: 0,  // смещение от начала сегмента в кадрах
            endFrameOffset: 12 * 25,  // 12 секунд * 25 кадров = 300 кадров
            level: 4
        });

        // 2. Возрастные 16+, 18+ + Курение
        if (segmentElement?.dataset.ageRating === '16' || segmentElement?.dataset.ageRating === '18') {
            graphics.push({
                id: `age_16_18_${segment.scheduledProgramId}`,
                name: 'Возрастная маркировка 16+/18+ + Курение',
                alias: '16+/18+',
                startFrameOffset: 0,
                endFrameOffset: 12 * 25,
                level: 4
            });
        }

        // 3. Иноагенты + возрастная
        if (isInoagent) {
            graphics.push({
                id: `inoagent_${segment.scheduledProgramId}`,
                name: 'Иноагенты + возрастная',
                alias: 'Иноагенты',
                startFrameOffset: 0,
                endFrameOffset: 12 * 25,
                level: 4
            });
        }

        // 4. Мета + возрастная
        if (isMeta) {
            graphics.push({
                id: `meta_${segment.scheduledProgramId}`,
                name: 'Мета + возрастная',
                alias: 'Мета',
                startFrameOffset: 0,
                endFrameOffset: 12 * 25,
                level: 4
            });
        }

        // 5. Иноагенты + Мета + возрастная
        if (isInoagent && isMeta) {
            graphics.push({
                id: `inoagent_meta_${segment.scheduledProgramId}`,
                name: 'Иноагенты + Мета + возрастная',
                alias: 'Иноагенты/Мета',
                startFrameOffset: 0,
                endFrameOffset: 20 * 25,  // 20 секунд
                level: 4
            });
        }

        // 6. Сейчас в эфире (весь сегмент)
        graphics.push({
            id: `air_now_${segment.scheduledProgramId}`,
            name: 'Сейчас в эфире',
            alias: 'Сейчас в эфире',
            startFrameOffset: 0,
            endFrameOffset: segmentDurationFrames,
            level: 3
        });

        // 7. Далее в эфире (последний сегмент)
        if (segmentIndex === totalSegments - 1) {
            let offsetBeforeEndSeconds = 0;
            if (isMovie && !isKids) offsetBeforeEndSeconds = 10 * 60; // 10 минут
            else if (isSeries && !isKids) offsetBeforeEndSeconds = 5 * 60; // 5 минут
            else if (isSeries && isCinemaChannel) offsetBeforeEndSeconds = 2 * 60; // 2 минуты
            else if (isKids && isMovie) offsetBeforeEndSeconds = 10 * 60; // 10 минут
            else if (isKids && isSeries) offsetBeforeEndSeconds = 30; // 30 секунд

            if (offsetBeforeEndSeconds > 0 && segmentDurationSeconds > offsetBeforeEndSeconds) {
                const offsetBeforeEndFrames = offsetBeforeEndSeconds * 25;
                const startFrameOffset = segmentDurationFrames - offsetBeforeEndFrames;
                graphics.push({
                    id: `next_air_${segment.scheduledProgramId}`,
                    name: 'Далее в эфире',
                    alias: 'Далее',
                    startFrameOffset: startFrameOffset,
                    endFrameOffset: startFrameOffset + (12 * 25),
                    level: 4
                });
            }
        }

        // 8. Сегодня в эфире (первый сегмент)
        if (segmentIndex === 0) {
            let startOffsetSeconds = 0;
            const currentHour = new Date().getHours();

            if (channelName.includes('Кино+') && currentHour >= 8 && currentHour < 19.5) {
                startOffsetSeconds = 5 * 60;
            } else if ((channelName.includes('Крепкий') || channelName.includes('Мировой')) && currentHour >= 8 && currentHour < 20.5) {
                startOffsetSeconds = segmentDurationSeconds * 0.5;
            } else if (channelName.includes('Мужской') && currentHour >= 8 && currentHour < 19.5) {
                startOffsetSeconds = segmentDurationSeconds * 0.5;
            } else if (channelName.includes('Наше детство') && currentHour >= 8 && currentHour < 18.5) {
                startOffsetSeconds = 3 * 60;
            } else if (channelName.includes('Наше родное кино') && currentHour >= 8 && currentHour < 20.5) {
                startOffsetSeconds = 5 * 60;
            } else if (channelName.includes('Планета дети') && currentHour >= 8 && currentHour < 17.5) {
                startOffsetSeconds = 5 * 60;
            } else if (channelName.includes('Романтичный') && currentHour >= 8 && currentHour < 20.5) {
                startOffsetSeconds = segmentDurationSeconds * 0.5;
            } else if (channelName.includes('Семейный') && currentHour >= 8 && currentHour < 20.5) {
                startOffsetSeconds = 5 * 60;
            } else if (channelName.includes('Советский будни') && currentHour >= 8 && currentHour < 19) {
                startOffsetSeconds = 5 * 60;
            } else if (channelName.includes('Советский выходные') && currentHour >= 8 && currentHour < 17) {
                startOffsetSeconds = 5 * 60;
            }

            if (startOffsetSeconds > 0 && startOffsetSeconds < segmentDurationSeconds) {
                const startFrameOffset = startOffsetSeconds * 25;
                graphics.push({
                    id: `today_air_${segment.scheduledProgramId}`,
                    name: 'Сегодня в эфире',
                    alias: 'Сегодня',
                    startFrameOffset: startFrameOffset,
                    endFrameOffset: startFrameOffset + (10 * 25),
                    level: 4
                });
            }
        }

        // 9. Завтра в эфире (последний сегмент)
        if (segmentIndex === totalSegments - 1) {
            const currentHour = new Date().getHours();
            if (currentHour >= 7 && currentHour < 23.75) {
                const startFrameOffset = segmentDurationFrames - (15 * 25); // за 15 секунд до конца
                if (startFrameOffset > 0) {
                    graphics.push({
                        id: `tomorrow_air_${segment.scheduledProgramId}`,
                        name: 'Завтра в эфире',
                        alias: 'Завтра',
                        startFrameOffset: startFrameOffset - (20 * 25),
                        endFrameOffset: startFrameOffset + (10 * 25),
                        level: 5
                    });
                }
            }
        }

        // 10. Телеграм (первый сегмент)
        if (segmentIndex === 0) {
            let startFrameOffset = 0;
            if (isMovie && !isKids) {
                startFrameOffset = 9 * 60 * 25; // через 9 минут в кадрах
            } else if (isSeries) {
                startFrameOffset = segmentDurationFrames * 0.5;
            }

            if (startFrameOffset > 0 && startFrameOffset < segmentDurationFrames) {
                graphics.push({
                    id: `telegram_${segment.scheduledProgramId}`,
                    name: 'Телеграм',
                    alias: 'Telegram',
                    startFrameOffset: startFrameOffset,
                    endFrameOffset: startFrameOffset + (18 * 25),
                    level: 4
                });
            }
        }

        // 11. Наркотики (через 21 секунду после начала)
        if (isNarc) {
            graphics.push({
                id: `narc_${segment.scheduledProgramId}`,
                name: 'Наркотики',
                alias: 'Наркотики',
                startFrameOffset: 21 * 25,
                endFrameOffset: 31 * 25,
                level: 5
            });
        }

        // Фильтруем дубликаты
        return graphics.filter((g, index, self) =>
            index === self.findIndex(g2 => g2.startFrameOffset === g.startFrameOffset && g2.endFrameOffset === g.endFrameOffset)
        );
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
                start: program.startFrame,
                end: program.endFrame,
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
                    start: segment.startFrame,
                    end: segment.endFrame,
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
                            start: graphic.startFrame,
                            end: graphic.endFrame,
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
                    start: block.startFrame,
                    end: block.endFrame,
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
            const startSeconds = item.start / 25;
            const endSeconds = item.end / 25;
            const startX = ((startSeconds / 3600 - this.startHour) / totalHours) * this.width;
            const endX = ((endSeconds / 3600 - this.startHour) / totalHours) * this.width;
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
                    const maxLen = 30;
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
                    const maxLen = 30;
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

        // Вертикальные линии
        ctx.lineWidth = 1;
        ctx.font = '10px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';

        // Определяем диапазон часов для отображения
        const startHourFloor = Math.floor(this.startHour);
        const endHourCeil = Math.ceil(this.endHour);

        const formatHourLabel = (hour) => {
            if (hour < 0) {
                const absHour = Math.abs(hour);
                const hours = Math.floor(absHour);
                const minutes = Math.floor((absHour % 1) * 60);
                if (minutes === 0) {
                    return `-${hours.toString().padStart(2, '0')}:00`;
                } else {
                    return `-${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
                }
            } else if (hour > 24) {
                const overHour = hour - 24;
                const hours = Math.floor(overHour);
                const minutes = Math.floor((overHour % 1) * 60);
                if (minutes === 0) {
                    return `+${hours.toString().padStart(2, '0')}:00`;
                } else {
                    return `+${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
                }
            } else {
                const hours = Math.floor(hour);
                const minutes = Math.floor((hour % 1) * 60);
                if (minutes === 0) {
                    return `${hours.toString().padStart(2, '0')}:00`;
                } else {
                    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
                }
            }
        };

        // Рисуем линии для каждого часа и получаса
        for (let hour = startHourFloor; hour <= endHourCeil; hour += 0.5) {
            const x = ((hour - this.startHour) / totalHours) * this.width;

            if (x >= 0 && x <= this.width) {
                const isFullHour = Math.abs(hour - Math.round(hour)) < 0.01;
                const isHalfHour = Math.abs(hour - Math.floor(hour) - 0.5) < 0.01;

                ctx.beginPath();

                if (isFullHour) {
                    // Часовые линии - более заметные
                    ctx.strokeStyle = isDark ? '#6c757d' : '#adb5bd';
                    ctx.lineWidth = 1;
                } else if (isHalfHour) {
                    // Получасовые линии - пунктирные и более светлые
                    ctx.strokeStyle = isDark ? 'rgba(73, 80, 87, 0.5)' : 'rgba(206, 212, 218, 0.6)';
                    ctx.lineWidth = 0.8;
                    ctx.setLineDash([3, 5]);
                } else {
                    // Пропускаем другие интервалы
                    continue;
                }

                ctx.moveTo(x, 0);
                ctx.lineTo(x, this.height);
                ctx.stroke();

                // Сбрасываем пунктир после отрисовки
                if (isHalfHour) {
                    ctx.setLineDash([]);
                }

                // Подпись только для часовых меток
                if (isFullHour) {
                    ctx.fillStyle = isDark ? '#dee2e6' : '#495057';
                    ctx.fillText(formatHourLabel(hour), x, 25);
                }
            }
        }

        // Линия текущего времени (только для сегодняшней даты)
        try {
            const currentDateInput = document.getElementById('current_schedule_day_date');
            if (currentDateInput && currentDateInput.dataset.currentScheduleDayDate) {
                const scheduleDate = currentDateInput.dataset.currentScheduleDayDate;
                const today = new Date().toISOString().split('T')[0];

                if (scheduleDate === today) {
                    const now = new Date();
                    const currentHour = now.getHours() + now.getMinutes() / 60 + now.getSeconds() / 3600;

                    if (currentHour >= this.startHour && currentHour <= this.endHour) {
                        const x = ((currentHour - this.startHour) / totalHours) * this.width;

                        // Сохраняем информацию о линии текущего времени для обработки наведения
                        this.currentTimeLine = {
                            x: x,
                            hour: currentHour
                        };

                        ctx.beginPath();
                        ctx.strokeStyle = '#dc3545';
                        ctx.lineWidth = 1.5;
                        ctx.setLineDash([5, 5]);
                        ctx.moveTo(x, 0);
                        ctx.lineTo(x, this.height);
                        ctx.stroke();
                        ctx.setLineDash([]);
                    } else {
                        this.currentTimeLine = null;
                    }
                } else {
                    this.currentTimeLine = null;
                }
            } else {
                this.currentTimeLine = null;
            }
        }
        catch (error) {
            console.error(error);
        }

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
            const programStart = this.parseDateTime(program.startFrame);
            const programDuration = parseInt(program.duration);

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
                const segmentStart = this.parseDateTime(segment.startFrame);
                const segmentDuration = parseInt(segment.duration);

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
                    const blockStart = this.parseDateTime(block.startFrame);
                    const blockDuration = parseInt(block.duration);

                    items.push({
                        id: block.scheduledProgramId,
                        type: 'block',
                        level: 3,
                        start: blockStart,
                        end: blockStart + blockDuration,
                        duration: blockDuration,
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
            let newEndHour = newStartHour + (this.endHour - this.startHour);

            // Ограничиваем
            if (newStartHour < this.minHour) {
                newStartHour = this.minHour;
                newEndHour = newStartHour + (this.endHour - this.startHour);
            }
            if (newEndHour > this.maxHour) {
                newEndHour = this.maxHour;
                newStartHour = newEndHour - (this.endHour - this.startHour);
            }

            // Округляем
            this.startHour = Math.round(newStartHour * 6) / 6;
            this.endHour = Math.round(newEndHour * 6) / 6;

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
        const mouseXRatio = Math.max(0, Math.min(1, mouseX / rect.width)); // Ограничиваем от 0 до 1

        const centerHour = this.startHour + mouseXRatio * (this.endHour - this.startHour);

        const range = this.endHour - this.startHour;
        const delta = e.deltaY > 0 ? 1.1 : 0.9;
        let newRange = range * delta;

        // Жесткие границы для диапазона
        const minRange = 1; // минимальный диапазон 1 час
        const maxRange = this.maxHour - this.minHour;
        newRange = Math.max(minRange, Math.min(maxRange, newRange));
        newRange = Math.round(newRange * 2) / 2;

        // Вычисляем новые границы, центрируя по позиции мыши
        let newStartHour = centerHour - newRange * mouseXRatio;
        let newEndHour = newStartHour + newRange;

        // Корректируем, если вышли за пределы
        if (newStartHour < this.minHour) {
            newStartHour = this.minHour;
            newEndHour = newStartHour + newRange;
        }
        if (newEndHour > this.maxHour) {
            newEndHour = this.maxHour;
            newStartHour = newEndHour - newRange;
        }

        // Округляем для плавности
        this.startHour = Math.round(newStartHour * 6) / 6;
        this.endHour = Math.round(newEndHour * 6) / 6;

        // Дополнительная проверка, чтобы startHour и endHour были в пределах
        this.startHour = Math.max(this.minHour, Math.min(this.maxHour - (this.endHour - this.startHour), this.startHour));
        this.endHour = this.startHour + (this.endHour - this.startHour);
        this.endHour = Math.min(this.maxHour, this.endHour);

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
                    start: segment.startFrame,
                    end: segment.endFrame,
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
                            start: graphic.startFrame,
                            end: graphic.endFrame,
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
                    start: block.startFrame,
                    end: block.endFrame,
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
                start: program.startFrame,
                end: program.endFrame,
                yStart: baseY - 60,
                yEnd: baseY,
                zIndex: 1,
                isProgram: true
            });
        });

        // Сортируем по zIndex (от большего к меньшему - сначала верхние)
        const sortedItems = [...items].sort((a, b) => b.zIndex - a.zIndex);

        for (const item of sortedItems) {
            const startSeconds = item.start / 25;
            const endSeconds = item.end / 25;
            const startX = ((startSeconds / 3600 - this.startHour) / totalHours) * this.width;
            const endX = ((endSeconds / 3600 - this.startHour) / totalHours) * this.width;
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

        let content = '';

        if (item.type === 'block') {
            // Для блока показываем список всех элементов внутри
            let itemsList = '';
            if (item.items && item.items.length > 0) {
                item.items.forEach(i => {
                    // Длительность в секундах
                    const durationSeconds = (i.endFrame - i.startFrame) / 25;
                    itemsList += `<div style="font-size: 11px; margin-left: 8px;">• ${i.name || 'Промо'}: ${this.formatTime(durationSeconds)}</div>`;
                });
            }

            // Длительность блока в секундах
            const blockDurationSeconds = (item.endFrame - item.startFrame) / 25;
            const startTimeSeconds = item.startFrame / 25;
            const endTimeSeconds = item.endFrame / 25;

            content = `
                <div style="color: ${style.stroke}; font-weight: 600; margin-bottom: 6px;">${item.name || 'Промо-блок'}</div>
                ${itemsList ? `<div style="margin: 4px 0;">${itemsList}</div><hr style="margin: 4px 0;">` : ''}
                <div style="font-size: 11px;">${this.formatTime(startTimeSeconds)} - ${this.formatTime(endTimeSeconds)}</div>
                <div style="font-size: 11px;">Длительность: ${this.formatTime(blockDurationSeconds)}</div>
            `;
        } else if (item.type === 'segment') {
            const startTimeSeconds = item.startFrame / 25;
            const endTimeSeconds = item.endFrame / 25;
            const durationSeconds = (item.endFrame - item.startFrame) / 25;

            content = `
                <div style="font-weight: 600; margin-bottom: 4px;">${item.name}</div>
                <hr style="margin: 4px 0;">
                <div style="font-size: 11px;">${this.formatTime(startTimeSeconds)} - ${this.formatTime(endTimeSeconds)}</div>
                <div style="font-size: 11px;">Длительность: ${this.formatTime(durationSeconds)}</div>
            `;
        } else if (item.type === 'program') {
            const startTimeSeconds = item.startFrame / 25;
            const endTimeSeconds = item.endFrame / 25;
            const durationSeconds = (item.endFrame - item.startFrame) / 25;

            content = `
                <div style="font-weight: 600; margin-bottom: 4px;">${item.name}</div>
                <hr style="margin: 4px 0;">
                <div style="font-size: 11px;">${this.formatTime(startTimeSeconds)} - ${this.formatTime(endTimeSeconds)}</div>
                <div style="font-size: 11px;">Длительность: ${this.formatTime(durationSeconds)}</div>
            `;
        } else if (item.type === 'graphic') {
            const startTimeSeconds = item.startFrame / 25;
            const endTimeSeconds = item.endFrame / 25;
            const durationSeconds = (item.endFrame - item.startFrame) / 25;

            content = `
                <div style="color: ${style.stroke}; font-weight: 600; margin-bottom: 4px;">${item.name}</div>
                <hr style="margin: 4px 0;">
                <div style="font-size: 11px;">${this.formatTime(startTimeSeconds)} - ${this.formatTime(endTimeSeconds)}</div>
                <div style="font-size: 11px;">Длительность: ${this.formatTime(durationSeconds)}</div>
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

            let newStartHour = center - newRange/2;
            let newEndHour = center + newRange/2;

            // Ограничиваем, но с учетом отступов
            newStartHour = Math.max(this.minHour, newStartHour);
            newEndHour = Math.min(this.maxHour, newEndHour);

            this.startHour = newStartHour;
            this.endHour = newEndHour;

            this.draw();
            this.updateTimeRange();
        }
    }

    zoomOut() {
        const range = this.endHour - this.startHour;
        if (range < (this.maxHour - this.minHour)) {
            const center = (this.startHour + this.endHour) / 2;
            let newRange = Math.min(this.maxHour - this.minHour, range + 4);
            newRange = Math.round(newRange * 2) / 2;

            let newStartHour = center - newRange/2;
            let newEndHour = center + newRange/2;

            // Ограничиваем, но с учетом отступов
            newStartHour = Math.max(this.minHour, newStartHour);
            newEndHour = Math.min(this.maxHour, newEndHour);

            this.startHour = newStartHour;
            this.endHour = newEndHour;

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
            const formatHourWithOffset = (hour) => {
                if (hour < 0) {
                    const absHour = Math.abs(hour);
                    const hours = Math.floor(absHour);
                    const minutes = Math.floor((absHour % 1) * 60);
                    const seconds = Math.floor(((absHour % 1) * 60 % 1) * 60);
                    return `(-${hours.toString().padStart(2, '0')}):${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                } else if (hour > 24) {
                    const overHour = hour - 24;
                    const hours = Math.floor(overHour);
                    const minutes = Math.floor((overHour % 1) * 60);
                    const seconds = Math.floor(((overHour % 1) * 60 % 1) * 60);
                    return `(+${hours.toString().padStart(2, '0')}):${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                } else {
                    const hours = Math.floor(hour);
                    const minutes = Math.floor((hour % 1) * 60);
                    const seconds = Math.floor(((hour % 1) * 60 % 1) * 60);
                    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                }
            };

            const startStr = formatHourWithOffset(this.startHour);
            const endStr = formatHourWithOffset(this.endHour);

            rangeElement.textContent = `${startStr} - ${endStr}`;
        }
    }
}

// Создаём экземпляр
window.timelineManager = new TimelineManager();
console.log('TimelineManager instance created');