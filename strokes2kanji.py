#!/usr/bin/python3

from defusedxml.ElementTree import parse as parse_xml
import sys, os.path

stroke_db = None
kanjivg_ns = "{http://kanjivg.tagaini.net}"

def transform_stroke_type(s):
    # Possible stroke types, from https://github.com/KanjiVG/kanjivg/blob/master/strokes.txt:
    # ㇔ ㇐ ㇑ ㇒ ㇏ ㇀ ㇖ ㇚ ㇂ ㇙ ㇕ ㇗ ㇛ ㇜ ㇇ ㇄ ㇆ ㇟ ㇊ ㇉ ㇋ ㇌ ㇈ ㇅ ㇞
    # Group them into 5 like Wubihua
    horizontal = ['㇐', '㇀']
    vertical = ['㇑']
    falling_left = ['㇒']
    dot = ['㇔', '㇏']
    # The rest is assumed to be Turning.
    s = s[0]
    checklists = (horizontal, vertical, falling_left, dot)
    for n, l in enumerate(checklists):
        if s in l:
            return n + 1
    return len(checklists) + 1

def flatten_stroke_groups(g):
    if g.tag == 'path':
        return [transform_stroke_type(g.get(kanjivg_ns + 'type'))]

    if g.tag != 'g':
        raise ValueError("Expected only elements with tag == 'g' or 'path'.")
    elif len(g) == 0:
        raise ValueError("Expected g to have children.")

    ret = []
    for child in g:
        ret.extend(flatten_stroke_groups(child))
    return ret

def convert_kanji_to_strokes(stroke_db_root):
    # stroke_db: n-ary tree allowing traversal to kanji by stroke types.
    # For example, accessing stroke_db with 3 1 2 3 4 5 4 = 私
    stroke_db = {}
    for kanji in stroke_db_root:
        if len(kanji) != 1:
            raise ValueError("Expected each kanji to only have one 'g' child.")
        g = kanji[0]
        if kanjivg_ns + 'element' not in g.keys():
            continue
        k = g.get(kanjivg_ns + 'element')
        try:
            strokes = flatten_stroke_groups(g)
        except Exception as e:
            print("Giving up on {0} due to error: {1}".format(k, e))
            continue
        d = stroke_db
        for stroke in strokes[:-1]:
            if stroke not in d:
                d[stroke] = ([], {})
            d = d[stroke][1]
        if strokes[-1] not in d:
            d[strokes[-1]] = ([k], {})
        else:
            d[strokes[-1]][0].append(k)
    return stroke_db

def find(stroke_db, strokes, n=10):
    pass

def main():
    global stroke_db
    stroke_db = convert_kanji_to_strokes(parse_xml(os.path.join("database", "kanjivg.xml")).getroot())
    d = stroke_db
    s = ""
    while 1:
        i = input("> ")
        if i == "0":
            d = stroke_db
            s = ""
            continue
        elif i == "q":
            break
        for c in i:
            if c in "12345":
                try:
                    if not s:
                        d = d[int(c)]
                    else:
                        d = d[1][int(c)]
                except KeyError as e:
                    print("No more match. Enter 0 to start over.")
                    d = {}
                s += c
        if d and s:
            print("{0}: {1}".format(s, ' '.join(d[0])))
            probe_list = [d]
            temp = []
            while 1:
                if not probe_list:
                    break
                if len(temp) > 9:
                    break
                probe = probe_list.pop()
                if len(probe) == 0 or not probe[1]:
                    temp.extend(probe[0])
                    continue
                for stroke in [5, 4, 3, 2, 1]:
                    if stroke in probe[1]:
                        temp.extend(probe[1][stroke][0])
                        probe_list.append(probe[1][stroke])
            if temp:
                print(' '.join(temp))
                
    return 0

if __name__ == "__main__":
    sys.exit(main())
