import re
import os

#returns None if no number in string s
def has_numbers(s):
    return re.search('\d', s)


#parses filename: sometimes a filename can be strangely named (contains extra irrelevant info); this function parses and cleans the string as well as possible
def parse_filename(s):
    original = s
    
    l = ["【", "『", "「", "[", "(", "（", "_", "<", "\\", "{", "-"]
    if not (any(substring in s for substring in l)) and (has_numbers(s) is None): return s
    
    #remove 【】brackets- may be either near start or end of string
    #it is assumed that any words inside these types of brackets is not extremely significant- i.e., it is not the song title
    while ("【" in s):
        pos_s = s.find("【")
        
        #start bracket
        if (pos_s < len(s)/3):
            pos_e = s.find("】")
            if pos_e == -1: pos_e = pos_s #rare case where there is no closing bracket
            s = s[pos_e+1:len(s)]
            
        #end bracket
        else: s = s[0:pos_s]
            
            
    def bracket(bracket_s, bracket_e ,s):
        while (bracket_s in s):
            pos_s = s.find(bracket_s)
            b = s[0: pos_s]
            pos_e = s.find(bracket_e)
            if pos_e == -1: pos_e = pos_s #rare case where there is no closing bracket
            
            #start bracket
            #in some cases, these brackets may actually enclose the song title; need to check for it
            if (pos_s < len(s)/3) and (b is "" or b.isspace()) or ("東方" in b):      
                if (bracket_s == "(") or (bracket_s == "["): x = "\\" + bracket_s
                else: x = bracket_s
                d = [s.start() for s in re.finditer(x, s)] 
                
                if len(d) == 1:
                    end = s[pos_e+1:]
                    
                    #checks if essentially「.」 is the only bracket; then song name is likely contained within 
                    if end.isspace() or end == "": s = s[pos_s+1: pos_e] 
                    else: s = s[pos_e+1:len(s)]                         
                
                else: s = s[pos_e+1:len(s)]

            #end bracket
            else: s = s[0:pos_s]

        return s
        
    
    s = bracket("「","」",s)
    s = bracket("『","』",s)
    s = bracket("[","]",s)
    s = bracket("{","}",s)
    s = bracket("（","）",s)
    
    def divider(div, s):
        while (div in s):
            d = [s.start() for s in re.finditer(div, s)] 
            e = s[d[0]+3: len(s)]
            keep = ["remix", "mix", "remaster"]
            br = False

            if (any(substring in e.lower() for substring in keep) and div!=" - "):
                s = s
                br = True
            
            else: s = e
            if br: break
        return s
        
    s = divider(" - ", s)    
    s = divider(" _ ", s)
    s = divider(" － ", s)
    #s = divider(" ～ ", s) #often part of a song name
    s = divider(" | ", s)
    s = divider(" ~ ", s)
    s = divider(" __ ", s)
    

    #() brackets check; this one is a little more tricky as we may want to include what is in brackets sometimes
    if ("(" in s):
        pos_s = s.find("(")
        pos_e = s.find(")")
        if pos_e == -1: pos_e = pos_s #rare case where there is no closing bracket  
        z = s[pos_s+1: pos_e]
        
        keep = ["remix", "mix", "remaster"]

        if (any(substring in z.lower() for substring in keep)): s = s
        else: s = s[0:pos_s]
        
    
    if (has_numbers(s[0:2])):
        if (s[2:3] == "."):
            s = s[3:len(s)]
        else: s = s[2:len(s)]

    while (s[0:1] == " "): s = s[1:len(s)] 
    return s
