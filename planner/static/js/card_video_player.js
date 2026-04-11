function startVideoPlayer() {
    const VideoPlayerModal = document.getElementById('VideoPlayerModal');
    try {
        // const videoPath = getHlsUrl('ContentS/FILMS/F_Alien.Romulus_2024_1080p25_H264_10Mbps.mp4/master.m3u8');

        if (VideoPlayerModal && Hls.isSupported()) {
            const modal = new bootstrap.Modal(VideoPlayerModal);
            let VideoPlayerTitle = document.getElementById('VideoPlayerTitle');
            let videoPlayerContainer = document.getElementById('video_player_container');
            videoPlayerContainer.innerHTML = '';
            let videoPlayer = document.createElement('video');
            videoPlayer.setAttribute('width', '100%');
            videoPlayer.setAttribute('controls', true);
            videoPlayer.classList.add('rounded');
            videoPlayer.controlsList = 'nodownload'; // убираем кнопку скачивания
            videoPlayer.playsInline = true; // для iOS

            const savedVolume = localStorage.getItem('videoPlayerVolume');
            videoPlayer.volume = savedVolume !== null ? parseFloat(savedVolume) : 0.3;

            // Включаем автовоспроизведение (с muted для обхода ограничений браузера)
            videoPlayer.muted = false;
            videoPlayer.autoplay = true;

            videoPlayer.addEventListener('volumechange', () => {
                localStorage.setItem('videoPlayerVolume', videoPlayer.volume);
            });

            let videoName = videoPlayerContainer?.dataset?.name
            let videoYear = videoPlayerContainer?.dataset?.year
            if (videoName && videoYear) {
                VideoPlayerTitle.innerText = `${videoName} (${videoYear})`
            } else if (videoName) {
                VideoPlayerTitle.innerText = videoName;
            } else {
                VideoPlayerTitle.innerText = 'Название';
            }

            let filePath = videoPlayerContainer?.dataset.filePath || ''
            if (!filePath) {
                return;
            }
            let filePathFooter = document.getElementById('video_player_file_path');
            let filePathTitle = document.createElement('small');
            filePathTitle.classList.add('text-secondary');
            filePathTitle.innerText = filePath;
            filePathFooter.appendChild(filePathTitle);

            const videoPath = getHlsUrl(filePath)

            const hls = new Hls({
                debug: false,
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90
            });

            hls.loadSource(videoPath);
            hls.attachMedia(videoPlayer);

            videoPlayerContainer.appendChild(videoPlayer);
            modal.show();

            VideoPlayerModal.addEventListener('hidden.bs.modal', function () {
                videoPlayerContainer.innerHTML = '';
            });
        }

    } catch (error) {
        console.log(error);
    }
}

function getHlsUrl(windowsPath) {
    let cleanPath = windowsPath.replace(/^\\\\[^\\]+\\(.+)$/i, '$1');

    // Заменяем обратные слеши на прямые
    cleanPath = cleanPath.replace(/\\/g, '/');

    // Разбиваем на части и кодируем
    const parts = cleanPath.split('/');
    const encodedParts = parts.map(part => {
        // Если это файл с расширением
        const lastDotIndex = part.lastIndexOf('.');
        if (lastDotIndex !== -1) {
            const name = part.substring(0, lastDotIndex);
            const ext = part.substring(lastDotIndex);
            return encodeURIComponent(name) + ext;
        }
        // Если это папка
        return encodeURIComponent(part);
    });

    const videoFile = encodedParts.join('/');

    const hostname = window.location.hostname;

    // Для SSH туннеля (вы разрабатываете удалённо)
    const baseUrl = (hostname === 'localhost' || hostname === '127.0.0.1')
        ? 'http://localhost:8002/hls/'
        : '/hls/';

    // Для HLS добавляем /master.m3u8
    return `${baseUrl}${videoFile}/master.m3u8`;
}