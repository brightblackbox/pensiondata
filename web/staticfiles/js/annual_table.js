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
    var $tr_category = '<th rowspan="2" style="vertical-align: middle;">Year</th>';

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
      var $td_html = '<span class="annual-value">' + format_annual_value(annual_item.attribute_value, annual_item.multiplier) + '</span>';
      $('#' + $td_id).html($td_html).data('annual-data-pk', annual_item.id);
    });

    $('.annual_table_area').css('display', 'block');
}

function redraw_annual_table() {
    // show all td
    $('#table-annual-data td').show();
    $('#table-annual-data th').show();

    // restore thead
    var $tr_category = '<th rowspan="2" style="vertical-align: middle;">Year</th>';

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
 * @input: 123456789.0123456
 * @result 123,456,789.0123456
 */
function numberWithCommas(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

/**
 * @v: plan_annual_attribute.value
 * @m: plan_attribute.multiplier
 * @result: $1,234,567 or 0
 */
function format_annual_value(v, m){
   money = v * m;
   if (money != 0){
       return '$'+ numberWithCommas(money);
   }
   return 0;
}


$(document).ready(function() {
    // draw plan_annual_attr table
    initialize_annual_table();
    redraw_annual_table();
});
