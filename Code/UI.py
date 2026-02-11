import tkinter as tk
from tkinter import * 
from tkinter import ttk
import psycopg2
from tkinter import messagebox,filedialog 
import bcrypt
import Facenet_engine as fn
from PIL import Image, ImageTk
import Detect as dt
import threading
import cv2
import time

def connect_to_db():
    try:
        return psycopg2.connect(
            host="localhost",
            database="WatchBot",
            user="postgres",
            password="onepiece!1"
        )
    except psycopg2.Error as err:
        print(f"Database connection error: {err}")
        return None

class Confirmation():
    def __init__(self,master,root,agreed,cancel):
        self.master = master
        self.root = root
        self.master.title("Ethical Confirmation")
        self.master.geometry("800x750")

        self.agreed = agreed

        self.cancel = cancel

        tk.Label(master,text="Terms And Agreement", font=('Helvetica', 18, 'bold')).pack()
        tk.Label(master, text= """
This application (“WatchBot”) is developed for educational and project purposes only.

By continuing, the user agrees to the following conditions: 
                """).pack()
        
        tk.Label(master, text= "1. Purpose of Use", font=('Helvetica', 16, 'bold')).pack()
                 
        tk.Label(master, text= """
This system is intended solely for learning, demonstration, and academic evaluation.
It must not be used for illegal surveillance, stalking, or invasion of privacy.
                """).pack()

        tk.Label(master, text="2. Camera & Image Data", font=('Helvetica', 16, 'bold')).pack()
        tk.Label(master, text= """      
The application may use camera input and store images or video data for security-related features.
Any captured images must only be used with the explicit consent of the individuals involved.
                """).pack()
        tk.Label(master, text="3. Privacy & Data Protection", font=('Helvetica', 16, 'bold')).pack()
        tk.Label(master, text= """ 
User passwords are securely stored using hashing techniques.

No plaintext passwords are saved.

Personal data should not be shared with third parties.
                 """).pack()

        tk.Label(master, text="4. User Responsibility", font=('Helvetica', 16, 'bold')).pack()
        tk.Label(master, text= """ 
The user is responsible for ensuring that this system is used ethically and lawfully.
The developer is not responsible for misuse of this software.
                 """).pack()
        tk.Label(master, text="5.Consent", font=('Helvetica', 16, 'bold')).pack()
        tk.Label(master, text= """ 
By clicking Continue, the user confirms that they understand and agree to these terms.

If you do not agree, please click Cancel.

""").pack()

        tk.Button(master, text="Continue", width=12, command=self.agreed).pack()

        tk.Button(master, text="Cancel", width=12, command=self.cancel).pack()
        


class New_Account():
    def __init__(self,master,root):
        self.master = master
        self.root = root
        self.master.title("Create New Account")
        self.master.geometry("500x500")


        tk.Label(master, text="Enter a Username").pack()
        self.new_username = tk.Entry(master)
        self.new_username.pack()

        tk.Label(master, text="Enter a Password").pack()
        self.new_password = tk.Entry(master,show="*")
        self.new_password.pack()

        self.var = tk.IntVar()

        checkbox = tk.Checkbutton(master,text="See Password", variable=self.var,onvalue=1,offvalue=0, command=self.on_click_check)
        checkbox.pack()

        tk.Label(master, text="Re-enter Password to confirm").pack()
        self.check_password = tk.Entry(master,show="*")
        self.check_password.pack()
            
        tk.Button(master,text="Create New Account",command=self.submit).pack(pady=15)

    def on_click_check(self):
            if self.var.get() == 1:
                self.new_password.configure(show="")
                self.check_password.configure(show="")
            else:
                self.new_password.configure(show="*")
                self.check_password.configure(show="*")

    def submit(self):
        
        username = self.new_username.get()
        password = self.new_password.get()
        check_password = self.check_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and Password cannot be empty!")
            return
        elif password != check_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        self.create_new_account(username,password)

    def create_new_account(self,username,password):
        db = connect_to_db()
        if db is None:
            messagebox.showerror("Error", "Database connection failed")
            return
        cur = db.cursor()
        try:
            password_byte = password.encode("utf-8")
            hashed = bcrypt.hashpw(password_byte,bcrypt.gensalt())
            hashed_str = hashed.decode("utf-8")

            cur.execute("INSERT INTO login_details(username, hash_values) VALUES (%s, %s) RETURNING user_id",
                        (username, hashed_str))

            user_id = cur.fetchone()[0]
            db.commit()
            messagebox.showinfo("Success", "Account created successfully!")
            self.master.destroy()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            cur.close()
            db.close() 
            

