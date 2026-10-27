# Rochondra: Roadmap

*Last reviewed: October 2026*

This roadmap is one of three documents that describe Rochondra. The [project brief](project-brief.md) explains its purpose, the [decision log](decision-log.md) records the choices that shaped it, and the roadmap sets out what comes next, and in what order.

Steps are ordered by dependency, not by date. The time available for the project is irregular, so a schedule would be fiction. Each phase has an objective and a verifiable exit criterion, and each one delivers something public: an article, a website update or both, depending on what is ready to show.

## How to read this roadmap

### Workstreams

| Workstream | Covers |
|---|---|
| Corpus | Collecting, cleaning and enriching the whitepaper dataset and its metadata |
| Analyses | Defining, implementing and verifying the indicators |
| Architecture | Building the code and infrastructure that run the pipeline |
| Site | Building the public website and updating it with each phase |
| Documentation | Writing and publishing articles and project documents |

### Priority levels

| Level | Meaning |
|---|---|
| High | Blocks work in later phases, costs more the longer it is put off, or reduces an uncertainty that other decisions depend on |
| Medium | Blocks the current phase only |
| Low | Blocks nothing. Convenience, cleanup, ergonomics |

### Board rules

- At most two cards are in progress at a time.
- Blocked cards go in a separate column, so blocked work does not look like work in progress.
- Only cards from the current phase are worked on, unless a card says otherwise.
- Documentation cards count toward the work-in-progress limit like any other card. Writing takes real hours, so it is planned, not squeezed in.
- Foundations should be solid enough to build on, and no more. This is a personal project, and over-engineering is a cost too.
- Cards state an intent, not a procedure: the details are settled when the work starts. Each phase is held to its exit criteria.
- Every endpoint that touches the ingested corpus is typed, tested and logged, and its results are versioned.
- At the start of each phase, its cards are detailed on the GitHub board and this roadmap is updated.

### Eras

The corpus is divided into three eras by CoinMarketCap listing date:

| Era | Period |
|---|---|
| ICO era | 2017–19 |
| Post-ICO era | 2020–22 |
| Modern era | 2023–26 |

The listing date only approximates the date of the document. A project may be listed well after its token sale, and an archived copy may be a later version of the whitepaper.

## Where things stand

**The corpus is collected.** Of the 6,941 whitepaper URLs tried, 5,880 PDFs were retrieved and verified (30.4 GB): 5,300 with extractable text, 546 scans and 34 encrypted files. About three in four came from the Internet Archive. Every failure is recorded, so the share of documents lost is known (about 15% of the URLs).

**The corpus is mostly post-ICO.** By listing date, 59% of the 5,880 retrieved PDFs belong to the post-ICO era, 24% to the modern era and only 15% to the ICO era. The remaining 2% were listed before 2017. This imbalance matters because most of the research behind the indicators was based on ICO-era documents.

**The pipeline is a working prototype.** It takes a PDF through text extraction, structural indicators, table of contents detection and sentiment per section. Its architecture follows the decision log (three storage layers with one role each, a single exit point from the working area, centralized configuration), apart from the gaps the log itself records.

**The measurements are prototypes.** They were built for speed, not reliability. A September 2026 audit of the repository against the decision log found three problems: some measurements include generated text, contrary to [D6][d6]; some valid values are discarded; and no measurement has been verified.

**Several pieces are missing.** There are no tests, no logging, no batch ingestion, no schema migration tool and no measurement of processing time per document. The Streamlit interface lags behind the API, so Swagger is used in its place for now.

## Phase 1: Proof of concept

**Objective.** Run the whole chain once on a small scale, from sampling to publication: 210 whitepapers checked by hand, measured with structural indicators and placed in deciles on a static site. The aim is to lay the foundations for the next phases, not to produce findings. The review also yields the first rules for cleaning the corpus.

**Deliverables.** The site, with its methodology page. An article on how the corpus was built.

