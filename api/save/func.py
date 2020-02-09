import os
import uuid
import json
import base64
import logging
import requests
from PIL import Image
from io import BytesIO
from azure.storage.blob import BlockBlobService
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateEntry

import azure.functions as func

# for storage in blob
base_folder = 'gamedata'
storageAccount = os.environ["StorageAccount"]
storageAccountKey = os.environ["StorageAccountKey"]
storageContainer = os.environ["StorageContainer"]

# for pushing to customvision
trainingKey = os.environ["TrainingKey"]
apiEndpoint = os.environ["ApiEndpoint"]
projectId = os.environ["ProjectId"]
tags = {}

def check_tags(trainer: CustomVisionTrainingClient) -> None:
    t = ['none', 'rock', 'paper', 'scissors', 'lizard', 'spock']
    etags = { t.name: t for t in trainer.get_tags(projectId) }
    for tag in t:
        if tag in etags:
            tags[tag] = etags[tag]
        else:
            tags[tag] = trainer.create_tag(projectId, tag)

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

    body = req.get_json()

    blob_service = BlockBlobService(account_name=storageAccount, account_key=storageAccountKey)

    # prep trainer
    trainer = CustomVisionTrainingClient(trainingKey, apiEndpoint)
    #check tags
    check_tags(trainer)

    records = { 'images': [] }
    image_list = []

    try:
        for item in body['items']:
            # sign
            sign = item['type'].strip()

            # image bits
            img = base64.b64decode(item['image'].replace('data:image/png;base64,', ''))
            stream = BytesIO(img)

            # storage path + save
            image_name = f'{str(uuid.uuid4())}.png'
            blob_name = f'{base_folder}/{sign}/{image_name}'            
            sresponse = blob_service.create_blob_from_stream(storageContainer, blob_name, stream)

            logging.info(f'Storage Response: {sresponse}')

            # save to custom vision
            image_list.append(ImageFileCreateEntry(name=image_name, contents=img, tag_ids=[tags[sign].id]))


            # return image
            path = f'{blob_service.protocol}://{blob_service.primary_endpoint}/{storageContainer}/{blob_name}'
            records['images'].append({'sign': sign, 'path': path })

        # save list
        upload_result = trainer.create_images_from_files(projectId, images=image_list)
        if not upload_result.is_batch_successful:
            records['error'] = {
                'type': 'CustomVision Error',
                'items': []
            }
            for image in upload_result.images:
                records['error']['items'].append({
                    image.source_url: image.status
                })
        else:
            records['error'] = { }
    except Exception as error:
        logging.exception('Python Error')
        records['error'] = { 
            'code': '500',
            'message': f'{type(error).__name__}: {str(error)}',
            'type': 'Python Error'
        }


    return func.HttpResponse(body=json.dumps(records),
                             status_code=200,                             
                             headers={ 'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*' })
