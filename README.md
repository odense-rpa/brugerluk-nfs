# Brugerluk NFS

Lukker NFS-brugere for medarbejdere, der er registreret til nedlukning i BOSS-systemet.

## Hvad gør robotten?

1. Henter alle systemer fra BOSS og filtrerer på systemName == 'NFS'
2. Tilføjer de fundne medarbejdere til arbejdskøen
3. For hvert element i køen: sletter brugeren i NFS via e-mailadressen (`data['email']`) gennem RoboB
4. Markerer brugeren som slettet i BOSS
5. Tracker opgaven via Odense SQL Server
6. Ved fejl (`ValueError`): rapporterer fejlen med brugernavn og fejlbesked, markerer stadig brugeren som slettet i BOSS og tracker som delvis fuldført

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø)
- Adgang til **BOSS** HR-system
- Adgang til **NFS** via **RoboB**
- Adgang til **Odense SQL Server**

## Installation

```sh
uv sync
```

## Konfiguration

Credentials registreres i Automation Server:

- `Odense SQL Server` — forbindelse til task-tracking-databasen
- `BOSS` — adgang til HR-systemet
- `RoboB` — gateway til NFS med brugernavn, adgangskode og `nfs_url` i data-feltet

Miljøvariabler:

| Variabel | Beskrivelse |
|---|---|
| `ATS_URL` | URL til Automation Server API |
| `ATS_TOKEN` | Adgangstoken til Automation Server |
| `ATS_WORKQUEUE_OVERRIDE` | Overstyr workqueue-ID (valgfri) |

## Kørsel

```sh
uv run python main.py --queue   # Fyld arbejdskøen med medarbejdere til nedlukning
uv run python main.py           # Behandl arbejdskøen og luk NFS-brugerne
```

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Klient til Automation Server – workqueue, credentials og WorkItemStatus |
| `boss-client` | Klient til BOSS HR-system – henter systemer og markerer brugere som slettet |
| `nfs-client` | Klient til NFS-systemet via RoboB – sletter brugere |
| `odk-tools` | Odense-værktøjer til fejlrapportering og task-tracking |
| `ruff` | Python linter |

## GDPR og sikkerhed

Processen behandler medarbejderdata fra BOSS: initialer, e-mailadresse og system-id. Oplysningerne bruges udelukkende til at identificere og slette brugere i NFS og overføres ikke til tredjeparter. Fejlrapporter med brugernavne logges via `odk-tools`.
