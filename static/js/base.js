$(document).ready(function() {
  //navbar-search
  $('#navbar-search-btn').click(function(){
    const q = $('#navbar-search-input').val();
    window.location.href = `/search/?q=${q}`
  });

  // 單層 nav
  $('.nav-item').click(function() {
    const cat = $(this).data('cat');
    $('.nav-item').removeClass('current-sunset');
    $(this).addClass('current-sunset');

    $('.nav-item-content').addClass('hide');
    $(`.nav-item-content[data-cat='${cat}']`).removeClass('hide');
  });

  //  雙層 nav
  $('.btn-toggle-flexible').click(function() {
    $('.dropdown-menu').removeClass('show');
    $(this).siblings('.dropdown-menu').addClass('show');
  });
  $('.toggle-item').click(function() {
    const cat = $(this).data('cat');
    $('.toggle-item').removeClass('current-green');
    $(this).addClass('current-green');

    $('.toggle-item-content').addClass('hide');
    $(`.toggle-item-content[data-cat='${cat}']`).removeClass('hide');
  });
})