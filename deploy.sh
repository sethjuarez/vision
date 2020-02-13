#!/bin/bash

# Function app and storage account names must be unique.
location=westus2
resourceGroup=$1
storageName=${resourceGroup}storage
functionAppName=${resourceGroup}funcapp
pythonVersion=3.6
customVisionTrainer=${resourceGroup}visiontrainer
customVisionPredictor=${resourceGroup}visionpredictor
rbacAppName=${resourceGroup}appcred
subscriptionId=$(az account get-access-token --query subscription -o tsv)

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
trainingKey=$(az cognitiveservices account keys list --name $customVisionTrainer --resource-group $resourceGroup --query key1 -o tsv)
apiEndpoint=$(az cognitiveservices account show --name $customVisionTrainer --resource-group $resourceGroup --query endpoint -o tsv)

# => Create CustomVision Project
projectId=$(python -c "from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient;print(CustomVisionTrainingClient('$trainingKey', endpoint='$apiEndpoint').create_project('seer', domain_id='0732100f-1a38-4e49-a514-c9b44c697ab5', classification_type='Multiclass').id)")


# enable static websites
az storage blob service-properties update --account-name $storageName \
                                          --static-website \
                                          --404-document 404.html \
                                          --index-document index.html

# set CORS for function app
# remove all allowed origins for CORS
az functionapp cors remove --resource-group $resourceGroup \
                           --name $functionAppName \
                           --allowed-origins

# add static website as allowed origin to functionapp
staticUrl=$(az storage account show -n $storageName -g $resourceGroup --query "primaryEndpoints.web" --output tsv)
az functionapp cors add --resource-group $resourceGroup \
                           --name $functionAppName \
                           --allowed-origins ${staticUrl%/}

# Create images blob container
export AZURE_STORAGE_ACCOUNT=$storageName
export AZURE_STORAGE_KEY=$(az storage account keys list --account-name $storageName --resource-group $resourceGroup --query [0].value -o tsv)
az storage container create --name images

# set up azfunc app settings
az webapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings StorageAccount=$storageName StorageContainer=images StorageAccountKey=$AZURE_STORAGE_KEY TrainingKey=$trainingKey ApiEndpoint=$apiEndpoint ProjectId=$projectId

# Get Azure Credentials
creds=$(az ad sp create-for-rbac --name $rbacAppName --role contributor --scopes /subscriptions/$subscriptionId/resourceGroups/$resourceGroup --sdk-auth)
# Create secrets file
printf "GitHub Secrets\n--------------\nFUNC_APP => $functionAppName\nSTORAGE_ACCOUNT => $storageName\nSTORAGE_KEY => $AZURE_STORAGE_KEY\nCREDENTIALS =>\n$creds\n" > creds.txt
cat creds.txt
