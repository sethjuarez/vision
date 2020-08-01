import { ApiKeyCredentials } from "@azure/ms-rest-js"
import { TrainingAPIClient, TrainingAPIMappers } from "@azure/cognitiveservices-customvision-training"
import { AzureFunction, Context, HttpRequest } from "@azure/functions"
import { ImageItem, convertBase64ToBinary } from "../shared/helpers"
import { v4 as uuidv4 } from 'uuid';

const httpTrigger: AzureFunction = async function (context: Context, req: HttpRequest): Promise<void> {
  context.log("JavaScript HTTP trigger function processed a request.");

  // environment variables
  const trainingKey = process.env.TrainingKey;
  const apiEndpoint = process.env.ApiEndpoint;
  const projectId = process.env.ProjectId;

  // custom vision api
  const credentials = new ApiKeyCredentials({ inHeader: { "Training-Key": trainingKey }});
  const trainer = new TrainingAPIClient(credentials, apiEndpoint);

  // make sure we have the right tags
  const desiredTags = ["none", "rock", "paper", "scissors"];
  const actualTags = await trainer.getTags(projectId);
  const tags = { }
  actualTags.forEach(t => tags[t.name] = t);
  for (const t of desiredTags){
    if(!tags.hasOwnProperty(t)) {
      tags[t] = await trainer.createTag(projectId, t);
    }
  }

  // post images
  const items = <ImageItem[]>req.body.items;
  const images = items.map(item => ({
    name: `${uuidv4()}.png`,
    contents: convertBase64ToBinary(item.image),
    tagIds: [tags[item.type].id]
  }));

  const result = await trainer.createImagesFromFiles(projectId, { images: images });
  
  console.log(result);

  context.res = {
    status: 200,
    body: "Success!"
  };
};

export default httpTrigger;