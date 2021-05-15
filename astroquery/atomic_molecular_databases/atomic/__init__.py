from astropy import config as _config


class AtomicTransition:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{0}<{1!r}>'.format(self.__class__.__name__, self.name)

    def __or__(self, other):
        return MultiTransition([self, other])

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class MultiTransition:
    def __init__(self, transitions):
        self.transitions = transitions

    def __str__(self):
        return ','.join(transition.name for transition in self.transitions)

    def __repr__(self):
        return '{0}<{1!r}>'.format(self.__class__.__name__, self.transitions)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and\
            set(self.transitions) == set(other.transitions)

    def __or__(self, other):
        if isinstance(other, MultiTransition):
            multi_transition = MultiTransition(self.transitions[:])
            for transition in other:
                # avoid adding duplicates
                if transition not in self:
                    multi_transition.transitions.append(transition)
            return multi_transition
        elif isinstance(other, AtomicTransition):
            # avoid adding duplicates
            if other in self:
                return self
            return MultiTransition(self.transitions + [other])
        else:
            raise TypeError()

    def __len__(self):
        return len(self.transitions)

    def __iter__(self):
        return iter(self.transitions)

    def __contains__(self, item):
        return item in self.transitions


class Transition:
    E1 = MultiTransition([AtomicTransition('E1')])
    IC = MultiTransition([AtomicTransition('IC')])
    M1 = MultiTransition([AtomicTransition('M1')])
    E2 = MultiTransition([AtomicTransition('E2')])
    all = AtomicTransition('All')
    nebular = AtomicTransition('Neb')


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.atomic`.
    """
    url = _config.ConfigItem(
        'http://www.pa.uky.edu/~peter/atomic/',
        'Atomic Line List URL')

    timeout = _config.ConfigItem(
        60, 'time limit for connecting to the Atomic Line List server')


conf = Conf()

from .core import AtomicLineList, AtomicLineListClass

__all__ = ['AtomicLineList', 'AtomicLineListClass', 'Transition', 'conf']
