"""One-shot script: inject description_pt_br into all mod JSON files."""

import json
from pathlib import Path

TRANSLATIONS: dict[str, str] = {
    # ── core ──────────────────────────────────────────────────────────────
    "accessories": "Um mod de acessórios extensível e orientado a dados para o Minecraft",
    "advanced_loot_info": "Plugin para EMI/JEI/REI que exibe informações avançadas sobre tabelas de loot e trocas de aldeões",
    "c2me": "Um mod Fabric projetado para melhorar o desempenho de geração de chunks no Minecraft.",
    "carry_on": "Carry On permite pegar Tile Entities e Mobs e carregá-los pelo mundo!",
    "chipped": "Todo bloco merece um amigo.",
    "chisel": "Adiciona muitas variações decorativas dos blocos vanilla",
    "cobble_furnies": "CobbleFurnies traz suas criações à vida com móveis lindamente elaborados com temática Cobblemon que se integram perfeitamente ao seu mundo Minecraft!",
    "cobble_safari": "Mundo da Distorção, O Submundo de Sinnoh... Cobblesafari adiciona novas mecânicas de gameplay baseadas nos jogos principais!",
    "cobbled_gacha": "Adiciona máquinas de gacha com foco em Cobblemon que entregam loot incrível! Ou talvez não?",
    "cobbledex_for_rei-emi-jei": "O CobbleDex transforma REI, JEI ou EMI em uma referência completa de Cobblemon no jogo. Clique em um Pokémon e veja spawns, evoluções, drops, movimentos, stats, formas, fósseis e muito mais",
    "cobbledollars": "CobbleDollars adiciona Dinheiro e Comerciantes ao Cobblemon",
    "cobblemon": "Adiciona Pokémon ao Minecraft como foco principal do gameplay.\nSubstitui a progressão tradicional por captura, treino e interação com criaturas.",
    "cobblemon_additions": "Mod que adiciona vilas com variantes de Vilas/Cidades Pokémon — criado originalmente para o servidor Brocraft. Gera diversas estruturas dentro das aldeias.",
    "cobblemon_capture_xp": "Concede EXP para seu time ao capturar um Pokémon selvagem.",
    "cobblemon_challenge": "Plugin simples para Cobblemon que facilita desafiar amigos e rivais em batalhas de nível fixo. Com prévia de times!",
    "cobblemon_cobble_stats": "Traz informações de stats e terreno no estilo Showdown para o Cobblemon",
    "cobblemon_gts": "Sistema Global de Trocas para Cobblemon que permite vender Pokémon e Itens.",
    "cobblemon_infinite_riding_stamina": "Datapack que remove o limite de stamina das montarias do Cobblemon 1.7, permitindo explorar e viajar sem interrupções.",
    "cobblemon_integrations": "Diversas integrações com outros mods para o Cobblemon.",
    "cobblemon_journey_mounts": "Mais montarias do Cobblemon para o Cobblemon 1.7",
    "cobblemon_legendary_monuments": "Adiciona métodos especiais de spawning para Pokémon Lendários e Míticos",
    "cobblemon_mega_showdown": "Adiciona mega evoluções, z-moves, terastalização, dynamax, ultra burst e fusões ao jogo",
    "cobblemon_move_dex": "Adiciona a função de consultar movimentos aprendíveis na Pokédex do Cobblemon.",
    "cobblemon_pasture_loot": "Quer abandonar o estilo caçador-coletor e deixar seus pokémon no pasto trabalharem por você? Este mod é para você!",
    "cobblemon_pokenav": "O mod Cobblenav é inspirado no item e mecânicas dos jogos Pokémon RSE e Pokémon ORAS",
    "cobblemon_raid_dens": "Introduz Covils de Raid ao Cobblemon!",
    "cobblemon_ranked": "Sistema de ranking adicionado ao Cobblemon",
    "cobblemon_repel": "Novos blocos que impedem o spawn de Pokémon em um raio",
    "cobblemon_research_tasks": "Adiciona Tarefas de Pesquisa similares às de Pokémon: Legends Arceus ao Cobblemon",
    "cobblemon_safe_pastures": "Deixe seus pastos seguros! Decore à vontade sem se preocupar com seus pokémon em perigo!",
    "cobblemon_scoremons": "Addon de Cobblemon que adiciona Estatísticas de Jogadores para rastreamento no placar",
    "cobblemon_smartphone": "Smartphone com integração ao Cobblemon para funções rápidas como curar o time, abrir o PC e o baú do Ender.",
    "cobblemon_spawn_notification": "E se o jogo te avisasse sobre spawns importantes?",
    "cobblemon_tents": "Adiciona Barracas ao Cobblemon",
    "cobblemon_wiki_gui": "Mod auxiliar do Cobblemon para ver informações úteis sobre cada espécie de Pokémon digitando /pwiki",
    "cobbreeding": "Mod auxiliar do Cobblemon para adicionar reprodução de Pokémon.",
    "complete_cobblemon_collection": "O maior pacote de addons do Cobblemon com modelos, spawns e animações para TODOS OS POKÉMON.",
    "easy_npc": "Crie NPCs com diálogos facilmente para o seu mundo ou mods.",
    "emotecraft": "Crie suas próprias emotes no Minecraft.",
    "explorers_compass": "Permite localizar estruturas em qualquer lugar do mundo.",
    "falling_tree": "Derrube árvores inteiras cortando apenas um bloco",
    "ferritecore": "Otimizações de uso de memória RAM",
    "furniture": "A próxima geração do Furniture Mod do MrCrayfish, redesenhado do zero com novos modelos, sons e muito mais!",
    "global_datapacks": "Adiciona uma pasta de datapacks compartilhada que funciona em todos os seus mundos.",
    "immersive_melodies": "Toque melodias personalizadas em vários instrumentos e irrite seus amigos!",
    "inventory_management": "Organize e transfira itens com o clique de um botão.",
    "iron_chests": "Baús melhorados para o Minecraft",
    "item_obliterator": "Mod utilitário para modpacks que permite desativar itens e suas interações. Remove das abas do criativo, receitas, trocas e JEI/REI/EMI.",
    "jade": "Mostra informações sobre o que você está olhando. (Fork de Hwyla/Waila para Minecraft 1.16+)",
    "jei": "Visualize Itens e Receitas",
    "luckys_cozy_home": "Adiciona móveis ao jogo!",
    "macaws_furniture": "Decore seu mundo com guarda-roupas, gavetas, cadeiras, mesas, sofás, pias e muito mais!",
    "mob_lassos": "Mob Lassos adiciona utensílios para mover mobs: crie um laço para transportar a maioria dos mobs no inventário! Sem guias ou comida para animais!",
    "mod_menu": "Adiciona um menu de mods para ver a lista de mods instalados.",
    "modern-fix": "Mod completo que melhora o desempenho, reduz o uso de memória e corrige muitos bugs. Compatível com seus mods de performance favoritos!",
    "natures_compass": "Permite localizar biomas em qualquer lugar do mundo.",
    "only_paxels": "Multitool que combina picareta, machado e pá em uma só ferramenta",
    "pokebadges": "Sistema completo de Insígnias de Academia para o Cobblemon. Armazene, gerencie e rastreie suas insígnias em uma Badge Box dedicada com GUI imersiva.",
    "polymorph": "Sem mais conflitos de receitas! Adiciona a opção de escolher o resultado de crafting quando há mais de um disponível.",
    "radical_cobblemon_trainers": "Mais de 1500 treinadores únicos e desafiadores dos ROM hacks Radical Red (v3.02) e Unbound (v2.0.3.2), além da série principal",
    "simple_tms": "Expansão do Cobblemon que integra TMs (Máquinas Técnicas) e TRs (Registros Técnicos) do universo Pokémon.",
    "simple_voice_chat": "Um chat de voz funcionando dentro do Minecraft!",
    "starter_kit": "Dê a todos os novos jogadores equipamentos, itens e/ou efeitos de poção iniciais configuráveis",
    "structurify": "Mod de configuração leve para personalizar tudo relacionado a estruturas, sem precisar criar múltiplos datapacks.",
    "supplementaries": "Adições Vanilla+: Jarros, placas de sinalização, torneiras, cataventos, lançadores de mola, suportes, vasos, luzes, decoração e automação",
    "terralith": "Explore quase 100 novos biomas de realismo e fantasia leve, usando apenas blocos Vanilla. Com estruturas imersivas para complementar o terreno renovado.",
    "toms_simple_storage": "Mod de armazenamento simples no estilo vanilla",
    "travelers_backpack": "Mochilas únicas e atualizáveis com personalização, integração com Curios API/Trinkets e muito mais!",
    "visual_workbench": "Os itens ficam dentro das bancadas de trabalho e são renderizados em cima delas. Muito chique!",
    "waterframes": "Adiciona um Quadro e um Projetor onde você insere URLs de vídeo ou imagem e o quadro os exibe",
    "waystones": "Teletransporte de volta a pedras de caminho ativadas. Para Survival, Aventura ou Servidores.",
    "xaeros_minimap": "Exibe um mapa do terreno próximo, jogadores, mobs e entidades no canto da tela. Crie waypoints para marcar locais importantes.",
    "you_shall_not_spawn": "Mod utilitário para modpacks que permite desativar o spawn de qualquer entidade.",
    "za_megas": "Adiciona todas as Mega Evoluções de Pokémon Legends ZA ao Cobblemon!",
    # ── client ────────────────────────────────────────────────────────────
    "3d_skin_layers": "Renderiza a camada de skin do jogador em 3D!",
    "ambient_sounds": "Adiciona uma ambientação sonora rica ao mundo do Minecraft. Suporta engines personalizadas e funciona bem com mods de geração de mundo.",
    "better_ping_display": "Adiciona um display numérico de ping configurável à lista de jogadores",
    "chat_heads": "Veja o avatar de quem está te enviando mensagem!",
    "cobble_sounds": "Adiciona músicas e sons de Pokémon ao Cobblemon!",
    "cobblemon_catch_rate_display": "Calculadora de taxa de captura em tempo real para Cobblemon. Mostra porcentagens ao vivo, comparação de Poké Bolas e efeitos de status. 100% client-side. Funciona em qualquer servidor.",
    "cobblemon_move_inspector": "Inspeção de movimentos durante batalhas, no lado do cliente, para Cobblemon",
    "continuity": "Mod do Minecraft que permite texturas conectadas de forma eficiente",
    "entity_culling": "Usa rastreamento de caminhos assíncrono para ocultar blocos e entidades que não estão visíveis",
    "immediately_fast": "Acelera a renderização de modo imediato no Minecraft",
    "iris_shaders": "Carregador moderno de shader packs para Minecraft, compatível com shader packs existentes do OptiFine",
    "music_control": "Tome controle da música do Minecraft!",
    "not_enough_animations": "Traz animações da primeira pessoa para a terceira pessoa",
    "particular": "Melhora a ambientação do Minecraft com efeitos visuais artesanais como vaga-lumes, folhas caindo e cascatas",
    "sodium": "O mod de otimização de renderização mais rápido e compatível para Minecraft. Disponível para NeoForge e Fabric!",
    "sounds_be_gone": "Permite desativar sons específicos que você não gosta. Perfeito para pessoas com Misofonia!",
    "zoomify": "Mod de zoom com infinita personalização.",
    # ── server ────────────────────────────────────────────────────────────
    "skin_restorer": "Mod server-side para gerenciar e restaurar skins de jogadores.",
}

ROOT = Path(__file__).parent
updated = skipped = missing = 0

for json_file in sorted(ROOT.rglob("*-info.json")):
    slug = json_file.stem.removesuffix("-info")
    if slug not in TRANSLATIONS:
        print(f"  MISSING translation: {slug}")
        missing += 1
        continue
    data = json.loads(json_file.read_text(encoding="utf-8"))
    if data.get("description_pt_br") == TRANSLATIONS[slug]:
        skipped += 1
        continue
    data["description_pt_br"] = TRANSLATIONS[slug]
    json_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    updated += 1

print(f"Done — updated: {updated}, skipped: {skipped}, missing translation: {missing}")
