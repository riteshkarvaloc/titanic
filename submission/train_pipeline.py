import json

import kfp
from kubernetes.client.models import V1EnvVar


class ContainerOp(kfp.dsl.ContainerOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_pod_label(name="platform", value="Dkube")
        self.add_pod_label(name="dkube.garbagecollect", value="true")
        self.add_pod_label(name="dkube.garbagecollect.policy", value="all")

@kfp.dsl.pipeline(
    name="Titanic pipeline (User)",
    description="A pipline showing how to use evaluation component",
)
def titanic_pipline(token, project_id, claimname):
    pipelineConfig = kfp.dsl.PipelineConf()
    pipelineConfig.set_image_pull_policy("Always")

    train_op = ContainerOp(
        name="train",
        image="ocdr/dkubepl:2.2.1.1",
        command=["dkubepl", "training", "--token", token, "--container", '{"image":"ocdr/dkube-datascience-tf-cpu:v2.0.0"}',
                "--framework", "tensorflow", "--version", "2.0.0", "--tags", f'["project:{project_id}"]',
                "--script", "python train.py", "--program","titanic",
                "--outputs",'["titanic"]', "--output_mounts",'["/opt/dkube/output"]',
                "--runid", '{{pod.name}}', "--wfid", '{{workflow.uid}}'
            ],
    )
    train_op.add_pod_label(name="stage", value="training")

    predict_op = ContainerOp(
        name="predict",
        image="ocdr/titanic_submission",
        command=["python", "predict.py"],
        pvolumes={"/titanic-test/": kfp.dsl.PipelineVolume(pvc=claimname)},
        file_outputs={"output": "/tmp/prediction.csv"},
    )
    predict_op.after(train_op)

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
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijc0YmNkZjBmZWJmNDRiOGRhZGQxZWIyOGM2MjhkYWYxIn0.eyJ1c2VybmFtZSI6Im9jZGt1YmUiLCJyb2xlIjoiZGF0YXNjaWVudGlzdCxtbGUscGUsb3BlcmF0b3IiLCJleHAiOjQ4NDY0ODY1NjQsImlhdCI6MTYwNjQ4NjU2NCwiaXNzIjoiREt1YmUifQ.hCg_enrkSYPEXTxsAyhPUFfynaovXnUG3aLjwb5izNAup_69nQQcvalCWvEl2lZXY5DB9qUHYfEetrHM-95CPSepmMBkhj9JUmod4m8jB2hU1q6Ezi_DOuuzIm0_xQS1F6PSsTrOPZPNs7vSEYA0OJid9KfTCefgb7OeqxfEL0pklz2bXWctc6Il_aln1SAwu6KTd8o7Qx6GVsPgu97GxV-3KyBktEB4lOpuGzp41amQE3NBpnNZN7mqMyOmsdJajRd_iYjwO-ivzu3syMU4RCwxBy9YzLVBpkQuHGt1SKRVxSKre-dJQAvQmOPDkWF6daNUF67XKxvtdf1HpEf5sw"
    args = {
        "token": token,
        "project_id": "szs1tg",
        "claimname" : "titanic-test-pvc"
    }
    kfp.Client().create_run_from_pipeline_func(titanic_pipline, arguments=args)
