class FunctionalRequirementTooComplex(Exception):
    def __init__(self, message, proposed_breakdown=None):
        self.message = message
        self.proposed_breakdown = proposed_breakdown
        super().__init__(self.message)


class ConflictingRequirements(Exception):
    pass


class CreditBalanceTooLow(Exception):
    pass


class LLMInternalError(Exception):
    pass


class MissingResource(Exception):
    pass


class PlainSyntaxError(Exception):
    pass


class OnlyRelativeLinksAllowed(Exception):
    pass


class LinkMustHaveTextSpecified(Exception):
    pass


class NoRenderFound(Exception):
    pass


class MultipleRendersFound(Exception):
    pass


class UnexpectedState(Exception):
    pass
