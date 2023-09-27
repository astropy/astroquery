# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astroquery.query import BaseQuery, BaseVOQuery


class with_VO(BaseVOQuery, BaseQuery):
    pass


class without_VO(BaseQuery):
    pass


class only_VO(BaseVOQuery):
    pass


def test_session_VO_header():
    test_instance = with_VO()
    user_agent = test_instance._session.headers['User-Agent']
    assert 'astroquery' in user_agent
    assert 'pyVO' in user_agent
    assert user_agent.count('astroquery') == 1


def test_session_nonVO_header():
    test_instance = without_VO()
    user_agent = test_instance._session.headers['User-Agent']
    assert 'astroquery' in user_agent
    assert 'pyVO' not in user_agent
    assert user_agent.count('astroquery') == 1


def test_session_hooks():
    # Test that we don't override the session in the BaseVOQuery
    test_instance = with_VO()
    assert len(test_instance._session.hooks['response']) > 0

    test_VO_instance = only_VO()
    assert len(test_VO_instance._session.hooks['response']) == 0
