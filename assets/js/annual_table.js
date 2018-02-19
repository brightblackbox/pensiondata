var datatable = null;
var is_government = false;

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
    // tbody attrs_len X years_len
    var $tbody = '';

    $.each(plan_annual_data, function (i, annual_item) {
      var $td_id = 'td-id-' + annual_item.year + '-' + annual_item.attribute_id;
      var arr_special_datatype = ['varchar', 'yesno', 'date', 'shortdate', 'text', '#N/A'];
      if (is_government === true) {
          if (arr_special_datatype.indexOf(annual_item.government_attribute__datatype) > -1){
              var value = type_converters[annual_item.government_attribute__datatype](annual_item.attribute_value)
          }
          else {
              var value = multiply_value(annual_item.attribute_value, annual_item.multiplier);
              value = type_converters[annual_item.government_attribute__datatype](value);
          }
      } else {
          if (arr_special_datatype.indexOf(annual_item.plan_attribute__datatype) > -1){
              var value = type_converters[annual_item.plan_attribute__datatype](annual_item.attribute_value)
          }
          else {
              var value = multiply_value(annual_item.attribute_value, annual_item.multiplier);
              value = type_converters[annual_item.plan_attribute__datatype](value);
          }
      }
      // if (is_government === true) {
      //     var value = multiply_value(annual_item.attribute_value, annual_item.multiplier);
      //     value = type_converters[annual_item.government_attribute__datatype](value);
      // } else {
      //     // if (annual_item.plan_attribute__datatype == 'date' || annual_item.plan_attribute__datatype == 'shortdate' ){
      //     //     var value = type_converters[annual_item.plan_attribute__datatype](annual_item.attribute_value)
      //     // } else {
      //     //     var value = format_annual_value(annual_item.attribute_value, annual_item.multiplier);
      //     // }
      //     var value = format_annual_value(annual_item.attribute_value, annual_item.multiplier);
      // }

      // annual_item.category_id == "362" is file links Attribute category for Plan Attribute
      if (annual_item.category_id == "362"){
          var $td_html = '<span class="annual-value"> <a href="'+ (annual_item.attribute_value) + '" target="_blank" > <i class="fa fa-folder" aria-hidden="true"></i> </a> </span>';
      } else {
          var $td_html = '<span class="annual-value">' + value + '</span>';
      }

      $('#' + $td_id).html($td_html).data('annual-data-pk', annual_item.id);
    });

    $('.annual_table_area').css('display', 'block');
}

function redraw_annual_table() {
    // show all td
    $('#table-annual-data td').show();
    $('.tr-attribute th').show();

    // hide datasource
    $(".datasource-column:not(:checked)").each(function () {
        var unchecked_source_id = $(this).data('source-id');

        // hide all relavant tds in tbody
        $('.td-source-'+unchecked_source_id).hide();
    });

    // hide attribute
    $(".attr-column:not(:checked)").each(function () {
        var unchecked_attr_id = $(this).data('attr-id');

        $('.td-attr-'+unchecked_attr_id).hide();
        $('.th-attr-'+unchecked_attr_id).hide();

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

    // data table
    if (datatable != null){
        console.log('resize start: ' + $.now());
        datatable.columns.adjust().draw();
        console.log('resize end: ' + $.now());
        // $('#table-annual-data').resize();
    }

}

// apply
$('.poup-settings-wrap .button-apply').on("click", function () {

    // console.log("click apply: " + $.now() );
    // $('body').addClass('loading');
    // redraw_annual_table();
    // console.log("--- redrawed_click apply: " +  $.now() );

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

    $(this).closest('form').submit();

  // $(".poup-settings-wrap").removeClass("active");

});

/**
 * @input: 123456789.0123456
 * @result 123,456,789.0123456
 */
function numberWithCommas(x) {
    if (x === null)
        return '';
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

/**
 * @v: plan_annual_attribute.value
 * @m: plan_attribute.multiplier
 * @returns {number}
 */
function multiply_value(v, m) {
    if (v === null || m ===null){
        return 0;
    }
    return m * v;
}


/**
 * @v: plan_annual_attribute.value
 * @m: plan_attribute.multiplier
 * @result: $1,234,567 or 0
 */
function format_annual_value(v, m){
    var money = multiply_value(v, m);

    if (money > 0){
        return '$'+ numberWithCommas(money);
    }else if (money < 0){
        return '-$'+ numberWithCommas(money*(-1));
    }
    return 0;
}


$(document).ready(function() {
    // draw plan_annual_attr table
    console.log("ready : " + $.now() );

    initialize_annual_table();

    console.log("start redraw:" + $.now() );
    redraw_annual_table();

    datatable = $('#table-annual-data').DataTable( {
        colReorder: {
            fixedColumnsLeft: 1
        },
        deferRender: true,
        scrollX: true,
        scrollY: "500px",
        paging: true,
        info: false,
        searching: false,
        order: [[ 0, 'desc' ]],
        fixedColumns: {
            leftColumns:1
        },
        preDrawCallback: function( settings ) {
            console.log('I am preDraw');
        },
        drawCallback: function( settings ) {
            console.log('I am DrawCallback');
        }

        // autoWidth: false,
        // responsive: true
    });

    console.log("ready done: " + $.now() );

});
