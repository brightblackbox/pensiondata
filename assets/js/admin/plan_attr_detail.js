$(document).ready(function (e) {
    $('#id_calculated_rule').css("visibility", "hidden");
    $('#id_attributes_for_master').css("visibility", "hidden");


    // insert select2 for master-selectbox
    $('#id_attrs_for_master-selectbox').insertBefore('#id_attributes_for_master').select2(
        // {
        //     templateResult: function (d) {
        //         var $option = $(d.text + '<span class="info-datasource">(' + d.data('source') + ')</span>');
        //         return $option;
        //
        //     }
        // }
    ).prop("disabled", true).change(function () {
        var attr_ids = $(this).val();
        // console.log(value);
        $('#id_attributes_for_master').val(attr_ids);
    });

    // When change DataSource
    $('#id_data_source').change(function () {
        if( $(this).val() === '0' ){ // NOTE: hardcoded 0: Pension Data. Should be changed when Datasource model is updated.
            $('#id_attrs_for_master-selectbox').prop("disabled", false);
        }else{
            $('#id_attrs_for_master-selectbox').prop("disabled", true).val(null).change();
        }
    }).change();

    // When change Attribute_type
    $('#id_attribute_type').change(function () {
      if($(this).val() == 'static'){

        $('.field-calculated_rule').css("visibility", "hidden");
        $('#id_calculated_rule').prop("disabled", true).val('');
      }else{

        $('.field-calculated_rule').css("visibility", "visible");
        $('#id_calculated_rule').prop("disabled", false);
      }
    }).change();

    // add new key 'value' for autocomplete
    $.each(static_attr_list, function (i, attr) {
        attr['value'] = attr['name']
    });

    // hide calculcated-rule, insert new UI element
    $('.insert-me').insertBefore('#id_calculated_rule');
    $('#id_calculated_rule').attr("rows", "1");

    // show formated rule
    var old_calc_rule = $('#id_calculated_rule').val();
    var old_calc_items = old_calc_rule.split(/#([\+\-\*\/\(\)]|\d+)#/);

    for(var i=0, len=old_calc_items.length; i < len; i++){
      if( old_calc_items[i].length <= 0){
          continue;
      }

      static_value = old_calc_items[i].match(/%(.+)%/);

      if ( $.inArray(old_calc_items[i], availableOperators) >= 0) {
        $('<li class="calc-item calc-operator">'+ old_calc_items[i] +'</li>').insertBefore(".calc-input-inline");
      }
      else if(static_value != null){
        $('<li class="calc-item calc-static">'+ static_value[1] +'</li>').insertBefore(".calc-input-inline");
      }
      else{
        id = old_calc_items[i];
        name = get_name_by_id(id);
        $('<li class="calc-item calc-operand" data-id="'+ id +'">'+ name +'</li>').insertBefore(".calc-input-inline");
      }
    }

    // add autocomplete
    $( ".calc-input__field" )
      .on( "keydown", function( event ) {
        // don't navigate away from the field on tab when selecting an item
        if ( event.keyCode === $.ui.keyCode.TAB &&
          $( this ).autocomplete( "instance" ).menu.active ) {
          event.preventDefault();
        }
        // if BACKSPACE, delete prev element and edit inputbox
        if ( event.keyCode === $.ui.keyCode.BACKSPACE && !$(this).val()) {
          $(this).val( $(".calc-input-inline").prev().text() );
          $('.calc-input-inline').prev("li").remove();
          //event.preventDefault();
        }
      })
      .blur(function(){
        var inputVal = $(this).val();
        if ( $.isNumeric( inputVal ) )
        {
          $('<li class="calc-item calc-static">'+ inputVal +'</li>').insertBefore(".calc-input-inline");
        }
        $(this).val('');
        extract_rule();
      })
      .autocomplete({
        minLength: 1,
        source: function( request, response ) {

          var term_string = request.term;
          var term_length = request.term.length;
          var lastChar = term_string[term_length-1];
          var sliced_string = term_string.slice(0, -1);

          if ($.inArray(lastChar, availableOperators) >= 0 )// lastChar is in [+, -, *, /, (, )]
          {
            if(term_length == 1){
              $('<li class="calc-item calc-operator">'+ lastChar +'</li>').insertBefore(".calc-input-inline");

              $('.calc-input__field').val('');
            }else if($.isNumeric( sliced_string )) {
              $('<li class="calc-item calc-static">'+ sliced_string +'</li><li class="calc-item calc-operator">'+ lastChar +'</li>').insertBefore(".calc-input-inline");

              $('.calc-input__field').val('');
            }
          }

          response( $.ui.autocomplete.filter(	static_attr_list, request.term ) );
        },
        focus: function() {
          // prevent value inserted on focus
          return false;
        },
        select: function( event, ui ) {
          $('<li class="calc-item calc-operand" data-id="'+ ui.item.id +'">'+ ui.item.value +'</li>').insertBefore(".calc-input-inline");
          this.value = '';
          return false;
        }
      });
}); // document.ready()

function get_name_by_id(id) {
  var name = '';
  $.each(static_attr_list, function (i, attr) {
    if(attr.id == id){
      name = attr.name;
      return false;
    }
  });
  return name;
}

function is_valid_rule(rule){
  try{
    eval( rule );
    $('.validation-result').html('');
    return true;
  }
  catch(err) {
    //$('.validation-result').html(err.message);
    $('.validation-result').html('Invalid rule');
    return false;
  }
}

function extract_rule(){
  var rule_for_validating = '';
  var	rule_for_storing = '';

  $('li.calc-item').each(function() {
    if ( $(this).hasClass("calc-operand") )
    {
      rule_for_validating += '1';
      rule_for_storing += '#' + $(this).data("id") + '#';

    }else if($(this).hasClass("calc-operator")){

      rule_for_validating += $(this).text();
      rule_for_storing += '#' + $(this).text() + '#';

    }else if($(this).hasClass("calc-static")){

      rule_for_validating += $(this).text();
      rule_for_storing += '#%'+$(this).text()+'%#';
    }
  });

  if(is_valid_rule(rule_for_validating)){
    $('#id_calculated_rule').val(rule_for_storing);
    return true;
  }else{
    $('#id_calculated_rule').val('');
    return false;
  }
}
