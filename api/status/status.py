import os
import json
import logging
import azure.functions as func
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient

trainingKey = os.environ["TrainingKey"]
apiEndpoint = os.environ["ApiEndpoint"]
projectId = os.environ["ProjectId"]

def to_json(iteration):
    return {
        'id': iteration.id,
        'status': str(iteration.status),
        'last_modified': str(iteration.last_modified),
        'trained_at': str(iteration.trained_at),
        'project_id': str(iteration.project_id),
        'exportable': str(iteration.exportable),
        'exportable_to': iteration.exportable_to,
        'domain_id': str(iteration.domain_id),
        'classification_type': str(iteration.classification_type),
        'training_type': str(iteration.training_type),
    }

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    iterationId = req.route_params['iterationId']

    logging.info(f'Method: {req.method}')
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204,                             
                             headers={ 
                                 'Access-Control-Allow-Headers': 'content-type',
                                 'Access-Control-Allow-Methods': 'POST',
                                 'Access-Control-Max-Age': '180',
                                 'Access-Control-Allow-Origin': '*' })

    response = {}
    try:
        # prep trainer
        trainer = CustomVisionTrainingClient(trainingKey, apiEndpoint)
        iteration = trainer.get_iteration(projectId, iterationId)
        response = to_json(iteration)

    except Exception as error:
        logging.exception('Python Error')
        response['error'] = { 
            'code': '500',
            'message': f'{type(error).__name__}: {str(error)}',
            'type': 'Python Error'
        }

    return func.HttpResponse(body=json.dumps(response),
                            status_code=200,                             
                            headers={ 'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*' })