| Card | Workstream | Priority | Notes |
|---|---|---|---|
| Draw the sample | Corpus | **High** | Random draw from text-extractable files, 70 per era. Documents listed before 2017 are excluded. A rejected document is replaced by the next one drawn. Equal allocation is deliberate: it does not reflect the corpus, but it ensures that problems specific to each era surface during the review |
| Review the sample | Corpus | **High** | Each document is checked by hand, and non-English documents are rejected at this stage. Every rejection is logged with its reason. The rejection criteria emerge from the review itself |
| Write the review checklist | Corpus | **High** | Formalizes the criteria that emerged during the review. The checklist is then reapplied to the whole sample, so that every document is judged by the same rules. Gives a first rejection rate per era. Basis for the Phase 2 cleaning protocol |
| Make the LLM optional in extraction | Architecture | **Medium** | Image descriptions behind a flag, off by default, to save processing time on the sample. Images are still extracted, so image statistics do not depend on the flag |
| Update the text preparation function | Analyses | **High** | One shared function used by every measurement. Strips generated text ([D6][d6]), Markdown syntax, tables and image markers, all of which distort sentence counts. Tested on the sample |
| Update the structural indicators | Analyses | **High** | Library-based: Gunning Fog, Flesch Reading Ease, word count, text size, PDF size, image count. Keeps negative Flesch scores, which are valid but currently discarded. Text size is measured on the prepared text |
| Write the batch script for the sample | Architecture | **High** | Calls modules/ directly ([D12][d12]), bypassing the working area. Logs time per step and per document ([D25][d25]) |
| Add the CoinMarketCap ID and era to the schema | Architecture | **High** | Closes the [D23][d23] gap. Without the ID, no measurement can be linked to a project |
| Create the Supabase tables | Site | **Medium** | Indicators and their distribution ([D28][d28]): deciles per indicator across the whole sample. Read-only, with row-level security (RLS) |
| Set the publication rules | Site | **Medium** | Measurements and a link to the source only. No redistribution of documents, no score ([D21][d21]), neutral wording. Check the legal framework for publishing measurements of named projects (brief, open question) |
| Build the static site | Site | **Medium** | Raw values, position within the sample and a link to the source. Display format still to be decided. Makes clear that positions are relative to the sample, not the corpus |
| Write the methodology page | Documentation | **Medium** | Prototype status, sample composition (one third per era, post-ICO era under-represented, non-English documents excluded), libraries used, text preparation, handling of ties in deciles |
| Article: building the corpus | Documentation | **Medium** | Recovery from the Internet Archive, era coverage, known biases. Drafts already exist |

**Exit criterion.** The first version of the site is online, with the structural indicators of every retained document. The methodology page and the article are published. The review checklist is written, and first estimates are recorded: the rejection rate per era, and the processing time per document for extraction and structural indicators.

## Phase 2: Cleaning and enriching the corpus

**Objective.** Know the corpus well enough to trust it: what it contains, what it excludes and why, and what metadata come with it. Cleaning builds on the Phase 1 checklist, and enrichment draws on free sources only.

**Deliverables.** An article on corpus exploration and another on the cleaning methodology.

| Card | Workstream | Priority | Notes |
|---|---|---|---|
| Explore the corpus (EDA) | Corpus | **High** | In-depth analysis of the corpus, to help turn the Phase 1 checklist into a cleaning protocol for the whole corpus |
| Article: exploring the corpus | Documentation | **Medium** | First descriptive findings from the EDA |
| Write the cleaning protocol | Corpus | **High** | Extends the Phase 1 checklist. Frozen once validated and before it is applied, so the rules do not shift during cleaning |
| Validate the protocol on the reviewed sample | Corpus | **High** | The hand-reviewed sample is the reference for checking the automatic rules |
| Apply the cleaning protocol | Corpus | **High** | Each rule reports how many documents it removes |
| Harvest the remaining CoinMarketCap metadata | Corpus | **Medium** | Identify and collect the information CoinMarketCap already provides that could broaden the analysis, such as the project category |
| Explore other data sources | Corpus | **Medium** | Map what other providers offer, free or paid, and whether their data can be joined on the CoinMarketCap ID ([D23][d23]). Paid sources are noted for later, not used |
| Check the scans | Corpus | **Medium** | Quick test of whether the scans can stay out of the corpus without skewing it. They would skew it if, for example, they were mostly failed projects |
| Article: cleaning the corpus | Documentation | **Medium** | The protocol, what it removed and what remains uncertain |

**Exit criterion.** The corpus is cleaned. Every exclusion, scans included, is explained, and its effect on the corpus is measured. The protocol has been checked against the reviewed sample, the available metadata are listed, and both articles are published.

## Phase 3: Stabilization and ingestion

**Objective.** Turn the prototype into a system that can process the whole cleaned corpus: verified structural indicators, a stable schema and the API as the single entry point. Then ingest the corpus through the API.

**Deliverables.** Every document in the corpus shown with its position on the site. An article on the data engineering behind the project, including the processing time per document. The decision log, the roadmap and the brief updated.

