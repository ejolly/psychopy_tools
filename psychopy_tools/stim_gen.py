# -*- coding: utf-8 -*-

"""Functions associated with stimulus generation and randomization."""

from __future__ import division
import numpy as np
import pandas as pd

def random_jitter(num_trials,desired_mean=6,iti_min=1,iti_max=None,discrete=True,tolerance=.05,nsim=20000,plot=True):
    """
    Create a series of ITIs (in seconds) with a given mean, number of trials and optionally minimum and maximum. ITIs follow either a discrete geometric distribution or a continuous exponential based on user settings. Either way produces a sequence with more shorter ITIs and fewer longer ITIs.

    Perhaps better for fast event-related designs where a mean ITI is desired that comes from a skewed distribution with many shorter ITIs and a few long ITIs.

    *NOTE*: The min ITI is guaranteed, but the max ITI is an upper bound. This means
    the generated maximum may actually be lower than the desired max. Setting the
    maximum too low will result in harder/no solutions and will cause the distribution to be less well behaved.

    Args:
        num_trials (int): number of trials (number of ITIs to create)
        desired_mean (float): desired mean ITI; default 6
        iti_min (int/float): minimum ITI length; guaranteed; default 1
        iti_max (int/float): maximum ITI length; only guaranteed that ITIs will not be longer than this; default None
        discrete (bool): should ITIs be integers only (discrete geometric) or floats (continuous exponential);
            default discrete
        tolerance (float): acceptable difference from desired mean; default 0.05
        nsim (int): number of search iterations; default 10,000
        plot (bool): plot the distribution for visual inspection; default True

    Returns:
        seq (np.ndarray): sequence

    """
    assert isinstance(num_trials,int), "Number of trials must be an integer"

    assert desired_mean > iti_min, "Desired mean must be greater than min ITI!"

    if discrete:
        assert isinstance(iti_min,int), "Minimum ITI from discrete distribution must be an integer"
        if iti_max is not None:
            assert isinstance(iti_max,int), "Maximum ITI from discrete distribution must be an integer"
        else:
            iti_max = np.inf

    # Initialize
    seq_mean = 0
    i = 0
    converged = False

    while not converged:

        # Generate random sequence with desired mean accounting for minimum
        adjusted_mean = desired_mean - (iti_min - 1)
        if discrete:
            # Sampling from geometric distribution where relationship between
            # p param and mean is:
            # mean = 1/p; p = 1/mean
            seq = np.random.geometric(1./adjusted_mean,size=num_trials)
        else:
            # Sampling from exponential distribution where relationship between
            # lambda param and mean is:
            # mean = 1/lambda; lambda = 1/mean; but numpy already uses 1/lambda implicitly
            seq = np.random.exponential(adjusted_mean,size=num_trials)

        seq += iti_min - 1
        seq_mean = seq.mean()

        # Check it
        if (np.allclose(seq_mean,desired_mean,atol=tolerance)) and (seq.max() <= iti_max):
            converged = True
        elif i == nsim:
            break
        else:
            i += 1

    if converged:
        print("Solution found in {} iterations".format(i))
    else:
        print("No solution found after {} interations.\nTry increasing tolerance.".format(nsim))

    if plot:
        if discrete:
            pd.Series(seq).plot(kind='hist',bins=len(np.unique(seq)),xticks=np.arange(iti_min,seq.max()))
        else:
            pd.Series(seq).plot(kind='hist',bins=10,xlim = (iti_min,seq.max()))
    return seq

def random_uniform_jitter(num_trials,desired_mean=6, iti_min=2,iti_max=None,discrete=True,tolerance=.05,nsim=20000,plot=True):
    """
    Create a series of ITIs (in seconds) from a uniform distribution. You must provid any **two** of the following three inputs: desired_mean, iti_min, iti_max. This is because for uniform sampling, the third parameter is necessarily constrained by the first two.

    Perhaps useful for slow event related designs, where a longish mean ITI is desired with some variability around that mean.

    ITIs follow either a discrete or continuous uniform distribution. If a small amount of variability is desired around a particular mean, simply provide a desired_mean, and a iti_min (or iti_max) that is very close to desired_mean.

    Args:
        num_trials (int): number of trials (number of ITIs to create)
        desired_mean (float): desired mean ITI; default 6
        iti_min (int/float): minimum ITI length; guaranteed; default 1
        iti_max (int/float): maximum ITI length; guaranteed; default 10 (computed)
        discrete (bool): should ITIs be integers only (discrete) or floats (continuous); default discrete
        tolerance (float): acceptable difference from desired mean; default 0.05
        nsim (int): number of search iterations; default 20,000
        plot (bool): plot the distribution for visual inspection; default True

    Returns:
        seq (np.ndarray): sequence

    """

    # For uniform distributions:
    # mean = .5 * (min + max)
    # min = (2 * mean) - max
    # max = (2 * mean) - min
    # Simplify everything to min and max

    assert isinstance(num_trials,int), "Number of trials must be an integer"

    if desired_mean and iti_min:
        assert iti_max is None, "Must provide only 2 of the following: desired_mean, iti_min, iti_max"
        iti_max = (2 * desired_mean) - iti_min
    elif desired_mean and iti_max:
        assert iti_min is None, "Must provide only 2 of the following: desired_mean, iti_min, iti_max"
        iti_min = (2 * desired_mean) - iti_max
    elif iti_min and iti_max:
        assert desired_mean is None, "Must provide only 2 of the following: desired_mean, iti_min, iti_max"
        desired_mean = .5 * (iti_min + iti_max)

    assert desired_mean > iti_min, "Desired mean must be greater than min ITI!"

    if discrete:
        if iti_min:
            assert isinstance(iti_min,int), "Minimum ITI from discrete distribution must be an integer"
        elif iti_max:
            assert isinstance(iti_max,int), "Maximum ITI from discrete distribution must be an integer"

    # Initialize
    seq_mean = 0
    i = 0
    converged = False

    while not converged:

        if discrete:
            # Sampling from discrete uniform distribution
            seq = np.random.randint(iti_min,iti_max+1,size=num_trials)
        else:
            # Sampling from continuous uniform distribution
            seq = np.random.uniform(iti_min, iti_max+.000000000001,size=num_trials)

        seq_mean = seq.mean()

        # Check it
        if (np.allclose(seq_mean,desired_mean,atol=tolerance)):
            converged = True
        elif i == nsim:
            break
        else:
            i += 1

    if converged:
        print("Solution found in {} iterations".format(i))
    else:
        print("No solution found after {} interations.\nTry increasing tolerance.".format(nsim))

    if plot:
        pd.Series(seq).plot(kind='hist',bins=len(np.unique(seq)),xlim = (iti_min,iti_max))
    return seq
