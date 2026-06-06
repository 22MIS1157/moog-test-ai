# MoogTestAI — Process & Results Report

**Project:** AI-Powered Hardware Test & Debug Assistant
**Author:** Afnaan Ahmed P | M.Tech Software Engineering, VIT Chennai Campus
**Organization:** Moog India Technology Center Pvt. Ltd.
**Date:** June 2026
**Revision:** 1.0

---

## 1. Project Objective & Scope

### 1.1 Objective

Design and implement an AI-powered assistant that can automatically generate hardware test plans, analyze test signals, produce risk assessment matrices, and provide intelligent debugging support for Moog's electronic hardware products — starting with card-level testing of a Servo Amplifier Control Card as the pilot design.

### 1.2 Problem Statement

Hardware test engineering at Moog, like most aerospace/defense companies, relies heavily on experienced engineers who manually:
1. Read and internalize design specifications (often 50–200 pages)
2. Identify testable parameters and their acceptance limits
3. Write structured test procedures covering functional, boundary, environmental, and fault conditions
4. Analyze test results and waveforms to determine pass/fail status
5. Diagnose failures through systematic root-cause analysis

This process is time-intensive, expertise-dependent, and susceptible to human oversight — particularly for test coverage gaps. An AI assistant that can ingest design documents and produce structured test artifacts would:
- **Reduce time-to-test** by automating the specification-to-test-plan translation
- **Improve coverage** by systematically identifying testable parameters that manual reviews might miss
- **Accelerate debugging** by correlating failure symptoms with design knowledge
- **Preserve institutional knowledge** by encoding test engineering heuristics in reusable AI workflows

### 1.3 Scope

| In Scope | Out of Scope (Phase 1) |
|---|---|
| Card-level test plan generation from design specs | Real-time instrument control and data acquisition |
| Signal/waveform analysis from uploaded data | Physical test execution automation |
| FMEA-style risk assessment matrix generation | Integration with Moog's PLM/MES systems |
| Intelligent debug assistance for test failures | Compliance certification documentation |
| MCP server for tool interoperability | Multi-user concurrent access |
| CLI-based user interface | Web-based graphical user interface |

### 1.4 Deliverables

The system produces five primary deliverables:

1. **Comprehensive Test Plan** — Structured procedure with test cases, parameters, expected results, equipment requirements, and pass/fail criteria derived directly from design specifications.

2. **Signal Analysis Report** — AI interpretation of waveform data (timing diagrams, oscilloscope captures, frequency domain plots) evaluated against design specifications.

3. **Risk Assessment Matrix** — FMEA-inspired matrix scoring each testable parameter on severity (impact of failure), occurrence (likelihood based on design complexity), and detection (ability to catch the failure during testing).

4. **Debug Report** — Root-cause analysis given a set of failure symptoms, correlating observed behavior with design expectations and suggesting corrective actions.

5. **Boundary Condition Analysis** — Identification of specification edges, guard bands, and parametric regions where the design is most vulnerable to out-of-spec behavior.

---

## 2. Methodology

### 2.1 Overall Approach

MoogTestAI employs a **Retrieval-Augmented Generation (RAG)** architecture with a **multi-agent system** exposed through the **Model Context Protocol (MCP)**. This approach was selected after a comprehensive survey of eight AI tools (documented in `tool_survey.md`), which concluded that no commercial off-the-shelf tool adequately addresses hardware test automation for aerospace/defense applications.

The methodology follows three key principles:

1. **Ground every response in actual design data** — The RAG pipeline ensures the LLM never generates electrical parameters from its training data; all specifications come from the retrieved document context.

2. **Separate reasoning from interface** — The MCP server layer decouples the AI agents from the client interface, enabling access from CLI, desktop apps, or IDE plugins without modifying the core logic.

3. **Design for auditability** — Every generated test plan includes source citations, enabling engineers to trace each test parameter back to the original specification.

### 2.2 RAG Pipeline

