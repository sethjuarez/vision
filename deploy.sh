#!/bin/bash

# Function app and storage account names must be unique.
location=westus2
resourceGroup=$1
storageName=$1storage
functionAppName=$1funcapp
pythonVersion=3.6 #3.7 also supported
customVisionTrainer=$1visiontrainer
customVisionPredictor=$1visionpredictor

# Create a resource group.
az group create --name $resourceGroup \
                --location $location

# Create an Azure storage account in the resource group.
az storage account create --name $storageName \
                          --location $location \
                          --resource-group $resourceGroup \
                          --sku Standard_LRS \
                          --kind StorageV2

# Create a serverless function app in the resource group.
az functionapp create --name $functionAppName \
                      --storage-account $storageName \
                      --consumption-plan-location $location \
                      --resource-group $resourceGroup \
                      --os-type Linux \
                      --runtime python \
                      --runtime-version $pythonVersion

# Create Custom Vision Training Service
az cognitiveservices account create --kind CustomVision.Training \
                                    --location $location \
                                    --name $customVisionTrainer \
                                    --resource-group $resourceGroup \
                                    --sku S0
                                    --yes

# Create Custom Vision Prediction Service
az cognitiveservices account create --kind CustomVision.Prediction \
                                    --location $location \
                                    --name $customVisionPredictor \
                                    --resource-group $resourceGroup \
                                    --sku S0 \
                                    --yes