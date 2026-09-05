from src.schemas import DataTaskSpec, DataAgentResult
from src.tools.metrics import compute_survey_metrics

class DataAgent:
    """
    Sub-agent responsible for executing deterministic metrics on survey records.
    Calls programmatic Python tools rather than guessing calculations.
    """
    def __init__(self):
        self.name = "DataAgent"

    def execute(self, task_spec: DataTaskSpec) -> DataAgentResult:
        """
        Executes computation tool based on structured task specification.
        """
        result = compute_survey_metrics(
            start_date=task_spec.start_date,
            end_date=task_spec.end_date,
            business_id=task_spec.business_id
        )
        return result