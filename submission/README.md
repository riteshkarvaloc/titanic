# How to build a kubeflow pipeline to submit prdictions

This repo has example pipeline for [Project Owner](owner_pipeline.py) and [Data-scientist](user_pipeline.py) here. For building your own pipeline, you can follow these steps:

1. In your pipeline file, define a ContainerOp function as below: 

```
class ContainerOp(kfp.dsl.ContainerOp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_pod_label(name="dkube.garbagecollect", value="true")
        self.add_pod_label(name="dkube.garbagecollect.policy", value="all")
        self.add_pod_label(name="runid", value="{{pod.name}}")
        self.add_pod_label(name="wfid", value="{{workflow.uid}}")
```

2. Add two pipeline parameters `token` and `project_id`. These will get autopopulated while creating RUN in kubeflow pipeline UI.

3. Project owner needs to first run a pipeline which exports Test dataset as PVC. This allows other users to access the dataset in their pipelines. This step is not required for non-owner of the dataset.  To export the dataset add following component in the pipeline:

```
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
```
* dataset   - name of the dataset which owner wants to make it available to other users.
* version   - numerical version of the dataset (of form 1604525752527) (Note: v1,v2 version names will be supported later)
* claimname - A name which can be shared with other users to access this dataset. Name can only contain [a-zA-Z0-9-] and cannot begin with a hypen and numeric.

4. Access the dataset in any of kubeflow component by providing the pvolumes argument. Example

```
    predict_op = ContainerOp(
        name="predict",
        image="ocdr/titanic_submission",
        command=["python", "predict.py"],
        pvolumes={"/titanic-test/": kfp.dsl.PipelineVolume(pvc=claimname)},
        file_outputs={"output": "/tmp/prediction.csv"},
    )
```

5. Submit the prediction from a pipeline component's output to leaderboard using following component:

```
    predictions = kfp.dsl.InputArgumentPath(predict_op.outputs["output"])
    submit_op = ContainerOp(
        name="submit",
        image="ocdr/d3project_eval",
        command=[
            "python",
            "submit.py",
            "-t",
            token,
            predictions,
        ],
        file_outputs={
            "mlpipeline-ui-metadata": "/metadata.json",
            "results": "/results",
        },
    )
```
