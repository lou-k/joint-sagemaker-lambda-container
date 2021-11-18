# Joint Sagemaker And Lambda Container
A proof of concept for building a docker container that can be deployed to _both_ sagemaker and lambda. This let's you easily migrate from inference on serverless, which is pay-as-you-go, to sagemaker, which scales more cost effectively.

This example creates a container that classifies images using pretrained models in the [gluoncv model zoo](https://cv.gluon.ai/model_zoo/classification.html), but the basic concept should be extendable to your own models.

## Project Structure

* `Dockerfile` - the dockerfile used to build the image
* `Pipfile` - Pipfile containing packages to install for the inference container
* `src/enrty.sh` - Entrypoint called when the container starts
* `src/lambda.py` - The lambda entry code.
* `src/serve.py` - The sagemaker entry code.
* `src/inference.py` - The core code that actually does the inference, called by `serve.py` and `lambda.py`.
* `deploy.ipynb` - Example notebook showing how to create a sagemaker endpoint using this container.


## Building and Testing

### Bulding the Container
```shell
docker build -t joint-sm-lambda .
```

## Local Testing Of Lambda Function
The container starts in lambda mode by default. Simply map port `8080` to it:

```shell
docker run -p 8080:8080 joint-sm-lambda
```

You'll see this on the console:
```shell
Local executionn. Running Lambda Runtime Interface Emulator...
.... [INFO] (rapid) exec '/usr/local/bin/python' (cwd=/opt/app, handler=lambda.handler)
```

You can send an invocation request via curl to `/2015-03-31/functions/function/invocations`. Just specify the image to classify via a `uri` field:
```shell
curl -q -d '{"uri":"https://cv.gluon.ai/_static/classification-demo.png"}' http://localhost:8080/2015-03-31/functions/function/invocations
```

You'll see the classification results in the response:
```shell
{
  "uri": "https://cv.gluon.ai/_static/classification-demo.png",
  "results": [
    {
      "label": "Welsh springer spaniel",
      "prob": "0.5098194"
    },
    {
      "label": "cocker spaniel",
      "prob": "0.10103245"
    },
    {
      "label": "Brittany spaniel",
      "prob": "0.05170257"
    },
    {
      "label": "English setter",
      "prob": "0.039764397"
    },
    {
      "label": "clumber",
      "prob": "0.03599626"
    }
  ]
}
```

You'll see the lambda logging information in the container output:
```
START RequestId: 081bdb70-8c66-4568-9836-09af42ad78e2 Version: $LATEST
END RequestId: 081bdb70-8c66-4568-9836-09af42ad78e2
REPORT RequestId: 081bdb70-8c66-4568-9836-09af42ad78e2	Duration: 673.65 ms	Billed Duration: 674 ms	Memory Size: 3008 MB	Max Memory Used: 3008 MB
```

## Local Testing Of Sagemaker Serving
To start the container in sagemaker mode, simply pass the `serve` argument:
```shell
docker run -p 8080:8080 joint-sm-lambda serve
```

Inference can be peformed via the `invcations` endpoint:
```shell
curl -q -H "Content-Type: application/json" -d '{"uri":"https://cv.gluon.ai/_static/classification-demo.png"}' http://localhost:8080/invocations
```

You'll see the classification results in the response:
```shell
{
  "uri": "https://cv.gluon.ai/_static/classification-demo.png",
  "results": [
    {
      "label": "Welsh springer spaniel",
      "prob": "0.5098194"
    },
    ...
```

Sagemaker serving loads models from the model registry, and mounts them into your container at `/opt/ml/model`. To test this locally, just mount the directory holding your model:
```shell
docker run -p 8080:8080 -v $(pwd)/my-model:/opt/ml/model joint-sm-lambda serve
```

# Deploying

Deploying the image to both Sagemaker and Lambda requires it to be in your elastic container registry (ECR). 

Tag it and push it up:
```shell
docker tag joint-sm-lambda <repo_uri>/joint-sm-lambda:latest
```
See the [amazon documentation](https://aws.amazon.com/ecr/getting-started/) for more info on setting up ECR.

## Deploying To Lambda
Once the image is in ECR, you can [create the lambda function](https://docs.aws.amazon.com/lambda/latest/dg/configuration-images.html#configuration-images-api) as you would any other based on containers:

```shell
aws lambda create-function \
    --function-name JointSMLambda \
    --package-type Image \
    --code <repo_uri>/joint-sm-lambda:latest \
    --role <lambda_role> \
    --timeout 30 \
    --memory-size 1024
```

And then you can invoke it with:
```shell
aws lambda invoke --function-name JointSMLambda --payload '{"uri":"https://cv.gluon.ai/_static/classification-demo.png"}' /dev/stdout
```

You should see the output as:
```
{"uri": "https://cv.gluon.ai/_static/classification-demo.png", "results": [{"label": "Welsh springer spaniel", "prob": "0.5098194"}, {"label": "cocker spaniel", "prob": "0.10103245"}, {"label": "Brittany spaniel", "prob": "0.05170257"}, {"label": "Englis{ setter", "prob": "0.039764397"}, {"label": "clumber", "prob": "0.03599626"}]}
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
```
## Deploying to Sagemaker
The notebook `deploy.ipynb` has an example of creating a sagemaker endpoint using this image and the sagemaker python sdk.