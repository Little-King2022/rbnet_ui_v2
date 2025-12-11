import random
import time
import uuid
from datetime import datetime
from typing import Optional, Dict

import numpy as np
from PySide6.QtCore import QSettings

from models.entities import LeafResult, SampleRecord

class RbnetStub:
    """
    A fake RBNet engine that generates plausible-looking random data.
    Reads severity thresholds from QSettings.
    """

    def __init__(self):
        self.settings = QSettings("RBNet", "FieldSurvey")

    def get_thresholds(self):
        """Reads current thresholds from settings."""
        return {
            "mild": int(self.settings.value("thresholds/mild", 10)),
            "moderate": int(self.settings.value("thresholds/moderate", 30))
        }

    def get_severity_class(self, ds_value: float, thresholds: Dict[str, float]) -> str:
        """Determines the severity class based on the DS value and thresholds."""
        if ds_value <= thresholds["mild"]:
            return "mild"
        elif ds_value <= thresholds["moderate"]:
            return "moderate"
        else:
            return "severe"

    def analyze(
        self,
        image: np.ndarray,
        plot_id: str = "PLOT-001",
        cultivar: str = "Cultivar-A",
        growth_stage: str = "Tillering",
        notes: str = ""
    ) -> SampleRecord:
        """
        Simulates analyzing an image and returns a fake SampleRecord.
        """
        print("Stub analysis started...")
        # Simulate processing time
        time.sleep(random.uniform(0.5, 1.5))

        thresholds = self.get_thresholds()
        
        num_leaves = random.randint(3, 8)
        leaf_results = []
        total_ds = 0

        for i in range(1, num_leaves + 1):
            ds_value = random.uniform(0.0, 60.0) # Range 0-60%
            severity = self.get_severity_class(ds_value, thresholds)
            leaf_results.append(
                LeafResult(
                    leaf_id=i,
                    ds_value=round(ds_value, 2),
                    severity_class=severity
                )
            )
            total_ds += ds_value

        mean_ds = total_ds / num_leaves
        overall_severity = self.get_severity_class(mean_ds, thresholds)
        
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d-%H%M%S")
        random_suffix = random.randint(10000, 99999)
        sample_id = f"{timestamp_str}-{random_suffix}"
        
        record = SampleRecord(
            sample_id=sample_id,
            timestamp=now,
            plot_id=plot_id,
            cultivar=cultivar,
            growth_stage=growth_stage,
            mean_ds=round(mean_ds, 2),
            severity_class=overall_severity,
            leaf_results=leaf_results,
            raw_image_path="", # Will be set by ResultPage/DataManager upon saving
            notes=notes
        )

        print(f"Stub analysis finished. Mean DS: {record.mean_ds}% ({record.severity_class})")
        return record