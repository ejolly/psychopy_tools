Usage
=====

1. Add to Psychopy's path
~~~~~~~~~~~~~~~~~~~~~~~~~

If using the standalone Psychopy application you'll need to add this to
Psychopy's path:

- Find out where ``pip`` installed the package (search for your ``site-packages``) directory, it'll be inside
- If you're using ``conda`` this should be somewhere like:  ``/Users/You/anaconda/lib/python2.7/site-packages/psychopy_tools-0.1.0-py2.7.egg`` (*note: the version number maybe different!*)
- Copy this path
- In Psychopy goto: File > Preferences > General
- Paste the path into the "paths" field, e.g ``['/Users/You/anaconda/lib/python2.7/site-packages/psychopy_tools-0.1.0-py2.7.egg']``
- Click OK to apply

2. Import within your experiment script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can just import this as if you would any other Psychopy
functionality:

.. code-block:: python

    from psychopy.presentation import clean_up

3. Typical use cases
~~~~~~~~~~~~~~~~~~~~

Generally Psychopy Tools contains modules that either:

1. work like normal Python functions
2. are designed to augment existing Psychopy classes with new abilities.
3. are subclasses of Psychopy classes with added attributes or functionality

An example of 1. is the ``random_jitter`` function which can be used like any Python function. For example creating a random sequence of 100 ITIs (jitters) with a mean of 5s, a min of 4s and a max of 20s:

.. code-block:: python

    from psychopy_tools.stim_gen import random_jitter

    ITIs = random_jitter(desired_mean=5,
                         num_trials=200,
                         min_iti=4,
                         max_iti=20)


An example of 2. is the ``wait_time`` function which is a convenience method designed to give ``clock.Clock()`` the ability to wait for a specific amount of time or run a function for a specific amount of time, using `non-slip timing <http://www.psychopy.org/general/timing/nonSlipTiming.html>`_. To use a function like this you must first create the object you want (in this case a clock) and then assign this function to it as a new method. For example:

.. code-block:: python

    from psychopy_tools.presentation import wait_time

    # We need a Python function that will convert wait_time to a method
    from types import MethodType

    # Then create your clock as your normally would
    timer = core.Clock()

    # Then add wait_time as a new method to the instance by wrapping it
    timer.wait_time = MethodType(wait_time,timer)

    # Use just like you would use any other timer method
    timer.wait_time(5) # just wait 5 seconds

An example of 3. is the ``rating.RatingScale`` class which sub-classes Psychopy's `visual.RatingScale`. This can be imported and used anywhere in a script one would normally use `visual.RatingScale`. It behaves identically except for a few differences: a) the ability to take an optional `bounds` parameter which prevents a user from making responses above or below certain values. This should be provided as a list ``bounds = [lower, upper]`` in units of the scale. It's left to the user to visualize these bounds in the window (b) a ``.draw_only()`` method which only displays the scale without listening for responses. This can be useful for using a ``RatingScale`` as a stimulus as oppose to an input controller, for example when visualizing values on a ``RatingScale`` or controlling the display of one ``RatingScale`` from another that actually takes inputs.

See the :doc:`Function Help <api>` for complete info on how to use specific functions.
