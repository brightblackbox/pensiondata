$(function () {

    var remove_datepicker_elems = null;

    $("#start_year").datepicker({
        changeMonth: false,
        changeYear: true,
        showButtonPanel: true,
        hideIfNoPrevNext: true,
        yearRange: '1950:2020', // Optional Year Range
        dateFormat: 'yy',
        defaultDate: $('#start_year').val() ? new Date($('#start_year').val()+'-01-01') : new Date('2020-01-01'),
        onClose: function (dateText, inst) {
            var year = $("#ui-datepicker-div .ui-datepicker-year :selected").val();
            $(this).datepicker('setDate', new Date(year, 0, 1));
            $(this).datepicker('option', 'defaultDate', new Date($('#start_year').val()+'-01-01'));
            $(this).datepicker('setDate', new Date(year, 0, 1));

            if (parseInt($('#start_year').val()) > $('#end_year').val()) {
                $("#end_year").datepicker('setDate', new Date($('#start_year').val(), 0, 1));
                $("#end_year").datepicker('option', 'defaultDate', new Date($('#end_year').val()+'-01-01'));
                $("#end_year").datepicker('setDate', new Date(year, 0, 1));
            }

            changeLinkUrl($('.export-file-link'), /&from=[^&]*/, '&from=' + year);
        }
    }).focus(function () {
        clearInterval(remove_datepicker_elems);
        remove_datepicker_elems = setInterval(function () {
            $(".ui-datepicker-prev, .ui-datepicker-next, .ui-datepicker-month").remove();
        }, 50);
    });

    $( "#end_year" ).datepicker({
        changeMonth: false,
        changeYear: true,
        showButtonPanel: true,
        hideIfNoPrevNext: true,
        yearRange: '1950:2020', // Optional Year Range
        dateFormat: 'yy',
        defaultDate: $('#end_year').val() ? new Date($('#end_year').val()+'-01-01') : new Date('2020-01-01'),
        onClose: function (dateText, inst) {
            var year = $("#ui-datepicker-div .ui-datepicker-year :selected").val();
            $(this).datepicker('setDate', new Date(year, 0, 1));
            $(this).datepicker('option', 'defaultDate', new Date($('#end_year').val()+'-01-01'));
            $(this).datepicker('setDate', new Date(year, 0, 1));

            if (parseInt($('#end_year').val()) < $('#start_year').val()) {
                $("#start_year").datepicker('setDate', new Date($('#end_year').val(), 0, 1));
                $("#start_year").datepicker('option', 'defaultDate', new Date($('#end_year').val()+'-01-01'));
                $("#start_year").datepicker('setDate', new Date(year, 0, 1));
            }

            changeLinkUrl($('.export-file-link'), /&to=[^&]*/, '&to=' + year);
        }
    }).on('focus', function () {
        $(".ui-datepicker-prev, .ui-datepicker-next, .ui-datepicker-month").remove();
    });

})