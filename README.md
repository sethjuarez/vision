# Welcome to the Azure Vision Workshop!

This workshop is a segment from the Ignite 2019 App Developer Keynote: "[App Development for Everyone](https://youtu.be/h9YaYdoqiRA?t=3890)" by Scott Hanselman and Seth Juarez. 


In the Keynote Scott built a "[Rock, Paper, Scissors, Lizard, Spock](https://github.com/microsoft/RockPaperScissorsLizardSpock)" web application in multiple languages which also includes the content from this workshop using [Azure CustomVision](https://www.customvision.ai/).

In this workshop we will build an end to end CustomVision solution that will demonstrate the infrastrucure required in Azure and how to build and train a custom vision based model. This workshop will not require any previous development experience and can be executed from any laptop with a modern browser (Edge, Chrome, Firefox, etc...)

Pre-requisites for this workshop are:
1. Browser with Internet Access
2. A [GitHub](https://www.github.com) Account
3. A [Microsoft](https://signup.live.com/) personal account (can register with live.com, outlook.com, gmail.com, etc...)
3. An [Azure](https://www.microsoftazurepass.com/) Account (passes will be provided for this workshop)
4. Excitement to build an AI Model!!!! :+1: :sparkles: :camel: :tada:
:rocket: :metal: :octocat: 

---
**Make sure you DO NOT use your WORK or SCHOOL account, You MUST use the Azure Pass provided and a Microsoft Personal Account**
---

## Step 0 - Get access to Azure
Create your Azure Pass Account by going to this website:
https://www.microsoftazurepass.com

Please follow the directions [here](https://www.microsoftazurepass.com/Home/HowTo?Length=5) to set-up your Azure Pass

It is recommended you perform this step before the workshop. Once you complete the process it may take a few minutes for the subscription to be activated.

You can log into Azure at:
https://portal.azure.com

**Please make sure you use the credentials you used to sign-up for the Azure Pass to sign-in. If your browser has cached Work or School credentials already, then you may want to use a Private browser session to access the portal.**

## Local Environment Notes
You can use either the [Azure Cloud Shell](https://shell.azure.com) or your local terminal to perform this workshop. It is recommended to use the Cloud Shell as all the dependencies are already installed.

If you choose to use your local environment please ensure:

1. Python 3.7.6 and Pip3 are installed 
2. python and pip are linked to Python3 and Pip3
2. [Azure Command Line Interface](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) is installed
3. Git is installed
4. You know how to use the tools above as instructions below will focus on the Cloud Shell

**For Windows, you must have Windows Subsystem for Linux installed**


## Step 1 - Deploy Resources

In this step we will get access to the Git repo for this workshop and deploy the infrasructure necessary to support CustomVision.

The services that will be deployed are all Platform as a Service and very lightweight:
1. [Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview): Contains a single method to save the UI data to Custom Vision
2. [Azure Storage](https://docs.microsoft.com/en-us/azure/storage/common/storage-introduction): Static Website to host the UI page and store the images
3. [CustomVison Service](https://www.customvision.ai/): The service stub in Azure that will train the model.
4. [Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview): An APIM for Azure Web Services.

Here is an architectural view of the solution that is deployed in this workshop:

![ARCH](/imgs/visionarch.png)

1. Via GitHub actions the client code will be deployed as a static website. The api code will be deployed as an Azure Function.

Some configuration steps will occur in the workshop below to connect the solution together.

2. User loads website and creates images to be trained
3. User submits training data which calls the Azure Function, save method.
4. The save method stores the images in the blob storage account which is accessible by Custom Vision.
5. User opens the Custom Vision portal to perform the training.
6. User downloads the TensorFlow.js client side file which contains the trained model. The model is manually uploaded to the website.
7. User reloads the web page

Now on to the deployment ...

To expedite this portion of the workshop a bash shell script was created that runs the Azure CLI to deploy the resources. You can view [deploy.sh](https://github.com/sethjuarez/vision/blob/master/deploy.sh) to see the infrastructure setup.  

### **Instructions:**
1. Sign-in to Github and fork this repo
2. Sign-in to the Azure Portal at: https://portal.azure.com
3. Open the Azure Shell

![SHELL](/imgs/01-CloudShell.png)

**NOTE:** The first time you run the Azure Cloud Shell, a wizard will pop up, asking you to set-up a storage account for persistent storage. Just select the default options and click OK.

4. Clone the repo:

    ```
    git clone (your repo)
    ```

IF you cloned locally, upload the file "deploy.sh" to Azure Cloud Shell:

![UPLOAD](/imgs/02-uploaddeploysh.png)

5. Run deploy.sh with a unique name.

```
sh deploy.sh {uniquename}

example:

sh deploy.sh superwiz123
```

Lots of scrolling output....
Wait for it to complete. It will take a few minutes.

![OUT](/imgs/03-terminalout.png)

Once the output completes, you will see the secrets necessary to perform the next step. These values are also stored in a local text file (creds.txt). These values are very important for the next step!

The unique name you used above is the name of the Resource Group in Azure where the resources were deployed. Go to the resource group in the Azure Portal to verify all the resources were created successfully:

![RESOURCES](/imgs/04-resourcegroup.png)

You can search for "Resource Groups" in the top search bar if you cannot find yours.

## Step 2 - Let's add some secrets, ssshh!! ;)

Let's setup the keys necessary for the Azure services to authorize communication with one another.

### **Instructions:**
1. In GitHub go to "Settings" and then select "Secrets"  

![SECRETPAGE](/imgs/05-secrets.png)

2. For each of the secret values that were output in Step 1.5 above, create a secret in GitHub. 

- Add new secret
    - NAME: FUNC_APP
    - VALUE: {name of function app}
- Add new secret
    - NAME: STORAGE_ACCOUNT
    - VALUE: {storage account value}
- Add new secret
    - NAME: STORAGE_KEY
    - VALUE: {storage key value}
- Add new secret
    - NAME: CREDENTIALS
    - VALUE: {paste the entire JSON including curly braces}

The final result after saving each secret should look like this:

![SECRETS](/imgs/06-secretsout.png)


3. We need to update the web application configuration for the function app save endpoint so the save function will work.

First go to the function app in the resource group:

![FUNCAPP](/imgs//07-functionapp.png)

Then, copy the URL for the endpoint

![FUNCURL](/imgs/08-funcurl.png)

Now we need to update the config file for the application.

If you are using Azure Cloud Shell you can use the built-in editor:

![EDITOR](/imgs/10-basheditor.png)

If you are using your local machine, use your favorite editor

and open the following file:

/client/public/config.json

![CONFIG](/imgs/11-configjson.png)

And then we are going to replace the first portion of the URL with the function app URL you copied above:

![NEWURL](/imgs/12-newurl.png)

4. Let's save and push your changes to the repo:

```
git add .

git commit -m "Added the endpoint"

git push origin master

```
**NOTE:** is git configured for your forked environment?
Make sure you set the git remote

**If you would rather not use the Git command line you can edit directly in Git itself.**

Ok, finally let's git outta here

## Step 3 - Trigger Builds

We are going to set-up some pretty sweet CI/CD using GitHub actions.

Actually, it is already set-up for you ;)

When you changed a file in the repo, it automatically kicked off the build. With the secrets in place, the build can happen automagically.

![FULLCI](/imgs/13-FullCI.png)

Click on "full ci" and take a look at the process status yourself as an exercise.


## Step 4 - Let's Play

We are finally ready to enjoy the fruits of our labor and load up the application. But we are missing something, perhaps the URL to execute. Can anyone figure out the URL on their own?

Need a hint? ok follow, me ....

1. Go back to the Resource Group and find the Storage Account

![STORAGE](/imgs/14-Storage.png)

2. Go to Static Websites in the left hand pane and pull out the URL in the window that comes up

![STORAGEURL](/imgs/15-storageurl.png)

and App On

![APPON](/imgs/16-appon.png)

Now the super fun part, we have to capture images to train the model. There will be a model error first load. That is because you have not created the model yet. First we need to create the images that will be inputs to train the model.

Follow the directions on the screen to capture images of yourself performing "rock", "paper", "scissors".

## Step 5 - Training Day

Ok, everyone on the floor and give me 50....

Ok, maybe not. Instead let's train the model we created.

1. Go to https://www.customvision.ai/projects and log-in with the same credentials you used to access the portal.

2. Open the "Seer" project

![SEER](/imgs/17-seer.png)

3. Click on "Train" and select "Quick Training"

![TRAIN](/imgs/18-train.png)

4. Click on "Export", Select "TensorFlow" and then choose "TensorFlow JS" from the dropdown.

![TFJS](/imgs/19-tensorflow.png)

5. Click on "Export" and then "Download"

![EXPORT](/imgs/20-export.png)

## Step 6 - Upload the model

1. The model that was downloaded is a pre-packaged set of files in zip file. Extract the contents of the zip file to a folder

![ZIP](/imgs/21-zipfile.png)

2. Go back to the Storage account and open "Containers" and then open the  "$Web" folder

![CONTAINER](/imgs/23-containers.png)

![WEB](/imgs/24-web.png)

The point here is that the static web site that was created to host the web application lives in a container. We need to upload the model to the website so when we next load the application it includes the model.

3. Once inside the $Web folder. Click on "Upload" and select all the files you extracted to a folder.

![UPLOAD](/imgs/25-upload.png)

4. Once uploaded, go back to your website URL in the browser, refresh the page and you should see the model "ERROR' message changed to "NONE". Which means it is now recognizing the "None" action you trained earlier.

![REFRESH](/imgs/26-refresh.png)

Go ahead and play with the application now, make goofy faces, use the different hand symbols you trained for rock, paper, and scissors and check the scoring results.

-----
HINTS

A [video walkthrough](https://visionworkshop32904.blob.core.windows.net/public/instructions.mp4) of the entire process

