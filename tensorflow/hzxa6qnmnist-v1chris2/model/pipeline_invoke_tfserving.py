import os
import numpy as np
import json
import logging

from pipeline_model import TensorFlowServingModel
from pipeline_monitor import prometheus_monitor as monitor
from pipeline_logger import log

import tensorflow as tf

_logger = logging.getLogger('pipeline-logger')
_logger.setLevel(logging.INFO)
_logger_stream_handler = logging.StreamHandler()
_logger_stream_handler.setLevel(logging.INFO)
_logger.addHandler(_logger_stream_handler)


__all__ = ['invoke']


_labels = {
           'model_name': 'hzxa6qnmnist',
           'model_tag': 'v1chris2',
           'model_type': 'tensorflow',
           'model_runtime': 'tfserving',
           'model_chip': 'cpu',
          }


def _initialize_upon_import():
    ''' Initialize / Restore Model Object.
    '''
    return TensorFlowServingModel(host='localhost',
                                  port=9000,
                                  model_name='hzxa6qnmnist',
                                  model_signature_name=None,
                                  timeout_seconds=10.0)


# This is called unconditionally at *module import time*...
_model = _initialize_upon_import()


# Schema
#   input: bytes
#   return: json
@log(labels=_labels, logger=_logger)
def invoke(request):
    """Where the magic happens..."""

    with monitor(labels=_labels, name="transform_request"):
        transformed_request = _transform_request(request)

    with monitor(labels=_labels, name="invoke"):
        response = _model.predict(transformed_request)

    with monitor(labels=_labels, name="transform_response"):
        transformed_response = _transform_response(response)

    return transformed_response


# input: bytes
# return: dict
def _transform_request(request):
    request_str = request.decode('utf-8')
    request_json = json.loads(request_str)
    request_np = ((255 - np.array(request_json['image'], dtype=np.uint8)) / 255.0).reshape(1, 28, 28)
    image_tensor = tf.make_tensor_proto(request_np, dtype=tf.float32)
    return {"image": image_tensor}


# input: dict
# return: json
def _transform_response(response):
    return json.dumps({"classes": response['classes'].tolist(),
                       "probabilities": response['probabilities'].tolist(),
                      })