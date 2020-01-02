from mutagen.mp3 import EasyMP3 as MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC
import mutagen
import os, time
import thwiki, filename_parser
import urllib.request as urllib2
import textwrap

def assign_metadata(audio, path, type_, title, album, circle, arrange, vocal, lyrics, original, dor, imgurl):

    if type_ == 2:
        if not title == "": audio['\xa9nam'] = title
        if not album == "": audio['\xa9alb'] = album
        if not circle == "": audio['aART'] = circle
        if not arrange == "": 
            audio['\xa9wrt'] = arrange
            #audio['arranger'] = arrange
        if not vocal == "": audio['\xa9ART'] = vocal
        if not lyrics == "": audio['\xa9lyr'] = lyrics
        if not original == "": audio['desc'] = original
        #audio['date'] = dor
        
    elif type_ == 1:
        if not title == "": audio['title'] = title
        if not album == "": audio['album'] = album
        if not circle == "": audio['albumartist'] = circle
        if not arrange == "": 
            audio['composer'] = arrange
            audio['arranger'] = arrange
        if not vocal == "": audio['artist'] = vocal
        if not lyrics == "": audio['lyricist'] = lyrics
        if not original == "": audio['discsubtitle'] = original
        #audio['date'] = dor
    

    audio.save()
    
    if imgurl is not None and imgurl is not "":
        if type_ == 1:
            audio = ID3(path)
            albumart = urllib2.urlopen(str(imgurl))

            audio['APIC'] = APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3, desc=u'Cover',
                            data=albumart.read()
                            )

            albumart.close()
            audio.save()
            
        elif type_ == 2:
            cover = imgurl
            fd = urllib2.urlopen(cover)
            covr = MP4Cover(fd.read(), getattr(
                        MP4Cover,
                        'FORMAT_PNG' if cover.endswith('png') else 'FORMAT_JPEG'
                    ))
            fd.close() 
            audio['covr'] = [covr] 
            audio.save()

    
    
    
#given a string(name of audio file) and path to that audio file, calls thwiki module to find metadata for that song    
def find_metadata(name, path, t):
    time.sleep(10)
    len = 0
    
    if t==1: audio = MP3(path)
    else:    audio = MP4(path)
    metadata = thwiki.main(name, False, audio.info.length, 6)

    print("====================================================")
    print("Name:     \t", metadata[0])
    print("Album:    \t", metadata[1])
    print("Circle:   \t", metadata[2])
    print("Arrange:  \t", metadata[3])
    print("Vocal:    \t", metadata[4])
    print("Lyrics:   \t", metadata[5])
    print("Original: \t", metadata[6])
    print("DoR:      \t", metadata[7])
    print("Album art url: \t", metadata[8])
    
    assign_metadata(audio, path, t, metadata[0], metadata[1], metadata[2], metadata[3], metadata[4], metadata[5], metadata[6], metadata[7], metadata[8])
    

def already_assigned(path):
    audio = MP3(path)
    k = 0
    
    try: audio['title']; k+=1
    except KeyError: pass
    
    try: audio['album']; k+=1
    except KeyError: pass
    
    try: audio['albumartist']; k+=1
    except KeyError: pass
    
    try: audio['composer']; k+=1
    except KeyError: pass
    
    try: audio['arranger']; k+=1
    except KeyError: pass
    
    try: audio['artist']; k+=1
    except KeyError: pass
    
    try: audio['lyricist']; k+=1
    except KeyError: pass
    
    print(k)
    return k

