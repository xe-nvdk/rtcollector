

from dataclasses import dataclass
from typing import Dict

@dataclass
class Metric:
    name: str
    value: float
    timestamp: int
    labels: Dict[str, str]

    def as_tsadd(self):
        """
        Returns arguments for TS.ADD RedisTimeSeries command
        """
        label_parts = []
        for k, v in self.labels.items():
            label_parts.extend([k, v])
        return [self.name, self.timestamp, self.value, "LABELS", *label_parts]