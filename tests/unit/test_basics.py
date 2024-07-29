import unittest
from unittest import mock

import ddt
from sample_xblocks.basic.problem import ProblemBlock

from multi_problem_xblock.compat import L_SHOWANSWER
from multi_problem_xblock.multi_problem_xblock import DISPLAYFEEDBACK, SCORE_DISPLAY_FORMAT, MultiProblemBlock

from ..utils import TestCaseMixin, instantiate_block


@ddt.ddt
class BasicTests(TestCaseMixin, unittest.TestCase):
    """ Basic unit tests for the Multi-problem block, using its default settings """

    def setUp(self):
        self.children_ids = []
        self.children = {}
        for i in range(3):
            usage_key = f'block-v1:edx+cs1+test+type@problem+block@{i}'
            problem_block = instantiate_block(ProblemBlock, fields={
                'usage_key': usage_key,
            })
            self.children[usage_key] = problem_block
            self.children_ids.append(usage_key)
        self.block = instantiate_block(MultiProblemBlock, fields={
            'usage_key': 'block-v1:edx+cs1+test+type@multi_problem+block@1',
            'children': self.children,
        })
        self.block.selected_children = lambda: [('problem', child) for child in self.children]
        self.block.allow_resetting_children = True
        self.patch_workbench()

    @staticmethod
    def _make_submission(modify_submission=None):
        modify = modify_submission if modify_submission else lambda x: x

        submission = {
            'display_name': "Multi Problem test block",
            'showanswer': L_SHOWANSWER.FINISHED,
            'display_feedback': DISPLAYFEEDBACK.IMMEDIATELY,
            'score_display_format': SCORE_DISPLAY_FORMAT.X_OUT_OF_Y,
            'cut_off_score': 0,
            'next_page_on_submit': False,
        }

        modify(submission)

        return submission

    def assertPublishEvent(self, completion):
        """
        Verify that publish event is fired with expected event data.
        """
        with mock.patch('workbench.runtime.WorkbenchRuntime.publish', mock.Mock()) as patched_publish:
            self.block.publish_completion(completion)
            expected_calls = [mock.call(self.block, 'completion', {'completion': completion})]
            self.assertEqual(patched_publish.mock_calls, expected_calls)

    def test_template_contents(self):
        context = {}
        student_fragment = self.block.runtime.render(self.block, 'student_view', context)
        self.assertIn(
            '<div class="multi-problem-container" data-next-page-on-submit="false">',
            student_fragment.content
        )
        self.assertIn('<div class="problem-test-score-container">', student_fragment.content)

    def test_student_view_data(self):
        _, template_context, js_context = self.block.student_view_data({})
        items = template_context.pop('items')
        self.assertEqual(template_context, {
            'self': self.block,
            'watched_completable_blocks': set(),
            'completion_delay_ms': None,
            'reset_button': True,
            'show_results': True,
            'next_page_on_submit': False,
            'overall_progress': 0,
            'bookmarks_service_enabled': False,
        })
        self.assertEqual(js_context, {
            'current_slide': 0,
            'next_page_on_submit': False,
        })
        for index, item in enumerate(items):
            self.assertEqual(item['id'], self.children_ids[index])
