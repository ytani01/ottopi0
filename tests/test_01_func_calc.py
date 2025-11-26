#
# (c) 2025 Yoichi Tanibayashi
#
import pytest

from ottopi0.func_calc import Calc


class TestCalc:
    """
    Test class for the Calc class in func_calc.py.
    """

    def setup_method(self):
        """
        Set up the test environment before each test method.
        Initializes an instance of the Calc class.
        """
        self.calc = Calc()

    def test_init(self):
        """
        Test the __init__ method of the Calc class.
        Ensures that the 'foo' attribute is correctly initialized.
        """
        assert self.calc.foo == "abc"

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            (1, 2, 3),  # Positive integers
            (-1, -2, -3),  # Negative integers
            (1.5, 2.5, 4.0),  # Positive floats
            (-1.5, -2.5, -4.0),  # Negative floats
            (0, 0, 0),  # Zeroes
            (100, -50, 50),  # Mixed signs
            (1e9, 2e9, 3e9),  # Large numbers
        ],
    )
    def test_add(self, a, b, expected):
        """
        Test the add method with various inputs.
        """
        assert self.calc.add(a, b) == expected

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            (3, 2, 1),  # Positive integers
            (-1, -2, 1),  # Negative integers
            (4.5, 2.5, 2.0),  # Positive floats
            (-1.5, -2.5, 1.0),  # Negative floats
            (0, 0, 0),  # Zeroes
            (50, -50, 100),  # Mixed signs
            (3e9, 1e9, 2e9),  # Large numbers
        ],
    )
    def test_sub(self, a, b, expected):
        """
        Test the sub method with various inputs.
        """
        assert self.calc.sub(a, b) == expected

    @pytest.mark.parametrize(
        "func, a, b, expected",
        [
            ("add", 1, 2, 3),
            ("sub", 3, 1, 2),
            ("add", -1, 1, 0),
            ("sub", -5, -2, -3),
            ("add", 1.5, 2.5, 4.0),
            ("sub", 4.5, 2.5, 2.0),
        ],
    )
    def test_calc_valid_func(self, func, a, b, expected):
        """
        Test the calc method with valid function strings ('add', 'sub').
        """
        assert self.calc.calc(func, a, b) == expected

    @pytest.mark.parametrize(
        "func, a, b",
        [
            ("multiply", 1, 2),  # Invalid function string
            ("divide", 10, 2),  # Invalid function string
            ("", 5, 3),  # Empty function string
            (None, 1, 1),  # None as function string
        ],
    )
    def test_calc_invalid_func(self, func, a, b):
        """
        Test the calc method with invalid function strings.
        It should return 0.0 for any unknown function.
        """
        assert self.calc.calc(func, a, b) == 0.0