The Retrieval-Augmented Generation pipeline is the foundation of MoogTestAI. It transforms static design documents into a queryable knowledge base that grounds every LLM response in factual specification data.

#### 2.2.1 Document Ingestion

```
Design Documents              Processing Pipeline              Vector Store
┌────────────────┐    ┌──────────────────────────────┐    ┌──────────────┐
│                │    │                                │    │              │
│ Design Spec    │───→│  PyMuPDF PDF Parser            │───→│              │
│ (.pdf)         │    │  - Text extraction              │    │   ChromaDB   │
│                │    │  - Table detection              │    │              │
├────────────────┤    │  - Image reference tagging      │    │  Collection: │
│                │    │                                │    │  moog_design │
│ Schematic      │───→│  LangChain Text Splitter       │    │  _docs       │
│ (.pdf export)  │    │  - Chunk size: 1000 chars       │    │              │
│                │    │  - Overlap: 200 chars           │    │  Embeddings: │
├────────────────┤    │  - Separator: paragraph/section │    │  Google      │
│                │    │                                │    │  embedding-  │
│ Test Procedure │───→│  Google Embedding Model         │    │  001         │
│ (.pdf)         │    │  - models/embedding-001         │    │              │
│                │    │  - 768-dimensional vectors      │    │              │
├────────────────┤    │                                │    │              │
│                │    │  Metadata Enrichment            │    │              │
│ BOM / Datasheet│───→│  - Source filename              │    │              │
│ (.pdf/.csv)    │    │  - Page number                  │    │              │
│                │    │  - Section heading              │    │              │
└────────────────┘    └──────────────────────────────┘    └──────────────┘
```

**Key Design Decisions:**

- **Chunk size of 1000 characters with 200-character overlap:** This balances retrieval granularity (smaller chunks = more precise retrieval) against context coherence (larger chunks = more complete specifications). A 200-character overlap ensures that specifications spanning chunk boundaries are captured in at least one chunk.

- **PyMuPDF over alternatives:** PyMuPDF (fitz) was selected for PDF parsing because it handles the formatting irregularities common in engineering documents — multi-column layouts, embedded tables, and mixed text/diagram pages — more reliably than alternatives like pdfplumber or PyPDF2.

- **Google embedding-001 model:** Selected for consistency with the Gemini LLM provider and strong performance on technical/scientific text. The 768-dimensional embeddings provide sufficient discriminative power for specification retrieval.

#### 2.2.2 Retrieval Strategy

At query time, the RAG retriever performs the following:

1. **Query embedding:** The user's question is embedded using the same model (embedding-001).
2. **Similarity search:** ChromaDB performs cosine similarity search against all stored chunks, returning the top-k (k=5) most relevant chunks.
3. **Context assembly:** Retrieved chunks are concatenated with source citations and injected into the LLM prompt.
4. **Grounded generation:** The LLM generates its response using only the retrieved context, with explicit instructions to cite sources and flag any information not found in the documents.

### 2.3 Multi-Agent Architecture

MoogTestAI uses specialized agents, each with a distinct system prompt and retrieval strategy optimized for its task:

```
                        User Query
                            │
                            ▼
                    ┌───────────────┐
                    │  Query Router  │
                    │  (Intent      │
                    │   Detection)  │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────────────┐
              │             │                       │
              ▼             ▼                       ▼
    ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐
    │  Test Plan   │ │   Signal     │ │     Debug        │
    │  Generator   │ │  Analyzer    │ │   Assistant      │
    │  Agent       │ │  Agent       │ │   Agent          │
    ├─────────────┤ ├──────────────┤ ├──────────────────┤
    │ Generates    │ │ Interprets   │ │ Correlates       │
    │ structured   │ │ waveforms    │ │ failure symptoms │
    │ test plans   │ │ & signals    │ │ with design      │
    │ from specs   │ │ against spec │ │ specifications   │
    └──────┬──────┘ └──────┬───────┘ └──────┬───────────┘
           │               │                 │
           └───────────────┼─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  RAG Pipeline │
                    │  (ChromaDB   │
                    │   Retrieval)  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Gemini 2.0   │
                    │ Flash LLM    │
                    └──────────────┘
```

