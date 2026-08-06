n8n Workflows

Workflow naming convention
--------------------------
Use the WF_ prefix and a two-digit stage number and a short descriptive name:

WF_01_ - registration
WF_02_ - role selection
WF_03_ - profile creation

Examples:
- WF_01_USER_REGISTRATION
- WF_02_ROLE_SELECTION

Notes:
- Exported workflows should NOT include real credentials. Replace credentials references with placeholders or leave blank and document required credentials in the workflow documentation.
- Store workflow exports in n8n/workflows/ and organize by feature (e.g., n8n/workflows/registration/).
