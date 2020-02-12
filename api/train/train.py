import os
import json
import logging
import datetime
import azure.functions as func
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import CustomVisionErrorException

# for pushing to customvision
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

    logging.info(f'Method: {req.method}')
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204,                             
                             headers={ 
                                 'Access-Control-Allow-Headers': 'content-type',
                                 'Access-Control-Allow-Methods': 'POST',
                                 'Access-Control-Max-Age': '180',
                                 'Access-Control-Allow-Origin': '*' })
    response = {}
    trainer = CustomVisionTrainingClient(trainingKey, apiEndpoint)
    try:
        # prep trainer
        iteration = trainer.train_project(projectId)
        response = to_json(iteration)

    except CustomVisionErrorException as cvError:
        logging.exception('CustomVisionErrorException Error')
        
        # get last iteration
        iterations = trainer.get_iterations(projectId)
        iteration = None
        for i in iterations:
            if iteration == None:
                iteration = i
            elif iteration.last_modified > i.last_modified:
                iteration = i

        response = to_json(iteration)

        response['error'] = { 
            'message': cvError.message,
            'type': 'CustomVisionErrorException'
        }

    except Exception as error:
        logging.exception('Python Error')
        response['error'] = { 
            'message': f'{type(error).__name__}: {str(error)}',
            'type': str(type(error))
        }


    return func.HttpResponse(body=json.dumps(response),
                             status_code=200,                             
                             headers={ 'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*' })