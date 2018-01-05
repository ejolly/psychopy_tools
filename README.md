# Psychopy Tools  

This package contains some tools to make working with [Psychopy](http://www.psychopy.org/) easier.

## Example functionality  
- Graceful clean-up function to handle quitting an experiment safely by closing devices (e.g. serial port) and data files
- Extra convenience methods for `core.Clock()` that automatically do non-slip timing (e.g. for fMRI studies)
- Extra `.draw_feature()` methods for visual elements that alter functionality (e.g. drawing/moving a `visual.RatingScale` without collecting a rating)

## Installation  
`pip install git+https://github.com/ejolly/psychopy_tools`  

(*coming to pypi soon!*)

## [Documentation](http://psychopy-tools.readthedocs.io/en/latest/index.html)

The documentation contains basic usage example, how to get setup, and complete information about all current tools.

----------
### Credits  


This package was created with [Cookiecutter](http://cookiecutter.readthedocs.io/en/latest/readme.html) and the [`ejolly/cookiecutter-pypackage`](https://github.com/ejolly/cookiecutter-pypackage) template.
