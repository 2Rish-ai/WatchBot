import cv2
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import database
import numpy as np
from tkinter import messagebox

threshold = 0.75

def setup_detection(user_id):
    db = database.connect_to_db()
    cur = db.cursor()

    cur.execute(
        "SELECT person_name,embedding FROM embedding_table WHERE user_id = %s",
        (user_id,))
    known_faces = cur.fetchall()

    cur.close()
    db.close()

    mtcnn = MTCNN(image_size=160)
    facenet = InceptionResnetV1(pretrained="vggface2").eval()

    if not known_faces:
        messagebox.showerror("Error","No known faces for this user")
        return None

    return known_faces, mtcnn, facenet

def process_frame(frame, mtcnn, facenet, known_faces):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detected_names = []

    boxes, _ = mtcnn.detect(img)

    if boxes is not None:
        for box in boxes:
            x1,y1,x2,y2 = [int(b) for b in box]

            # Clamp coordinates to image bounds
            h, w = img.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            # Skip if face region is too small
            if x2 - x1 < 20 or y2 - y1 < 20:
                continue

            # Extract face region for this specific box
            face_img = img[y1:y2, x1:x2]

            # Get embedding for this specific face
            try:
                face_tensor = mtcnn(face_img)
            except RuntimeError:
                continue

            if face_tensor is not None:
                with torch.no_grad():
                    live_embedding = facenet(face_tensor.unsqueeze(0))[0]

                best_distance = float("-inf")
                best_name = "Unknown"

                for name, db_embedding in known_faces:
                    db_embedding = torch.tensor(db_embedding)
                    distance = torch.cosine_similarity(live_embedding.unsqueeze(0), db_embedding.unsqueeze(0)).item()

                    if distance > best_distance:
                        best_distance = distance
                        best_name = name

                if best_distance > threshold:
                    label = f"{best_name} {best_distance:.2f}"
                else:
                    label = "Unknown"
            else:
                label = "Unknown"

            is_known = label != "Unknown"
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

            if is_known:
                detected_names.append({"name": label, "known": True, "person_name": best_name, "confidence": best_distance})
            else:
                detected_names.append({"name": label, "known": False, "person_name": "Unknown", "confidence": 0.0})

    return frame, detected_names
