import sqlite3 as sl
import face_recognition
import json
import click
import glob, os
import pathlib

con = sl.connect('my-test.db')
with con:
	con.execute("""
		CREATE TABLE IF NOT EXISTS USER (
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			landmarks TEXT
		);
	""")

def insert_data(id,name,landmarks):
    sql = 'INSERT INTO USER (id, name, landmarks) values(?, ?, ?)'
    data = [
        (id, name, str(landmarks)),
    ]
    with con:
        con.executemany(sql, data)

def get_all():
    ret = []
    with con:
        data = con.execute("SELECT * FROM USER")
        for row in data:
            ret.append(row)
    return ret

def read_all():
    data = get_all()
    for row in data:
        print(row)

def save_image(id,url,name):
    img = face_recognition.load_image_file(url)
    try:
        img_face_encoding = face_recognition.face_encodings(img)[0]
        insert_data(id,name,str(img_face_encoding.tolist()))
    except IndexError:
        print("I wasn't able to locate any faces in at least one of the images. Check the image files. Aborting... @save_image@"+url)
        quit()

def find_image(list):
    with con:
        data = con.execute("SELECT * FROM USER WHERE `landmarks`=?",[list])
        for row in data:
            return row[1]
        return "not found"

def read_all_encodings():
    retLM = []
    retNames = []
    with con:
        data = con.execute("SELECT * FROM USER")
        for row in data:
            r = row[2]
            d = json.loads(r)
            retLM.append(d)
            retNames.append(row[1])
    return [retLM,retNames]

def find_image_from_source(url,data = read_all_encodings()):
    image = face_recognition.load_image_file(url)
    # print(image)
    try:
        encoding = face_recognition.face_encodings(image)[0]
        results = face_recognition.compare_faces(data[0], encoding)
        print(results)
        for (idx,item) in enumerate(results):
            if(item):
                return data[1][idx]
        if(True not in results):
            return "not found!"
    except IndexError:
        return "I wasn't able to locate any faces in at least one of the images. Check the image files. Aborting... @"+url

def delete_all():
    with con:
        data = con.execute("TRUNCATE TABLE USER")

def read_dir():
    all = get_all()
    id = int(all[len(all)-1][0])
    for dir in os.listdir('images'):
        subdir = os.listdir('images/'+dir)[0]
        path = "images/"+dir+"/"+subdir
        # print("Checking "+path)
        img = face_recognition.load_image_file(path)
        try:
            temp = face_recognition.face_encodings(img)[0]
            print("OK "+path)
            id = id + 1
            save_image(id,path,dir)
        except IndexError:
            print("Failed "+path)

def read_dir_and_compare():
    data = read_all_encodings()
    # print(data)
    for dir in os.listdir('images'):
        for subdir in os.listdir('images/'+dir):
            path = "images/"+dir+"/"+subdir
            ret = find_image_from_source(path,data)
            if ret != dir:
                print("[ERROR] "+path+" (should) does not match to (is) "+ret)
            else:
                print("[OK] "+path+" matched "+ret)


@click.command()
@click.option('--all', default=False, prompt=False,is_flag=True, help='Determines if i should print all known faces.',type=bool,required=False)
@click.option('--find', prompt=False, help='Finds a user by its face. (param url to image)',type=str,required=False)
@click.option('--insert', prompt=False, help='Inserts a new face into the database. (param url to image - name needed)',type=str,required=False)
@click.option('--name', prompt=False, help='Sets the name for the inserted person',type=str,required=False)
@click.option('--load', prompt=False, help='temp',type=bool,required=False,is_flag=True)
@click.option('--clear', prompt=False, help='Clears the database',type=bool,required=False,is_flag=True)
@click.option('--compare', prompt=False, help='Compares batch entries',type=bool,required=False,is_flag=True)
def hello(all,find,insert,name,load,clear,compare):
    if(compare):
        print("Comparing...")
        read_dir_and_compare()
    elif(load):
        print("Loading...")
        read_dir()
    elif(clear):
        print("Deleting all Records")
        delete_all()
    elif(all):
        print("Getting all Records")
        read_all()
    elif(find):
        print("Finding Image by "+find)
        print(find_image_from_source(find))
    elif(insert and name):
        print("Inserting "+name)
        save_image(len(get_all())+2,insert,name)

if __name__ == '__main__':
    hello()