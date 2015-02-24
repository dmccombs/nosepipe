from django.test import TestCase


class BaseTestCase(TestCase):
    def test_simple(self):
        self.assertTrue(1)
