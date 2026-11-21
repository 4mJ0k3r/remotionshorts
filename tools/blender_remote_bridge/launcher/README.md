# Blender Bridge Launcher

Double-click **Start Blender Bridge.vbs** in the parent folder. Click **Start bridge** when you are ready to begin a new session.

The launcher opens Blender with its worker, starts an authenticated local server, starts Cloudflare Tunnel, and checks the public connection. **Copy agent prompt** becomes available after the public address responds with this session's identity.

The existing manually started bridge remains independent. If its server, Blender or tunnel is still running, the launcher displays an existing-session message and refuses to start a competing session. It never adopts or stops processes started outside the launcher.

## First session after your current animation finishes

1. Let the current agent finish. Save its Blender project and retrieve its deliverables.
2. Stop the old Python server and tunnel in their existing terminal windows, then close Blender after saving.
3. Open **Start Blender Bridge.vbs** and click **Start bridge**.
4. Wait for **Connected — Blender is ready**.
5. Click **Copy access token** and paste it into `BLENDER_BRIDGE_TOKEN` in the web agent's server-side secrets. The launcher creates its own persistent token. It does not retrieve the token from the current manually started server.
6. Set `BLENDER_BRIDGE_URL` to the connection address shown in the launcher.
7. Click **Copy agent prompt**, send it to the agent, then send your animation brief.

Blender and the launcher must stay open. Closing an active launcher window minimizes it. **Stop bridge** stops only its own server and tunnel and asks its worker to retire when idle. Blender remains open for saving. The launcher refuses this stop action while it sees a running job. Finish the job and save/close Blender before beginning the next fresh session.

## Permanent address

Temporary mode works without a Cloudflare account, but receives a new URL on each launch. It copies that URL into the agent prompt. Update the agent's URL secret each time temporary mode starts.

For the same address and prompt every time, complete this one-time Cloudflare setup:

1. Use a domain managed in your Cloudflare account.
2. Create a remotely managed Cloudflare Tunnel in the Cloudflare dashboard.
3. Configure a public hostname, for example `blender.yourdomain.com`, with the local HTTP service `http://127.0.0.1:8765`.
4. In launcher **Settings**, select **Permanent Cloudflare hostname**. Enter the HTTPS hostname and paste that tunnel's connector token into the masked field. Paste only the token value, not the complete installation command.
5. Save settings. The launcher uses the connector token through the child process environment, without putting it in command-line arguments.
6. Set the web agent's URL secret to the permanent HTTPS hostname once. Its bridge access token remains the same across launcher sessions.

The Cloudflare connector token and the bridge access token are different secrets. The web agent needs only the bridge access token. Interactive Cloudflare login protection in front of the public hostname can prevent programmatic agent requests unless the agent is also configured for that authentication scheme.

Official references:

- https://developers.cloudflare.com/tunnel/get-started/
- https://developers.cloudflare.com/tunnel/reference/run-parameters/

## Files and recovery

- `config.json` holds local paths, tunnel mode and public hostname.
- `.private/*.bin` contains credentials encrypted with Windows DPAPI for the current Windows user. The launcher lock is also local to this directory.
- `sessions/<session-id>/jobs/` contains request and result records for that launch. A new launch uses a new queue so interrupted requests are not replayed automatically. Records can contain private code and paths. The directories are excluded from Git by the launcher's `.gitignore`.
- `sessions/<session-id>/*.log` contains process logs. Treat these as private. Credentials are not intentionally logged by the launcher.
- The existing `../exports/` folder remains the download location.
- A crash may leave a job marked running. The launcher never retries that job automatically. Inspect the saved job record and Blender scene before continuing.
- If Blender's executable alias fails to forward `--python`, select the installed Blender executable in **Settings**. A conventional Blender installation can be selected if the Microsoft Store package rejects direct execution.

This bridge grants the agent full Blender Python execution under your Windows account. The download endpoint restricts exported paths, but Python execution has your account's broader permissions. Use it only with an agent you trust.

## Validation performed while an existing production was active

Python syntax checks, Windows credential-encryption round trips, operating-system conflict detection, and isolated API/worker tests run without connecting to the current server, sending it a job, or operating its Blender. Real Blender startup and public tunnel startup are intentionally deferred until the current production finishes. There is no account login, permanent hostname or tunnel credential configured by these files.
