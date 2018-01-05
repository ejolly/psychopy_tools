Psychopy Tools
==============

This package contains some tools to make working with
`Psychopy <http://www.psychopy.org/>`__ easier.

Example functionality
---------------------

-  Graceful clean-up function to handle quitting an experiment safely by
   closing devices (e.g. serial port) and data files
-  Extra convenience methods for ``core.Clock()`` that automatically do
   non-slip timing (e.g. for fMRI studies)
-  Extra ``.draw_feature()`` methods for visual elements that alter
   functionality (e.g. drawing/moving a ``visual.RatingScale`` without
   collecting a rating)

Installation
------------

.. code-block:: python

    pip install git+https://github.com/ejolly/psychopy_tools

(*coming to pypi soon!*)

.. toctree::
   :maxdepth: 0
   :hidden:

   usage
   api

:doc:`Usage <usage>`
-------------------

:doc:`Function Help <api>`
-------------------------

--------------

Credits
~~~~~~~

This package was created with
`Cookiecutter <http://cookiecutter.readthedocs.io/en/latest/readme.html>`__
and the
`ejolly/cookiecutter-pypackage <https://github.com/ejolly/cookiecutter-pypackage>`__
template.
