import glob
import logging
import os

import gluoncv
import mxnet
import mxnet as mx
import requests
from gluoncv.data.transforms.presets import imagenet


def load_model(model_path = None):
    """
    Loads a model from model_path, if found, or a pretrained model specified in
    the MODEL_NAME environment variable.
    """

    # Try to load a model specified in the model_path if we are running on sagemaker.
    if model_path and os.path.exists(model_path):
        symbol_file = glob.glob(os.path.join(model_path, '*symbol.json'))[0]
        params_file = glob.glob(os.path.join(model_path, '*.params'))[0]
        logging.info(f"Loading model {symbol_file} with params {params_file}")
        return mx.gluon.nn.SymbolBlock.imports(symbol_file, 'data', params_file)
    else:
        model_name = os.environ.get('MODEL_NAME', 'mobilenetv3_large')
        logging.info(f"No local model found, download loading model {model_name}")
        return gluoncv.model_zoo.get_model(model_name, pretrained=True, root='/tmp/')


def open_image(uri):
    """
    Downlaods an image and decompresses it into rgb pixels.
    """
    content = requests.get(uri).content
    return mxnet.image.imdecode(content, flag=1).astype('uint8')


def infer(uri, net):
    """
    Performs inference on the image pointed to in `uri.`
    """

    # Download and decompress the image
    img = open_image(uri)

    # Preprocess the image
    transformed_img = imagenet.transform_eval(img)

    # Perform the inference
    pred = net(transformed_img)
    prob = mxnet.nd.softmax(pred)[0].asnumpy()
    ind = mxnet.nd.topk(pred, k=5)[0].astype('int').asnumpy().tolist()

    # accumulate the results
    if hasattr(net, 'classes'):
        results = [{'label': net.classes[i], 'prob': str(prob[i])} for i in ind]
    else:
        results = [{'label': i, 'prob': str(prob[i])} for i in ind]

    # Compose the results
    return {'uri': uri, 'results': results}
