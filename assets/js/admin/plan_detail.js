// display popup for selectors
$(".start-settings").on("click", function(e) {
    e.preventDefault();
    $(".poup-settings-wrap").toggleClass("active");
});

// disappear popup
$(".button-cancel").on("click", function() {
    $(".poup-settings-wrap").removeClass("active");
});

// search function for attributes
$(".input-search").on("keyup", function() {

    var value = $(this).val().toLowerCase();

    $(this).parent().find('.column-list .count-result').remove();

    $(this).parent().find(".column-list li.attr-level").filter(function() {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
    });

    var countResult = $(this).parent().find(".column-list li.attr-level").filter(function() {
        return $(this).css('display') !== 'none';
    }).length;

    if (value != '') {
        $(this).parent().find(".column-list").prepend('<span class="count-result">' + countResult + ' MATCHES</span>');
    }
});

// handle category/attribute relationship when checkbox is changed.
$('input.column-check-box').change(function () {
    var $cb = $(this);
    var $li = $cb.closest('li');
    var state = $cb.prop('checked');

    if ($cb.hasClass('category-column')){
      // check all children
        $li.find('input').each(function () {
            if ( !$(this).prop('disabled') ){
                $(this).prop('checked', state);
            }
        });
    }

    if ($cb.hasClass('attr-column')){
      // check all parents, as applicable
      var $siblings = $li.closest("ul").find("li");
      var $parent = $li.parent().closest('li');

      var checkedNum = 0;
      $siblings.each(function() {
          checkedNum += $(this).find('input').is(':checked')? 1: 0;
      });

      var parentCheckbox = $parent.children('label').children("input[type=checkbox]");
      if (checkedNum == $siblings.length) {
          parentCheckbox.prop('checked', true);
      } else {
          parentCheckbox.prop('checked', false);
      }
    }

    if ( $cb.hasClass('datasource-column') ){
      var source_id = $(this).data('source-id');

      $('.attr-column').each(function () {
          if( $(this).data('source-id') == source_id ){
              $(this).prop('checked', state).prop('disabled', !state).change();
              if(state)
                $(this).closest('li').show();
              else
                $(this).closest('li').hide();

          }
      })
    }
});

// render table
function initialize_annual_table() {
    // tr for "category"
    var $tr_category = '<th rowspan="3" style="vertical-align: middle;">Year</th>';

    $('.category-level').each(function () {
      var attr_children_len = $(this).find("li").length;
      if ( attr_children_len > 0 )
        $tr_category += '<th style="text-align: center;" colspan="' + attr_children_len
            + '" id="th-category-' + $('label:first input', this).data('category-id') + '">'
            + $('label:first', this).text()
            + '</th>';
    });

    // thead
    $('.tr-category ').html($tr_category);

    // tbody attrs_len X years_len
    var $tbody = '';

    $.each(plan_annual_data, function (i, annual_item) {
      var $td_id = 'td-id-' + annual_item.year + '-' + annual_item.attribute_id;
      var $td_html = '<span class="annual-value">' + numberWithCommas(annual_item.attribute_value) + '</span>';
      $('#' + $td_id).html($td_html).attr({'data-annual-data-pk': annual_item.id, 'data-is-from-source': annual_item.is_from_source});
    });

    $('.annual_table_area').css('display', 'block');
}

function redraw_annual_table() {
    // show all td
    $('#table-annual-data td').show();
    $('#table-annual-data th').show();

    // restore thead
    var $tr_category = '<th rowspan="3" style="vertical-align: middle;">Year</th>';

    $('.category-level').each(function () {
    var attr_children_len = $(this).find("li").length;
    if ( attr_children_len > 0 )
      $tr_category += '<th style="text-align: center;" colspan="' + attr_children_len
          + '" id="th-category-' + $('label:first input', this).data('category-id') + '">'
          + $('label:first', this).text()
          + '</th>';
    });

    $('.tr-category ').html($tr_category);

    // hide datasource
    $(".datasource-column:not(:checked)").each(function () {
        var unchecked_source_id = $(this).data('source-id');

        // hide all relavant tds in tbody
        $('.td-source-'+unchecked_source_id).hide();

        // decrese colspan in thead Category
        $('.th-source-'+unchecked_source_id).each(function () {
            category_id = $(this).data('category-id');

            old_colspan = $('#th-category-'+ category_id).attr('colspan');
            if (old_colspan > 1){
                $('#th-category-'+category_id).attr('colspan', old_colspan-1);
            }else{
                $('#th-category-'+category_id).hide();
            }

            $(this).hide();
        });
    });

    // hide attribute
    $(".attr-column:not(:checked)").each(function () {
        var unchecked_attr_id = $(this).data('attr-id');

        // hide all relavant tds in tbody
        $('.td-attr-'+unchecked_attr_id).hide();

        // decrese colspan in thead Category
        $('.th-attr-'+unchecked_attr_id).each(function () {
            category_id = $(this).data('category-id');

            old_colspan = $('#th-category-'+category_id).attr('colspan');
            if (old_colspan > 1){
                $('#th-category-'+category_id).attr('colspan', old_colspan-1);
            }else{
                $('#th-category-'+category_id).hide();
            }

            $(this).hide();
        })
    });

    // remove emtpy row
    $('.tr-annual-data-per-year').each(function () {
        var $tr = $(this);
        $tr.show();
        var is_visible = false;

        $tr.find('td').each(function () {

            var $td = $(this);

            if( $td.is(":visible") && $td.find('span').length > 0 ){
                is_visible = true;
                return false;
            }
        });

        if ( !is_visible ){
            $tr.hide();
        }
    });

}

