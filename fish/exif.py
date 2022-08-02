from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# confirmed to work for exifversion b'0220'

input = "shark.jpg"

def getexif(image):
    img = Image.open(image)._getexif()
    dec = {}
    for k, v in img.items():
        dec[TAGS.get(k)] = v
    for k in dec["GPSInfo"].keys():
        dec[GPSTAGS.get(k)] = dec["GPSInfo"][k]
    return dec

# (41.0, 47.0, 2.17)  hour-minute-second
# HMS -> DEC: ( h + m/60 + s/3600 ) * direction; -1 for w/s or 1 for e/n
# (int(new[0])+int(new[1])/60.0+int(new[2])/3600.0) # badboy

def showexif(exif):
    for k, v in dec.items():
        print(k, v)

def imgtime(exif):
    out = exif["DateTime"]
    # change time format here, standard: YYYY:MM:DD hh:mm:ss
    return out

def hmsdec(hms):
    out = []
    for k in ["Latitude", "Longitude"]:
        new = hms["GPS"+k]
        new = str(new).strip("()").split(",")
        new = [float(x) for x in new]
        ref = hms["GPS"+k+"Ref"]
        new = (new[0]+new[1]/60.0+new[2]/3600.0) * (-1 if ref in ["S","W"] else 1)
        out.append(new)
    return out
        

dec = getexif(input)
#showexif(dec)
print(imgtime(dec))
print(hmsdec(dec))