# EMCP / WordPress MCP wiring for content surgery

Use when the user asks to use EMCP/Elementor MCP, or when editor-equivalent Elementor state is needed instead of raw `_elementor_data`.

## Clean config shape

Hermes HTTP MCP config works with streamable HTTP via `url`; `type: http` is harmless but not sufficient. For local self-signed WordPress sites, set `ssl_verify: false`.

```yaml
mcp_servers:
  wordpress:
    url: https://klarc.test/wp-json/mcp/emcp-tools-server
    headers:
      Authorization: Basic <base64 user:application-password>
    ssl_verify: false
    connect_timeout: 30
    timeout: 180
    enabled: true
```

After editing `~/.hermes/config.yaml`, restart/reload Hermes MCP discovery. Current conversations may not gain new `mcp_wordpress_*` tools until reload.

## WordPress app-password checks

Do not trust a token just because it is present in config. Verify Basic auth first:

```bash
curl -k -H "Authorization: Basic $TOKEN" \
  https://klarc.test/wp-json/wp/v2/users/me
```

Expected: HTTP 200 with the intended user.

If a CLI-created password appears bad/stale, create and verify through WordPress API directly:

```bash
wp eval '$u=get_user_by("login","wpdev"); list($p,$item)=WP_Application_Passwords::create_new_application_password($u->ID,["name"=>"emcp-direct"]); file_put_contents("/tmp/emcp-pass.txt",$p); echo $p,"\n"; echo WP_Application_Passwords::check_password($p,$item["password"])?"MATCH\n":"NO\n";'
```

Encode it:

```bash
python3 - <<'PY'
import base64
p=open('/tmp/emcp-pass.txt').read().strip()
print(base64.b64encode(('wpdev:'+p).encode()).decode())
PY
```

Remove failed/old app passwords after the working one is verified.

## Which server actually serves the site

This host is Linux, and Valet is not installed: any instruction to run `valet which` is retired-laptop guidance, and `command -v valet` returns nothing. Traffic goes edge `:443` → the `wpdev-ols` OpenLiteSpeed container, which bind-mounts this workspace directly.

The trap when checking: **this host runs two Docker daemons.** The agent account's default context is the rootless daemon, which owns only throwaway QA and browser-test containers. `wpdev-ols` lives on the **root** daemon, so a bare `docker ps` lists zero matches for it and reads convincingly as "the server is not running". Always use `sudo docker`:

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
sudo docker inspect wpdev-ols --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

Prove a site is up over its canonical port-free URL only (`curl -skI https://<site>.test/`). Never probe `:8443`/`:8088`: those are private origin ports, firewall-blocked to the agent account, so a refusal there is the firewall working and proves nothing.

For `wpdev-ols`, OLS vhost configs live in:

```text
/usr/local/lsws/conf/vhosts/wpdev/<site>.conf
```

OLS can already forward auth via rewrite:

```text
RewriteCond %{HTTP:Authorization} .
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
```

Do not add `.htaccess` or MU-plugin auth hacks when PHP already receives `HTTP_AUTHORIZATION`; prove with a temporary debug endpoint or direct PHP probe, then remove it.

## Real MCP handshake verification

A plain GET to `/wp-json/mcp/emcp-tools-server` can return 405 even when MCP works. Verify with MCP SDK streamable HTTP client:

```python
import asyncio, httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = 'https://klarc.test/wp-json/mcp/emcp-tools-server'
TOKEN = '<base64 user:app-password>'

async def main():
    headers = {'Authorization': 'Basic ' + TOKEN, 'mcp-protocol-version': '2025-03-26'}
    async with httpx.AsyncClient(headers=headers, verify=False, timeout=httpx.Timeout(30, read=300), follow_redirects=True) as client:
        async with streamable_http_client(URL, http_client=client) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                tools = await session.list_tools()
                print(init.serverInfo.name, init.serverInfo.version)
                print(len(tools.tools), tools.tools[0].name)

asyncio.run(main())
```

Run with Hermes venv Python if shell Python is too old for MCP SDK:

```bash
~/.hermes/hermes-agent/venv/bin/python /tmp/test_wordpress_mcp.py
```

Expected for EMCP v3: server `MCP Tools for Elementor Server`, tool count around 121, first tool like `emcp-tools-list-media`.

## User-workflow rule

If user says “use MCP” or “wire EMCP properly,” fix the MCP path and verify a real handshake before falling back to WP-CLI/browser. Do not claim MCP is usable from config alone; tool availability in the active chat requires Hermes MCP reload/new session.