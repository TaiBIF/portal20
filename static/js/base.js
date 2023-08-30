$(document).ready(function() {
  //navbar-search
  $('#navbar-search-btn').click(function(){
    const q = $('#navbar-search-input').val();
    window.location.href = `/search/?q=${q}`
  });
})