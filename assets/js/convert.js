var type_converters = {
    '': convertToText,
    'real': convertToReal,
    'int': convertToInt,
    'int_separated3': convertToInt3,
    'text': convertToText,
    'percentage': convertToPercentage,
    'percentage2': convertToPercentage2,
    'percentage4': convertToPercentage4,
    'yesno': convertToYesNo,
}


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


function convertToReal(value) {
    if (parseFloat(value) == NaN) {
        return '';
    }
    return parseFloat(value);
}

function convertToInt(value) {
    if (parseInt(value) == NaN) {
        return '';
    }
    return parseInt(value);
}


function convertToInt3(value) {
    if (parseInt(value) == NaN) {
        return '';
    }
    if (value > 0){
        return numberWithCommas(value);
    }
    else if (value < 0) {
        return '-' + numberWithCommas(value);
    }
    return 0;
}


function convertToText(value) {
    return value.toString();
}

function convertToPercentage(value) {
    if (parseFloat(value) == NaN) {
        return '';
    }
    return value.toString() + ' %';
}

function convertToPercentage2(value) {
    if (parseFloat(value) == NaN) {
        return '';
    }
    return parseFloat(value).toFixed(2).toString() + ' %';
}

function convertToPercentage4(value) {
    if (parseFloat(value) == NaN) {
        return '';
    }
    return parseFloat(value).toFixed(4).toString() + ' %';
}

function convertToYesNo(value) {
    if (value === 0 || value === false) {
        return 'No';
    } else if (value === 1 || value === true) {
        return 'Yes';
    }
    return '';
}
