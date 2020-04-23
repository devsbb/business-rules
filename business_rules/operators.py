import inspect
import re

from decimal import Decimal
from functools import wraps

from .fields import (
    FIELD_NO_INPUT,
    FIELD_NUMERIC,
    FIELD_SELECT,
    FIELD_SELECT_MULTIPLE,
    FIELD_TEXT
)
from .utils import float_to_decimal, fn_name_to_pretty_label


class BaseType:
    """Base type"""

    def __init__(self, value):
        """ Ctor """
        self.value = self._assert_valid_value_and_cast(value)

    def _assert_valid_value_and_cast(self, value):
        """Check value and cast to type"""
        raise NotImplementedError()

    @classmethod
    def get_all_operators(cls) -> list:
        """Get operators list"""
        methods = inspect.getmembers(cls)
        return [{'name': m[0],
                 'label': m[1].label,
                 'input_type': m[1].input_type}
                for m in methods if getattr(m[1], 'is_operator', False)]


def export_type(cls):
    """ Decorator to expose the given class to business_rules.export_rule_data. """
    cls.export_in_rule_data = True
    return cls


def type_operator(input_type, label=None,
                  assert_type_for_arguments=True):
    """ Decorator to make a function into a type operator.

    - assert_type_for_arguments - if True this patches the operator function
      so that arguments passed to it will have _assert_valid_value_and_cast
      called on them to make type errors explicit.
    """

    def wrapper(func):
        func.is_operator = True
        func.label = label or fn_name_to_pretty_label(func.__name__)
        func.input_type = input_type

        @wraps(func)
        def inner(self, *args, **kwargs):
            if assert_type_for_arguments:
                args = [self._assert_valid_value_and_cast(arg) for arg in args]
                kwargs = dict((k, self._assert_valid_value_and_cast(v))
                              for k, v in kwargs.items())
            return func(self, *args, **kwargs)

        return inner

    return wrapper


@export_type
class StringType(BaseType):
    """String type"""
    name = "string"

    def _assert_valid_value_and_cast(self, value):
        """ """
        value = value or ""
        if not isinstance(value, str):
            raise AssertionError("{0} is not a valid string type.".
                                 format(value))
        return value

    @type_operator(FIELD_TEXT)
    def equal_to(self, other_string):
        """Equal to"""
        return self.value == other_string

    @type_operator(FIELD_TEXT, label="Equal To (case insensitive)")
    def equal_to_case_insensitive(self, other_string):
        """Equal to CI"""
        return self.value.lower() == other_string.lower()

    @type_operator(FIELD_TEXT)
    def not_equal_to(self, other_string):
        """Not equal to"""
        return self.value != other_string

    @type_operator(FIELD_TEXT, label="Not Equal To (case insensitive)")
    def not_equal_to_case_insensitive(self, other_string):
        """Not equal to CI"""
        return self.value.lower() != other_string.lower()

    @type_operator(FIELD_TEXT)
    def starts_with(self, other_string):
        """Starts with"""
        return self.value.startswith(other_string)

    @type_operator(FIELD_TEXT)
    def ends_with(self, other_string):
        """Ends with"""
        return self.value.endswith(other_string)

    @type_operator(FIELD_TEXT)
    def contains(self, other_string):
        """Contains"""
        return other_string in self.value

    @type_operator(FIELD_TEXT)
    def matches_regex(self, regex):
        """RE matches"""
        return re.search(regex, self.value)

    @type_operator(FIELD_NO_INPUT)
    def non_empty(self):
        """Non empty """
        return bool(self.value)


