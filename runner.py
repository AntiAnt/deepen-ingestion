"""
Write code here to initialize a remote aws procssing of a given audio file for the rest of the deepen processing

"""
from typing import Dict


class AWSSummaryRunner:
    def __init__(self, relic_name: str, relic_type: str, storage_name: str, pipeline_args: Dict) -> None:
        self.relic_name = relic_name
        self.relic_type = relic_type
        self.storage_name = storage_name
        self.pipeline_args = pipeline_args



    def run(self) -> str:
        raise NotImplementedError


def get_summary_runner(relic_name: str, relic_type: str, storage_name: str, pipeline_args: Dict) -> AWSSummaryRunner:
    return AWSSummaryRunner(
        relic_name=relic_name,
        relic_type=relic_type,
        storage_name=storage_name,
        pipeline_args=pipeline_args
    )