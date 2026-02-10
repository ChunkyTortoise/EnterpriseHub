"""Shared score normalization utilities."""


def clamp_score(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamp a score to [min_val, max_val] range."""
    return min(max_val, max(min_val, value))


def normalize_score(
    value: float,
    input_min: float = 0.0,
    input_max: float = 1.0,
    output_min: float = 0.0,
    output_max: float = 100.0,
) -> float:
    """Normalize a value from one range to another, clamped."""
    if input_max == input_min:
        return output_min
    normalized = (value - input_min) / (input_max - input_min)
    scaled = output_min + normalized * (output_max - output_min)
    return clamp_score(scaled, output_min, output_max)
