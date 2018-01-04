# Psychopy Tools  

This package contains some tools to make working with [Psychopy](http://www.psychopy.org/) easier.

## Example functionality  
- Graceful clean-up function to handle quitting an experiment safely by closing devices (e.g. serial port) and data files
- Extra convenience methods for `core.Clock()` that automatically do non-slip timing (e.g. for fMRI studies)
- Extra `.draw_feature()` methods for visual elements that alter functionality (e.g. drawing/moving a `visual.RatingScale` without collecting a rating)

## Installation  
`pip install git+https://github.com/ejolly/psychopy_tools`  

(*coming to pypi soon!*)

## Usage  

### Add to Psychopy's path
If using the standalone Psychopy application you'll need to add this to Psychopy's path:
- Find out where `pip` installed the package (search for your `site-packages`) directory, it'll be inside
    - If you're using `conda` this should be somewhere like: `/Users/You/anaconda/lib/python2.7/site-packages/psychopy_tools-0.1.0-py2.7.egg`
    - Note the version number maybe different!
- Copy this path
- In Psychopy goto: File > Preferences > General
- Paste the path into the "paths" field, e.g `['/Users/You/anaconda/lib/python2.7/site-packages/psychopy_tools-0.1.0-py2.7.egg']`
- Click OK to apply

### Within your experiment script
You can just import this as if you would any other Psychopy functionality:  
`from psychopy.presentation import clean_up`

See the function helps or the documentation for more info.

----------
### Credits  


This package was created with [Cookiecutter](http://cookiecutter.readthedocs.io/en/latest/readme.html) and the [`ejolly/cookiecutter-pypackage`](https://github.com/ejolly/cookiecutter-pypackage) template.
