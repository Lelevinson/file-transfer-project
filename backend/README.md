# Demo backend

A small Flask server that stands in for the future hospital server. The
desktop app (`file_transfer/`) no longer copies files into a local target
folder -- it uploads them here over HTTP. This folder is deliberately a
separate program from the desktop app: in production the two run on
different machines, and the only bridge between them is HTTP. No code in
`backend/` may import from `file_transfer/`, and vice versa.

## How to run the demo

Two terminals, both from the project root:

```
# terminal 1 -- the server
.venv\Scripts\python backend\app.py

# terminal 2 -- the desktop app
.venv\Scripts\python -m file_transfer
```

Then upload files from the tray as usual. Results land in three places:

| Place | What you see |
|---|---|
| `backend/uploads/<user>/<category>/` | the file bytes |
| `demo.db`, table `files` | one metadata row per received file |
| `fail/` (client side) | files that failed validation (never sent) |

`demo.db` and `uploads/` are generated data and gitignored.

## The full flow

```
tray upload -> source/<user>/<category>/ -> watchdog event
    -> policy checks (extension, size, magic bytes, filename)
         -> invalid: moved to fail/, error popup, never sent
         -> valid:   POST /upload  (file + user_id + category + SHA-256)
                         -> server: user registered? hash matches?
                              -> 201: client deletes its local copy
                              -> 404/400: client reports failure
```

The folder path used to carry the metadata (which user, which category).
Over HTTP the path stays behind, so that information now travels
explicitly as form fields next to the file -- together with the file's
SHA-256 hash, so the server can prove the bytes arrived intact.

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/users` | list registered users (the desktop app calls this at startup to fill the User ID dropdown) |
| POST | `/users` | add or replace a user (demo/admin convenience) |
| POST | `/upload` | receive one file + metadata + hash from the desktop app |
| GET | `/test/<name>/<age>` | template rendering exercise, unrelated to the app |

`POST /upload` answers with:

| Status | Meaning | What the client does |
|---|---|---|
| 201 | stored, hash verified | deletes its local copy (the "move" is complete) |
| 404 | user not registered | treats it like the old missing target folder: popup + cleanup |
| 400 | hash mismatch (corrupted in transit) | transfer fails, file stays in source |
| (no answer) | server unreachable | transfer fails gracefully, file stays in source and is retried by the next event |

## Storage: disk for bytes, database for facts

SQLite *could* store the file bytes themselves (BLOB columns exist), but
the standard design keeps the two concerns apart:

- **`uploads/`** holds the actual files, mirroring the same
  `<user>/<category>/` layout the client uses. Name collisions get the
  same `report.pdf -> report_1.pdf` treatment as on the client.
- **`demo.db`** holds one row per file in the `files` table: user,
  category, filename, hash, size, upload time. This is what lets you
  answer questions like "what did user X send last week?" with one query
  instead of crawling folders.

The `users` table is seeded with the three demo users at startup
(`INSERT OR IGNORE`, so restarts change nothing).

## What changed in the desktop app for this integration

| File | Change | Why |
|---|---|---|
| `core/file_sender.py` | **new** -- posts each file with metadata + hash, deletes the local copy only after the server confirms | HTTP twin of `file_mover.py`: same "deliver and verify, or raise" contract, different transport |
| `core/transfer_service.py` | `process_folder` calls `Sender` instead of `Transfer`; dropped the `target_root` parameter | the target folder is now the server's business |
| `watch/watcher.py` | no longer carries `target_root` | same reason; everything else (fail folder, popups, batching) unchanged |
| `__main__.py` | fetches the user list from `GET /users` at startup (config list as fallback); the DEMO-ONLY target-folder registration loop is gone | the server now owns the user list, which was the plan all along |
| `config.py` / `config.json` | `target_root` removed, `server_url` added | pointing the app at a real server later = changing this one URL |

Two deliberate compatibility tricks kept the rest of the app untouched:

1. When the server answers 404 (unknown user), `file_sender` raises
   `FileNotFoundError` -- the same exception the old code raised for a
   missing target folder. The watcher's non-registered-user handling
   (popup + source cleanup) therefore works without modification.
2. `requests`' network errors inherit from `OSError`, which
   `process_folder` already caught. Only one new branch was added, so the
   log can say "backend server not reachable" instead of a raw traceback.

## Left for later

- `GET /files` status page (render the `files` table as HTML with a
  template) -- a nice demo touch and a template exercise with real data.
- Refreshing the user list while the app runs (it is fetched once at
  startup).
- Real-server concerns: authentication, HTTPS, category validation on
  the server side. All of it lands in this folder; the desktop app
  should not need to change.
