# n8n-ngrok-ytdlp: Stack di Automazione

Questo repository offre una configurazione completa basata su **Docker Compose** per eseguire **n8n**, esposto in modo sicuro tramite **Ngrok**, e integrato con un **Python Worker** personalizzato. Questa architettura permette di gestire flussi di automazione complessi che richiedono l'esecuzione di script Python con dipendenze specifiche (come `yt-dlp`, `pandas`, `ffmpeg`) e la gestione avanzata dei cookie.

## 📂 Tour del Progetto

Ecco come è strutturato il progetto e a cosa serve ogni componente:

*   **`docker-compose.yaml`**: Il file principale che orchestra i tre servizi:
    *   `n8n`: Il motore di automazione.
        *   *Nota*: La variabile `NODES_EXCLUDE=[]` viene usata per assicurarsi che nessun nodo predefinito di n8n sia disabilitato. Se volessi nascondere alcuni nodi, potresti elencarli qui.
    *   `ngrok`: Il tunnel che rende n8n accessibile dall'esterno (necessario per ricevere webhook).
    *   `python_worker`: Un servizio Flask personalizzato per eseguire script Python.
*   **`.env`**: Il file (da creare) che custodisce tutte le configurazioni sensibili e le variabili d'ambiente.
*   **`ngrok.yml`**: File di configurazione specifico per il tunnel Ngrok.
*   **`python_worker/`**: Cartella dedicata al worker Python.
    *   `Dockerfile`: Definisce l'ambiente del worker (Python, Node.js, ffmpeg, ecc.).
    *   `main.py`: L'applicazione Flask che riceve le richieste da n8n ed esegue gli script.
    *   `requirements.txt`: Le librerie Python installate.
    *   `cookies.txt`: File (da generare) necessario per autenticare script come `yt-dlp` su siti che richiedono login.
    *   `scripts/`: Dove posizionare i tuoi script Python `.py`.
*   **`shared_data/`**: Un volume condiviso montato sia su n8n che sul Python Worker. Utile per passare file scaricati o elaborati da un servizio all'altro.
    *   **Nota**: Attenzione, al momento potrebbero rimanere dei file nascosti (che iniziano con `.`) all'interno di questa cartella tra una trascrizione e l'altra.

---

## 🌍 Perché Ngrok?

In questo setup, Ngrok svolge due funzioni fondamentali:

1.  **Accesso Remoto**: Ti permette di accedere all'interfaccia di n8n da qualsiasi dispositivo tramite un dominio pubblico, liberandoti dal vincolo di usare `localhost` sulla macchina che ospita i container.
2.  **Test dei Webhook (es. Telegram)**: Molti servizi (come Telegram) richiedono tassativamente un URL **HTTPS** pubblico valido per inviare dati ai webhook. Senza un tunnel come Ngrok, i **Trigger** di test nell'editor di n8n non funzionerebbero, rendendo impossibile lo sviluppo dei flussi.

> **Nota**: Una volta terminata la fase di configurazione e test, se non hai necessità di ricevere webhook dall'esterno o di accedere a n8n da remoto, puoi tranquillamente rimuovere il servizio Ngrok dal `docker-compose.yaml`; il resto dello stack continuerà a funzionare.

---

## 🚀 Guida all'Installazione e Configurazione

Segui questi passaggi per configurare il progetto con le tue credenziali.

### 1. Prerequisiti
Assicurati di avere installato:
*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Clona il Repository
```bash
git clone <URL_DEL_REPOSITORY>
cd n8n-ngrok
```

### 3. Creazione Cartella Condivisa (`shared_data`)
Sebbene Docker Compose possa creare automaticamente i volumi, è **fortemente consigliato** creare manualmente la cartella `shared_data` prima dell'avvio. Questo garantisce che la cartella abbia i permessi corretti per il tuo utente, permettendo a n8n (che gira come utente non-root) di scriverci senza errori di permessi.

```bash
mkdir -p shared_data
```

### 4. Configurazione Variabili d'Ambiente (`.env`)
Crea un file `.env` nella root del progetto. Questo file **NON deve essere committato** se contiene dati reali. Copia il seguente template e compila i campi:

```bash
# Imposta il tuo fuso orario
TIMEZONE=Europe/Rome

# Il tuo Authtoken di Ngrok (dalla dashboard di Ngrok)
NGROK_TOKEN=inserisci_qui_il_tuo_token_ngrok_segreto

# L'URL del dominio statico che hai prenotato su Ngrok
# Esempio: https://mio-dominio.ngrok-free.app
URL=https://inserisci-il-tuo-dominio.ngrok-free.app

# Una chiave segreta a tua scelta per proteggere l'API del Python Worker
# Generane una lunga e complessa. n8n dovrà usare questa chiave nell'header delle richieste.
PYTHON_WORKER_API_KEY=genera_una_stringa_casuale_e_sicura
```

### 5. Configurazione Ngrok (`ngrok.yml`)
Modifica il file `ngrok.yml` per far corrispondere il dominio a quello inserito nel file `.env`.

**Importante**: Assicurati di aver prenotato un dominio statico (gratuito o a pagamento) nella sezione "Cloud Edge > Domains" della dashboard di Ngrok.

```yaml
version: 2
log_level: debug
tunnels:
    n8n:
        proto: http
        addr: n8n:5678
        # DEVE corrispondere al dominio nel file .env (senza https://)
        domain: inserisci-il-tuo-dominio.ngrok-free.app
```

### 6. Configurazione Cookie per Python Worker
Se i tuoi script Python (es. `yt-dlp`) necessitano di accedere a siti protetti o verificare l'identità (come YouTube, Instagram, ecc.), devi fornire i cookie.

