[![asciicast](https://asciinema.org/a/350528.svg)](https://asciinema.org/a/350528)

Look up kanji by stroke type and order, similar to the stroke count method or wubihua in many Chinese IMEs, from the comfort of your terminal.

# File dependencies:
* kanjidic2.xml, extracted from the [KANJIDIC2](http://www.edrdg.org/wiki/index.php/KANJIDIC_Project) file ("kanjidic2.xml.gz").
    * [KANJIDIC License](http://www.edrdg.org/edrdg/licence.html).
* kanjivg-\<datetime\>.xml.gz, from the [kanjivg repository](https://github.com/KanjiVG/kanjivg/releases).
    * [KanjiVG License](https://github.com/KanjiVG/kanjivg/blob/master/COPYING).
    * [KanjiVG's Website](http://kanjivg.tagaini.net)

# Software dependencies:
* Python 3.7
    * defusedxml package (`pip install [--user] defusedxml`)

# Instructions:
1. Create an empty `database` directory.
2. Download kanjivg then extract into ./database/kanjivg.xml.
3. Download kanjidic2 then extract into ./database/kanjidic2.xml.
4. Run strokes2kanji.py without arguments.

# Optional steps:
* Copy ./default\_settings.json into ./database/settings.json and modify it to show more or fewer readings or information.
    * Permissible 'display' types: 'pinyin', 'korean\_r', 'korean\_h', 'vietnam', 'ja\_on', 'ja\_kun', 'meaning', 'remaining\_strokes'
