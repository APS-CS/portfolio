# 🤖 AI CXO Agents (OpenClaw)

> **Status:** In progress — built and documented incrementally

## The idea

Most people run an AI assistant as a single chat window. This project asks a different question: **what happens if you organise AI agents the way you organise a company?**

Instead of one general-purpose assistant, the platform runs a structured organisation of agents — a small permanent leadership layer, functional managers under them, and short-lived workers that are spawned to do one narrow, mechanical task and then disappear. Each agent has a defined role, a defined mandate, and nothing beyond it.
        You (owner / CEO)
               |
      Permanent leadership layer
     (operations, security, finance, IT)
               |
       Functional managers
               |
    Ephemeral task-level workers

Everything runs self-hosted on my own hardened server. Nothing about the setup depends on a third party hosting the agents.

## Why this is a security project

An autonomous agent is, for all practical purposes, a user account that can be socially engineered. It reads untrusted input, it holds credentials, and it takes actions. That makes the interesting problem an **information security problem**, not an AI problem — and the design applies the same principles you'd apply to human staff and service accounts:

| Principle | How it's applied |
| :--- | :--- |
| **Need-to-know** | Each agent is told only what its own function requires. Infrastructure, topology and unrelated services are deliberately withheld — even from agents running on that infrastructure. |
| **Least privilege** | Tooling and capabilities are scoped per role, not shared globally. |
| **Strict reporting lines** | No lateral agent-to-agent communication. All coordination flows vertically, so no agent can be used as a pivot to reach another. |
| **Blast radius** | Isolation and containment assumed by default; the platform is designed on the premise that an agent *will* eventually be manipulated. |
| **Data hygiene** | Sensitive data is masked before anything is written to long-term storage. |
| **Attack surface reduction** | Components that don't need to listen on a network don't. Internal services were rewritten to remove open ports entirely. |

The goal is not just "agents that work" — it's agents that fail safely.

## ✅ What's done

- Hardened host and an isolated container runtime for the platform
- Agent hierarchy, role separation and mandates defined and documented
- **First live pipeline:** automated, scheduled external monitoring that collects and triages information daily and escalates into a weekly report — running unattended on a schedule
- Architecture for long-term agent memory: what an agent is allowed to remember, where it's stored, and how it's kept separated per role
- Sanitisation layer designed to strip sensitive data before storage
- Specification for the first task-level worker agent, deliberately chosen to have zero blast radius and deterministic, testable output

## 🔜 Roadmap

- Additional functional pipelines (IT operations, cost tracking, tech watch)
- Hardening review and threat modelling of the agent-to-agent boundaries
- Validation of the target agent count against real hardware and cost limits

## 💡 What I've taken away so far

- The hardest part isn't getting agents to do things — it's deciding what they're allowed to know. Most failure modes trace back to an agent having  context it never needed.
- Prompt injection stops being theoretical the moment an agent reads external content on a schedule.
- Classic infosec doctrine (segmentation, least privilege, need-to-know) maps onto autonomous agents almost unchanged.

---
