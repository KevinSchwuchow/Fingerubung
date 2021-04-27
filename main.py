import os
import xml.etree.ElementTree as ET
from collections import defaultdict

from dataclasses import dataclass, asdict
from typing import Any, Dict, Sequence, Tuple, List

import json

import graphviz

import networkx as nx

from networkx.drawing.nx_agraph import to_agraph

import spacy

import sys


@dataclass
class Tag():
    name: str
    id: str
    attrib: Dict[str, str]

    def get_label(self, id: str):
        text = self.attrib["text"]
        if not(text):
            text = self.attrib.get("comment", "")
            text = ""

        # return self.name+"\n"+id+"\n\n"+text
        return text


@dataclass
class Tags:
    """Class for keeping track of an item in inventory."""
    tags: Dict[str, List[Tag]]
    text: str
    token_counter: Dict[str, int]

    def findx(self, x: str):
        tag = self.tags["PLACE"]
        res = list(filter(lambda y: y.id == x, tag))
        if len(res) == 0:
            return ""

        return (res[0].attrib["text"])

    def get_mergeable(self):
        metalinks = list(map(lambda x: (
            x.attrib["fromID"], x.attrib["toID"]),
            filter(lambda xy: (xy.attrib.get("relType") == "COREFERENCE"), self.tags.get("METALINK", []))))

        mergeable = []

        while len(metalinks) != 0:
            x = metalinks.pop()
            id1 = x[0]
            id2 = x[1]

            merge = [id2, id1]

            metalinks_new = []
            for y in metalinks:
                if (id1 in y) or (id2 in y):
                    merge.append(y[0])
                    merge.append(y[1])
                else:
                    metalinks_new.append(y)

            mergeable.append(merge)
            metalinks = metalinks_new

        # print(mergeable)

        mergeable = [list(set(x)) for x in mergeable]

        lookup_table = dict()

        for merge in mergeable:
            helper = list(zip(map(self.findx, merge), merge))
            # print(helper)
            first = merge[0]

            for x in merge:
                lookup_table[x] = first

        return lookup_table

    def to_file(self, path):
        with open(path, "w") as file:
            file.write(json.dumps(asdict(self), indent=4))

    def print_pos(self):
        print_table("Wie oft kommen welche PoS-Tags vor?",
                    ("Tag",), self.token_counter.items())


def print_table(name: str, y_label: Tuple[str, ...], items, limit=None):
    pos_sorted = list(sorted(items,
                             key=lambda x: x[1], reverse=True))[:limit]

    print("##", name)

    t = "| Count |"
    maxlength = max(len(str(pos_sorted[0][1])), len(t)-1)
    print(t, f" {' | '.join(y_label)} |", sep="")
    print("| -- |" + " -- |"*len(y_label))

    # print(f"`{pos_sorted}`")
    for x, y in pos_sorted:
        xx = x if type(x) == tuple else (x,)
        length = len(str(y))-1
        print("|", y, " | ", ' | '.join([str(xxx)
                                         for xxx in xx]), " |", sep="")

    print()


def from_file(file_name: str) -> Tags:

    tags = Tags(tags=dict(), text="", token_counter={})

    root = ET.parse(file_name).getroot()

    x = root.findall('TAGS/*')

    tags.text = root.find("TEXT").text or ""

    for y in x:
        attrib = y.attrib
        id = attrib.pop("id")
        tag = Tag(attrib=attrib, id=id, name=y.tag)

        if(tags.tags.get(tag.name) == None):
            tags.tags[tag.name] = []

        tags.tags[tag.name].append(tag)

    return tags


def do_spacy_stuff(tags: Tags):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(tags.text)

    token_counter = defaultdict(lambda: 0)

    tokens: Sequence[Tag] = []
    start = 0
    for token in (doc):
        word_len = len(token.text_with_ws)

        token_counter[token.pos_] += 1

        tokens.append(Tag("TOKEN", f"token{len(tokens)+1}", {
            "start": str(start),
            "end": str(start+word_len),
            "pos_tag": token.pos_
        }),)

        start += word_len

    start = 0

    sentences: Sequence[Tag] = []

    for sent in doc.sents:
        sent_len = len(sent.text_with_ws)

        sentences.append(Tag("SENTENCE", f"sentence{len(sentences)+1}", {
            "start": str(start),
            "end": str(start+sent_len),
        }),)
        start += sent_len

    tags.tags["TOKEN"] = tokens
    tags.tags["SENTENCE"] = sentences

    token_counter = dict(token_counter)

    tags.token_counter = token_counter


def between(x):
    start = int(x.attrib["start"])
    end = int(x.attrib["end"])
    sentence_length = (end-start)//10

    return (sentence_length*10, (1+sentence_length)*10)