**Agent Descriptions:**

| Agent | System Prompt Focus | Retrieval Emphasis |
|---|---|---|
| **Test Plan Generator** | Extract testable parameters; generate structured test procedures with steps, expected results, equipment, and pass/fail criteria | Electrical specifications, timing parameters, interface descriptions |
| **Signal Analyzer** | Compare provided waveform data against expected behavior; identify anomalies, timing violations, and out-of-spec conditions | Timing specifications, waveform characteristics, tolerance limits |
| **Debug Assistant** | Given failure symptoms, identify probable root causes by correlating with design specifications, known failure modes, and circuit topology | Full specification context, fault detection mechanisms, protection circuits |

### 2.4 MCP Server Integration

The Model Context Protocol server exposes MoogTestAI's capabilities as discoverable tools that any MCP-compatible client can invoke:

```
MCP Client                    MCP Server                    MoogTestAI Core
(Claude Desktop,              (JSON-RPC over stdio)         (RAG + Agents)
 CLI, IDE Plugin)
      │                              │                              │
      │  ── tools/list ──→           │                              │
      │  ←── tool schemas ──         │                              │
      │                              │                              │
      │  ── tools/call ──→           │                              │
      │     {tool: "generate_       │                              │
      │      test_plan",             │  ──→ invoke agent ──→       │
      │      args: {design:          │                              │
      │       "servo_amp"}}          │  ←── structured result ←──  │
      │  ←── result ──               │                              │
      │                              │                              │
```

**Exposed MCP Tools:**

| Tool Name | Description | Parameters |
|---|---|---|
| `generate_test_plan` | Generate a comprehensive test plan from ingested design documents | `design_name`, `test_categories`, `output_format` |
| `analyze_signal` | Analyze waveform/signal data against design specifications | `signal_data`, `signal_type`, `expected_spec` |
| `generate_risk_matrix` | Produce FMEA-style risk assessment for the design | `design_name`, `focus_areas` |
| `debug_failure` | Provide root-cause analysis for observed test failures | `failure_description`, `observed_symptoms`, `test_conditions` |
| `analyze_boundaries` | Identify boundary conditions and guard bands | `design_name`, `parameter_focus` |
| `ingest_document` | Add a new design document to the RAG knowledge base | `file_path`, `document_type` |

---

## 3. Architecture Overview

### 3.1 System Architecture

The complete MoogTestAI system follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│                                                                      │
│   ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐      │
│   │  CLI App  │    │ Claude Desktop│    │ Future: Web UI /    │      │
│   │ (Typer +  │    │ (MCP Client) │    │ IDE Plugin          │      │
│   │  Rich)    │    │              │    │                      │      │
│   └─────┬─────┘    └──────┬───────┘    └──────────┬───────────┘      │
│         │                 │                        │                  │
└─────────┼─────────────────┼────────────────────────┼──────────────────┘
          │                 │                        │
          ▼                 ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP SERVER LAYER                                │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │  MCP Server (JSON-RPC / stdio transport)                     │   │
│   │  - Tool registration & discovery                             │   │
│   │  - Input validation & schema enforcement                     │   │
│   │  - Response formatting & error handling                      │   │
│   └──────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AGENT LAYER                                    │
│                                                                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐      │
│   │  Test Plan    │  │   Signal     │  │   Debug Assistant    │      │
│   │  Generator    │  │  Analyzer    │  │   Agent              │      │
│   └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘      │
│          │                 │                      │                   │
│          └─────────────────┼──────────────────────┘                   │
│                            │                                         │
└────────────────────────────┼─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     RAG PIPELINE LAYER                                │
│                                                                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐      │
│   │  Document     │  │  LangChain   │  │  Context Assembly    │      │
│   │  Ingestion    │  │  Retriever   │  │  & Prompt Builder    │      │
│   │  (PyMuPDF)    │  │  (Top-K=5)   │  │                      │      │
│   └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘      │
│          │                 │                      │                   │
│          ▼                 ▼                      ▼                   │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │  ChromaDB Vector Store                                       │   │
│   │  Collection: moog_design_docs                                │   │
│   │  Persistence: ./chroma_db/                                   │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        LLM LAYER                                     │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │  Google Gemini 2.0 Flash                                     │   │
│   │  - Temperature: 0.2 (low creativity, high precision)         │   │
│   │  - Via LangChain ChatGoogleGenerativeAI                      │   │
│   │  - Fallback: OpenAI GPT-4o (configurable)                   │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