1.  Installa l'estensione **"Get cookies.txt LOCALLY"** (o simile) sul tuo browser (Chrome/Firefox).
2.  Vai sul sito di interesse (es. YouTube) ed effettua il login.
3.  Usa l'estensione per scaricare i cookie in formato Netscape/Mozilla.
4.  Rinomina il file scaricato in `cookies.txt`.
5.  Posizionalo nella cartella `python_worker/` del progetto.

> **Nota**: Il file `python_worker/cookies.txt` viene montato automaticamente nel container alla posizione `/app/cookies.txt`.

---

## ▶️ Avvio del Progetto

Una volta configurato tutto, avvia lo stack:

```bash
docker-compose up -d
```
L'opzione `-d` avvia i container in background.

Per vedere i log (utile per il debug):
```bash
docker-compose logs -f
```

Per fermare tutto:
```bash
docker-compose down
```

---

## 💡 Utilizzo

### Workflow n8n Preconfigurato
Nella root del progetto trovi il file `yt_summarize_video.json`. Questo file contiene un workflow di n8n già configurato per:
1. Ricevere un link YouTube da un bot Telegram.
2. Estrarre i sottotitoli tramite il Python Worker.
3. Riassumere il contenuto utilizzando Google Gemini.
4. Inviare il riassunto all'utente.

**Per usarlo:**
1. Apri la tua istanza di n8n.
2. Clicca su **Workflows** > **Import from File...** e seleziona `yt_summarize_video.json`.
3. **Nota bene**: Il workflow è sprovvisto di chiavi API e token. Dovrai configurare manualmente le credenziali per i nodi **Telegram Trigger/Node** e per il nodo **Google Gemini** (usando la tua API Key di Google AI Studio).

### Accedere a n8n
Apri il browser e vai all'URL che hai configurato (es. `https://mio-dominio.ngrok-free.app`). Dovresti vedere l'interfaccia di n8n.

### Usare il Python Worker da n8n
Per eseguire uno script Python da un workflow di n8n:

1.  Aggiungi un nodo **HTTP Request**.
2.  **Method**: `POST`
3.  **URL**: `http://python_worker:5000/run` (nota: usiamo il nome del servizio Docker `python_worker` come hostname).
4.  **Headers**:
    *   Name: `X-API-KEY`
    *   Value: `LaTuaChiaveSegretaDefinitaInEnv` (puoi usare un'espressione n8n `{{ $env.PYTHON_WORKER_API_KEY }}` se la rendi disponibile a n8n, altrimenti scrivila direttamente).
5.  **Body Parameters** (JSON):
    ```json
    {
      "script": "nome_dello_script.py",
      "args": ["argomento1", "argomento2"]
    }
    ```
    *   `script`: Il nome del file presente in `python_worker/scripts/`.
    *   `args`: Una lista di argomenti da passare allo script.

### Esempio di Script
Assicurati che il tuo script in `python_worker/scripts/` stampi il risultato in JSON su `stdout` se vuoi recuperarlo strutturato in n8n.

### 📝 Esempi Pratici per gli Script Inclusi

Ecco come configurare il nodo **HTTP Request** di n8n per utilizzare gli script già presenti nella cartella `scripts/`.

#### 1. Eseguire `test_script.py`
Questo script prende due argomenti (Nome e Cognome) e restituisce un saluto.

*   **URL**: `http://python_worker:5000/run`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
      "script": "test_script.py",
      "args": ["Mario", "Rossi"]
    }
    ```
*   **Risultato atteso**: Un oggetto JSON con un messaggio di saluto.

#### 2. Eseguire `get_subs.py`
Questo script scarica i sottotitoli di un video YouTube utilizzando `yt-dlp` (e i cookie se configurati).

*   **URL**: `http://python_worker:5000/run`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
      "script": "get_subs.py",
      "args": ["https://www.youtube.com/watch?v=VIDEO_ID"]
    }
    ```
*   **Risultato atteso**: Un JSON contenente il percorso del file `.srt` scaricato nel volume condiviso.
    *   Nota: Il file verrà salvato in `/data` (lato worker) che corrisponde a `/home/node/.n8n-files` (lato n8n).

## ⚠️ Sicurezza
*   Non committare mai il file `.env` o `python_worker/cookies.txt` in repository pubblici.
*   La `PYTHON_WORKER_API_KEY` impedisce chiamate non autorizzate al tuo worker, ma dato che è una rete interna Docker, il rischio è controllato. Tuttavia, è buona norma mantenerla.

## 🛠️ Strumenti Consigliati

### Lazydocker
Per gestire i container in modo più semplice e visuale da terminale, ti consiglio vivamente l'uso di [lazydocker](https://github.com/jesseduffield/lazydocker). Ti permette di vedere log, stato dei container e statistiche di consumo risorse senza dover ricordare i comandi Docker.

---

## 🔧 Risoluzione Problemi Comuni

### 🚫 Il dominio Ngrok non è raggiungibile o viene bloccato
Se provando ad accedere al tuo dominio Ngrok (es. `https://xxx.ngrok-free.app`) riscontri errori di connessione, timeout o avvisi di sicurezza:

1.  **Controlla il Router o il DNS**: Alcuni fornitori di servizi internet o router con protezioni di sicurezza attive (es. "Navigazione Sicura") potrebbero bloccare i domini gratuiti di Ngrok (`.ngrok-free.app`) ritenendoli potenzialmente rischiosi.
2.  **Verifica**: Prova a cambiare momentaneamente i DNS (es. usando 8.8.8.8 di Google) o a disattivare i filtri di protezione del router per isolare il problema.