def histrogram(x: Any):
    hist = defaultdict(lambda: 0)
    for y in x:
        hist[y] += 1

    return dict(hist)


def main(filename):
    stdout = sys.stdout
    outputfile = "./output/"+filename.split('/')[-1]+".md"
    if(os.name == "posix"): # windows probally does not support redirection
        sys.stdout = open(outputfile, 'w')
    
    print(f"# {filename.split('/')[-1]}")


    res = from_file(filename)

    k = map(lambda x: (x.attrib["relType"]), res.tags["QSLINK"])
    how_many_rel_type = histrogram(k)

    do_spacy_stuff(res)

    sentence_length = map(between, res.tags["SENTENCE"])

    res.print_pos()

    how_many_entites = map(lambda x: (x[0], len(x[1])), res.tags.items())
    print_table("Wie viele [SpatialEntities,...] gibt es",
                ("Entity",), how_many_entites)

    print_table("Wie oft kommen welche QsLink Typen vor? Länge",
                ("Typ",), how_many_rel_type.items())

    print_table("Verteilung der Satzlänge graphisch darstellen, länge zwischen a und b",
                ("a", "b"), histrogram(sentence_length).items())

    merge_table = res.get_mergeable()



    links = list(filter(lambda x: (x.attrib["trigger"] != ""),res.tags.get('QSLINK',[]) + res.tags.get('OLINK',[])))

    trigger = {a:b for a,b in map(lambda x:(x.id,x.attrib["text"]),res.tags.get('SPATIAL_SIGNAL',[]))}

    links_trigger = [(x.name,trigger.get(x.attrib["trigger"],"")) for x in links]

    print_table("Welche Links (QSLinks, OLinks) werden von welchen Präpositionen getriggert",("Link Typ","Präposition"),histrogram(links_trigger).items())


    abcd = list(map(lambda x:(x.attrib["text"]),res.tags.get('MOTION',[])))

    print_table("Welches sind die fünf häufigsten „MOTION“ Verben ",("verb",),histrogram(abcd).items(),limit=5)

    # print(json.dumps(asdict(res)["tags"]))

    graph = graphviz.Digraph()
    ids = []

    color_table = {
        "PLACE": "red",
        "SPATIAL_ENTITY": "green",
        "PATH": "blue",
        "NONMOTIONEVENT": "orange",
        "QSLINK": "red",
        "OLINK": "blue",
    }

    bgraph: nx.DiGraph = nx.DiGraph()

    for tag in res.tags["PLACE"] + res.tags.get("SPATIAL_ENTITY", []) + res.tags.get("PATH", []) + res.tags.get("NONMOTIONEVENT", []):
        bgraph.add_node(merge_table.get(tag.id, tag.id),
                        label=tag.get_label(merge_table.get(tag.id, tag.id)), color=color_table.get(tag.name, "black"))
        ids.append(merge_table.get(tag.id, tag.id))

    for tag in res.tags["QSLINK"] + res.tags["OLINK"]:
        from_id = merge_table.get(tag.attrib["fromID"], tag.attrib["fromID"])
        to_id = merge_table.get(tag.attrib["toID"], tag.attrib["toID"])
        if not(from_id in ids) or not(to_id in ids):
            continue

        bgraph.add_edge(from_id, to_id, label=tag.attrib["relType"], color=color_table.get(
            tag.name, "black"))

    removal = []
    # Remove Empty Nodes which don't have neighbors
    for node in list(bgraph.nodes(data=True)):
        neighbors = list(bgraph.predecessors(
            node[0])) + list(bgraph.successors(node[0]))
        if node[1]["label"].split("\n")[-1] == "" and len(neighbors) == 0:
            removal.append(node[0])

    for xx in removal:
        bgraph.remove_node(xx)

    A = to_agraph(bgraph)
    A.layout(prog="circo")

    graph_filename = "svg/"+filename.split("/")[-1] + ".svg"
    json_filename = filename.split("/")[-1] + ".json"

    A.draw("output/"+graph_filename)

    #print(f"Wrote Graph to: {graph_filename}\n")
    #print(f"Wrote Json  to: {json_filename}")
    print("## Graph Vis")
    print(f"![Graph]({graph_filename})")

    res.to_file("output/"+json_filename)

    if(os.name == "posix"):
        sys.stdout.close()
        sys.stdout = stdout
    print("Wrote Result to:",outputfile)
    # print(A.to_string())


if __name__ == "__main__":
    main('/home/kevin/projects/token/Traning/ANC/WhereToMadrid/Highlights_of_the_Prado_Museum.xml')

    main('./Traning/RFC/Bicycles.xml')
