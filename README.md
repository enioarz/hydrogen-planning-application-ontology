# Hydrogen project planning application ontology

**What information was available to the developer when an electrolyser site and capacity were selected, and what decision was recorded?**

The ontology represents events and the records that support answers about a project, actor, and date. The example is fictional. It uses a 2025 siting decision and delivery terms for 2026. Scenario assumptions, REMix runs, counterfactuals, disclosure experiments, and regret calculations belong to the paper’s implementation.

## Run the demonstration

Requires Python 3, Java, and [ROBOT v1.9.11](https://github.com/ontodev/robot/releases/tag/v1.9.11) for the full demonstration. The first run downloads the pinned source documents from GitHub, verifies their SHA-256 digests, and caches them in `.ontology-cache/`.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p .ontology-cache
curl -fL -o .ontology-cache/robot.jar https://github.com/ontodev/robot/releases/download/v1.9.11/robot.jar
.venv/bin/python validate.py --robot-jar .ontology-cache/robot.jar
```

Omit `--robot-jar` if `robot` is already on your PATH. Use `validate.py --queries-only` to compare the query rows without Java or ontology downloads after the Python dependencies are installed. The full run also checks that the included OEO triples occur in the pinned release. ROBOT merges the application, example, and resolved imports, then runs HermiT to check consistency. The second run substitutes OWL’s empty class and property for the equipment classes and physical grid connection relation in a temporary copy. The second model shows that neither existence claim follows, even for an unnamed device or connection.

Load [ontology.ttl](ontology.ttl) and [examples/planning-decision.ttl](examples/planning-decision.ttl) for the SPARQL demonstration. Bind `?decision` to `https://w3id.org/hydrogen-planning/example/EX_0000028` as the validator does, or add an equivalent `VALUES` clause. The queries use asserted triples and explicit subclass paths where needed. The [expected rows](examples/expected.json) follow each query’s column order.

## Competency questions

| ID | Question | Expected answer in the example |
| --- | --- | --- |
| [CQ1](queries/CQ1.rq) | Which sites did the developer identify for the electrolyser project? | Sites A and B in the application |
| [CQ2](queries/CQ2.rq) | What electrical input capacity did the developer specify for each site in its application? | 40 MW at A and 30 MW at B |
| [CQ3](queries/CQ3.rq) | Which electricity grid connection point did the grid operator identify in its offer for that site? | A1 for Site A |
| [CQ4](queries/CQ4.rq) | What limit on electricity withdrawal did the grid operator state in that offer? | 30 MW at A1 |
| [CQ5](queries/CQ5.rq) | Which hydrogen pipelines were in operation in the project area on the date of the siting decision? | The pipeline whose operator log covers 20 March |
| [CQ6](queries/CQ6.rq) | Which hydrogen delivery point does the offtake agreement name? | D1 |
| [CQ7](queries/CQ7.rq) | What quantity of hydrogen does the offtake agreement specify for each delivery period? | 50,000 kg in January 2026 and 55,000 kg in February 2026 |
| [CQ8](queries/CQ8.rq) | What price or pricing rule does the electricity supply offer specify for the project? | Fixed EUR 65 per MWh |
| [CQ9](queries/CQ9.rq) | Which version of the infrastructure data did the developer receive before the siting decision? | v1, received on 15 March |
| [CQ10](queries/CQ10.rq) | For which geographical area does that version report electricity connection capacity? | District D |
| [CQ11](queries/CQ11.rq) | Which site and electrical input capacity did the developer select in its recorded decision? | Site A at 30 MW |
| [CQ12](queries/CQ12.rq) | Which infrastructure records did the developer cite as grounds for that decision? | The grid operator’s connection offer |

## Modelling decisions

- The application, offer, and decision contain distinct terms for requested input, permitted withdrawal, and selected input. Site and point identifiers designate existing places or infrastructure. The stated MW values describe the terms of records. The decision contains a separate citation to the offer.
- Issue, signing, receipt, and citation have their own event types and dates. Queries for issued and signed records use dates at or before the selected decision. CQ9 and CQ10 require a documented receipt by the developer strictly before the decision. Issue and receipt supply separate evidence. The example has an issue event for the connection offer and explicit evidence of its citation.
- CQ5 uses a documented operating interval with an inclusive start and exclusive end. The announced commissioning date belongs to an announcement about a pipeline plan. The pipeline announcement contributes no operating interval.
- The first iteration uses UTC timestamps, a district as the project area, one site and connection point per connection offer, and fixed units for project quantities. Pricing rules are retained as text so the original language can be returned.

## Term identifiers

Application classes and properties use stable IDs in the form `HPA_0000001`. Fictional example individuals use `EX_0000001` IDs. Use `rdfs:label` for the human-readable name and `IAO_0000115` for the textual definition. Allocate a new number for each new entity and keep the ID when a label changes. Version 0.2.0 replaces the draft’s descriptive IDs, including in the example and competency queries.

## Ontology hygiene

Run the checks on the merged imports with `.venv/bin/python validate.py --hygiene-only --robot-jar .ontology-cache/robot.jar`. The full demonstration also runs them. Each SPARQL query returns violations, so an empty result passes.

- [English labels](validation/missing-english-label.rq) require a nonblank English-tagged label. Other languages are allowed alongside it.
- [Definitions](validation/missing-definition.rq) require a nonblank `IAO_0000115` literal. The label and definition checks cover application terms, example individuals, and the selected OEO terms.
- [Orphan classes](validation/orphan-classes.rq) require every application class to have an asserted `rdfs:subClassOf` path to BFO continuant or occurrent, including paths through CCO. An attachment only to `owl:Thing` or BFO entity fails.
- [Opaque IDs](validation/term-identifiers.rq) check the format of application and example identifiers.

## Versioned sources and reused IRIs

The validator maps version IRIs to pinned files locally and checks the full import closure used for the demo. The project IRIs under `https://w3id.org/hydrogen-planning/` are provisional.

| Source | Reused IRIs |
| --- | --- |
| [BFO 2020, ISO 21838-2 release](https://github.com/BFO-ontology/BFO-2020/tree/9029787b007ac8ac4afa735134db4b9574eda746/21838-2/owl) | With prefix `http://purl.obolibrary.org/obo/`, `BFO_0000015` process, `BFO_0000029` site, `BFO_0000040` material entity, and `BFO_0000057` has participant |
| [CCO v2.2, merged release](https://github.com/CommonCoreOntology/CommonCoreOntologies/blob/0bc7d33e1bc09fd4693366119ab4e03cb0340042/src/cco-merged/CommonCoreOntologiesMerged.ttl) | With prefix `https://www.commoncoreontologies.org/`, `ont00000958` information content entity, `ont00000686` designative information content entity, `ont00000965` directive information content entity, `ont00000853` descriptive information content entity, `ont00000300` agent, `ont00001180` organization, `ont00001916` designates, and `ont00001982` describes |
| [OEO v2.14.0](https://github.com/OpenEnergyPlatform/ontology/releases/tag/v2.14.0) | With prefix `https://openenergyplatform.org/ontology/oeo/`, `OEO_00010021` water electrolyser, `OEO_00020006` grid component, `OEO_00000296` grid node, `OEO_00000526` is connected to, and `OEO_00390001` megawatt |

HermiT reported inconsistency for the full OEO v2.14.0 release combined with the BFO 2020 ISO ontology, including before application axioms were added. [The local OEO selection](oeo-planning-alignment.ttl) retains the reviewed declarations and the grid relation’s symmetry, domain, and range. The water electrolyser declaration supports the installation class without importing OEO’s additional equipment restrictions. OEO power rating (`OEO_00230001`) is a capacity of an energy converting component with a power unit restriction. It remains a term to consider when equipment evidence is in scope.

## Open domain decisions

Determine which evidence qualifies for a receipt, citation, or interval of operation in the research data, and how to handle same-day events with unknown order or intervals with unknown bounds. Decide whether project-area membership should be asserted from records or derived geometrically for pipelines crossing district boundaries. For richer offers, decide how limits attach to individual site and point pairs, how revisions supersede earlier offers, and whether the study requires computable tariffs.