#assign metadata to all files in audio directory
def main(path, skip_num: bool, skip_albumart: bool, skip_albumname:bool, skip_num_meta=0):
    
    for entry in os.scandir(path):
        print(entry.name)
        
        if (entry.name.endswith(".mp3") or entry.name.endswith(".mp4") or entry.name.endswith(".m4a")) and entry.is_file():
            
            print("====================================================")
            p = path; e = "\\"; n = p + e + entry.name
            print("Filename:",n)
            u = filename_parser.parse_filename(os.path.splitext(entry.name)[0])
            print("Parsed:",u)
            t = (1 if entry.name.endswith(".mp3") else 2)

            
            def album_art(path):
                if entry.name.endswith(".mp3"):
                    try:
                        audio = ID3(path)
                        for k in audio.keys():
                            if u'covr' in k or u'APIC' in k:
                                return True
                        return False
                    except Exception: return False
                elif entry.name.endswith(".mp4"):
                    try:
                        audio = MP4(path)
                        for k in audio.keys():
                            if u'covr' in k or u'APIC' in k:
                                return True
                        return False
                    except Exception: return False
            
            
            def check_meta(path):
                if entry.name.endswith(".mp3"):
                    audio = MP3(n)
                    try: audio['album']; return True
                    except KeyError:     return False
                    
                elif entry.name.endswith(".mp4"):
                    audio = MP4(n)
                    try: audio['\xa9alb']; return True
                    except Exception:      return False

            
            #check if metadata already exists
            if u == "" or u.isspace():           print("Bad parse of filename")
            elif skip_albumart and album_art(n): print("Album art exists")
            elif skip_num and(filename_parser.has_numbers(entry.name[0:2])): print("Filename starts with a number")
            elif skip_albumname and check_meta(n): print("Album already added")
            #elif (already_assigned(n)) >= skip_num_meta: print("Number of requested metadata already assigned")
            else: 
                try: find_metadata(u, n, t)
                except Exception: pass
                
            print("====================================================")
            
            
            
def start():
    
    skim_num = None
    skip_albumart: None
    skip_albumname: None
    
    strs =("Welcome to the Touhou Metadata-Adder script. This script aims to add any metadata that is missing from your song library, catered towards Touhou music. This script will do its best to parse filenames that are not explicitly the song title, however it is not perfect. If you run this script and notice that there are songs that did not get any metadata added to them, please change the filename so that it is exactly the song title (with no other information included), and then run the script again. Additionally, please note that this script might take a while to run; this is deliberate. Please do not attempt to change the value of the sleep() parameter in the code, as it is purposely there to keep from spamming thwiki.cc's servers with requests. This script may also override any existing metadata in some cases, or may occasionally assign the wrong metadata to a song. I have tried to keep the error rate of this happening low, but note that it is still a possibility. It is reccomended to perhaps make a temporary folder and copy the music that you want metadata assigned to, and then provide the path to that folder (instead of your main song library path) to this program. With those disclaimers out of the way, this script will need some information. Press enter to begin or CTRL+C to exit.")
    print(textwrap.fill(strs, 100))
    
    try: input("")
    except KeyboardInterrupt: exit(0)
    
    pathinf = "Firstly, please provide the path to the folder in which the music you want the metadata assigned to is contained."
    print(textwrap.fill(pathinf, 100))
    found = False; path = None
    
    while not found:
        user_inp = input("")
        if os.path.isdir(user_inp):
            found = True
            path = user_inp
        else:
            strs = ("This path does not exist. Please enter the path correctly; It should look something like: C:\\Users\\Admin\\Music\\Touhou")
            print(textwrap.fill(strs, 100))
    
    
    skipnuminf = "Next, we need to know if we should skip any filenames beginning with a number (this is often used to identify songs that come from an album, and thus have metadata assigned to them already). Enter y for yes or n for no."
    print(textwrap.fill(skipnuminf, 100))
    found = False; 

    while not found:
        user_inp = input("")
        if user_inp == "y" or user_inp == "n": found = True
        else:
            strs = ("Please enter only y or n.")
            print(textwrap.fill(strs, 100))
    
    if user_inp == "y": skim_num = True
    elif user_inp == "n": skip_num = False


    skipalbumartinf = "Next, should we skip any songs that already have album art assigned to them? Enter y for yes or n for no."
    print(textwrap.fill(skipalbumartinf, 100))
    found = False; 

    while not found:
        user_inp = input("")
        if user_inp == "y" or user_inp == "n": found = True
        else:
            strs = ("Please enter only y or n.")
            print(textwrap.fill(strs, 100))
    
    if user_inp == "y": skip_albumart = True
    elif user_inp == "n": skip_albumart = False
    
    
    skipalbumnameinf = "Finally, should we skip any songs that already have an album name assigned to them? Enter y for yes or n for no."
    print(textwrap.fill(skipalbumnameinf, 100))
    found = False; 

    while not found:
        user_inp = input("")
        if user_inp == "y" or user_inp == "n": found = True
        else:
            strs = ("Please enter only y or n.")
            print(textwrap.fill(strs, 100))
    
    if user_inp == "y": skip_albumname = True
    elif user_inp == "n": skip_albumname = False
    
    strs = "Starting script.."
    print(textwrap.fill(strs, 100))
    time.sleep(4)
    
    main(path,skim_num,skip_albumart,skip_albumname)
    print("finished")



start()
