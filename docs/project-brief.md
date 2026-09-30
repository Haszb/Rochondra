# Rochondra: Project Brief

*Comparative analysis of digital-asset whitepapers*

This document sets out the problem Rochondra addresses, the direction the project is taking, and the method that guides its trade-offs. It does not cover project progress, which is tracked in the roadmap, or the architecture decisions and their costs, which are recorded in the [decision log](decision-log.md).

- **Repository:** <https://github.com/Haszb/Rochondra>
- **Author:** Hassan Zbib
- **Field:** NLP / Data engineering / Document analysis
- **Method:** Kanban, sequencing by dependency
- **Team size:** 1 person

### Version history

| Version | Author | Description | Date |
|---|---|---|---|
| 1.0 | Hassan Zbib | Initial Version | 30/09/2026 |

## 1. Problem

In an unregulated market, the whitepaper is the document a low-quality project finds most costly to fake without giving itself away, which makes it one of the few quality signals that can be used before fundraising begins. Yet it is largely underused. About half of investors look at it and a third try to analyze it, but many of them lack the time or expertise to work through its technical complexity.

Meanwhile, many analysts do not read it. They base their views on what is immediately accessible, such as the team, the community and the social media presence. Their assessments also tend to be structurally optimistic: a positive rating on a successful project leads to advisory work on other projects. The figures confirm this. Two-thirds of ICOs fail, and even with a positive rating from the best analysts, the failure rate only drops to just over half.

That said, the document itself carries information. Research has identified measurable signals in it, such as length, readability, language errors and tone intensity. None of them determines whether a project succeeds, but each one can be observed at an early stage. Scale is a further problem. Reading a whitepaper is not enough on its own, as it also needs to be put in context, but no existing tool can compare a document with several thousand others against the same criteria.

