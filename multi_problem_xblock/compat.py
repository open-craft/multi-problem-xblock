"""
Compatibility layer to import LibraryContentBlock from edx-platform
"""

import logging

log = logging.getLogger(__name__)


def getLibraryContentBlock():
    try:
        from xmodule.library_content_block import LibraryContentBlock
    except ModuleNotFoundError:
        log.warning('LibraryContentBlock not found, using empty object')
        LibraryContentBlock = object
    return LibraryContentBlock


class SHOWANSWER:
    """
    Local copy of SHOWANSWER from xmodule/capa_block.py in edx-platform
    """
    ALWAYS = "always"
    ANSWERED = "answered"
    ATTEMPTED = "attempted"
    CLOSED = "closed"
    FINISHED = "finished"
    CORRECT_OR_PAST_DUE = "correct_or_past_due"
    PAST_DUE = "past_due"
    NEVER = "never"
    AFTER_SOME_NUMBER_OF_ATTEMPTS = "after_attempts"
    AFTER_ALL_ATTEMPTS = "after_all_attempts"
    AFTER_ALL_ATTEMPTS_OR_CORRECT = "after_all_attempts_or_correct"
    ATTEMPTED_NO_PAST_DUE = "attempted_no_past_due"


def getShowAnswerOptions():
    """Get SHOWANSWER constant from xmodule/capa_block.py"""
    try:
        from xmodule.capa_block import SHOWANSWER
        return SHOWANSWER
    except ModuleNotFoundError:
        log.warning('SHOWANSWER not found, using local copy')
        return SHOWANSWER