The end-to-end data flow for a test plan generation request:

```
Step 1: INGESTION (one-time per design)
  Design PDF → PyMuPDF → Raw Text → LangChain Splitter → Chunks
  Chunks → Google Embedding Model → Vectors → ChromaDB (persisted)

Step 2: QUERY (per user request)
  User Query → Embedding → ChromaDB Similarity Search → Top-5 Chunks
  Top-5 Chunks + System Prompt + User Query → Gemini 2.0 Flash → Response

Step 3: OUTPUT
  LLM Response → Structured Parser → Formatted Output (Markdown/JSON)
  Output → CLI Display / MCP Response / File Export
```

---

## 4. Results Summary

### 4.1 Test Plan Generation

**Input:** Design specification PDF for the Servo Amplifier Control Card.

**Output:** A structured test plan containing:

| Element | Example |
|---|---|
| Test ID | `SAC-FUNC-001` |
| Test Name | PWM Output Frequency Accuracy |
| Category | Functional |
| Objective | Verify PWM output frequency matches configured value within ±0.1% |
| Prerequisites | Card powered at 28V DC, firmware v2.1 loaded, oscilloscope connected to TP5 |
| Test Steps | 1. Configure PWM frequency to 20 kHz via SPI register 0x0A. 2. Measure output frequency at TP5 using oscilloscope. 3. Record measured frequency. |
| Expected Result | 20.00 kHz ± 20 Hz |
| Pass/Fail Criteria | PASS if measured frequency is within 19.98–20.02 kHz |
| Equipment | Oscilloscope (≥100 MHz bandwidth), SPI programmer, DC power supply |

**Key Metrics:**
- Parameters identified: 50+ testable parameters extracted from a ~30-page design spec
- Coverage categories: Functional, boundary, communication, environmental, and fault injection tests generated
- Source traceability: Each test parameter linked to its source page/section in the design document

### 4.2 Risk Assessment Matrix

**Output format:** FMEA-style matrix with Severity (S), Occurrence (O), and Detection (D) scores.

| Risk Item | Failure Mode | S | O | D | RPN | Priority |
|---|---|---|---|---|---|---|
| PWM dead-time | Shoot-through (simultaneous high/low side) | 10 | 3 | 4 | 120 | Critical |
| Current sense | Offset drift causes overcurrent | 8 | 4 | 5 | 160 | Critical |
| EtherCAT sync | Distributed clock desynchronization | 6 | 3 | 3 | 54 | Medium |
| Thermal shutdown | False triggering under normal load | 7 | 2 | 6 | 84 | High |
| SPI communication | Register corruption during write | 5 | 2 | 3 | 30 | Low |

### 4.3 Debug Report

**Input:** Symptom description — "Motor oscillates at low speed with audible 500 Hz whine."

**Output:** Structured root-cause analysis:
1. **Probable Cause 1 (High confidence):** Current loop instability — proportional gain too high for the motor inductance, causing limit-cycle oscillation at the current loop bandwidth.
2. **Probable Cause 2 (Medium confidence):** PWM dead-time too large — at low duty cycles, excessive dead-time causes current distortion that manifests as acoustic noise.
3. **Probable Cause 3 (Low confidence):** ADC noise on current feedback — insufficient filtering on the current sense signal introduces noise that the controller amplifies.
4. **Recommended actions:** Measure current waveform at TP12, check PI gains against motor parameters, verify dead-time setting in register 0x0C.

### 4.4 Signal Analysis

