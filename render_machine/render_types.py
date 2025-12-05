from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FridContext:
    frid: str
    specifications: dict
    functional_requirement_text: str
    linked_resources: dict
    functional_requirement_render_attempts: int = 0
    changed_files: set[str] = field(default_factory=set)
    refactoring_iteration: int = 0


@dataclass
class UnitTestsRunningContext:
    fix_attempts: int
    changed_files: set[str] = field(default_factory=set)


@dataclass
class ConformanceTestsRunningContext:
    current_testing_frid: Optional[str]
    fix_attempts: int
    conformance_tests_json: dict
    conformance_tests_render_attempts: int
    current_testing_frid_specifications: Optional[dict[str, list]]
    conformance_test_phase_index: int  # 0 => conformance tests, 1 or more => acceptance tests
    regenerating_conformance_tests: bool = False

    # will be propagated only when:
    # - current_testing_frid == frid  noqa: E800
    # - conformance_test_phase_index == 0 (conformance tests phase)
    current_testing_frid_high_level_implementation_plan: Optional[str] = None
    should_prepare_testing_environment: bool = False
