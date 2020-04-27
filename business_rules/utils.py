import inspect

from decimal import Context, Decimal, Inexact


class ActionResult:
    STATUS_SUCCESS = 'success'
    STATUS_ERROR = 'error'

    def __init__(self, name: str, params: dict, status, result):
        self.action_name = name
        self.action_params = params
        self.action_status = status
        self.action_result = result

    @property
    def is_failed(self):
        return self.action_status == self.STATUS_ERROR

    def to_dict(self):
        return {
            'action_name': self.action_name,
            'action_params': self.action_params,
            'action_status': self.action_status,
            'action_result': self.action_result,
        }



def fn_name_to_pretty_label(name) -> str:
    """ Func name to label """
    return ' '.join([w.title() for w in name.split('_')])


def export_rule_data(variables, actions) -> dict:
    """ export_rule_data is used to export all information about the
    variables, actions, and operators to the client. This will return a
    dictionary with three keys:
    - variables: a list of all available variables along with their label,
      type and options
    - actions: a list of all actions along with their label and params
    - variable_type_operators: a dictionary of all field_types -> list
      of available operators
    """
    # pylint: disable=import-outside-toplevel
    from . import operators

    actions_data = actions.get_all_actions()
    variables_data = variables.get_all_variables()
    variable_type_operators = {}
    for variable_class in inspect.getmembers(
            operators, lambda x: getattr(x, 'export_in_rule_data', False)
    ):
        variable_type = variable_class[1]  # getmembers returns (name, value)
        variable_type_operators[variable_type.name] = variable_type.get_all_operators()

    return {"variables": variables_data,
            "actions": actions_data,
            "variable_type_operators": variable_type_operators}


def float_to_decimal(f) -> Decimal:
    """
    Convert a floating point number to a Decimal with
    no loss of information. Intended for Python 2.6 where
    casting float to Decimal does not work.
    """
    n, d = f.as_integer_ratio()
    numerator, denominator = Decimal(n), Decimal(d)
    ctx = Context(prec=60)
    result = ctx.divide(numerator, denominator)
    while ctx.flags[Inexact]:
        ctx.flags[Inexact] = False
        ctx.prec *= 2
        result = ctx.divide(numerator, denominator)
    return result
