"""Test runner for reference count opcode insertion transform test cases.

The transform inserts needed reference count increment/decrement
operations to IR.
"""

import os.path

from mypy.errors import CompileError
from mypy.test.config import test_temp_dir
from mypy.test.data import DataDrivenTestCase
from mypyc.common import TOP_LEVEL_NAME
from mypyc.ir.pprint import format_func
from mypyc.test.testutil import (
    ICODE_GEN_BUILTINS,
    MypycDataSuite,
    assert_test_output,
    build_ir_for_single_file,
    infer_ir_build_options_from_test_name,
    remove_comment_lines,
    replace_word_size,
    use_custom_builtins,
)
from mypyc.transform.refcount import insert_ref_count_opcodes
from mypyc.transform.uninit import insert_uninit_checks

files = ["refcount.test"]


class TestRefCountTransform(MypycDataSuite):
    files = files
    base_path = test_temp_dir
    optional_out = True

    def run_case(self, testcase: DataDrivenTestCase) -> None:
        """Perform a runtime checking transformation test case."""
        options = infer_ir_build_options_from_test_name(testcase.name)
        if options is None:
            # Skipped test case
            return
        with use_custom_builtins(os.path.join(self.data_prefix, ICODE_GEN_BUILTINS), testcase):
            expected_output = remove_comment_lines(testcase.output)
            expected_output = replace_word_size(expected_output)
            try:
                ir = build_ir_for_single_file(testcase.input, options)
            except CompileError as e:
                actual = e.messages
            else:
                actual = []
                for fn in ir:
                    if fn.name == TOP_LEVEL_NAME and not testcase.name.endswith("_toplevel"):
                        continue
                    insert_uninit_checks(fn)
                    insert_ref_count_opcodes(fn)
                    actual.extend(format_func(fn))

            assert_test_output(testcase, actual, "Invalid source code output", expected_output)
