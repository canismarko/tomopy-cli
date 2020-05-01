import unittest
from unittest import mock

from tomopy_cli import config

class WithParamsDecoratorTests(unittest.TestCase):
    def test_docstring(self):
        """Make sure the docstring transfers from the decorated function."""
        # Prepare a test function and then decorate it
        def times_two(x):
            """Multiple x by two."""
            return x*2
        decorated = config.with_params(times_two)
        # Make sure the docstring transferred properly
        self.assertEqual(decorated.__doc__, 'Multiple x by two.')
    
    def test_no_params(self):
        """Any function decorated this way *should* work normally too."""
        # Prepare a test function and then decorate it
        def times_two(x):
            """Multiple x by two."""
            return x*2
        decorated = config.with_params(times_two)
        # Call the decorated function and test the result
        self.assertEqual(decorated(4), 8)
        self.assertEqual(decorated(x=4), 8)
    
    def test_optional_params(self):
        """Any function decorated this way *should* work normally too."""
        # Prepare a test function and then decorate it
        def times_two(x, params=None):
            """Multiple x by two."""
            return x*2
        decorated = config.with_params(times_two)
        # Call the decorated function and test the result
        self.assertEqual(decorated(4), 8)
        self.assertEqual(decorated(x=4), 8)
        
    def test_params_by_keyword(self):
        """Passing in *params* should work just fine."""
        # Prepare a test function and then decorate it
        def times_two(x):
            return x*2
        decorated = config.with_params(times_two)
        # Call the decorated function and test the result
        params = mock.MagicMock()
        params.x = 4
        self.assertEqual(decorated(params=params), 8)
    
    def test_params_by_position(self):
        """Passing in *params* by postion should also work."""
        # Prepare a test function and then decorate it
        def times_two(params, x):
            return x*2
        decorated = config.with_params(times_two)
        # Call the decorated function and test the result
        params = mock.MagicMock()
        params.x = 4
        self.assertEqual(decorated(params), 8)
        
    def test_extra_params_argument(self):
        """Ensure parameters get passed on if there's a *params* argument."""
        # Prepare a test function and then decorate it
        def times_two(x, params):
            return x*2
        decorated = config.with_params(times_two)
        # Call the decorated function and test the result
        params = mock.MagicMock()
        del params.params # Since this hides a potentially nasty bug
        params.x = 4
        self.assertEqual(decorated(params=params), 8)
        self.assertEqual(decorated(params=params), 8)
