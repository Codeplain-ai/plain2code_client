import argparse
import os

import plain_file
import plain_modules
import plain_spec
from event_bus import EventBus
from plain2code_console import console
from plain2code_events import RenderCompleted, RenderFailed
from plain2code_state import RunState
from plain_modules import PlainModule
from render_machine.code_renderer import CodeRenderer
from render_machine.render_context import RenderContext
from render_machine.render_types import RenderError
from render_machine.states import States


class ModuleRenderer:
    def __init__(
        self,
        codeplainAPI,
        filename: str,
        render_range: list[str] | None,
        template_dirs: list[str],
        args: argparse.Namespace,
        run_state: RunState,
        event_bus: EventBus,
    ):
        self.codeplainAPI = codeplainAPI
        self.filename = filename
        self.render_range = render_range
        self.template_dirs = template_dirs
        self.args = args
        self.run_state = run_state
        self.event_bus = event_bus

    def _build_render_context_for_module(
        self,
        module_name: str,
        plain_source: dict,
        required_modules: list[PlainModule],
        template_dirs: list[str],
        render_range: list[str] | None,
    ) -> RenderContext:
        return RenderContext(
            self.codeplainAPI,
            module_name,
            plain_source,
            required_modules,
            template_dirs,
            build_folder=os.path.join(self.args.build_folder, module_name),
            build_dest=self.args.build_dest,
            conformance_tests_folder=self.args.conformance_tests_folder,
            conformance_tests_dest=self.args.conformance_tests_dest,
            unittests_script=self.args.unittests_script,
            conformance_tests_script=self.args.conformance_tests_script,
            prepare_environment_script=self.args.prepare_environment_script,
            copy_build=self.args.copy_build,
            copy_conformance_tests=self.args.copy_conformance_tests,
            render_range=render_range,
            render_conformance_tests=self.args.render_conformance_tests,
            base_folder=self.args.base_folder,
            verbose=self.args.verbose,
            run_state=self.run_state,
            event_bus=self.event_bus,
        )

    def _render_module(
        self, filename: str, render_range: list[str] | None, force_render: bool
    ) -> tuple[bool, list[PlainModule], bool]:
        """Render a module.

        Returns:
            tuple[bool, list[PlainModule], bool]: (Whether the module was rendered, the required modules, and whether the rendering failed)
        """
        module_name, plain_source, required_modules_list = plain_file.plain_file_parser(filename, self.template_dirs)

        resources_list = []
        plain_spec.collect_linked_resources(plain_source, resources_list, None, True)

        required_modules = []
        has_any_required_module_changed = False
        if not self.args.render_machine_graph and required_modules_list:
            console.info(f"Analyzing required modules of module {module_name}...")
            for required_module_name in required_modules_list:
                required_module_filename = required_module_name + plain_file.PLAIN_SOURCE_FILE_EXTENSION
                has_module_changed, sub_required_modules, rendering_failed = self._render_module(
                    required_module_filename,
                    None,
                    self.args.force_render,
                )

                if rendering_failed:
                    return False, required_modules, True

                if has_module_changed:
                    has_any_required_module_changed = True

                for sub_required_module in sub_required_modules:
                    if sub_required_module.name not in [m.name for m in required_modules]:
                        required_modules.append(
                            plain_modules.PlainModule(sub_required_module.name, self.args.build_folder)
                        )

                required_modules.append(plain_modules.PlainModule(required_module_name, self.args.build_folder))

        plain_module = plain_modules.PlainModule(module_name, self.args.build_folder)
        if (
            ((not force_render) or any(module.name == plain_module.name for module in self.loaded_modules))
            and plain_module.get_repo() is not None
            and not plain_module.has_plain_spec_changed(plain_source, resources_list)
            and not plain_module.has_required_modules_code_changed(required_modules)
            and not has_any_required_module_changed
        ):
            return False, required_modules, False

        render_context = self._build_render_context_for_module(
            module_name, plain_source, required_modules, self.template_dirs, render_range
        )
        code_renderer = CodeRenderer(render_context)
        if self.args.render_machine_graph:
            code_renderer.generate_render_machine_graph()
            return True, required_modules, False

        code_renderer.run()
        if code_renderer.render_context.state == States.RENDER_FAILED.value:
            error_message = RenderError.get_display_message(
                code_renderer.render_context.previous_action_payload,
                fallback_message=code_renderer.render_context.last_error_message,
            )
            code_renderer.render_context.event_bus.publish(RenderFailed(error_message=error_message))
            return False, required_modules, True

        plain_module.save_module_metadata(plain_source, resources_list, required_modules)

        self.loaded_modules.append(plain_module)

        return True, required_modules, False

    def render_module(self) -> None:
        self.loaded_modules = list[PlainModule]()
        _, _, rendering_failed = self._render_module(self.filename, self.render_range, True)
        if not rendering_failed:
            self.event_bus.publish(RenderCompleted())
