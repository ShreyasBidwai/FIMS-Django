
$(document).ready(function() {

  $('#addCityForm').on('submit', function(e) {
    var valid = true;
    var state = $('#state_id');
    var city = $('#addCityForm input[name="name"]');
    var errorSpan = $(this).find('.error-message');
    errorSpan.text('');
    state.removeClass('input-error');
    city.removeClass('input-error');
    if (!state.val()) {
      errorSpan.text('State is required.');
      state.addClass('input-error');
      valid = false;
    } else if (!city.val().trim()) {
      errorSpan.text('City name is required.');
      city.addClass('input-error');
      valid = false;
    }
    if (!valid) e.preventDefault();
  });
  $('#state_id, #addCityForm input[name="name"]').on('input change', function() {
    $(this).removeClass('input-error');
    $(this).closest('form').find('.error-message').text('');
  });

  // Add State form
  $('#addStateForm').on('submit', function(e) {
    var name = $(this).find('input[name="name"], input[name="state_name"]');
    var errorSpan = $(this).find('.error-message');
    errorSpan.text('');
    name.removeClass('input-error');
    if (!name.val().trim()) {
      errorSpan.text('State name is required.');
      name.addClass('input-error');
      e.preventDefault();
    }
  });
  $('#addStateForm input[name="name"], #addStateForm input[name="state_name"]').on('input', function() {
    $(this).removeClass('input-error');
    $(this).closest('form').find('.error-message').text('');
  });


  $('#editCityForm').on('submit', function(e) {
    var name = $(this).find('input[name="name"], input[name="city_name"]');
    var errorSpan = $(this).find('.error-message');
    errorSpan.text('');
    name.removeClass('input-error');
    if (!name.val().trim()) {
      errorSpan.text('City name is required.');
      name.addClass('input-error');
      e.preventDefault();
    }
  });
  $('#editCityForm input[name="name"], #editCityForm input[name="city_name"]').on('input', function() {
    $(this).removeClass('input-error');
    $(this).closest('form').find('.error-message').text('');
  });


  $('#editStateForm').on('submit', function(e) {
    var name = $(this).find('input[name="name"], input[name="state_name"]');
    var errorSpan = $(this).find('.error-message');
    errorSpan.text('');
    name.removeClass('input-error');
    if (!name.val().trim()) {
      errorSpan.text('State name is required.');
      name.addClass('input-error');
      e.preventDefault();
    }
  });
  $('#editStateForm input[name="name"], #editStateForm input[name="state_name"]').on('input', function() {
    $(this).removeClass('input-error');
    $(this).closest('form').find('.error-message').text('');
  });
});