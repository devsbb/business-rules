import asyncio
import logging
from typing import Union

from .actions import BaseActions
from .fields import FIELD_NO_INPUT
from .variables import BaseVariables

logger = logging.getLogger(__name__)


class InvalidRuleDefinition(Exception):
    """Invalid rule"""


async def run(
    rule: dict,
    defined_variables: BaseVariables,
    defined_actions: BaseActions,
) -> Union[dict, None]:
    """
    Check rules and run actions
    :param rule: rule conditions
    :param defined_variables: defined variable
    :param defined_actions: defined actions
    :return:
    {
        'action_name': action_name,
        'action_params': action_params,
        'action_result': action_result
    }
    """

    conditions, actions = rule['conditions'], rule['actions']
    if actions is None:
        raise InvalidRuleDefinition('Actions are None')

    if len(actions) !=1:
        raise InvalidRuleDefinition(f'You should specify only one action, '
                                    f'but specified: {len(actions)}')
    action = actions[0]

    rule_triggered = await check_conditions_recursively(
        conditions,
        defined_variables,
    )
    if rule_triggered:
        logger.debug(f'business-rules conditions: {conditions}')
        logger.debug(f'business-rules actions: {actions}')

        return await do_action(action, defined_actions)


async def check_conditions_recursively(conditions, defined_variables):
    """ Check conditions """
    keys = list(conditions.keys())
    if keys == ['all']:
        assert len(conditions['all']) >= 1
        for condition in conditions['all']:
            if not await check_conditions_recursively(condition, defined_variables):
                return False
        return True

    if keys == ['any']:
        assert len(conditions['any']) >= 1
        for condition in conditions['any']:
            if await check_conditions_recursively(condition, defined_variables):
                return True
        return False

    # help prevent errors - any and all can only be in the condition dict
    # if they're the only item
    assert not ('any' in keys or 'all' in keys)
    return await check_condition(conditions, defined_variables)


async def check_condition(condition, defined_variables):
    """
    Checks a single rule condition - the condition will be made up of
    variables, values, and the comparison operator. The defined_variables
    object must have a variable defined for any variables in this condition
    """
    name = condition['name']
    op = condition['operator']
    value = condition['value']
    operator_type = await _get_variable_value(defined_variables, name)
    if 'value_is_variable' in condition and condition['value_is_variable']:
        variable_name = value
        temp_value = await _get_variable_value(defined_variables, variable_name)
        value = temp_value.value
    return _do_operator_comparison(operator_type, op, value)


async def _get_variable_value(defined_variables, name):
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

    if asyncio.iscoroutine(val):
        val = await val

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


async def do_action(action, defined_actions) -> dict:
    """
    Run action
    return:
    {
        'action_name': 'action_name',
        'action_params': action_params,
        'action_result': action_result
    }
    """
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
    action_result = method(**params)
    if asyncio.iscoroutine(action_result):
        action_result = await action_result

    return {
        'action_name': method_name,
        'action_params': params,
        'action_result': action_result
    }
