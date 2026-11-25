# Moss Inference: book-question retrieval comparison

This repository is my hands-on Moss work sample: reproducible inference experiments, machine-readable results, and exports of the three Tasks I ran through the Portal. My unedited impressions of the Portal, Inference API, and Tasks API are in [FOUNDER_FEEDBACK_ORIGINAL.md](FOUNDER_FEEDBACK_ORIGINAL.md). These are personal observations, not claims established by the benchmark. In particular, the benchmark compares Moss's hosted book index against Graphify's PDF knowledge-graph context on only three book questions; it is **not** a general product comparison or a test of code retrieval. The Portal notes are manual observations; the repo does not contain automated Portal navigation measurements.

**Repository map:** [`benchmark.py`](benchmark.py) runs the four core inference arms; [`graphify_arm.py`](graphify_arm.py) adds Graphify; [`build_graphify.py`](build_graphify.py) builds its private PDF graph; [`export_tasks.py`](export_tasks.py) exports Portal task traces. [`logs/`](logs/) holds sanitized inference runs and [`logs/tasks/manifest.json`](logs/tasks/manifest.json) indexes Portal task results/traces and four text outputs. The copyrighted PDF, extracted book text, Graphify graph, and credentials are deliberately excluded.

Three questions from *System Design Interview: An Insider's Guide* (Alex Xu, Volume 1, second edition), three runs per question/arm, on `qwen/qwen3.8-flash`. All 45 final requests returned HTTP 200 with `status=completed`. Questions, model answers, timestamps, token usage, per-request timings, and Moss retrieval timing headers are in [`logs/`](logs/). No account keys or book text are included.

| Arm | How context reaches model | Median input tokens | Median client TTFT | Median full response | Median `X-Moss-Retrieve-Ms` | Exact answers* |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Plain | No retrieval | 131 | 896 ms | 1,857 ms | 0 ms | 7/9 |
| Moss | Existing Moss book index | 830 | 1,030 ms | 1,608 ms | 15.3 ms | 8/9 |
| Local | Top 3 lexical BM25 chunks from local PDF text in instructions | 750 | 556 ms | 1,253 ms | 0 ms | 9/9 |
| Both | Moss index + same local chunks | 1,449 | 769 ms | 1,448 ms | 15.7 ms | 9/9 |
| Graphify | Query PDF knowledge graph; pass selected node descriptions/relations | 370 | 1,013 ms | 1,269 ms | 0 ms | 7/9 |

\*Manually checked against the local PDF: Base 62 uses `0-9`, `a-z`, `A-Z` (PDF p.126); Snowflake layout is `1/41/5/5/12` bits (p.114); news-feed hybrid uses push for ordinary users and pull for celebrities (p.172). For exact scoring, an answer grouping both 5-bit IDs into a 10-bit worker ID does **not** answer the requested per-part layout; an abstention is not counted correct. Plain missed two ID-layout answers; Moss once omitted the Base 62 character set; Graphify missed two ID-layout answers. The three questions are not enough to establish general accuracy.

## Reproduce

Requirements: Python 3, `requests`, `pdftotext` (poppler), the **same edition** of the book PDF, a Moss account with an index named `system-design-interview-by-alex-xu`, and credits. No need to re-upload the book: this tests the already-created Moss index. Do not commit the PDF, extracted text, or credentials.

```bash
python -m pip install -r requirements.txt
pdftotext -layout '/path/to/System Design Interview by Alex Xu.pdf' /private/location/book.txt
# Create /private/location/credentials.json (permissions 0600):
# {"project_id":"YOUR_PROJECT_ID","project_key":"YOUR_PROJECT_KEY"}
python benchmark.py \
  --credentials /private/location/credentials.json \
  --pdf-text /private/location/book.txt \
  --output logs/another-run.jsonl
```

The script generates one random run identifier per execution to avoid Moss's reply cache returning zero input tokens for a repeated prompt. It sends the **same question** in `input` in all four arms. Local snippets go into `instructions`, not `input`, so Moss's automatic index search still queries the question rather than the whole PDF excerpt. Retrieval is explicitly disabled for the plain/local arms to override any project default index. Qwen `reasoning.effort=none` is set to avoid consuming the output cap on hidden reasoning with no answer. The script saves each response immediately to JSONL and logs no book passages or credentials.

