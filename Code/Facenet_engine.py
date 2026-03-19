import database
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

# B4: MTCNN detects and crops faces from uploaded images, resizing to 160x160 for FaceNet input
mtcnn = MTCNN(image_size=160)
# B6: FaceNet (InceptionResnetV1) pretrained on VGGFace2 generates 512-dimensional face embeddings
facenet = InceptionResnetV1(pretrained="vggface2").eval()

def save_embeddings(user_id, person_name, file_paths):
    db = database.connect_to_db()
    cur = db.cursor()

    embeddings = []

    for file_path in file_paths:
        # B4: Open each image, convert to RGB, and pass through MTCNN to detect and crop the face
        img = Image.open(file_path).convert("RGB")
        img_tensor = mtcnn(img)

        # B5: Skip any image where no face is detected by MTCNN (img_tensor is None)
        if img_tensor is None:
            continue

        # B6: Generate a 512-dimensional embedding for each detected face using FaceNet
        with torch.no_grad():
            embedding = facenet(img_tensor.unsqueeze(0))[0]
            embeddings.append(embedding)

    if not embeddings:
            return

    # B7: Calculate the mean embedding across all images — stacks all tensors and computes mean(dim=0)
    # This produces a single representative embedding that is more robust than any individual image
    avg_embedding = torch.stack(embeddings).mean(dim=0)
    embedding_list = avg_embedding.tolist()

    # B8: Delete existing embedding for this person under the same user, then replace with the new mean embedding
    cur.execute("DELETE FROM embedding_table WHERE user_id = %s AND person_name = %s", (user_id, person_name))
    # B9: Store the mean embedding in the embedding_table in PostgreSQL, linked to user_id and person_name
    cur.execute("""
            INSERT INTO embedding_table (user_id, person_name, embedding)
            VALUES (%s, %s, %s)
            """, (user_id, person_name, embedding_list))
    db.commit()
    cur.close()
    db.close()