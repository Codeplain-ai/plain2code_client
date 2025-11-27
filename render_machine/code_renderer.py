from transitions.extensions.diagrams import HierarchicalGraphMachine

from plain2code_state import RunState
from render_machine.render_context import RenderContext
from render_machine.state_machine_config import StateMachineConfig, States


class CodeRenderer:
    """Main code renderer class that orchestrates the code generation workflow using a hierarchical state machine."""

    def __init__(self, codeplain_api, plain_source_tree: dict, args: dict, run_state: RunState):
        self.render_context = RenderContext(codeplain_api, plain_source_tree, args, run_state)
        self.state_machine_config = StateMachineConfig()

        # Initialize the state machine
        states = self.state_machine_config.get_states(self.render_context)
        transitions = self.state_machine_config.get_transitions()

        self.machine = HierarchicalGraphMachine(
            model=self.render_context,
            states=states,
            transitions=transitions,
            initial=States.RENDER_INITIALISED.value,
        )
        self.render_context.set_machine(self.machine)

        # Get action mappings
        self.action_map = self.state_machine_config.get_action_map()
        self.action_result_triggers_map = self.state_machine_config.get_action_result_triggers_map()

    def run(self):
        """Execute the main rendering workflow."""
        previous_action_payload = None
        while True:
            outcome, previous_action_payload = self.action_map[self.render_context.state].execute(
                self.render_context, previous_action_payload
            )

            if self.render_context.state in [
                States.RENDER_FAILED.value,
                States.RENDER_COMPLETED.value,
            ]:
                break

            next_trigger = self.action_result_triggers_map[outcome]
            self.machine.dispatch(next_trigger)

    def generate_render_machine_graph(self):
        """Generate a visual diagram of the state machine."""
        self.render_context.get_graph().draw("render_machine_diagram.png", prog="dot")
