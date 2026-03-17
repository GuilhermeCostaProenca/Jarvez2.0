import unittest


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ARG001
    # Reserved partition for Spotify/OneNote/media integrations as dedicated tests are extracted.
    return unittest.TestSuite()
