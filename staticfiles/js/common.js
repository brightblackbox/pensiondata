/**
 * @main.js
 * This is used in all of front/admin pages
 */

$(document).ajaxStart(function () {
    $('body').addClass('loading');
}).ajaxStop(function () {
    $('body').removeClass('loading');
});