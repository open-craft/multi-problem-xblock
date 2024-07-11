#
"""Multi Problem XBlock"""

# Imports ###########################################################

import logging
from copy import copy

from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.fields import Float, Integer, Scope, String

try:
    from xblock.utils.resources import ResourceLoader
except ModuleNotFoundError:  # For backward compatibility with releases older than Quince.
    from xblockutils.resources import ResourceLoader

from .compat import getLibraryContentBlock, getShowAnswerOptions, getShowCorrectnessOptions, getStudentView
from .utils import _

# Globals ###########################################################

loader = ResourceLoader(__name__)
logger = logging.getLogger(__name__)
LibraryContentBlock = getLibraryContentBlock()
SHOWANSWER = getShowAnswerOptions()
ShowCorrectness = getShowCorrectnessOptions()
STUDENT_VIEW = getStudentView()


# Classes ###########################################################


class DISPLAYFEEDBACK:
    """
    Constants for when to show feedback
    """

    IMMEDIATELY = 'immediately'
    END_OF_TEST = 'end_of_test'
    NEVER = 'never'


class SCORE_DISPLAY_FORMAT:
    """
    Constants for how score is displayed
    """

    PERCENTAGE = 'percentage'
    X_OUT_OF_Y = 'x_out_of_y'


@XBlock.wants('library_tools')
@XBlock.wants('studio_user_permissions')  # Only available in CMS.
@XBlock.wants('user')
@XBlock.needs('bookmarks')
class MultiProblemBlock(LibraryContentBlock):
    # Override LibraryContentBlock resources_dir
    resources_dir = ''
    display_name = String(
        display_name=_('Display Name'),
        help=_('The display name for this component.'),
        default='Multi Problem Block',
        scope=Scope.settings,
    )

    showanswer = String(
        display_name=_('Show Answer'),
        help=_(
            'Defines when to show the answer to the problem. '
            'Acts as default value for showanswer field in each problem under this block'
        ),
        scope=Scope.settings,
        default=SHOWANSWER.FINISHED,
        values=[
            {'display_name': _('Always'), 'value': SHOWANSWER.ALWAYS},
            {'display_name': _('Answered'), 'value': SHOWANSWER.ANSWERED},
            {'display_name': _('Attempted or Past Due'), 'value': SHOWANSWER.ATTEMPTED},
            {'display_name': _('Closed'), 'value': SHOWANSWER.CLOSED},
            {'display_name': _('Finished'), 'value': SHOWANSWER.FINISHED},
            {'display_name': _('Correct or Past Due'), 'value': SHOWANSWER.CORRECT_OR_PAST_DUE},
            {'display_name': _('Past Due'), 'value': SHOWANSWER.PAST_DUE},
            {'display_name': _('Never'), 'value': SHOWANSWER.NEVER},
            {'display_name': _('After Some Number of Attempts'), 'value': SHOWANSWER.AFTER_SOME_NUMBER_OF_ATTEMPTS},
            {'display_name': _('After All Attempts'), 'value': SHOWANSWER.AFTER_ALL_ATTEMPTS},
            {'display_name': _('After All Attempts or Correct'), 'value': SHOWANSWER.AFTER_ALL_ATTEMPTS_OR_CORRECT},
            {'display_name': _('Attempted'), 'value': SHOWANSWER.ATTEMPTED_NO_PAST_DUE},
        ],
    )

    weight = Float(
        display_name=_('Problem Weight'),
        help=_(
            'Defines the number of points each problem is worth. '
            'If the value is not set, each response field in each problem is worth one point.'
        ),
        values={'min': 0, 'step': 0.1},
        scope=Scope.settings,
    )

    display_feedback = String(
        display_name=_('Display feedback'),
        help=_('Defines when to show feedback i.e. correctness in the problem slides.'),
        scope=Scope.settings,
        default=DISPLAYFEEDBACK.IMMEDIATELY,
        values=[
            {'display_name': _('Immediately'), 'value': DISPLAYFEEDBACK.IMMEDIATELY},
            {'display_name': _('End of test'), 'value': DISPLAYFEEDBACK.END_OF_TEST},
            {'display_name': _('Never'), 'value': DISPLAYFEEDBACK.NEVER},
        ],
    )

    score_display_format = String(
        display_name=_('Score display format'),
        help=_('Defines how score will be displayed to students.'),
        scope=Scope.settings,
        default=SCORE_DISPLAY_FORMAT.X_OUT_OF_Y,
        values=[
            {'display_name': _('Percentage'), 'value': SCORE_DISPLAY_FORMAT.PERCENTAGE},
            {'display_name': _('X out of Y'), 'value': SCORE_DISPLAY_FORMAT.X_OUT_OF_Y},
        ],
    )

    cut_off_score = Float(
        display_name=_('Cut-off score'),
        help=_('Defines min score for successful completion of the test'),
        scope=Scope.settings,
        values={'min': 0, 'step': 0.1, 'max': 1},
    )

    current_slide = Integer(help=_('Stores current slide/problem number for a user'), scope=Scope.user_state, default=0)

    @property
    def non_editable_metadata_fields(self):
        """
        Set current_slide as non editable field
        """
        non_editable_fields = super().non_editable_metadata_fields
        non_editable_fields.extend([MultiProblemBlock.current_slide])
        return non_editable_fields

    def _process_display_feedback(self, child):
        """
        Set child correctness based on parent display_feedback
        """
        if not hasattr(child, 'show_correctness'):
            return
        # If display_feedback is IMMEDIATELY, show answers immediately after submission as well as at the end
        # In other cases i.e., END_OF_TEST & NEVER, set show_correctness to never
        # and display correctness via force argument in the last slide if display_feedback set to END_OF_TEST
        child.show_correctness = (
            ShowCorrectness.ALWAYS if self.display_feedback == DISPLAYFEEDBACK.IMMEDIATELY else ShowCorrectness.NEVER
        )

    def post_editor_saved(self, user, old_metadata, old_content):
        """
        Update child field values based on parent block.
        child.showanswer <- self.showanswer
        child.showanswer <- self.showanswer
        child.show_correctness <- ALWAYS if display_feedback == IMMEDIATELY else NEVER
        """
        super().post_editor_saved(user, old_metadata, old_content)
        for child in self.get_children():
            if hasattr(child, 'showanswer'):
                child.showanswer = self.showanswer
            if hasattr(child, 'weight'):
                child.weight = self.weight
            self._process_display_feedback(child)

    @XBlock.handler
    def handle_slide_change(self, request, suffix=None):
        """
        Handle slide change request, triggered when user clicks on next or previous button.
        """
        try:
            data = request.json
        except ValueError:
            return Response('Invalid request body', status=400)

        self.current_slide = data.get('current_slide')
        return Response()

    def student_view(self, context):  # lint-amnesty, pylint: disable=missing-function-docstring
        fragment = Fragment()
        contents = []
        child_context = {} if not context else copy(context)
        jump_to_id = context.get('jumpToId')
        bookmarks_service = self.runtime.service(self, 'bookmarks')

        if 'username' not in child_context:
            user_service = self.runtime.service(self, 'user')
            child_context['username'] = user_service.get_current_user().opt_attrs.get(
                'edx-platform.username'
            )

        for index, child in enumerate(self._get_selected_child_blocks()):
            child_id = str(child.location)
            if child is None:
                # https://github.com/openedx/edx-platform/blob/448acc95f6296c72097102441adc4e1f79a7444f/xmodule/library_content_block.py#L391-L396
                logger.error('Skipping display for child block that is None')
                continue
            if jump_to_id == child_id:
                self.current_slide = index

            rendered_child = child.render(STUDENT_VIEW, child_context)
            fragment.add_fragment_resources(rendered_child)
            contents.append(
                {
                    'id': child_id,
                    'content': rendered_child.content,
                    'bookmark_id': "{},{}".format(child_context['username'], child_id),
                    'is_bookmarked': bookmarks_service.is_bookmarked(usage_key=child.location),
                }
            )

        fragment.add_content(
            loader.render_django_template(
                '/templates/html/multi_problem_xblock.html',
                {
                    'items': contents,
                    'self': self,
                    'watched_completable_blocks': set(),
                    'completion_delay_ms': None,
                    'reset_button': self.allow_resetting_children,
                },
            )
        )
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/multi_problem_xblock.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/multi_problem_xblock.js'))
        fragment.initialize_js('MultiProblemBlock')
        fragment.json_init_args = {'current_slide': self.current_slide}
        return fragment