// apply
$('.poup-settings-wrap .button-apply').on("click", function () {

    redraw_annual_table();

    $.ajax({
        type: "POST",
        url: save_checklist_url,
        data: $(this).closest('form').serialize(),
        success: function (response) {
          console.log(response);
        },
        error: function (XMLHttpRequest, textStatus, err) {
            console.log(err);
        }
    });

  $(".poup-settings-wrap").removeClass("active");

});

/**
 * @input: unformated number, for example: 123456789.0123456
 * @result 123,456,789.0123456
 */
function numberWithCommas(unformatted) {
    var parts = unformatted.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

/**
 * @input: formated number, for example: 123,456,789.0123456
 * @result 123456789.0123456
 */
function unformatnumber(formatted) {
    return formatted.replace(/,/g, "");
}


var selected_annual_id = 0;
var $selected_td_element=null;
// click td
$('#table-annual-data td').on("click", function () {

  $('span.annual-value').removeClass('selected_td');
  var annual_data_pk = $(this).data('annual-data-pk');

  var is_from_source = $(this).data('is-from-source');
  var source_pk = $(this).data('source-pk');

  var is_readonly = false;
  if (is_from_source && source_pk===0) { // NOTE: hardcoded
      console.log('here-------readonly');
      is_readonly = true;
  }

  var $span = $('span', this);
  $selected_td_element = $span;

  if( annual_data_pk > 0 ){
    selected_annual_id = annual_data_pk;
    $span.addClass('selected_td');
    $('.btn-edit-for-modal').prop( "disabled", false );
    $('.btn-delete-for-modal').prop( "disabled", false );

    var old_value = unformatnumber($span.text());
    $('#annual-new-val').val(old_value).prop("readonly", is_readonly);


  }else{
    $('.btn-edit-for-modal').prop( "disabled", true );
    $('.btn-delete-for-modal').prop( "disabled", true );
  }
});

// edit value
$('.btn-update').click(function () {
    var new_val = $('#annual-new-val').val();
    var old_val = unformatnumber($selected_td_element.text());

    if ( !new_val || 0 === new_val.length){
        alert('The value is required.');
        return;
    }else if (new_val == old_val){
        return;
    }
    $.ajax({
      data:{
        'attr_id': selected_annual_id,
        'new_val': new_val,
        'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val()
      },
      type: "post",
      url: edit_annual_data_url,
      success: function (resp) {
        console.log(resp);
        if(resp.result == 'success'){
          $selected_td_element.text(new_val);
        }else{
          alert(resp.msg);
        }
      },
      error: function (resp) {
        alert(resp);
      }
    });
});

// delete
$('.btn-delete').click(function () {
    $.ajax({
      data:{
        'attr_id': selected_annual_id,
        'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val()
      },
      type: "post",
      url: delete_annual_data_url,
      success: function (resp) {
        console.log(resp);
        if(resp.result == 'success'){
            $selected_td_element.remove();
            $('.btn-edit-for-modal').prop( "disabled", true );
            $('.btn-delete-for-modal').prop( "disabled", true );
        }else{
          alert(resp.msg);
        }
      },
      error: function (resp) {
        console.log('error');
        console.log(resp);
      }
    });
});

// add--------------------------
// when a user selects attribute.
$('#attr-selectbox').change(function () {
    var attr_id = $(this).val();
    if(!attr_id){
      $('#attribute-type').text('');
      $('#attribute-source').text('');
      $('#attribute-category').text('');
      $('#attribute-rule').html('');
      $('#attr-val-input').val( '' );
      return false;
    }
    show_detail_for_add_new(attr_id);
});

// when a user selects year.
$('#year-selectbox').change(function () {
    var attr_id = $('#attr-selectbox').val();
    show_detail_for_add_new(attr_id);
});

 $("input[name='is_from_source']").change(function(){
    var _val = $(this).val();
    if (_val == 1){
        $('#attr-val-input').hide().val();
    }else{
        $('#attr-val-input').show();
    }
});


function show_detail_for_add_new(attr_id){
    var selected_attr = get_attr_by_id(attr_id);
    $('#attribute-type').text( selected_attr.attribute_type );
    $('#attribute-source').text( selected_attr.data_source );

    $('#id-is_from_source-radio1').prop("checked", true);
    if (selected_attr.data_source === 'pensiondata.org'){ // NOTE: hardcoded !!!
        $('#id-is_from_source-wrapper').show();
        $('#attr-val-input').hide().val();
    }else{
        $('#id-is_from_source-wrapper').hide();
        $('#attr-val-input').show();
    }

    $('#attribute-category').text( selected_attr.category );
    $('#add-new-result').hide();
    var rule = selected_attr.calculated_rule;
    if(! rule){
      $('#attribute-rule').html( '' );
      $('#attr-val-input').val( '' );
      return;
    }
    var old_calc_items = rule.split(/#([\+\-\*\/\(\)]|\d+)#/);
    var availableOperators = ['+', '-', '*', '/', '(', ')'];
    var readable_rule = '<label>Rule:&nbsp;</label>';
    var calc_formula = '';
    var year = $('#year-selectbox').val();
    var is_valid = true;
    for(var i=0, len=old_calc_items.length; i < len; i++){
      if( old_calc_items[i].length <= 0){
          continue;
      }
      static_value = old_calc_items[i].match(/%(.+)%/);
      if ( $.inArray(old_calc_items[i], availableOperators) >= 0) {
        readable_rule += '<span style="color:green">' + old_calc_items[i] + '</span>';
        calc_formula += old_calc_items[i]
      }
      else if(static_value != null){
        readable_rule += '<span style="color:blue">' + static_value[1] + '</span>';
        calc_formula += static_value[1]
      }
      else{
        id = old_calc_items[i];
        name = get_attr_by_id(id).name;
        readable_rule += '<span style="background-color:#e4e4e4;">' + name + '</span>';
        value = get_value(name, year);
        if (! value){
            is_valid = false;
            calc_formula += '0';
        }else{
            calc_formula += value;
        }
      }
    }

    $('#attribute-rule').html( readable_rule );
    if(is_valid){
      $('#attr-val-input').val( eval(calc_formula) )
    }else{
      $('#attr-val-input').val( '0' )
    }
}

function get_attr_by_id(id) {
    var selected_attr = {};
    $.each(all_attr_list, function (i, attr) {
      if(attr.id == id){
        selected_attr = attr;
        return false;
      }
    });
    return selected_attr;
}

function get_value(name, year) {
    var selected_val = false;
    $.each(plan_annual_data, function (i, annual_attr) {
      if(annual_attr.attribute == name && annual_attr.year == year){
        selected_val = annual_attr.attribute_value;
        return false;
      }
    });
    return selected_val;
}
// add new form submit
$('#add-new-form').on('submit', function (e) {
  e.preventDefault();
  var year = $('#year-selectbox').val();
  var attr_id = $('#attr-selectbox').val();
  var value = $('#attr-val-input').val();
  var is_from_source = $("input[name='is_from_source']:checked").val();
  if(attr_id==""){
    alert("invalid attribute");
    return false;
  }
  // disable buttons before submit
  $('#add-new-result').html('Please wait ...').css('color', 'red').show();
  $('#add-new-form .btn-primary').prop('disabled', true);
  $('#add-new-form button').prop('disabled', true);
  // submit
  $.ajax({
    data:{
      'attr_id': attr_id,
      'plan_id': plan_pk,
      'year': year,
      'value': value,
      'is_from_source': is_from_source,
      'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val()
    },
    type: "post",
    url: add_annual_data_url,
    success: function (resp) {
      console.log(resp);
      if(resp.result == 'success'){
        $('#add-new-result').html('Successfully added').css('color','green').show();
        setTimeout(
          function()
          {
            location.reload();
          }, 2000);
      }else{
        $('#add-new-result').html(resp.msg).css('color','red').show();
        // disable buttons before submit
        $('#add-new-form .btn-primary').prop('disabled', false);
        $('#add-new-form button').prop('disabled', false);
      }
    },
    error: function (resp) {
      alert(resp);
      $('#add-new-form .btn-primary').prop('disabled', false);
      $('#add-new-form button').prop('disabled', false);
    }
  });
  return false;
});

$(document).ready(function() {

    // make selectbox for attributes
    $.each(all_attr_list, function (i, attr) {
        $('#attr-selectbox').append('<option value="'+ attr.id +'">' + attr.name +'</option>');
    });

    // draw plan_annual_attr table
    initialize_annual_table();
    redraw_annual_table();
});
