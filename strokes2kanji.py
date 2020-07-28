#!/usr/bin/python3

from defusedxml.ElementTree import parse as parse_xml
import sys
import os.path
import copy

stroke_db = None
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
    untransformed_strokes = [i[0] for i in s.split('/')]
    transformed_strokes = set()
    checklists = (horizontal, vertical, falling_left, dot, turning)
    for stroke in untransformed_strokes:
        found = False
        for n, l in enumerate(checklists):
            if found: break
            elif stroke in l:
                transformed_strokes.add(n + 1)
                found = True
        if not found:
            # Found unrecognized stroke type. Make it a wildcard.
            transformed_strokes.update({1, 2, 3, 4, 5})
    return transformed_strokes

def extract_stroke_groups(g):
    if g.tag == 'path':
        return [transform_stroke_type(g.get(kanjivg_ns + 'type'))]

    if g.tag != 'g':
        raise ValueError("Expected only elements with tag == 'g' or 'path'.")
    elif len(g) == 0:
        raise ValueError("Expected g to have children.")

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
                    d[stroke] = (set(), {})
                d = d[stroke][1]
            if strokes[-1] not in d:
                d[strokes[-1]] = ({k}, {})
            else:
                d[strokes[-1]][0].add(k)
    return stroke_db

def main():
    global stroke_db
    stroke_db = convert_kanji_to_strokes(parse_xml(os.path.join("database", "kanjivg.xml")).getroot())
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
                        d = d[int(c)]
                    else:
                        d = d[1][int(c)]
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
                if len(probe) == 0 or not probe[1]:
                    temp.extend(probe[0])
                    continue
                for stroke in [5, 4, 3, 2, 1]:
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
