# CRM + AI MVP - Big Picture

## Overview

This diagram shows the high-level architecture of the CRM + AI MVP system, including all planned modules for the complete product vision. It illustrates how different components will work together to provide a comprehensive CRM solution for small offices (1-5 people).

**Note:** This represents the **future state** after all MVP modules are implemented. For the current implementation status, see [architecture.md](./architecture.md).

## System Architecture Diagram

```mermaid
C4Container
    title CRM + AI MVP - High Level (Extendable)

    Person(user, "Small Office User", "Owner, assistant, or staff (1-5 people)")

    Container_Boundary(crm, "CRM + AI Platform (MVP)") {
        Container(web, "Web App", "React or Next.js", "UI for contacts and inbox and pipeline and tasks")
        Container(api, "API + BFF", "FastAPI or Node.js", "REST or GraphQL endpoints and auth and session and context")
        Container(crmCore, "CRM Core", "Module", "Contacts and Deals and Pipelines and Tasks")
        Container(comm, "Comm Module", "Module", "Email and SMS channel abstraction and message storage")
        Container(sched, "Scheduling Module", "Module", "Calendar integration and appointments")
        Container(bill, "Billing Module", "Module", "Invoices and payments and status")
        Container(ai, "AI Orchestrator", "Module", "Summaries and intake and follow-up and workflow generation")
        Container(db, "PostgreSQL", "Database", "Multi-tenant relational store")
        Container(queue, "Worker Queue", "Redis + Worker", "Async jobs for sync and AI calls and notifications")
        Container(files, "File Storage", "S3 or MinIO", "Documents and attachments")
    }

    System_Ext(email, "Email Provider", "Gmail or Outlook")
    System_Ext(calendar, "Calendar Provider", "Google Calendar")
    System_Ext(pay, "Payment Provider", "Stripe or PayPal")
    System_Ext(sms, "SMS Provider", "Twilio")
    System_Ext(llm, "AI Provider", "OpenAI or Anthropic")

    Rel(user, web, "Uses via browser")
    Rel(web, api, "HTTP(S)")
    Rel(api, crmCore, "Use cases for contacts and deals and tasks")
    Rel(api, comm, "Use cases for inbox and messages")
    Rel(api, sched, "Use cases for events")
    Rel(api, bill, "Use cases for invoices and payments")
    Rel(api, ai, "Invoke AI flows")

    Rel(crmCore, db, "CRUD")
    Rel(comm, db, "Store messages and threads")
    Rel(bill, db, "Store invoices and payments")
    Rel(api, queue, "Publish async jobs")
    Rel(queue, email, "Sync email messages")
    Rel(queue, sms, "Send SMS")
    Rel(queue, llm, "Call LLM for AI tasks")
    Rel(sched, calendar, "Sync events")
    Rel(bill, pay, "Charge and reconcile payments")
    Rel(api, files, "Upload and download documents")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Module Descriptions

### Core Modules (MVP)

1. **CRM Core**
   - Contact management (✅ Implemented)
   - Deal pipeline tracking
   - Task management
   - Relationship tracking

2. **Scheduling Module** (✅ Phase 1 Complete)
   - Staff management (✅ Implemented)
   - Appointment booking (✅ Implemented)
   - Calendar integration (Planned: iCal export)
   - Automated reminders (Planned)
   - Availability management (✅ Data model implemented)

3. **Communication Module** (Planned)
   - Unified inbox (email + SMS)
   - Message threading
   - Channel abstraction
   - Two-way sync with email providers

4. **Billing Module** (Planned)
   - Invoice generation
   - Payment processing
   - Payment status tracking
   - Integration with Stripe/PayPal

5. **AI Orchestrator** (Planned)
   - Email/message summaries
   - Automated intake forms
   - Follow-up suggestions
   - Workflow generation
   - Integration with OpenAI/Anthropic

### Infrastructure Components

- **PostgreSQL**: Multi-tenant relational data store (currently SQLite in dev)
- **Worker Queue**: Background job processing (Redis + worker processes)
- **File Storage**: Document and attachment management (S3 or MinIO)

### External Integrations

- **Email Providers**: Gmail, Outlook for bidirectional email sync
- **Calendar**: Google Calendar integration via iCal/ICS format
- **Payment**: Stripe or PayPal for invoice payments
- **SMS**: Twilio for text message reminders
- **AI**: OpenAI (GPT) or Anthropic (Claude) for AI features

## Current Implementation Status

### ✅ Completed (Phase 1)
- Clean Architecture directory structure
- Contact management CRUD
- Staff management CRUD
- Appointment booking and management
- Database models for scheduling
- Health check endpoints
- Comprehensive test suite (29 tests passing)

### 🚧 In Progress
- Availability management endpoints
- Slot calculation algorithm
- Conflict detection logic

### 📋 Planned (Future Phases)
- iCal calendar export
- Automated reminder system
- Email/SMS communication module
- AI-powered features
- Billing and invoicing
- Multi-tenant support

## Related Documentation

- [Detailed Architecture](./architecture.md) - Clean Architecture implementation details
- [C4 Model Diagrams](./C4.md) - Multiple levels of architectural diagrams
- [README](../README.md) - Project overview and setup instructions

---

**Last Updated:** 2025-12-14
**Status:** Phase 1 Complete (Scheduling Foundation)
