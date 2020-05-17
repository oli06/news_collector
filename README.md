# news_collector
Collect news articles from puplic news pages and saves them into a mongoDB.

## Crawlers
Currently support for four main german news pages
* https://www.n-tv.de/ (ntv)
* https://www.spiegel.de/ (spiegel)
* https://www.tagesschau.de/ (tagesschau)
* https://www.zeit.de/ (zeit)
* https://www.golem.de/ (golem) (it-news)

Run a crawler with `scrapy crawl ntv`.

More information at [Scrapy](https://docs.scrapy.org/en/latest/topics/spiders.html) and [MongoDB](https://docs.mongodb.com/manual/) 

## What it does
1. Crawls articles from the homepages and their references articles (`named_references`) inside the text (see above) of german newspages.
2. Every spider must be run on its own
3. Not all homepage articles are parsed, only the first few
4. Use `self.total_parsed` inside each spider to define a maximum of articles (otherwise spiders could run extremely long)
5. 
6. Article information is saved to the collection `articles` in a mongo db called `news` (hosted locally)
7. Article raw html is saved to the collection `metadata`in a mongo db called `news` (hosted locally)

Example data for an article about [football during corona](https://www.n-tv.de/sport/Mediziner-haelt-Fussball-mit-Fans-fuer-moeglich-article21785968.html)


{'agency': 'n-tv',
 'authors': ['Max Mustermann'],
 'category': 'Sport',
 'date': 1589751006,
 'headline': 'Mediziner hält Fußball mit Fans für möglich',
 'is_update': False,
 'kicker': 'Zugang wie zu Ikea?',
 'named_references': {'Fußball-Bundesliga': 'https://www.sportschau.de/fussball/bundesliga/spieltag/index.html'},
 'tags': ['Fußball-Bundesliga',
          'Corona-Krise',
          'Pandemien',
          'Epidemien',
          'Gesundheit',
          'Fußball'],
 'teaser': 'Der Neustart der Fußball-Bundesliga unter strengen Auflagen sorgt '
           'seit Wochen für Diskussionen. Für den Sportmediziner Fritz Sörgel '
           'hat er den "Charakter einer wissenschaftlichen Studie". Auch die '
           'Anwesenheit von Zuschauern bei kommenden Spielen hält er für '
           'machbar - unter bestimmten Voraussetzungen.',
 'text': 'Der Pharmakologe und Sportmediziner Fritz Sörgel hält Fußball-Spiele '
         'mit einer geringen Anzahl an Zuschauern für bald möglich. "Ich sehe '
         'die Möglichkeit der schrittweisen Anpassung", sagte er im Interview '
         'mit dem "Kölner Stadt-Anzeiger": "Ich weiß nicht genau, wie '
         'realistisch das ist, aber wenn man sagen könnte: Der Zugang von '
         'Menschen zum Stadion kann so geregelt werden wie der Zugang der '
         'Kunden zum Ikea, und es wäre möglich, im Stadion die notwendigen '
         'Abstände einzuhalten, dann wüsste ich ehrlich gesagt nicht, was '
         'dagegen einzuwenden wäre, Spiele vor reduziertem Publikum '
         'zuzulassen."   Dass die Bundesliga den Spielbetrieb wieder aufnimmt, '
         'habe den "Charakter einer wissenschaftlichen Studie", sagte Sörgel: '
         '"Ein solches Konzept, rund 1700 Personen in einer Hygiene-Zone '
         'inmitten einer Pandemie konsequent zu testen, ist so noch nie '
         'irgendwo durchgeführt worden." In einem Gastbeitrag in der '
         '"Mainpost" schrieb der Leiter des Instituts für Biomedizinische und '
         'Pharmazeutische Forschung in Nürnberg: "Was aber noch viel wichtiger '
         "ist: Ausgerechnet der zu meiner Jugendzeit als 'Proletensport' "
         'bezeichnete Fußball könnte Financier werden für den gesamten Sport '
         'und das Kulturleben, als er in einer Art Kollateraleffekt '
         'wissenschaftliche Grundlagen zu Fragen von Mindestabstand, '
         'Kontagiosität und vieler anderer Aspekte der Corona-Krise liefert." '
         'Zudem komme dem Videobeweis nun eine neue Bedeutung zu: "In welcher '
         'Szene könnte sich Thomas Müller den Virus eingefangen haben, wo der '
         'doch gar nicht so körperlich spielt", schrieb Sörgel: "Selten war '
         'Zeitlupe hilfreicher."   Die Ergebnisse des Testversuchs seien zwar '
         'nicht repräsentativ. "Es sind weder extrem alte Menschen noch Kinder '
         'vertreten. Dennoch werden die Daten ihren Wert haben, denn sie '
         'beschreiben eine Gruppe in der Pandemie unter besonderen Umständen", '
         'sagte Sörgel. Und glaubt, dass Nationalmannschaftsarzt Tim Meyer, '
         'der die Taskforce leitete, sie zusammen mit seiner Saarbrücker '
         'Kollegin Barbara Gärtner veröffentlichen wird. Sie hätten das '
         'Konzept mit der DFL ausgearbeitet, so der 69-Jährige im "Kölner '
         'Stadt-Anzeiger", "und ich nehme an, sie werden genügend akademischen '
         'Ehrgeiz haben, es selbst zu publizieren. Und ich hoffe schnell."',
 'url': 'https://www.n-tv.de/sport/Mediziner-haelt-Fussball-mit-Fans-fuer-moeglich-article21785968.html',
 'raw': 'raw html'}