import os
import json
import logging
import datetime
import azure.functions as func
from azure.storage.blob import BlockBlobService
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import CustomVisionErrorException

storageAccount = os.environ["StorageAccount"]
storageAccountKey = os.environ["StorageAccountKey"]
# for static website
storageContainer = '$web'

# for pushing to customvision
trainingKey = os.environ["TrainingKey"]
apiEndpoint = os.environ["ApiEndpoint"]
projectId = os.environ["ProjectId"]


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
    try:

        # get access to blob storage
        blob_service = BlockBlobService(account_name=storageAccount, account_key=storageAccountKey)

        # prep trainer
        trainer = CustomVisionTrainingClient(trainingKey, apiEndpoint)

        # get last iteration
        iterations = trainer.get_iterations(projectId)
        iteration = None
        for i in iterations:
            if iteration == None:
                iteration = i
            elif iteration.last_modified > i.last_modified:
                iteration = i

        export = trainer.export_iteration(projectId, iteration.id, platform="TensorFlow", flavor="TensorFlowJs")

        response = {
            'platform': export.platform,
            'status': export.status,
            'download_uri': export.download_uri,
            'flavor': export.flavor,
            'newer_version_available': export.newer_version_available
        }


    except CustomVisionErrorException as cvError:
        logging.exception('CustomVisionErrorException Error')

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
