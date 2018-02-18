# -*- coding: utf-8 -*-

"""Modified fork of PsychoPy's original visual rating scale. This scale has the add 'bounds' parameter to limit choices above and below certain values during response collection."""

from __future__ import division
# Original code
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from builtins import str
from builtins import range
from past.builtins import basestring
import copy
import sys
import numpy

from psychopy import core, logging, event
from psychopy.colors import isValidColor
from psychopy.visual.circle import Circle
from psychopy.visual.patch import PatchStim
from psychopy.visual.shape import ShapeStim
from psychopy.visual.text import TextStim
from psychopy.visual.basevisual import MinimalStim
from psychopy.visual.helpers import pointInPolygon, groupFlipVert
from psychopy.tools.attributetools import logAttrib
from psychopy.constants import FINISHED, STARTED, NOT_STARTED


class RatingScale(MinimalStim):

    """
    This is a sub-class of the PsychoPy's original visual.RatingScale. It has two specific alterations:

    1) It can take an optional 'bounds' parameter on initialization that prevent responses and mouse-controlled movement above or beyond certain values. This should be provided as a list [lower_bound, upper_bound] in units of the underlying scale or proportions if the scale spans the range 0-1. It is left to the user to add visual elements to indicate where these bounds are on the screen.

    2) A .draw_only() method that simply draws the scale the screen without listening for any input responses. Useful if the scale is used as a stimulus object rather than an input object (e.g. for displaying certain scale values, or yoking values on one-scale to a different input scale)

    Args:
        bounds (list): lower and upper bounds to prevent responses or movement control; in internal units of the scale
        **kwargs: all other input arguments to visual.RatingScale

    """

    def __init__(self,
                 win,
                 scale='<default>',
                 choices=None,
                 low=1,
                 high=7,
                 precision=1,
                 labels=(),
                 tickMarks=None,
                 tickHeight=1.0,
                 marker='triangle',
                 markerStart=None,
                 markerColor=None,
                 markerExpansion=1,
                 singleClick=False,
                 disappear=False,
                 textSize=1.0,
                 textColor='LightGray',
                 textFont='Helvetica Bold',
                 showValue=True,
                 showAccept=True,
                 acceptKeys='return',
                 acceptPreText='key, click',
                 acceptText='accept?',
                 acceptSize=1.0,
                 leftKeys='left',
                 rightKeys='right',
                 respKeys=(),
                 lineColor='White',
                 skipKeys='tab',
                 mouseOnly=False,
                 noMouse=False,
                 size=1.0,
                 stretch=1.0,
                 pos=None,
                 minTime=0.4,
                 maxTime=0.0,
                 flipVert=False,
                 depth=0,
                 name=None,
                 autoLog=True,
                 bounds=[0.,1.],
                 mouseScale=1,
                 **kwargs):  # catch obsolete args
    
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        super(RatingScale, self).__init__(name=name, autoLog=False)

        # warn about obsolete arguments; Jan 2014, for v1.80:
        obsoleted = {'showScale', 'ticksAboveLine', 'displaySizeFactor',
                     'markerStyle', 'customMarker', 'allowSkip',
                     'stretchHoriz', 'escapeKeys', 'textSizeFactor',
                     'showScale', 'showAnchors',
                     'lowAnchorText', 'highAnchorText'}
        obsArgs = set(kwargs.keys()).intersection(obsoleted)
        if obsArgs:
            msg = ('RatingScale obsolete args: %s; see changelog v1.80.00'
                   ' for notes on how to migrate')
            logging.error(msg % list(obsArgs))
            core.quit()
        # kwargs will absorb everything, including typos, so warn about bad
        # args
        unknownArgs = set(kwargs.keys()).difference(obsoleted)
        if unknownArgs:
            msg = "RatingScale unknown kwargs: %s"
            logging.error(msg % list(unknownArgs))
            core.quit()

        self.autoLog = False  # needs to start off False
        self.win = win
        self.disappear = disappear

        # internally work in norm units, restore to orig units at the end of
        # __init__:
        self.savedWinUnits = self.win.units
        self.win.setUnits(u'norm', log=False)
        self.depth = depth

        # 'hover' style = like hyperlink with hover over choices:
        if marker == 'hover':
            showAccept = False
            singleClick = True
            textSize *= 1.5
            mouseOnly = True
            noMouse = False

        # make things well-behaved if the requested value(s) would be trouble:
        self._initFirst(showAccept, mouseOnly, noMouse, singleClick,
                        acceptKeys, marker, markerStart, low, high, precision,
                        choices, scale, tickMarks, labels, tickHeight)
        self._initMisc(minTime, maxTime)

        # Set scale & position, key-bindings:
        self._initPosScale(pos, size, stretch)
        self._initKeys(self.acceptKeys, skipKeys,
                       leftKeys, rightKeys, respKeys)

        # Construct the visual elements:
        self._initLine(tickMarkValues=tickMarks,
                       lineColor=lineColor, marker=marker,mouseScale=mouseScale)
        self._initMarker(marker, markerColor, markerExpansion)
        self._initTextElements(win, self.scale, textColor, textFont, textSize,
                               showValue, tickMarks)
        self._initAcceptBox(self.showAccept, acceptPreText, acceptText,
                            acceptSize, self.markerColor, self.textSizeSmall,
                            textSize, self.textFont)

        # List-ify the visual elements; self.marker is handled separately
        self.visualDisplayElements = []
        if self.showScale:
            self.visualDisplayElements += [self.scaleDescription]
        if self.showAccept:
            self.visualDisplayElements += [self.acceptBox, self.accept]
        if self.labels:
            for item in self.labels:
                if not item.text == '':  # skip any empty placeholders
                    self.visualDisplayElements.append(item)
        if marker != 'hover':
            self.visualDisplayElements += [self.line]

        # Mirror (flip) vertically if requested
        self.flipVert = False
        self.setFlipVert(flipVert)

        # Final touches:
        self.origScaleDescription = self.scaleDescription.text
        self.reset()  # sets .status, among other things
        self.win.setUnits(self.savedWinUnits, log=False)

        self.timedOut = False
        self.beyondMinTime = False

        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" % (self.name, repr(self)))

        self.bounds = bounds

    def __repr__(self, complete=False):
        return self.__str__(complete=complete)  # from MinimalStim

    def _initFirst(self, showAccept, mouseOnly, noMouse, singleClick,
                   acceptKeys, marker, markerStart, low, high, precision,
                   choices, scale, tickMarks, labels, tickHeight):
        """some sanity checking; various things are set, especially those
        that are used later; choices, anchors, markerStart settings are
        handled here
        """
        self.showAccept = bool(showAccept)
        self.mouseOnly = bool(mouseOnly)
        self.noMouse = bool(noMouse) and not self.mouseOnly  # mouseOnly wins
        self.singleClick = bool(singleClick)
        self.acceptKeys = acceptKeys
        self.precision = precision
        self.labelTexts = None
        self.tickHeight = tickHeight

        if not self.showAccept:
            # the accept button is the mouse-based way to accept the current
            # response
            if len(list(self.acceptKeys)) == 0:
                # make sure there is in fact a way to respond using a
                # key-press:
                self.acceptKeys = ['return']
            if self.mouseOnly and not self.singleClick:
                # then there's no way to respond, so deny mouseOnly / enable
                # using keys:
                self.mouseOnly = False
                msg = ("RatingScale %s: ignoring mouseOnly (because "
                       "showAccept and singleClick are False)")
                logging.warning(msg % self.name)

        # 'choices' is a list of non-numeric (unordered) alternatives:
        if choices and len(list(choices)) < 2:
            msg = "RatingScale %s: choices requires 2 or more items"
            logging.error(msg % self.name)
        if choices and len(list(choices)) >= 2:
            low = 0
            high = len(list(choices)) - 1
            self.precision = 1  # a fractional choice makes no sense
            self.choices = choices
            self.labelTexts = choices
        else:
            self.choices = False
        if marker == 'hover' and not self.choices:
            logging.error("RatingScale: marker='hover' requires "
                          "a set of choices.")
            core.quit()

        # Anchors need to be well-behaved [do after choices]:
        try:
            self.low = int(low)
        except Exception:
            self.low = 1
        try:
            self.high = int(high)
        except Exception:
            self.high = self.low + 1
        if self.high <= self.low:
            self.high = self.low + 1
            self.precision = 100

        if not self.choices:
            diff = self.high - self.low
            if labels and len(labels) == 2:
                # label the endpoints
                first, last = labels[0], labels[-1]
                self.labelTexts = [first] + [''] * (diff - 1) + [last]
            elif labels and len(labels) == 3 and diff > 1 and (1 + diff) % 2:
                # label endpoints and middle tick
                placeHolder = [''] * ((diff - 2) // 2)
                self.labelTexts = ([labels[0]] + placeHolder +
                                   [labels[1]] + placeHolder +
                                   [labels[2]])
            elif labels in [None, False]:
                self.labelTexts = []
            else:
                first, last = str(self.low), str(self.high)
                self.labelTexts = [first] + [''] * (diff - 1) + [last]

        self.scale = scale
        if tickMarks and not labels is False:
            if labels is None:
                self.labelTexts = tickMarks
            else:
                self.labelTexts = labels
            if len(self.labelTexts) != len(tickMarks):
                msg = "RatingScale %s: len(labels) not equal to len(tickMarks)"
                logging.warning(msg % self.name)
                self.labelTexts = tickMarks
            if self.scale == "<default>":
                self.scale = False

        # Marker pre-positioned? [do after anchors]
        try:
            self.markerStart = float(markerStart)
        except Exception:
            if (isinstance(markerStart, basestring) and
                    type(self.choices) == list and
                    markerStart in self.choices):
                self.markerStart = self.choices.index(markerStart)
                self.markerPlacedAt = self.markerStart
                self.markerPlaced = True
            else:
                self.markerStart = None
                self.markerPlaced = False
        else:  # float(markerStart) suceeded
            self.markerPlacedAt = self.markerStart
            self.markerPlaced = True
        # default markerStart = 0 if needed but otherwise unspecified:
        if self.noMouse and self.markerStart is None:
            self.markerPlacedAt = self.markerStart = 0
            self.markerPlaced = True

    def _initMisc(self, minTime, maxTime):
        # precision is the fractional parts of a tick mark to be sensitive to,
        # in [1,10,100]:
        if type(self.precision) != int or self.precision < 10:
            self.precision = 1
            self.fmtStr = "%.0f"  # decimal places, purely for display
        elif self.precision == 60:
            self.fmtStr = "%d:%s"  # minutes:seconds.zfill(2)
        elif self.precision < 100:
            self.precision = 10
            self.fmtStr = "%.1f"
        else:
            self.precision = 100
            self.fmtStr = "%.2f"

        self.clock = core.Clock()  # for decision time
        try:
            self.minTime = float(minTime)
        except ValueError:
            self.minTime = 1.0
        self.minTime = max(self.minTime, 0.)
        try:
            self.maxTime = float(maxTime)
        except ValueError:
            self.maxTime = 0.0
        self.allowTimeOut = bool(self.minTime < self.maxTime)

        self.myMouse = event.Mouse(
            win=self.win, visible=bool(not self.noMouse))
        # Mouse-click-able 'accept' button pulsates (cycles its brightness
        # over frames):
        framesPerCycle = 100
        self.pulseColor = [0.6 + 0.22 * numpy.cos(i/15.65)
                           for i in range(framesPerCycle)]

    def _initPosScale(self, pos, size, stretch, log=True):
        """position (x,y) and size (magnification) of the rating scale
        """
        # Screen position (translation) of the rating scale as a whole:
        if pos:
            if len(list(pos)) == 2:
                offsetHoriz, offsetVert = pos
            elif log and self.autoLog:
                msg = "RatingScale %s: pos expects a tuple (x,y)"
                logging.warning(msg % self.name)
        try:
            self.offsetHoriz = float(offsetHoriz)
        except Exception:
            if self.savedWinUnits == 'pix':
                self.offsetHoriz = 0
            else:  # default x in norm units:
                self.offsetHoriz = 0.0
        try:
            self.offsetVert = float(offsetVert)
        except Exception:
            if self.savedWinUnits == 'pix':
                self.offsetVert = int(self.win.size[1]/-5.0)
            else:  # default y in norm units:
                self.offsetVert = -0.4
        # pos=(x,y) will consider x,y to be in win units, but want norm
        # internally
        if self.savedWinUnits == 'pix':
            self.offsetHoriz = float(self.offsetHoriz) / self.win.size[0] / 0.5
            self.offsetVert = float(self.offsetVert) / self.win.size[1] / 0.5
        # just expose; not used elsewhere yet
        self.pos = [self.offsetHoriz, self.offsetVert]

        # Scale size (magnification) of the rating scale as a whole:
        try:
            self.stretch = float(stretch)
        except ValueError:
            self.stretch = 1.
        try:
            self.size = float(size) * 0.6
        except ValueError:
            self.size = 0.6

    def _initKeys(self, acceptKeys, skipKeys, leftKeys, rightKeys, respKeys):
        # keys for accepting the currently selected response:
        if self.mouseOnly:
            self.acceptKeys = []  # no valid keys, so must use mouse
        else:
            if type(acceptKeys) not in [list, tuple, set]:
                acceptKeys = [acceptKeys]
            self.acceptKeys = acceptKeys
        self.skipKeys = []
        if skipKeys and not self.mouseOnly:
            if type(skipKeys) not in [list, tuple, set]:
                skipKeys = [skipKeys]
            self.skipKeys = list(skipKeys)
        if type(leftKeys) not in [list, tuple, set]:
            leftKeys = [leftKeys]
        self.leftKeys = leftKeys
        if type(rightKeys) not in [list, tuple, set]:
            rightKeys = [rightKeys]
        self.rightKeys = rightKeys

        # allow responding via arbitrary keys if given as a param:
        nonRespKeys = (self.leftKeys + self.rightKeys + self.acceptKeys +
                       self.skipKeys)
        if respKeys and hasattr(respKeys, '__iter__'):
            self.respKeys = respKeys
            self.enableRespKeys = True
            if set(self.respKeys).intersection(nonRespKeys):
                msg = 'RatingScale %s: respKeys may conflict with other keys'
                logging.warning(msg % self.name)
        else:
            # allow resp via numeric keys if the response range is in 0-9
            self.respKeys = []
            if not self.mouseOnly and self.low > -1 and self.high < 10:
                self.respKeys = [str(i)
                                 for i in range(self.low, self.high + 1)]
            # but if any digit is used as an action key, that should
            # take precedence so disable using numeric keys:
            if set(self.respKeys).intersection(nonRespKeys) == set([]):
                self.enableRespKeys = True
            else:
                self.enableRespKeys = False
        if self.enableRespKeys:
            self.tickFromKeyPress = {}
            for i, key in enumerate(self.respKeys):
                self.tickFromKeyPress[key] = i + self.low

        # if self.noMouse:
        #     could check that there are appropriate response keys

        self.allKeys = nonRespKeys + self.respKeys

    def _initLine(self, tickMarkValues=None, lineColor='White', marker=None,mouseScale=1):
        """define a ShapeStim to be a graphical line, with tick marks.
        ### Notes (JRG Aug 2010)
        Conceptually, the response line is always -0.5 to +0.5
        ("internal" units). This line, of unit length, is scaled and
        translated for display. The line is effectively "center justified",
        expanding both left and right with scaling, with pos[] specifying
        the screen coordinate (in window units, norm or pix) of the
        mid-point of the response line. Tick marks are in integer units,
        internally 0 to (high-low), with 0 being the left end and (high-low)
        being the right end. (Subjects see low to high on the screen.)
        Non-numeric (categorical) choices are selected using tick-marks
        interpreted as an index, choice[tick]. Tick units get mapped to
        "internal" units based on their proportion of the total ticks
        (--> 0. to 1.). The unit-length internal line is expanded or
        contracted by stretch and size, and then is translated to
        position pos (offsetHoriz=pos[0], offsetVert=pos[1]).
        pos is the name of the arg, and its values appear in the code as
        offsetHoriz and offsetVert only for historical reasons (could be
        refactored for clarity).
        Auto-rescaling reduces the number of tick marks shown on the
        screen by a factor of 10, just for nicer appearance, without
        affecting the internal representation.
        Thus, the horizontal screen position of the i-th tick mark,
        where i in [0,n], for n total ticks (n = high-low),
        in screen units ('norm') will be:
          tick-i             == offsetHoriz + (-0.5 + i/n ) * stretch * size
        So two special cases are:
          tick-0 (left end)  == offsetHoriz - 0.5 * stretch * size
          tick-n (right end) == offsetHoriz + 0.5 * stretch * size
        The vertical screen position is just offsetVert (in screen norm units).
        To elaborate: tick-0 is the left-most tick, or "low anchor";
        here 0 is internal, the subject sees <low>.
        tick-n is the right-most tick, or "high anchor", or
        internal-tick-(high-low), and the subject sees <high>.
        Intermediate ticks, i, are located proportionally
        between -0.5 to + 0.5, based on their proportion
        of the total number of ticks, float(i)/n.
        The "proportion of total" is used because it's a line of unit length,
        i.e., the same length as used to internally represent the
        scale (-0.5 to +0.5).
        If precision > 1, the user / experimenter is asking for
        fractional ticks. These map correctly
        onto [0, 1] as well without requiring special handling
        (just do ensure float() ).
        Another note: -0.5 to +0.5 looked too big to be the default
        size of the rating line in screen norm units,
        so I set the internal size = 0.6 to compensate (i.e., making
        everything smaller). The user can adjust the scaling around
        the default by setting size, stretch, or both.
        This means that the user / experimenter can just think of > 1
        being expansion (and < 1 == contraction) relative to the default
        (internal) scaling, and not worry about the internal scaling.
        ### Notes (HS November 2012)
        To allow for labels at the ticks, the positions of the tick marks
        are saved in self.tickPositions. If tickMarks, those positions
        are used instead of the automatic positions.
        """

        self.lineColor = lineColor
        # vertical height of each tick, norm units; used for markers too:
        self.baseSize = 0.04
        # num tick marks to display, can get autorescaled
        self.tickMarks = float(self.high - self.low)
        self.autoRescaleFactor = 1

        if tickMarkValues:
            tickTmp = numpy.asarray(tickMarkValues, dtype=numpy.float32)
            tickMarkPositions = (tickTmp - self.low)/self.tickMarks
        else:
            # visually remap 10 ticks onto 1 tick in some conditions (=
            # cosmetic):
            if (self.low == 0 and
                    self.tickMarks > 20 and
                    int(self.tickMarks) % 10 == 0):
                self.autoRescaleFactor = 10
                self.tickMarks /= self.autoRescaleFactor
            tickMarkPositions = numpy.linspace(0, 1, self.tickMarks + 1)
        self.scaledPrecision = float(self.precision * self.autoRescaleFactor)

        # how far a left or right key will move the marker, in tick units:
        self.keyIncrement = 1. / self.autoRescaleFactor / self.precision
        self.hStretchTotal = self.stretch * self.size

        # ends of the rating line, in norm units:
        self.lineLeftEnd = self.offsetHoriz - 0.5 * self.hStretchTotal
        self.lineRightEnd = self.offsetHoriz + 0.5 * self.hStretchTotal

        # space around the line within which to accept mouse input:
        # not needed if self.noMouse, but not a problem either
        pad = 0.06 * self.size * mouseScale
        if marker == 'hover':
            padText = ((1.0/(3 * (self.high - self.low))) *
                       (self.lineRightEnd - self.lineLeftEnd))
        else:
            padText = 0
        self.nearLine = [
            [self.lineLeftEnd - pad - padText, -2 * pad + self.offsetVert],
            [self.lineLeftEnd - pad - padText, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad + padText, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad + padText, -2 * pad + self.offsetVert]]

        # vertices for ShapeStim:
        self.tickPositions = []  # list to hold horizontal positions
        vertices = [[self.lineLeftEnd, self.offsetVert]]  # first vertex
        # vertical height of ticks (purely cosmetic):
        if self.tickHeight is False:
            self.tickHeight = -1.  # backwards compatibility for boolean
        # numeric -> scale tick height;  float(True) == 1.
        tickSize = self.baseSize * self.size * float(self.tickHeight)
        lineLength = self.lineRightEnd - self.lineLeftEnd
        for count, tick in enumerate(tickMarkPositions):
            horizTmp = self.lineLeftEnd + lineLength * tick
            vertices += [[horizTmp, self.offsetVert + tickSize],
                         [horizTmp, self.offsetVert]]
            if count < len(tickMarkPositions) - 1:
                tickRelPos = lineLength * tickMarkPositions[count + 1]
                nextHorizTmp = self.lineLeftEnd + tickRelPos
                vertices.append([nextHorizTmp, self.offsetVert])
            self.tickPositions.append(horizTmp)
        vertices += [[self.lineRightEnd, self.offsetVert],
                     [self.lineLeftEnd, self.offsetVert]]

        # create the line:
        self.line = ShapeStim(win=self.win, units='norm', vertices=vertices,
                              lineWidth=4, lineColor=self.lineColor,
                              name=self.name + '.line', autoLog=False)

    def _initMarker(self, marker, markerColor, expansion):
        """define a visual Stim to be used as the indicator.
        marker can be either a string, or a visual object (custom marker).
        """
        # preparatory stuff:
        self.markerOffsetVert = 0.
        if isinstance(marker, basestring):
            self.markerStyle = marker
        elif not hasattr(marker, 'draw'):
            logging.error("RatingScale: custom marker has no draw() method")
            self.markerStyle = 'triangle'
        else:
            self.markerStyle = 'custom'
            if hasattr(marker, 'pos'):
                self.markerOffsetVert = marker.pos[1]
            else:
                logging.error(
                    "RatingScale: custom marker has no pos attribute")

        self.markerSize = 8. * self.size
        if isinstance(markerColor, basestring):
            markerColor = markerColor.replace(' ', '')

        # define or create self.marker:
        if self.markerStyle == 'hover':
            self.marker = TextStim(win=self.win, text=' ', units='norm',
                                   autoLog=False)  # placeholder
            self.markerOffsetVert = .02
            if not markerColor:
                markerColor = 'darkorange'
        elif self.markerStyle == 'triangle':
            scaledTickSize = self.baseSize * self.size
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize * 3],
                    [scaledTickSize * 1.8, scaledTickSize * 3], [0, -0.005]]
            if markerColor is None or not isValidColor(markerColor):
                markerColor = 'DarkBlue'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                                    lineWidth=0.1, lineColor=markerColor,
                                    fillColor=markerColor,
                                    name=self.name + '.markerTri',
                                    autoLog=False)
        elif self.markerStyle == 'slider':
            scaledTickSize = self.baseSize * self.size
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize],
                    [scaledTickSize * 1.8, scaledTickSize],
                    [scaledTickSize * 1.8, -1 * scaledTickSize],
                    [-1 * scaledTickSize * 1.8, -1 * scaledTickSize]]
            if markerColor is None or not isValidColor(markerColor):
                markerColor = 'black'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                                    lineWidth=0.1, lineColor=markerColor,
                                    fillColor=markerColor,
                                    name=self.name + '.markerSlider',
                                    opacity=0.7, autoLog=False)
        elif self.markerStyle == 'glow':
            if markerColor is None or not isValidColor(markerColor):
                markerColor = 'White'
            self.marker = PatchStim(win=self.win, units='norm',
                                    tex='sin', mask='gauss',
                                    color=markerColor, opacity=0.85,
                                    autoLog=False,
                                    name=self.name + '.markerGlow')
            self.markerBaseSize = self.baseSize * self.markerSize
            self.markerOffsetVert = .02
            self.markerExpansion = float(expansion) * 0.6
            if self.markerExpansion == 0:
                self.markerBaseSize *= self.markerSize * 0.7
                if self.markerSize > 1.2:
                    self.markerBaseSize *= .7
                self.marker.setSize(self.markerBaseSize/2.0, log=False)
        elif self.markerStyle == 'custom':
            if markerColor is None:
                if hasattr(marker, 'color'):
                    try:
                        # marker.color 0 causes problems elsewhere too
                        if not marker.color:
                            marker.color = 'DarkBlue'
                    except ValueError:  # testing truth value of list
                        marker.color = 'DarkBlue'
                elif hasattr(marker, 'fillColor'):
                    marker.color = marker.fillColor
                else:
                    marker.color = 'DarkBlue'
                markerColor = marker.color
            if not hasattr(marker, 'name') or not marker.name:
                marker.name = 'customMarker'
            self.marker = marker
        else:  # 'circle':
            if markerColor is None or not isValidColor(markerColor):
                markerColor = 'DarkRed'
            x, y = self.win.size
            windowRatio = y/x
            self.markerSizeVert = 3.2 * self.baseSize * self.size
            circleSize = [self.markerSizeVert *
                          windowRatio, self.markerSizeVert]
            self.markerOffsetVert = self.markerSizeVert/2.0
            self.marker = Circle(self.win, size=circleSize, units='norm',
                                 lineColor=markerColor, fillColor=markerColor,
                                 name=self.name + '.markerCir', autoLog=False)
            self.markerBaseSize = self.baseSize
        self.markerColor = markerColor
        self.markerYpos = self.offsetVert + self.markerOffsetVert
        # save initial state, restore on reset
        self.markerOrig = copy.copy(self.marker)

    def _initTextElements(self, win, scale, textColor,
                          textFont, textSize, showValue, tickMarks):
        """creates TextStim for self.scaleDescription and self.labels
        """
        # text appearance (size, color, font, visibility):
        self.showValue = bool(showValue)  # hide if False
        self.textColor = textColor  # rgb
        self.textFont = textFont
        self.textSize = 0.2 * textSize * self.size
        self.textSizeSmall = self.textSize * 0.6

        # set the description text if not already set by user:
        if scale == '<default>':
            if self.choices:
                scale = ''
            else:
                msg = u' = not at all . . . extremely = '
                scale = str(self.low) + msg + str(self.high)

        # create the TextStim:
        self.scaleDescription = TextStim(
            win=self.win, height=self.textSizeSmall,
            pos=[self.offsetHoriz, 0.22 * self.size + self.offsetVert],
            color=self.textColor, wrapWidth=2 * self.hStretchTotal,
            font=textFont, autoLog=False)
        self.scaleDescription.font = textFont
        self.labels = []
        if self.labelTexts:
            if self.markerStyle == 'hover':
                vertPosTmp = self.offsetVert  # on the line = clickable labels
            else:
                vertPosTmp = -2 * self.textSizeSmall * self.size + self.offsetVert
            for i, label in enumerate(self.labelTexts):
                # need all labels for tick position, i
                if label:  # skip '' placeholders, no need to create them
                    txtStim = TextStim(
                        win=self.win, text=str(label), font=textFont,
                        pos=[self.tickPositions[i // self.autoRescaleFactor],
                             vertPosTmp],
                        height=self.textSizeSmall, color=self.textColor,
                        autoLog=False)
                    self.labels.append(txtStim)
        self.origScaleDescription = scale
        self.setDescription(scale)  # do last

    def setDescription(self, scale=None, log=True):
        """Method to set the brief description (scale).
        Useful when using the same RatingScale object to rate several
        dimensions. `setDescription(None)` will reset the description
        to its initial state. Set to a space character (' ') to make
        the description invisible.
        """
        if scale is None:
            scale = self.origScaleDescription
        self.scaleDescription.setText(scale)
        self.showScale = bool(scale)  # not in [None, False, '']
        if log and self.autoLog:
            logging.exp('RatingScale %s: setDescription="%s"' %
                        (self.name, self.scaleDescription.text))

    def _initAcceptBox(self, showAccept, acceptPreText, acceptText,
                       acceptSize, markerColor,
                       textSizeSmall, textSize, textFont):
        """creates a ShapeStim for self.acceptBox (mouse-click-able
        'accept'  button) and a TextStim for self.accept (container for
        the text shown inside the box)
        """
        if not showAccept:  # no point creating things that won't be used
            return

        self.acceptLineColor = [-.2, -.2, -.2]
        self.acceptFillColor = [.2, .2, .2]

        if self.labelTexts:
            boxVert = [0.3, 0.47]
        else:
            boxVert = [0.2, 0.37]

        # define self.acceptBox:
        sizeFactor = self.size * textSize
        leftRightAdjust = 0.04 + 0.2 * max(0.1, acceptSize) * sizeFactor
        acceptBoxtop = self.offsetVert - boxVert[0] * sizeFactor
        self.acceptBoxtop = acceptBoxtop
        acceptBoxbot = self.offsetVert - boxVert[1] * sizeFactor
        self.acceptBoxbot = acceptBoxbot
        acceptBoxleft = self.offsetHoriz - leftRightAdjust
        self.acceptBoxleft = acceptBoxleft
        acceptBoxright = self.offsetHoriz + leftRightAdjust
        self.acceptBoxright = acceptBoxright

        # define a rectangle with rounded corners; for square corners, set
        # delta2 to 0
        delta = 0.025 * self.size
        delta2 = delta/7
        acceptBoxVertices = [
            [acceptBoxleft, acceptBoxtop - delta],
            [acceptBoxleft + delta2, acceptBoxtop - 3 * delta2],
            [acceptBoxleft + 3 * delta2, acceptBoxtop - delta2],
            [acceptBoxleft + delta, acceptBoxtop],
            [acceptBoxright - delta, acceptBoxtop],
            [acceptBoxright - 3 * delta2, acceptBoxtop - delta2],
            [acceptBoxright - delta2, acceptBoxtop - 3 * delta2],
            [acceptBoxright, acceptBoxtop - delta],
            [acceptBoxright, acceptBoxbot + delta],
            [acceptBoxright - delta2, acceptBoxbot + 3 * delta2],
            [acceptBoxright - 3 * delta2, acceptBoxbot + delta2],
            [acceptBoxright - delta, acceptBoxbot],
            [acceptBoxleft + delta, acceptBoxbot],
            [acceptBoxleft + 3 * delta2, acceptBoxbot + delta2],
            [acceptBoxleft + delta2, acceptBoxbot + 3 * delta2],
            [acceptBoxleft, acceptBoxbot + delta]]
        # interpolation looks bad on linux, as of Aug 2010
        interpolate = bool(not sys.platform.startswith('linux'))
        self.acceptBox = ShapeStim(
            win=self.win, vertices=acceptBoxVertices,
            fillColor=self.acceptFillColor, lineColor=self.acceptLineColor,
            interpolate=interpolate, autoLog=False)

        # text to display inside accept button before a marker is placed:
        if self.low > 0 and self.high < 10 and not self.mouseOnly:
            self.keyClick = 'key, click'
        else:
            self.keyClick = 'click line'
        if acceptPreText != 'key, click':  # non-default
            self.keyClick = str(acceptPreText)
        self.acceptText = str(acceptText)

        # create the TextStim:
        self.accept = TextStim(
            win=self.win, text=self.keyClick, font=self.textFont,
            pos=[self.offsetHoriz, (acceptBoxtop + acceptBoxbot)/2.0],
            italic=True, height=textSizeSmall, color=self.textColor,
            autoLog=False)
        self.accept.font = textFont

        self.acceptTextColor = markerColor
        if markerColor in ['White']:
            self.acceptTextColor = 'Black'

    def _getMarkerFromPos(self, mouseX):
        """Convert mouseX into units of tick marks, 0 .. high-low.
        Will be fractional if precision > 1
        """
        value = min(max(mouseX, self.lineLeftEnd), self.lineRightEnd)
        # map mouseX==0 -> mid-point of tick scale:
        _tickStretch = self.tickMarks/self.hStretchTotal
        adjValue = value - self.offsetHoriz
        markerPos = adjValue * _tickStretch + self.tickMarks/2.0
        # We need float value in getRating(), but round() returns
        # numpy.float64 if argument is numpy.float64 in Python3.
        # So we have to convert return value of round() to float.
        rounded = float(round(markerPos * self.scaledPrecision))
        return rounded/self.scaledPrecision

    def setMouseFromMarker(self,mouse):
        """Position a mouse to the current marker position on the screen. Convenient when the marker position is being manually initialized by the experimenter and the scale is designed to be used with a mouse dynamically.
        """
        markerPos = self.markerPlacedAt
        #rounded = current_pos * self.scaledPrecision
        _tickStretch = self.tickMarks/self.hStretchTotal
        adjValue = (markerPos - self.tickMarks/2.0) / _tickStretch
        value = adjValue + self.offsetHoriz
        return mouse.setPos(newPos=[value,self.pos[-1]])

    def _getMarkerFromTick(self, tick):
        """Convert a requested tick value into a position on internal scale.
        Accounts for non-zero low end, autoRescale, and precision.
        """
        # ensure its on the line:
        value = max(min(self.high, tick), self.low)
        # set requested precision:
        value = round(value * self.scaledPrecision)//self.scaledPrecision
        return (value - self.low) * self.autoRescaleFactor

    def setMarkerPos(self, tick):
        """Method to allow the experimenter to set the marker's position
        on the scale (in units of tick marks). This method can also set
        the index within a list of choices (which start at 0).
        No range checking is done.
        Assuming you have defined rs = RatingScale(...), you can specify
        a tick position directly::
            rs.setMarkerPos(2)
        or do range checking, precision management, and auto-rescaling::
            rs.setMarkerPos(rs._getMarkerFromTick(2))
        To work from a screen coordinate, such as the X position of a
        mouse click::
            rs.setMarkerPos(rs._getMarkerFromPos(mouseX))
        """
        self.markerPlacedAt = tick
        self.markerPlaced = True  # only needed first time

    def setFlipVert(self, newVal=True, log=True):
        """Sets current vertical mirroring to ``newVal``.
        """
        if self.flipVert != newVal:
            self.flipVert = not self.flipVert
            self.markerYpos *= -1
            groupFlipVert([self.nearLine, self.marker] +
                          self.visualDisplayElements)
        logAttrib(self, log, 'flipVert')

    # autoDraw and setAutoDraw are inherited from basevisual.MinimalStim

    def acceptResponse(self, triggeringAction, log=True):
        """Commit and optionally log a response and the action.
        """
        self.noResponse = False
        self.history.append((self.getRating(), self.getRT()))
        if log and self.autoLog:
            vals = (self.name, triggeringAction, str(self.getRating()))
            logging.data('RatingScale %s: (%s) rating=%s' % vals)

    def draw(self, log=True):
        """Update the visual display, check for response (key, mouse, skip).
        Sets response flags: `self.noResponse`, `self.timedOut`.
        `draw()` only draws the rating scale, not the item to be rated.
        """
        self.win.setUnits(u'norm', log=False)  # get restored
        if self.firstDraw:
            self.firstDraw = False
            self.clock.reset()
            self.status = STARTED
            if self.markerStart:
                # has been converted in index if given as str
                if (self.markerStart % 1 or self.markerStart < 0 or
                        self.markerStart > self.high or
                        self.choices is False):
                    first = self.markerStart
                else:
                    # back to str for history
                    first = self.choices[int(self.markerStart)]
            else:
                first = None
            self.history = [(first, 0.0)]  # this will grow
            self.beyondMinTime = False  # has minTime elapsed?
            self.timedOut = False

        if not self.beyondMinTime:
            self.beyondMinTime = bool(self.clock.getTime() > self.minTime)
        # beyond maxTime = timed out? max < min means never allow time-out
        if (self.allowTimeOut and
                not self.timedOut and
                self.maxTime < self.clock.getTime()):
            # only do this stuff once
            self.timedOut = True
            self.acceptResponse('timed out: %.3fs' % self.maxTime, log=log)

        # 'disappear' == draw nothing if subj is done:
        if self.noResponse == False and self.disappear:
            self.win.setUnits(self.savedWinUnits, log=False)
            return

        # draw everything except the marker:
        for visualElement in self.visualDisplayElements:
            visualElement.draw()

        # draw a fixed marker if the scale is being drawn after a response:
        if self.noResponse == False:
            # fix the marker position on the line
            if not self.markerPosFixed:
                try:
                    self.marker.setFillColor('DarkGray', log=False)
                except AttributeError:
                    try:
                        self.marker.setColor('DarkGray', log=False)
                    except Exception:
                        pass
                # drop it onto the line
                self.marker.setPos((0, -.012), ('+', '-')[self.flipVert],
                                   log=False)
                self.markerPosFixed = True  # flag to park it there
            self.marker.draw()
            if self.showAccept:
                self.acceptBox.draw()  # hides the text
            self.win.setUnits(self.savedWinUnits, log=False)
            return  # makes the marker unresponsive

        if self.noMouse:
            mouseNearLine = False
        else:
            mouseX, mouseY = self.myMouse.getPos()  # norm units
            mouseNearLine = pointInPolygon(mouseX, mouseY, self.nearLine)

        # draw a dynamic marker:
        if self.markerPlaced or self.singleClick:
            # update position:
            if self.singleClick and mouseNearLine:
                # handle bounds
                current_pos = self._getMarkerFromPos(mouseX)
                if current_pos < self.bounds[0]:
                    current_pos = self.bounds[0]
                elif current_pos > self.bounds[1]:
                    current_pos = self.bounds[1]
                self.setMarkerPos(current_pos)
            proportion = self.markerPlacedAt/self.tickMarks
            # expansion for 'glow', based on proportion of total line
            if self.markerStyle == 'glow' and self.markerExpansion != 0:
                if self.markerExpansion > 0:
                    newSize = 0.1 * self.markerExpansion * proportion
                    newOpacity = 0.2 + proportion
                else:  # self.markerExpansion < 0:
                    newSize = - 0.1 * self.markerExpansion * (1 - proportion)
                    newOpacity = 1.2 - proportion
                self.marker.setSize(self.markerBaseSize + newSize, log=False)
                self.marker.setOpacity(min(1, max(0, newOpacity)), log=False)
            # set the marker's screen position based on tick (==
            # markerPlacedAt)
            if self.markerPlacedAt is not False:
                x = self.offsetHoriz + self.hStretchTotal * (-0.5 + proportion)
                # handle bounds
                # if x < self.bounds[0]:
                #     x = self.bounds[0]
                # elif x > self.bounds[1]:
                #     x = self.bounds[1]
                self.marker.setPos((x, self.markerYpos), log=False)
                self.marker.draw()
            if self.showAccept and self.markerPlacedBySubject:
                self.frame = (self.frame + 1) % 100
                self.acceptBox.setFillColor(
                    self.pulseColor[self.frame], log=False)
                self.acceptBox.setLineColor(
                    self.pulseColor[self.frame], log=False)
                self.accept.setColor(self.acceptTextColor, log=False)
                if self.showValue and self.markerPlacedAt is not False:
                    if self.choices:
                        val = str(self.choices[int(self.markerPlacedAt)])
                    elif self.precision == 60:
                        valTmp = self.markerPlacedAt + self.low
                        minutes = int(valTmp)  # also works for hours:minutes
                        seconds = int(60. * (valTmp - minutes))
                        val = self.fmtStr % (minutes, str(seconds).zfill(2))
                    else:
                        valTmp = self.markerPlacedAt + self.low
                        val = self.fmtStr % (valTmp * self.autoRescaleFactor)
                    self.accept.setText(val)
                elif self.markerPlacedAt is not False:
                    self.accept.setText(self.acceptText)

        # handle key responses:
        if not self.mouseOnly:
            for key in event.getKeys(self.allKeys):
                if key in self.skipKeys:
                    self.markerPlacedAt = None
                    self.noResponse = False
                    self.history.append((None, self.getRT()))
                elif key in self.respKeys and self.enableRespKeys:
                    # place the marker at the corresponding tick (from key)
                    self.markerPlaced = True
                    self.markerPlacedBySubject = True
                    resp = self.tickFromKeyPress[key]
                    self.markerPlacedAt = self._getMarkerFromTick(resp)
                    proportion = self.markerPlacedAt/self.tickMarks
                    self.marker.setPos(
                        [self.size * (-0.5 + proportion), 0], log=False)
                if self.markerPlaced and self.beyondMinTime:
                    # placed by experimenter (as markerStart) or by subject
                    if (self.markerPlacedBySubject or
                            self.markerStart is None or
                            not self.markerStart % self.keyIncrement):
                        # inefficient to do every frame...
                        leftIncr = rightIncr = self.keyIncrement
                    else:
                        # markerStart is fractional; arrow keys move to next
                        # location
                        leftIncr = self.markerStart % self.keyIncrement
                        rightIncr = self.keyIncrement - leftIncr
                    if key in self.leftKeys:
                        self.markerPlacedAt = self.markerPlacedAt - leftIncr
                        self.markerPlacedBySubject = True
                    elif key in self.rightKeys:
                        self.markerPlacedAt = self.markerPlacedAt + rightIncr
                        self.markerPlacedBySubject = True
                    elif key in self.acceptKeys:
                        self.acceptResponse('key response', log=log)
                    # off the end?
                    self.markerPlacedAt = max(0, self.markerPlacedAt)
                    self.markerPlacedAt = min(
                        self.tickMarks, self.markerPlacedAt)
                    # bounds
                    current_marker = int(self.markerPlacedAt)
                    if self.choices[current_marker] < self.bounds[0]:
                        self.markerPlacedAt = (numpy.where(self.choices > self.bounds[0])[0]).min() (numpy.abs(self.choices-self.bounds[0])).argmin()
                    elif self.choices[current_marker] > self.bounds[1]:
                        self.markerPlacedAt = (numpy.where(self.choices < self.bounds[1])[0]).max()
                    self.markerPlacedAt = float(self.markerPlacedAt)

                if (self.markerPlacedBySubject and self.singleClick
                        and self.beyondMinTime):
                    self.marker.setPos((0, self.offsetVert), '+', log=False)
                    self.acceptResponse('key single-click', log=log)

        # handle mouse left-click:
        if not self.noMouse and self.myMouse.getPressed()[0]:
            # mouseX, mouseY = self.myMouse.getPos() # done above
            # if click near the line, place the marker there:
            if mouseNearLine:
                self.markerPlaced = True
                self.markerPlacedBySubject = True
                # handle bounds
                current_pos = self._getMarkerFromPos(mouseX)
                if current_pos < self.bounds[0]:
                    current_pos = self.bounds[0]
                elif current_pos > self.bounds[1]:
                    current_pos = self.bounds[1]
                self.markerPlacedAt = current_pos
                if self.singleClick and self.beyondMinTime:
                    self.acceptResponse('mouse single-click', log=log)
            # if click in accept box and conditions are met, accept the
            # response:
            elif (self.showAccept and
                    self.markerPlaced and
                    self.beyondMinTime and
                    self.acceptBox.contains(mouseX, mouseY)):
                self.acceptResponse('mouse response', log=log)

        if self.markerStyle == 'hover' and self.markerPlaced:
            # 'hover' --> noMouse = False during init
            if (mouseNearLine or
                    self.markerPlacedAt != self.markerPlacedAtLast):
                if hasattr(self, 'targetWord'):
                    self.targetWord.setColor(self.textColor, log=False)
                    # self.targetWord.setHeight(self.textSizeSmall, log=False)
                    # # avoid TextStim memory leak
                self.targetWord = self.labels[int(self.markerPlacedAt)]
                self.targetWord.setColor(self.markerColor, log=False)
                # skip size change to reduce mem leakage from pyglet text
                # self.targetWord.setHeight(1.05*self.textSizeSmall,log=False)
                self.markerPlacedAtLast = self.markerPlacedAt
            elif not mouseNearLine and self.wasNearLine:
                self.targetWord.setColor(self.textColor, log=False)
                # self.targetWord.setHeight(self.textSizeSmall, log=False)
            self.wasNearLine = mouseNearLine

        # decision time = sec from first .draw() to when first 'accept' value:
        if not self.noResponse and self.decisionTime == 0:
            self.decisionTime = self.clock.getTime()
            if log and self.autoLog:
                logging.data('RatingScale %s: rating RT=%.3f' %
                             (self.name, self.decisionTime))
                logging.data('RatingScale %s: history=%s' %
                             (self.name, self.getHistory()))
            # minimum time is enforced during key and mouse handling
            self.status = FINISHED
            if self.showAccept:
                self.acceptBox.setFillColor(self.acceptFillColor, log=False)
                self.acceptBox.setLineColor(self.acceptLineColor, log=False)
        else:
            # build up response history if no decision or skip yet:
            tmpRating = self.getRating()
            if (self.history[-1][0] != tmpRating and
                    self.markerPlacedBySubject):
                self.history.append((tmpRating, self.getRT()))  # tuple

        # restore user's units:
        self.win.setUnits(self.savedWinUnits, log=False)

    def reset(self, log=True):
        """Restores the rating-scale to its post-creation state.
        The history is cleared, and the status is set to NOT_STARTED. Does
        not restore the scale text description (such reset is needed between
        items when rating multiple items)
        """
        # only resets things that are likely to have changed when the
        # ratingScale instance is used by a subject
        self.noResponse = True
        # restore in case it turned gray, etc
        self.marker = copy.copy(self.markerOrig)
        # placed by subject or markerStart: show on screen
        self.markerPlaced = False
        # placed by subject is actionable: show value, singleClick
        self.markerPlacedBySubject = False
        self.markerPlacedAt = False
        # NB markerStart could be 0; during __init__, its forced to be numeric
        # and valid, or None (not boolean)
        if self.markerStart != None:
            self.markerPlaced = True
            # __init__ assures this is valid:
            self.markerPlacedAt = self.markerStart - self.low
        self.markerPlacedAtLast = -1  # unplaced
        self.wasNearLine = False
        self.firstDraw = True  # -> self.clock.reset() at start of draw()
        self.decisionTime = 0
        self.markerPosFixed = False
        self.frame = 0  # a counter used only to 'pulse' the 'accept' box

        if self.showAccept:
            self.acceptBox.setFillColor(self.acceptFillColor, log=False)
            self.acceptBox.setLineColor(self.acceptLineColor, log=False)
            self.accept.setColor('#444444', log=False)  # greyed out
            self.accept.setText(self.keyClick, log=False)
        if log and self.autoLog:
            logging.exp('RatingScale %s: reset()' % self.name)
        self.status = NOT_STARTED
        self.history = None

    def getRating(self):
        """Returns the final, accepted rating, or the current value.
        The rating is None if the subject skipped this item, took longer
        than ``maxTime``, or no rating is
        available yet. Returns the currently indicated rating even if it has
        not been accepted yet (and so might change until accept is pressed).
        The first rating in the list will have the value of
        markerStart (whether None, a numeric value, or a choice value).
        """
        if self.noResponse and self.status == FINISHED:
            return None
        # Turning this off because we don't care about skips and there
        # are hard-to-debug numpy int vs int type errors
        # if not type(self.markerPlacedAt) in [float, int]:
        #     return None  # eg, if skipped a response

        # set type for the response, based on what was wanted
        val = self.markerPlacedAt * self.autoRescaleFactor
        if self.precision == 1:
            response = int(val) + self.low
        else:
            response = float(val) + self.low
        if self.choices:
            try:
                response = self.choices[response]
            except Exception:
                pass
                # == we have a numeric fractional choice from markerStart and
                # want to save the numeric value as first item in the history
        return response

    def getRT(self):
        """Returns the seconds taken to make the rating (or to indicate skip).
        Returns None if no rating available, or maxTime if the response
        timed out. Returns the time elapsed so far if no rating has been
        accepted yet (e.g., for continuous usage).
        """
        if self.status != FINISHED:
            return round(self.clock.getTime(), 3)
        if self.noResponse:
            if self.timedOut:
                return round(self.maxTime, 3)
            return None
        return round(self.decisionTime, 3)

    def getHistory(self):
        """Return a list of the subject's history as (rating, time) tuples.
        The history can be retrieved at any time, allowing for continuous
        ratings to be obtained in real-time. Both numerical and categorical
        choices are stored automatically in the history.
        """
        return self.history

    def draw_only(self):
        """Like .draw(), but **only** draws the scale to the screen without collecting a rating. Useful for presenting the scale as another stimulus type rather than a data input tool.
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
