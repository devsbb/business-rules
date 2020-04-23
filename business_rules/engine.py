import logging

from .fields import FIELD_NO_INPUT


logger = logging.getLogger(__name__)


class InvalidRuleDefinition(Exception):
    """Invalid rule"""


def get_value(rule_list, defined_variables, defined_actions) -> dict:
    """
    Run Rules till first will be triggered and returns its actions results.
    Exception will be raised if more than one action was executed by the
    triggered rule.
    :returns: value returned by executed action
    """
    rule_results = run_all(rule_list, defined_variables, defined_actions,
                           stop_on_first_trigger=True)
    if len(rule_results) == 0:
        raise InvalidRuleDefinition(
            'No rule executed or no action found in matching rule'
        )
    actions_result = rule_results[0]
    if len(actions_result) != 1:
        raise InvalidRuleDefinition(
            f'Expected only one action to be executed. '
            f'Executed {actions_result} actions')

    return actions_result[_get_first_key_in_dictionary(actions_result)]


def _get_first_key_in_dictionary(dictionary):
    """Get first key of the dict"""
    return list(dictionary)[0]


def run_all(rule_list,
            defined_variables,
            defined_actions,
            stop_on_first_trigger=False) -> list:
    """ Run all Rules and return the rules actions results
    :returns:
        rule_results(list): list of dictionaries. Each dictionary is a rule
        actions' results
    """
    logger.debug("business-rules starting")
    rule_results = []
    for rule in rule_list:
        actions_results = run(rule, defined_variables, defined_actions)
        if actions_results:
            rule_results.append(actions_results)
            if stop_on_first_trigger:
                logger.debug("business-rules finished")
                return rule_results
    logger.debug("business-rules finished")
    return rule_results


def run(rule, defined_variables, defined_actions) -> dict:
    """ Run the rule and get the action returned result
    Attributes:
        rule(dict): the rule dictionary
        defined_variables(BaseVariables): the defined set of variables object
        defined_actions(BaseActions): the actions object
    """
    conditions, actions = rule['conditions'], rule['actions']
    rule_triggered = check_conditions_recursively(conditions, defined_variables)
    if rule_triggered:
        logger.debug(f'business-rules conditions: {conditions}')
        logger.debug(f'business-rules actions: {actions}')

        return do_actions(actions, defined_actions)
    return {}


def check_conditions_recursively(conditions, defined_variables):
    """ Check conditions """
    keys = list(conditions.keys())
    if keys == ['all']:
        assert len(conditions['all']) >= 1
        for condition in conditions['all']:
            if not check_conditions_recursively(condition, defined_variables):
                return False
        return True

    if keys == ['any']:
        assert len(conditions['any']) >= 1
        for condition in conditions['any']:
            if check_conditions_recursively(condition, defined_variables):
                return True
        return False

    # help prevent errors - any and all can only be in the condition dict
    # if they're the only item
    assert not ('any' in keys or 'all' in keys)
    return check_condition(conditions, defined_variables)


def check_condition(condition, defined_variables):
    """
    Checks a single rule condition - the condition will be made up of
    variables, values, and the comparison operator. The defined_variables
    object must have a variable defined for any variables in this condition
    """
    name = condition['name']
    op = condition['operator']
    value = condition['value']
    operator_type = _get_variable_value(defined_variables, name)
    if 'value_is_variable' in condition and condition['value_is_variable']:
        variable_name = value
        temp_value = _get_variable_value(defined_variables, variable_name)
        value = temp_value.value
    return _do_operator_comparison(operator_type, op, value)


def _get_variable_value(defined_variables, name):
    """ Call the function provided on the defined_variables object with the
    given name (raise exception if that doesn't exist) and casts it to the
    specified type.

    Returns an instance of operators.BaseType
    """

    def fallback(*args, **kwargs):
        raise AssertionError("Variable {0} is not defined in class {1}".format(
            name, defined_variables.__class__.__name__))

    method = getattr(defined_variables, name, fallback)
    val = method()
    return method.field_type(val)


def _do_operator_comparison(operator_type, operator_name, comparison_value):
    """ Finds the method on the given operator_type and compares it to the
    given comparison_value.

    operator_type should be an instance of operators.BaseType
    comparison_value is whatever python type to compare to
    returns a bool
    """

    def fallback(*args, **kwargs):
        raise AssertionError("Operator {0} does not exist for type {1}".format(
            operator_name, operator_type.__class__.__name__))

    method = getattr(operator_type, operator_name, fallback)
    if getattr(method, 'input_type', '') == FIELD_NO_INPUT:
        return method()
    return method(comparison_value)


def do_actions(actions, defined_actions) -> dict:
    """ Run the actions
    Attributes:
        actions(list): list of dictionaries of actions. e.g: [
            { "name": "put_on_sale",
            "params": {"sale_percentage": 0.25},
            }
        ]
    Returns:
        actions_results(dict): Dictionary of actions results
            e.g: {"put_on_sale: [product1, product2, ...]}
    """
    actions_results = {}
    for action in actions:
        method_name = action['name']

        params = action.get('params') or {}
        if hasattr(defined_actions, method_name):
            method = getattr(defined_actions, method_name)
        else:
            raise AssertionError(
                'Action {} is not defined in class {}'.format(
                    method_name, defined_actions.__class__.__name__
                )
            )
        actions_results[method_name] = method(**params)

    return actions_results