**Input:** Waveform data (timing measurements, frequency domain data, or oscilloscope captures described in text).

**Output:** Comparison against design specifications with pass/fail determination, identification of anomalies (ringing, overshoot, timing violations), and recommendations for further investigation.

---

## 5. Challenges Encountered & Solutions

### 5.1 PDF Parsing Challenges

**Challenge:** Engineering design documents are notoriously difficult to parse. They contain multi-column layouts, embedded tables with merged cells, inline equations, and diagrams with overlapping text labels. Standard PDF-to-text extraction frequently produces garbled output.

**Solution:** Used PyMuPDF (fitz) with block-level text extraction, which preserves reading order better than character-level extraction. Implemented post-processing heuristics to:
- Detect and reconstruct tables based on spatial alignment of text blocks
- Merge hyphenated words split across lines
- Tag specification values (voltage, current, frequency) with metadata for improved retrieval

### 5.2 Chunking Strategy Optimization

**Challenge:** Initial chunking with fixed character counts split specification tables across chunks, causing retrieval to return incomplete parameter sets. For example, a specification like "Output voltage: 28V ± 4V" might get split between "Output voltage: 28V" in one chunk and "± 4V" in the next.

**Solution:** Implemented section-aware chunking that respects document structure:
- Primary split on section headings (detected via font size/bold formatting)
- Secondary split on paragraph boundaries within sections
- Minimum chunk size enforcement to prevent fragments
- 200-character overlap as a safety net for boundary cases

### 5.3 LLM Hallucination of Electrical Parameters

**Challenge:** Despite RAG grounding, the LLM occasionally "filled in" plausible-sounding but incorrect electrical parameters when the retrieved context didn't contain the requested information. For example, it might generate a temperature specification of "-40°C to +85°C" even if the document specified "-20°C to +70°C."

**Solution:** Multi-layered mitigation:
1. System prompt explicitly instructs the model to state "Not found in available documentation" rather than guessing
2. Temperature set to 0.2 to minimize creative generation
3. Post-processing validation checks extracted parameters against retrieved context
4. All outputs include source citations so engineers can verify

### 5.4 MCP Server Async Complexity

**Challenge:** The MCP protocol uses asynchronous communication (JSON-RPC over stdio), which introduces complexity when the underlying RAG pipeline and LLM calls are also asynchronous. Race conditions and timeout management required careful handling.

**Solution:** Used Python's `asyncio` with structured concurrency patterns. Implemented:
- Timeout wrappers around LLM API calls (30-second default)
- Graceful error propagation through the MCP response format
- Connection health monitoring with automatic reconnection

### 5.5 Embedding Model Consistency

**Challenge:** Switching between embedding models (e.g., during development using OpenAI embeddings vs. production using Google embeddings) caused retrieval quality degradation because the vector spaces are incompatible.

**Solution:** Enforced embedding model consistency through configuration:
- ChromaDB collection metadata records the embedding model used during ingestion
- Retrieval refuses to operate if the query embedding model doesn't match the stored model
- Migration utility to re-embed all documents when switching models

---

## 6. Limitations & Future Improvements

### 6.1 Current Limitations

| Limitation | Impact | Severity |
|---|---|---|
| No real hardware integration | Cannot execute tests or capture live data — all analysis is document-based | Medium |
| Single-user design | No concurrent access, no user authentication | Low (pilot phase) |
| CLI-only interface | Limited accessibility for non-technical users | Medium |
| No persistent session state | Each query is independent; cannot maintain context across a debugging session | Medium |
| ChromaDB scale ceiling | Performance may degrade with very large document collections (100+ documents) | Low (pilot phase) |
| No image/schematic analysis | Cannot parse circuit diagrams — limited to text-based design documents | Medium |

### 6.2 Planned Improvements

#### Phase 2: Enhanced Intelligence

