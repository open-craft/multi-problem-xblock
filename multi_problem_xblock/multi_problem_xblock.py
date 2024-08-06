"""Multi Problem XBlock"""

# Imports ###########################################################

import json
import logging
import math
from copy import copy

from lxml import etree
from lxml.etree import XMLSyntaxError
from web_fragments.fragment import Fragment
from webob import Response
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.fields import Boolean, Float, Integer, Scope, String

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


@XBlock.wants('library_tools', 'studio_user_permissions', 'user', 'completion', 'bookmarks')
class MultiProblemBlock(LibraryContentBlock):
    """
    Multi problem xblock using LibraryContentBlock as base.
    """

    # Override LibraryContentBlock resources_dir
    resources_dir = ''

    has_custom_completion = True
    completion_mode = XBlockCompletionMode.COMPLETABLE

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
            'Acts as default value for showanswer field in each problem under this block. '
            'NOTE: Do not change this field and `Library` field together, child show answer field '
            'will not be updated.'
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

    display_feedback = String(
        display_name=_('Display feedback'),
        help=_(
            'Defines when to show feedback i.e. correctness in the problem slides. '
            'NOTE: Do not change this field and `Library` field together, child show correctness field '
            'will not be updated.'
        ),
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
        default=0,
    )

    next_page_on_submit = Boolean(
        display_name=_('Next page on submit'),
        help=_(
            'If true and display feedback is set to End of test or Never,'
            ' next problem will be displayed automatically on submit.'
        ),
        scope=Scope.settings,
        default=False,
    )

    current_slide = Integer(help=_('Stores current slide/problem number for a user'), scope=Scope.user_state, default=0)

    @property
    def non_editable_metadata_fields(self):
        """
        Set current_slide as non editable field
        """
        non_editable_fields = []
        if hasattr(super(), 'non_editable_metadata_fields'):
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
        # HACK: For some reason, child.show_correctness is not saved if self.show_correctness is not updated.
        self.show_correctness = child.show_correctness = (  # pylint: disable=attribute-defined-outside-init
            ShowCorrectness.ALWAYS if self.display_feedback == DISPLAYFEEDBACK.IMMEDIATELY else ShowCorrectness.NEVER
        )

    def editor_saved(self, user, old_metadata, old_content):
        """
        Update child field values based on parent block.
        child.showanswer <- self.showanswer
        child.weight <- self.weight
        child.show_correctness <- ALWAYS if display_feedback == IMMEDIATELY else NEVER
        """
        if hasattr(super(), 'editor_saved'):
            super().editor_saved(user, old_metadata, old_content)
        for child in self.get_children():
            if hasattr(child, 'showanswer'):
                child.showanswer = self.showanswer
            self._process_display_feedback(child)
            child.save()

    @XBlock.json_handler
    def handle_slide_change(self, data, suffix=None):
        """
        Handle slide change request, triggered when user clicks on next or previous button.
        """
        self.current_slide = data.get('current_slide')
        return Response()

    @staticmethod
    def _calculate_progress_percentage(completed_problems, total_problems):
        return int((completed_problems / (total_problems or 1)) * 100)

    def _children_iterator(self, filter_block_type=None):
        """
        Generator to yield child problem blocks.
        """
        # use selected_children method from LibraryContentBlock to get child xblocks.
        for index, (block_type, block_id) in enumerate(self.selected_children()):
            if filter_block_type and (block_type != filter_block_type):
                continue
            child = self.runtime.get_block(self.usage_key.course_key.make_usage_key(block_type, block_id))
            yield (index, block_type, child)

    def _get_problem_stats(self):
        """
        Get completed_problems and total_problems in the current test.
        """
        total_problems = 0
        completed_problems = 0
        for _index, _block_type, child in self._children_iterator(filter_block_type='problem'):
            if hasattr(child, 'is_submitted'):
                total_problems += 1
                if child.is_submitted():
                    completed_problems += 1
        return completed_problems, total_problems

    @XBlock.handler
    def get_overall_progress(self, _data, _suffix=None):
        """
        Fetch status of all child problem xblocks to get overall progress and updates completion percentage.
        """
        completed_problems, total_problems = self._get_problem_stats()
        progress = self._calculate_progress_percentage(completed_problems, total_problems)
        completion = progress / 100
        if completion == 1:
            _, student_score, total_possible_score = self._prepare_user_score()
            if student_score / total_possible_score < self.cut_off_score:
                # Reserve 10% if user score is less than self.cut_off_score
                completion = 0.9
        self.publish_completion(completion)
        return Response(json.dumps({'overall_progress': progress}))

    def _prepare_user_score(self, include_question_answers=False):
        """
        Calculate total user score and prepare list of question answers with user response.

        Args:
            include_question_answers (bool): Includes question and correct answers with user response.
        """
        question_answers = []
        student_score = 0
        total_possible_score = 0
        for _index, _block_type, child in self._children_iterator(filter_block_type='problem'):
            lcp = child.lcp
            correct_map = lcp.correct_map
            for answer_id, student_answer in lcp.student_answers.items():
                # Check is_correct before fetching score as lcp is initialized here
                is_correct = child.is_correct()
                score = child.score
                student_score += score.raw_earned
                total_possible_score += score.raw_possible
                if include_question_answers:
                    question_answers.append(
                        {
                            'question': lcp.find_question_label(answer_id),
                            'answer': lcp.find_answer_text(answer_id, current_answer=student_answer),
                            'correct_answer': lcp.find_correct_answer_text(answer_id),
                            'is_correct': is_correct,
                            'msg': correct_map.get_msg(answer_id),
                        }
                    )
        return question_answers, student_score, total_possible_score

    @XBlock.handler
    def get_test_scores(self, _data, _suffix):
        """
        Get test score slide content
        """
        if self.display_feedback == DISPLAYFEEDBACK.NEVER:
            return Response(_('Not allowed to see results'), 400)
        completed_problems, total_problems = self._get_problem_stats()
        if completed_problems != total_problems and total_problems > 0:
            return Response(_('All problems need to be completed before checking test results!'), status=400)
        question_answers, student_score, total_possible_score = self._prepare_user_score(include_question_answers=True)
        passed = False
        allow_back_button = True

        if self.score_display_format == SCORE_DISPLAY_FORMAT.X_OUT_OF_Y:
            score_display = f'{student_score}/{total_possible_score}'
            cut_off_score = f'{math.ceil(self.cut_off_score * total_possible_score)}/{total_possible_score}'
        else:
            score_display = f'{(student_score / total_possible_score):.0%}'
            cut_off_score = f'{self.cut_off_score:.0%}'

        if (student_score / total_possible_score) >= self.cut_off_score:
            self.publish_completion(1)
            passed = True

        if self.display_feedback != DISPLAYFEEDBACK.IMMEDIATELY:
            allow_back_button = False
            self.current_slide = -1

        template = loader.render_django_template(
            '/templates/html/multi_problem_xblock_test_scores.html',
            {
                'cut_off_score': cut_off_score if self.cut_off_score else '',
                'question_answers': question_answers,
                'score': score_display,
                'passed': passed,
                'allow_back_button': allow_back_button,
            },
        )
        return Response(template, content_type='text/html')

    @XBlock.handler
    def reset_selected_children(self, data, suffix=None):
        # reset current_slide field
        self.current_slide = 0
        return super().reset_selected_children(data, suffix)

    def student_view_context(self, context=None):
        """
        Student view data for templates and javascript initialization
        """
        fragment = Fragment()
        items = []
        child_context = {} if not context else copy(context)
        jump_to_id = child_context.get('jumpToId')
        bookmarks_service = self.runtime.service(self, 'bookmarks')
        total_problems = 0
        completed_problems = 0

        if 'username' not in child_context:
            user_service = self.runtime.service(self, 'user')
            child_context['username'] = user_service.get_current_user().opt_attrs.get('edx-platform.username')

        for index, block_type, child in self._children_iterator():
            child_id = str(child.usage_key)
            if child is None:
                # https://github.com/openedx/edx-platform/blob/448acc95f6296c72097102441adc4e1f79a7444f/xmodule/library_content_block.py#L391-L396
                logger.error('Skipping display for child block that is None')
                continue
            if jump_to_id == child_id:
                self.current_slide = index

            if block_type == 'problem' and hasattr(child, 'is_submitted'):
                # set current progress on first load
                total_problems += 1
                if child.is_submitted():
                    completed_problems += 1

            rendered_child = child.render(STUDENT_VIEW, child_context)
            fragment.add_fragment_resources(rendered_child)
            items.append(
                {
                    'id': child_id,
                    'content': rendered_child.content,
                    'bookmark_id': '{},{}'.format(child_context['username'], child_id),
                    'is_bookmarked': (
                        bookmarks_service.is_bookmarked(usage_key=child.usage_key) if bookmarks_service else False
                    ),
                }
            )

        next_page_on_submit = self.next_page_on_submit and self.display_feedback != DISPLAYFEEDBACK.IMMEDIATELY
        overall_progress = self._calculate_progress_percentage(completed_problems, total_problems)

        # Reset current_slide field if display_feedback is set to never after user completes all problems.
        if overall_progress == 100 and self.current_slide == -1 and self.display_feedback == DISPLAYFEEDBACK.NEVER:
            self.current_slide = 0

        template_context = {
            'items': items,
            'self': self,
            'watched_completable_blocks': set(),
            'completion_delay_ms': None,
            'reset_button': self.allow_resetting_children,
            'show_results': self.display_feedback != DISPLAYFEEDBACK.NEVER,
            'next_page_on_submit': next_page_on_submit,
            'overall_progress': overall_progress,
            'bookmarks_service_enabled': bookmarks_service is not None,
        }
        js_context = {
            'current_slide': self.current_slide,
            'next_page_on_submit': next_page_on_submit,
        }
        return fragment, template_context, js_context

    def student_view(self, context):
        """
        Student view
        """
        fragment, template_context, js_context = self.student_view_context(context)
        fragment.add_content(
            loader.render_django_template('/templates/html/multi_problem_xblock.html', template_context)
        )
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/multi_problem_xblock.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/multi_problem_xblock.js'))
        fragment.initialize_js('MultiProblemBlock', js_context)
        return fragment

    def publish_completion(self, progress: float):
        """
        Update block completion status.
        """
        completion_service = self.runtime.service(self, 'completion')
        if completion_service and completion_service.completion_tracking_enabled():
            self.runtime.publish(self, 'completion', {'completion': progress})

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """Generate object from xml"""
        children = []

        for child in xml_object.getchildren():
            try:
                children.append(system.process_xml(etree.tostring(child)).scope_ids.usage_id)
            except (XMLSyntaxError, AttributeError):
                msg = (
                    'Unable to load child when parsing Multi Problem Block. '
                    'This can happen when a comment is manually added to the course export.'
                )
                logger.error(msg)
                if system.error_tracker is not None:
                    system.error_tracker(msg)

        definition = dict(xml_object.attrib.items())
        return definition, children

    def definition_to_xml(self, resource_fs):
        """Exports Library Content Block to XML"""
        xml_object = etree.Element('multi_problem')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        # Set node attributes based on our fields.
        for field_name, field in self.fields.items():
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self):
                xml_object.set(field_name, str(field.read_from(self)))
        return xml_object
