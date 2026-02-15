# n8n-ngrok-ytdlp: Automation Stack

This repository provides a complete configuration based on **Docker Compose** to
run **n8n**, exposed via **Ngrok**, and integrated with a custom **Python
Worker**. This architecture allows managing complex automation flows that
require executing Python scripts with specific dependencies (like `yt-dlp`,
`pandas`, `ffmpeg`) and advanced cookie management.

## 📂 Project Tour

Here's how the project is structured and what each component is for:

- **`docker-compose.yaml`**: The main file that orchestrates the three services:
  - `n8n`: The automation engine.
    - _Note_: The `NODES_EXCLUDE=[]` variable is used to ensure that no default
      n8n nodes are disabled. If you want to hide some nodes, you can list them
      here.
  - `ngrok`: The tunnel that makes n8n accessible from the outside (necessary
    for receiving webhooks).
  - `python_worker`: A custom Flask service for executing Python scripts.
- **`.env`**: The file (to be created) that stores all sensitive configurations
  and environment variables.
- **`ngrok.yml`**: Specific configuration file for the Ngrok tunnel.
- **`python_worker/`**: Folder dedicated to the Python worker.
  - `Dockerfile`: Defines the worker's environment (Python, Node.js, ffmpeg,
    etc.).
  - `main.py`: The Flask application that receives requests from n8n and
    executes scripts.
  - `requirements.txt`: The installed Python libraries.
  - `cookies.txt`: File (to be generated) required to authenticate scripts like
    `yt-dlp` on sites that require login.
  - `scripts/`: Where to place your Python `.py` scripts.
- **`shared_data/`**: A shared volume mounted on both n8n and the Python Worker.
  Useful for passing downloaded or processed files from one service to another.
  - **Note**: Be careful, currently some hidden files (starting with `.`) might
    remain inside this folder between transcriptions.

---

## 🌍 Why Ngrok?

In this setup, Ngrok performs two fundamental functions:

1. **Remote Access**: It allows you to access the n8n interface from any device
   via a public domain, freeing you from the constraint of using `localhost` on
   the machine hosting the containers.
2. **Webhook Testing (e.g., Telegram)**: Many services (like Telegram) strictly
   require a valid public **HTTPS** URL to send data to webhooks. Without a
   tunnel like Ngrok, test **Triggers** in the n8n editor would not work, making
   workflow development impossible.

> **Note**: Once the configuration and testing phase is complete, if you don't
> need to receive external webhooks or access n8n remotely, you can safely
> remove the Ngrok service from `docker-compose.yaml`; the rest of the stack
> will continue to function.

---

## 🚀 Installation and Configuration Guide

Follow these steps to configure the project with your credentials.

### 1. Prerequisites

Make sure you have installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd n8n-ngrok
```

### 3. Create Shared Folder (`shared_data`)

Although Docker Compose can automatically create volumes, it is **strongly
recommended** to manually create the `shared_data` folder before starting. This
ensures that the folder has the correct permissions for your user, allowing n8n
(which runs as a non-root user) to write to it without permission errors.

```bash
mkdir -p shared_data
```

### 4. Configure Environment Variables (`.env`)

Create a `.env` file in the project root based on the example file:

```bash
cp env_sample .env
```

This file **SHOULD NOT be committed** if it contains real data. Open `.env` and
fill in the fields:

```bash
# Set your timezone
TIMEZONE=Europe/Rome

# Your Ngrok Authtoken (from the Ngrok dashboard)
NGROK_TOKEN=insert_your_secret_ngrok_token_here

# The URL of the static domain you reserved on Ngrok
# Example: https://my-domain.ngrok-free.app
URL=https://insert-your-domain.ngrok-free.app

# A secret key of your choice to protect the Python Worker API
# Generate a long and complex one. n8n will need to use this key in the request header.
PYTHON_WORKER_API_KEY=generate_a_random_and_secure_string

# Actually, the API key for the Python server is not necessary at all.
# One can remove it by modifying the Python server code. However, I decided
# to include it anyway, thinking that someone might find it useful or pleasant
# perhaps if used in specific environments where it is required.
```

### 5. Configure Ngrok (`ngrok.yml`)

Create the configuration file for Ngrok based on the example:

```bash
cp ngrok_sample.yml ngrok.yml
```

Edit the `ngrok.yml` file to match the domain entered in the `.env` file.

**Important**: Make sure you have reserved a static domain (free or paid) in the
"Cloud Edge > Domains" section of the Ngrok dashboard.

```yaml
version: 2
log_level: debug
tunnels:
    n8n:
        proto: http
        addr: n8n:5678
        # MUST match the domain in the .env file (without https://)
        domain: insert-your-domain.ngrok-free.app
