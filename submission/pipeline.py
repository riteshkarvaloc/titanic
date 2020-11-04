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
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijc0YmNkZjBmZWJmNDRiOGRhZGQxZWIyOGM2MjhkYWYxIn0.eyJ1c2VybmFtZSI6Im9jIiwicm9sZSI6ImRhdGFzY2llbnRpc3QsbWxlLHBlLG9wZXJhdG9yIiwiZXhwIjo0ODQzODk2MjM4LCJpYXQiOjE2MDM4OTYyMzgsImlzcyI6IkRLdWJlIn0.EPBlkIdrPalYet0jN1Nvnzi7mMmf0-Nqi693Z0u45dkv3HHBHX1DWFO4-4XOWmx5cMogPg3LReglKSI88Rbacb2XdNYrYJVefbIhj_HTJu_tdWDABJ0gciWzNPByHVMpwj3fMQ8lpZrP5m3ZY5MGG-PkwIuz2ZSq0ncDYhNvxxjldWrdEBtHL78Eh5ts17ktqpmwIYytBcAwJvXsIj85Zy21hvGPCS0RXVZHNXDpg0OhZ_ifHC-etOgag1vQV_QfRA8iRhKMPzJmsAl2T9uwBPhKgLWwnEEcWOwiKRYZxajDP03jzBrnv6r318skdkLikb_--LuWoJIWRuDf430FAQ"
    args = {
        "token": token,
        "project_id": "fe7i48",
        "dataset": "titanic-dataset",
        "version": "1603979982241",
    }
    kfp.Client().create_run_from_pipeline_func(titanic_pipline, arguments=args)
