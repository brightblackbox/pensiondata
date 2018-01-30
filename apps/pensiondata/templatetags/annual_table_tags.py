from django import template

register = template.Library()

NONE = 0


@register.assignment_tag()
def get_checked_status(column_visibiity_state, item_type, item_id):
    """
    Check if this item was selected in last session.
    column_visibiity_state: request.session
    model: one of (plan, government)
    item_type: one of (source, category, attr)
    return True/False
    """
    if not column_visibiity_state:
        return True

    try:
        if item_id is None:
            return NONE in column_visibiity_state[item_type]
        return item_id in column_visibiity_state[item_type]
    except Exception as e:
        print(e.__dict__)
        return False


@register.assignment_tag()
def get_attribute(object, key1, key2=None, default=None):
    key = key1
    if key2:
        key += key2
    if hasattr(object, key):
        return getattr(object, key)
    elif key in object:
        return object[key]
    return default


@register.assignment_tag()
def build_export_url(file_type, plan_id, year_from=None, year_to=None, fields=None):
    if fields is None:
        fields = 'all'
    url = 'ExportFile?file_type={file_type}&plan_id={plan_id}&fields={fields}'.format(
        file_type=file_type, plan_id=plan_id, fields=fields
    )
    if year_from:
        url += '&from=' + str(year_from)
    if year_to:
        url += '&to=' + str(year_to)
    return url


@register.filter()
def none2number(param):
    if param is None:
        return NONE
    else:
        return param
