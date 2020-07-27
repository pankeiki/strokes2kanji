# File dependencies:
* kanjidic2.xml, extracted from the [KANJIDIC2](http://www.edrdg.org/wiki/index.php/KANJIDIC_Project) file ("kanjidic2.xml.gz").
    * [KANJIDIC License](http://www.edrdg.org/edrdg/licence.html).
* kanjivg-<datetime>.xml.gz, from the [kanjivg repository](https://github.com/KanjiVG/kanjivg/releases).
    * [KanjiVG License](https://github.com/KanjiVG/kanjivg/blob/master/COPYING).
    * [KanjiVG's Website](http://kanjivg.tagaini.net)

# Software dependencies:
* Python 3.7
    * defusedxml package (`pip install [--user] defusedxml`)
    * keyboard package (`pip install [--user] keyboard`)

# Instructions:
1. Download kanjivg then extract into ./database/kanjivg.xml.
2. Download kanjidic2 then extract into ./database/kanjidic2.xml.
3. Run strokes2kanji.py without arguments.
