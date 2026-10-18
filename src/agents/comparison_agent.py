from typing import Optional

from src.agents.data_agent import DataAgent
from src.schemas import (
    ComparisonResult,
    ComparisonTaskSpec,
    DataTaskSpec,
)


class ComparisonAgent:
    """Compares deterministic survey metrics across two date ranges."""

    def __init__(self, data_agent: Optional[DataAgent] = None):
        self.name = "ComparisonAgent"
        self.data_agent = data_agent or DataAgent()

    def execute(self, task_spec: ComparisonTaskSpec) -> ComparisonResult:
        current_metrics = self.data_agent.execute(DataTaskSpec(
            start_date=task_spec.current_start,
            end_date=task_spec.current_end,
            business_id=task_spec.business_id,
        ))
        previous_metrics = self.data_agent.execute(DataTaskSpec(
            start_date=task_spec.previous_start,
            end_date=task_spec.previous_end,
            business_id=task_spec.business_id,
        ))

        average_rating_delta = round(
            current_metrics.average_rating - previous_metrics.average_rating,
            2,
        )
        current_themes = {
            theme.theme: theme.count for theme in current_metrics.top_themes
        }
        previous_themes = {
            theme.theme: theme.count for theme in previous_metrics.top_themes
        }
        theme_changes = {
            theme: current_themes.get(theme, 0) - previous_themes.get(theme, 0)
            for theme in current_themes.keys() | previous_themes.keys()
        }

        direction = (
            "improved" if average_rating_delta > 0.05
            else "declined" if average_rating_delta < -0.05
            else "unchanged"
        )

        return ComparisonResult(
            current_metrics=current_metrics,
            previous_metrics=previous_metrics,
            average_rating_delta=average_rating_delta,
            response_count_delta=(
                current_metrics.total_responses - previous_metrics.total_responses
            ),
            theme_changes=theme_changes,
            direction=direction,
        )