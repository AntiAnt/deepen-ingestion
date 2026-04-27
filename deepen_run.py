import argparse
import json
import os
from typing import Dict
from urllib.parse import parse_qs, parse_qsl, urlparse

from reliquery import Relic

from deepen_ingestion import SourceTypeError, get_ingestion_service
from runner import get_summary_runner


def get_pipeline_config(path: str) -> Dict:
    assert os.path.exists(path)
    config = None
    with open(path, "r") as f:
        config = json.loads(f.read())
    assert config is not None
    return config


def get_relic(relic_name: str, relic_type, storage_name: str = None) -> Relic:
    if storage_name is not None:
        return Relic(name=relic_name, relic_type=relic_type, storage_name=storage_name)

    return Relic(name=relic_name, relic_type=relic_type)


def get_video_id_from_url(url: str) -> str:
    return parse_qs(urlparse(url).query).get("v", [None])[0]


def main():
    parser = argparse.ArgumentParser(
        description="Deepen pipeline: ingest, transcribe, and summarize informational videos.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("--config-path", required=True, help="path to pipeline config")

    args = parser.parse_args()
    config = get_pipeline_config(args.config_path)

    source_type = config.get("source_type", None)
    if source_type == "file-system":
        input_source = config["audio_path"]
        print(input_source)
        relic_name = config["relic_name"]
    elif source_type == "youtube":
        input_source = config["video_url"] 
        video_id = get_video_id_from_url(input_source)
        relic_name = config.get("relic_name", video_id)
    else:
        raise SourceTypeError(f"Source type {source_type} not supported")

    relic_type = config.get("relic_type", "video-summary")
    relic_storage_name = config.get("relic_storage_name")
    skip_ingestion = config.get("skip_ingestion")
    user_data_path = config["path_to_user_data"]

    relic = get_relic(
        relic_name=relic_name, relic_type=relic_type, storage_name=relic_storage_name
    )

    # store config on bucket
    relic.add_json(name="remote-config", json_data=config["pipeline"])
    print(input_source)
    # Ingestion
    if skip_ingestion is not None and skip_ingestion is False:
        ingestion_service = get_ingestion_service(source_type=source_type)
        ingestion_result = ingestion_service.ingest_audio(input_source)
        ingestion_result["audio"].seek(0)
        relic.add_audio(name="audio.wav", audio_obj=ingestion_result["audio"])
        relic.add_json(name="metadata", json_data=ingestion_result["metadata"])
        if ingestion_result.get("info") is not None:
            relic.add_json(name="video_info", json_data=ingestion_result["info"])

        print("Ingestion complete!")

        if config["ingestion_only"] is True:
            return

    if config["remote_summary_processing"] is True:
        pipeline_args = config["pipeline"]
        if "ingestion" in pipeline_args:
            del pipeline_args["ingestion"]

        summary_runner = get_summary_runner(
            relic_name=relic_name,
            relic_type=relic_type,
            storage_name=relic_storage_name,
            user_data_path=user_data_path
        )

        isnstance_id = summary_runner.run()


        print(f"Remote summariztion started on instance: {isnstance_id}")
    else:
        raise NotImplementedError("Local processing is not yet supported")


if __name__ == "__main__":
    main()
