import json

import kfp
from kubernetes.client.models import V1EnvVar


class ContainerOp(kfp.dsl.ContainerOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_pod_label(name="dkube.garbagecollect", value="true")
        self.add_pod_label(name="dkube.garbagecollect.policy", value="all")
        self.add_pod_label(name="runid", value="{{pod.name}}")
        self.add_pod_label(name="wfid", value="{{workflow.uid}}")

@kfp.dsl.pipeline(
    name="Titanic Experiment pipeline",
    description="A pipline showing how to use evaluation component",
)
def titanic_pipline(token, project_id, dataset, version):
    pipelineConfig = kfp.dsl.PipelineConf()
    pipelineConfig.set_image_pull_policy("Always")
    
    input_volumes = json.dumps([f"titanic-test-pvc@dataset://{dataset}/{version}"])
    storage_op = ContainerOp(
        name="get_dataset",
        image="ocdr/dkubepl:storage_v2",
        command=[
            "dkubepl",
            "storage",
            "--token",
            token,
            "--namespace",
            "kubeflow",
            "--input_volumes",
            input_volumes,
        ],
    )

    predict_op = ContainerOp(
        name="predict",
        image="ocdr/titanic_submission",
        command=["python", "predict.py"],
        pvolumes={"/titanic-test/": kfp.dsl.PipelineVolume(pvc="titanic-test-pvc")},
        file_outputs={"output": "/tmp/prediction.csv"},
    )
    predict_op.after(storage_op)
    predictions = kfp.dsl.InputArgumentPath(predict_op.outputs["output"])
    
    submit_op = ContainerOp(
        name="submit",
        image="ocdr/d3project_eval",
        command=[
            "python",
            "submit.py",
            kfp.dsl.RUN_ID_PLACEHOLDER,
            "-t",
            token,
            predictions,
        ],
        file_outputs={
            "mlpipeline-ui-metadata": "/metadata.json",
            "results": "/results",
        },
    )
    env_var = V1EnvVar(name="DKUBE_PROJECT_ID", value=project_id)
    submit_op.add_env_variable(env_var)


if __name__ == "__main__":
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijc0YmNkZjBmZWJmNDRiOGRhZGQxZWIyOGM2MjhkYWYxIn0.eyJ1c2VybmFtZSI6Im9jIiwicm9sZSI6ImRhdGFzY2llbnRpc3QsbWxlLHBlLG9wZXJhdG9yIiwiZXhwIjo0ODQ0NDA1NDUyLCJpYXQiOjE2MDQ0MDU0NTIsImlzcyI6IkRLdWJlIn0.JovI7NHWRZTa3mYFduxF88cRk6AOzduFruvInWO5bpEJHn1N7s0-GUuIEGDwExiKH98q9NIFlYwSfeGbEH8Mw89EPkRTiGW6Wx_x9ju44lQ6VJJWXEYjJtJ97s3c9tN8nNGFTX1LIoVDQ2-0_qRTgd6YVcDX6b6qQ4J_x5_M9KpHcyBvxaIZxDVjEFDNwBJN15Y-hlehsQAYXoO-xNVMioAOAee7pka3htpxnof0pDG_9R5vYFiSaw_u84GgKMBN2SpeEU7tEYyOCXqXrgQVBO9i8QlsozE44o09WDiURg4h_3t7nGQYaZr5HwIfK83xbowPDKDXTxSfMJGAhp6tWQ"
    args = {
        "token": token,
        "project_id": "eairm4",
        "dataset": "oc:titanic-test",
        "version": "1604490031795",
    }
    kfp.Client().create_run_from_pipeline_func(titanic_pipline, arguments=args)
