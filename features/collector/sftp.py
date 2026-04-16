import io
import json
import logging

import nbtlib
import paramiko
from django.conf import settings

logger = logging.getLogger(__name__)


def get_sftp_client() -> paramiko.SFTPClient:
    """Return an authenticated SFTP client using SSH key auth."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # nosec B507 — internal server, known_hosts not provisioned yet
    ssh.connect(
        hostname=settings.SFTP_HOST,
        port=int(settings.SFTP_PORT),
        username=settings.SFTP_USER,
        key_filename=settings.SFTP_KEY_PATH,
    )
    return ssh.open_sftp()


def read_json_file(sftp: paramiko.SFTPClient, path: str) -> dict | None:
    """Read and parse a JSON file from the remote server. Returns dict or None."""
    try:
        with sftp.open(path) as f:
            return json.loads(f.read())
    except Exception as e:
        logger.debug("Could not read %s: %s", path, e)
        return None


def read_nbt_file(sftp: paramiko.SFTPClient, path: str) -> nbtlib.File | None:
    """Read and parse an NBT file from the remote server. Returns nbtlib object or None."""
    try:
        with sftp.open(path) as f:
            data = f.read()
        logger.info("NBT read %s — %d bytes", path, len(data))
        result = nbtlib.File.parse(io.BytesIO(data))
        logger.info("NBT parsed — root keys: %s", list(result.keys()))
        return result
    except Exception as e:
        logger.error("Could not read NBT %s: %s", path, e)
        return None


def read_usercache(sftp: paramiko.SFTPClient) -> dict[str, str]:
    """Read usercache.json and return a {uuid: name} dict."""
    from pathlib import PurePosixPath

    server_path = str(PurePosixPath(settings.MINECRAFT_WORLD_PATH).parent)
    data = read_json_file(sftp, f"{server_path}/usercache.json")
    if not data:
        return {}
    return {
        entry["uuid"]: entry["name"]
        for entry in data
        if "uuid" in entry and "name" in entry
    }


def collect_player_data(sftp: paramiko.SFTPClient, uuid: str) -> dict[str, int]:
    """
    Collect all stats for a single player UUID.
    Returns a dict with keys matching PlayerStats fields.
    """
    data = {}
    shard = uuid[:2]

    # Vanilla play time — world/stats/{uuid}.json
    stats_file = read_json_file(
        sftp, f"{settings.MINECRAFT_WORLD_PATH}/stats/{uuid}.json"
    )
    if stats_file:
        data["play_time_ticks"] = (
            stats_file.get("stats", {})
            .get("minecraft:custom", {})
            .get("minecraft:play_time", 0)
        )
    else:
        data["play_time_ticks"] = 0

    # Cobblemon player data — sharded: cobblemonplayerdata/{shard}/{uuid}.json
    cobblemon_data = read_json_file(
        sftp, f"{settings.COBBLEMON_DATA_PATH}/{shard}/{uuid}.json"
    )
    data["battles_won"] = (cobblemon_data or {}).get("battleWins", 0)

    # Caught pokemon — counted from per-pokemon files in storage directory
    try:
        pokemon_dir = f"{settings.COBBLEMON_DATA_PATH}/pokemon/{shard}/{uuid}"
        data["pokemons_caught"] = len(sftp.listdir(pokemon_dir))
    except Exception:
        data["pokemons_caught"] = 0

    # Pokédex — sharded NBT: world/pokedex/{shard}/{uuid}.nbt
    # speciesRecords has one entry per species registered
    pokedex_path = f"{settings.MINECRAFT_WORLD_PATH}/pokedex/{shard}/{uuid}.nbt"
    try:
        pokedex_nbt = read_nbt_file(sftp, pokedex_path)
        if pokedex_nbt is not None:
            species = pokedex_nbt["speciesRecords"]
            count = len(species)
            logger.info("Pokédex %s — speciesRecords count: %d", uuid, count)
            data["pokedex_registered"] = count
        else:
            logger.warning(
                "Pokédex %s — NBT file returned None: %s", uuid, pokedex_path
            )
            data["pokedex_registered"] = 0
    except Exception as e:
        logger.error("Pokédex %s — failed to parse: %s", uuid, e)
        data["pokedex_registered"] = 0

    # CobbleDollars — cobbledollarsplayerdata/{uuid}.json
    economy_data = read_json_file(sftp, f"{settings.COBBLE_ECONOMY_PATH}/{uuid}.json")
    data["cobbledollars"] = int((economy_data or {}).get("cobbledollars", 0))

    # CobbleTCG — addon not installed yet
    data["cobbletcg_cards"] = 0

    return data
