from getpass import getuser

import pytest

from duqtools.ids import ImasHandle

TEST_STRINGS = (
    'gu3ido/m0o/9234/123',
    'guido4/mo0/9234/123',
    '123_guido_123/123moo/9234/123',
    'moo/9234/123',
)
TEST_OUTPUT = (
    ('gu3ido', 'm0o', 9234, 123),
    ('guido4', 'mo0', 9234, 123),
    ('123_guido_123', '123moo', 9234, 123),
    (getuser(), 'moo', 9234, 123),
)


@pytest.mark.parametrize('string,expected', zip(TEST_STRINGS, TEST_OUTPUT))
def test_from_string(string, expected):
    handle = ImasHandle.from_string(string)

    assert handle.user == expected[0]
    assert handle.db == expected[1]
    assert handle.shot == expected[2]
    assert handle.run == expected[3]