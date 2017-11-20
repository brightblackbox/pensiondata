from django import template

register = template.Library()


@register.filter(name='is_in')
def is_in(var, str_list):
    print('---------------------')
    print(str_list)
    # str_list : separated with comma: ","

    if str_list is None:
        return False
    arg_list = str_list.split()
    return var in arg_list

