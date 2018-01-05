# -*- coding: utf-8 -*-

"""Main module."""

from __future__ import division
import numpy as np
import pandas as pd


def random_jitter(desired_mean,num_trials,iti_min=1,iti_max=np.inf,discrete=True,tolerance=.05,nsim=10000,plot=True):
    """
    Create a series of ITIs (in seconds) with a given mean and number of trials.
    ITIs follow either a discrete geometric distribution or a continuous exponential
    based on user settings. Either way produces a sequence with more shorter ITIs and fewer longer ITIs.
    A minimum and maximum ITI can also be provided.

    *NOTE*: The min ITI is guaranteed, but the max ITI is an upper bound. This means
    the generated maximum may actually be lower than the desired max. Setting the
    maximum too low will result in harder/no solutions and will cause the distribution
    to be less well behaved.

    Args:
        desired_mean (float): desired mean ITI
        num_trials (int): number of trials (number of ITIs to create)
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

    assert desired_mean > iti_min, "Desired mean must be greater than min ITI!"

    if discrete:
        assert isinstance(iti_min,int), "Minimum ITI from discrete distribution must be an integer"
        if iti_max != np.inf:
            assert isinstance(iti_max,int), "Maximum ITI from discrete distribution must be an integer"

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
