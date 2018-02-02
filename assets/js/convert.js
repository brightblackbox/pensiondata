var type_converters = {
    '': convertToText,
    'real': convertToReal,
    'int': convertToInt,
    'text': convertToText,
    'percentage': convertToPercentage,
    'percentage2': convertToPercentage2,
    'percentage4': convertToPercentage4,
    'yesno': convertToYesNo,
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
