import os
import subprocess

class AWSSummaryRunner:
    def __init__(self, relic_name: str, relic_type: str, storage_name: str, user_data_path: str) -> None:
        self.relic_name = relic_name
        self.relic_type = relic_type
        self.storage_name = storage_name
        print(user_data_path)
        assert os.path.exists(user_data_path)
        self.user_data_path = user_data_path

    def run(self) -> str:
        command = [
            "aws", "ec2", "run-instances",
            "--image-id", "ami-0944cdf9f9acd69a1",
            "--count", "1",
            "--instance-type", "g4dn.xlarge",
            "--key-name", "deepen-test",
            "--iam-instance-profile", "Name=DeepenRunnerRole",
            "--tag-specifications", f"ResourceType=instance,Tags=[{{Key=Name,Value=DeepenRunner}},{{Key=Bucket,Value=deepen-relics}},{{Key=RelicName,Value={self.relic_name}}},{{Key=RelicType,Value={self.relic_type}}},{{Key=StorageName,Value={self.storage_name}}}]",
            "--user-data", f"file://{self.user_data_path}", 
            "--instance-market-options", '{ "MarketType": "spot", "SpotOptions": { "SpotInstanceType": "one-time" } }',
            "--instance-initiated-shutdown-behavior", "terminate",
            "--block-device-mappings", '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]',
            "--metadata-options", '{ "HttpTokens": "required", "HttpPutResponseHopLimit": 2, "InstanceMetadataTags": "enabled" }',
            "--security-group-ids", "sg-025b49eec4e8e5360",
            "--region", "us-east-2",
            "--output", "json",
            "--query", "Instances[0].InstanceId"
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            instance_id = result.stdout.strip()
            return instance_id
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError(e.returncode, e.cmd, e.output, e.stderr)

def get_summary_runner(
    relic_name: str, relic_type: str, storage_name: str, user_data_path: str
) -> AWSSummaryRunner:
    return AWSSummaryRunner(
        relic_name=relic_name,
        relic_type=relic_type,
        storage_name=storage_name,
        user_data_path=user_data_path
    )
