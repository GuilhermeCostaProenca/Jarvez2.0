import unittest


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ARG001
    # Reserved partition for the WhatsApp migration work. Coverage still lives in broader action tests.
    return unittest.TestSuite()
