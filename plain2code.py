import importlib.util
import logging
import logging.config
import os
import traceback

import yaml
from liquid2.exceptions import TemplateNotFoundError
from requests.exceptions import RequestException

import file_utils
import plain_spec
from plain2code_arguments import parse_arguments
from plain2code_console import console
from plain2code_state import RunState
from plain2code_utils import RetryOnlyFilter, print_dry_run_output
from render_machine.code_renderer import CodeRenderer
from system_config import system_config

TEST_SCRIPT_EXECUTION_TIMEOUT = 120  # 120 seconds
LOGGING_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging_config.yaml")

DEFAULT_TEMPLATE_DIRS = "standard_template_library"

MAX_UNITTEST_FIX_ATTEMPTS = 20
MAX_CONFORMANCE_TEST_FIX_ATTEMPTS = 20
MAX_CONFORMANCE_TEST_RUNS = 20
MAX_REFACTORING_ITERATIONS = 5
MAX_UNIT_TEST_RENDER_RETRIES = 2

MAX_ISSUE_LENGTH = 10000  # Characters.

UNRECOVERABLE_ERROR_EXIT_CODES = [69]
TIMEOUT_ERROR_EXIT_CODE = 124


class InvalidFridArgument(Exception):
    pass


def get_render_range(render_range, plain_source_tree):
    render_range = render_range.split(",")
    range_end = render_range[1] if len(render_range) == 2 else render_range[0]

    return _get_frids_range(plain_source_tree, render_range[0], range_end)


def get_render_range_from(start, plain_source_tree):
    return _get_frids_range(plain_source_tree, start)


def _get_frids_range(plain_source_tree, start, end=None):
    frids = list(plain_spec.get_frids(plain_source_tree))

    start = str(start)

    if start not in frids:
        raise InvalidFridArgument(f"Invalid start functional requirement ID: {start}. Valid IDs are: {frids}.")

    if end is not None:
        end = str(end)
        if end not in frids:
            raise InvalidFridArgument(f"Invalid end functional requirement ID: {end}. Valid IDs are: {frids}.")

        end_idx = frids.index(end) + 1
    else:
        end_idx = len(frids)

    start_idx = frids.index(start)
    if start_idx >= end_idx:
        raise InvalidFridArgument(
            f"Start functional requirement ID: {start} must be before end functional requirement ID: {end}."
        )

    return frids[start_idx:end_idx]


class IndentedFormatter(logging.Formatter):

    def format(self, record):
        original_message = record.getMessage()

        modified_message = original_message.replace("\n", "\n                ")

        record.msg = modified_message
        return super().format(record)


