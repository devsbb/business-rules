from business_rules.variables import BaseVariables, string_rule_variable
from business_rules.actions import BaseActions, rule_action
from business_rules.exceptions import MissingVariableException
from business_rules import run
import pytest


class Payment:
    def __init__(self, amount, type):
        self.amount = amount
        self.type = type


class Order:
    def __init__(self, name, payment):
        self.name = name
        self.payment = payment


class Variables(BaseVariables):

    def __init__(self, order):
        self.order = order

    @string_rule_variable()
    async def order_payment_type(self):
        if self.order.payment is None:
            raise MissingVariableException()

        return self.order.payment.type


class Actions(BaseActions):
    @rule_action()
    async def approve(self):
        return {'action': 'approve'}


@pytest.mark.asyncio
async def test_missing_variable_exception():
    rule = {
        'conditions': {
            'all': [
                {
                    'name': 'order_payment_type',
                    'operator': 'not_equal_to',
                    'value': 'paypal'
                }
            ]
        },
        'actions': [
            {
                'name': 'approve'
            }
        ]
    }
    order = Order(
        name='order',
        payment=Payment(amount=10, type='credit_card')
    )
    result = await run(
        rule=rule,
        defined_variables=Variables(order),
        defined_actions=Actions()
    )
    assert result == {'action_name': 'approve', 'action_params': {}, 'action_result': {'action': 'approve'}}

    order = Order(
        name='order',
        payment=Payment(amount=10, type='paypal')
    )
    result = await run(
        rule=rule,
        defined_variables=Variables(order),
        defined_actions=Actions()
    )
    assert result is None

    order = Order(
        name='order',
        payment=None
    )
    result = await run(
        rule=rule,
        defined_variables=Variables(order),
        defined_actions=Actions()
    )
    assert result is None
