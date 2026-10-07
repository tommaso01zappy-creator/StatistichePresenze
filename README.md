
# ⚾ Baseball – Gestione Presenze

Applicazione desktop Windows per gestire le presenze di una squadra di baseball.

## Funzioni
- Database locale SQLite (`presenze.db`)
- Aggiunta, modifica ed eliminazione giocatori
- Calendario giornaliero
- Presente / Assente
- Salvataggio automatico nel database locale
- Percentuale di presenza per giocatore
- Dashboard con statistiche della squadra
- Grafici delle percentuali
- Interfaccia scura moderna

## Requisiti
- Windows 10/11
- Python 3.10 o superiore

## Installazione
Apri PowerShell nella cartella del progetto:

```powershell
python -m pip install -r requirements.txt
```

## Avvio

```powershell
python main.py
```

Al primo avvio viene creato automaticamente il file:

`presenze.db`

Non cancellarlo: contiene tutti i dati della squadra.

## Creare un EXE Windows
Per creare un eseguibile:

```powershell
python -m pip install pyinstaller
pyinstaller --noconsole --onefile --name BaseballPresenze main.py
```

L'eseguibile sarà nella cartella:

`dist\BaseballPresenze.exe`

Per mantenere il database accanto all'EXE è consigliato usare la modalità cartella:

```powershell
pyinstaller --noconsole --name BaseballPresenze main.py
```

e avviare:

`dist\BaseballPresenze\BaseballPresenze.exe`

## Utilizzo
1. Vai su **Giocatori** e aggiungi i nomi.
2. Vai su **Calendario**.
3. Seleziona il giorno.
4. Fai doppio clic sulla riga per alternare Presente/Assente.
5. Premi **Salva presenze**.
6. Dashboard e Statistiche si aggiornano automaticamente.

La percentuale è:

`presenze / giornate registrate × 100`

Solo le giornate salvate nel calendario vengono considerate.
