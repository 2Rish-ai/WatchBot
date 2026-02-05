import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

mtcnn = MTCNN(image_size=160)
facenet = InceptionResnetV1(pretrained='vggface2').eval()

img_tensor = mtcnn(Image.open("/Users/rishiprajapati/Desktop/Projects/WATCHBot/rishi.jpg").convert("RGB"))
check_img_tensor = mtcnn(Image.open("/Users/rishiprajapati/Desktop/Projects/WATCHBot/rishi2.jpg").convert("RGB"))

with torch.no_grad():
    embedding1 = facenet(img_tensor.unsqueeze(0))
    embedding2 = facenet(check_img_tensor.unsqueeze(0))

    distance = torch.dist(embedding1,embedding2)
    print("Distance between faces:",distance.item())

