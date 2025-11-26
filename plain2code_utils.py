import logging
from typing import Optional

import plain_spec
from plain2code_console import console

AMBIGUITY_CAUSES = {
    "reference_resource_ambiguity": "Ambiguity is in the reference resources",
    "definition_ambiguity": "Ambiguity is in the definitions",
    "non_functional_requirement_ambiguity": "Ambiguity is in the non-functional requirements",
    "functional_requirement_ambiguity": "Ambiguity is in the functional requirements",
    "other": "Ambiguity in the other parts of the specification",
}


class RetryOnlyFilter(logging.Filter):
    def filter(self, record):
        # Allow all logs with level > DEBUG (i.e., INFO and above)
        if record.levelno > logging.DEBUG:
            return True
        # For DEBUG logs, only allow if message matches retry-related patterns
        msg = record.getMessage().lower()
        return (
            "retrying due to" in msg
            or "raising timeout error" in msg
            or "raising connection error" in msg
            or "encountered exception" in msg
            or "retrying request" in msg
            or "retry left" in msg
            or "1 retry left" in msg
            or "retries left" in msg
        )


def print_dry_run_output(plain_source_tree: dict, render_range: Optional[list[str]]):
    frid = plain_spec.get_first_frid(plain_source_tree)

    while frid is not None:
        is_inside_range = render_range is None or frid in render_range

        if is_inside_range:
            specifications, _ = plain_spec.get_specifications_for_frid(plain_source_tree, frid)
            functional_requirement_text = specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1]
            console.info("\n-------------------------------------")
            console.info(f"Rendering functional requirement {frid}")
            console.info(f"[b]{functional_requirement_text}[/b]")
            console.info("-------------------------------------\n")
            if plain_spec.ACCEPTANCE_TESTS in specifications:
                for i, acceptance_test in enumerate(specifications[plain_spec.ACCEPTANCE_TESTS], 1):
                    console.info(f"\nGenerating acceptance test #{i}:\n\n{acceptance_test}")
        else:
            console.info("\n-------------------------------------")
            console.info(f"Skipping rendering iteration: {frid}")
            console.info("-------------------------------------\n")

        frid = plain_spec.get_next_frid(plain_source_tree, frid)
