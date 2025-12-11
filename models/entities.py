
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class LeafResult:
    """Represents the analysis result for a single leaf."""
    leaf_id: int
    ds_value: float          # Disease Severity (DS) percentage
    severity_class: str      # "mild" / "moderate" / "severe"
    overlay_path: str = ""   # Path to the overlay image for this leaf

@dataclass
class SampleRecord:
    """Represents a complete sample record for a single capture."""
    sample_id: str
    timestamp: datetime
    plot_id: str
    cultivar: str
    growth_stage: str
    mean_ds: float
    severity_class: str
    leaf_results: List[LeafResult] = field(default_factory=list)
    raw_image_path: str = ""
    notes: str = ""
