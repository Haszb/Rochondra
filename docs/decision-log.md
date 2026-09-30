# Rochondra: Decision Log

This log records the key decisions that have shaped the project since it began, in chronological order. Each entry gives the problem it solves, the alternatives that were ruled out and the cost that was accepted. Only the decisions that explain the project's current shape are included. Earlier entries were reconstructed after the fact, while later ones are recorded and dated as they are made.

Nothing is ever deleted: a superseded decision is marked as such rather than removed. Three labels are added to entries where they apply:

- **Status** flags a decision that is transitional or not yet implemented.
- **Current gap** flags a point where the code does not yet follow the decision.
- **Revisit if** gives the condition that would reopen the decision.

*Last revised: September 2026*

| No. | Date | Decision | Status |
|---|---|---|---|
| [D1](#d1-measuring-inputs-instead-of-predicting-price) | n/a | Measuring Inputs Instead of Predicting Price | Active |
| [D2](#d2-indicators-drawn-from-literature) | n/a | Indicators Drawn from Literature | Active |
| [D3](#d3-a-five-pillar-evaluation-framework) | n/a | A Five-Pillar Evaluation Framework | Active |
| [D4](#d4-starting-with-the-whitepaper) | n/a | Starting with the Whitepaper | Active |
| [D5](#d5-deployable-from-day-one) | n/a | Deployable from Day One | Active |
| [D6](#d6-deterministic-first-the-llm-as-arbiter) | n/a | Deterministic First, the LLM as Arbiter | Active |
| [D7](#d7-starting-with-pdf) | n/a | Starting with PDF | Active |
| [D8](#d8-api-first-with-fastapi-and-streamlit) | n/a | API First, with FastAPI and Streamlit | Active |
| [D9](#d9-centralized-configuration-nothing-hardcoded) | n/a | Centralized Configuration, Nothing Hardcoded | Active |
| [D10](#d10-free-llms-by-default) | n/a | Free LLMs by Default | Active |
| [D11](#d11-the-model-name-determines-where-calls-go) | n/a | The Model Name Determines Where Calls Go | Transitional |
| [D12](#d12-business-logic-independent-of-the-api) | n/a | Business Logic Independent of the API | Active |
| [D13](#d13-a-cascade-for-extracting-the-table-of-contents) | n/a | A Cascade for Extracting the Table of Contents | Active |
| [D14](#d14-two-ways-to-read-a-document) | n/a | Two Ways to Read a Document | Active |
| [D15](#d15-one-representation-per-target-instead-of-a-single-data-model) | n/a | One Representation per Target Instead of a Single Data Model | Active, current gap |
| [D16](#d16-three-storage-layers-one-role-each) | n/a | Three Storage Layers, One Role Each | Active |
| [D17](#d17-a-star-schema) | n/a | A Star Schema | Active |
| [D18](#d18-nothing-on-local-disk) | n/a | Nothing on Local Disk | Active |
| [D19](#d19-a-single-exit-point-from-the-working-area) | n/a | A Single Exit Point from the Working Area | Active, current gap |
| [D20](#d20-working-keys-do-not-expire) | n/a | Working Keys Do Not Expire | Transitional |
| [D21](#d21-measurements-rather-than-ratings) | n/a | Measurements Rather Than Ratings | Active |
| [D22](#d22-coinmarketcap-as-the-source) | Sep 2026 | CoinMarketCap as the Source | Active |
| [D23](#d23-an-internal-identifier-never-the-ticker-or-the-name) | Sep 2026 | An Internal Identifier, Never the Ticker or the Name | Transitional, current gap |
| [D24](#d24-recovery-through-the-internet-archive) | Sep 2026 | Recovery Through the Internet Archive | Active |
| [D25](#d25-measurement-driven-development) | Sep 2026 | Measurement-Driven Development | Not yet implemented |
| [D26](#d26-a-read-only-ingested-corpus-and-a-working-copy) | Sep 2026 | A Read-Only Ingested Corpus and a Working Copy | Not yet implemented |
| [D27](#d27-what-can-be-bolted-on-later-can-wait) | Sep 2026 | What Can Be Bolted On Later Can Wait | Active |
| [D28](#d28-interpretation-on-the-fly-distribution-precomputed) | Sep 2026 | Interpretation on the Fly, Distribution Precomputed | Partly implemented |

## D1. Measuring Inputs Instead of Predicting Price

**Problem:** An earlier project aimed at predicting the price of Bitcoin but found no usable signal in price history. Price is an output variable, driven by information that the series itself does not contain. What fails for the most liquid asset in the market is unlikely to succeed for younger, more volatile ones.

**Decision:** Drop price modeling and measure inputs instead: the traces a project leaves behind as it is being built, starting with its documents.

**Alternative ruled out:** Pursue prediction by adding exogenous variables to the model. The field is highly competitive, and a single-person project has little to add to it.

**Cost:** Starting from scratch, with no reusable code or data, and giving up on the most requested use case.

## D2. Indicators Drawn from Literature

**Problem:** A decision-support tool is only as good as the rigor of its measurements. Criteria invented for the purpose are a matter of judgment, and a third party cannot verify them.

**Decision:** Build on indicators that published research has associated with project outcomes, rather than starting from scratch, and publish the calculation method alongside the results.

**Alternative ruled out:** Build the project's own indicators from the outset. This was rejected only as a starting point: internal indicators will complement those from literature once the foundation is established.

**Cost:** The set of indicators is limited to what research has validated. Moreover, most of that work predates the spread of language models, and these models may have weakened some surface-level signals.

## D3. A Five-Pillar Evaluation Framework

**Problem:** A project leaves different kinds of traces, each with its own sources and access constraints, and no single one is sufficient.

**Decision:** Use as evaluation pillars the five dimensions that recurred across an initial literature review: team, technology and code, tokenomics, documentation, and community.

**Alternative ruled out:** None.

**Cost:** The framework promises more than it covers, since only one pillar has been addressed so far.

## D4. Starting with the Whitepaper

**Problem:** The five pillars cannot all be built at once, and the data behind them differ in both cost and accessibility.

**Decision:** Tackle the Documentation pillar first. The whitepaper brings together a project's technical, economic and marketing vision in a single document, it is costly for a weak project to fake, and Documentation is the only pillar free of all the obstacles listed below.

**Alternatives ruled out:**

- Community, whose social data requires paid APIs
- Technology and code, whose analysis relies heavily on LLMs and is costly in tokens
- Team, which involves handling personal data
- Tokenomics, which requires extensive manual research

**Cost:** The whitepaper is what a project says about itself, and until the other pillars are covered, nothing checks it against what the project actually does.

## D5. Deployable from Day One

**Problem:** A notebook prototype cannot be deployed, and a personal machine cannot handle the full workload, let alone host a public website.

**Decision:** Design the project from the start as a production-ready application that runs the same way locally and in the cloud. The provider will be chosen according to the available startup credits, with AWS preferred but not required. Several later decisions follow from this one, notably D9, D16 and D18.

**Alternative ruled out:** Prototype in a notebook first and make the code production-ready along the way.

**Cost:** A significant engineering investment before any analysis result is produced.

## D6. Deterministic First, the LLM as Arbiter

**Problem:** Although well suited to text, LLMs are non-deterministic: the same document can produce different results from one run to the next. This is incompatible with a corpus whose rows must be comparable. Their outputs are also hard to explain and using them is expensive.

**Decision:** Two rules:

- Measurements rely on proven deterministic methods. Where the variety of documents pushes these methods to their limits, the model acts as an arbiter: it confirms candidates produced upstream, or chooses between them, rather than generating its own answer.
- Generation is reserved for reading aids, such as summaries and image descriptions. Generated text never feeds into the measurements.

**Alternatives ruled out:**

- Sending the full document to the model
- Adding RAG or agents to showcase skills, which would amount to a solution looking for a problem. These techniques may be adopted later if a real need arises.

**Cost:** Each call requires structuring the problem upstream, and the boundary between generation and measurement has to be enforced in the code: any generated text must remain identifiable so that it can be excluded from the measurements.

## D7. Starting with PDF

**Problem:** Early whitepapers were mostly published as PDFs, while more recent projects have moved to GitBook. The two formats require separate processing pipelines.

**Decision:** Handle PDF first. It is the corpus's historical format, and well-established extraction libraries already exist, whereas GitBook will likely require in-house tooling. Starting with PDF also means the analysis can be prototyped earlier, and it is the analysis that determines what needs to be extracted and how.

**Alternative ruled out:** Start with GitBook and build in-house extraction tooling before knowing what the analysis will require.

**Cost:** Even established libraries such as PyMuPDF produce imperfect output that needs cleaning, and the table of contents remains hard to retrieve. Until GitBook is handled, the corpus stays biased toward the post-ICO era, which silently skews any comparison.

## D8. API First, with FastAPI and Streamlit

**Problem:** Prototyping needs to be fast, but the logic must remain reusable beyond the prototype.

**Decision:** Use FastAPI for the API, which exposes all the logic, and Streamlit for a prototype interface. Both tools were already familiar and quick to set up.

**Alternative ruled out:** Build the whole application in Streamlit. This would have been faster at first, but the logic would not have survived a change of interface.

**Cost:** Two layers must be kept in sync: every change to the API has to be reflected in the interface, which falls behind whenever that step is skipped.

## D9. Centralized Configuration, Nothing Hardcoded

**Problem:** Hardcoded parameters scattered across the code make every migration of the stack costly and risky and prevent the same code from running identically locally and in the cloud.

**Decision:** Centralize all configuration in a single place and derive every service endpoint from it, so that moving the stack, or even a single service, requires no code changes. Secrets are kept separate and excluded from the repository and will be supplied through the platform's environment variables at deployment. Follows from D5.

**Alternative ruled out:** Define each value where it is used.

**Cost:** A heavier setup at the start, with a configuration schema to be settled before writing the rest of the code, so that it is clear where each parameter should be read from.

## D10. Free LLMs by Default

**Problem:** Prototyping involves many model calls, each of which a commercial provider would bill. Yet frontier models are not needed: the LLM only acts as an arbiter on deliberately narrow tasks, which makes paid calls an avoidable expense at this stage.

**Decision:** Develop on free models, either local or hosted, and keep paid APIs as an occasional backup. The free models are used first for rapid prototyping, then for prompt optimization.

**Alternative ruled out:** Commit a budget to frontier models from the start.

**Cost:** The first call to a local model takes about 90 seconds from a cold start, compared with roughly one second in the cloud. A local model can also get stuck looping on its own output.

## D11. The Model Name Determines Where Calls Go

**Problem:** Development runs on free LLMs (D10), but some tasks occasionally require a more capable model and comparing the free and paid models is part of the work ahead. Switching between them must be possible at any time without changing the code or the service configuration.

**Decision:** Let the model's name alone determine which endpoint is called, local or hosted, so that switching models also changes the destination, with no other setting to adjust.

**Alternative ruled out:** Add a separate endpoint setting, which would have to be kept consistent with the chosen model.

**Cost:** The rule is implicit: the system's behavior cannot be predicted without knowing it. It also relies on the provider's naming convention, so if that convention changes, requests will be silently sent to the wrong destination.

**Status:** Transitional. The convention only distinguishes between two destinations from the same provider. A proper routing layer will be needed to add other providers, to choose the destination based on the task, or to fall back to another model when a call fails.

## D12. Business Logic Independent of the API

**Problem:** Business logic mixed into the API can only be used through it. Yet the logic must also serve other consumers: another interface, scripts, and possibly, in time, an analysis agent.

**Decision:** Separate the interface, the API, the business logic and the persistence layer from the start, so that each can be replaced without affecting the others. The business logic never imports anything from the API: the API calls the logic, which calls persistence, never the other way around.

**Alternatives ruled out:**

- Putting the logic directly in the routes: faster to write, but unusable outside the API
- Moving the logic out of the routes while still allowing it to import from the API, including its schemas, which risks circular imports and couples it to the HTTP contract
- A full hexagonal architecture, where the logic does not even depend on persistence: more rigorous, but overkill for a single-person project

**Cost:** Conversion code at every boundary, and a rule enforced only by discipline, since no tool checks the imports yet.

## D13. A Cascade for Extracting the Table of Contents

**Problem:** The table of contents shapes how a document is read, but in PDFs it is hard to extract (D7). Whitepapers share no common format, and this is compounded by their authors' layout habits, artifacts from PDF conversion, and inconsistent use of fonts and sizes.

**Decision:** Extract it in stages. First, use the PDF's native bookmarks if they exist. Otherwise, visual heuristics propose candidates based on font size relative to body text, font weight, numbering patterns, and exclusion lists for crypto addresses and URLs. The model then confirms the candidates and assigns each a heading level. If the model fails, a purely heuristic fallback takes over. This is a direct application of D6: the prompt stays short, the output is constrained and therefore verifiable, and a model failure degrades the result rather than losing it entirely.

**Alternatives ruled out:**

- Handing the full document to the model to produce the table (see D6)
- Relying on heuristics alone: each edge case calls for another rule, with diminishing returns, whereas a small model can absorb this variability at lower cost

**Cost:** Several code paths to maintain, heuristics to tune on a heterogeneous corpus, and reliability that has yet to be measured across the full corpus.

## D14. Two Ways to Read a Document

**Problem:** A whitepaper's table of contents reflects the structure chosen by its authors. No two documents have the same sections in the same order, so a segmentation based on the table of contents cannot be used to compare documents.

**Decision:** Run two separate processes. The first serves the reading of a single document: it follows the document's own table of contents to offer quick navigation, with a section-by-section summary and sentiment analysis, and its output is stored as files. The second serves comparison: drawn from the literature, it uses topic modeling to map the text onto a fixed outline shared by all documents (introduction, risks, content and other parts), and it feeds the fact tables and enables comparison across the whole corpus.

**Alternative ruled out:** Compare documents based on their own tables of contents.

**Cost:** Two processes for the same document, and a shared segmentation that depends on a methodology yet to be settled.

## D15. One Representation per Target Instead of a Single Data Model

**Problem:** The project's data takes many forms: database rows, JSON and Markdown files, images, PDFs and API responses. A single data model based on one of them would impose its shape on all the others.

**Decision:** Let the business logic work with its own objects, independent of any format, and handle conversion at the boundaries: JSON serialization for object storage, Pydantic models for API responses, and SQLAlchemy models for the tables.

**Alternative ruled out:** SQLModel, which merges the API model and the table definition. It would tie the business logic to a single format, relational tables, even though most outputs do not fit them. It would also make the API contract mirror the database schema.

**Cost:** A conversion at every boundary, and manual alignment between business objects and tables. This alignment calls for a contract test that has yet to be written.

**Current gap:** API responses carry metrics as an untyped dictionary. Database writes also re-read the cached API response rather than the business object, so the API contract still sits on the persistence path.

**Revisit if:** The synchronization overhead outweighs the gain in flexibility and no external consumer depends on a stable contract.

## D16. Three Storage Layers, One Role Each

**Problem:** A document is pending in the working area until it exits, either retained or deleted (D19), and the data it produces varies in volume, lifespan and access patterns. Keeping files, working state and durable facts in a single storage system would favor one at the expense of the others.

**Decision:**

- MinIO for files, including analysis results kept as JSON
- Redis for the working area: the state of pending documents and results bound for the database
- PostgreSQL for durable facts

Nothing is written to the database before finalization, so that a submitted document can eventually be held back long enough to verify that it is authentic and safe. No step is recomputed to work around a missing key, and no layer is read in place of another to fill a gap. MinIO was chosen for its S3 compatibility, in line with D5.

**Alternatives ruled out:**

- A single storage system for everything
- Writing directly to the database with no working area, which rules out checking a document before it is stored
- Introducing Redis only at deployment: one fewer system today, but a working area to bolt onto a pipeline that is already built

**Cost:** Three systems to run instead of one. Redis currently serves only as the working area, a light load for a dedicated system, and will only be used more fully once per-user sessions and rate limiting, deferred to deployment (D27), are in place.

## D17. A Star Schema

**Problem:** Analysis families do not progress at the same pace: some are already computed, while others are waiting for a methodology that has yet to be settled. Adding a new indicator must not disrupt existing ones.

**Decision:** Use a single whitepaper dimension, shared by one fact table per family: structure (including image statistics), sentiment, named entities and references. Families still awaiting their methodology exist as placeholders, with their keys but no measurement columns. The sentiment table is already indexed by document and by section, ready for the shared segmentation.

**Alternatives ruled out:**

- A single table combining all analyses
- Guessing the columns of pending families now, at the cost of a later migration on data already ingested

**Cost:** More tables and joins, and a schema that looks unfinished, because it is.

## D18. Nothing on Local Disk

**Problem:** Local files were acceptable early in development, but they do not scale: a result stored on one instance's disk is invisible to the others, a service that writes to its own disk cannot be replicated without a shared volume, and in a container, anything written locally is lost whenever the container is replaced.

**Decision:** Files only pass through temporary directories, and everything that must be kept goes to object storage. First applied to the table of contents and analysis results, the rule was then extended to the whole pipeline. The service is now stateless, so that a result computed by one instance is visible to all of them. Follows from D5.

**Alternative ruled out:** A cache and working files on local disk.

**Cost:** Every step has to download its inputs before running. Moreover, since existing results are not recomputed, stored results can mask a change in processing logic across all instances at once. This limitation is documented in the repository.

## D19. A Single Exit Point from the Working Area

**Problem:** A document can leave the working area for several reasons: a user action, the end of a session or a scheduled task. Writing one exit path for each would duplicate the same logic, and a single inconsistency could remove a document from the working area but leave its files behind.

**Decision:** Provide a single exit point that handles both possible outcomes: keeping the document permanently (finalization) or deleting it. The outcome is decided when the document is submitted, not when it exits, so every trigger makes the same call. If an ID is provided, it identifies the document to process; otherwise, the document currently open in the session is used.

**Alternative ruled out:** One exit path per trigger.

**Cost:** This exit point becomes the only way a document can leave the working area. Automatic expiration would bypass it, so working keys must not expire on their own (D20).

**Current gap:** An ID passed as a parameter is ignored when a session is open, even though the decision gives it priority over the session.

## D20. Working Keys Do Not Expire

**Problem:** By default, keys in the working area expired after one hour. Since finalization re-reads the structural analysis stored there, it failed whenever it came more than an hour after the analysis, which was the case every time a document was resumed in a later session.

**Decision:** Remove expiration from working keys and make the single exit point solely responsible for deleting them. Follows from D19.

**Alternative ruled out:** Extend the expiration time, which only postpones the failure rather than preventing it.

**Cost:** Abandoned documents leak keys indefinitely until the scheduled cleanup described below is built.

**Status:** Transitional. In development, timing can be controlled and keys can be cleaned up by hand. Production will require abandoned documents to expire, but through a scheduled task that calls the single exit point (D19) rather than through native key expiration, so that their files are removed along with their keys.

## D21. Measurements Rather Than Ratings

**Problem:** Rating platforms in the sector are marked by structurally optimistic assessments, documented conflicts of interest and, in several cases, sanctions or shutdowns. There is also a methodological obstacle: the project has no measure of quality yet, such as labeled data, against which the indicators could be tested. Any weighting that combined them into a score would therefore be arbitrary, and presenting it as a verdict on a project would assert a link that has not been demonstrated.

**Decision:** Output raw values and a document's position within a distribution, never an aggregate score or a risk level. This departs from the initial goal: a fundamentals score.

**Alternative ruled out:** An aggregate score, which would have inherited the format's weaknesses. It would also have turned a verifiable measurement into a judgment about an identified project, with the legal exposure that comes with it.

**Cost:** The output is harder to read at a glance for a non-technical reader, who has to interpret several dimensions rather than a single number. Without a single number, no overall ranking of documents is possible, even though some users will expect one.

## D22. CoinMarketCap as the Source

**Problem:** Building a comparable corpus requires three things: a list of projects broad enough for the distributions to be meaningful, a common identifier that other sources can use as a matching key, and the whitepaper URL of each project. Academic databases only cover projects with recorded ICO data, which limits the number of usable documents.

**Decision:** Build an in-house corpus from CoinMarketCap. After a review of many sources, it was the only one found to provide whitepaper links free of charge, across a broad enough scope. External databases will be integrated later, once ingestion is complete.

**Alternatives ruled out:**

- TORD (Token Offerings Research Database) by Paul Momtaz: 10,807 hand-collected offerings, but only about 40% with a document URL, and it would have needed thorough exploration before being used. It is planned for later integration, which its existing CoinMarketCap identifier will make easier.
- Scraping aggregators: whitepaper.io no longer seems to be updated, and others raise unresolved legal questions.
- Buying a commercial dataset, such as golden.com, which was too expensive for the project and whose documents are protected against automated retrieval in any case.

**Cost:** The corpus inherits CoinMarketCap's listing coverage, so any project that was never listed there is missing from it. Building it internally also means handling retrieval, cleaning and verification that a commercial dataset would have spared the project.

## D23. An Internal Identifier, Never the Ticker or the Name

**Problem:** Each external source identifies projects in its own way. Among the 38,409 coins listed on CoinMarketCap, 5,682 of the 26,286 distinct tickers are used by more than one coin, and 956 names are shared in the same way. A join on the ticker or the name would silently attach documents to the wrong project.

**Decision:** Assign each document a unique internal identifier, regardless of its origin. Identifiers from external sources, starting with CoinMarketCap's, are kept as matching keys. Tickers and names serve only as display attributes, never as keys.

**Alternative ruled out:** Using the ticker or the project name as a key.

**Cost:** A cleaning and matching step before any external source can be used.

**Status:** Transitional. Document identity is settled, but project identity is not. It has yet to be decided how to link several documents to the same project and how to track successive versions of its documentation. Until then, the CoinMarketCap identifier is meant to serve as the matching key between documents and projects.

**Current gap:** The documents table still lacks a column for the CoinMarketCap identifier. It must be added before ingestion, or no ingested document will be linkable to a project.

## D24. Recovery Through the Internet Archive

**Problem:** On the live web, only about one whitepaper in five is still accessible. Older projects have shut down their websites, and the platforms that hosted their documents have disappeared along with them. The ICO era was by far the hardest hit.

**Decision:** Recover dead URLs from web archives: query the Internet Archive for each whitepaper that is no longer online.

**Alternative ruled out:** Keep only documents still online, at the cost of a corpus limited to surviving projects and therefore subject to survivorship bias.

**Cost:** The corpus inherits the biases of what was archived (truncation, selection). Since these biases have been identified and measured but not corrected, they remain part of the corpus and must be reported with every analysis. Moreover, the Internet Archive is slow, and querying it once per URL across several thousand URLs required a parallelized collector rather than a simple download loop.

## D25. Measurement-Driven Development

**Problem:** With the technical foundation in place, the next decisions are no longer about what works but about what works well: processing cost, application response time and the quality of the analyses produced. None of these three are systematically measured yet, and they trade off against one another: cheaper processing often means lower quality. A project that produces verifiable measurements of documents cannot hold itself to a lower standard.

**Decision:** Instrument the pipeline so that every processing step is logged with figures, and base later decisions on these records: what to keep, what to replace and what to improve. Cost, response time and quality are always measured together, so that none of them improves at the expense of another without it being seen.

**Alternative ruled out:** Rely on intuition, tackling whatever seems slow or expensive, at the risk of improving one metric while unknowingly degrading another.

**Cost:** Work sessions that deliver no new features, and instrumentation to write and then maintain, with token usage and processing time logged for every call.

**Status:** Not yet implemented. The instrumentation has yet to be written, and no processing step is logged with figures so far.

## D26. A Read-Only Ingested Corpus and a Working Copy

**Problem:** Ingesting the corpus requires compute time and model calls, so any data that is lost or corrupted must be paid for again in full. And experimenting on real data inevitably damages some of it.

**Decision:** Once ingestion is complete, the ingested corpus becomes a durable, read-only reference. All exploration and analysis are carried out on a disposable working copy that can be rebuilt from it.

**Alternative ruled out:** Work directly on the ingested corpus and rerun ingestion if something goes wrong.

**Cost:** Storage is doubled, and any correction to the reference requires a new ingestion run on the affected documents, after which the working copy must be updated.

**Status:** Not yet implemented. The rule takes effect once ingestion is complete.

## D27. What Can Be Bolted On Later Can Wait

**Problem:** Several of the project's choices anticipate needs that do not exist yet, such as a working area before any document is submitted by a third party (D16), or a separation of layers before a second consumer exists (D12). User accounts, authentication and rate limiting fall into the same category but are handled differently.

**Decision:** Defer user accounts, authentication and rate limiting until deployment. These components can be bolted onto an existing application without rewriting it, whereas a working area or a boundary between layers requires reworking whatever was built without them.

**Alternative ruled out:** Build them now, at the cost of complexity that would weigh on every development step while there is still nothing to protect.

**Cost:** Some work is pushed back to launch, adding to the workload at a time when other issues will also be pressing.

## D28. Interpretation on the Fly, Distribution Precomputed

**Problem:** The output format is not fixed, and an indicator stored in interpreted form requires a migration whenever the interpretation changes. However, placing a document means comparing it with the whole ingested corpus, and redoing that computation each time a document is displayed becomes costly as the corpus grows.

**Decision:** Store only raw values in the fact tables, and compute at display time everything that interprets them: percentiles, qualitative labels and other comparisons against the ingested corpus. The exception is the corpus-level distribution itself, which changes only when a batch is ingested or the analysis method changes, so it is computed once and stored in its own table. Any document, including one that has been submitted but not yet ingested, can then be placed against this distribution without re-reading the whole ingested corpus.

**Alternative ruled out:** Store percentiles or qualitative labels directly. Both go stale as soon as the corpus grows.

**Cost:** A document's position is recomputed at every display, and the distribution becomes a second representation to keep consistent with the facts.

**Status:** Partly implemented. The raw-values rule is in place, and the distribution table is planned for the first version of the website.
