```mermaid
C4Container
    title CRM + AI MVP - High Level (Extendable)

Person(user, "Small Office User", "Owner / assistant / staff (1–5 people)")

System_Boundary(crm, "CRM + AI Platform (MVP)") {

  Container(web, "Web App", "React/Next.js", "UI for contacts, inbox, pipeline, tasks")
  Container(api, "API + BFF", "FastAPI / Node.js", "REST/GraphQL endpoints, auth, session/context")
  
  Container_Boundary(domain, "Domain Layer") {
    Container(crmCore, "CRM Core", "Module", "Contacts, Deals, Pipelines, Tasks")
    Container(comm, "Comm Module", "Module", "Email/SMS channel abstraction, message storage")
    Container(sched, "Scheduling Module", "Module", "Calendar integration, appointments")
    Container(bill, "Billing Module", "Module", "Invoices, payments, status")
    Container(ai, "AI Orchestrator", "Module", "Summaries, intake, follow-up, workflow gen")
  }

  Container(db, "PostgreSQL", "Database", "Multi-tenant relational store")
  Container(queue, "Worker / Queue", "Redis + Worker", "Async jobs: sync, AI calls, notifications")
  Container(files, "File Storage", "S3/MinIO", "Documents & attachments")
}

System_Ext(email, "Email Provider", "Gmail/Outlook")
System_Ext(calendar, "Calendar Provider", "Google Calendar")
System_Ext(pay, "Payment Provider", "Stripe/PayPal")
System_Ext(sms, "SMS Provider", "Twilio/etc.")
System_Ext(llm, "AI Provider", "OpenAI/Anthropic/Local LLM")

Rel(user, web, "Uses via browser")
Rel(web, api, "HTTP(S)")
Rel(api, crmCore, "Use cases: contacts, deals, tasks")
Rel(api, comm, "Use cases: inbox, send message")
Rel(api, sched, "Use cases: events")
Rel(api, bill, "Use cases: invoices/payments")
Rel(api, ai, "Invoke AI flows")

Rel(crmCore, db, "CRUD")
Rel(comm, db, "Store messages/threads")
Rel(bill, db, "Store invoices/payments")
Rel(domain, queue, "Publish async jobs")
Rel(queue, email, "Sync email messages")
Rel(queue, sms, "Send SMS")
Rel(queue, llm, "Call LLM for AI tasks")
Rel(sched, calendar, "Sync events")
Rel(bill, pay, "Charge / reconcile payments")
Rel(domain, files, "Upload/download documents")
```

