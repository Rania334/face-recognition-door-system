# Face Recognition Door Access System


---

## Project Overview

The Face Recognition Door Access System is a desktop-based security solution that controls door access based on facial recognition. It combines real-time video processing, secure cloud-based authentication, cloud storage of images, and access logging for both authorized users and unknown intruders.

The system provides an easy-to-use graphical interface for administrators to manage user registrations, review access logs, and control the door operations in real time. In case of unrecognized faces, it triggers alerts via cloud messaging.

---

## Features

- **Real-time face recognition** using webcam video feed.
- **Admin-controlled user management** with Firebase Authentication.
- **New face registration** directly via the application interface.
- **Persistent face data storage** using local encoding files and Cloudinary for remote image backup.
- **Access attempt logging** with timestamps, user names, and image snapshots saved in Firestore.
- **Intruder detection** with real-time alerts sent through Firebase Cloud Messaging.
- **Graphical User Interface (GUI)** built with Tkinter for easy interaction.

---

## Technology Stack

| Technology       | Usage                                      |
|-------------------|--------------------------------------------|
| Python 3.x        | Programming language                       |
| OpenCV            | Video capture and image processing         |
| face_recognition  | Face detection and encoding (dlib-based)   |
| Firebase          | Authentication, Firestore, Cloud Messaging |
| Cloudinary        | Cloud-based image storage                  |
| Tkinter           | Desktop GUI interface                      |

---

## System Architecture

The application workflow includes:

1. **Video Capture:** Captures frames via webcam using OpenCV.
2. **Face Detection:** Locates faces in frames and encodes them using `face_recognition`.
3. **Authentication:** Admin login handled securely via Firebase Authentication API.
4. **Registration:** Admin registers new users, captures multiple images, and encodes faces.
5. **Recognition Loop:** Live video scanning for known faces.
6. **Logging:** Access results (success/failure) are logged into Firebase Firestore.
7. **Cloud Storage:** Captured images are uploaded to Cloudinary.
8. **Intruder Alert:** If unknown faces persist, an alert is triggered via Firebase Cloud Messaging.

---

## Setup and Installation

### 1. Clone Repository

```bash
git clone https://github.com/Rania334/face-recognition-door-system/
cd face-recognition-door-system
