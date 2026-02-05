import cv2
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import database
import numpy as np
from tkinter import messagebox

threshold = 0.85

def run_live_detection(user_id):
    db = database.connect_to_db()
    cur = db.cursor()

    cur.execute(
        "SELECT person_name,embedding FROM embedding_table WHERE user_id = %s",
        (user_id,))
    known_faces = cur.fetchall()

    if not known_faces:
        messagebox.showerror("Error","No known faces for this user")
        return

    mtcnn = MTCNN(image_size=160)
    facenet = InceptionResnetV1(pretrained="vggface2").eval()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Camera not accessible")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_tensor = mtcnn(img)

        if img_tensor is not None:
            boxes,_ = mtcnn.detect(img)

            with torch.no_grad():
                live_embedding = facenet(img_tensor.unsqueeze(0))[0]
                
            best_distance = float("inf")
            best_name = "Unknown"

            for name, db_embedding in known_faces:
                db_embedding = torch.tensor(db_embedding)
                distance = torch.norm(live_embedding - db_embedding).item()

                if distance < best_distance:
                    best_distance = distance
                    best_name = name
            
            if best_distance < threshold:
                label = f"{best_name} {best_distance:.2f}"
            else:
                label = "Unknown"

            if boxes is not None:
                for box in boxes:
                    x1,y1,x2,y2 = [int(b) for b in box]
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
                    cv2.putText(
                        frame,
                        label,
                        (x1,y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0,255,0),
                        2
                    )
                

        cv2.imshow("Live Feed", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    cur.close()
    db.close()
