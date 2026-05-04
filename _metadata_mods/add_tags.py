"""One-shot script: inject tags into all mod JSON files."""

import json
from pathlib import Path

TAGS: dict[str, list[str]] = {
    # ── decoration ────────────────────────────────────────────────────────
    "chipped": ["decoration"],
    "chisel": ["decoration"],
    "cobble_furnies": ["decoration"],
    "furniture": ["decoration"],
    "luckys_cozy_home": ["decoration"],
    "macaws_furniture": ["decoration"],
    "supplementaries": ["decoration"],
    "waterframes": ["decoration"],
    # ── economy ───────────────────────────────────────────────────────────
    "cobbledollars": ["economy"],
    "cobblemon_gts": ["economy"],
    # ── gameplay_control ──────────────────────────────────────────────────
    "item_obliterator": ["gameplay_control"],
    "structurify": ["gameplay_control"],
    "you_shall_not_spawn": ["gameplay_control"],
    # ── performance ───────────────────────────────────────────────────────
    "c2me": ["performance"],
    "ferritecore": ["performance"],
    "modern-fix": ["performance"],
    # ── pokemon ───────────────────────────────────────────────────────────
    "cobbledex_for_rei-emi-jei": ["pokemon"],
    "cobbled_gacha": ["pokemon"],
    "cobblemon": ["pokemon"],
    "cobblemon_additions": ["pokemon"],
    "cobblemon_capture_xp": ["pokemon"],
    "cobblemon_challenge": ["pokemon"],
    "cobblemon_cobble_stats": ["pokemon"],
    "cobblemon_infinite_riding_stamina": ["pokemon"],
    "cobblemon_integrations": ["pokemon"],
    "cobblemon_journey_mounts": ["pokemon"],
    "cobblemon_legendary_monuments": ["pokemon"],
    "cobblemon_mega_showdown": ["pokemon"],
    "cobblemon_move_dex": ["pokemon"],
    "cobblemon_pasture_loot": ["pokemon"],
    "cobblemon_pokenav": ["pokemon"],
    "cobblemon_raid_dens": ["pokemon"],
    "cobblemon_ranked": ["pokemon"],
    "cobblemon_repel": ["pokemon"],
    "cobblemon_research_tasks": ["pokemon"],
    "cobblemon_safe_pastures": ["pokemon"],
    "cobblemon_scoremons": ["pokemon"],
    "cobblemon_smartphone": ["pokemon"],
    "cobblemon_spawn_notification": ["pokemon"],
    "cobblemon_tents": ["pokemon"],
    "cobblemon_wiki_gui": ["pokemon"],
    "cobble_safari": ["pokemon"],
    "cobbreeding": ["pokemon"],
    "complete_cobblemon_collection": ["pokemon"],
    "pokebadges": ["pokemon"],
    "radical_cobblemon_trainers": ["pokemon"],
    "simple_tms": ["pokemon"],
    "za_megas": ["pokemon"],
    # ── quality_of_life ───────────────────────────────────────────────────
    "accessories": ["quality_of_life"],
    "advanced_loot_info": ["quality_of_life"],
    "carry_on": ["quality_of_life"],
    "explorers_compass": ["quality_of_life"],
    "falling_tree": ["quality_of_life"],
    "global_datapacks": ["quality_of_life"],
    "inventory_management": ["quality_of_life"],
    "iron_chests": ["quality_of_life"],
    "jade": ["quality_of_life"],
    "jei": ["quality_of_life"],
    "mob_lassos": ["quality_of_life"],
    "mod_menu": ["quality_of_life"],
    "natures_compass": ["quality_of_life"],
    "only_paxels": ["quality_of_life"],
    "polymorph": ["quality_of_life"],
    "starter_kit": ["quality_of_life"],
    "toms_simple_storage": ["quality_of_life"],
    "travelers_backpack": ["quality_of_life"],
    "visual_workbench": ["quality_of_life"],
    "waystones": ["quality_of_life"],
    "xaeros_minimap": ["quality_of_life"],
    # ── roleplay ──────────────────────────────────────────────────────────
    "easy_npc": ["roleplay"],
    "emotecraft": ["roleplay"],
    "immersive_melodies": ["roleplay"],
    "simple_voice_chat": ["roleplay"],
    # ── worldgen ──────────────────────────────────────────────────────────
    "terralith": ["worldgen"],
    # ── client-side (single best-fit tag) ─────────────────────────────────
    "3d_skin_layers": ["quality_of_life"],
    "ambient_sounds": ["quality_of_life"],
    "better_ping_display": ["quality_of_life"],
    "chat_heads": ["quality_of_life"],
    "cobble_sounds": ["pokemon"],
    "cobblemon_catch_rate_display": ["pokemon"],
    "cobblemon_move_inspector": ["pokemon"],
    "continuity": ["quality_of_life"],
    "entity_culling": ["performance"],
    "immediately_fast": ["performance"],
    "iris_shaders": ["quality_of_life"],
    "music_control": ["quality_of_life"],
    "not_enough_animations": ["quality_of_life"],
    "particular": ["quality_of_life"],
    "sodium": ["performance"],
    "sounds_be_gone": ["quality_of_life"],
    "zoomify": ["quality_of_life"],
    # ── server-side ───────────────────────────────────────────────────────
    "skin_restorer": ["quality_of_life"],
}

ROOT = Path(__file__).parent
updated = skipped = missing = 0

for json_file in sorted(ROOT.rglob("*-info.json")):
    slug = json_file.stem.removesuffix("-info")
    if slug not in TAGS:
        print(f"  MISSING tags: {slug}")
        missing += 1
        continue
    data = json.loads(json_file.read_text(encoding="utf-8"))
    if data.get("tags") == TAGS[slug]:
        skipped += 1
        continue
    data["tags"] = TAGS[slug]
    json_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    updated += 1

print(f"Done — updated: {updated}, skipped: {skipped}, missing: {missing}")
