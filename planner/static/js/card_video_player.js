function startVideoPlayer() {
    const VideoPlayerModal = document.getElementById('VideoPlayerModal');
    try {
        if (VideoPlayerModal && Hls.isSupported()) {
            const modal = new bootstrap.Modal(VideoPlayerModal);
            let VideoPlayerTitle = document.getElementById('VideoPlayerTitle');
            let videoPlayerContainer = document.getElementById('video_player_container');
            let filePathFooter = document.getElementById('video_player_file_path');

            VideoPlayerTitle.innerText = '';
            videoPlayerContainer.innerHTML = '';
            filePathFooter.innerHTML = '';

            let filePath = videoPlayerContainer?.dataset.filePath || '';
            if (!filePath) {
                console.log('Нет материала');
                return;
            }

            // Создаем видео элемент с атрибутами для Video.js
            const videoElement = document.createElement('video-js');
            videoElement.id = 'my-video-player';
            videoElement.classList.add('vjs-default-skin', 'vjs-big-play-centered');
            videoElement.setAttribute('controls', '');
            videoElement.setAttribute('width', '100%');
            videoElement.setAttribute('height', 'auto');
            videoElement.setAttribute('playsinline', '');

            videoPlayerContainer.appendChild(videoElement);

            let videoName = videoPlayerContainer?.dataset?.name;
            let videoYear = videoPlayerContainer?.dataset?.year;

            if (videoName && videoYear) {
                VideoPlayerTitle.innerText = `${videoName} (${videoYear})`;
            } else if (videoName) {
                VideoPlayerTitle.innerText = videoName;
            } else {
                VideoPlayerTitle.innerText = 'Название';
            }

            let filePathTitle = document.createElement('small');
            filePathTitle.classList.add('text-secondary');
            filePathTitle.innerText = filePath.length > 167 ? filePath.slice(0, 167) + '...' : filePath;
            filePathFooter.appendChild(filePathTitle);

            const videoPath = getHlsUrl(filePath);

            // Инициализация Video.js
            const player = videojs('my-video-player', {
                controls: true,
                autoplay: false,
                preload: 'auto',
                fluid: true,
                playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2],
                controlBar: {
                    children: [
                        'playToggle',
                        'volumePanel',
                        'currentTimeDisplay',
                        'timeDivider',
                        'durationDisplay',
                        'progressControl',
                        'liveDisplay',
                        'seekToLive',
                        'remainingTimeDisplay',
                        'customControlSpacer',
                        'playbackRateMenuButton',
                        'chaptersButton',
                        'descriptionsButton',
                        'subsCapsButton',
                        'audioTrackButton',
                        'fullscreenToggle'
                    ]
                }
            });

            // Загрузка сохраненной громкости
            const savedVolume = localStorage.getItem('videoPlayerVolume');
            player.volume(savedVolume !== null ? parseFloat(savedVolume) : 0.3);

            // Сохранение громкости
            player.on('volumechange', () => {
                localStorage.setItem('videoPlayerVolume', player.volume());
            });

            // HLS загрузка
            const hls = new Hls({
                debug: false,
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90
            });

            hls.loadSource(videoPath);
            hls.attachMedia(player.tech().el());

            // Инициализация плагина маркеров
            initializeMarkersPlugin(player);

            // Навигация стрелками
            setupKeyboardNavigation(player);

            // Плагин для маркеров на таймлайне
            function initializeMarkersPlugin(player) {
                // Создаем контейнер для маркеров
                const markersContainer = document.createElement('div');
                markersContainer.id = 'markers-container';
                markersContainer.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    pointer-events: none;
                `;

                // Добавляем его к progress control
                player.ready(() => {
                    const progressControl = player.controlBar.progressControl;
                    if (progressControl) {
                        progressControl.el().appendChild(markersContainer);
                    }
                });

                // Хранилище маркеров
                let markers = JSON.parse(localStorage.getItem(`video_markers_${filePath}`) || '[]');

                // Рендеринг маркеров
                function renderMarkers() {
                    markersContainer.innerHTML = '';
                    const duration = player.duration();

                    markers.forEach((marker, index) => {
                        const markerEl = document.createElement('div');
                        markerEl.className = 'video-marker';
                        const position = (marker.time / duration) * 100;

                        markerEl.style.cssText = `
                            position: absolute;
                            left: ${position}%;
                            top: -12px;
                            width: 4px;
                            height: 12px;
                            background-color: ${marker.color};
                            cursor: pointer;
                            pointer-events: all;
                            z-index: 2;
                        `;

                        markerEl.title = `${marker.label} (${formatTime(marker.time)})`;
                        markerEl.onclick = (e) => {
                            e.stopPropagation();
                            player.currentTime(marker.time);
                        };

                        markersContainer.appendChild(markerEl);
                    });
                }

                function saveMarkers() {
                    localStorage.setItem(`video_markers_${filePath}`, JSON.stringify(markers));
                }

                function formatTime(seconds) {
                    const hrs = Math.floor(seconds / 3600);
                    const mins = Math.floor((seconds % 3600) / 60);
                    const secs = Math.floor(seconds % 60);
                    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                }

                function getRandomColor() {
                    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'];
                    return colors[Math.floor(Math.random() * colors.length)];
                }

                // Обновляем маркеры при изменении длительности
                player.on('loadedmetadata', renderMarkers);
                player.on('durationchange', renderMarkers);

                // Начальный рендеринг
                setTimeout(renderMarkers, 1000);
            }

            // Навигация стрелками
            function setupKeyboardNavigation(player) {
                const skipSeconds = 5;
                let lastKeyTime = 0;
                const keyCooldown = 200; // ms для предотвращения слишком быстрых нажатий

                document.addEventListener('keydown', (e) => {
                    // Проверяем, что фокус не на элементе ввода
                    if (document.activeElement.tagName === 'INPUT' ||
                        document.activeElement.tagName === 'TEXTAREA' ||
                        document.activeElement.isContentEditable) {
                        return;
                    }

                    const now = Date.now();
                    if (now - lastKeyTime < keyCooldown) return;

                    switch(e.key) {
                        case 'ArrowLeft':
                            e.preventDefault();
                            player.currentTime(Math.max(0, player.currentTime() - skipSeconds));
                            showTimeToast(player, `-${skipSeconds}s`);
                            lastKeyTime = now;
                            break;
                        case 'ArrowRight':
                            e.preventDefault();
                            player.currentTime(Math.min(player.duration(), player.currentTime() + skipSeconds));
                            showTimeToast(player, `+${skipSeconds}s`);
                            lastKeyTime = now;
                            break;
                        case 'ArrowUp':
                            e.preventDefault();
                            player.volume(Math.min(1, player.volume() + 0.1));
                            break;
                        case 'ArrowDown':
                            e.preventDefault();
                            player.volume(Math.max(0, player.volume() - 0.1));
                            break;
                    }
                });
            }

            // Визуальный toast для отображения перемотки
            function showTimeToast(player, text) {
                const toast = document.createElement('div');
                toast.className = 'time-skip-toast';
                toast.textContent = text;
                toast.style.cssText = `
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 18px;
                    font-weight: bold;
                    z-index: 1000;
                    pointer-events: none;
                    animation: fadeInOut 0.6s ease-in-out;
                `;

                player.el().appendChild(toast);
                setTimeout(() => toast.remove(), 600);
            }

            modal.show();

            // Очистка при закрытии
            VideoPlayerModal.addEventListener('hidden.bs.modal', function () {
                if (player) {
                    player.dispose();
                }
                videoPlayerContainer.innerHTML = '';
            });

            // Обработка изменения размера модального окна
            VideoPlayerModal.addEventListener('shown.bs.modal', function () {
                if (player) {
                    player.trigger('resize');
                }
            });
        }

    } catch (error) {
        console.log('Video player error:', error);
    }
}

// Ваша функция getHlsUrl остается без изменений
function getHlsUrl(windowsPath) {
    let cleanPath = windowsPath.replace(/^\\\\[^\\]+\\(.+)$/i, '$1');
    cleanPath = cleanPath.replace(/\\/g, '/');

    const parts = cleanPath.split('/');
    const encodedParts = parts.map(part => {
        const lastDotIndex = part.lastIndexOf('.');
        if (lastDotIndex !== -1) {
            const name = part.substring(0, lastDotIndex);
            const ext = part.substring(lastDotIndex);
            return encodeURIComponent(name) + ext;
        }
        return encodeURIComponent(part);
    });

    const videoFile = encodedParts.join('/');
    const hostname = window.location.hostname;
    const baseUrl = (hostname === 'localhost' || hostname === '127.0.0.1')
        ? 'http://localhost:8002/hls/'
        : '/hls/';

    return `${baseUrl}${videoFile}/master.m3u8`;
}