from dataclasses import dataclass

from africa_pulse.acquisition.tomtom import TrafficFlowResponse


@dataclass(frozen=True)
class ValidationResult:
    rule_id: str
    outcome: str
    reason: str | None = None


def validate_traffic_flow(observation: TrafficFlowResponse) -> tuple[ValidationResult, ...]:
    results = []
    if observation.free_flow_speed_kph <= 0:
        results.append(ValidationResult("traffic.free_flow_speed_positive", "fail", "free-flow speed <= 0"))
    else:
        results.append(ValidationResult("traffic.free_flow_speed_positive", "pass"))

    if observation.current_speed_kph < 0:
        results.append(ValidationResult("traffic.current_speed_non_negative", "fail", "current speed < 0"))
    else:
        results.append(ValidationResult("traffic.current_speed_non_negative", "pass"))

    if not 0 <= observation.confidence <= 1:
        results.append(ValidationResult("traffic.confidence_in_range", "fail", "confidence outside [0, 1]"))
    else:
        results.append(ValidationResult("traffic.confidence_in_range", "pass"))
    return tuple(results)


def congestion_ratio(observation: TrafficFlowResponse) -> float:
    """Return 0 for free-flow and values approaching 1 as speed falls."""
    if observation.free_flow_speed_kph <= 0:
        raise ValueError("free-flow speed must be positive")
    return max(0.0, 1 - observation.current_speed_kph / observation.free_flow_speed_kph)
