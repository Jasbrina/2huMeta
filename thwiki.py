"""
Note that this project is not affiliated in any way with thwiki.cc
"""

import requests
import urllib.request
import time, sys, math
from bs4 import BeautifulSoup
import urllib.parse


#song page exists
def case1(soup, time, error_margin):
    metadata_2 = ["", "", "", "", "", "", "", "", ""]

    #find position of wikitable mw-collapsible table
    cond = False; i = 0;
    while not cond:
        if "wikitable mw-collapsible" in soup.find_all('table')[i]['class']:
            cond = True
            break
        i += 1
        
    tt = soup.find_all('table')[i].b.a
    d = soup.find_all('table')[i].find_all('dd')[0]

    #find album art url
    for fnd in soup.find_all('table')[i].find_all('div'):
        if fnd['class'] == "floatright":
            url = None
            if fnd.a is not None:
                if fnd.a.img is not None:
                    try:
                        h = fnd.a.img['srcset']
                        ind = h.find('1.5x,')
                        if ind != -1: url = h[ind+6: len(h)-3]
                    except KeyError: pass
            metadata_2[8] = url 
    
    
    #check if duration matches given song duration (important check to see if grabbing the correct song; could check against other metadata but this is the most reliable check method)
    print(error_margin)
    e = ""
    for y in soup.find_all('table')[i].find_all('tr')[1].find_all('td')[0]:
        if "[" in y and "]" in y: e = y[2:7]     
    
    if e != "":
        minutes =  int(e[0:2])
        seconds =  int(e[3:5])
        t = 60 * minutes + seconds
        t_m = t - error_margin
        t_p = t + error_margin

        if time >= t_m and time <= t_p: pass;
        else: return metadata_2, False
    

    #grab data from table
    def grab_content(s, y):
        k = 1; e = "";
        while d.contents[i+k] is not None and d.contents[i+k].string is not None and s not in d.contents[i+k].string:
            e += d.contents[i+k].string; k += 1;
            
        metadata_2[y] = e
    
    i = 0
    metadata_2[0] = (str(tt.contents[0]))
    metadata_2[1] = d.contents[0].string
    for x in d:
        if x.string is not None and x is not None:
            k = 1; e = "";
            if "（" in x.string and "）" in x.string:
                metadata_2[7] = x.string
                
            if "社团" in x.string: grab_content("编曲", 2)  #circle
            if "编曲" in x.string: grab_content("演唱", 3)  #arrange
            if "演唱" in x.string: grab_content("作词", 4)  #vocal
            if "作词" in x.string: grab_content("原曲", 5)  #Lyrics
            if "原曲" in x.string: #original
                try:
                    while d.contents[i+k] is not None and d.contents[i+k].string is not None:
                        print(d.contents[i+k].string)
                        e += d.contents[i+k].string; k += 1;
                except IndexError:
                    pass
                metadata_2[6] = e         
        i += 1
    
    return metadata_2, True


