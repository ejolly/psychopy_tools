# -*- coding: utf-8 -*-

"""Main module."""

from __future__ import division
from psychopy import core

def clean_up(window,serial=None, labjack=None, data_files=None):
    '''
    Safer close function on premature experiment quit designed to gracefully close datafiles and devices. Minimum requires a window to close, but can also close: a serial object (typically one created to collect fMRI triggers), a labjack object (typically one created to trigger biopac/psychophys trigger), and a list of data_files (typically opened with Python's 'open').

    *Note*: Sometimes psychopy will issue a crash message when prematurely quitting. This is nothing to worry about.

    This function is designed to be used as Psychopy global key function for example:

    from psychopy_tools.presentation import clean_up

    # Then later in your script after window creation:
    # Close window only
    event.globalKeys.add(key='q',func=clean_up, name='shutdown',func_args=(window))

    Or embedded within a while loop:

    while True:
        # do something
        if len(event.getKeys(['q'])):
            # Close window, devices and data files
            clean_up(window,scanner,biopac,data_files)

    Args:
        window: window handle from psychopy script
        serial: scanner trigger serial object instance
        labjack: labjack (psychophys) object instance
        data_files: list of data files

    '''
    print("CLOSING WINDOW...")
    window.close()
    print("CLOSING DATAFILES...")
    if data_files:
        if not isinstance(data_files,list):
            data_files = [data_files]
        for f in data_files:
            f.close()
    if serial:
        serial.close()
    if labjack:
        labjack.close()
    print("QUITTING...")
    core.quit()

def draw_scale_only(self):
    """
    Auxilliary dynamic method to only draw a rating scale, but not collect a rating.

    Use this by augmenting an already existing visual scale instance:

    from types import MethodType
    my_scale = visual.RatingScale(...)
    my_scale.draw_only = MethodType(draw_scale_only,my_scale)

    # Use just like you would have used .draw()
    my_scale.draw_only()

    """
    self.win.setUnits(u'norm',log=False)
    proportion = self.markerPlacedAt/self.tickMarks
    for visualElement in self.visualDisplayElements:
        visualElement.draw()

    if self.markerStyle == 'glow' and self.markerExpansion != 0:
        if self.markerExpansion > 0:
            newSize = 0.1 * self.markerExpansion * proportion
            newOpacity = 0.2 + proportion
        else:  # self.markerExpansion < 0:
            newSize = - 0.1 * self.markerExpansion * (1 - proportion)
            newOpacity = 1.2 - proportion
            self.marker.setSize(self.markerBaseSize + newSize, log=False)
            self.marker.setOpacity(min(1, max(0, newOpacity)), log=False)

    x = self.offsetHoriz + self.hStretchTotal * (-0.5 + proportion)
    self.marker.setPos((x, self.markerYpos), log=False)
    self.marker.draw()
    self.win.setUnits(self.savedWinUnits,log=False)

def wait_time(self,duration,func=None,*func_args):
    """
    Convenience method to augment clocks with non-slip timing. Can just wait a specific duration and do nothing, or run some function (e.g. get a rating)

    Use this by augmenting an already existing clock instance:

    from types import MethodType
    timer = core.Clock()
    timer.wait_time = MethodType(wait_time,timer)

    # use just like you would use any other timer method
    timer.wait_time(5) # just wait 5 seconds

    Args:
        duration (int/float): time to wait in seconds
        func (function handle): function to execute for the duration

    """
    self.reset()
    self.add(duration)
    while self.getTime() < 0:
        if func:
            func(*func_args)
        else:
            pass