class Home_Page():
    def __init__(self,master,root,username,user_id,on_logout=None):
        self.master = master
        self.root = root
        self.on_logout = on_logout
        self.master.title("Home Page")
        self.master.geometry("500x500")
        self.username = username.get()
        self.username = self.username.title()
        self.user_id = user_id

        img = Image.open("/Users/rishiprajapati/Desktop/Projects/WATCHBot/Code/logout.jpg")
        img = img.resize((30, 30), Image.Resampling.LANCZOS)
        self.logout_icon = ImageTk.PhotoImage(img)

        top_bar = tk.Frame(self.master, bg="#b1b1b1", height=60)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        user_label = tk.Label(top_bar , text=f"Hello {self.username} !", fg="white",bg="#b1b1b1",font=("Comic Sans MS", 20,"bold"))
        user_label.pack(side="left",padx=15)

        logout_btn = tk.Button(top_bar,image=self.logout_icon,command=self.logout,relief="flat")
        logout_btn.pack(side="right", padx=15)

        button_row = tk.Frame(self.master)
        button_row.pack(pady=20)

        # tk.Button(button_row, text="Live Camera", height=6,width=20 , command=lambda: threading.Thread(target=fn.detect_faces(self.user_id), daemon=True).start()).pack(side="left",padx=10)
        tk.Button(button_row, text="Live Camera", height=6,width=20 , command=self.open_live_feed).pack(side="left",padx=10)
        tk.Button(button_row, text="Database", height=6, width=20,command=self.open_database_window).pack(side="right", padx=10)

        tk.Button(self.master, text="Upload Image",height=3,width=45, command=self.open_upload_image).pack(pady=20)
    
    def open_live_feed(self):
        self.master.withdraw()
        self.open_live_feed_window = tk.Toplevel(self.root)

        def on_close():
            self.live_feed.stop()


        self.open_live_feed_window.protocol("WM_DELETE_WINDOW", on_close)
        self.live_feed = Live_Feed(self.open_live_feed_window, self.root, self.master, self.user_id)

    
    def open_upload_image(self):
        self.master.withdraw()
        self.open_upload_image_window = tk.Toplevel(self.root)

        def on_close():
            self.master.deiconify()
            self.open_upload_image_window.destroy()

        self.open_upload_image_window.protocol("WM_DELETE_WINDOW", on_close)
        Upload_Image(self.open_upload_image_window,self.root,self.master,self.username,self.user_id)

    def open_database_window(self):
        self.master.withdraw()
        db_menu_window = tk.Toplevel(self.root)

        def on_close():
            self.master.deiconify()
            db_menu_window.destroy()

        db_menu_window.protocol("WM_DELETE_WINDOW", on_close)
        Database_Menu(db_menu_window, self.root, self.master, self.user_id)

    def logout(self):
        if self.on_logout:
            self.on_logout()
        else:
            self.root.deiconify()
            self.master.destroy()


