"""
Spark MCP Server — local stdio MCP server for Claude Code.
Dispatches commands to the DGX Spark via SSH and exposes tools for:
  - FalkorDB queries (raptor_knowledge_base + raptor_flowcharts)
  - Nemotron LLM prompts (classification, analysis, tagging)
  - Running scripts on the Spark
  - Checking job status
"""

import asyncio
import json
import shlex
import subprocess
import os
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# EverMemOS config — uses Tailscale IP (UFW blocks LAN on :1995)
EVERMEMOS_URL = "http://100.114.179.3:1995/api/v1"
EVERMEMOS_USER = "claude-code"
EVERMEMOS_GROUP = "coven"

SSH_KEY = os.environ.get(
    "SPARK_SSH_KEY",
    r"C:\Users\ELF\AppData\Local\NVIDIA Corporation\Sync\config\nvsync.key",
)
SSH_HOST = os.environ.get("SPARK_SSH_HOST", "luna@10.255.233.161")
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
NEMOTRON_URL = "http://localhost:30002/v1"
NEMOTRON_MODEL = "nemotron-3-nano-30b"
FALKORDB_HOST = "falkordb"
FALKORDB_PORT = "6379"

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "agents", "catalog.json")
TRACKING_BASE = "/home/luna/Raptor_Dynamics/tracking"
LINEAR_UPDATES_DIR = os.path.join(os.path.dirname(__file__), "linear_updates")

server = Server("spark-tools")


def _ssh_run(cmd: str, timeout: int = 120) -> str:
    """Run a command on the Spark via SSH."""
    full_cmd = ["ssh", "-i", SSH_KEY] + SSH_OPTS + [SSH_HOST, cmd]
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR: " + result.stderr
        return output[:50000]
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after {}s".format(timeout)
    except Exception as e:
        return "ERROR: {}".format(e)


