#!/usr/bin/python3

from defusedxml.ElementTree import parse as parse_xml
import sys
import os.path
import copy
import json

kanjivg_ns = "{http://kanjivg.tagaini.net}"
settings = {
    'display': ['ja_on', 'ja_kun', 'meaning', 'remaining_strokes'],
    'lookahead': 10,
}

def transform_stroke_type(s):
    # Possible stroke types, from https://github.com/KanjiVG/kanjivg/blob/master/strokes.txt:
    # ㇔ ㇐ ㇑ ㇒ ㇏ ㇀ ㇖ ㇚ ㇂ ㇙ ㇕ ㇗ ㇛ ㇜ ㇇ ㇄ ㇆ ㇟ ㇊ ㇉ ㇋ ㇌ ㇈ ㇅ ㇞
    # Group them into 5 like Wubihua
    horizontal = "㇐㇀"
    vertical = "㇑"
    falling_left = "㇒"
    dot = "㇔㇏"
    turning = "㇖㇚㇂㇙㇕㇗㇛㇜㇇㇄㇆㇟㇊㇉㇋㇌㇈㇅㇞"
    # If there are multiple possible strokes, return a list.
    # Also strip letter suffix, e.g. "b", "v", "a".
    try:
        untransformed_strokes = [i[0] for i in s.split('/')]
    except IndexError as e:
        # kanjivg has a 'path' element with an empty stroke.
        # Replace it with wildcard.
        return {str(i) for i in range(1, 6)}
    transformed_strokes = set()
    checklists = (horizontal, vertical, falling_left, dot, turning)
    for stroke in untransformed_strokes:
        found = False
        for n, l in enumerate(checklists):
            if found: break
            elif stroke in l:
                transformed_strokes.add(str(n + 1))
                found = True
        if not found:
            # Found unrecognized stroke type. Make it a wildcard.
            return {str(i) for i in range(1, 6)}
    return transformed_strokes

def extract_stroke_groups(g):
    if g.tag == 'path':
        stroke = g.get(kanjivg_ns + 'type')
        if not stroke:
            # kanjivg has a 'path' element without a stroke type.
            # Make it a wildcard.
            return [{str(i) for i in range(1, 6)}]
        return [transform_stroke_type(stroke)]

    if g.tag != 'g':
        raise ValueError("Expected only elements with tag == 'g' or 'path'.")
    elif len(g) == 0:
        # g has no children. Make this into one wildcard stroke.
        return [{str(i) for i in range(1, 6)}]

    ret = []
    for child in g:
        ret.extend(extract_stroke_groups(child))
    return ret

