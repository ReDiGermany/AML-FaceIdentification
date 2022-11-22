import sqlite3 as sl
import face_recognition
import json
import click
import glob, os
import pathlib
import json

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
        print(row[1])

def save_image(id,url,name):
    img = face_recognition.load_image_file(url)
    try:
        img_face_encoding = face_recognition.face_encodings(img,model="large")[0]
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
        encoding = face_recognition.face_encodings(image,model="large")[0]
        results = face_recognition.compare_faces(data[0], encoding,tolerance=0.45)
        for (idx,item) in enumerate(results):
            if(item):
                return data[1][idx]
        if(True not in results):
            return "not found!"
    except IndexError:
        return "I wasn't able to locate any faces in at least one of the images. Check the image files. Aborting... @"+url

def find_image_from_base64(url,data = read_all_encodings()):
    image = face_recognition.load_image_base64(url)
    # print(image)
    try:
        encoding = face_recognition.face_encodings(image,model="large")[0]
        results = face_recognition.compare_faces(data[0], encoding,tolerance=0.45)
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
    id = int(all[len(all)-1][0]) if len(all) > 0 else 0
    for dir in os.listdir('images'):
        subdir = os.listdir('images/'+dir)[0]
        path = "images/"+dir+"/"+subdir
        # print("Checking "+path)
        img = face_recognition.load_image_file(path)
        try:
            temp = face_recognition.face_encodings(img,model="large")[0]
            print("OK "+path)
            id = id + 1
            save_image(id,path,dir)
        except IndexError:
            print("Failed "+path)

def read_dir_and_compare():
    data = read_all_encodings()
    errors = 0
    total = 0
    obj = []
    # print(data)
    for dir in os.listdir('images'):
        for subdir in os.listdir('images/'+dir):
            path = "images/"+dir+"/"+subdir
            ret = find_image_from_source(path,data)
            total = total + 1
            dcc = {
                "path":path,
                "ret":"images/"+ret+"/"+os.listdir("images/"+ret)[0] if ret != "not found!" else "",
                "matched":ret == dir
            }
            obj.append(dcc)
            # obj[path] = ret
            if ret != dir:
                print("[ERROR] "+path+" (should) does not match to (is) "+ret)
                errors = errors + 1
            else:
                print("[OK] "+path+" matched "+ret)
    if errors > 0:
        print("Finished with "+str(errors)+" errors out of "+str(total)+" entries ("+str(total/errors)+"%).")
    else:
        print("Finished with "+str(errors)+" errors.")
    y = json.dumps(obj,indent=4)
    f = open("result.json", "w+")
    f.write(y)
    f.close()

def try_find(path,num_jitters):
    # print("Checking "+path)
    img = face_recognition.load_image_file(path)
    try:
        temp = face_recognition.face_encodings(img,num_jitters=num_jitters,model="large")[0]
        return True
    except IndexError:
        return False

def test_dir():
    # all = get_all()
    # id = int(all[len(all)-1][0])
    tested = 0
    found = 0
    with open("test.json", "a") as myfile:
        should = len(os.listdir('test'))
        myfile.write("[\n")
        for dir in os.listdir('test'):
            tested = tested + 1
            path = "test/"+dir
            # print("Checking "+path)
            temp = try_find(path,1)
            if temp:
                print("[{0} / {1} | {2}%] OK {3}".format(tested,should,round(tested/should*100,2),path))
                myfile.write("{\"path\":\""+path+"\",\"success\":true},\n")
                found = found + 1 
            else:
                myfile.write("{\"path\":\""+path+"\",\"success\":false},\n")
                print("[{0} / {1} | {2}%] FAILED (1/2) {3}".format(tested,should,round(tested/should*100,2),path))
                # temp2 = try_find(path,100)
                # if temp2:
                #     print("[{0} / {1} | {2}%] OK {3}".format(tested,should,round(tested/should*100,2),path))
                #     found = found + 1 
                # else:
                #     print("[{0} / {1} | {2}%] FAILED (2/2) {3}".format(tested,should,round(tested/should*100,2),path))
        
        myfile.write("]")
        print("Found {0} out of {1} images".format(found,tested))

@click.command()
@click.option('--all',      help='Determines if i should print all known faces.',                             type=bool,  prompt=False, required=False,is_flag=True)
@click.option('--find',     help='Finds a user by its face. (param url to image)',                            type=str,   prompt=False, required=False)
@click.option('--insert',   help='Inserts a new face into the database. (param url to image - name needed)',  type=str,   prompt=False, required=False)
@click.option('--name',     help='Sets the name for the inserted person',                                     type=str,   prompt=False, required=False)
@click.option('--load',     help='temp',                                                                      type=bool,  prompt=False, required=False,is_flag=True)
@click.option('--clear',    help='Clears the database',                                                       type=bool,  prompt=False, required=False,is_flag=True)
@click.option('--compare',  help='Compares batch entries',                                                    type=bool,  prompt=False, required=False,is_flag=True)
@click.option('--test',     help='Test images from test folder',                                                    type=bool,  prompt=False, required=False,is_flag=True)
def hello(all,find,insert,name,load,clear,compare,test):
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
    elif(test):
        print("testing")
        test_dir()

if __name__ == '__main__':
    hello()