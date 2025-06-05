let cardsContainer = document.getElementById('cards_container');
let fullList = document.getElementById('full_list');

new Sortable(cardsContainer, {
    group: 'desktop',
	animation: 200,
	ghostClass: "custom-ghost", // Класс для "призрака" (перетаскиваемого элемента)
    chosenClass: "custom-chosen", // Класс для выбранного элемента
    dragClass: "custom-drag", // Класс для элемента при перетаскивании

});

new Sortable(fullList, {
    group: 'desktop',
	animation: 200,
	ghostClass: "custom-ghost", // Класс для "призрака" (перетаскиваемого элемента)
    chosenClass: "custom-chosen", // Класс для выбранного элемента
    dragClass: "custom-drag", // Класс для элемента при перетаскивании

});
