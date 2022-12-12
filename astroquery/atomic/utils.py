from . import Transition, MultiTransition


def is_valid_transitions_param(transitions):
    """
    Parameters
    ----------
    transitions : `~astroquery.atomic.Transitions`
    """
    simple_transitions = [Transition.all, Transition.nebular]
    is_custom_choice = isinstance(transitions, MultiTransition) and\
        all(t not in simple_transitions for t in transitions)

    return (transitions is None or transitions in simple_transitions
            or is_custom_choice)