```

### 6. Configure Cookies for Python Worker

If your Python scripts (e.g., `yt-dlp`) need to access protected sites or verify
identity (like YouTube, Instagram, etc.), you must provide cookies.

1. Install the **"Get cookies.txt LOCALLY"** (or similar) extension on your
   browser (Chrome/Firefox).
2. Go to the site of interest (e.g., YouTube) and log in.
3. Use the extension to download cookies in Netscape/Mozilla format.
4. Rename the downloaded file to **`cookies.txt`** and place it in the
   **`python_worker/`** folder of the project.

> **Note**: The `python_worker/cookies.txt` file is automatically mounted in the
> container at `/app/cookies.txt`.

---

## ▶️ Project Startup

Once everything is configured, start the stack:

```bash
docker-compose up -d
```

The `-d` option starts the containers in the background.

To view logs (useful for debugging):

```bash
docker-compose logs -f
```

To stop everything:

```bash
docker-compose down
```

---

## ℹ️ Info

- All Telegram messages and the Gemini prompt are in Italian (go change them if
  u need)
- Telegram messages are sent in chunks of maximum 3800 characters, with a
  maximum of 5 chunks (considered sufficient for "summarizing").
- A Telegram message is sent if there's a "probable" exceeding of the API key
  limit (the error is not literally handled, but if an error is detected by
  Gemini, this message will appear).
- Gemini's temperature updated to = 0.9.
- Chunks do not truncate Gemini's output message but try to cut based on
  sentences (using the dot '.' as a separator) with a minimum threshold of 3000
  characters; if not respected, it falls back to separating the message by
  complete words (nothing is ever truncated!).

---

## 💡 Usage

### Pre-configured n8n Workflow

In the project root, you'll find the `yt_summarize_video.json` file. This file
contains an n8n workflow already configured to:

1. Receive a YouTube link from a Telegram bot.
2. Extract subtitles via the Python Worker.
3. Summarize the content using Google Gemini.
4. Send the summary to the user.

**To use it:**

1. Open your n8n instance.
2. Click on **Workflows** > **Import from File...** and select
   `yt_summarize_video.json`.
3. **Please note**: The workflow is without API keys and tokens. You will need
   to manually configure the credentials for the **Telegram Trigger/Node** and
   for the **Google Gemini** node (using your Google AI Studio API Key).

### Accessing n8n

Open your browser and go to the URL you configured (e.g.,
`https://my-domain.ngrok-free.app`). You should see the n8n interface.

### Using the Python Worker from n8n

To execute a Python script from an n8n workflow:

1. Add an **HTTP Request** node.
2. **Method**: `POST`
3. **URL**: `http://python_worker:5000/run` (note: we use the Docker service
   name `python_worker` as the hostname).
4. **Headers**:
   - Name: `X-API-KEY`
   - Value: `YourSecretKeyDefinedInEnv` (you can use an n8n expression
     `{{ $env.PYTHON_WORKER_API_KEY }}` if you make it available to n8n,
     otherwise write it directly).
5. **Body Parameters** (JSON):
   ```json
   {
       "script": "script_name.py",
       "args": ["argument1", "argument2"]
   }
   ```
   - `script`: The name of the file in `python_worker/scripts/`.
   - `args`: A list of arguments to pass to the script.

### Script Example

Make sure your script in `python_worker/scripts/` prints the result in JSON to
`stdout` if you want to retrieve it structured in n8n.

### 📝 Practical Examples for Included Scripts

Here's how to configure the n8n **HTTP Request** node to use the scripts already
present in the `scripts/` folder.

#### 1. Execute `test_script.py`

This script takes two arguments (Name and Surname) and returns a greeting.

- **URL**: `http://python_worker:5000/run`
- **Method**: `POST`
- **Body**:
  ```json
  {
      "script": "test_script.py",
      "args": ["Mario", "Rossi"]
  }
  ```
- **Expected result**: A JSON object with a greeting message.

#### 2. Execute `get_subs.py`

This script downloads subtitles for a YouTube video using `yt-dlp` (and cookies
if configured).

- **URL**: `http://python_worker:5000/run`
- **Method**: `POST`
- **Body**:
  ```json
  {
      "script": "get_subs.py",
      "args": ["https://www.youtube.com/watch?v=VIDEO_ID"]
  }
  ```
- **Expected result**: A JSON containing the path to the `.srt` file downloaded
  in the shared volume.
  - Note: The file will be saved in `/data` (worker side) which corresponds to
    `/home/node/.n8n-files` (n8n side).

## ⚠️ Security

- Never commit the `.env` file or `python_worker/cookies.txt` to public
  repositories.
- The `PYTHON_WORKER_API_KEY` prevents unauthorized calls to your worker, but
  since it's an internal Docker network, the risk is controlled. However, it's
  good practice to keep it.

## 🛠️ Recommended Tools

### Lazydocker

To manage containers more easily and visually from the terminal, I highly
recommend using [lazydocker](https://github.com/jesseduffield/lazydocker). It
allows you to see logs, container status, and resource consumption statistics
without having to remember Docker commands.

---

## 🔧 Common Troubleshooting

### 🚫 Ngrok domain unreachable or blocked

If you encounter connection errors, timeouts, or security warnings when trying
to access your Ngrok domain (e.g., `https://xxx.ngrok-free.app`):

1. **Check Router or DNS**: Some internet service providers or routers with
   active security protections (e.g., "Safe Browsing") might block free Ngrok
   domains (`.ngrok-free.app`) considering them potentially risky.
2. **Verify**: Try temporarily changing the DNS (e.g., using Google's 8.8.8.8)
   or disabling router protection filters to isolate the problem.

---

## 📜 License

This project is distributed under the **MIT** license. Consult the `LICENSE`
file for more details.
