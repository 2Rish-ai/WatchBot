import database
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

mtcnn = MTCNN(image_size=160)
facenet = InceptionResnetV1(pretrained="vggface2").eval()


def save_embeddings(user_id, person_name, file_paths):
    db = database.connect_to_db()
    cur = db.cursor()

    embeddings = []

    for file_path in file_paths:
        img = Image.open(file_path).convert("RGB")
        img_tensor = mtcnn(img)

        if img_tensor is None:
            continue

        with torch.no_grad():
            embedding = facenet(img_tensor.unsqueeze(0))[0]
            embeddings.append(embedding)

    if not embeddings:
            return
    
    avg_embedding = torch.stack(embeddings).mean(dim=0)
    embedding_list = avg_embedding.tolist()

    cur.execute("""
            INSERT INTO embedding_table (user_id, person_name, embedding)
            VALUES (%s, %s, %s)
            """, (user_id, person_name, embedding_list))

    db.commit()
    cur.close()
    db.close()
# test

def detect_faces(user_id):
    import Detect
    Detect.run_live_detection(user_id)
