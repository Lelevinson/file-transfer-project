# File Transfer App

Copies files from category subfolders under a **source root** to matching
category subfolders under a **target root**. Runs in the background, watches for
new files with `watchdog`, and offers a system-tray GUI for manual uploads.

## Run it

From this project folder (the folder that *contains* `file_transfer/`):

```
python -m file_transfer
```

`python -m file_transfer` runs the package's `__main__.py` (the entry point).

## Project structure

```
file-transfer-project/         <- project root (config, README, requirements)
├── file_transfer/             <- the app package (all the code lives here)
│   ├── __init__.py            <- marks this folder as a package
│   ├── __main__.py            <- ENTRY POINT: starts watcher + tray, handles shutdown
│   ├── config.py              <- settings: source/target roots, category list
│   ├── utils.py               <- tiny shared helpers
│   ├── core/                  <- LOGIC: does the real work, knows nothing about GUI/watchdog
│   │   ├── source_reader.py   <- validate source folder, list its files
│   │   ├── file_ops.py        <- low-level file work: hash, move, verify
│   │   └── transfer_service.py<- ties reader + file_ops together: "transfer one category"
│   ├── watch/                 <- INPUT: watchdog observer + event handler
│   │   └── watcher.py         <- on new file -> call transfer_service
│   └── ui/                    <- INPUT: system tray GUI
│       └── tray.py            <- menu, file picker, "copy into source category"
├── logs/                      <- runtime logs (app.log is git-ignored)
├── requirements.txt
└── README.md
```

## How to think about the folders

- **core/** = the brain. Pure logic. It should never import from `ui/` or `watch/`.
- **watch/** and **ui/** = the two ways work gets *triggered* (a new file appears,
  or a user clicks the tray). Both just call into `core/`.
- **__main__.py** = wiring. Starts everything and connects the pieces.

Rule of thumb: an arrow of dependency should point *toward* `core/`, never out of it.