The studies this section draws on are covered in [Decoding Whitepapers](https://medium.com/@rochondra.lab/decoding-whitepapers-what-academic-research-reveals-about-crypto-project-quality-4e7c8f842570) and [Information asymmetry and conflicts of interest](https://medium.com/@rochondra.lab/information-asymmetry-and-conflicts-of-interest-the-ambiguous-role-of-analysts-in-the-ico-c969af990ab7), where the full references can be found.

## 2. Approach

What the ecosystem lacks, then, is not another opinion on whitepapers but a measurement. Rochondra relies on indicators validated by scientific literature rather than inventing its own criteria, and publishes its calculation method alongside the results, so that anyone can verify and challenge the dimensions of the analysis.

These indicators are not new, but they have so far only been applied to small samples in academic settings. Natural language processing now makes it possible to compute them across thousands of documents with no common format, which changes the nature of the result: a document is no longer described in isolation but placed within a distribution.

## 3. Scope

For now, Rochondra is focusing on the Documentation pillar of a five-pillar evaluation framework: team, technology and code, tokenomics, documentation and community. The whitepaper was tackled first because it brings together a project's technical, economic and marketing vision in a single place, and because it is costly for a weak project to fake. Documentation is also the cheapest pillar to build, since whitepapers are publicly available and require no paid APIs, no personal data, no heavy LLM usage and no extensive manual research, whereas each of the other four runs into at least one of these obstacles.

Price prediction, trading signals and any form of investment advice are explicitly out of scope. The other four pillars are also excluded until the Documentation pillar has been validated, as is real-time analysis, since this is a corpus problem handled in batches.

Success means that whitepapers with no common format can be compared along the same dimensions, and that a third party can reproduce these comparisons from the published methodology. A working pipeline is therefore not enough: its outputs must also be comparable across the corpus and hold up under scrutiny.

## 4. Outputs

Rochondra aims to support decisions with verifiable measurements rather than social signals. Its outputs are built in stages, and each stage is usable on its own before the next is available.

- **Stage 1:** positioning a document along measured structural dimensions against several thousand others. This stage is available as soon as part of the corpus has been processed and becomes more informative as ingestion continues.
- **Stage 2:** split the document according to its own table of contents, with quick navigation, a section-by-section summary and sentiment analysis. This splitting supports reading a single document rather than comparing documents, since each whitepaper has its own structure.
- **Stage 3:** map each document into a common outline (introduction, risks, content and other parts) using a topic modeling method from the literature, so that sections become comparable across the whole corpus. This stage requires the segmentation method to be validated first.
- **Stage 4:** extend the set of indicators, for example with named entities and innovation markers, drawing on both the scientific literature and in-house work.

This progression relies on a single architectural rule: fact tables store only raw values, and percentiles, qualitative labels and aggregations are computed at display time. The only exception is the corpus-level distribution, which is precomputed but fully rebuilt with every ingested batch. Adding an indicator or changing the output format therefore does not affect data that has already been ingested.

The system outputs measurements and a document's position within a distribution. It does not produce an aggregate score, a risk level or a recommendation. These measurements describe the document, not the project or the people behind it.

This choice reflects how the project has evolved. The initial goal was an aggregate fundamentals score, but a review of existing rating platforms revealed structurally optimistic assessments, documented conflicts of interest and, in several cases, sanctions or shutdowns. Rather than inherit these weaknesses, Rochondra shifted toward what can be verified and reproduced: raw measurements and each document's position within a distribution.

In the longer term, Rochondra will expand to the other evaluation pillars, aiming to assess crypto projects as rigorously as the data allows.

## 5. Current Status

The application currently handles PDF whitepapers and is built on three layers: an API that exposes the extraction and analysis steps; storage split between a working cache, object storage for files and a persistent database; and an interface that is still a Streamlit prototype.

The corpus has been built out of 6,941 attempted URLs, 5,880 documents (30.4 GB) were retrieved and verified, and 5,300 of them can be used directly as text. The 2017–2019 period, which had lost the most documents, was largely rebuilt from the Internet Archive, raising its recovery rate from 14.7% to 71.7%. Truncation and selection biases have been identified and measured against a known denominator, and the method used to build the corpus is described in a dedicated article (Work in progress, Link will be updated later on).

Some resources are already available but not yet used: project activity statuses and GitBook documentation URLs. Since GitBook has become the dominant format for recent projects, processing these URLs is necessary to keep the corpus from remaining biased toward the post-ICO era.

At this stage, unit and integration tests are still missing, as is a schema migration tool, since the schemas still change too often for one to be worthwhile. Following the order set out in Section 6, they come after tasks that unblock more work, and a migration tool will only be worthwhile once the schemas stabilize. More importantly, the processing cost per document has not yet been measured. Until it is, whether the full corpus can be ingested remains an assumption.

## 6. Decision-Making Method

The project is run by a single person with irregular availability, so steps are ordered by dependency rather than by date. A schedule would cause friction, whereas exit criteria can be verified.

Two criteria are applied to each task, in this order:

- Downstream impact: a task that unblocks three others comes before one that unlocks only one.
- Cost of delay: tests and migrations cost little today, but more with every week that passes.

The first criterion is the easiest to neglect, because tasks that reduce uncertainty produce nothing visible. They get pushed back, and everything that depends on them remains impossible to plan. For example, measuring the processing cost per document unblocks no code, but it unblocks every decision that follows. Both criteria are made explicit so that the roadmap can be checked rather than taken on trust.

## 7. Open Questions

**What is the processing cost per document?** It has not been measured yet, and the feasibility of ingesting the full corpus depends on it.

**Which section segmentation should be used, and does it hold beyond the post-ICO era?** Since the corpus is dominated by documents from 2020–2022, an outline validated on that period may not suit more recent formats, such as GitBook.

**Do surface-level indicators still hold up against language models?** Most of the research this project relies on predates their widespread use. Since writers can now improve readability and linguistic correctness with almost no effort, these indicators may lose their value as signals in recent documents.

**Under what legal framework can measurements about named projects be published?** Although the corpus consists of public documents, redistributing them and publishing measurements tied to named projects raises legal questions that Rochondra has not yet addressed.
