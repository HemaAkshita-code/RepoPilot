# 🔎 RepoPilot

### An Agentic AI System for Intelligent Repository Investigation

RepoPilot is an **open-source repository investigation agent** that uses **Gemma** and a registry of specialized code-analysis tools to investigate software repositories, trace code flows, discover dependencies, and answer complex questions about unfamiliar codebases.

Instead of simply summarizing source code, RepoPilot **acts as an investigator**: it decides what evidence it needs, selects the appropriate tool, inspects the repository, observes the result, and iteratively builds a grounded explanation.

---

## 🚀 The Problem

Understanding an unfamiliar codebase can be slow and frustrating.

Developers often need to answer questions such as:

* Where does a particular API request go?
* Where does authentication actually happen?
* Which files depend on this module?
* Where is this function called?
* How does data flow from the frontend to the database?
* What is the architecture of this project?
* What happens internally when a specific feature is triggered?

Answering these questions manually often requires jumping between files, searching for symbols, following references, and building a mental model of the repository.

### RepoPilot aims to make this investigation conversational.

Instead of manually navigating the codebase, a developer can ask:

> **"Trace the login flow from the API endpoint to the database and explain where authentication occurs."**

RepoPilot investigates the repository and produces an evidence-based explanation.

---

# 🧠 How RepoPilot Works

RepoPilot follows an **agentic investigation loop**.

```text
                    User Question
                          │
                          ▼
                   ┌─────────────┐
                   │   Gemma LLM │
                   │  Reasoning  │
                   └──────┬──────┘
                          │
                  Select next tool
                          │
                          ▼
                 ┌─────────────────┐
                 │   Tool Registry │
                 └────────┬────────┘
                          │
                          ▼
                  Repository Tool
                          │
                          ▼
                     Code Evidence
                          │
                          ▼
                   ┌─────────────┐
                   │   Gemma LLM │
                   └──────┬──────┘
                          │
                   Need more evidence?
                     /          \
                   Yes           No
                   │              │
                   ▼              ▼
                 Tool         Final Answer
                 Call
```

The model does **not** receive the entire repository and blindly generate an answer.

Instead:

1. The user asks an investigation question.
2. Gemma determines what information it needs.
3. Gemma selects an appropriate repository tool.
4. The tool executes against the codebase.
5. The resulting evidence is returned to the model.
6. Gemma decides what to investigate next.
7. The process continues until sufficient evidence has been collected.
8. Gemma generates a final explanation grounded in the collected evidence.

This makes RepoPilot an **agent rather than a conventional code summarizer**.

---

# 🛠️ Tool Registry

RepoPilot exposes repository-analysis capabilities through a centralized **Tool Registry**.

The registry acts as the bridge between the LLM and the repository.

### Currently registered tools

| Tool                       | Purpose                                      |
| -------------------------- | -------------------------------------------- |
| `list_files`               | Explore repository structure                 |
| `read_file`                | Read source files                            |
| `search_code`              | Search for code patterns or keywords         |
| `search_repository`        | Search repository content                    |
| `find_symbol`              | Locate functions, classes, and other symbols |
| `find_references`          | Find references/usages of a symbol           |
| `get_symbol_relationships` | Discover relationships between symbols       |
| `trace_call_flow`          | Follow function call chains                  |
| `get_file_dependencies`    | Analyze file/module dependencies             |

The LLM does not directly manipulate the repository.

Instead, it requests a tool through the registry:

```text
Gemma
  │
  │ "Use search_code"
  ▼
Tool Registry
  │
  ▼
search_code(...)
  │
  ▼
Repository
  │
  ▼
Evidence
  │
  ▼
Gemma
```

This provides a controlled and extensible interface between the reasoning model and repository analysis layer.

---

# 🔬 Example Investigation

### Question

> **Trace the login flow from the API endpoint to the database and explain where authentication occurs.**

RepoPilot dynamically investigated the repository.

### Step 1 — Search

```text
search_code("login")
```

The agent identified the login-related code.

### Step 2 — Inspect the API

```text
read_file("app/routes.py")
```

The agent discovered that:

```text
login_route()
       │
       ▼
authenticate_user()
```

### Step 3 — Follow authentication

```text
read_file("app/auth.py")
```

The agent found the authentication logic and discovered a database call:

```text
authenticate_user()
       │
       ▼
get_user_by_id()
```

### Step 4 — Inspect the database layer

```text
read_file("app/database.py")
```

The agent followed the flow into the database layer:

```text
get_user_by_id()
       │
       ▼
query_db()
       │
       ▼
SELECT * FROM users ...
```

### Final reconstructed flow

```text
API Request
     │
     ▼
login_route()
     │
     ▼
authenticate_user()
     │
     ├── Validate credentials
     │
     ▼
get_user_by_id()
     │
     ▼
query_db()
     │
     ▼
Database
```

RepoPilot then explains **where authentication occurs and how the request travels through the codebase**, rather than merely listing the files involved.

---

# 🏗️ Architecture

At a high level, RepoPilot consists of four major components:

```text
┌───────────────────────────────────────────────┐
│                    User                       │
│       Natural-language investigation          │
│                   question                    │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                Agent Controller               │
│                                               │
│      Investigation loop / orchestration       │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                  Gemma LLM                    │
│                                               │
│     Reasoning + tool selection + synthesis    │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                 Tool Registry                 │
│                                               │
│  Search │ Read │ Symbols │ References │ Flow │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                  Repository                   │
│                                               │
│          Source code + project structure      │
└───────────────────────────────────────────────┘
```

