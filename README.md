
# Theia Guard: Approval-Based AI Execution System

## The Problem

Last week, a Meta AI security researcher panic-tweeted in real time.

Summer Yue had given her AI agent a simple instruction:

> “Organize my inbox, but ask before deleting anything.”

A reasonable safeguard.

Then she watched her phone as the agent began deleting emails.  
No confirmation. No warning. Just execution.

She couldn’t stop it remotely. She had to run to her Mac mini and manually kill the process.

> “It felt like defusing a bomb.”

What went wrong?  
The agent didn’t ignore the instruction.  
It **lost** it.  
Due to context compression and token limits, the “please confirm” constraint disappeared.

---

## Why “Please Confirm” Is Not Enough

We keep telling AI systems: “Be careful. Ask first.”  
But safety in a prompt is just a suggestion.  
A calculator doesn’t “remember” not to divide by zero — it is **designed** not to.

**Safety should not live in prompts. Safety should live in architecture.**

---

## The Solution: Controlled Automation

There is a missing layer between manual workflows and fully autonomous agents:

> **An AI system that can act — but never assumes authority.**

### Core Architecture

| Layer                | Function                                      | Principle       |
|----------------------|-----------------------------------------------|-----------------|
| Intent Parsing       | Break down user requests into steps           | Clarity         |
| Plan Generation      | Build execution plan using tools              | Transparency    |
| Risk Classification  | Label actions (Low / Medium / High)           | Awareness       |
| **Approval Gate**    | Require user validation for critical actions  | **Control**     |
| Execution Engine     | Execute approved steps                        | Capability      |
| Logging & Rollback   | Record actions, enable reversal               | Accountability  |

---

## The Critical Innovation: The Approval Gate

The Approval Gate is **not** a prompt the agent can forget.  
It is a **system-level constraint the agent cannot bypass.**

- Agent proposes → “Delete 47 emails”  
- Gatekeeper says → “User approval required from phone”  
- Agent **pauses** — not by choice, by design.

The gate lives **outside** the agent’s context window. No compression. No override. Immutable.

---

## Execution Flow

```mermaid
graph TD
    A[Agent - Intent & Plan] --> B[Risk Classification]
    B --> C{Approval Gate?}
    C -->|High Risk| D[User Approval - Phone/Telegram]
    C -->|Low Risk| E[Sandbox Execution]
    D --> E
    E --> F[Logging & Rollback]

Preventing Approval Fatigue
Not every action needs a phone buzz.
Theia Guard uses smart risk classification based on real impact:

Low Risk (/tmp/*, cache clearing) → automatic
Medium Risk (apt install, system updates) → one-click summary approval
High Risk (rm -rf ~, email deletion, sudo) → phone notification + mandatory “Approve” button

The Gatekeeper calculates risk score based on actual impact area.
The user never has to mindlessly click “Approve” on everything.