def _docker_python(script: str, timeout: int = 120) -> str:
    """Run a Python script inside the arthur_chatbot container."""
    # Write script to a temp file on the host, then docker exec it
    escaped = script.replace("'", "'\"'\"'")
    cmd = (
        "cat > /tmp/_mcp_run.py << 'MCPEOF'\n"
        + script
        + "\nMCPEOF\n"
        + "cp /tmp/_mcp_run.py /home/luna/Raptor_Dynamics/Production/arthur_chatbot/_mcp_run.py && "
        + "docker exec arthur_chatbot python3 /app/backend/_mcp_run.py 2>&1 && "
        + "rm -f /home/luna/Raptor_Dynamics/Production/arthur_chatbot/_mcp_run.py"
    )
    return _ssh_run(cmd, timeout=timeout)


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_falkordb",
            description="Run a Cypher query against a FalkorDB graph on the Spark. Graphs: raptor_knowledge_base (4137 chunks), raptor_flowcharts (68 flowcharts). Returns result rows as JSON.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cypher": {
                        "type": "string",
                        "description": "Cypher query to execute",
                    },
                    "graph": {
                        "type": "string",
                        "description": "Graph name (default: raptor_knowledge_base)",
                        "default": "raptor_knowledge_base",
                    },
                },
                "required": ["cypher"],
            },
        ),
        Tool(
            name="nemotron_prompt",
            description="Send a prompt to Nemotron-3-Nano-30B on the Spark (port 30002). Use for classification, analysis, tagging tasks. Returns the LLM response text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to send to Nemotron",
                    },
                    "system": {
                        "type": "string",
                        "description": "Optional system prompt",
                        "default": "",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Max tokens in response (default 512)",
                        "default": 512,
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature (default 0.1 for classification)",
                        "default": 0.1,
                    },
                },
                "required": ["prompt"],
            },
        ),
        Tool(
            name="nemotron_batch_classify",
            description="Classify a batch of FalkorDB chunks using Nemotron. Reads chunks by ID range, classifies intent_category/problem_type/models, and updates FalkorDB. Returns classification results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "offset": {
                        "type": "integer",
                        "description": "Start offset (SKIP value for chunk query)",
                        "default": 0,
                    },
                    "batch_size": {
                        "type": "integer",
                        "description": "Number of chunks to classify (default 50)",
                        "default": 50,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, classify but don't update FalkorDB",
                        "default": False,
                    },
                    "fields": {
                        "type": "string",
                        "description": "Comma-separated fields to classify: intent_category,problem_type,models (default: all)",
                        "default": "intent_category,problem_type,models",
                    },
                },
            },
        ),
        Tool(
            name="spark_run_script",
            description="Run a named script on the Spark server. Scripts live in /home/luna/Raptor_Dynamics/Production/arthur_chatbot/. Can also run arbitrary shell commands.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command or script path to run on the Spark",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 120)",
                        "default": 120,
                    },
                    "in_container": {
                        "type": "boolean",
                        "description": "Run inside arthur_chatbot container (default false)",
                        "default": False,
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="spark_status",
            description="Get current status of the Spark server: docker containers, FalkorDB stats, Nemotron health.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="agent_list",
            description="List all available Nemotron agents from the catalog. Returns name, description, category, and typical usage for each agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category: knowledge_base, llm_tasks, quality_assurance, infrastructure, project_management (optional)",
                    }
                },
            },
        ),
        Tool(
            name="agent_run",
            description="Run a named agent from the catalog with its typical parameters. Convenience wrapper around the underlying tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "string",
                        "description": "Agent name from the catalog (use agent_list to see available agents)",
                    },
                    "params": {
                        "type": "object",
                        "description": "Override parameters (optional — uses agent's typical_params by default)",
                    },
                },
                "required": ["agent"],
            },
        ),
        Tool(
            name="linear_update",
            description="Generate and save a Linear project update based on current tracking files. Reads week tracking .md files from the server, generates a formatted update, and saves it locally. Use every 2-3 turns when significant progress is made.",
            inputSchema={
                "type": "object",
                "properties": {
                    "week": {
                        "type": "string",
                        "description": "Which week file to read: week1, week2, week3, week4 (default: week1)",
                        "default": "week1",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Optional summary of what was accomplished this session to include in the update",
                    },
                },
            },
        ),
        Tool(
            name="evermemos_remember",
            description="Store a memory in EverMemOS shared Coven memory. Messages are queued for async extraction. Use for session summaries, decisions, architecture notes, and cross-session context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember",
                    },
                    "sender": {
                        "type": "string",
                        "description": "Who is sending: claude-code, em, or openclaw-twin",
                        "default": "claude-code",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="evermemos_recall",
            description="Search EverMemOS for relevant memories. Returns matching memories from the Coven shared memory space.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Max results (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="evermemos_fetch",
            description="Fetch recent memories from EverMemOS. Good for session start context restoration. Returns chronological memory history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max items to return (default 10)",
                        "default": 10,
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Type: episodic_memory or profile (default episodic_memory)",
                        "default": "episodic_memory",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_falkordb":
        graph = arguments.get("graph", "raptor_knowledge_base")
        cypher = arguments["cypher"]
        script = """
import json
from falkordb import FalkorDB
db = FalkorDB(host="{host}", port={port})
g = db.select_graph("{graph}")
r = g.query(\"\"\"{cypher}\"\"\")
header = r.header if hasattr(r, 'header') else []
rows = []
for row in r.result_set:
    rows.append([str(v) if not isinstance(v, (int, float, bool, type(None))) else v for v in row])
print(json.dumps({{"header": header, "rows": rows, "count": len(rows)}}))
""".format(host=FALKORDB_HOST, port=FALKORDB_PORT, graph=graph, cypher=cypher.replace('"', '\\"'))
        result = _docker_python(script)
        return [TextContent(type="text", text=result)]

    elif name == "nemotron_prompt":
        prompt = arguments["prompt"].replace('"', '\\"').replace("'", "'")
        system = arguments.get("system", "").replace('"', '\\"').replace("'", "'")
        max_tokens = arguments.get("max_tokens", 512)
        temperature = arguments.get("temperature", 0.1)
        script = """
import json, requests
messages = []
system = \"\"\"{system}\"\"\"
if system.strip():
    messages.append({{"role": "system", "content": system}})
messages.append({{"role": "user", "content": \"\"\"{prompt}\"\"\"}})
r = requests.post(
    "{url}/chat/completions",
    json={{"model": "nemotron-3-nano-30b", "messages": messages, "max_tokens": {max_tokens}, "temperature": {temperature}}},
    timeout=120,
)
data = r.json()
text = data.get("choices", [{{}}])[0].get("message", {{}}).get("content", "ERROR: no response")
print(text)
""".format(
            url=NEMOTRON_URL,
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        result = _docker_python(script, timeout=180)
        return [TextContent(type="text", text=result)]

    elif name == "nemotron_batch_classify":
        offset = arguments.get("offset", 0)
        batch_size = arguments.get("batch_size", 50)
        dry_run = arguments.get("dry_run", False)
        fields = arguments.get("fields", "intent_category,problem_type,models")
        script = _build_classifier_script(offset, batch_size, dry_run, fields)
        result = _docker_python(script, timeout=600)
        return [TextContent(type="text", text=result)]

    elif name == "spark_run_script":
        command = arguments["command"]
        timeout = arguments.get("timeout", 120)
        in_container = arguments.get("in_container", False)
        if in_container:
            result = _ssh_run(
                'docker exec arthur_chatbot bash -c "{}"'.format(command.replace('"', '\\"')),
                timeout=timeout,
            )
        else:
            result = _ssh_run(command, timeout=timeout)
        return [TextContent(type="text", text=result)]

    elif name == "spark_status":
        status_parts = []
        status_parts.append("=== DOCKER ===\n" + _ssh_run('docker ps --format "table {{.Names}}\t{{.Status}}"', 15))
        status_parts.append(
            "\n=== NEMOTRON ===\n"
            + _ssh_run("curl -s --connect-timeout 3 http://localhost:30002/v1/models | python3 -m json.tool 2>/dev/null | head -5 || echo 'Nemotron unreachable'", 10)
        )
        status_parts.append(
            "\n=== FALKORDB GRAPHS ===\n"
            + _docker_python(
                'from falkordb import FalkorDB\n'
                'db = FalkorDB(host="falkordb", port=6379)\n'
                'for g in db.list_graphs():\n'
                '    gr = db.select_graph(g)\n'
                '    r = gr.query("MATCH (n) RETURN count(n) AS cnt")\n'
                '    print(f"  {g}: {r.result_set[0][0]} nodes")\n',
                15,
            )
        )
        return [TextContent(type="text", text="\n".join(status_parts))]

    elif name == "agent_list":
        try:
            with open(CATALOG_PATH) as f:
                catalog = json.load(f)
        except Exception as e:
            return [TextContent(type="text", text="ERROR loading catalog: {}".format(e))]
        category_filter = arguments.get("category", "").strip().lower()
        agents = catalog.get("agents", [])
        if category_filter:
            agents = [a for a in agents if a.get("category", "").lower() == category_filter]
        lines = ["# Nemotron Agent Catalog\n"]
        for a in agents:
            lines.append("## {} [{}]".format(a["name"], a.get("category", "")))
            lines.append("  " + a["description"])
            lines.append("  Tool: {}".format(a.get("tool", "")))
            if a.get("notes"):
                lines.append("  Notes: {}".format(a["notes"]))
            lines.append("")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "agent_run":
        agent_name = arguments["agent"]
        override_params = arguments.get("params", {})
        try:
            with open(CATALOG_PATH) as f:
                catalog = json.load(f)
        except Exception as e:
            return [TextContent(type="text", text="ERROR loading catalog: {}".format(e))]
        agent = next((a for a in catalog.get("agents", []) if a["name"] == agent_name), None)
        if not agent:
            names = [a["name"] for a in catalog.get("agents", [])]
            return [TextContent(type="text", text="Agent '{}' not found. Available: {}".format(agent_name, ", ".join(names)))]
        params = dict(agent.get("typical_params", {}))
        params.update(override_params)
        tool_name = agent["tool"]
        # Recursively call the underlying tool
        return await call_tool(tool_name, params)

    elif name == "linear_update":
        week = arguments.get("week", "week1")
        extra_summary = arguments.get("summary", "")
        week_file_map = {
            "week1": "week1_feb24-mar02.md",
            "week2": "week2_mar03-09.md",
            "week3": "week3_mar10-16.md",
            "week4": "week4_mar17-21.md",
        }
        week_file = week_file_map.get(week, "week1_feb24-mar02.md")
        # Read tracking files from server
        tracking_content = _ssh_run(
            "cat {base}/project_status.md {base}/{wf} 2>/dev/null".format(
                base=TRACKING_BASE, wf=week_file
            ),
            timeout=15,
        )
        if "No such file" in tracking_content or len(tracking_content.strip()) < 20:
            return [TextContent(type="text", text="ERROR: Could not read tracking files from server.\n" + tracking_content)]
        import datetime
        today = datetime.date.today().isoformat()
        os.makedirs(LINEAR_UPDATES_DIR, exist_ok=True)
        update_path = os.path.join(LINEAR_UPDATES_DIR, "{}.md".format(today))
        update_content = "# Linear Update — {}\n\n".format(today)
        update_content += "**Project**: Raptor Dynamics Chatbot (Ceres Air LLC)\n"
        update_content += "**Week**: {}\n\n".format(week.upper())
        if extra_summary:
            update_content += "## Session Summary\n{}\n\n".format(extra_summary)
        update_content += "## Tracking File Snapshot\n\n```\n{}\n```\n".format(tracking_content[:3000])
        with open(update_path, "w") as f:
            f.write(update_content)
        return [TextContent(type="text", text="Linear update saved to: {}\n\n{}".format(update_path, update_content[:1500]))]

    elif name == "evermemos_remember":
        import datetime
        import urllib.request
        content = arguments["content"]
        sender = arguments.get("sender", EVERMEMOS_USER)
        msg_id = "cc-{}".format(int(datetime.datetime.now().timestamp()))
        create_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000+00:00")
        payload = json.dumps({
            "message_id": msg_id,
            "create_time": create_time,
            "sender": sender,
            "sender_name": sender,
            "group_id": EVERMEMOS_GROUP,
            "content": content,
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                EVERMEMOS_URL + "/memories",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text="ERROR writing memory: {}".format(e))]

    elif name == "evermemos_recall":
        import urllib.request
        import urllib.parse
        query = arguments["query"]
        top_k = arguments.get("top_k", 5)
        params = urllib.parse.urlencode({
            "query": query,
            "user_id": EVERMEMOS_USER,
            "group_id": EVERMEMOS_GROUP,
            "top_k": top_k,
        })
        try:
            url = EVERMEMOS_URL + "/memories/search?" + params
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
            # Format output
            memories = result.get("result", {}).get("memories", [])
            pending = result.get("result", {}).get("pending_messages", [])
            lines = ["Found {} memories, {} pending".format(len(memories), len(pending))]
            for m in memories:
                lines.append("\n--- Memory ---")
                lines.append(json.dumps(m, indent=2)[:500])
            for p in pending:
                lines.append("\n--- Pending ---")
                lines.append("  sender: {}".format(p.get("sender", "?")))
                lines.append("  content: {}".format(p.get("content", "")[:200]))
                lines.append("  time: {}".format(p.get("message_create_time", "?")))
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:
            return [TextContent(type="text", text="ERROR searching memories: {}".format(e))]

    elif name == "evermemos_fetch":
        import urllib.request
        import urllib.parse
        limit = arguments.get("limit", 10)
        memory_type = arguments.get("memory_type", "episodic_memory")
        params = urllib.parse.urlencode({
            "user_id": EVERMEMOS_USER,
            "group_id": EVERMEMOS_GROUP,
            "limit": limit,
            "memory_type": memory_type,
        })
        try:
            url = EVERMEMOS_URL + "/memories?" + params
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
            return [TextContent(type="text", text=json.dumps(result, indent=2)[:5000])]
        except Exception as e:
            return [TextContent(type="text", text="ERROR fetching memories: {}".format(e))]

    return [TextContent(type="text", text="Unknown tool: {}".format(name))]


def _build_classifier_script(offset, batch_size, dry_run, fields):
    """Build the Python script that runs Nemotron classification on chunks."""
    return '''
import json, requests, time
from falkordb import FalkorDB

db = FalkorDB(host="falkordb", port=6379)
g = db.select_graph("raptor_knowledge_base")
NEMOTRON_URL = "http://10.255.233.161:30002/v1"
DRY_RUN = {dry_run}
FIELDS = "{fields}".split(",")

# Fetch batch of chunks
r = g.query(
    "MATCH (c:Chunk) RETURN c.id AS id, substring(c.content, 0, 1500) AS content, "
    "c.intent_category AS intent, c.problem_type AS ptype, c.models AS models, "
    "c.source_type AS stype, c.brand AS brand "
    "ORDER BY c.id SKIP {offset} LIMIT {batch_size}"
)

chunks = []
for row in r.result_set:
    chunks.append({{
        "id": row[0], "content": row[1], "intent": row[2],
        "ptype": row[3], "models": row[4], "stype": row[5], "brand": row[6],
    }})

print("Fetched {{}} chunks (offset={offset})".format(len(chunks)))
if not chunks:
    print("No chunks to classify")
    exit(0)

CLASSIFY_PROMPT = """You are a metadata classifier for an agricultural drone support knowledge base.
Given the following text chunk, classify it into these fields:

1. intent_category: EXACTLY one of: warranty, training, troubleshooting, parts, general
2. problem_type: If troubleshooting, specify the problem type (e.g., motor_failure, battery_issue, calibration_failed, connection_lost, gps_signal_lost, nozzle_offline, firmware_update_failed, flight_unstable, esc_offline, radar_offline, signal_weak, overheating, spray_uneven). Use empty string if not troubleshooting.
3. models: Comma-separated list of drone models mentioned (e.g., T40, P100, P150, HD580, V40). Use empty string if none mentioned.

IMPORTANT RULES:
- warranty = content about coverage, claims, warranty periods, what is/isn't covered, RMA
- training = how-to guides, setup instructions, calibration procedures, assembly, courses
- troubleshooting = diagnosing faults, fixing issues, error resolution
- parts = product listings, SKUs, prices, part specifications, replacement parts
- general = company info, news, events, or content that doesn't fit above categories
- If content is mostly [Music] or transcription noise, classify as general

Respond with ONLY a JSON object, no other text:
{{"intent_category": "...", "problem_type": "...", "models": "..."}}

TEXT:
{{content}}"""

results = []
errors = 0
updated = 0
start = time.time()

for i, chunk in enumerate(chunks):
    content_preview = chunk["content"][:1500]
    if len(content_preview.strip()) < 20:
        results.append({{"id": chunk["id"], "skip": "too_short"}})
        continue

    prompt = CLASSIFY_PROMPT.replace("{{content}}", content_preview)
    try:
        resp = requests.post(
            NEMOTRON_URL + "/chat/completions",
            json={{
                "model": "nemotron-3-nano-30b",
                "messages": [{{"role": "user", "content": prompt}}],
                "max_tokens": 150,
                "temperature": 0.05,
            }},
            timeout=60,
        )
        text = resp.json()["choices"][0]["message"]["content"].strip()
        # Parse JSON from response (handle markdown code blocks)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        classification = json.loads(text)
    except Exception as e:
        errors += 1
        results.append({{"id": chunk["id"], "error": str(e)[:100]}})
        continue

    new_intent = classification.get("intent_category", chunk["intent"])
    new_ptype = classification.get("problem_type", chunk["ptype"] or "")
    new_models = classification.get("models", chunk["models"] or "")

    changed = (
        new_intent != chunk["intent"]
        or (new_ptype and new_ptype != (chunk["ptype"] or ""))
        or (new_models and new_models != (chunk["models"] or ""))
    )

    result_entry = {{
        "id": chunk["id"],
        "old_intent": chunk["intent"],
        "new_intent": new_intent,
        "new_ptype": new_ptype,
        "new_models": new_models,
        "changed": changed,
    }}
    results.append(result_entry)

    if changed and not DRY_RUN:
        updates = []
        params = {{"cid": chunk["id"]}}
        if "intent_category" in FIELDS:
            updates.append("c.intent_category = $new_intent")
            params["new_intent"] = new_intent
        if "problem_type" in FIELDS and new_ptype:
            updates.append("c.problem_type = $new_ptype")
            params["new_ptype"] = new_ptype
        if "models" in FIELDS and new_models:
            updates.append("c.models = $new_models")
            params["new_models"] = new_models
        if updates:
            q = "MATCH (c:Chunk {{id: $cid}}) SET " + ", ".join(updates)
            g.query(q, params=params)
            updated += 1

    if (i + 1) % 10 == 0:
        elapsed = time.time() - start
        rate = (i + 1) / elapsed
        print("  Progress: {{}}/{{}}, rate: {{:.1f}} chunks/s".format(i + 1, len(chunks), rate))

elapsed = time.time() - start
changed_count = sum(1 for r in results if r.get("changed"))
print()
print("=== CLASSIFICATION COMPLETE ===")
print("  Chunks processed: {{}}".format(len(chunks)))
print("  Changed: {{}}".format(changed_count))
print("  Updated in DB: {{}}".format(updated))
print("  Errors: {{}}".format(errors))
print("  Time: {{:.1f}}s ({{:.1f}} chunks/s)".format(elapsed, len(chunks) / max(elapsed, 0.1)))
print("  Dry run: {{}}".format(DRY_RUN))

# Show intent distribution changes
intent_changes = {{}}
for r in results:
    if r.get("changed") and "old_intent" in r:
        key = "{{}} -> {{}}".format(r["old_intent"], r["new_intent"])
        intent_changes[key] = intent_changes.get(key, 0) + 1
if intent_changes:
    print("\\n=== INTENT RECLASSIFICATIONS ===")
    for k, v in sorted(intent_changes.items(), key=lambda x: -x[1]):
        print("  {{}}: {{}}".format(k, v))

# Print sample of changed chunks
changed_samples = [r for r in results if r.get("changed")][:10]
if changed_samples:
    print("\\n=== SAMPLE CHANGES ===")
    for s in changed_samples:
        print("  {{}} | {{}} -> {{}} | ptype={{}} | models={{}}".format(
            s["id"], s.get("old_intent",""), s.get("new_intent",""),
            s.get("new_ptype",""), s.get("new_models","")
        ))
'''.format(
        offset=offset,
        batch_size=batch_size,
        dry_run=dry_run,
        fields=fields,
    )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
