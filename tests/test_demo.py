import pytest
from unittest import TestCase

assertions = TestCase('__init__')

def test_demo():
    assertions.assertEqual(0, 0, "0 should equal 0")
