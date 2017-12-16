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


@register.filter()
def none2number(param):
    if param is None:
        return NONE
    else:
        return param
