#!/bin/bash

# Function app and storage account names must be unique.
DIGITS=$RANDOM
location=westus2
resourceGroup=$1
storageName=${resourceGroup}storage${DIGITS}
functionAppName=${resourceGroup}funcapp${DIGITS}
pythonVersion=3.6
customVisionTrainer=${resourceGroup}visiontrainer${DIGITS}
customVisionPredictor=${resourceGroup}visionpredictor${DIGITS}
rbacAppName=${resourceGroup}appcred${DIGITS}
subscriptionId=$(az account get-access-token --query subscription | tr -d \")


####### INFRA
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
                                    --sku S0 \
                                    --yes

# Create Custom Vision Prediction Service
az cognitiveservices account create --kind CustomVision.Prediction \
                                    --location $location \
                                    --name $customVisionPredictor \
                                    --resource-group $resourceGroup \
                                    --sku S0 \
                                    --yes
######### APP
# CustomVision
# => Install package
pip install azure-cognitiveservices-vision-customvision

# => Get key/endpoint
trainingKey=$(az cognitiveservices account keys list --name $customVisionTrainer --resource-group $resourceGroup --query key1 | tr -d \")
apiEndpoint=$(az cognitiveservices account show --name $customVisionTrainer --resource-group $resourceGroup --query endpoint | tr -d \")

# => Create CustomVision Project
projectId=$(python -c "from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient;print(CustomVisionTrainingClient('$trainingKey', endpoint='$apiEndpoint').create_project('seer', domain_id='0732100f-1a38-4e49-a514-c9b44c697ab5', classification_type='Multiclass').id)")


# enable static websites
az storage blob service-properties update --account-name $storageName \
                                          --static-website \
                                          --404-document 404.html \
                                          --index-document index.html

# Create images container
export AZURE_STORAGE_ACCOUNT=$storageName
export AZURE_STORAGE_KEY=$(az storage account keys list --account-name $storageName --resource-group $resourceGroup --query [0].value | tr -d \")
az storage container create --name images

# set up azfunc app settings
az webapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings StorageAccount=$storageName StorageContainer=images StorageAccountKey=$AZURE_STORAGE_KEY TrainingKey=$trainingKey ApiEndpoint=$apiEndpoint ProjectId=$projectId


# Get Azure Credentials
az ad sp create-for-rbac --name $rbacAppName --role contributor \
                            --scopes /subscriptions/$subscriptionId/resourceGroups/$resourceGroup \
                            --sdk-auth > creds.json

cat creds.json