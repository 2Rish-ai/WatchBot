import cv2
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import database
import numpy as np
from tkinter import messagebox

# A7/A8: Cosine similarity threshold — scores above 0.75 = recognised, below = "Unknown"
threshold = 0.75

def setup_detection(user_id):
    db = database.connect_to_db()
    cur = db.cursor()

    # C5: Filter embeddings by user_id so each user only sees their own enrolled faces
    cur.execute(
        "SELECT person_name,embedding FROM embedding_table WHERE user_id = %s",
        (user_id,))
    known_faces = cur.fetchall()

    cur.close()
    db.close()

    # A2: Initialise MTCNN for face detection — returns bounding box coordinates (x1, y1, x2, y2) per face
    mtcnn = MTCNN(image_size=160)
    # A4: Initialise FaceNet (InceptionResnetV1 pretrained on VGGFace2) to convert faces into 512-dim embeddings
    facenet = InceptionResnetV1(pretrained="vggface2").eval()

    if not known_faces:
        messagebox.showerror("Error","No known faces for this user")
        return None

    return known_faces, mtcnn, facenet

def process_frame(frame, mtcnn, facenet, known_faces):
    # A1: Convert the captured BGR frame to RGB for MTCNN face detection
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detected_names = []

    # A2: Detect all faces in the frame using MTCNN — returns bounding box coordinates for each detected face
    boxes, _ = mtcnn.detect(img)

    # A9: Process multiple faces independently within a single frame
    if boxes is not None:
        for box in boxes:
            x1,y1,x2,y2 = [int(b) for b in box]

            # A3: Clamp bounding box coordinates to image bounds
            h, w = img.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            # A3: Skip any detected face region smaller than 20x20 pixels to avoid processing noise
            if x2 - x1 < 20 or y2 - y1 < 20:
                continue

            # A4: Extract the face region from the frame for this specific bounding box
            face_img = img[y1:y2, x1:x2]

            # A4: Pass the face region through MTCNN to crop and align the face for FaceNet
            try:
                face_tensor = mtcnn(face_img)
            except RuntimeError:
                continue

            if face_tensor is not None:
                # A4: Pass the face through FaceNet to generate a 512-dimensional embedding vector
                with torch.no_grad():
                    live_embedding = facenet(face_tensor.unsqueeze(0))[0]

                best_distance = float("-inf")
                best_name = "Unknown"

                # A5: Compare the live embedding against each stored mean embedding using cosine similarity
                for name, db_embedding in known_faces:
                    # Parse the embedding from PostgreSQL array format to a tensor
                    if isinstance(db_embedding, str):
                        db_embedding = [float(x) for x in db_embedding.strip('{}[]').split(',')]
                    db_embedding = torch.tensor(db_embedding)
                    # A5: Cosine similarity produces a score between 0 and 1
                    distance = torch.cosine_similarity(live_embedding.unsqueeze(0), db_embedding.unsqueeze(0)).item()

                    # A6: Select the known person with the highest cosine similarity score as the best match
                    if distance > best_distance:
                        best_distance = distance
                        best_name = name

                # A7: If best score exceeds 0.75, display the person's name with confidence score
                if best_distance > threshold:
                    label = f"{best_name} {best_distance:.2f}"
                # A8: If best score falls below 0.75, label the person as "Unknown"
                else:
                    label = "Unknown"
            else:
                label = "Unknown"

            is_known = label != "Unknown"
            # A7/A8: Green bounding box for recognised persons, red for unknown
            color = (0, 255, 0) if is_known else (0, 0, 255)

            cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
            cv2.putText(
                frame,
                label,
                (x1,y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )

            # C1: Build detection data to be logged into detection_history (person_name, is_known, confidence_score)
            if is_known:
                detected_names.append({"name": label, "known": True, "person_name": best_name, "confidence": best_distance})
            else:
                detected_names.append({"name": label, "known": False, "person_name": "Unknown", "confidence": 0.0})

    return frame, detected_names
