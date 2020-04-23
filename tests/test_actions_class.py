from business_rules.actions import (
    BaseActions,
    ReturnNumericActions,
    ReturnTextActions,
    rule_action
)
from business_rules.fields import FIELD_NUMERIC, FIELD_TEXT

from . import TestCase


class ActionsClassTests(TestCase):
    """ Test methods on classes that inherit from BaseActions.
    """

    def test_base_has_no_actions(self):
        """ _ """
        self.assertEqual(len(BaseActions.get_all_actions()), 0)

    def test_return_numeric_actions_interface(self):
        """ _ """
        actions = ReturnNumericActions.get_all_actions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['name'], 'return_numeric')
        self.assertEqual(actions[0]['label'], 'Return Numeric')
        self.assertEqual(
            actions[0]['params'],
            [{'fieldType': FIELD_NUMERIC,
              'name': 'return_value',
              'label': 'Return Value'}]
        )

    def test_return_numeric_actions_should_return_passed_value(self):
        """ _ """
        expected_value = 5.1
        self.assertEqual(
            ReturnNumericActions().return_numeric(expected_value),
            expected_value
        )

    def test_return_text_actions_interface(self):
        """ _ """
        actions = ReturnTextActions.get_all_actions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['name'], 'return_text')
        self.assertEqual(actions[0]['label'], 'Return Text')
        self.assertEqual(
            actions[0]['params'],
            [{'fieldType': FIELD_TEXT, 'name': 'return_value', 'label': 'Return Value'}]
        )

    def test_return_text_actions_should_return_passed_value(self):
        """ _ """
        expected_value = 'expected text to be returned'
        self.assertEqual(
            ReturnTextActions().return_text(expected_value),
            expected_value
        )

    def test_get_all_actions(self):
        """ Returns a dictionary listing all the functions on the class that
        have been decorated as actions, with some of the data about them.
        """

        class SomeActions(BaseActions):
            """ docs """

            @rule_action(params={'foo': FIELD_TEXT})
            # pylint: disable=unused-argument,no-self-use,blacklisted-name
            def some_action(self, foo):
                """ _ """
                return 'blah'

            # pylint: disable=unused-argument, no-self-use
            def non_action(self):
                """ _ """
                return 'baz'

        actions = SomeActions.get_all_actions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['name'], 'some_action')
        self.assertEqual(actions[0]['label'], 'Some Action')
        self.assertEqual(actions[0]['params'], [{
            'fieldType': FIELD_TEXT, 'name': 'foo', 'label': 'Foo'}])

        # should work on an instance of the class too
        self.assertEqual(len(SomeActions().get_all_actions()), 1)

    def test_rule_action_doesnt_allow_unknown_field_types(self):
        """ _ """
        err_string = 'Unknown field type blah specified for action some_action param foo'
        with self.assertRaisesRegex(AssertionError, err_string):
            @rule_action(params={'foo': 'blah'})
            # pylint: disable=unused-argument,blacklisted-name,unused-variable
            def some_action(self, foo):
                pass

    def test_rule_action_doesnt_allow_unknown_parameter_name(self):
        """ _ """
        err_string = 'Unknown parameter name foo specified for action some_action'
        with self.assertRaisesRegex(AssertionError, err_string):
            @rule_action(params={'foo': 'blah'})
            # pylint: disable=unused-argument,blacklisted-name,unused-variable
            def some_action(self):
                pass

    def test_rule_action_with_no_params_or_label(self):
        """ A rule action should not have to specify paramers or label. """

        # pylint: disable=unused-argument
        @rule_action()
        def some_action(self):
            pass

        self.assertTrue(some_action.is_rule_action)
