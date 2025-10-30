function copyCode(button) {
    const pre = document.querySelector('pre');
    const text = pre.innerText;

    navigator.clipboard.writeText(text).then(() => {
        // Меняем текст кнопки на пару секунд
        const originalText = button.innerHTML;
        button.innerHTML = '✓ Скопировано!';
        button.classList.add('copied');

        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Ошибка копирования:', err);
        button.innerHTML = '✘ Ошибка';
    });
}