def convert_sparse_sets_to_full(space, sparse_set):
    # Sparse set:
    # [{1}, {2, 3}, {4, 5}]
    #
    # Full set, converted from the above:
    # [ [1, 2, 4],
    #   [1, 2, 5],
    #   [1, 3, 4],
    #   [1, 3, 5] ]
    n = 1
    while sparse_set:
        current_level = sparse_set.pop(0)
        if len(current_level) > 1:
            cp = copy.deepcopy(space)
            m = n * len(current_level)
            o = n
            while n < m:
                n += o
                space.extend(cp)
            for i, lst in enumerate(space):
                lst.append(list(current_level)[i // o])
        else:
            for lst in space:
                lst.append(list(current_level)[0])

def convert_kanji_to_strokes(stroke_db_root):
    # stroke_db: n-ary tree allowing traversal to kanji by stroke types.
    # For example, accessing stroke_db with 3 1 2 3 4 5 4 = 私
    # stroke_db could also be indexed by the kanji itself to retrieve
    # the ordered strokes.
    stroke_db = {}
    for kanji in stroke_db_root:
        if len(kanji) != 1:
            raise ValueError("Expected each kanji to only have one 'g' child.")
        g = kanji[0]
        if kanjivg_ns + 'element' not in g.keys():
            continue
        k = g.get(kanjivg_ns + 'element')
        try:
            sparse_strokes_sets = extract_stroke_groups(g)
        except Exception as e:
            print("Giving up on {0} due to error: {1}".format(k, e))
            continue

        strokes_sets = [[]]
        convert_sparse_sets_to_full(strokes_sets, sparse_strokes_sets)
        for strokes in strokes_sets:
            d = stroke_db
            for stroke in strokes[:-1]:
                if stroke not in d:
                    d[stroke] = ([], {})
                d = d[stroke][1]
            if strokes[-1] not in d:
                d[strokes[-1]] = ([k], {})
            elif k not in d[strokes[-1]][0]:
                d[strokes[-1]][0].append(k)
        stroke_db[k] = ''.join([str(s) for s in strokes_sets[0]])
    return stroke_db

def extract_kanji_info(root):
    # Kanji_db: Map each kanji to a dictionary of readings.
    kanji_db = {}
    # First element in kanjidic2 is "header". Skip it.
    for n, character in enumerate(root[1:]):
        kanji = None
        reading_meaning = None

        for element in character:
            if element.tag == 'literal':
                kanji = element.text
            elif element.tag == 'reading_meaning':
                reading_meaning = element
            if kanji and reading_meaning:
                break
        if not kanji:
            raise ValueError("Failed to find kanji or reading/meaning at character #{0}".format(n))
        if not reading_meaning:
            #print("{0} has no reading_meaning element, skipping".format(kanji))
            continue

        rmgroup = None
        for element in reading_meaning:
            if element.tag == 'rmgroup':
                rmgroup = element
            if rmgroup:
                break

        if not rmgroup:
            #print("{0} has no rmgroup element, skipping".format(kanji))
            continue
        kanji_db[kanji] = {'meaning' : []}
        for element in rmgroup:
            if element.tag == 'reading':
                typ = element.get('r_type')
                rd = element.text
                if typ not in kanji_db[kanji]:
                    kanji_db[kanji][typ] = [rd]
                else:
                    kanji_db[kanji][typ].append(rd)
            elif element.tag == 'meaning' and not element.items():
                kanji_db[kanji]['meaning'].append(element.text)
    return kanji_db

def get_kanji_info(kanji_db, kanji):
    if kanji not in kanji_db or 'display' not in settings or not settings['display']:
        return ""
    s = "| "
    info = kanji_db[kanji]
    permissible_kanji_info_type = ['pinyin', 'korean_r', 'korean_h', 'vietnam', 'ja_on', 'ja_kun', 'meaning']
    for typ in settings['display']:
        if typ in permissible_kanji_info_type and typ in info:
            s += ', '.join(info[typ])
            s += " | "
    return s

def load_cache(root, db_file, cache, loader):
    # Read from json cache if one is present.
    cache_path = os.path.join(root, cache)
    db = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                db = json.load(f)
        except json.decoder.JSONDecodeError as e:
            print("Failed to decode {0}; deleting.".format(cache))
            os.remove(cache_path)
    if not db:
        db = loader(parse_xml(os.path.join(root, db_file)).getroot())
        with open(cache_path, 'w') as f:
            json.dump(db, f)
    return db

def load_settings(root, filename):
    global settings
    temp_settings = {}
    path = os.path.join(root, filename)
    if os.path.exists(path):
        try:
            with open(path) as f:
                temp_settings = json.load(f)
        except json.decoder.JSONDecodeError as e:
            print("Failed to decode {0}; using default settings.".format(path))
    if temp_settings:
        settings = temp_settings

def main():
    root = "database"
    stroke_db_file = "kanjivg.xml"
    stroke_db_cache = "kanjivg.cache.json"
    stroke_db = load_cache(root, stroke_db_file, stroke_db_cache, convert_kanji_to_strokes)
    kanji_db_file = "kanjidic2.xml"
    kanji_db_cache = "kanjidic2.cache.json"
    kanji_db = load_cache(root, kanji_db_file,  kanji_db_cache, extract_kanji_info)
    load_settings(root, "settings.json")

    d = stroke_db
    s = ""
    d_stack = []
    lookahead = 10 if 'lookahead' not in settings else int(settings['lookahead'])
    while 1:
        i = input("> ")
        if i == "0":
            d = stroke_db
            s = ""
            d_stack = []
            continue
        elif i == "q":
            break
        for c in i:
            if c in "12345":
                d_stack.append(d)
                try:
                    if not s:
                        d = d[c]
                    else:
                        d = d[1][c]
                except KeyError as e:
                    d = {}
                s += c
            elif c == '-' and s and d_stack:
                s = s[:-1]
                d = d_stack.pop()
        if d and s:
            if 'display' not in settings or not settings['display']:
                print("{0}: {1}".format(s, ' '.join(d[0])))
            else:
                print("{0}:".format(s))
                for kanji in d[0]:
                    print("{0} {1}".format(kanji, get_kanji_info(kanji_db, kanji)))
            probe_list = [d]
            temp = []
            while 1:
                temp = list(set(temp) - set(d[0]))
                if not probe_list:
                    break
                if len(temp) >= lookahead:
                    break
                probe = probe_list.pop(0)
                if not probe:
                    continue
                if not probe[1]:
                    temp.extend(probe[0])
                    continue
                for node in probe[1].values():
                    temp.extend(node[0])
                    probe_list.append(node)
            temp.sort(key=lambda element: len(stroke_db[element]))
            temp = temp[:lookahead]
            if 'display' not in settings or not settings['display']:
                print(' '.join(temp))
            else:
                for kanji in temp:
                    if 'display' in settings and 'remaining_strokes' in settings['display']:
                        print("...{0} ".format(stroke_db[kanji][len(s):]), end='')
                    print("{0} {1}".format(kanji, get_kanji_info(kanji_db, kanji)))
        elif not d:
            print("{0}: No match. Enter 0 to start over or - to go back once.".format(s))

    return 0

if __name__ == "__main__":
    sys.exit(main())
