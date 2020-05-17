import datetime
import json

from business_rules import (
    run,
    export_rule_data,
)
from business_rules.actions import (
    BaseActions,
    rule_action
)
from business_rules.variables import (
    numeric_rule_variable,
    string_rule_variable,
    rule_variable,
    BaseVariables,
)
from business_rules.fields import FIELD_NUMERIC


def test_1():
    # rules = _some_function_to_receive_from_client()
    rules = """
    [{
        "conditions": {
            "all": [{
                    "name": "expiration_days",
                    "operator": "less_than",
                    "value": 5
                },
                {
                    "name": "current_inventory",
                    "operator": "greater_than",
                    "value": 20
                }
            ]
        },
        "actions": [{
            "name": "put_on_sale",
            "params": {
                "sale_percentage": 0.25
            }
        }]
    },
    {
        "conditions": {
            "any": [{
                "name": "current_inventory",
                "operator": "less_than",
                "value": 5
            }]
        },
        "actions": [{
            "name": "order_more",
            "params": {
                "number_to_order": 40
            }
        }]
    }
    ]"""

    class Order:
        def __init__(self):
            self.expiration_date = datetime.datetime.now().date()

    class Product:
        """ Product to test rules """

        def __init__(self):
            self.id = 1
            self.price = 1.34
            self.current_inventory = 21
            self.orders = [Order(), Order()]

    class ProductVariables(BaseVariables):

        def __init__(self, product):
            self.product = product

        @numeric_rule_variable
        def current_inventory(self):
            return self.product.current_inventory

        @numeric_rule_variable(label='Days until expiration')
        def expiration_days(self):
            last_order = self.product.orders[-1]
            return (last_order.expiration_date - datetime.date.today()).days

        @string_rule_variable()
        def current_month(self):
            return datetime.datetime.now().strftime("%B")

    class ProductActions(BaseActions):

        def __init__(self, product):
            self.product = product

        @rule_action(params={"sale_percentage": FIELD_NUMERIC})
        def put_on_sale(self, sale_percentage):
            # self.product.price = (1.0 - sale_percentage) * self.product.price
            # self.product.save()
            return (1.0 - sale_percentage) * self.product.price

        @rule_action(params={"number_to_order": FIELD_NUMERIC})
        def order_more(self, number_to_order):
            # Product(product_id=self.product.id,
            #         quantity=number_to_order)
            return number_to_order

    export_result = export_rule_data(ProductVariables, ProductActions)

    rules = json.loads(rules)

    product = Product()
    # actions = ProductActions(product)
    # vars = ProductVariables(product)

    run_all_result = run(
        rule_list=rules,
        defined_variables=ProductVariables(product),
        defined_actions=ProductActions(product),
        stop_on_first_trigger=False
    )

    print(run_all_result)

    assert run_all_result is not None