class Database_Menu():
    def __init__(self, master, root, previous_window, user_id):
        self.master = master
        self.root = root
        self.previous_window = previous_window
        self.user_id = user_id
        self.master.title("Database")
        self.master.geometry("500x500")

        tk.Label(master, text="Database", font=('Helvetica', 18, 'bold')).pack(pady=30)

        button_row = tk.Frame(master)
        button_row.pack(pady=20)

        tk.Button(button_row, text="Historical Data", height=6, width=20, command=self.open_historical_data).pack(side="left", padx=10)
        tk.Button(button_row, text="Manage Faces", height=6, width=20, command=self.open_database_view).pack(side="right", padx=10)
        tk.Button(self.master, text="Back",height=3,width=45, command=self.back).pack(pady=20)

    def open_historical_data(self):
        self.master.withdraw()
        historical_data_view_window = tk.Toplevel(self.root)

        def on_close():
            self.master.deiconify()
            historical_data_view_window.destroy()

        historical_data_view_window.protocol("WM_DELETE_WINDOW", on_close)
        Historical_Data(historical_data_view_window, self.root, self.master, self.user_id)

    def open_database_view(self):
        self.master.withdraw()
        db_view_window = tk.Toplevel(self.root)

        def on_close():
            self.master.deiconify()
            db_view_window.destroy()

        db_view_window.protocol("WM_DELETE_WINDOW", on_close)
        Database_View(db_view_window, self.root, self.master, self.user_id)

    def back(self):
        self.previous_window.deiconify()
        self.master.destroy()
    
class Historical_Data():
    def __init__(self,master,root,previous_window,user_id):
        self.master = master
        self.root = root
        self.previous_window = previous_window
        self.user_id = user_id
        self.master.title("Historical Data")
        self.master.geometry("700x400")

        tree = ttk.Treeview(master, columns=("Person", "Known", "Confidence", "Time"), show="headings")
        tree.heading("Person", text="Person Name")
        tree.heading("Known", text="Known")
        tree.heading("Confidence", text="Confidence")
        tree.heading("Time", text="Detected At")
        tree.column("Person", width=150)
        tree.column("Known", width=80)
        tree.column("Confidence", width=100)
        tree.column("Time", width=200)
        tree.pack(fill="both", expand=True)
        self.tree = tree

        tk.Button(master, text="Refresh", command=self.load_data).pack(pady=5)
        tk.Button(master, text="Delete History", command=self.delete_history).pack(pady=5)
        tk.Button(master, text="Back" , command=self.back).pack(pady=5)

        self.load_data()

    def load_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.db = connect_to_db()
        self.cur = self.db.cursor()
        self.cur.execute(
            "SELECT person_name, is_known, confidence_score, detected_at FROM detection_history WHERE user_id=%s ORDER BY detected_at DESC",
            (self.user_id,)
        )
        rows = self.cur.fetchall()
        for row in rows:
            person_name, is_known, confidence, detected_at = row
            known_text = "Yes" if is_known else "No"
            confidence_text = f"{confidence:.2f}" if confidence else "—"
            time_text = detected_at.strftime("%Y-%m-%d %H:%M:%S")
            self.tree.insert("", tk.END, values=(person_name, known_text, confidence_text, time_text))
        self.cur.close()
        self.db.close()
    
    def delete_history(self):
        db = connect_to_db()
        cur = db.cursor()
        cur.execute("DELETE FROM detection_history WHERE user_id=%s", (self.user_id,))
        db.commit()
        cur.close()
        db.close()
        messagebox.showinfo("Success", "History cleared")
        self.load_data()

    def back(self):
        self.previous_window.deiconify()
        self.master.destroy()


