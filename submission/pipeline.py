import kfp
from kubernetes.client.models import V1EnvVar


@kfp.dsl.pipeline(
    name="Titanic Experiment pipeline",
    description="A pipline showing how to use evaluation component",
)
def titanic_pipline(token):
    pipelineConfig = kfp.dsl.PipelineConf()
    pipelineConfig.set_image_pull_policy("Always")

    predict_op = kfp.dsl.ContainerOp(
        "predict",
        image="ocdr/titanic_submission",
        command=["python", "predict.py"],
        file_outputs={"output": "/tmp/prediction.csv"},
    )
    predictions = kfp.dsl.InputArgumentPath(predict_op.outputs["output"])
    submit_op = kfp.dsl.ContainerOp(
        "submit",
        image="ocdr/d3project_eval",
        command=["python", "submit.py", "-t", token, predictions],
        file_outputs={"mlpipeline-ui-metadata": "/metadata.json"},
    )
    env_var = V1EnvVar(name="DKUBE_PROJECT_ID", value="p123")
    submit_op.add_env_variable(env_var)


token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijc0YmNkZjBmZWJmNDRiOGRhZGQxZWIyOGM2MjhkYWYxIn0.eyJ1c2VybmFtZSI6Im9jIiwicm9sZSI6ImRhdGFzY2llbnRpc3QsbWxlLHBlLGRhdGEtZW5naW5lZXIsY2F0YWxvZy1hZG1pbixkYXRhLWFuYWx5c3Qsb3BlcmF0b3IiLCJleHAiOjQ4NDIzMjgwMjQsImlhdCI6MTYwMjMyODAyNCwiaXNzIjoiREt1YmUifQ.DzZYBg5xCYTIrtcwpdFIfRNzX5jPJoCAbY4t8hW-x24tNcpkO2geyjYzbcGwOhl10it3fw8htoIHJAkUvQMNZ1TYqs7WfDMXLSewLuLHhNzTPZYI5gU6It6ei7PGO2QtSlneaCtEYjLHNr6mbRNe218YUsdNBuHCy8iIbN17tXKA4MhN-m_zjR8T_clSBAtxhYaSO2sdjtQija7TzP8mzFmlRKZxslwmhecjZ_j3b-roMKcTNVyHauClFyJ9ld6V-9_bRE8jzVPaogXulrotNK42hVdtbI78thuHJWBse7XAqbyVNKJoM6kQti5N8ECBJDEdK_La2TEOP3oSODaYVg"
kfp.Client().create_run_from_pipeline_func(titanic_pipline, arguments={"token": token})
