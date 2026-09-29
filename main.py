import logging
import sys

from automation_server_client import (
    AutomationServer,
    Credential,
    WorkItemStatus,
    Workqueue,
)
from boss_client import client as boss_client
from nfs_client import client as nfs_client
from odk_tools.reporting import report
from odk_tools.tracking import Tracker

proces_navn = "Brugerluk NFS"


def populate_queue(workqueue: Workqueue, boss: boss_client.BossClient):
    logger = logging.getLogger(__name__)
    systems = boss.hent_systemer()
    boss_items = [item for item in systems["systems"] if item["systemName"] == "NFS"]
    logger.info(f"Fandt {len(boss_items)} NFS-brugere til lukning i BOSS")

    for item in boss_items:
        workqueue.add_item(item, item["initials"])


def process_workqueue(
    workqueue: Workqueue,
    boss: boss_client.BossClient,
    nfs: nfs_client.NFSClient,
    tracker: Tracker,
):
    logger = logging.getLogger(__name__)

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict

            try:
                nfs.brugere.slet_bruger(data["email"])
                boss.marker_bruger_som_slettet(data["id"])
                logger.info(
                    f"Bruger {data['initials']} slettet i NFS og markeret i BOSS"
                )
                tracker.track_task(proces_navn)
                report(
                    "brugerluk_nfs",
                    "Lukkede brugere",
                    {"Brugernavn": data["initials"]},
                )
            except ValueError as e:
                logger.warning(
                    f"Bruger {data['initials']} kunne ikke slettes i NFS: {e}"
                )
                report(
                    "brugerluk_nfs",
                    "Fejl",
                    {"Brugernavn": data["initials"], "Fejl": str(e)},
                )
                boss.marker_bruger_som_slettet(data["id"])
                tracker.track_partial_task(proces_navn)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger(__name__).setLevel(logging.INFO)
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()

    # Initialize external systems for automation here..

    tracking_credential = Credential.get_credential("Odense SQL Server")
    boss_credential = Credential.get_credential("BOSS")
    robob_credential = Credential.get_credential("RoboB")

    boss = boss_client.BossClient(
        client_id=boss_credential.username,
        client_secret=boss_credential.password,
        api_url=boss_credential.data["api_url"],
        base_url=boss_credential.data["base_url"],
        login_url=boss_credential.data["login_url"],
    )

    nfs = nfs_client.NFSClient(
        base_url=robob_credential.data["nfs_url"],
        username=robob_credential.username,
        password=robob_credential.password,
        headless=True,
    )

    tracker = Tracker(
        username=tracking_credential.username, password=tracking_credential.password
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        populate_queue(workqueue, boss)
        sys.exit(0)

    # Process workqueue
    process_workqueue(workqueue, boss, nfs, tracker)
