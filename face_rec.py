import face_recognition

def find_image_from_base64(b64image, data):
    image = face_recognition.load_image_base64(b64image)
    try:
        encoding = face_recognition.face_encodings(image,model="large")[0]
        results = face_recognition.compare_faces(data.values(), encoding,tolerance=0.45)
        for (idx,item) in enumerate(results):
            if(item):
                keys = [k for k, v in data.items() if v == idx]
                return True, keys, []
        if(True not in results):
            return False, "", encoding
    except IndexError:
        return False, "", []
