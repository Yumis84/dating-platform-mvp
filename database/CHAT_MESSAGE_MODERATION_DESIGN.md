# Chat Message Moderation Design

Purpose
-------
This document describes the design and rationale for AI‑assisted moderation of chat messages in the Dating Platform MVP. The goal is to detect harmful, abusive, or policy‑violating content early, reduce user harm, and provide a clear escalation path for human moderators while preserving user privacy.

Why moderate chat messages
--------------------------
- Chats are the primary communication channel where abuse, fraud, extortion, harassment and policy violations occur.
- Live messaging can cause immediate harm; automated detection helps reduce exposure and surface high‑risk cases to moderators quickly.
- Moderation of messages differs from profile moderation: profiles are persistent public artifacts (images, text) reviewed once or periodically; messages are transient, high‑volume, and often conversational, requiring different tradeoffs for latency and accuracy.

Categories of violations to detect
---------------------------------
- Fraud / Scams: attempts to deceive users into sending money or giving up credentials.
- Extortion / Solicitation for money: explicit requests for payment or transfer.
- Aggression / Threats: threats of violence, harassment, severe insults.
- Spam / Mass messaging: unsolicited promotional content, phishing links.
- Prohibited content: illegal content, explicit materials violating policy.
- Attempts to move conversation off‑platform: requests to share phone numbers, emails, or direct contact where policy prohibits immediate disclosure.

Design choices
--------------
- Pre‑moderation (sync): Evaluate message before delivery. Pros: prevents immediate harm. Cons: adds latency to message delivery and may increase user friction or false positives. Use when a user or content pattern is high‑risk (new users, flagged accounts) or when message contains media/links.
- Post‑moderation (async): Deliver quickly, evaluate after sending, and take remediation if needed (hide message, notify moderator, block user). Pros: low latency. Cons: potential brief exposure to harmful content.
- Hybrid: Apply lightweight checks synchronously (spam heuristics, link detection) and full AI model asynchronously. Expand pre‑moderation for users with elevated risk score.

Verdicts and actions
--------------------
- APPROVED: allow delivery (or move to delivery queue if pre‑check passes).
- BLOCKED: do not deliver; create chat_report and alert moderators; consider immediate block of sender depending on severity.
- REVIEW: send to human moderators with context; hold delivery until manual review if policy requires.

Privacy and data minimization
----------------------------
- Store only references (message_id) and minimal metadata in the moderation queue. Avoid storing Telegram IDs, email or phone numbers in moderation records.
- Keep model outputs (flags, scores) in JSONB for audit and explainability, with retention policies.

Integration points
------------------
- n8n WF_12 will accept message_id and orchestrate AI calls and outcome routing.
- If APPROVED → insert into message_delivery_queue (as PENDING) so the delivery worker handles sending.
- If BLOCKED → create chat_reports + audit_event and possibly set chat_sessions.status = 'BLOCKED' depending on severity.
- If REVIEW → send notification to moderators (Telegram/Admin UI) with last N messages context.

Evaluation and thresholds
-------------------------
- Define score thresholds per violation category for BLOCKED / REVIEW / APPROVED; tune in staging using human review feedback.
- Maintain a feedback loop: human moderator decisions update model calibration and rules.

Operational considerations
--------------------------
- Monitor moderation queue depth, false positive rates and moderator throughput.
- Consider rate limiting moderation API calls to control costs for large volumes.
- Retain moderation events as audit trail; implement retention/archival policy.
