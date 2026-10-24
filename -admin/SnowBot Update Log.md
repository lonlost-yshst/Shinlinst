# SnowBot Update Log

This log is compiled based on a function/keyword comparison of `SnowBot old version.zip` (Beta and 1.1.x/1.2.x) with the 1.3.x series source code.

---

## ——— Snowball (Web Era) ———

### Snowball 1.1 - alpha
*(25 lines, Gradio Web UI)*

The first runnable prototype. Single-turn conversation only, fixed system prompt (aloof catgirl), no registration, no memory.

### Snowball 3.4.1-1 / 3.4.1-2 - beta
*(129 / 136 lines, Gradio Web)*

Official Web prototype:
- Added `chat_with_cat` (conversation function)
- Added `load_memories` / `save_memories` (memory persistence, files named with timestamps)
- Used `gr.Blocks` to build a multi-option Web UI
- No user registration, no model selection

### Snowball 3.4.2-1 / 3.4.2-2 - beta
*(149 / 149 lines, Gradio Web)*

- Added interactive features: `feed_fish`, `pat_head`
- Both essentially call `chat_with_cat` with preset prompts

### Snowball 3.4.3-1 - beta
*(168 lines, Gradio Web)*

- Added `_call_api` and `concurrent.futures`
- Introduced timeout protection (`timeout` keyword)

### Snowball 3.4.3-2 - beta
*(191 lines, Gradio Web)*

- Added `_submit_with_timeout` to encapsulate timeout call logic (multithreading via `ThreadPoolExecutor`)

### Snowball 3.4.3-3 / 3.4.3-4 - beta
*(191 / 187 lines, Gradio Web)*

Minor iterations, no core function changes.

### Snowball 3.5.1-1 / 3.5.1-2 - beta
*(196 / 204 lines, Gradio Web)*

- Removed `_next_memory_path` (memory path strategy adjusted)
- Slight code size increase

### Snowball 3.5.2-1 - beta
*(209 lines)*

- Abandoned Gradio Web, added `chat` / `main` functions
- Reverted to terminal (`input()`), but still no complete user system

---

## ——— Snowball → SnowBot (rc Transition) ———

### Snowball rc.1
*(291 lines, terminal)*

The first true SnowBot. Fully transitioned from Web to terminal:
- Added `register` / `login` / `hash_password` / SHA encryption
- Added `chat_loop` (chat loop)
- Added `load_users` / `save_users` (user persistence)
- Added `init_api` (API initialization)
- Added `get_memory_file` (organize memory files by username)

### SnowBot rc.2
*(336 lines, terminal)*

- Added `format_output` (formatted and beautified chat replies)
- Added UI helper functions: `print_header` / `print_menu` / `print_error` / `print_divider`, etc.
- Code structure began to clarify

### SnowBot rc.3
*(436 lines, terminal)*

- Added `check_internet` / `check_api_status` / `do_status` / `print_info`
- Code size continued to expand

---

## ——— Official Version 1.1.x ———

### SnowBot 1.1.1
*(893 lines, terminal, first official release)*

Integrated all rc features and greatly expanded:
- Added complete multilingual system (`CURRENT_LANG` + 7 language dictionaries): Simplified Chinese, Traditional Chinese, Classical Chinese (Simp/Trad), English, Japanese, French
- Added `build_system_prompt` (AI character system prompt construction)
- Added `collect_settings` (user setting collection: AI name, persona, form of address)
- Added `load_settings` / `save_settings` / `get_settings_file`
- Added `do_language` (language selection)
- Added `load_language` / `save_language` (language preference persistence)
- No `records_dir` — chat logs and settings were fixed under the user's current directory

### SnowBot 1.1.2
*(1010 lines)*

