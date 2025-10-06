
import face_recognition
import numpy as np

def generate_face_encoding(image_path):
    """
    Trả về list 128 float hoặc None nếu không thấy mặt.
    """
    img = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(img)
    if encodings:
        return encodings[0].tolist()
    return None

def compare_face(frame, known_encodings, tolerance=0.6):
    """
    frame: numpy array (BGR như OpenCV).
    known_encodings: list các list 128 float.
    return True nếu có match.
    """
    encodings = face_recognition.face_encodings(frame)
    if not encodings:
        return False
    current = encodings[0]
    results = face_recognition.compare_faces([np.array(e) for e in known_encodings], current, tolerance=tolerance)
    return any(results)
