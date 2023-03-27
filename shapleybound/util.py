import itertools
import string


def sample_base_payoff(n_player):
    payoff = {}
    players = [p for p, _ in zip(string.ascii_lowercase, range(n_player))]
    for size_group in range(n_player + 1):
        payoff.update(
            {"".join([f"{p}" for p in group]): 0.0 for group in itertools.combinations(players, r=size_group)})

    return payoff