import json

import kfp
from kubernetes.client.models import V1EnvVar


@kfp.dsl.pipeline(
    name="Titanic Experiment pipeline",
    description="A pipline showing how to use evaluation component",
)
def titanic_pipline(token, project_id):
    pipelineConfig = kfp.dsl.PipelineConf()
    pipelineConfig.set_image_pull_policy("Always")

    input_volumes = json.dumps(
        ["titanic-test-pvc@dataset://titanic-test/1603048660622"]
    )
    storage_op = kfp.dsl.ContainerOp(
        "get_dataset",
        image="ocdr/dkubepl:storage_v1",
        command=[
            "dkubepl",
            "storage",
            "--token",
            token,
            "--namespace",
            "kubeflow",
            "--input_volumes",
            input_volumes,
            "--runid",
            "{{pod.name}}",
            "--wfid",
            "{{workflow.uid}}",
        ],
    )

    predict_op = kfp.dsl.ContainerOp(
        "predict",
        image="ocdr/titanic_submission",
        command=["python", "predict.py"],
        pvolumes={"/titanic-test/": kfp.dsl.PipelineVolume(pvc="titanic-test-pvc")},
        file_outputs={"output": "/tmp/prediction.csv"},
    )
    predict_op.after(storage_op)
    predictions = kfp.dsl.InputArgumentPath(predict_op.outputs["output"])
    submit_op = kfp.dsl.ContainerOp(
        "submit",
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
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijc0YmNkZjBmZWJmNDRiOGRhZGQxZWIyOGM2MjhkYWYxIn0.eyJ1c2VybmFtZSI6Im9jIiwicm9sZSI6ImRhdGFzY2llbnRpc3QsbWxlLHBlLG9wZXJhdG9yIiwiZXhwIjo0ODQyODUzNzk0LCJpYXQiOjE2MDI4NTM3OTQsImlzcyI6IkRLdWJlIn0.3LFnWC1fI2vUVn2EHIaodC_BJxv2G19PbdyLVx8Vzid5CI_9F_UnAjX9N3P1cgO-npf4FnQqYM3hMGyRh1JCnNA2Ag2rXx4g5Da4ecdsndhZjXwtuEulXAGJO2FGe_L5zCciWEzOZB9JUW1xdOyLOZOUAT71TxBnX7rVRvQHyuTY3SF1Fs7na5z82ggMgFC2BI1vhc2XCwV9u6ftqww3rogdPMLri7mbtyQIQ9Ip-NrOOcjXyFD5Uow7-PevnkxLSOICAh7QvvI7WHxJxa6xDHuokPaX-q8qk1tHm4-hbFUcyIa8WeUB-DDxyWgczQmQ_s70q4cJt2vwPbRAfoyWqw"
    kfp.Client().create_run_from_pipeline_func(
        titanic_pipline, arguments={"token": token, "project_id": "ucpu3w"}
    )
