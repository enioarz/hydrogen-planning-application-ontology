"""Validate the competency queries, pinned alignments, and OWL consistency."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.request import urlopen
from xml.etree import ElementTree

from rdflib import Graph, Literal, Namespace, OWL, URIRef, XSD

ROOT = Path(__file__).resolve().parent
EX = Namespace("https://w3id.org/hydrogen-planning/example/")
HPA = Namespace("https://w3id.org/hydrogen-planning/ontology#")
OEO = Namespace("https://openenergyplatform.org/ontology/oeo/")
ONTOLOGY = URIRef("https://w3id.org/hydrogen-planning/ontology")
ALIGNMENT = URIRef("https://w3id.org/hydrogen-planning/oeo-planning-alignment")
SOURCES = {
    "bfo": (
        "http://purl.obolibrary.org/obo/bfo/2020/bfo.owl",
        "https://raw.githubusercontent.com/BFO-ontology/BFO-2020/"
        "9029787b007ac8ac4afa735134db4b9574eda746/21838-2/owl/bfo-2020.owl",
        "cb7e646388f77eb76e534371c0c703452df461d986378edd4a1e884024318329",
        "xml",
    ),
    "cco": (
        "https://www.commoncoreontologies.org/2026-08-13/CommonCoreOntologiesMerged",
        "https://raw.githubusercontent.com/CommonCoreOntology/CommonCoreOntologies/"
        "0bc7d33e1bc09fd4693366119ab4e03cb0340042/src/cco-merged/CommonCoreOntologiesMerged.ttl",
        "a9453382b25b40781c181d6ba44981f228abb76d90d548846713adba9baadb42",
        "turtle",
    ),
    "oeo": (
        "https://openenergyplatform.org/ontology/oeo/releases/2.14.0/oeo.owl",
        "https://github.com/OpenEnergyPlatform/ontology/releases/download/v2.14.0/oeo-full.owl",
        "fd9c47d107ab5dff2d553aab7d15bfcdfd6045c72fd4071b5d6d29d304540b0a",
        "xml",
    ),
}


def load_release(name):
    version, url, checksum, syntax = SOURCES[name]
    cache = ROOT / ".ontology-cache" / checksum
    if cache.exists():
        content = cache.read_bytes()
    else:
        with urlopen(url, timeout=30) as response:
            content = response.read()
    if hashlib.sha256(content).hexdigest() != checksum:
        raise ValueError(f"{name} checksum mismatch. Check {cache} and the pinned release.")
    graph = Graph().parse(data=content, format=syntax)
    if (None, OWL.versionIRI, URIRef(version)) not in graph:
        raise ValueError(f"{name} does not declare its expected version IRI")
    cache.parent.mkdir(exist_ok=True)
    if not cache.exists():
        cache.write_bytes(content)
    return graph, cache


def validate_queries(graph):
    def format_term(value):
        if isinstance(value, Literal) and value.datatype == XSD.decimal:
            return str(value)
        return value.n3(graph.namespace_manager)

    expected = json.loads((ROOT / "examples/expected.json").read_text())
    questions = {f"CQ{number}" for number in range(1, 13)}
    if set(expected) != questions or {p.stem for p in (ROOT / "queries").glob("*.rq")} != questions:
        raise ValueError("Expected one query and one expected result for each of CQ1–CQ12")
    for question, expected_rows in expected.items():
        query = (ROOT / "queries" / f"{question}.rq").read_text()
        result = graph.query(query, initBindings={"decision": EX.EX_0000028})
        rows = [[format_term(term) for term in row] for row in result]
        if sorted(rows) != sorted(expected_rows):
            raise ValueError(f"{question}: expected {expected_rows!r}, got {rows!r}")
        print(f"{question}: {len(rows)} expected row(s)", flush=True)


def write_catalog(path, documents):
    catalog = ElementTree.Element("catalog", xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog")
    for iri, document in documents.items():
        ElementTree.SubElement(catalog, "uri", name=str(iri), uri=document.as_uri())
    ElementTree.ElementTree(catalog).write(path, encoding="utf-8", xml_declaration=True)


def validate_owl(graph, robot, *, hygiene_only):
    alignment_path = ROOT / "oeo-planning-alignment.ttl"
    alignment = Graph().parse(alignment_path)
    release, _ = load_release("oeo")
    for triple in alignment:
        if str(triple[0]).startswith(str(OEO)) and triple not in release:
            raise ValueError(f"OEO alignment triple missing from the pinned release: {triple!r}")

    bfo, bfo_cache = load_release("bfo")
    cco, cco_cache = load_release("cco")
    with tempfile.TemporaryDirectory() as temp:
        staging = Path(temp)
        documents = {
            URIRef(SOURCES["bfo"][0]): staging / "bfo.owl",
            URIRef(SOURCES["cco"][0]): staging / "cco.ttl",
            ONTOLOGY: ROOT / "ontology.ttl",
            ALIGNMENT: alignment_path,
        }
        for source in (graph, bfo, cco, alignment):
            unresolved = set(source.objects(None, OWL.imports)) - documents.keys()
            if unresolved:
                raise ValueError(f"No pinned document for imports: {unresolved!r}")

        shutil.copyfile(bfo_cache, documents[URIRef(SOURCES["bfo"][0])])
        shutil.copyfile(cco_cache, documents[URIRef(SOURCES["cco"][0])])
        catalog = staging / "catalog.xml"
        write_catalog(catalog, documents)

        closure = staging / "closure.owl"
        subprocess.run(
            [*robot, "merge", "--catalog", str(catalog),
             "--input", str(ROOT / "examples/planning-decision.ttl"),
             "--output", str(closure)],
            check=True,
        )
        rules = sorted((ROOT / "validation").glob("*.rq"))
        subprocess.run(
            [*robot, "verify", "--input", str(closure), "--output-dir", str(staging),
             "--queries", *map(str, rules)],
            check=True,
        )
        print("ROBOT: ontology hygiene checks passed.", flush=True)
        if hygiene_only:
            return
        subprocess.run(
            [*robot, "reason", "--reasoner", "HermiT", "--input", str(closure)], check=True
        )
        print("ROBOT: application and example are consistent with the pinned imports.", flush=True)

        # Substitute OWL's empty class and property in the temporary closure.
        # This checks for a model with empty extensions without leaving named
        # unsatisfiable classes for ROBOT to reject during its coherence check.
        subprocess.run(
            [*robot, "rename", "--input", str(closure), "--allow-duplicates", "true",
             "--mapping", str(OEO.OEO_00010021), str(OWL.Nothing),
             "--mapping", str(HPA.HPA_0000014), str(OWL.Nothing),
             "--mapping", str(OEO.OEO_00000526), str(OWL.bottomObjectProperty),
             "reason", "--reasoner", "HermiT"],
            check=True,
        )
        print("ROBOT: the example admits a model with no electrolyser and no physical grid connection.",
              flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--hygiene-only", action="store_true", help="Run only the ROBOT hygiene checks.")
    mode.add_argument("--queries-only", action="store_true", help="Skip release downloads and OWL checks.")
    parser.add_argument("--robot-jar", type=Path, help="Use this ROBOT JAR instead of robot on PATH.")
    args = parser.parse_args()
    graph = Graph().parse(ROOT / "ontology.ttl").parse(ROOT / "examples/planning-decision.ttl")
    if not args.hygiene_only:
        validate_queries(graph)
    if not args.queries_only:
        if args.robot_jar:
            robot = ["java", "-jar", str(args.robot_jar)]
        else:
            executable = shutil.which("robot")
            if executable is None:
                parser.error("ROBOT is required for OWL checks. Put robot on PATH or pass --robot-jar.")
            robot = [executable]
        validate_owl(graph, robot, hygiene_only=args.hygiene_only)


if __name__ == "__main__":
    main()