---

# 🤖 Why an Agent?

A traditional code assistant might work like:

```text
Question
   ↓
LLM
   ↓
Answer
```

RepoPilot instead follows:

```text
Question
   ↓
Reason
   ↓
Choose Tool
   ↓
Inspect Code
   ↓
Observe Evidence
   ↓
Reason Again
   ↓
Choose Another Tool
   ↓
...
   ↓
Final Explanation
```

This allows the system to investigate questions where the answer is distributed across multiple files and layers of a repository.

---

# ✨ Key Features

### 🔎 Repository Exploration

Navigate unfamiliar repositories using natural-language questions.

### 🧩 Tool-Based Investigation

Use specialized tools for searching, reading, symbol discovery, references, dependencies, and call-flow analysis.

### 🤖 Agentic Reasoning

Gemma dynamically determines what to investigate instead of following a fixed sequence.

### 🔗 Code Flow Tracing

Follow execution paths across functions and modules.

### 📚 Evidence-Grounded Answers

Final explanations are constructed from evidence collected directly from the repository.

### 🧱 Extensible Tool Registry

New repository-analysis capabilities can be added as tools without redesigning the entire agent.

### 🌐 Open Source

Designed as an extensible foundation for intelligent codebase investigation.

---

# 🧪 Current Demonstration

RepoPilot has been tested against:

* A controlled fixture repository for validating investigation behavior.
* A real React-based project repository (**PetBloom**) to test investigation on a larger codebase.

Example:

```bash
python backend/main.py C:\path\to\repository "explain the architecture of the project"
```

The agent can then inspect the repository and iteratively gather evidence.

---

# ⚙️ Getting Started

## Prerequisites

* Python 3.x
* A compatible Gemma API endpoint/API key
* Git

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd RepoPilot
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required API credentials/environment variables.

---

# ▶️ Running RepoPilot

### Investigate the included fixture repository

```bash
python backend/main.py
```

### Investigate another repository

```bash
python backend/main.py "C:\path\to\repository" "your investigation question"
```

For example:

```bash
python backend/main.py "C:\Users\LENOVO\Desktop\Repositories\PetBloom" "Explain the architecture of the project"
```

---

# 📋 Example Questions

RepoPilot is designed for questions such as:

```text
Trace the login flow from the API endpoint to the database.
```

```text
Where is authentication implemented?
```

```text
What files are responsible for handling user authentication?
```

```text
Explain the architecture of this project.
```

```text
Where is this function called?
```

```text
What modules depend on this file?
```

```text
Trace the call flow from this API endpoint.
```

```text
How does data move from the frontend to the backend?
```

---

# 📊 Investigation Output

Each investigation reports:

* Investigation status
* Number of tool steps
* Tools executed
* Evidence collected
* Final explanation
* Relevant repository files

Example:

```text
INVESTIGATION RESULTS

Status: completed
Total Tool Steps: 5

Collected Evidence:
  - app/routes.py
  - app/auth.py
  - app/database.py

Final Explanation:
The login flow begins at the API endpoint,
passes through the authentication layer,
and finally reaches the database.
```

This makes the investigation process **observable and debuggable**, rather than treating the LLM as a black box.

---

# 🧭 Design Philosophy

RepoPilot is built around three principles:

### 1. Investigate, Don't Guess

The model should gather evidence from the actual repository before producing an explanation.

### 2. Reason Through Tools

Repository interaction is performed through explicit, specialized tools rather than unrestricted model behavior.

### 3. Explain the Codebase Like a Developer

The final output should translate low-level source code into an understandable explanation of architecture, dependencies, and execution flow.

---

# 🔮 Future Direction

RepoPilot is designed to evolve into a more capable open-source repository intelligence platform.

Potential directions include:

* More advanced architectural reasoning
* Deeper dependency graphs
* Cross-language repository analysis
* Persistent repository indexing
* Visual architecture and call-flow graphs
* More sophisticated code navigation
* Test and bug investigation
* Security-oriented repository analysis
* Multi-agent repository investigation
* Local/on-device model support
* Integration with developer workflows and IDEs

The long-term goal is to make large and unfamiliar repositories **investigable through natural language**.

---

# 🧑‍💻 Technology

### Core

* **Python**
* **Gemma**
* **LLM Tool Calling**
* **Agentic Investigation Loop**
* **Repository Analysis Tools**

### Architecture

```text
User
 ↓
Agent Controller
 ↓
Gemma
 ↓
Tool Registry
 ↓
Repository Analysis
 ↓
Evidence
 ↓
Gemma
 ↓
Final Explanation
```

---

# 📌 Project Status

**RepoPilot is currently an early-stage MVP.**

The core agentic investigation loop is functional:

* Repository ingestion ✅
* Tool registration ✅
* LLM integration ✅
* Dynamic tool selection ✅
* Iterative investigation ✅
* Evidence collection ✅
* Final explanation generation ✅

The project is actively being extended toward deeper repository understanding and more sophisticated investigation capabilities.

---

# 💡 One-Line Description

> **RepoPilot is an agentic AI codebase investigator that uses Gemma and specialized repository tools to explore, trace, and explain unfamiliar software projects.**

---

## 👥 Team

Built as an open-source project exploring **Agentic AI × Software Engineering**.

---

## 📄 License

This project is open source. See the `LICENSE` file for details.
