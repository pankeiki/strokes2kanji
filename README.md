# strokes2kanji

[![asciicast](https://asciinema.org/a/350528.svg)](https://asciinema.org/a/350528)

Look up kanji by stroke type and order, similar to the [stroke count method or wubihua](https://en.wikipedia.org/wiki/Stroke_count_method) in many Chinese IMEs, from the comfort of your terminal. The kanji strokes are extracted from [KanjiVG](http://kanjivg.tagaini.net), so actual Japanese kanji are returned instead of Chinese variants. Kanji readings and meaning are extracted from [KANJIDIC](http://www.edrdg.org/wiki/index.php/KANJIDIC_Project).

## File dependencies
* kanjidic2.xml, extracted from the [KANJIDIC2](http://www.edrdg.org/wiki/index.php/KANJIDIC_Project) file ("kanjidic2.xml.gz").
    * [KANJIDIC License](http://www.edrdg.org/edrdg/licence.html).
* kanjivg-\<datetime\>.xml.gz, from the [kanjivg repository](https://github.com/KanjiVG/kanjivg/releases).
    * [KanjiVG License](https://github.com/KanjiVG/kanjivg/blob/master/COPYING).
    * [KanjiVG's Website](http://kanjivg.tagaini.net)

## Software dependencies
* [Python 3.6+](https://www.python.org/)
    * defusedxml package (`pip install [--user] defusedxml`)

## Instructions
1. Create an empty `database` directory.
2. Download kanjivg then extract into ./database/kanjivg.xml.
3. Download kanjidic2 then extract into ./database/kanjidic2.xml.
4. Run strokes2kanji.py without arguments.
5. At the prompt (`> `), enter the [wubihua](https://en.wikipedia.org/wiki/Stroke_count_method) numbers to reach your kanji.
    1. Enter `q` to quit, or just do Ctrl+C.
    2. Enter `0` to clear all entered strokes.
    3. Enter one or more `-` to undo the same number of entered strokes.
    4. In addition to wubihua's 1 through 5 inputs, `*` is also usable as a wildcard stroke.

## Optional steps
* Copy ./default\_settings.json into ./database/settings.json and modify it to show more or fewer readings or information.
    * Permissible 'display' types: 'pinyin', 'korean\_r', 'korean\_h', 'vietnam', 'ja\_on', 'ja\_kun', 'meaning', 'remaining\_strokes'
