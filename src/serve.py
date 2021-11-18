import argparse
import json
import logging

from flask import Flask, Response, request

import inference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP Server
app = Flask(__name__)

# The neural network
net = None


@app.route("/ping", methods=["GET"])
def ping():
    return Response(response="\n", status=200)

@app.route("/invocations", methods=["POST"])
def predict():
    # parse payload
    try:
        lines = request.data.decode()
        data = json.loads(lines)
    except ValueError as e:
        error_message = f"Parsing request payload failed with error '{e}'"
        logger.exception(error_message)
        return Response(response=error_message, status=400)

    # do prediction
    try:
        results = inference.infer(data['uri'], net)
        logging.info(f'Results: {results}')
    except ValueError as e:
        error_message = f"Prediction failed with error '{e}'"
        logger.exception(error_message)
        return Response(response=error_message, status=400)
    output = json.dumps(results)
    return Response(response=output, status=200)


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Performs inference on an image file using a provided model.'
    )
    parser.add_argument(
        "--model-path", type=str, default='/opt/ml/model', help="The model artifact to run inference on."
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to run the server on."
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to run the server on."
    )
    return parser.parse_args(args)


if __name__ == "__main__":
    # parse command line arguments
    args = parse_args()
    # load the model
    net = inference.load_model(args.model_path)
    # start the server
    app.run(host=args.host, port=args.port)
