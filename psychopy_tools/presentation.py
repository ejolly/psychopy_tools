# -*- coding: utf-8 -*-

"""Main module."""

from __future__ import division

def clean_up(scanner, biopac):
    '''
    Safer close function on premature experiment quit designed to gracefully close datafiles and devices. Assumes the existence of serial port, labjack, and data_file instances named 'ser', 'lj', and 'data_file' respectively. Also assumes existence of boolean variables: 'scanner' and 'biopac'.

    This function is designed to be used as global key function for example:

    from psychopy_tools.presentation import clean_up

    # Then later in your script after window creation:
    event.globalKeys.add(key='q',func=clean_up, name='shutdown',func_args=(scanner,biopac))

    Or embedded within a while loop:

    while True:
        # do something
        if len(event.getKeys(['q'])):
            clean_up(scanner,biopac)

    '''
    print("CLOSING WINDOW...")
    window.close()
    print("CLOSING DATAFILES...")
    data_file.close()
    if scanner:
        ser.close()
    if biopac:
        lj.close()
    print("QUITTING...")
    core.quit()

def draw_scale_only(self):
    """
    Auxilliary dynamic method to only draw a rating scale, but not collect a rating.

    Use this by augmenting an already existing visual scale instance:

    from types import MethodType
    my_scale = visual.RatingScale(...)
    my_scale.draw_only = MethodType(draw_scale_only,my_scale)

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

def wait_time(self,duration):
    """
    Convenience method to augment clocks with non-slip timing.

    Use this by augmenting an already existing clock instance:

    from types import MethodType
    timer = core.Clock()
    timer.wait_time = MethodType(wait_time,timer)

    """
    self.reset()
    self.add(duration)
    while self.getTime() < 0:
        pass
