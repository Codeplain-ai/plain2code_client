import logging

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
