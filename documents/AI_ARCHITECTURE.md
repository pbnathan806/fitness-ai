# AI_ARCHITECTURE.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Overview

AI acts exclusively as the Coaching Intelligence Layer. It assists Trainers and Super Admins and never makes operational or coaching decisions.

---

## Technology Stack

| Component             | Technology     |
| --------------------- | -------------- |
| AI Orchestration      | LangGraph      |
| LLM Framework         | LangChain      |
| Primary LLM           | Groq (Llama)   |
| Background Processing | Celery + Redis |

---

## Architecture

```text
               Coaching Data
                      |
                 Celery Queue
                      |
                   Workers
                      |
                  LangGraph
                      |
                  LangChain
                      |
                 Model Router
                      |
                    Groq
                      |
                    Llama
                      |
              Coaching Intelligence
                      |
               ------------------
               |       |        |
            Reports  Trends  Recommendations
                      |
                 Human Review
                      |
                 Final Reports
```

---

## AI Responsibilities

* Weekly report generation.
* Monthly report generation.
* Progress analysis.
* Trend analysis.
* Coaching recommendations.
* Session note summarization.
* Coaching intelligence generation.

---

## AI Principles

1. AI shall always execute asynchronously.
2. AI shall never block business workflows.
3. AI recommendations shall always require human review.
4. AI shall never make operational decisions.
5. Clients shall never directly interact with AI in Version-1.

---

## Future Model Support

The model router shall support future integrations with:

* OpenAI
* Ollama
* DeepSeek
* Mistral
* Other LLM providers

> Groq (Llama) shall remain the primary provider for Version-1.

---

## Version-1 Constraints

Version-1 shall NOT support:

* AI Chatbots.
* AI Coaches.
* Autonomous AI Agents.
* AI driven scheduling.
* AI driven subscription management.
* Self-hosted models.
