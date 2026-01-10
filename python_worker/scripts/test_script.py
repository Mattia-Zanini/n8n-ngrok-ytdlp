import sys
import json

# Esempio di script che riceve argomenti e restituisce un JSON
# Uso: python3 test_script.py <nome> <cognome>

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Argomenti insufficienti"}))
        sys.exit(1)

    nome = sys.argv[1]
    cognome = sys.argv[2]

    result = {
        "message": f"Ciao, {nome} {cognome}! Questo script Python funziona.",
        "received_args": sys.argv[1:]
    }

    # Stampa il risultato come JSON su stdout (n8n lo riceverà)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