| Card | Workstream | Priority | Notes |
|---|---|---|---|
| Verify the structural indicators | Analyses | **High** | Protocol set before measuring: which indicators are verified, whether each is computed from the PDF or the prepared text, how it is checked and what threshold it must meet |
| Rewrite the API | Architecture | **High** | The API becomes the single entry point for ingestion; core modules can still be called directly, but only for development ([D12][d12]). Closes the [D15][d15] and [D19][d19] gaps |
| Freeze the schema | Architecture | **High** | Identifiers, projects and provenance (file hash, source, era, CoinMarketCap ID), including how several documents are linked to one project ([D23][d23]). Later changes go through Alembic migrations |
| Version the methods | Architecture | **High** | Every measurement carries the version of the method that produced it (addresses the cost noted in [D18][d18]) |
| Add tests | Architecture | **High** | Endpoints, input/output formats and the contract test [D15][d15] calls for |
| Add logging | Architecture | **High** | Extends the Phase 1 timing to the API path, at corpus scale ([D25][d25]) |
| Ingest in batches | Architecture | **High** | One transaction per document: a failed batch can be resumed without redoing the documents already ingested |
| Protect the ingested corpus | Architecture | **High** | The ingested corpus becomes a read-only reference; exploration happens on a disposable working copy ([D26][d26]) |
| Export to Supabase after each batch | Site | **High** | Indicators exported and distribution rebuilt each time ([D28][d28]). Positions move during ingestion, so the site shows how many documents have been ingested so far |
| Update the site | Site | **Medium** | Positions now relative to the corpus; caveats updated accordingly |
| Update the project documents | Documentation | **Medium** | Decision log (the API as the single entry point, one transaction per document), roadmap and brief |
| Article: the data engineering behind the project | Documentation | **Medium** | Architecture, ingestion at scale, processing time per document |
| Clean up the dependencies | Architecture | *Low* | Keep only what the code imports |

**Exit criterion.** The cleaned corpus is ingested through the API, the structural indicators meet the thresholds set by their verification protocol, and every measurement carries its method version. Every endpoint is tested and logged. The ingested corpus is protected as a read-only reference. Its distribution is computed, the site shows the position of every document, and the processing time per document is measured at corpus scale. The article is published and the project documents are updated.

## Phase 4: Reading a single document

**Objective.** Help readers find their way through a single document: navigation follows its own table of contents, and each section comes with a summary and its sentiment.

**Deliverables.** Reading pages on the site. An article on the table of contents extraction method, its performance and its cost compared with a fully LLM-based approach. The decision log updated.

| Card | Workstream | Priority | Notes |
|---|---|---|---|
| Rewrite the table of contents extraction | Analyses | **High** | The [D13][d13] cascade, evaluated on bookmarked PDFs, plus a hand-annotated sample without bookmarks. Arbiter options compared, including typed decision models, against a fully LLM-based baseline |
| Evaluate the section splitting | Analyses | **High** | Heading detection and the placement of each heading in the text, each measured separately |
| Check the sentiment model | Analyses | **High** | FinBERT was trained on financial news, so it is checked on hand-annotated whitepaper sections. Uses the shared text preparation ([D6][d6]) |
| Rewrite the summarizer | Analyses | **Medium** | Reading aid only, never a measurement ([D6][d6]). Fidelity checked before publishing |
| Update the API | Architecture | **High** | New endpoints are typed, tested and logged, and their results are versioned (see Board rules) |
| Decide where processing runs | Architecture | **High** | Based on processing times measured on a sample of the new steps. Two choices: local or cloud processing, and summaries precomputed or generated on demand. Recorded in the decision log |
| Store the reading data privately | Architecture | **Medium** | JSON and Markdown in private object storage. Only derived data reaches the site |
| Run the new analysis family across the corpus | Architecture | **High** | No re-extraction of the text unless the text extraction method has changed |
| Build the reading pages | Site | **Medium** | One page per ingested document: table of contents, sentiment per section, summaries once cleared for publication. No comparison across documents ([D14][d14]) |
| Update the decision log | Documentation | **Medium** | Final extraction method, where processing runs, how summaries are produced and cleared |
| Article: extracting the table of contents | Documentation | **Medium** | Method, performance and cost compared with a fully LLM-based approach |

**Exit criterion.** The table of contents extraction, the section splitting and the sentiment model meet the thresholds set by their protocols, and the fidelity of the summaries has been checked. Every ingested document has a reading page, with summaries only where publication has been cleared. The article is published, and the decision log records the chosen extraction method and where processing runs.

## Phase 5: Extending the corpus to GitBook

**Objective.** Bring in GitBook, the documentation format of recent projects, along with the latest listings, so that the modern era carries the same weight in the corpus as it does among listed projects.

**Deliverables.** The GitBook documents on the site, with their measurements, tables of contents and sentiment. An article on GitBook and the representativeness of the corpus, and possibly one on how whitepapers changed over time.

