import unittest
from unittest import mock

import ddt

from multi_problem_xblock.compat import L_SHOWANSWER, L_ShowCorrectness
from multi_problem_xblock.multi_problem_xblock import DISPLAYFEEDBACK, SCORE_DISPLAY_FORMAT, MultiProblemBlock

from ..utils import SampleProblemBlock, TestCaseMixin, instantiate_block


@ddt.ddt
class BasicTests(TestCaseMixin, unittest.TestCase):
    """ Basic unit tests for the Multi-problem block, using its default settings """

    def setUp(self):
        self.children_ids = []
        self.children = {}
        for i in range(3):
            usage_key = f'block-v1:edx+cs1+test+type@problem+block@{i}'
            problem_block = instantiate_block(SampleProblemBlock, fields={
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
        """Verify rendered template contents"""
        context = {}
        student_fragment = self.block.runtime.render(self.block, 'student_view', context)
        self.assertIn(
            '<div class="multi-problem-container" data-next-page-on-submit="false">',
            student_fragment.content
        )
        self.assertIn('<div class="problem-test-score-container">', student_fragment.content)

    def test_student_view_data(self):
        """Verify student data used in templates"""
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

    def test_editor_saved(self):
        """Verify whether child values are updated based on parent block"""
        self.block.showanswer = L_SHOWANSWER.NEVER
        self.block.display_feedback = DISPLAYFEEDBACK.END_OF_TEST
        # Call editor_saved as this is called by cms xblock api before saving the block
        self.block.editor_saved(None, None, None)
        for child in self.block.get_children():
            self.assertEqual(child.showanswer, L_SHOWANSWER.NEVER)
            self.assertEqual(child.show_correctness, L_ShowCorrectness.NEVER)

        # if display_feedback = immediately, child block showanswer should be set to always
        self.block.display_feedback = DISPLAYFEEDBACK.IMMEDIATELY
        self.block.editor_saved(None, None, None)
        for child in self.block.get_children():
            self.assertEqual(child.show_correctness, L_ShowCorrectness.ALWAYS)

    def test_incomplete_overall_progress_handler(self):
        """Check progress handler information when all problems are not completed"""
        # Check progress handler when 2/3 problems are completed
        self.block.children[self.children_ids[0]].is_submitted = lambda: True
        self.block.children[self.children_ids[1]].is_submitted = lambda: True
        self.block.children[self.children_ids[2]].is_submitted = lambda: False
        res = self.call_handler('get_overall_progress', {}, method='GET')
        self.assertEqual(res, {'overall_progress': int((2 / 3) * 100)})

    def test_completed_overall_progress_handler(self):
        """Check progress handler information when all problems are completed"""
        self.block.publish_completion = mock.Mock()
        # Set cut_off_score to 100%
        self.block.cut_off_score = 1
        # Check progress handler when 3/3 problems are completed and all are correct
        for child in self.block.get_children():
            child.is_submitted = lambda: True
            child.is_correct = lambda: True
            child.score = mock.Mock(raw_earned=1, raw_possible=1)
        res = self.call_handler('get_overall_progress', {}, method='GET')
        self.assertEqual(res, {'overall_progress': 100})
        self.block.publish_completion.assert_called_once_with(1)

        # Update one child to be incorrect
        self.block.children[self.children_ids[2]].is_correct = lambda: False
        self.block.children[self.children_ids[2]].score = mock.Mock(raw_earned=0, raw_possible=1)
        res = self.call_handler('get_overall_progress', {}, method='GET')
        self.assertEqual(res, {'overall_progress': 100})
        # Completion should be reduced to 0.9 as the student score was less than required cut_off_score
        self.block.publish_completion.assert_called_with(0.9)

    def test_get_scores_when_incomplete(self):
        """Test get_test_scores handler when all problems are not completed"""
        for _, child in enumerate(self.block.get_children()):
            child.is_submitted = lambda: False
        res = self.call_handler('get_test_scores', {}, expect_json=False, method='GET')
        self.assertEqual(res.status_code, 400)

    def test_get_scores(self):
        """Test get_test_scores handler"""
        for index, child in enumerate(self.block.get_children()):
            child.is_submitted = lambda: True
            # Set last problem incorrect
            child.score = mock.Mock(raw_earned=1 if index < 2 else 0, raw_possible=1)
            child.is_correct = lambda: index < 2  # pylint: disable=cell-var-from-loop
        res = self.call_handler('get_test_scores', {}, expect_json=False, method='GET')
        self.assertIn('question2', res.text)
        self.assertIn('answer2', res.text)
        self.assertIn('correct_answer2', res.text)
        self.assertIn('question1', res.text)
        self.assertIn('answer1', res.text)
        self.assertIn('question0', res.text)
        self.assertIn('answer0', res.text)
        self.assertIn('<b class="test-score">2/3</b>', res.text)

    def test_get_scores_in_percentage(self):
        """Test get_test_scores handler returns percentage"""
        self.block.score_display_format = SCORE_DISPLAY_FORMAT.PERCENTAGE
        for index, child in enumerate(self.block.get_children()):
            child.is_submitted = lambda: True
            # Set last problem incorrect
            child.score = mock.Mock(raw_earned=1 if index < 2 else 0, raw_possible=1)
            child.is_correct = lambda: index < 2  # pylint: disable=cell-var-from-loop
        res = self.call_handler('get_test_scores', {}, expect_json=False, method='GET')
        self.assertIn('question2', res.text)
        self.assertIn('answer2', res.text)
        self.assertIn('correct_answer2', res.text)
        self.assertIn('question1', res.text)
        self.assertIn('answer1', res.text)
        self.assertIn('question0', res.text)
        self.assertIn('answer0', res.text)
        self.assertIn('<b class="test-score">67%</b>', res.text)