class Database_View():
    def __init__(self, master, root, previous_window, user_id):
        self.master = master
        self.root = root
        self.previous_window = previous_window
        self.user_id = user_id
        self.master.title("Manage Faces")
        self.master.geometry("600x400")

        tree = ttk.Treeview(master, columns=("Name", "Num Images", "User ID"), show="headings")
        tree.heading("Name", text="Person Name")
        tree.heading("Num Images", text="Number of Images")
        tree.heading("User ID", text="User ID")
        tree.pack(fill="both", expand=True)
        self.tree = tree

        tk.Button(master, text="Remove Selected Person", command=self.remove_person).pack(pady=5)
        tk.Button(master, text="Refresh", command=self.load_data).pack(pady=5)
        tk.Button(master, text="Back" , command=self.back).pack(pady=5)

        self.load_data()

    def load_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        db = connect_to_db()
        cur = db.cursor()
        cur.execute("SELECT person_name, COUNT(*), user_id FROM embedding_table GROUP BY person_name, user_id")
        rows = cur.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        cur.close()
        db.close()

    def remove_person(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a person to remove")
            return
        person_name = self.tree.item(selected[0])['values'][0]

        db = connect_to_db()
        cur = db.cursor()
        cur.execute("DELETE FROM embedding_table WHERE person_name=%s AND user_id=%s", (person_name, self.user_id))
        db.commit()
        cur.close()
        db.close()
        messagebox.showinfo("Success", f"All data for '{person_name}' removed")
        self.load_data()

    def back(self):
        self.previous_window.deiconify()
        self.master.destroy()

class Live_Feed():
    def __init__(self,master,root,previous_window,user_id):
        self.root = root
        self.master = master
        self.user_id = user_id
        self.previous_window = previous_window
        self.master.title("Live Feed")
        self.master.geometry("900x530")

        top_section = tk.Frame(self.master)
        top_section.pack(fill="both", expand=True)

        self.video_frame = tk.Frame(top_section)
        self.video_frame.pack(side="left", padx=10, pady=10)

        self.text_frame = tk.Frame(top_section)
        self.text_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        result = dt.setup_detection(self.user_id)
        if result is not None:
            self.known_faces, self.mtcnn, self.facenet = result
        else:
            self.previous_window.deiconify()
            self.master.destroy()
            return

        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack()

        tk.Label(self.text_frame, text="Known", font=("Helvetica", 16, "bold"), fg="green").pack(pady=(10,5))
        self.known_label = tk.Label(self.text_frame, text="—", font=("Helvetica", 14), fg="green", justify="center")
        self.known_label.pack()

        tk.Label(self.text_frame, text="Unknown", font=("Helvetica", 16, "bold"), fg="red").pack(pady=(20,5))
        self.unknown_label = tk.Label(self.text_frame, text="—", font=("Helvetica", 14), fg="red", justify="center")
        self.unknown_label.pack()

        self.logged_recently = {}
        self.cap = cv2.VideoCapture(0)
        self.update_frame()

        tk.Button(self.master, text="Close Camera", height=3, width=45, command=self.stop).pack(pady=10)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame, names = dt.process_frame(frame, self.mtcnn, self.facenet, self.known_faces)

            # convert for tkinter, keep aspect ratio
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img = pil_img.resize((550, int(550 * pil_img.height / pil_img.width)), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(pil_img)

            # update video
            self.video_label.configure(image=photo)
            self.video_label.image = photo

            # update text
            known = [n["name"] for n in names if n["known"]]
            unknown_count = sum(1 for n in names if not n["known"])

            self.known_label.configure(text="\n".join(known) if known else "—")
            self.unknown_label.configure(text=f"{unknown_count} unknown face(s)" if unknown_count > 0 else "—")

            self.log_detections(names)

        self.master.after(30, self.update_frame)

    def log_detections(self, names):
        now = time.time()
        for face in names:
            person_name = face["person_name"]
            last_logged = self.logged_recently.get(person_name, 0)
            if now - last_logged < 30:  # check if any new person arrives after 30 sec after detected then only continue
                continue
            self.logged_recently[person_name] = now
            try:
                db = connect_to_db()
                cur = db.cursor()
                cur.execute(
                    "INSERT INTO detection_history (user_id, person_name, is_known, confidence_score) VALUES (%s, %s, %s, %s)",
                    (self.user_id, person_name, face["known"], face["confidence"])
                )
                db.commit()
                cur.close()
                db.close()
            except Exception as e:
                print(f"Detection log error: {e}")

    def stop(self):
        self.cap.release()
        self.previous_window.deiconify()
        self.master.destroy()


class Upload_Image():
    def __init__(self,master,root,previous_window,username,user_id):
        self.master = master
        self.root = root
        self.previous_window = previous_window
        self.master.title("Upload Image")
        self.master.geometry("500x500")
        self.username = username
        self.user_id = user_id

        img = Image.open("/Users/rishiprajapati/Desktop/Projects/WATCHBot/Code/back.png")
        img = img.resize((30, 30), Image.Resampling.LANCZOS)
        self.logout_icon = ImageTk.PhotoImage(img)

        top_bar = tk.Frame(self.master, bg="#b1b1b1", height=60)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        user_label = tk.Label(top_bar , text=f"Hello {self.username}!", fg="white",bg="#b1b1b1",font=("Comic Sans MS", 20,"bold"))
        user_label.pack(side="left",padx=15)

        back_btn = tk.Button(top_bar,image=self.logout_icon,command=self.back,relief="flat")
        back_btn.pack(side="right", padx=15)


        tk.Label(master,text="You can complete the credentials to update a new person").pack(pady=10)
        tk.Label(master,text="Name of Person").pack()
        self.new_name = tk.Entry(master)
        self.new_name.pack()

        tk.Button(self.master, text="Upload Image (Atleast 10 images for accuracy)", command=self.import_images).pack()
        tk.Button(self.master, text="Submit", command=self.submit).pack(pady=20)
        

    def submit(self):
        if not self.file_paths:
            messagebox.showerror("Error", "Please upload images first")
            return
        if not self.new_name.get():
            messagebox.showerror("Error","Please enter a message")
            return
        
        fn.save_embeddings(
            self.user_id,
            self.new_name.get(),
            self.file_paths
        )

        messagebox.showinfo("Success", "Face data saved successfully")

    def import_images(self):
        self.file_paths = []
        self.file_name = filedialog.askopenfilenames(title="Select at least 1 image (you can hold CMD/CTRL to select multiple)",filetypes=[("Image Files","*.jpg *.png")])
        self.file_paths = list(self.file_name)
        
        print(self.file_name)
        print(self.file_paths)

    def back(self):
        self.previous_window.deiconify()
        self.master.destroy()


    
def check_password(username,password):
        
        db = connect_to_db()
        if db is None:
            messagebox.showerror("Error", "Database connection failed")
            return
        cur = db.cursor()

        cur.execute(
            "SELECT user_id, hash_values FROM login_details WHERE username = %s",
            (username,)
        )

        result = cur.fetchone()
        if result is None:
            return None

        user_id, stored_hash = result
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return user_id
        return None
        


def main():

    root = tk.Tk()
    root.title('Login Page')
    root.minsize(400,400)
    root.maxsize(500,500)
    root.geometry("300x300")

    def on_click_check():
        if var.get() == 1:
            password_entry.configure(show="")
        else:
            password_entry.configure(show="*")

    current_frame = tk.Frame(root)
    current_frame.pack(pady=15)

    tk.Label(current_frame, text="Username").pack()

    username_entry = tk.Entry(current_frame)
    username_entry.pack()

    tk.Label(current_frame,text="Password").pack()
    password_entry = tk.Entry(current_frame, show="*")
    password_entry.pack()

    var = tk.IntVar()

    checkbox = tk.Checkbutton(current_frame,text="See Password", variable=var,onvalue=1,offvalue=0, command=on_click_check)
    checkbox.pack()

    def open_home_page(user_id):
        root.withdraw()
        home_page_window = tk.Toplevel(root)
        
        def on_close():
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
            root.deiconify()
            home_page_window.destroy()

        home_page_window.protocol("WM_DELETE_WINDOW", on_close)
        Home_Page(home_page_window,root,username_entry,user_id,on_close)

    def confirm_credentials():
        root.withdraw()
        confirmation_window = tk.Toplevel(root)

        def agreed():
            confirmation_window.destroy()
            open_new_account()

        def cancel():
            root.deiconify()
            confirmation_window.destroy()

        Confirmation(confirmation_window,root, agreed, cancel)
        

    def open_new_account():
        root.withdraw()
        new_account_window = tk.Toplevel(root)
        
        def on_close():
            root.deiconify()
            new_account_window.destroy()

        new_account_window.protocol("WM_DELETE_WINDOW", on_close)
        New_Account(new_account_window,root)
        
    button = tk.Button(text="Submit", command=lambda: login() )
    button.pack()

    new_Account = tk.Button(text="Create New Account", command=confirm_credentials)
    new_Account.pack()
        
    def login():
        username = username_entry.get()
        password = password_entry.get()

        user_id = check_password(username,password)

        if user_id is not None:
            open_home_page(user_id)
        else:
            messagebox.showerror("Error", "Invalid Username or Password")


    root.mainloop()

if __name__ == "__main__":

    main()
