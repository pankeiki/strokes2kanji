#!/usr/bin/python3

from defusedxml.ElementTree import parse as parse_xml
import sys
import os.path
import copy
import json

kanjivg_ns = "{http://kanjivg.tagaini.net}"

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
    return stroke_db

def main():
    # Read from json cache if one is present.
    cache_path = os.path.join("database", "kanjivg.cache.json")
    stroke_db = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                stroke_db = json.load(f)
        except json.decoder.JSONDecodeError as e:
            print("Failed to decode kanjivg cache; deleting.")
            os.remove(cache_path)
    if not stroke_db:
        stroke_db = convert_kanji_to_strokes(parse_xml(os.path.join("database", "kanjivg.xml")).getroot())
        with open(cache_path, 'w') as f:
            json.dump(stroke_db, f)

    d = stroke_db
    s = ""
    d_stack = []
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
            print("{0}: {1}".format(s, ' '.join(d[0])))
            probe_list = [d]
            temp = []
            while 1:
                temp = list(set(temp))
                if not probe_list:
                    break
                if len(temp) > 9:
                    break
                probe = probe_list.pop()
                if not probe:
                    continue
                if not probe[1]:
                    temp.extend(probe[0])
                    continue
                for stroke in [str(i) for i in range(1, 6)]:
                    if stroke in probe[1]:
                        temp.extend(probe[1][stroke][0])
                        probe_list.append(probe[1][stroke])
            if temp:
                print(' '.join(temp))
        elif not d:
            print("{0}: No match. Enter 0 to start over or - to go back once.".format(s))

    return 0

if __name__ == "__main__":
    sys.exit(main())