def render(args, run_state: RunState):  # noqa: C901
    if args.verbose:

        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("anthropic").setLevel(logging.WARNING)
        logging.getLogger("langsmith").setLevel(logging.WARNING)
        logging.getLogger("git").setLevel(logging.WARNING)
        logging.getLogger("anthropic._base_client").setLevel(logging.DEBUG)
        logging.getLogger("services.langsmith.langsmith_service").setLevel(logging.INFO)
        logging.getLogger("transitions").setLevel(logging.WARNING)

        # Try to load logging configuration from YAML file
        if os.path.exists(LOGGING_CONFIG_PATH):
            try:
                with open(LOGGING_CONFIG_PATH, "r") as f:
                    config = yaml.safe_load(f)
                    logging.config.dictConfig(config)
                    console.info(f"Loaded logging configuration from {LOGGING_CONFIG_PATH}")
            except Exception as e:
                console.warning(f"Failed to load logging configuration from {LOGGING_CONFIG_PATH}: {str(e)}")

        # if we have debug level for anthropic._base_client to debug, catch only logs relevant to retrying (ones that are relevant for us)
        if logging.getLogger("anthropic._base_client").level == logging.DEBUG:
            logging.getLogger("anthropic._base_client").addFilter(RetryOnlyFilter())

        formatter = IndentedFormatter("%(levelname)s:%(name)s:%(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        codeplain_logger = logging.getLogger("codeplain")
        codeplain_logger.addHandler(console_handler)
        codeplain_logger.propagate = False

        llm_logger = logging.getLogger("llm")
        llm_logger.addHandler(console_handler)
        llm_logger.propagate = False

        logging.getLogger("repositories").setLevel(logging.INFO)

    # Check system requirements before proceeding
    system_config.verify_requirements()

    with open(args.filename, "r") as fin:
        plain_source = fin.read()

    template_dirs = file_utils.get_template_directories(args.filename, args.template_dir, DEFAULT_TEMPLATE_DIRS)

    [full_plain_source, loaded_templates] = file_utils.get_loaded_templates(template_dirs, plain_source)

    if args.full_plain:
        if args.verbose:
            console.info("Full plain text:\n")

        console.info(full_plain_source)
        return

    codeplainAPI = codeplain_api.CodeplainAPI(args.api_key, console)
    codeplainAPI.verbose = args.verbose

    if args.api:
        codeplainAPI.api_url = args.api

    console.info(f"Rendering {args.filename} to target code.")

    plain_source_tree = codeplainAPI.get_plain_source_tree(plain_source, loaded_templates, run_state)

    if args.render_range is not None:
        args.render_range = get_render_range(args.render_range, plain_source_tree)
    elif args.render_from is not None:
        args.render_range = get_render_range_from(args.render_from, plain_source_tree)

    resources_list = []
    plain_spec.collect_linked_resources(plain_source_tree, resources_list, None, True)

    # Handle dry run and full plain here (outside of state machine)
    if args.dry_run:
        console.info("Printing dry run output...")
        print_dry_run_output(plain_source_tree, args.render_range)
        return
    if args.full_plain:
        console.info("Printing full plain output...")
        console.info(full_plain_source)
        return

    console.info("Using the state machine to render the functional requirement.")
    code_renderer = CodeRenderer(codeplainAPI, plain_source_tree, args, run_state)

    if args.render_machine_graph:
        code_renderer.generate_render_machine_graph()
        return

    code_renderer.run()
    return


if __name__ == "__main__":  # noqa: C901
    args = parse_arguments()

    codeplain_api_module_name = "codeplain_local_api"

    codeplain_api_spec = importlib.util.find_spec(codeplain_api_module_name)
    if args.api or codeplain_api_spec is None:
        if not args.api:
            args.api = "https://api.codeplain.ai"
        console.debug(f"Running plain2code using REST API at {args.api}.")
        import codeplain_REST_api as codeplain_api
    else:
        if not args.full_plain:
            console.debug("Running plain2code using local API.\n")

        codeplain_api = importlib.import_module(codeplain_api_module_name)

    run_state = RunState(spec_filename=args.filename, replay_with=args.replay_with)
    console.debug(f"Render ID: {run_state.render_id}")

    try:
        render(args, run_state)
    except InvalidFridArgument as e:
        console.error(f"Error rendering plain code: {str(e)}.\n")
        # No need to print render ID since this error is going to be thrown at the very start so user will be able to
        # see the render ID that's printed at the very start of the rendering process.
    except FileNotFoundError as e:
        console.error(f"Error rendering plain code: {str(e)}\n")
        console.debug(f"Render ID: {run_state.render_id}")
    except TemplateNotFoundError as e:
        console.error(f"Error: Template not found: {str(e)}\n")
        console.error(system_config.get_error_message("template_not_found"))
    except KeyboardInterrupt:
        console.error("Keyboard interrupt")
        # Don't print the traceback here because it's going to be from keyboard interrupt and we don't really care about that
        console.debug(f"Render ID: {run_state.render_id}")
    except RequestException as e:
        console.error(f"Error rendering plain code: {str(e)}\n")
        console.debug(f"Render ID: {run_state.render_id}")
    except Exception as e:
        console.error(f"Error rendering plain code: {str(e)}\n")
        console.debug(f"Render ID: {run_state.render_id}")
        traceback.print_exc()
