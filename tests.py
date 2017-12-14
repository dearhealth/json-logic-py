"""JonLogic tests."""

from __future__ import unicode_literals

import json
import logging
import unittest
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
from json_logic import jsonLogic


# Python 2 fallback
if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Fallback for Python versions prior to 3.4
class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""

    def __init__(self, *args, **kwargs):
        self.messages = dict(
            debug=[], info=[], warning=[], error=[], critical=[])
        super(MockLoggingHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        try:
            self.messages[record.levelname.lower()].append(record.getMessage())
        except Exception:
            self.handleError(record)

    def reset(self):
        for logging_level in self.messages.keys():
            self.messages[logging_level] = []


class SharedJsonLogicTests(unittest.TestCase):
    """Shared tests from from http://jsonlogic.com/tests.json."""

    cnt = 0

    @classmethod
    def create_test(cls, logic, data, expected):
        """Add new test to the class."""

        def test(self):
            """Actual test function."""
            self.assertEqual(jsonLogic(logic, data), expected)

        test.__doc__ = "{},  {}  =>  {}".format(logic, data, expected)
        setattr(cls, "test_{}".format(cls.cnt), test)
        cls.cnt += 1


UNSUPPORTED_OPERATIONS = (
    "?:", "substr", "filter", "map", "reduce", "all", "none", "some")
skipped_tests_count = 0

SHARED_TESTS = json.loads(
    urlopen("http://jsonlogic.com/tests.json").read().decode('utf-8'))

for item in SHARED_TESTS:
    if isinstance(item, list):
        if any(("'%s'" % op in str(item[0])) for op in UNSUPPORTED_OPERATIONS):
            skipped_tests_count += 1
        else:
            SharedJsonLogicTests.create_test(*item)
print("Skipped %d shared test(s)" % skipped_tests_count)


class SpecificJsonLogicTest(unittest.TestCase):
    """Specific JsonLogic tests that are not included into the shared list."""

    @classmethod
    def setUpClass(cls):
        super(SpecificJsonLogicTest, cls).setUpClass()
        mock_logger = logging.getLogger('json_logic')
        mock_logger.setLevel(logging.DEBUG)
        cls.mock_logger_handler = MockLoggingHandler()
        mock_logger.addHandler(cls.mock_logger_handler)
        cls.log_messages = cls.mock_logger_handler.messages

    def setUp(self):
        super(SpecificJsonLogicTest, self).setUp()
        self.mock_logger_handler.reset()

    @classmethod
    def tearDownClass(cls):
        mock_logger = logging.getLogger('json_logic')
        mock_logger.removeHandler(cls.mock_logger_handler)
        super(SpecificJsonLogicTest, cls).tearDownClass()

    def test_bad_operator(self):
        with self.assertRaisesRegex(ValueError, "Unrecognized operation"):
            self.assertFalse(jsonLogic({'fubar': []}))

    def test_array_of_logic_entries(self):
        logic = [
            {'+': [1, 2]},
            {'var': 'a'},
            {'if': [{'>': [1, 2]}, 'yes', 'no']},
            "just some data"
        ]
        self.assertSequenceEqual(
            jsonLogic(logic, {'a': "test"}),
            [3, "test", "no", "just some data"])

    def test_log_forwards_first_argument_to_logging_module_at_info_level(self):
        # with self.assertLogs('json_logic', logging.INFO) as log:
        jsonLogic({'log': 'apple'})
        jsonLogic({'log': 1})
        jsonLogic({'log': True})
        self.assertEqual(len(self.log_messages['info']), 3)
        self.assertIn('apple', self.log_messages['info'][0])
        self.assertIn('1', self.log_messages['info'][1])
        self.assertIn('True', self.log_messages['info'][2])

    def test_log_returns_unmodified_first_argument(self):
        self.assertEqual(jsonLogic({'log': 'apple'}), 'apple')
        self.assertEqual(jsonLogic({'log': 1}), 1)
        self.assertEqual(jsonLogic({'log': True}), True)

    def test_strict_equality_ignores_numeric_type_differences(self):
        self.assertIs(jsonLogic({'===': [1, 1]}), True)
        self.assertIs(jsonLogic({'===': [1.23, 1.23]}), True)
        self.assertIs(jsonLogic({'===': [1, 1.0]}), True)
        self.assertIs(
            jsonLogic({'===': [10000000000000000000, 10000000000000000000.0]}),
            True)

    def test_arithmetic_operations_convert_data_to_apropriate_numerics(self):
        # Conversion
        self.assertIs(jsonLogic({'+': [1]}), 1)
        self.assertIs(jsonLogic({'+': [1.0]}), 1)
        self.assertIs(jsonLogic({'+': ["1"]}), 1)
        self.assertIs(jsonLogic({'+': ["1.0"]}), 1)
        self.assertEqual(jsonLogic({'+': [1.23]}), 1.23)
        self.assertEqual(jsonLogic({'+': ["1.23"]}), 1.23)
        self.assertEqual(
            jsonLogic({'+': [10000000000000000000]}), 10000000000000000000)
        # Arithmetic operations
        self.assertIs(jsonLogic({'+': [1, 1]}), 2)
        self.assertIs(jsonLogic({'+': [0.25, 0.75]}), 1)
        self.assertEqual(jsonLogic({'+': [1, 0.75]}), 1.75)
        self.assertIs(jsonLogic({'-': [1, 1]}), 0)
        self.assertIs(jsonLogic({'-': [1.75, 0.75]}), 1)
        self.assertEqual(jsonLogic({'-': [1, 0.75]}), 0.25)
        self.assertIs(jsonLogic({'*': [1, 2]}), 2)
        self.assertIs(jsonLogic({'*': [2, 0.5]}), 1)
        self.assertEqual(jsonLogic({'*': [2, 0.75]}), 1.5)
        self.assertIs(jsonLogic({'/': [2, 2]}), 1)
        self.assertEqual(jsonLogic({'/': [2, 4]}), 0.5)
        self.assertIs(jsonLogic({'/': [2, 0.5]}), 4)
        self.assertIs(jsonLogic({'%': [2, 2]}), 0)
        self.assertIs(jsonLogic({'%': [4, 3]}), 1)
        self.assertEqual(jsonLogic({'%': [2, 1.5]}), 0.5)


if __name__ == '__main__':
    unittest.main()
