import pyrebase # pip install pyrebase
from google.cloud import storage
import os
import face_recognition as fr # pip install face-recognition
from datetime import datetime
import cv2 # pip install cv2
import numpy as np
from datetime import datetime
from pathlib import Path

# create database connection to realtime database
try:
    firebaseConfig = {
    "Enter firebase configuration settings"
    }
    firebase = pyrebase.initialize_app(firebaseConfig) # initialize firebase
    store = firebase.storage() # object to store data in firebase storage
    data= firebase.database() # object to store data in raltime database
except:
    print("connnect to the internet")


class database:
    path = "StaffImage" # image path on the computer
    image_list=[] # list to hold images
    encode_list=[] # list to hold encode value
    name_list=[] # list to hold the name of the images or reg number
  
    def __init__(self):
        pass
    def storageimage(self):
        try:
            for files in os.listdir(self.path): # list image in file directory
                image_path = f"StaffImage/{files}" # name of image to stored on cloud
                image_destination = f"StaffImage/{files}" # namew of folder to store images on cloud
                store.child(image_destination).put(image_path) # store data in this location on the cloud
            print("done")
        except:
            print("not a available")
    def downloadimage(self):
        try:
            storage_client = storage.Client.from_service_account_json("facerecognition.json")
            bucket = storage_client.get_bucket("facerecognition-ca243.appspot.com")
            source_folder = "StaffImage" # name of folder on cloud
            blobs = list(bucket.list_blobs(prefix=source_folder)) # list images in the folder
            for blob in blobs:
                file_path=blob.name # extract the name of the file
                file_name = Path(file_path) # to sperate the folder name from the file name
                img_name = file_name.name # get the image name only
                name = os.path.splitext(img_name)[0] # split the name from the extension
                self.name_list.append(name) # add the image name to list
                r=cv2.imread(file_path) # read image directly from folder
                self.image_list.append(r) # add image to image list
            for img in self.image_list:
                # encode the image
                face_encode = fr.face_encodings(img)[0]
                self.encode_list.append(face_encode)
        except:
            print("No internet connection")
   
    def create_database(self):
        try:   

            Data= {"Name":"Israel",
                "Total_Attendance":0,
            }
            data.child("Staff").child("003").set(Data)
            print("Record created")
        except:
            print("Unable to connect")
           
    def webcam(self):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")       
        counter= 0
        vid = cv2.VideoCapture(0)
        vid.set(3,400) # set hte width of the window
        vid.set(4,500) # set the height of the window
        while True:
            ret,img = vid.read()
          # locate the face
            locate_face = fr.face_locations(img)
            encode_face = fr.face_encodings(img,locate_face)
            # if face is present
            if locate_face:
                for face_encode, face_locate in zip(encode_face,locate_face):
                    match = fr.compare_faces(self.encode_list,face_encode)
                    face_dist = fr.face_distance(self.encode_list,face_encode)
                    match_index = np.argmin(face_dist)
                    if match[match_index]:
                        my_name = self.name_list[match_index]
                        #print(my_name)
                        y1,x2,y2,x1 = face_locate
                        cv2.rectangle(img,(x1,y1),(x2,y2),(255,0,0),2)
                        cv2.rectangle(img,(x1,y2-25),(x2,y2),(255,0,0),cv2.FILLED)
                        cv2.putText(img,my_name,(x1+6,y2-6),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1)
                        id = self.name_list[match_index]
                        #print(f"this is id: {id}")
                        if counter ==0:
                            counter=1
                    if counter != 0:
                        if counter==1:
                            # get the time in value
                            time_in_value = data.child(f"Staff/{id}").child(datetime.now().strftime("%Y-%m-%d")).child("Time in").get().val()
                            time_out_value= data.child(f"Staff/{id}").child(datetime.now().strftime("%Y-%m-%d")).child("Time out").get().val()
                    
                            if not time_in_value: # check for time in value
                                time_in = data.child(f"Staff/{id}").child(datetime.now().strftime("%Y-%m-%d")).set({"Time in":time})
                                print("Time inserted")
                            if time_in_value: # check for time in value
                                value_time_in = data.child(f"Staff/{id}").child(datetime.now().strftime("%Y-%m-%d")).child("Time in").get().val()                          
                                timeobject = datetime.strptime(value_time_in,"%Y-%m-%d %H:%M:%S")# convert to string object
                                diff_time = (datetime.now()-timeobject).total_seconds()# subtract current time from time in
                                if diff_time>120:
                                    data.child(f"Staff/{id}").child(datetime.now().strftime("%Y-%m-%d")).child("Time out").set({"Time out":datetime.now().strftime("%Y-%m-%d %H:%M:%S")  })
                                    print("Time out")
                                    studentinfo=data.child(f"Staff/{id}").child("Total_Attendance").get().val()
                                    studentinfo+=1
                                    data.child(f"Staff/{id}").update({"Total_Attendance":studentinfo})
                                    print("Goodbye")
                            else:
                                print("close for today")
                            if 10<counter<20:
                                print("registered")
                        
                        counter+=1

                        if counter>20:
                            counter=0
                            studentinfo=0



            cv2.imshow("Image",img)
            key = cv2.waitKey(1)
            if key==ord("q"):
                break
        vid.release()
        cv2.destroyAllWindows()
             
if __name__ =="__main__":
    db = database()
    db.downloadimage()
    #db.create_database()
    db.storageimage()
    db.webcam()
    