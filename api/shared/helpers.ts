
export interface ImageItem {
  type: string,
  image: string
}

export function convertBase64ToBinary(dataString) {
  var matches = dataString.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
  return new Buffer(matches[2], 'base64');
}