@export_type
class NumericType(BaseType):
    """Numeric type"""
    EPSILON = Decimal('0.000001')

    name = "numeric"

    @staticmethod
    def _assert_valid_value_and_cast(value):
        """Check value and cast"""
        if isinstance(value, float):
            return float_to_decimal(value)
        if isinstance(value, int):
            return Decimal(value)
        if isinstance(value, Decimal):
            return value

        raise AssertionError("{0} is not a valid numeric type.".
                             format(value))

    @type_operator(FIELD_NUMERIC)
    def equal_to(self, other_numeric):
        """Equal to"""
        return abs(self.value - other_numeric) <= self.EPSILON

    @type_operator(FIELD_NUMERIC)
    def greater_than(self, other_numeric):
        """Greate than"""
        return (self.value - other_numeric) > self.EPSILON

    @type_operator(FIELD_NUMERIC)
    def greater_than_or_equal_to(self, other_numeric):
        """Greater or equal """
        return self.greater_than(other_numeric) or self.equal_to(other_numeric)

    @type_operator(FIELD_NUMERIC)
    def less_than(self, other_numeric):
        """Less then"""
        return (other_numeric - self.value) > self.EPSILON

    @type_operator(FIELD_NUMERIC)
    def less_than_or_equal_to(self, other_numeric):
        """Less or equal"""
        return self.less_than(other_numeric) or self.equal_to(other_numeric)


@export_type
class BooleanType(BaseType):
    """Boolean type"""
    name = "boolean"

    def _assert_valid_value_and_cast(self, value):
        """Check value and cast to type"""
        if not isinstance(value, bool):
            raise AssertionError("{0} is not a valid boolean type".
                                 format(value))
        return value

    @type_operator(FIELD_NO_INPUT)
    def is_true(self):
        """is true"""
        return self.value

    @type_operator(FIELD_NO_INPUT)
    def is_false(self):
        """is false"""
        return not self.value


@export_type
class SelectType(BaseType):
    """Select type"""
    name = "select"

    def _assert_valid_value_and_cast(self, value):
        """Check value and cast to type"""
        if not hasattr(value, '__iter__'):
            raise AssertionError("{0} is not a valid select type".
                                 format(value))
        return value

    @staticmethod
    def _case_insensitive_equal_to(value_from_list, other_value):
        """Equal to CI"""
        if (isinstance(value_from_list, str) and
                isinstance(other_value, str)):
            return value_from_list.lower() == other_value.lower()

        return value_from_list == other_value

    @type_operator(FIELD_SELECT, assert_type_for_arguments=False)
    def contains(self, other_value):
        """Contains"""
        for val in self.value:
            if self._case_insensitive_equal_to(val, other_value):
                return True
        return False

    @type_operator(FIELD_SELECT, assert_type_for_arguments=False)
    def does_not_contain(self, other_value):
        """Doesn't contain"""
        for val in self.value:
            if self._case_insensitive_equal_to(val, other_value):
                return False
        return True


@export_type
class SelectMultipleType(BaseType):
    """Select multiple type"""
    name = "select_multiple"

    def _assert_valid_value_and_cast(self, value):
        """Check value and cast"""
        if not hasattr(value, '__iter__'):
            raise AssertionError("{0} is not a valid select multiple type".
                                 format(value))
        return value

    @type_operator(FIELD_SELECT_MULTIPLE)
    def contains_all(self, other_value):
        """Contains all"""
        select = SelectType(self.value)
        for other_val in other_value:
            if not select.contains(other_val):
                return False
        return True

    @type_operator(FIELD_SELECT_MULTIPLE)
    def is_contained_by(self, other_value):
        """Is contained by"""
        other_select_multiple = SelectMultipleType(other_value)
        return other_select_multiple.contains_all(self.value)

    @type_operator(FIELD_SELECT_MULTIPLE)
    def shares_at_least_one_element_with(self, other_value):
        """Shares at least uno elemento"""
        select = SelectType(self.value)
        for other_val in other_value:
            if select.contains(other_val):
                return True
        return False

    @type_operator(FIELD_SELECT_MULTIPLE)
    def shares_exactly_one_element_with(self, other_value):
        """Shares only one"""
        found_one = False
        select = SelectType(self.value)
        for other_val in other_value:
            if select.contains(other_val):
                if found_one:
                    return False
                found_one = True
        return found_one

    @type_operator(FIELD_SELECT_MULTIPLE)
    def shares_no_elements_with(self, other_value):
        """No shares"""
        return not self.shares_at_least_one_element_with(other_value)
