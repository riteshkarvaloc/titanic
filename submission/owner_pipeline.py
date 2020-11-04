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
    name="Titanic Experiment pipeline (Owner)",
    description="A pipline showing how to use evaluation component",
)
def titanic_pipline(token, project_id, dataset, version, claimname="titanic-test-pvc"):
    pipelineConfig = kfp.dsl.PipelineConf()
    pipelineConfig.set_image_pull_policy("Always")
    
    input_volumes = json.dumps([f"{claimname}@dataset://{dataset}/{version}"])
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
        pvolumes={"/titanic-test/": kfp.dsl.PipelineVolume(pvc=claimname)},
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
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijc0YmNkZjBmZWJmNDRiOGRhZGQxZWIyOGM2MjhkYWYxIn0.eyJ1c2VybmFtZSI6Im9jIiwicm9sZSI6ImRhdGFzY2llbnRpc3QsbWxlLHBlLG9wZXJhdG9yIiwiZXhwIjo0ODQ0NTIzOTc3LCJpYXQiOjE2MDQ1MjM5NzcsImlzcyI6IkRLdWJlIn0.j-9ZJMuD9DKSU-JE-MyBVPxPqNu4jW-4_KZYS6kHoNw2ju0qvot6oqQ6aD6aQd2gQHFH3Zf-deNt-PPzKlG1vex0cnb5qPeew_dJa7JCwt9YSrXcpajhE_-GDwVrlJpauBfo_sardhrqwvp--mEh8i0wWDZeP8mW11pUdv2IctcxZks7MI7C2ocooZ90yZzcOlmeK6YHqSLa6uyjGFlaA5fj2HuE4A3EE8bxJbnRUujuRs5skhrY-BnU00DrlLNQqGzNuxmk1J9EOnCZz8GqPnvIBJFdHsGVMAY1jOh1BEePX4ONv8ETQoTsIfK8CJ3aM1rkAlGNsq8v9B454IWuqQ"
    args = {
        "token": token,
        "project_id": "up88n1",
        "dataset": "oc:titanic-test",
        "version": "1604525752527",
        "claimname": "titanic-test-pvc"
    }
    kfp.Client().create_run_from_pipeline_func(titanic_pipline, arguments=args)