Major architectural adjustment — introduced `records_dir` system:
- Added `collect_records_dir` (custom record path upon registration)
- Added `collect_login_records_dir` (confirm path upon login)
- Added `create_records_dir` / `ensure_login_records_dir`
- Added `get_default_records_parent` / `get_user_records_dir`
- Added `validate_records_dir` (including `snowbot_write_test` write permission check)
- Added `safe_filename` (filename sanitization)
- Introduced `APPDATA\Roaming\SnowBot` as the default data location

### SnowBot 1.1.3
*(1090 lines)*

- Added `normalize_parent_path` (path normalization: environment variables, user directory, relative/absolute path handling)
- Added `read_chat_message` (unified chat input processing)

### SnowBot 1.1.4
*(1293 lines)*

- Introduced `concurrent.futures` + `ThreadPoolExecutor`
- Added `_submit_with_timeout` (90-second timeout protection)
- Added `API_TIMEOUT` constant
- Added `timeout_msg` / `api_maybe_available` translation keys

### SnowBot 1.1.5
*(1291 lines)*

Minor iteration, code size -2 (cleanup and tweaks).

---

## ——— Official Version 1.2.x ———

### SnowBot 1.2.1
*(1385 lines)*

- Added `collect_model` (AI model selection)
- Added `model_name` / `model_changed` / `model_not_set` / `choose_model` translation keys

### SnowBot 1.2.2
*(1390 lines)*

Minor iteration, code size +5.

### SnowBot 1.2.3
*(1345 lines)*

- Removed `check_internet` / `do_status` (network check feature removed)

### SnowBot 1.2.4
*(1370 lines)*

- Added ANSI terminal color support (`kernel32.SetConsoleMode` on Windows)

---

## ——— Official Version 1.3.x ———

### SnowBot 1.3.1
*(1427 lines)*

Major path architecture change:
- Data directory unified migration from `APPDATA` to `C:\Shinlinst\.files\SnowBot`
- Added `SNOWBOT_DATA_DIR` environment variable (can override default data directory)
- Added `migrate_legacy_data` (auto-migrate old `users.json` / `language.txt` from `APPDATA` on first run)
- No longer forcibly creates a `SnowBot` subfolder under user-specified paths; uses the specified path directly

### Sn 1.3.2
*(1504 lines)*

- Added `read_password` function: displays `*` mask during password input to protect privacy
- Only affects password input; API Key and chat messages remain in plaintext
- Project name changed from "Hanshuang SnowBot" to "Xuexing SnowBot"
- AI character name changed from "Hanshuang" to "Xuexing"
- Filename prefix changed from `SnowBot` to `Sn`

### Sn 1.3.3
*(1504 lines, code size unchanged)*

- Chat interface `User>` changed to display current logged-in username (e.g., `lonlost>`)
- `User` in chat history echo synchronized to username

### Sn 1.3.4
*(1678 lines, code size +174)*

Multilingual improvements:
- Traditional Chinese split into three independent languages: Traditional (Hong Kong), Traditional (Macau), Traditional (Taiwan)
- Regional vocabulary differentiated per local customs (e.g., user/account, internet, record, timeout/overdue)
- Added 300+ lines of translation dictionary content

### Sn 1.3.5
*(1763 lines, code size +85)*

AI reads local files:
- Added `/read <file_path>` chat command
- Added `read_local_file` function (supports UTF-8 / GBK auto-detection, 100k character limit, automatic truncation prompt)
- Added `READ_CHAR_LIMIT` constant
- `chat()` function added `documents` parameter to inject AI context

### Sn 1.3.6
*(1816 lines, code size +53)*

Automatic migration on chat record path change:
- Added `move_user_records` function
- On login, if `records_dir` path changes, automatically moves `settings_*.json` + `memories_*.json`
- Only moves files of the currently logged-in user, does not affect other users
- If a file with the same name already exists at the new path, automatically backs it up as `.old`
- Added `records_moved` / `records_move_conflict` translation keys

---

## Notes

- The SnowBall (Web) series was initially named after the "Snowball" concept and used Gradio as the Web framework.