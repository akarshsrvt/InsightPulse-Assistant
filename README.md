# InsightPulse Assistant

> An enterprise-grade AI assistant powered by Deterministic Intent Routing, Retrieval-Augmented Generation (RAG), and Large Language Models (LLMs) for reliable, context-aware, and hallucination-resistant responses.

---

## Overview

InsightPulse Assistant is an intelligent AI system designed to overcome the limitations of traditional Retrieval-Augmented Generation (RAG) chatbots. Instead of sending every user query directly to an LLM, the system first classifies the user's intent and routes requests through specialized processing pipelines.

This hybrid architecture combines deterministic decision-making, machine learning models, semantic retrieval, and LLM reasoning to improve response accuracy, reduce hallucinations, and optimize operational efficiency.

---

## Key Features

- Deterministic Intent Routing
- Hybrid RAG Architecture
- Semantic Document Retrieval
- Gemini LLM Integration
- Machine Learning-based Classification
- Context-Aware Response Generation
- Hallucination Reduction
- Modular Backend Design
- Scalable Architecture
- Enterprise-ready Workflow

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| AI Model | Gemini |
| Framework | FastAPI |
| ML | Scikit-Learn |
| Retrieval | RAG |
| Data | Pandas |
| Documentation | Markdown |
| Version Control | Git & GitHub |

---

## Project Architecture

```
                User Query
                     │
                     ▼
          Intent Classification
                     │
        ┌────────────┴────────────┐
        │                         │
 Out-of-Scope               In-Scope
        │                         │
 Safe Response        Retrieve Context
                               │
                               ▼
                        Gemini LLM
                               │
                               ▼
                      Final AI Response
```

---

## Folder Structure

```
InsightPulse-Assistant/
│
├── chatbot/
│   ├── app.py
│   ├── intents.py
│   ├── train_churn_model.py
│   └── ...
│
├── Data/
│   ├── Raw/
│   └── Processed/
│
├── docs/
│   └── week3_genai_report.md
│
├── Notebook/
│   └── Task1.ipynb
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation

```bash
git clone https://github.com/akarshsrvt/InsightPulse-Assistant.git

cd InsightPulse-Assistant

pip install -r requirements.txt
```

---

## Run

```bash
python app.py
```

---

## Project Highlights

- Deterministic AI Pipeline
- Intelligent Intent Detection
- Reduced Hallucination
- Context-Aware Retrieval
- Enterprise-grade Architecture
- Production-ready Modular Design

---

## Future Improvements

- Multi-Agent Workflow
- Voice Assistant Support
- Memory-based Conversations
- Vector Database Integration
- Docker Deployment
- Kubernetes Support
- CI/CD Pipeline

---

## Author

**Akarsh Srivastav**

AI & Machine Learning Engineer

GitHub: https://github.com/akarshsrvt

---

## License

This project is intended for educational, research, and portfolio purposes.
