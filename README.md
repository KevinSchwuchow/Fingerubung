# Abgabe
Das Programm `main.py` schreibt die Ergebnisse im Markdown Format in den Output Ordner.

# Laufbedingungen
`networkx`  
`spacy`  
`Python 3.7+`  da dataclasses verwendet werden  
graphviz muss installiert sein(glaube ich...)  
Das Betriebsystem sollte nicht windows sein, denn in diesem Fall gibt es den text einfach nur aus und speichert ihn nicht


# Infos
Die Daten können im Json Format gespeichert werden und werden dies aus, sie liegen Unter den folgenden links 
[Highlights_of_the_Prado_Museum.xml.json](output/Highlights_of_the_Prado_Museum.xml.json)  
[Bicycles.xml.json](output/Bicycles.xml.json)

Das Programm speichert die Analyse in Markdown Dateien in diesen finden man auch den Graph. Man findet diese an folgenen Orten

[Highlights_of_the_Prado_Museum](output/Highlights_of_the_Prado_Museum.xml.md)  
[Bicycles](output/Bicycles.xml.md)

Hier die Farben die, die Kanten und Knoten im Graphen haben

```python
color_table = {
    "PLACE": "red",
    "SPATIAL_ENTITY": "green",
    "PATH": "blue",
    "NONMOTIONEVENT": "orange",

    "QSLINK": "red",
    "OLINK": "blue",
    }
```