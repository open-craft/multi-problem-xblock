import json
from unittest.mock import MagicMock, Mock, patch

from sample_xblocks.basic.problem import ProblemBlock, String
from webob import Request
from workbench.runtime import WorkbenchRuntime
from xblock.core import Scope
from xblock.field_data import DictFieldData


def make_request(data, method='POST'):
    """ Make a webob JSON Request """
    request = Request.blank('/')
    request.method = 'POST'
    data = json.dumps(data).encode('utf-8') if data is not None else b''
    request.body = data
    request.method = method
    return request


def instantiate_block(cls, fields=None):
    """
    Instantiate the given XBlock in a mock runtime.
    """
    fields = fields or {}
    usage_key = fields.pop('usage_key')
    children = fields.pop('children', {})
    field_data = DictFieldData(fields or {})
    block = cls(
        runtime=WorkbenchRuntime(),
        field_data=field_data,
        scope_ids=MagicMock()
    )
    block.children = children
    block.runtime.get_block = lambda child_id: children[child_id]
    block.usage_key.__str__.return_value = usage_key
    block.usage_key.course_key.make_usage_key = lambda _, child_id: child_id
    block.get_children = lambda: list(children.values())
    return block


class SampleProblemBlock(ProblemBlock):
    question = String(scope=Scope.content)
    showanswer = String(scope=Scope.settings, default="")
    show_correctness = String(scope=Scope.settings, default="")
    lcp = Mock(student_answers={1: 1})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Return incremental mock question answer text each time it is called.
        self.lcp.find_question_label.side_effect = [f'question{x}' for x in range(3)]
        self.lcp.find_answer_text.side_effect = [f'answer{x}' for x in range(3)]
        self.lcp.find_correct_answer_text.side_effect = [f'correct_answer{x}' for x in range(3)]


class TestCaseMixin:
    """ Helpful mixins for unittest TestCase subclasses """
    maxDiff = None

    SLIDE_CHANGE_HANDLER = 'handle_slide_change'
    GET_OVERALL_PROGRESS_HANDLER = 'get_overall_progress'
    GET_TEST_SCORES = 'get_test_scores'
    RESET_HANDLER = 'reset_selected_children'

    def patch_workbench(self):
        self.apply_patch(
            'workbench.runtime.WorkbenchRuntime.local_resource_url',
            lambda _, _block, path: '/expanded/url/to/multi_problem_xblock/' + path
        )

    def apply_patch(self, *args, **kwargs):
        new_patch = patch(*args, **kwargs)
        mock = new_patch.start()
        self.addCleanup(new_patch.stop)
        return mock

    def call_handler(self, handler_name, data=None, expect_json=True, method='POST'):
        response = self.block.handle(handler_name, make_request(data, method=method))
        if expect_json:
            self.assertEqual(response.status_code, 200)
            return json.loads(response.body.decode('utf-8'))
        return response
