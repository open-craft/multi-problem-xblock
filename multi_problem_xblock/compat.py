"""
Compatibility layer to import LibraryContentBlock from edx-platform
"""

import logging

from xblock.core import XBlock

log = logging.getLogger(__name__)


def getLibraryContentBlock():
    """Get LibraryContentBlock from edx-platform if possible"""
    try:
        from xmodule.library_content_block import LibraryContentBlock  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError:
        log.warning('LibraryContentBlock not found, using empty object')
        LibraryContentBlock = XBlock
    return LibraryContentBlock


class L_SHOWANSWER:
    """
    Local copy of SHOWANSWER from xmodule/capa_block.py in edx-platform
    """

    ALWAYS = 'always'
    ANSWERED = 'answered'
    ATTEMPTED = 'attempted'
    CLOSED = 'closed'
    FINISHED = 'finished'
    CORRECT_OR_PAST_DUE = 'correct_or_past_due'
    PAST_DUE = 'past_due'
    NEVER = 'never'
    AFTER_SOME_NUMBER_OF_ATTEMPTS = 'after_attempts'
    AFTER_ALL_ATTEMPTS = 'after_all_attempts'
    AFTER_ALL_ATTEMPTS_OR_CORRECT = 'after_all_attempts_or_correct'
    ATTEMPTED_NO_PAST_DUE = 'attempted_no_past_due'


class L_ShowCorrectness:
    """
    Local copy of ShowCorrectness from xmodule/graders.py in edx-platform
    """

    # Constants used to indicate when to show correctness
    ALWAYS = 'always'
    PAST_DUE = 'past_due'
    NEVER = 'never'


def getShowAnswerOptions():
    """Get SHOWANSWER constant from xmodule/capa_block.py"""
    try:
        from xmodule.capa_block import SHOWANSWER  # pylint: disable=import-outside-toplevel

        return SHOWANSWER
    except ModuleNotFoundError:
        log.warning('SHOWANSWER not found, using local copy')
        return L_SHOWANSWER


def getShowCorrectnessOptions():
    """Get ShowCorrectness constant from xmodule/graders.py"""
    try:
        from xmodule.graders import ShowCorrectness  # pylint: disable=import-outside-toplevel

        return ShowCorrectness
    except ModuleNotFoundError:
        log.warning('ShowCorrectness not found, using local copy')
        return L_ShowCorrectness


def getStudentView():
    """Get STUDENT_VIEW constant from xmodule/x_module.py"""
    try:
        from xmodule.x_module import STUDENT_VIEW  # pylint: disable=import-outside-toplevel

        return STUDENT_VIEW
    except ModuleNotFoundError:
        log.warning('STUDENT_VIEW not found, using raw string')
        return 'student_view'
