import itertools
import string

import pyshapley.game
import pyshapley.solution


def test_game1():
    players = {"a", "b", "c"}
    game = pyshapley.game.ManualDictGame(players, {
        "": 0,
        "a": 0,
        "b": 1,
        "c": 1,
        "ab": 0,
        "ac": 0,
        "bc": 1,
        "abc": 0
    })
    solution = pyshapley.solution.Shapley(game)
    vs = []
    print()
    for p in game.players:
        shap_p = solution.shapley(p)
        vs.append(shap_p)
        print(f"phi({p}) = {shap_p}, approx_subset({p}) = {solution.approx_shapley_with_subsets(p, 1000)}, approx_permut({p}) = {solution.approx_shapley_with_permutations(p, 1000)}")


def test_game2():
    players = {"a", "b", "c", "d"}
    game = pyshapley.game.ManualDictGame(players, {
        "": 0,
        "a": 0,
        "b": 1,
        "c": 1,
        "d": 1,
        "ab": 0,
        "ac": 0,
        "ad": 0,
        "bc": 1,
        "bd": 1,
        "cd": 1,
        "abc": 0,
        "abd": 0,
        "acd": 0,
        "bcd": 1,
        "abcd": 0
    })
    solution = pyshapley.solution.Shapley(game)
    vs = []
    print()
    for p in game.players:
        shap_p = solution.shapley(p)
        vs.append(shap_p)
        print(f"phi({p}) = {shap_p}, approx_subset({p}) = {solution.approx_shapley_with_subsets(p, 1000)}, approx_permut({p}) = {solution.approx_shapley_with_permutations(p, 1000)}")
    print(f"Sum is {sum(vs)}")

def test_game3():
    players = {"a", "b", "c", "d", "e"}
    game = pyshapley.game.ManualDictGame(players, {
        "": 0,
        "a": 0,
        "b": 1,
        "c": 1,
        "d": 1,
        "e": 1,
        "ab": 0,
        "ac": 0,
        "ad": 0,
        "ae": 0,
        "bc": 1,
        "bd": 1,
        "be": 1,
        "cd": 1,
        "ce": 1,
        "de": 1,
        "abc": 0,
        "abd": 0,
        "abe": 0,
        "acd": 0,
        "ace": 0,
        "ade": 0,
        "bcd": 1,
        "bce": 1,
        "bde": 1,
        "cde": 1,
        "abcd": 0,
        "abce": 0,
        "abde": 0,
        "acde": 0,
        "bcde": 1,
        "abcde": 0
    })
    solution = pyshapley.solution.Shapley(game)
    vs = []
    print()
    for p in game.players:
        shap_p = solution.shapley(p)
        vs.append(shap_p)
        print(f"phi({p}) = {shap_p}, approx_subset({p}) = {solution.approx_shapley_with_subsets(p, 1000)}, approx_permut({p}) = {solution.approx_shapley_with_permutations(p, 1000)}")
    print(f"Sum is {sum(vs)}")


def test_game_n():
    n_players = 8
    payoff = {}
    players = list(string.ascii_lowercase[:n_players])
    negative = string.ascii_lowercase[n_players-1]
    payoff[""] = 0
    for size_group in range(1, n_players+1):
        for comb in itertools.combinations(players, size_group):
            payoff["".join([f"{p}" for p in comb])] = 0 if negative in comb else 1
    game = pyshapley.game.ManualDictGame(players, payoff)
    solution = pyshapley.solution.Shapley(game)
    vs = []
    print()
    for p in game.players:
        shap_p = solution.shapley(p)
        vs.append(shap_p)
        print(f"phi({p}) = {shap_p}, approx_subset({p}) = {solution.approx_shapley_with_subsets(p, 1000)}, approx_permut({p}) = {solution.approx_shapley_with_permutations(p, 1000)}")
    print(f"Sum is {sum(vs)}")