- **Redis caching layer:** Cache frequently accessed document chunks and LLM responses to reduce latency and API costs. Expected 60–80% latency reduction for repeated queries.
- **Conversation memory:** Implement LangChain's conversation buffer to maintain context across multi-turn debugging sessions.
- **Hybrid retrieval:** Combine semantic search (embeddings) with keyword search (BM25) for improved retrieval on exact part numbers, register addresses, and specification values.

#### Phase 3: Hardware Integration

- **Instrument control via SCPI:** Generate and execute test scripts that communicate directly with oscilloscopes, multimeters, and power supplies through SCPI/VISA protocols.
- **Live data ingestion:** Stream real-time test data from instruments into the signal analysis agent for immediate evaluation.
- **Automated test execution:** Close the loop from test plan generation to test execution and result analysis.

#### Phase 4: Enterprise Deployment

- **Fine-tuned domain model:** Train a LoRA adapter on Moog's historical test procedures to improve generation quality and consistency with Moog's documentation standards.
- **Web-based UI:** Build a React/Next.js frontend for broader accessibility within engineering teams.
- **Multi-user with RBAC:** Role-based access control to manage document access and test approval workflows.
- **Vector store migration:** Move from ChromaDB to Pinecone or pgvector for production-grade scalability and managed infrastructure.
- **CI/CD integration:** Trigger automated test plan regeneration when design documents are updated in Moog's PLM system.

---

## 7. Technology Stack Summary

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| LLM | Google Gemini 2.0 Flash | Latest | Primary language model for generation |
| LLM (alt) | OpenAI GPT-4o | Latest | Alternative LLM provider (configurable) |
| RAG Framework | LangChain | ≥0.2.0 | Chain orchestration, retrieval, agent management |
| Vector Store | ChromaDB | ≥0.5.0 | Embedding storage and similarity search |
| Embedding | Google embedding-001 | Latest | Document and query vectorization |
| PDF Parsing | PyMuPDF (fitz) | ≥1.24.0 | Design document text extraction |
| CLI Framework | Typer + Rich | ≥0.12.0 / ≥13.7.0 | Command-line interface with rich formatting |
| MCP SDK | mcp (Python) | ≥1.0.0 | Model Context Protocol server implementation |
| Data Processing | Pandas | ≥2.2.0 | Tabular data handling (BOM, test results) |
| Testing | pytest + pytest-asyncio | ≥8.0.0 / ≥0.23.0 | Unit and integration testing |
| Environment | python-dotenv | ≥1.0.0 | Environment variable management |
| Language | Python | ≥3.11 | Primary implementation language |

---

## 8. Conclusion

MoogTestAI demonstrates that AI-augmented hardware test engineering is both technically feasible and practically valuable. The combination of Retrieval-Augmented Generation with a multi-agent architecture addresses the fundamental challenge that general-purpose LLMs face in hardware testing: they don't know the design. By grounding every response in actual specification data retrieved from ingested documents, the system produces test plans, risk assessments, and debug analyses that are anchored in engineering reality rather than statistical patterns.

The pilot implementation using a Servo Amplifier Control Card validates the approach across multiple test categories — functional, boundary, communication, environmental, and fault injection — covering 50+ testable parameters extracted automatically from design specifications.

Key achievements:
- **Document-grounded test generation** eliminates hallucination of electrical parameters
- **Multi-agent architecture** provides specialized reasoning for different test engineering tasks
- **MCP integration** makes the system accessible from any compatible AI client
- **LLM-agnostic design** via LangChain prevents vendor lock-in
- **Zero infrastructure cost** during pilot phase using Gemini's free tier

The architecture is designed to scale — from the current CLI prototype to enterprise deployment with real hardware integration, fine-tuned models, and multi-user access. The patterns established with the servo amplifier pilot generalize directly to Moog's broader product portfolio: motor controllers, valve drivers, power modules, and sensor interface cards.

MoogTestAI is not a replacement for test engineers. It is a force multiplier — handling the specification parsing, parameter extraction, and structured document generation so that engineers can focus on the judgment calls that require human expertise: test strategy, failure interpretation, and design improvement.

---

*Document Version: 1.0 | Last Updated: June 2026*
