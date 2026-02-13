import database
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

mtcnn = MTCNN(image_size=160)
facenet = InceptionResnetV1(pretrained="vggface2").eval()

#  Get values from user about the person name to be added and the neccessary fie path to access 
def save_embeddings(user_id, person_name, file_paths):
    #  Acess the database
    db = database.connect_to_db()
    cur = db.cursor()

    embeddings = []

    # Open the files from the file path added by the User 
    for file_path in file_paths:
        img = Image.open(file_path).convert("RGB")
        img_tensor = mtcnn(img)

        if img_tensor is None:
            continue

        # Get the face embedding from applying facenet functon 
        with torch.no_grad():
            embedding = facenet(img_tensor.unsqueeze(0))[0]
            embeddings.append(embedding)

    if not embeddings:
            return
    
    # Get an average face embedding which allows less data to be used and more accurate
    avg_embedding = torch.stack(embeddings).mean(dim=0)
    embedding_list = avg_embedding.tolist()

    # Delete existing embedding for this person if it exists, then insert new one
    cur.execute("DELETE FROM embedding_table WHERE user_id = %s AND person_name = %s", (user_id, person_name))
    cur.execute("""
            INSERT INTO embedding_table (user_id, person_name, embedding)
            VALUES (%s, %s, %s)
            """, (user_id, person_name, embedding_list))
    # close the database
    db.commit()
    cur.close()
    db.close()