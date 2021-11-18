import json
import logging

import inference

# Loads the model when the lambda starts up
net = inference.load_model()


def handler(event, context):
    global net
    try:
        return inference.infer(event['uri'], net)
    except Exception as e:
        logging.error(f'Could not perform inference on payload {event}', e)
        return json.dumps({'error': 'Unable to perform inference!'})
