import time
import s3fs
from datetime import datetime
from math import comb
import numpy as np
import itertools
import string
import pyshapley.game
import pyshapley.solution
from joblib import Parallel, delayed

from shapleysearch.persistence import LocalCache

ns = np.arange(9, 13)
size_population = 100
n_generations = 1000
p_remove = 0.7
p_mutation = 0.3
p_crossover_top = (0, 0.05)
# check = lambda p_crossover, p_mutation, s, p_remove: ((p_crossover*s)*((p_crossover*s)-1))/2+p_mutation*s < p_remove*s

# For pop=40:
# n_remove = 0.2*40 = 8
# n_mutate = 0.15*40 = 6
# added by crossover: 0.15*40=6 -> 6*(6+1)/2 = 21
# removed after mutation and crossover 40-8=32+6+21=59 -> 59-40 = 19 removed afterwards

bounds = {
    #"1/2": lambda n: -1/2,
    "-2/n": lambda n: -2/n,
    "-(n-(n+1)/n)/n": lambda n: -(n-(n+1)/n)/n, # = -1+((n+1)/(n**2))
    "-(n-1)/n": lambda n: -(n-1)/n,
    "-1": lambda n: -1
}

cachemanager = LocalCache("/media/data/shapleysearch/")


def sample_candidate(payoff):
    candidate = payoff.copy()
    for group in payoff:
        candidate[group] = float(np.random.rand(1))
        chance_limits = np.random.rand(1)
        if chance_limits < 0.2:
            candidate[group] = 0.0
        elif chance_limits > 0.8:
            candidate[group] = 1.0
    candidate[''] = 0
    return candidate


def evaluate_candidate(players, candidate):
    cache_hit = cachemanager.get(len(players), candidate)
    if cache_hit is not None:
        return cache_hit

    game = pyshapley.game.ManualDictGame(players, candidate)
    solution = pyshapley.solution.Shapley(game)
    phi_min = None
    for p in game.players:
        phi_cur = solution.shapley(p)
        if phi_min is None or phi_cur < phi_min:
            phi_min = phi_cur
    return phi_min


def evaluate_population(players, population):
    def process_eval(players, cand, phi_prev):
        if phi_prev is not None:
            return cand, phi_prev
        return cand, evaluate_candidate(players, cand)

    return Parallel(n_jobs=8)(delayed(process_eval)(players, cand, prev_eval) for (cand, prev_eval) in population)


def sample_evaluated_population(players, payoff, n_sample):
    def sample_and_eval_cand():
        cand = sample_candidate(payoff)
        phi_min = evaluate_candidate(players, cand)
        return (cand, phi_min)

    return Parallel(n_jobs=8)(delayed(sample_and_eval_cand)() for _ in range(n_sample))

"""def equal_candidate(cand1, cand2):
    if len(cand1) is not len(cand2):
        return False
    for group in cand1:
        if group not in cand2:
            return False
        if cand1[group] != cand2[group]:
            return False
    return True"""


def crossover(cand1, cand2):
    child = cand1
    groups_available = list(cand1.keys())
    n_crossings = np.random.randint(3, len(groups_available))
    groups = np.random.choice(groups_available, n_crossings)
    for group in groups:
        child[group] = cand2[group]
    return child


def mutate_switch(cand):
    mutant = cand
    groups_available = list(mutant.keys()-{""})
    assert "" not in groups_available
    #idx_pairs_available = list(itertools.combinations(range(len(groups_available)), 2))
    pairs_available = list(itertools.combinations(groups_available, 2))
    n_mutations = comb(len(groups_available), 2)
    idx_pairs_switch = np.random.choice(range(len(pairs_available)), n_mutations, replace=False)
    for idx_pair in idx_pairs_switch:
        group1, group2 = pairs_available[idx_pair]
        mutant[group1] = cand[group2]
    return mutant


def mutate_change(cand):
    mutant = cand
    groups_available = list(mutant.keys()-{""})
    assert "" not in groups_available
    n_mutations = np.random.randint(1, len(groups_available))
    groups = np.random.choice(groups_available, n_mutations)
    for group in groups:
        mutant[group] = min(max(mutant[group]+np.random.normal(0, 0.1), 0), 1)
    return mutant