Local search tokenizes the extracted PDF and ranks short chunks with a basic BM25 formula. This is **not Serena**: Serena indexes code symbols, not PDFs. Local search timing (recorded in run 3 only) is ~0.6–1.0 ms after PDF text extraction and chunk indexing; the table's client timings are the *API call only* and exclude local preprocessing/search. Likewise, Moss's `X-Moss-Retrieve-Ms` is a server-reported internal search duration, not network round-trip or full answer time. On the nine fresh Moss-index calls in these final runs, the reported retrieval times were 14.5–17.3 ms; no sub-10 ms observation. This does **not** benchmark Moss's separate in-process SDK claim. The hybrid arm carried both sources and roughly doubled prompt input; it was not an accuracy improvement over local alone on these questions.

## Graphify arm

Graphify v0.9.96 processed the same book PDF in a **private scratch folder**. Its semantic extraction called `moss/fastlane-1` through Moss's OpenAI-compatible API, produced 216 nodes and 231 edges, then `graphify query` selected the first eight matching nodes per question. Their node rationales and connecting edges became context for the same Qwen inference model, with Moss index retrieval disabled. Build the graph separately (requires the Graphify `pdf` and `openai` extras) and run the arm:

```bash
python build_graphify.py --credentials /private/location/credentials.json \
  --book-dir /private/book-only-folder --out /private/graphify-work
python graphify_arm.py --credentials /private/location/credentials.json \
  --graph /private/graphify-work/graphify-out/graph.json \
  --output logs/graphify-another-run.jsonl
```

The run had an important **partial-extraction limitation**: one of 16 semantic chunks returned no nodes despite retries. Its existing graph was still queryable, but it is not a complete extraction of the PDF. Graphify reported 81,311 input / 47,653 output tokens and an estimated **$0.1088** for the first graph build; this is Graphify's estimate using its generic `openai` backend prices, **not a verified Moss bill**. A retry again left one chunk hollow. The graph query took a median 338 ms; that is **excluded** from the Graphify row's API latency above. The graph omitted exact Base 62 characters and Snowflake bit counts in the retrieved node descriptions, so correct answers to those details may have come from the Qwen model's prior knowledge rather than the graph. **Do not publish `graph.json` or the PDF**: the graph was built from a copyrighted book. The sanitized Graphify JSONL logs include node names, but not book passages.

## Portal Tasks: API export

The same project key reads the browser tasks created in the Portal. `GET /v1/tasks` returned three tasks (with `limit`/`after` pagination); `GET /v1/tasks/{id}` returned result, status, timestamps, and usage; `GET /v1/tasks/{id}/trace` returned a timeline plus screenshot/video metadata; and `GET /v1/tasks/{id}/files` listed saved artifacts. [`export_tasks.py`](export_tasks.py) exported all three to [`logs/tasks/manifest.json`](logs/tasks/manifest.json), with one `task.json`, `trace.json`, and `files-manifest.json` per task, plus four small textual outputs. These are **the user's own Portal runs**, not tasks created for this inference benchmark. The trace's `steps` is a count and `timeline` is a compact event list, **not** full hidden model reasoning or a full browser recording. Screenshot and video binaries were not downloaded; their metadata remains in the trace/manifest. URLs in structured `url` fields have query strings/fragments removed, and project credentials/ID are redacted. Review task output and trace content yourself before publishing.

```bash
python export_tasks.py --credentials /private/location/credentials.json --out logs/tasks
```

**Limits:** Sequential runs on one client and a tiny, easy question set; no randomized order, concurrency/load test, cost billing cross-check, or independent manual audit of every indexed passage. Input token differences include instruction and context length; model answers, cache effects, and provider load vary. Treat latency numbers as observations, not a statistically controlled speed ranking. The book PDF is copyrighted; do not upload it or long excerpts to this repository.

Docs: [Moss inference retrieval](https://docs.moss.dev/docs/inference/retrieval.md) · [Responses usage](https://docs.moss.dev/docs/api-reference/v1/inference/responses.md) · [Moss models](https://docs.moss.dev/docs/inference/models.md)