| Card | Workstream | Priority | Notes |
|---|---|---|---|
| Refresh the project list | Corpus | **High** | Latest CoinMarketCap listings. New PDFs go through the Phase 2 protocol |
| Inventory the GitBook URLs | Corpus | **High** | Separate actual GitBook documentation from other links |
| Build the GitBook retrieval | Corpus | **High** | In-house or library-based ([D7][d7]). Polite crawling, in batches. Quality checked on a hand-reviewed subset |
| Clean the GitBook documents | Corpus | **High** | Phase 2 protocol, extended with rules specific to GitBook as a new, versioned protocol |
| Update the extraction | Architecture | **High** | GitBook output in the common format, navigation elements removed. GitBook's native structure provides the table of contents |
| Update the structural analysis | Analyses | **High** | Indicators made comparable across formats. Projects available in both formats provide a direct check |
| Ingest and rebuild the distribution | Architecture | **High** | Structural indicators first, then the other analysis families. Every document carries its ingestion date |
| Update the corpus exploration | Corpus | **Medium** | Re-run the Phase 2 exploration with the GitBook documents, to see how they change the composition of the corpus. Feeds the article on representativeness |
| Update the site | Site | **Medium** | Signals the shift in corpus composition, since positions will move |
| Article: GitBook and the representativeness of the corpus | Documentation | **Medium** | Era coverage before and after the extension |
| Article: how whitepapers changed over time | Documentation | *Low* | Possible angle: whether surface-level indicators remain informative in the LLM era (open question in the brief) |

**Exit criterion.** GitBook documents are ingested, and their indicators have been checked for comparability across formats. Each one has a reading page with its table of contents and sentiment. The share of each era in the corpus is measured against its share among listed projects, before and after the extension. The shift in the distribution is documented on the site, and the article on representativeness is published.

## Horizon

This section lists work that matters but depends on the phases above. The order below is indicative and will be settled when the time comes.

- **A common outline.** Map every document onto the same outline (introduction, risks, content and other parts) with a topic modeling method drawn from the literature, so that sections become comparable across the corpus ([D14][d14]). This is Stage 3 of the brief, and it comes first on the Horizon: its evaluation set must cover every era and both formats, which only Phase 5 makes possible.
- **New methods.** Candidates include the indicators the brief names but the code does not yet measure (spelling and grammar errors, tone intensity), the exaggeration index, already prototyped, named entities and references, n-grams, or a principal component analysis to see which indicators overlap. These are used for analysis only, never published as a single score per document ([D21][d21]).
- **Comparison with real outcomes.** Use tracked/untracked status (whether CoinMarketCap still tracks a project) and listing dates for labeling and survival analysis, starting with a check of the label on a sample of each class. This is the only way to know whether the indicators carry information about projects. It is also where the project would move from measuring to judging, so the results require validation before anything is published.
- **Corpus extensions.** OCR for the scans, a second attempt at the sites that blocked the crawler and a join with the token offerings dataset (TORD).
- **Deployment.** Moving the application to the cloud, with a provider chosen based on available startup credits ([D5][d5]). It may come earlier if Phase 4 shows that processing cannot run on a personal machine. User accounts, authentication and rate limiting come with it ([D27][d27]).
- **Version check on view.** When a user views a project, compare the ingested document with the one currently published on the project's site, and flag any newer version.
- **Analysis on submission.** A user submits a whitepaper that is not in the corpus and gets its analysis, placed against the existing distribution without being ingested ([D28][d28]). The working area ([D16][d16], [D19][d19]) was designed for this. It requires deployment, accounts and rate limiting ([D27][d27]). Each submission must also be checked to be a genuine, safe whitepaper before anything is processed or stored.

[d5]: decision-log.md#d5-deployable-from-day-one
[d6]: decision-log.md#d6-deterministic-first-the-llm-as-arbiter
[d7]: decision-log.md#d7-starting-with-pdf
[d12]: decision-log.md#d12-business-logic-independent-of-the-api
[d13]: decision-log.md#d13-a-cascade-for-extracting-the-table-of-contents
[d14]: decision-log.md#d14-two-ways-to-read-a-document
[d15]: decision-log.md#d15-one-representation-per-target-instead-of-a-single-data-model
[d16]: decision-log.md#d16-three-storage-layers-one-role-each
[d18]: decision-log.md#d18-nothing-on-local-disk
[d19]: decision-log.md#d19-a-single-exit-point-from-the-working-area
[d21]: decision-log.md#d21-measurements-rather-than-ratings
[d23]: decision-log.md#d23-an-internal-identifier-never-the-ticker-or-the-name
[d25]: decision-log.md#d25-measurement-driven-development
[d26]: decision-log.md#d26-a-read-only-ingested-corpus-and-a-working-copy
[d27]: decision-log.md#d27-what-can-be-bolted-on-later-can-wait
[d28]: decision-log.md#d28-interpretation-on-the-fly-distribution-precomputed
