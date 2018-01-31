$(function () {

    $('#start_year, #end_year').on('change', function () {
        var start_year = $('#start_year').val()
        var end_year = $('#end_year').val()
        if (start_year > end_year) {
            $('#end_year').val(start_year);
            var end_year = $('#end_year').val();
        }

        changeLinkUrl($('.export-file-link'), /&from=[^&]*/, '&from=' + start_year);
        changeLinkUrl($('.export-file-link'), /&to=[^&]*/, '&to=' + end_year);
    });

    function changeLinkUrl(links, replace, insert) {
        if (!links.length) {return;}
        var regex = new RegExp(replace, 'g');
        links.each(function () {
            var url = $(this).attr('href')
            if (url.match(regex) !== null) {
                url = url.replace(regex, insert);
            } else {
                url += insert;
            }
            $(this).attr('href', url);
        });
    }

    $('#exportFile').change(function() {
        var links = $('.export-file-link');
        if ($(this).is(":checked")) {
            changeLinkUrl(links, '&fields=selected', '&fields=all');
        } else {
            changeLinkUrl(links, '&fields=all', '&fields=selected');
        }
    });

});
