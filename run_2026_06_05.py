#!/usr/bin/env python3
"""Product Hunt scrape, score, and analysis — 2026-06-05 (second pass)"""
import csv, os

BASE = "/home/user/product-hunt-tracker"
NOW  = "2026-06-05T12:00:00.000Z"
DATE = "2026-06-05"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 – New products to append to products.csv
# ─────────────────────────────────────────────────────────────────────────────
NEW_PRODUCTS = [
    {
        "id": 1158674,
        "slug": "wallie-v2",
        "name": "Wallie V2",
        "desc": "The open-source AI streamer that actually feels alive",
        "launch": "2026-05-29T05:16:07-07:00",
    },
    {
        "id": 1162181,
        "slug": "composer-3",
        "name": "Composer",
        "desc": "Multiplayer markdown for you, your team, and your agents.",
        "launch": "2026-06-02T23:41:12-07:00",
    },
]

products_path = os.path.join(BASE, "products.csv")

# Read existing slugs
existing_slugs = set()
with open(products_path, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) > 3:
            existing_slugs.add(row[3].strip())

added_products = []
with open(products_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    for p in NEW_PRODUCTS:
        if p["slug"] not in existing_slugs:
            url = f"https://www.producthunt.com/posts/{p['slug']}"
            row = [
                str(p["id"]),          # col 0: id (PH Post ID)
                url,                   # col 1: url
                p["name"],             # col 2: name
                p["slug"],             # col 3: slug
                p["desc"],             # col 4: description
                p["desc"][:200],       # col 5: tagline
                "0",                   # col 6: unknown
                "0",                   # col 7: unknown
                NOW,                   # col 8: discovered_date
                p["launch"],           # col 9: launch_date
                "new",                 # col 10: status
                "", "",                # col 11-12: empty
                NOW,                   # col 13: scraped_at
                "", "", "", "",        # col 14-17: empty
                NOW,                   # col 18
                NOW,                   # col 19
            ]
            writer.writerow(row)
            added_products.append(p["name"])
            print(f"Added to products.csv: {p['name']} ({p['slug']})")

print(f"products.csv: {len(added_products)} product(s) added")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 – Filter unanalyzed products from analyzed_ids.csv
# ─────────────────────────────────────────────────────────────────────────────
analyzed_path = os.path.join(BASE, "analyzed_ids.csv")

existing_analyzed_ids = set()
with open(analyzed_path, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if row and row[0].strip():
            existing_analyzed_ids.add(row[0].strip())

# All 8 unanalyzed products from the feed
UNANALYZED = [
    {"id": 1160919, "name": "Agent Mode on Arena",        "slug": "arena-5",         "desc": "Get real-world tasks done with autonomous AI agents"},
    {"id": 1163741, "name": "Nemotron 3 Ultra by NVIDIA", "slug": "nvidia",           "desc": "Powers faster, efficient reasoning for long-running agents"},
    {"id": 1163789, "name": "Microsoft MAI-Voice-2",      "slug": "mai-image-2-3",   "desc": "Expressive TTS with voice cloning in 15 languages"},
    {"id": 1162305, "name": "TimeTuna.com",               "slug": "bookva-ai",        "desc": "If Calendly had gorgeous video backgrounds"},
    {"id": 1160486, "name": "Astra Autonomous Pentest",   "slug": "astra-security",   "desc": "AI agents that find, validate, and fix every vulnerability"},
    {"id": 1162731, "name": "Basedash Semantic Layer",    "slug": "basedash",         "desc": "Define metrics once. Use them everywhere."},
    {"id": 1158674, "name": "Wallie V2",                  "slug": "wallie-v2",        "desc": "The open-source AI streamer that actually feels alive"},
    {"id": 1162181, "name": "Composer",                   "slug": "composer-3",       "desc": "Multiplayer markdown for you, your team, and your agents."},
]

to_analyze = [p for p in UNANALYZED if str(p["id"]) not in existing_analyzed_ids]
print(f"\nSTEP 3: {len(to_analyze)} unanalyzed products found")
for p in to_analyze:
    print(f"  {p['id']} - {p['name']}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 – Pass 1: Quick Scoring
# ─────────────────────────────────────────────────────────────────────────────
PASS1_SCORES = {
    1160919: {"opportunity_score": 7, "market_viability_score": 8, "technical_complexity": "high",   "pass": True},
    1163741: {"opportunity_score": 3, "market_viability_score": 5, "technical_complexity": "high",   "pass": False},
    1163789: {"opportunity_score": 6, "market_viability_score": 7, "technical_complexity": "high",   "pass": True},
    1162305: {"opportunity_score": 6, "market_viability_score": 6, "technical_complexity": "medium", "pass": True},
    1160486: {"opportunity_score": 8, "market_viability_score": 8, "technical_complexity": "high",   "pass": True},
    1162731: {"opportunity_score": 7, "market_viability_score": 7, "technical_complexity": "medium", "pass": True},
    1158674: {"opportunity_score": 5, "market_viability_score": 5, "technical_complexity": "high",   "pass": False},
    1162181: {"opportunity_score": 7, "market_viability_score": 7, "technical_complexity": "medium", "pass": True},
}

passing = [p for p in to_analyze if PASS1_SCORES[p["id"]]["pass"]]
failing = [p for p in to_analyze if not PASS1_SCORES[p["id"]]["pass"]]

print(f"\nSTEP 4 Pass 1: {len(passing)} pass (score>=6), {len(failing)} fail")
for p in passing:
    s = PASS1_SCORES[p["id"]]
    print(f"  PASS  {p['id']} {p['name']}: opp={s['opportunity_score']}, mkt={s['market_viability_score']}, complexity={s['technical_complexity']}")
for p in failing:
    s = PASS1_SCORES[p["id"]]
    print(f"  FAIL  {p['id']} {p['name']}: opp={s['opportunity_score']}, mkt={s['market_viability_score']}, complexity={s['technical_complexity']}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 – Pass 2: Full Analysis for passing products
# ─────────────────────────────────────────────────────────────────────────────
ANALYSES = [
    {
        "product_id": 1160919,
        "product_name": "Agent Mode on Arena",
        "product_url": "https://www.producthunt.com/posts/arena-5",
        "category": "AI Agent Platform / Productivity",
        "value_proposition": "An autonomous AI agent platform that executes real-world tasks end-to-end—from web research to software operations—eliminating constant manual steering and unlocking genuine hands-off automation.",
        "target_audience": "Knowledge workers, developers, and business teams seeking to automate repetitive digital tasks without coding",
        "pain_points": "1. Manual task execution consumes valuable time across repetitive digital workflows\n2. Existing AI chat tools require constant human steering rather than full autonomy\n3. Context-switching between apps and tools fragments productivity and increases errors",
        "improvement_opportunities": "1. Domain-specific agent templates for industries such as legal research, finance, and HR\n2. Native integrations with enterprise systems (Salesforce, SAP, ServiceNow) for deeper workflow automation\n3. Team-level agent orchestration dashboard to manage and monitor multiple concurrent agent workflows",
        "feature_gaps": "1. Audit trails and step-level explainability needed for enterprise compliance requirements\n2. Collaborative multi-agent pipelines where specialized sub-agents hand off tasks\n3. On-premise or private-cloud deployment option for security-sensitive organizations",
        "competitors": "1. Devin by Cognition (AI software engineer agent)\n2. Google Mariner (AI web task agent)\n3. Microsoft Copilot (enterprise AI automation platform)",
        "market_viability_score": 8,
        "opportunity_score": 7,
        "differentiation_strategies": "1. Focus on a narrow vertical such as sales prospecting or competitive research where agent task scope is bounded and measurable\n2. Offer transparent agent reasoning logs so users understand and can correct what the agent did\n3. Build a marketplace of task-specific micro-agents that users can chain and customize without code",
        "technical_complexity": "high",
        "estimated_build_time": "12–16 weeks",
        "monetization_ideas": "1. Per-task credit model where users pay for agent actions consumed\n2. Team subscription tiers with shared agent pools, usage analytics, and admin controls\n3. Enterprise licenses with custom agent training, SLA guarantees, and compliance reporting",
        "red_flags": "1. Hyperscaler competition from Google, Microsoft, and OpenAI with superior resources and distribution\n2. AI agent reliability issues—silent task failures—can rapidly erode user trust\n3. Rapidly shifting foundation model landscape requires continuous re-architecture of the agent runtime",
        "recommended_approach": "Start with a single high-value vertical such as sales prospecting or competitive intelligence where task success is easily measurable. Build a lightweight agent runtime that chains existing LLM APIs and browser automation tools, and charge per successful task completion. Once the vertical is validated and trust is built, expand horizontally by adding task libraries for adjacent use cases.",
        "key_insights": "The agent platform market is winner-take-most, so vertical specificity and high task success rates are the only durable moats against better-funded incumbent competitors.",
        "analyzed_at": NOW,
    },
    {
        "product_id": 1163789,
        "product_name": "Microsoft MAI-Voice-2",
        "product_url": "https://www.producthunt.com/posts/mai-image-2-3",
        "category": "Text-to-Speech / Voice AI",
        "value_proposition": "Enterprise-grade expressive text-to-speech with zero-shot voice cloning across 15 languages, enabling developers and content creators to deploy lifelike, brand-consistent AI voices at scale via API.",
        "target_audience": "Developers building voice-enabled apps, e-learning platforms, contact center operators, and content creators needing multilingual AI narration",
        "pain_points": "1. Existing TTS sounds robotic and breaks immersion in customer-facing or educational products\n2. Cloning a brand voice requires expensive studio recordings and lengthy custom model training pipelines\n3. Maintaining multilingual voice consistency across a single brand identity is technically complex and expensive",
        "improvement_opportunities": "1. Emotion intensity sliders to tune voice personality from neutral to empathetic without re-recording\n2. Real-time low-latency streaming API optimized for live conversational AI agent use cases\n3. Built-in PII detection and redaction before audio synthesis for compliance-heavy industries",
        "feature_gaps": "1. Voice age and gender morphing without re-recording source audio samples\n2. Background noise injection API for realistic phone or IVR simulation testing\n3. SSML 2.0-level control for prosody, pacing, and emphasis in long-form audiobook narration",
        "competitors": "1. ElevenLabs (voice cloning market leader)\n2. PlayHT (API-focused TTS with cloning)\n3. Cartesia AI (real-time low-latency streaming voice)",
        "market_viability_score": 7,
        "opportunity_score": 6,
        "differentiation_strategies": "1. Target a high-value niche such as accessible audiobooks or corporate e-learning where quality and consistency outweigh unit cost\n2. Offer a white-label voice API with custom voice model training as a fully managed service for agencies\n3. Undercut incumbent per-character pricing while maintaining quality parity by building on open-weight TTS models",
        "technical_complexity": "high",
        "estimated_build_time": "16–20 weeks",
        "monetization_ideas": "1. Per-character or per-minute API pricing with volume discounts for high-throughput customers\n2. Voice library subscription allowing teams to share, reuse, and version-control cloned voices\n3. Enterprise SLA plan with dedicated inference capacity, latency guarantees, and compliance certifications",
        "red_flags": "1. ElevenLabs and major cloud TTS providers (Google, AWS, Azure) have significant head starts in quality and API ecosystem\n2. Voice cloning raises regulatory and ethical scrutiny in several jurisdictions, requiring robust consent frameworks\n3. High-quality neural TTS inference costs compress margins significantly at scale",
        "recommended_approach": "Build a specialized TTS SaaS for a single high-value vertical—enterprise e-learning or accessibility tools—where quality, consistency, and multilingual support command premium pricing. Use open-weight TTS models (Kokoro, Coqui) to reduce inference costs, then layer zero-shot voice cloning and a simple integration API on top. Price meaningfully above commodity TTS for the quality-consistency guarantee and grow through integration partnerships with LMS and content creation platforms.",
        "key_insights": "Winning in TTS requires owning a workflow or vertical rather than competing on model quality alone, as enterprise buyers choose voice providers for reliability and ecosystem integrations over raw audio fidelity.",
        "analyzed_at": NOW,
    },
    {
        "product_id": 1162305,
        "product_name": "TimeTuna.com",
        "product_url": "https://www.producthunt.com/posts/bookva-ai",
        "category": "Scheduling / Meeting Productivity",
        "value_proposition": "A visual-first scheduling tool that replaces generic calendar booking links with personalized video-background pages, turning appointment booking into a branded, high-conversion first impression.",
        "target_audience": "Sales professionals, coaches, consultants, and small business owners who rely heavily on scheduling links as first-touch outreach",
        "pain_points": "1. Calendly and similar tools produce generic booking pages that feel impersonal and low-effort to prospects\n2. Sales teams cannot differentiate their outreach experience when the booking page is the first brand touchpoint\n3. High-friction or bland booking UX leads to drop-offs before meetings are confirmed",
        "improvement_opportunities": "1. Dynamic video backgrounds that adapt automatically based on meeting type, audience segment, or time of day\n2. Embedded short host introduction videos that build rapport before the call even starts\n3. AI-powered scheduling suggestions based on the invitee's stated availability preferences",
        "feature_gaps": "1. A/B testing of booking page designs to quantify conversion rate impact of different visual styles\n2. CRM integration that auto-creates or updates contact records when a booking is confirmed\n3. Group or round-robin team scheduling pages where any available host can accept the meeting",
        "competitors": "1. Calendly (dominant scheduling market leader)\n2. Cal.com (open-source scheduling alternative)\n3. SavvyCal (UX-focused scheduling with recipient control)",
        "market_viability_score": 6,
        "opportunity_score": 6,
        "differentiation_strategies": "1. Position as a conversion optimization tool—not just a scheduler—by measuring booking-to-deal rates and proving ROI\n2. Target video-first creators and coaches on YouTube and LinkedIn who already invest in branded visual experiences\n3. Offer native inline embeds in email signatures so the video background previews without a separate link click",
        "technical_complexity": "medium",
        "estimated_build_time": "6–8 weeks",
        "monetization_ideas": "1. Freemium with premium background video library and custom branding removed on paid tiers\n2. Team plans for sales organizations requiring shared scheduling, centralized analytics, and brand consistency\n3. White-label OEM licensing for CRM or sales tools that want to embed branded scheduling natively",
        "red_flags": "1. Calendly's dominant distribution and brand recognition makes customer acquisition expensive and slow in this category\n2. Video backgrounds are a UX novelty that may not sustain long-term retention without deeper workflow value\n3. Relatively small addressable market among users who truly prioritize scheduling aesthetics and conversion",
        "recommended_approach": "Validate with a tight niche—high-ticket coaches, consultants, or online course creators—who already invest in branded experiences and would pay for a scheduling page that reflects their personal brand. Build the core booking and video background MVP in 6 to 8 weeks, then grow organically through integrations with popular creator tools such as ConvertKit and Kajabi before expanding to enterprise sales teams.",
        "key_insights": "Differentiation through visual aesthetics is weak as a moat unless paired with conversion rate analytics that prove the branded booking experience produces measurable pipeline uplift.",
        "analyzed_at": NOW,
    },
    {
        "product_id": 1160486,
        "product_name": "Astra Autonomous Pentest",
        "product_url": "https://www.producthunt.com/posts/astra-security",
        "category": "Cybersecurity / AI Security Testing",
        "value_proposition": "AI-powered autonomous penetration testing agents that continuously find, validate, and remediate vulnerabilities across web, API, and cloud environments without manual triage, shrinking exposure windows from months to hours.",
        "target_audience": "Security teams at mid-market and enterprise companies, DevSecOps engineers, and compliance-driven organizations requiring continuous assurance",
        "pain_points": "1. Annual manual pentests leave months-long windows of unknown vulnerability exposure between assessments\n2. Skilled penetration testers are scarce and expensive, creating persistent security capacity gaps\n3. Traditional scanners produce massive noisy reports that overwhelm remediation teams with false positives",
        "improvement_opportunities": "1. Continuous testing cadence synchronized with CI/CD pipelines to assess every code push automatically\n2. Auto-generated developer-ready remediation pull requests instead of static vulnerability reports\n3. Risk-ranked finding prioritization using business context such as asset criticality and data classification",
        "feature_gaps": "1. Physical security and IoT device testing coverage beyond software application surfaces\n2. Adversarial red team simulation scenarios including social engineering and phishing vectors\n3. Executive-level risk dashboards that translate technical findings into measurable business risk metrics",
        "competitors": "1. Pentera (automated pentesting platform)\n2. Cobalt (PTaaS with human-AI hybrid)\n3. HackerOne (managed bug bounty and pentesting)",
        "market_viability_score": 8,
        "opportunity_score": 8,
        "differentiation_strategies": "1. Target compliance-driven mid-market companies (SOC 2, PCI-DSS, ISO 27001) where continuous testing is a mandate with defined budget\n2. Integrate natively into CI/CD pipelines so security testing becomes a standard development workflow event rather than a periodic audit\n3. Offer remediation-as-a-service where AI agents not only identify vulnerabilities but automatically open validated fix pull requests",
        "technical_complexity": "high",
        "estimated_build_time": "20–26 weeks",
        "monetization_ideas": "1. Annual subscription priced per number of assets or applications tested continuously\n2. Compliance reporting add-on that auto-generates audit evidence packages for SOC 2 or PCI-DSS reviews\n3. Managed pentest service pairing AI autonomous agents with human expert escalation for critical or complex findings",
        "red_flags": "1. False positives in autonomous security testing can cause production incidents if auto-remediation misfires without human review\n2. Regulatory liability exposure if an autonomous pentest tool inadvertently causes service disruption in a production environment\n3. Enterprise security sales cycles are long (6 to 18 months) and require established trust, credentials, and relationships",
        "recommended_approach": "Lead with compliance automation—specifically continuous SOC 2 evidence collection and validated vulnerability triage—as the entry wedge, since buyers have a defined budget and clear ROI model. Build an agent runtime that chains mature open-source tools such as Nuclei and Nmap with an LLM reasoning layer for validation and prioritization, then add auto-remediation as a premium feature once the core testing loop has established trust and accuracy.",
        "key_insights": "The highest-value moat in autonomous pentesting is validated findings with near-zero false positives, because security teams will pay a significant premium to eliminate triage overhead rather than simply receive more vulnerability data.",
        "analyzed_at": NOW,
    },
    {
        "product_id": 1162731,
        "product_name": "Basedash Semantic Layer",
        "product_url": "https://www.producthunt.com/posts/basedash",
        "category": "Business Intelligence / Data Analytics Infrastructure",
        "value_proposition": "A centralized semantic layer that lets data teams define business metrics once and expose consistent, governed definitions across every BI tool, dashboard, and AI query interface without duplication or drift.",
        "target_audience": "Data engineers, analytics engineers, and BI leads at growth-stage and enterprise companies running multiple reporting tools with inconsistent metric definitions",
        "pain_points": "1. Metric definitions diverge across tools—Tableau shows one number, Looker another—causing stakeholder distrust and analysis paralysis\n2. Re-defining the same KPIs in every new tool wastes engineering time and introduces subtle calculation errors\n3. Onboarding new analysts requires extensive tribal knowledge about undocumented metric logic buried in SQL",
        "improvement_opportunities": "1. AI-powered metric discovery that automatically suggests standard metrics from existing SQL queries and dbt models\n2. Lineage tracking that visually shows how each metric depends on upstream data transformations and source tables\n3. Automated alerting when metric definitions drift from the canonical source after a schema change or model update",
        "feature_gaps": "1. Self-serve metric creation interface for non-technical business users who cannot write SQL\n2. Metric governance workflows with approval chains and change history for modifications to critical KPIs\n3. Native real-time streaming metric support alongside traditional batch-computed metrics",
        "competitors": "1. dbt Semantic Layer (open-source ecosystem leader)\n2. Looker/Google (LookML semantic layer deeply embedded in GCP)\n3. Cube (headless BI and semantic layer API)",
        "market_viability_score": 7,
        "opportunity_score": 7,
        "differentiation_strategies": "1. Target dbt shop migrations aggressively with a one-click conversion tool that translates dbt metrics to Basedash format in minutes\n2. Build a natural language query interface on top of the semantic layer so non-technical users get metric-consistent answers without BI training\n3. Position as the AI-ready semantic layer where LLM queries are grounded in business-defined governed metrics via MCP or API",
        "technical_complexity": "medium",
        "estimated_build_time": "10–14 weeks",
        "monetization_ideas": "1. Per-seat SaaS pricing for data team users with a generous free tier for small teams to drive bottom-up adoption\n2. Connector marketplace with revenue sharing for BI tool and data source integrations built by partners\n3. Enterprise tier with RBAC, audit logs, SSO, and dedicated support for metric governance at scale",
        "red_flags": "1. dbt's semantic layer is free and deeply embedded in the modern data stack, making displacement difficult for entrenched dbt users\n2. Long enterprise sales cycles in data infrastructure require strong engineering credibility and proof-of-concept investment\n3. Connector maintenance across many BI tools and data sources creates ongoing engineering overhead that scales poorly",
        "recommended_approach": "Differentiate by building the most powerful AI query experience on top of the semantic layer—enabling any employee to ask business questions in plain English and receive answers backed by IT-governed metric definitions. Win early adopters from dbt shops frustrated by the complexity of the dbt Semantic Layer, offer a painless migration tool, then expand the connector ecosystem to expose metrics through Slack, Notion, and AI agents via MCP.",
        "key_insights": "The semantic layer category is commoditizing at the metric definition layer, so the sustainable competitive advantage lies in the AI query surface that makes governed metrics accessible to every employee—not just data teams.",
        "analyzed_at": NOW,
    },
    {
        "product_id": 1162181,
        "product_name": "Composer",
        "product_url": "https://www.producthunt.com/posts/composer-3",
        "category": "Collaborative Productivity / AI Document Tools",
        "value_proposition": "A multiplayer markdown editor built for human-agent collaboration, where AI agents can read, write, and update living documents in real time alongside human teammates—turning AI output from ephemeral chat into persistent shared knowledge.",
        "target_audience": "Software development teams, product managers, and technical writers already using AI coding or research agents in their daily workflows",
        "pain_points": "1. AI agent outputs generated in chat threads are immediately disconnected from team documents and lost to institutional memory\n2. Existing markdown editors were not designed for asynchronous or real-time AI agent contribution alongside humans\n3. Teams lack a shared context layer where both humans and AI agents can read and act on the same living information",
        "improvement_opportunities": "1. Structured agent contribution logs so humans can review, accept, reject, or revert specific agent edits with clear attribution\n2. Doc-level agent assignment where designated agents are responsible for autonomously keeping specific sections current\n3. Granular permission controls that limit which agents can edit which sections of a sensitive document",
        "feature_gaps": "1. Native GitHub integration so AI agents can sync documentation changes automatically with related code changes\n2. Meaningful diff views that distinguish AI-generated edits from human edits in version history\n3. Public read-only access for external stakeholders without requiring a Composer account",
        "competitors": "1. Notion (dominant collaborative knowledge base and document platform)\n2. Obsidian (markdown-native editor with a large plugin ecosystem)\n3. Coda (programmatic docs combining databases and documents)",
        "market_viability_score": 7,
        "opportunity_score": 7,
        "differentiation_strategies": "1. Position as the canonical shared memory layer for AI coding agents (Claude Code, Cursor) where specs, decisions, and progress notes live persistently\n2. Build a native GitHub integration so pull requests automatically update the relevant Composer spec document—closing the code-to-docs loop\n3. Offer an MCP server that exposes all Composer docs as structured context to any MCP-compatible AI agent, making it the team knowledge graph",
        "technical_complexity": "medium",
        "estimated_build_time": "8–12 weeks",
        "monetization_ideas": "1. Per-seat subscription with a free tier for individual developers to drive organic adoption\n2. Team workspaces with advanced agent permissions, unlimited version history, and collaboration analytics\n3. API access tier for developers building custom agent pipelines that need to read from and write to Composer documents",
        "red_flags": "1. Notion and Coda have enormous distribution advantages and are rapidly adding AI features that will reduce differentiation over time\n2. Markdown-native positioning limits initial appeal to non-technical users and restricts the total addressable market\n3. Agent-native collaboration is a new and unfamiliar workflow that requires meaningful user behavior change to adopt",
        "recommended_approach": "Launch initially to developer teams already using AI coding agents and position Composer as the shared workspace where Claude Code or Cursor agents write specs, architectural decisions, and progress notes in real time. Distribute through a Cursor extension and Claude Code MCP integration as the primary acquisition channel, then grow into product managers and team leads who want visibility into AI-assisted development workflows without needing to read code diffs.",
        "key_insights": "The winning strategy is to become the standard shared context and memory layer between AI coding agents and human developers—owning the spec-to-ship documentation workflow before document incumbents can replicate the agent-first collaboration experience.",
        "analyzed_at": NOW,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6A – Append to analysis_history.csv
# ─────────────────────────────────────────────────────────────────────────────
history_path = os.path.join(BASE, "analysis_history.csv")
HISTORY_HEADERS = [
    "product_id","product_name","product_url","category","value_proposition",
    "target_audience","pain_points","improvement_opportunities","feature_gaps",
    "competitors","market_viability_score","opportunity_score",
    "differentiation_strategies","technical_complexity","estimated_build_time",
    "monetization_ideas","red_flags","recommended_approach","key_insights","analyzed_at",
]

with open(history_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=HISTORY_HEADERS)
    for a in ANALYSES:
        writer.writerow(a)
        print(f"Wrote analysis: {a['product_name']}")

print(f"\nSTEP 6A: {len(ANALYSES)} analyses appended to analysis_history.csv")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6C – Update analyzed_ids.csv (all 8: pass + fail)
# ─────────────────────────────────────────────────────────────────────────────
new_ids_to_mark = [p["id"] for p in to_analyze if str(p["id"]) not in existing_analyzed_ids]

with open(analyzed_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    for pid in new_ids_to_mark:
        # Match existing format: id followed by 19 empty columns
        writer.writerow([str(pid)] + [""] * 19)
        print(f"Marked as analyzed: {pid}")

print(f"\nSTEP 6C: {len(new_ids_to_mark)} product IDs marked in analyzed_ids.csv")
print("\nDone. Ready to commit.")