def mutate(cand):
    ops_mutate = [mutate_change, mutate_switch]
    op_choice = np.random.choice(ops_mutate, 1)[0]
    return op_choice(cand)


for n_player in ns:
    time_start = time.time()
    players = [p for p, _ in zip(string.ascii_lowercase, range(n_player))]
    payoff = {}
    for size_group in range(n_player + 1):
        payoff.update({"".join([f"{p}" for p in group]): 0.0 for group in itertools.combinations(players, r=size_group)})

    cur_gen = 0
    n_sampled_total = size_population
    n_sampled_total_co = 0
    n_sampled_total_mut = 0
    population = [(sample_candidate(payoff), None) for _ in range(size_population)]

    while cur_gen < n_generations:
        cur_gen += 1

        # Evaluate candidates
        #population = [(candidate, evaluate_candidate(players, candidate) if _prev_eval is None else _prev_eval) for (candidate, _prev_eval) in population]
        population = evaluate_population(players, population)

        # Resize population to original
        size_cur = len(population)
        if size_cur > size_population:
            del population[-(size_cur-size_population):]
        elif size_cur < size_population:
            """for _ in range(size_population-size_cur):
                candidate = sample_candidate(payoff)
                population.append((candidate, evaluate_candidate(players, candidate)))"""
            population.extend(sample_evaluated_population(players, payoff, size_population-size_cur))
            n_sampled_total += size_population-size_cur
        assert len(population) == size_population, f"{len(population)}, {size_population}"

        population = sorted(population, key=lambda x: x[1])
        n_remove = max(int(p_remove*len(population)), 1)
        n_mutate = int(p_mutation*len(population))
        idx_start = int(p_crossover_top[0]*len(population))
        idx_end = int(p_crossover_top[1]*len(population))

        """print("To remove")
        print([val for _, val in population[-n_remove:]])
        print("Top:")
        print(population[0])"""

        # Remove p1% worst candidates
        #population.pop(n_remove)
        #print(f"#pop = {len(population)}, removing {n_remove}")
        #print(f"Worst is at {population[-1][1]}")
        del population[-n_remove:]
        #print(f"Worst after deletion is at {population[-1][1]}")
        #print(f"#pop = {len(population)}")

        # Mutations of best
        n_added_mutations = 0
        for cand, _ in population[:n_mutate]:
            population.append((mutate(cand), None))
            n_added_mutations += 1
        n_sampled_total += n_added_mutations
        n_sampled_total_mut += n_added_mutations

        # Crossover
        n_added_crossover = 0
        for c1, c2 in itertools.combinations([cand for cand, _ in population[idx_start:idx_end]], 2):
            population.append((crossover(c1, c2), None))
            n_added_crossover += 1
        n_sampled_total += n_added_crossover
        n_sampled_total_co += n_added_crossover

        cachemanager.update(n_player, population)
        #print(f"#pop = {len(population)}")

    # Final evaluation
    population = [(candidate, evaluate_candidate(players, candidate) if _prev_eval is None else _prev_eval) for (candidate, _prev_eval) in population]
    population = sorted(population, key=lambda x: x[1])
    best_candidate, best_min = population[0]

    time_end = time.time()
    time_computation = time_end-time_start

    print(f"Started at {datetime.fromtimestamp(time_start)}")
    print(f"Took {time_computation:10.4f}s for computation")
    print(f"Ran {cur_gen} generations and sampled {n_sampled_total} candidates in total of which have been {n_sampled_total_co} crossovers and {n_sampled_total_mut} mutations")
    print(f"Game over {n_player}, min phi = {best_min} ; {best_candidate}")
    for name_bound in bounds:
        val_bound = bounds[name_bound](n_player)
        if best_min > val_bound:
            print(f"\tbound by {name_bound}={val_bound}")
        else:
            print(f"\tNOT BOUND by {name_bound}={val_bound}")
    print(f"Ended completely {datetime.fromtimestamp(time.time())}")