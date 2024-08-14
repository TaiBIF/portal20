$(document).ready(function() {
    $('.contact-name').on('click', function() {
        toggleAccordion($(this));
    });
});

function toggleAccordion($element) {
    var $ul = $element.next('ul');
    var $icon = $element.find('.icon-toggle svg');
    
    $ul.toggleClass('d-none');

    if ($ul.hasClass('d-none')) {
        $icon.css('transform', 'rotate(0deg)');
    } else {
        $icon.css('transform', 'rotate(180deg)');
    }
}