#case where an album page exists, but song page doesn't
def case2(soup, temp, time, error_margin):
    metadata_2 = ["", "", "", "", "", "", "", "", ""]

    #find position of musicTable
    #note: there may be several musicTables corresponding to the amount of disks in a given album; need to grab all of them
    indices = []; i = 0; 
    try:
        for g in soup.find_all('table'):
            if "wikitable musicTable" in soup.find_all('table')[i]['class']:
                indices.append(i)
            i+=1
    except IndexError: pass;


    #function to test if song duration matches
    def check_duration(r):
        i = indices[r]; 
        m = soup.find_all('table')[i].find_all('td')[index+1]
        if (m['class'] == "time"):
            e = m.string
            if e != "-" and e!= "":          
                minutes =  int(e[0:2])
                seconds =  int(e[3:5])
                t = 60 * minutes + seconds
                t_m = t - error_margin
                t_p = t + error_margin
                print(t, t_m, t_p)

                if time >= t_m and time <= t_p: pass
                else: i = math.inf; 
        return i
    
    #grab correct song from song listing in album table
    #include check for song duration match
    found = False
    for r in range(len(indices)):
        find = temp[0:6] #哀しみに霞む摩天楼
        index = 0
        
        for link in soup.find_all('table')[indices[r]].find_all('td'):
            found = False
            a = link.get('id'); b = None
            
            if link.string == "制作方":
                metadata_2[2] = str(soup.find_all('td')[index+1].string)

            if link is not None:
                if link.a is not None and link.a.string is not None:
                    b = link.a.string
                    if b is not None and find.lower() in b.lower() and "text" not in link['class']:
                        metadata_2[0] = str(b); found = True; 
                
                elif isinstance(a, str) and find.lower() in a.lower() and "text" not in link['class']:
                    metadata_2[0] = str(link.contents[0]); found = True; 
                    
                
            if isinstance(a,str) and not found: 
                x = find.replace(" ", "_")
                if x.lower() in a.lower() and "text" not in link['class']:
                    print(a)
                    metadata_2[0] = str(link.contents[0]); found = True; 

            #check duration
            if found:
                i = check_duration(r)
                if i != math.inf: break
                else: pass 
            index+=1
            
        if found: 
            i = indices[r]; break

    print(found)

    if not found or i == math.inf:
        return ["", "", "", "", "", "", "", "", ""], False

    
    #编曲 = arrange // 再编曲 also acceptable
    #演唱 = vocal
    #作词 = lyrics
    #原曲 = original song
    #extract info from appropriate song in table
    # grab album name, circle, and date of release (if applicable)
    try:
        v = soup.find_all('table')[0]
        if "名称" or "Title" in str(v.contents[2].td.contents[0]):
            metadata_2[1] = str(v.contents[2].contents[1].contents[0])  #album name

        if "制作方" or "Producer" in str(v.contents[3].td.contents[0]):
            metadata_2[2] = str(v.contents[3].contents[1].contents[0].contents[0])  #circle

        if "首发日期" or "Release" in str(v.contents[4].td.contents[0]):
            s = str(v.contents[4].contents[1].contents[0])  #date of release
            x = len(s); s = s[0: x-1];
            metadata_2[7] = s
    except Exception: pass
        

    #grab album art
    for fnd in v.find_all('td'):
        try: 
            if fnd['class'] == "cover-artwork":
                url = None
                if fnd.a is not None:
                    if fnd.a.img is not None:
                        try:
                            h = fnd.a.img['srcset']
                            ind = h.find('1.5x,')
                            if ind != -1: url = h[ind+6: len(h)-3]
                        except KeyError: pass
                metadata_2[8] = url 
        except KeyError: pass


    def grab_content(v, y):
        e = ""
        if v is not None:
            for p in v.contents:
                if p.string is not None: e += str(p.string)
                
            if not e: metadata_2[y] = str(v.a.contents[0]) 
            else:     metadata_2[y] = e
        
    try :
        for j in range(20):
            u = soup.find_all('table')[i].find_all('td')[index+j]
            if "info" in u['class'].lower(): break; print("BREAK");
            v = soup.find_all('table')[i].find_all('td')[index+j+1]

            if isinstance(u.string, str) and ("编曲" in u) or ("再编曲" in u): grab_content(v, 3)
            if isinstance(u.string, str) and ("演唱" in u): grab_content(v, 4)
            if isinstance(u.string, str) and ("作词" in u): grab_content(v, 5)
            if isinstance(u.string, str) and ("社团" in u): grab_content(v, 2)
            if isinstance(u.string, str) and "原曲" in u:
                e = ""
                for j in v.find_all('a'):
                    if j.string is not None: e += j.string; e+= ", "
                metadata_2[6] = e

    except IndexError: pass;

    return metadata_2, True



#grabs initial search request and grabs appropriate thwiki.cc/ page; determines which case to jump to
'''
parameters:
    songname: (string) song name; can include relevant parts of the search
    exact_search: (bool) whether or not to search with quotes
    time_: (int) length of given song; must be in seconds
    error_margin: (int) error += to add when calculating if time duration matches; useful to refine searches
'''
def main(songname, exact_search, time_, error_margin):
    # song name*, album name, circle, arrange, vocal, lyrics, original title, date, url
    metadata = ["", "", "", "", "", "", "", "", "", ""]
    
    #grab initial search request
    temp = songname
    songname = songname.replace(" ", "+")
    if exact_search:
        o = '"'; n = o; n += songname; n += o
        songname = n
    print("SONGNAME:", songname)
    
    urlbase = "https://www.google.ca/search?q=site%3Athwiki.cc+"
    urlbase += songname
    #print("url:", urlbase)

    #soup for initial google search
    response = requests.get(urlbase)
    soup = BeautifulSoup(response.text, "html.parser")
    print(response)

    i = 0; broke = False
    links = []; links_2 = []
    link_indices = []
    
    for link in soup.find_all('a'):
        if "https://thwiki.cc/" in str(link.get('href')) and not("imgres" in str(link.get('href'))):
            broke = True;
            links.append(str(link.get('href'))) 
            link_indices.append(i)

        i+=1

    if not broke: return metadata
    
    for r in range(len(link_indices)):
        link = soup.find_all('a')[link_indices[r]]
        data = urllib.parse.parse_qs(urllib.parse.urlparse(link['href']).query)
        no_lang = data['q'][0]

        #default to standard language settings
        if ("setlang" in data['q'][0]):
            tmp = data['q'][0]
            x = len(tmp) - 11
            no_lang = tmp[0:x]
        links_2.append(no_lang)
        

    #this tests out multiple different links if the first result does not return the correct match; sleep penalty of 10 seconds after the first request so as to not spam their server with requests
    for n in range(len(links_2)):
        found = False
        time.sleep(1) if n == 0 else time.sleep(10)
        response = requests.get(links_2[n])
        case = None
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser", multi_valued_attributes=None)
            
            if len(soup.find_all('tr')) != 0:
                cc = soup.find_all('tr')[0].string
                if isinstance(cc, str) and "曲目信息" in cc:
                    metadata, found = case1(soup, time_, error_margin); 
                    case = 1
                    
                elif isinstance(cc, str) and ("基本信息" in cc):
                    metadata, found = case2(soup, temp, time_, error_margin); 
                    case = 2
                           
                else:
                    found = False
                    case = 3

        print("Case =", case)
        if found: break

    if metadata[1][0:1] == " ": metadata[1] = metadata[1][1:len(metadata[1])]
    return metadata

   
