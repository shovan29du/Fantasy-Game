"""D&D 5e Visual Skill Tree — full node graph with attribute prerequisites."""
from __future__ import annotations

ATTR_COLORS = {
    "strength":    "#e53935",
    "dexterity":   "#43a047",
    "constitution":"#fb8c00",
    "intelligence":"#7b1fa2",
    "wisdom":      "#00838f",
    "charisma_stat":"#d81b60",
}

def _n(id,name,desc,tier,level_req,attr_req,parents,children,category,icon):
    return {"id":id,"name":name,"desc":desc,"tier":tier,"level_req":level_req,
            "attr_req":attr_req,"parents":parents,"children":children,"category":category,"icon":icon}

# ── COMBAT (STR / DEX) ─────────────────────────────────────────────
_C=[
 _n("atk_basic","Basic Attack","Standard weapon attack action.",1,1,{},[]
    ,["pwr_strike","qck_strike","wpn_focus"],"combat","⚔"),
 _n("unarmed","Unarmed Strike","Proficiency with fists; 1+STR mod damage.",1,1,{},[]
    ,["grapple","tavern_brawl"],"combat","👊"),
 _n("fighting_stance","Fighting Stance","Choose a fighting style (Dueling, GWF, Archery).",1,1,{"strength":10},[]
    ,["def_stance","pwr_stance","archery_stance"],"combat","🛡"),
 _n("pwr_strike","Power Strike","−5 hit / +10 damage on melee attacks.",2,3,{"strength":13},["atk_basic"]
    ,["great_cleave","crushing_blow"],"combat","💥"),
 _n("qck_strike","Quick Strike","Bonus-action light weapon attack.",2,3,{"dexterity":13},["atk_basic"]
    ,["dual_wield","flurry"],"combat","⚡"),
 _n("wpn_focus","Weapon Focus","+2 to hit with one weapon type.",2,3,{"strength":12},["atk_basic"]
    ,["wpn_mastery","precision"],"combat","🎯"),
 _n("grapple","Grapple Expert","Adv. grapple checks; restrain on hit.",2,3,{"strength":13},["unarmed"]
    ,["pin_down"],"combat","✊"),
 _n("tavern_brawl","Tavern Brawler","+1 STR; prof with improvised weapons.",2,3,{"strength":11},["unarmed"]
    ,["brutal_brawler"],"combat","🍺"),
 _n("def_stance","Defensive Stance","Dodge also imposes disadvantage on attackers.",2,3,{"constitution":12},["fighting_stance"]
    ,["iron_guard","riposte"],"combat","🛡"),
 _n("pwr_stance","Power Stance","+5 damage / −2 AC until next turn.",2,3,{"strength":13},["fighting_stance"]
    ,["great_cleave"],"combat","💪"),
 _n("archery_stance","Archery Stance","+2 to ranged attack rolls.",2,3,{"dexterity":13},["fighting_stance"]
    ,["sharpshooter","multishot"],"combat","🏹"),
 _n("great_cleave","Great Cleave","On kill, free attack on adjacent enemy.",3,7,{"strength":16},["pwr_strike","pwr_stance"]
    ,["whirlwind"],"combat","🌀"),
 _n("crushing_blow","Crushing Blow","Hit knocks prone (CON save DC 14+STR mod).",3,7,{"strength":16},["pwr_strike"]
    ,["execution"],"combat","💢"),
 _n("dual_wield","Dual Wielder","+1 AC dual-wielding; use non-light off-hand.",3,7,{"dexterity":15},["qck_strike"]
    ,["blade_dance"],"combat","⚔⚔"),
 _n("flurry","Flurry of Blows","1 ki: 2 bonus unarmed attacks.",3,7,{"dexterity":16},["qck_strike"]
    ,["shadow_strike"],"combat","🌊"),
 _n("precision","Precision Strike","Add prof bonus to damage once per turn.",3,7,{"dexterity":14},["wpn_focus"]
    ,["blade_dance"],"combat","🔪"),
 _n("wpn_mastery","Weapon Mastery","+4 damage; unlock weapon's special property.",3,7,{"strength":14},["wpn_focus"]
    ,["legendary_blade"],"combat","⭐"),
 _n("riposte","Riposte","Reaction counter-attack when missed.",3,7,{"dexterity":14},["def_stance"]
    ,["parry_master"],"combat","↩"),
 _n("sharpshooter","Sharpshooter","No cover penalty; −5/+10 ranged option.",3,7,{"dexterity":16},["archery_stance"]
    ,["arrow_rain"],"combat","🏹"),
 _n("multishot","Multishot","One attack action targets up to 3 enemies.",3,7,{"dexterity":15},["archery_stance"]
    ,["arrow_rain"],"combat","🎪"),
 _n("pin_down","Pin Down","Restrained foe halved speed even after escape.",3,7,{"strength":15},["grapple"]
    ,["iron_grip"],"combat","📌"),
 _n("brutal_brawler","Brutal Brawler","Unarmed 1d6+STR; bonus second attack.",3,7,{"strength":15},["tavern_brawl"]
    ,["iron_fist"],"combat","🤛"),
 _n("iron_guard","Iron Guard","Reduce all damage by prof bonus.",3,7,{"constitution":15},["def_stance"]
    ,["unbreakable"],"combat","⚙"),
 _n("whirlwind","Whirlwind Attack","Attack every adjacent creature in one action.",4,15,{"strength":18},["great_cleave"],[],"combat","🌪"),
 _n("execution","Execution Strike","Max damage vs targets below 25 % HP.",4,15,{"strength":18},["crushing_blow"],[],"combat","☠"),
 _n("blade_dance","Blade Dance","Bonus-action double attack after main attack action.",4,15,{"dexterity":18},["dual_wield","precision"],[],"combat","💫"),
 _n("shadow_strike","Shadow Strike","Attack without breaking stealth; +3d6 sneak.",4,15,{"dexterity":18},["flurry"],[],"combat","🌑"),
 _n("arrow_rain","Arrow Rain","Volley hits all enemies in 20 ft radius.",4,15,{"dexterity":18},["sharpshooter","multishot"],[],"combat","☔"),
 _n("iron_fist","Iron Fist","Unarmed 2d8+STR; counts as magical.",4,15,{"strength":18},["brutal_brawler"],[],"combat","👊⭐"),
 _n("unbreakable","Unbreakable","Once/long rest drop to 1 instead of 0.",4,15,{"constitution":18},["iron_guard"],[],"combat","💎"),
 _n("legendary_blade","Legendary Blade","Mastered weapon deals +1d10+5.",4,15,{"strength":17},["wpn_mastery"],[],"combat","👑⚔"),
 _n("parry_master","Parry Master","Reduce any single melee hit by 1d10+DEX mod.",4,15,{"dexterity":17},["riposte"],[],"combat","🌟"),
 _n("iron_grip","Iron Grip","Escape grapple requires 3 STR checks not 1.",4,15,{"strength":17},["pin_down"],[],"combat","⛓"),
]

# ── DEFENSE (CON / STR) ────────────────────────────────────────────
_D=[
 _n("tough_skin","Tough Skin","+2 natural AC (doesn't stack with armor).",1,1,{"constitution":10},[]
    ,["fortitude","dmg_resist"],"defense","🛡"),
 _n("shield_prof","Shield Mastery","React to deflect 1d6 damage.",1,1,{"strength":10},[]
    ,["shield_wall","shield_bash"],"defense","🗡"),
 _n("heavy_armor","Armor Training","Heavy armor prof; no stealth penalty.",1,1,{"strength":12},[]
    ,["full_plate","bulwark"],"defense","⚙"),
 _n("endure","Endurance","+2 to all CON saving throws.",1,1,{"constitution":11},[]
    ,["fortitude","iron_will"],"defense","💪"),
 _n("fortitude","Fortitude","Adv. saves vs poison, disease, exhaustion.",2,3,{"constitution":13},["tough_skin","endure"]
    ,["iron_const","stalwart"],"defense","⚡"),
 _n("dmg_resist","Damage Reduction","Reduce all physical damage by 2.",2,3,{"constitution":13},["tough_skin"]
    ,["juggernaut"],"defense","🔮"),
 _n("shield_wall","Shield Wall","+2 AC when adjacent to an ally.",2,3,{"strength":13},["shield_prof"]
    ,["tower_shield","shield_expert"],"defense","🏰"),
 _n("shield_bash","Shield Bash","Shield as weapon 1d6+STR; push 5 ft.",2,3,{"strength":13},["shield_prof"]
    ,["shield_expert"],"defense","💥"),
 _n("full_plate","Full Plate","+1 AC in plate; resistance to slashing.",2,3,{"strength":15},["heavy_armor"]
    ,["living_fortress"],"defense","🔩"),
 _n("bulwark","Bulwark","Can't be forced to move while stationary.",2,3,{"strength":14},["heavy_armor"]
    ,["iron_bastion"],"defense","⚓"),
 _n("iron_will","Iron Will","+2 mental saves vs enchantment.",2,3,{"constitution":12},["endure"]
    ,["stalwart"],"defense","🧠"),
 _n("iron_const","Iron Constitution","Immunity to poison; adv. death saves.",3,7,{"constitution":16},["fortitude"]
    ,["immortal"],"defense","⚙"),
 _n("stalwart","Stalwart","Reduce crits to normal hits once/combat.",3,7,{"constitution":15},["fortitude","iron_will"]
    ,["immortal"],"defense","🛡"),
 _n("juggernaut","Juggernaut","Move through enemies; no OAs while moving.",3,7,{"constitution":16},["dmg_resist"]
    ,["immortal"],"defense","🏋"),
 _n("tower_shield","Tower Shield","+3 AC from shield; half cover for ally.",3,7,{"strength":16},["shield_wall"]
    ,["impenetrable"],"defense","🏰"),
 _n("shield_expert","Shield Expert","Bonus-action shield bash on attack action.",3,7,{"strength":15},["shield_wall","shield_bash"]
    ,["impenetrable"],"defense","🌟"),
 _n("living_fortress","Living Fortress","Aura: adjacent allies +1 AC.",3,7,{"strength":17},["full_plate"]
    ,["godlike_def"],"defense","🏯"),
 _n("iron_bastion","Iron Bastion","Full cover behind shield as free action.",3,7,{"strength":16},["bulwark"]
    ,["godlike_def"],"defense","🔒"),
 _n("immortal","Immortal Stance","Half damage from all sources once/combat (reaction).",4,15,{"constitution":18},["iron_const","stalwart","juggernaut"],[],"defense","✨"),
 _n("impenetrable","Impenetrable","Block any single hit once per round.",4,15,{"strength":18},["tower_shield","shield_expert"],[],"defense","🔱"),
 _n("godlike_def","Godlike Defense","Resistance to all damage types while armored.",4,15,{"constitution":18},["living_fortress","iron_bastion"],[],"defense","👑"),
]

# ── MOVEMENT (DEX / STR) ───────────────────────────────────────────
_M=[
 _n("sprinter","Sprinter","+10 ft speed; dash as bonus action once/combat.",1,1,{"dexterity":10},[]
    ,["fleet_foot","blur"],"movement","💨"),
 _n("climber","Climber","Climb at full speed; skip easy climb checks.",1,1,{"strength":10},[]
    ,["wall_runner","free_climber"],"movement","🧗"),
 _n("jumper","High Jumper","Long jump 15+STR ft; high jump 5+STR/2 ft.",1,1,{"strength":11},[]
    ,["sky_leap","wall_runner"],"movement","⬆"),
 _n("swimmer","Swimmer","Swim full speed; hold breath ×2.",1,1,{"constitution":10},[]
    ,["deep_diver"],"movement","🌊"),
 _n("evasion_base","Evasion","AoE saves: half on fail, none on success.",1,1,{"dexterity":11},[]
    ,["phase_step","blur"],"movement","👁"),
 _n("fleet_foot","Fleet of Foot","+20 ft speed; speed can't be reduced below base.",2,3,{"dexterity":13},["sprinter"]
    ,["wind_step","fleet_master"],"movement","💨"),
 _n("blur","Blur Motion","Attackers have disadvantage first round of combat.",2,3,{"dexterity":14},["sprinter","evasion_base"]
    ,["phase_step","wind_step"],"movement","🌀"),
 _n("wall_runner","Wall Runner","Run along vertical surfaces at half speed.",2,3,{"dexterity":13},["climber","jumper"]
    ,["vertical_assault"],"movement","🧱"),
 _n("free_climber","Free Climber","Climb overhangs; ignore difficult terrain.",2,3,{"strength":13},["climber"]
    ,["sky_leap"],"movement","🕷"),
 _n("sky_leap","Sky Leap","Jump ×2 distance; no fall damage ≤60 ft.",2,3,{"strength":15},["jumper","free_climber"]
    ,["levitate_jump"],"movement","🌤"),
 _n("phase_step","Phase Step","Teleport ≤15 ft as bonus action once/round.",2,3,{"dexterity":16},["evasion_base","blur"]
    ,["shadow_walk"],"movement","✨"),
 _n("deep_diver","Deep Diver","Breathe underwater; swim speed = move speed.",2,3,{"constitution":12},["swimmer"]
    ,["water_walk"],"movement","🐟"),
 _n("wind_step","Wind Step","+30 ft speed; ignore difficult terrain.",3,7,{"dexterity":16},["fleet_foot","blur"]
    ,["wind_walker"],"movement","🌪"),
 _n("fleet_master","Fleet Master","Two bonus dashes/combat; no OAs while dashing.",3,7,{"dexterity":16},["fleet_foot"]
    ,["wind_walker"],"movement","⚡"),
 _n("vertical_assault","Vertical Assault","Attack from wall/ceiling with advantage.",3,7,{"dexterity":15},["wall_runner"]
    ,["levitate_jump"],"movement","⬆⚔"),
 _n("levitate_jump","Levitate","Float 10 ft; negate all fall damage.",3,7,{"dexterity":16},["sky_leap","vertical_assault"]
    ,["teleport_mastery"],"movement","🕊"),
 _n("shadow_walk","Shadow Walk","Teleport between shadows ≤60 ft as bonus action.",3,7,{"dexterity":17},["phase_step"]
    ,["ethereal_form"],"movement","🌑"),
 _n("water_walk","Water Walking","Walk on liquid; swim ×2 speed.",3,7,{"constitution":14},["deep_diver"]
    ,["elemental_move"],"movement","🌊"),
 _n("wind_walker","Wind Walker","Move through walls once/turn; speed ×2.",4,15,{"dexterity":18},["wind_step","fleet_master"],[],"movement","🌬"),
 _n("teleport_mastery","Teleport","Teleport ≤60 ft as movement action; no LoS needed.",4,15,{"dexterity":18},["levitate_jump"],[],"movement","🌌"),
 _n("ethereal_form","Ethereal Form","Move through walls; invisible while moving (1 round/long rest).",4,15,{"dexterity":18},["shadow_walk"],[],"movement","👻"),
 _n("elemental_move","Elemental Movement","Fly 60 ft, swim 60 ft, or burrow 30 ft (choose one).",4,15,{"constitution":17},["water_walk"],[],"movement","🌍"),
]

# ── MAGIC (INT / WIS / CHA) ────────────────────────────────────────
_MG=[
 _n("cantrip_mastery","Cantrip Mastery","Cantrips as bonus action; damage scales +1 die.",1,1,{"intelligence":10},[]
    ,["spell_focus","arcane_theory"],"magic","✨"),
 _n("divine_favor","Divine Favor","+1d4 radiant after prayer; 10 ft radius.",1,1,{"wisdom":10},[]
    ,["healing_touch","sacred_aura"],"magic","☀"),
 _n("bardic_basic","Bardic Inspiration","Give ally a d6 inspiration die once/short rest.",1,1,{"charisma_stat":10},[]
    ,["inspire","song_of_rest"],"magic","🎵"),
 _n("mana_sense","Mana Sense","Detect magic 60 ft at will; identify spells.",1,1,{"intelligence":11},[]
    ,["arcane_theory","counter_spell"],"magic","🔮"),
 _n("wild_magic_root","Wild Magic","Spells: 20% chance of beneficial surge.",1,1,{"charisma_stat":11},[]
    ,["wild_surge","chaos_weaving"],"magic","🌈"),
 _n("spell_focus","Spell Focus","+2 spell attack; spell save DC +1.",2,3,{"intelligence":13},["cantrip_mastery"]
    ,["evocation_mastery","illusion_expert"],"magic","🔮"),
 _n("arcane_theory","Arcane Theory","+2 spells/level prepared; ritual-cast any known spell.",2,3,{"intelligence":13},["cantrip_mastery","mana_sense"]
    ,["metamagic","spellbook_exp"],"magic","📚"),
 _n("healing_touch","Healing Touch","Channel Divinity: heal 2d8+WIS (action).",2,3,{"wisdom":13},["divine_favor"]
    ,["greater_healing","life_ward"],"magic","💚"),
 _n("sacred_aura","Sacred Aura","Allies ≤10 ft: +1 to saving throws.",2,3,{"wisdom":13},["divine_favor"]
    ,["holy_light","divine_intervention"],"magic","✨"),
 _n("inspire","Grand Inspiration","Inspiration die → d8; affect 3 allies/rest.",2,3,{"charisma_stat":13},["bardic_basic"]
    ,["song_battle","cutting_words"],"magic","🎶"),
 _n("song_of_rest","Song of Rest","Short rests: allies regain extra 1d6 HP.",2,3,{"charisma_stat":12},["bardic_basic"]
    ,["song_battle"],"magic","🎵"),
 _n("wild_surge","Wild Surge","Surge chance 30%; surges always benefit you.",2,3,{"charisma_stat":14},["wild_magic_root"]
    ,["chaos_weaving","surge_control"],"magic","🌊"),
 _n("counter_spell","Counterspell","React to cancel any spell being cast (level 3–7).",2,3,{"intelligence":14},["mana_sense"]
    ,["dispel_mastery"],"magic","⛔"),
 _n("evocation_mastery","Evocation Mastery","Maximize one damage die/spell; allies exempt from AoE.",3,7,{"intelligence":16},["spell_focus"]
    ,["arcane_bombardment"],"magic","💥"),
 _n("illusion_expert","Illusion Expert","Illusions have substance; disbelief needs INT check.",3,7,{"intelligence":15},["spell_focus"]
    ,["mirage_master"],"magic","👁"),
 _n("metamagic","Metamagic","4 sorcery points; Quickened, Twinned, Extended spells.",3,7,{"intelligence":15},["arcane_theory"]
    ,["spellstorm"],"magic","⚡"),
 _n("spellbook_exp","Expanded Spellbook","Prepare INT mod extra spells; access one extra school.",3,7,{"intelligence":16},["arcane_theory"]
    ,["spellstorm"],"magic","📖"),
 _n("greater_healing","Greater Healing","Heal 4d8+WIS; revive unconscious as action.",3,7,{"wisdom":16},["healing_touch"]
    ,["miracle"],"magic","💊"),
 _n("life_ward","Life Ward","Auto-stabilize adjacent allies at 0 HP.",3,7,{"wisdom":15},["healing_touch"]
    ,["miracle"],"magic","💛"),
 _n("holy_light","Holy Light","Radiant burst: 3d8 to undead/fiends in 30 ft.",3,7,{"wisdom":16},["sacred_aura"]
    ,["divine_intervention"],"magic","☀"),
 _n("song_battle","Song of Battle","Allies hearing you: +1 attack and +1d4 damage.",3,7,{"charisma_stat":15},["inspire","song_of_rest"]
    ,["voice_nations"],"magic","🎺"),
 _n("cutting_words","Cutting Words","React: subtract Inspiration die from enemy roll.",3,7,{"charisma_stat":14},["inspire"]
    ,["voice_nations"],"magic","🗡"),
 _n("chaos_weaving","Chaos Weaving","Choose from 3 surge results; bend wild magic.",3,7,{"charisma_stat":16},["wild_magic_root","wild_surge"]
    ,["wild_incarnate"],"magic","🌀"),
 _n("surge_control","Surge Control","Trigger surge deliberately once/short rest.",3,7,{"charisma_stat":15},["wild_surge"]
    ,["wild_incarnate"],"magic","🎲"),
 _n("dispel_mastery","Dispel Mastery","Auto-dispel spells of 5th level or lower.",3,7,{"intelligence":16},["counter_spell"]
    ,["arcane_bombardment"],"magic","💨"),
 _n("divine_intervention","Divine Intervention","Once/week: call deity for a major miraculous effect.",3,7,{"wisdom":17},["holy_light","sacred_aura"]
    ,["miracle"],"magic","🙏"),
 _n("arcane_bombardment","Arcane Bombardment","Cast 2nd spell as bonus action without concentration conflict.",4,15,{"intelligence":18},["evocation_mastery","metamagic","spellbook_exp","dispel_mastery"],[],"magic","💫"),
 _n("miracle","Miracle","Replicate any divine spell or intervention (once/month).",4,15,{"wisdom":18},["greater_healing","life_ward","divine_intervention"],[],"magic","⭐"),
 _n("wild_incarnate","Wild Incarnate","Cast any spell from any class list once/day.",4,15,{"charisma_stat":18},["chaos_weaving","surge_control"],[],"magic","🌈"),
 _n("mirage_master","Mirage Master","Create 1-mile illusory landscape; deals real damage.",4,15,{"intelligence":18},["illusion_expert"],[],"magic","🏔"),
 _n("spellstorm","Spellstorm","Cast 3 spells simultaneously on same turn (1/day).",4,15,{"intelligence":18},["metamagic","spellbook_exp"],[],"magic","⛈"),
 _n("voice_nations","Voice of Nations","Charm an entire crowd; command armies without combat.",4,15,{"charisma_stat":18},["song_battle","cutting_words"],[],"magic","📯"),
]

# ── STEALTH (DEX) ─────────────────────────────────────────────────
_ST=[
 _n("sneak_basic","Stealth","Hide in dim light/cover; adv. stealth checks.",1,1,{"dexterity":10},[]
    ,["shadow_step","ambush"],"stealth","👤"),
 _n("pickpocket","Sleight of Hand","Pick pockets with adv.; 90% vs unaware.",1,1,{"dexterity":10},[]
    ,["cutpurse","cat_burglar"],"stealth","👐"),
 _n("disguise_basic","Disguise Self","Adopt another appearance; +2 Deception.",1,1,{"charisma_stat":10},[]
    ,["master_faces","infiltrator"],"stealth","🎭"),
 _n("trap_sense","Trap Sense","Passive trap detect; adv. disarming checks.",1,1,{"intelligence":10},[]
    ,["trap_expert","scout"],"stealth","🕵"),
 _n("lockpick","Lockpicking","Pick locks; silence any mechanism 1 hr.",1,1,{"dexterity":11},[]
    ,["cat_burglar","master_thief"],"stealth","🔑"),
 _n("shadow_step","Shadow Step","Teleport between shadows ≤15 ft (bonus action).",2,3,{"dexterity":13},["sneak_basic"]
    ,["vanish","greater_invis"],"stealth","🌑"),
 _n("ambush","Ambush Expert","Attacks vs unaware: +2d6 sneak damage.",2,3,{"dexterity":13},["sneak_basic"]
    ,["assassinate"],"stealth","🗡"),
 _n("cutpurse","Master Cutpurse","Steal from combat targets as bonus action.",2,3,{"dexterity":13},["pickpocket"]
    ,["master_thief"],"stealth","💰"),
 _n("cat_burglar","Cat Burglar","Climb walls silently; no check ≤15 ft falls.",2,3,{"dexterity":14},["pickpocket","lockpick"]
    ,["phantom_thief"],"stealth","🐱"),
 _n("master_faces","Master of Faces","Perfectly imitate any person; adv. disguise.",2,3,{"charisma_stat":13},["disguise_basic"]
    ,["infiltrator","changeling"],"stealth","🎭"),
 _n("infiltrator","Infiltrator","Blend into any organization; forge credentials.",2,3,{"charisma_stat":13},["disguise_basic"]
    ,["changeling","spy_master"],"stealth","🕵"),
 _n("trap_expert","Trap Expert","Disarm any trap without failure; set traps as bonus action.",2,3,{"intelligence":13},["trap_sense"]
    ,["bomb_maker","spy_master"],"stealth","⚙"),
 _n("scout","Scout","Move at full speed while hidden; Passive Perc +5.",2,3,{"dexterity":13},["trap_sense"]
    ,["phantom_thief"],"stealth","🔭"),
 _n("master_thief","Master Thief","Auto-succeed common locks; +3d6 sneak attacks.",2,3,{"dexterity":14},["lockpick","cutpurse"]
    ,["phantom_thief"],"stealth","🔓"),
 _n("vanish","Vanish","Invisible at will as bonus action (1 min, 3/long rest).",3,7,{"dexterity":16},["shadow_step"]
    ,["greater_invis"],"stealth","👻"),
 _n("greater_invis","Greater Invisibility","Stay invisible even while attacking. Full minute.",3,7,{"dexterity":17},["shadow_step","vanish"]
    ,["shadow_god"],"stealth","🌑"),
 _n("assassinate","Assassinate","Auto-critical on surprised target.",3,7,{"dexterity":16},["ambush"]
    ,["death_strike"],"stealth","☠"),
 _n("phantom_thief","Phantom Thief","Steal magical items without triggering wards.",3,7,{"dexterity":16},["cat_burglar","scout","master_thief"]
    ,["shadow_god"],"stealth","👻"),
 _n("changeling","Changeling","Permanently adopt any appearance; voice & scent match.",3,7,{"charisma_stat":16},["master_faces","infiltrator"]
    ,["spy_master"],"stealth","🎭"),
 _n("spy_master","Spy Master","Build spy network; gather info on anyone.",3,7,{"intelligence":15},["infiltrator","trap_expert"]
    ,["shadow_god"],"stealth","🕸"),
 _n("bomb_maker","Alchemist","Craft potions and explosives; +2d6 blast.",3,7,{"intelligence":15},["trap_expert"]
    ,["grand_alchemist"],"stealth","⚗"),
 _n("death_strike","Death Strike","Crit: target saves vs death or drops to 0 HP.",3,7,{"dexterity":17},["assassinate"]
    ,["shadow_god"],"stealth","💀"),
 _n("shadow_god","Shadow God","Can't be detected magically; perfect stealth in light.",4,15,{"dexterity":18},["greater_invis","phantom_thief","spy_master","death_strike"],[],"stealth","🌑"),
 _n("grand_alchemist","Grand Alchemist","Craft any potion including legendary (1/week).",4,15,{"intelligence":17},["bomb_maker"],[],"stealth","🔮"),
]

# ── SOCIAL / UTILITY (CHA / INT / WIS) ────────────────────────────
_SO=[
 _n("persuasion","Persuasion","+2 Persuasion; NPCs start one disposition better.",1,1,{"charisma_stat":10},[]
    ,["silver_tongue","diplomat_basic"],"social","💬"),
 _n("intimidation","Intimidation","Frighten one enemy (bonus action; WIS save).",1,1,{"charisma_stat":10},[]
    ,["battle_shout","authority"],"social","😠"),
 _n("deception","Deception","+2 Deception; convincingly lie about anything.",1,1,{"charisma_stat":10},[]
    ,["silver_tongue","con_artist"],"social","🎭"),
 _n("investigation","Investigation","+2 Investigation; find clues in half time.",1,1,{"intelligence":10},[]
    ,["deduction","lorekeeper"],"social","🔍"),
 _n("insight","Insight","+2 Insight; auto-detect lies on nat 15+.",1,1,{"wisdom":10},[]
    ,["empathy","read_person"],"social","👁"),
 _n("medicine","Medicine","Stabilize without healer's kit; diagnose poisons.",1,1,{"wisdom":10},[]
    ,["field_medic","herbalist"],"social","⚕"),
 _n("survival_skill","Survival","Track creatures; find food and shelter.",1,1,{"wisdom":11},[]
    ,["ranger_lore","pathfinder"],"social","🌲"),
 _n("crafting","Crafting","Create basic items; repair damaged equipment.",1,1,{"intelligence":10},[]
    ,["master_crafter","engineering"],"social","🔨"),
 _n("silver_tongue","Silver Tongue","Treat hostile NPCs as neutral; reroll fail once/day.",2,3,{"charisma_stat":13},["persuasion","deception"]
    ,["master_negotiator","con_master"],"social","💫"),
 _n("battle_shout","Battle Shout","Grant allies +1d6 attacks for 1 round (bonus action).",2,3,{"charisma_stat":13},["intimidation"]
    ,["warcry","authority"],"social","📣"),
 _n("authority","Authority","Lower-status NPCs auto-comply with requests.",2,3,{"charisma_stat":13},["intimidation"]
    ,["political_power"],"social","👑"),
 _n("con_artist","Con Artist","Sell worthless items as valuable; perfect forgery.",2,3,{"charisma_stat":13},["deception"]
    ,["master_negotiator","con_master"],"social","🃏"),
 _n("diplomat_basic","Diplomat","Avoid combat with Persuasion check vs CR/level.",2,3,{"charisma_stat":12},["persuasion"]
    ,["grand_diplomat"],"social","🤝"),
 _n("deduction","Deduction","Solve puzzles/mysteries; INT 10+ = auto-success.",2,3,{"intelligence":13},["investigation"]
    ,["brilliant_analysis","engineer_mastery"],"social","🧩"),
 _n("lorekeeper","Lorekeeper","Know history, mythology, arcana on INT check.",2,3,{"intelligence":13},["investigation"]
    ,["historian","linguist"],"social","📜"),
 _n("empathy","Empathy","Know emotional state of any creature.",2,3,{"wisdom":13},["insight"]
    ,["read_mind","counselor"],"social","💛"),
 _n("read_person","Read Person","Learn one truth on successful Insight.",2,3,{"wisdom":13},["insight"]
    ,["counselor","detect_lies"],"social","👤"),
 _n("field_medic","Field Medic","Heal 2d8 HP as action (3/long rest).",2,3,{"wisdom":13},["medicine"]
    ,["battlefield_surgeon"],"social","🏥"),
 _n("herbalist","Herbalist","Brew herbal remedies; adv. vs poison/disease.",2,3,{"wisdom":12},["medicine"]
    ,["battlefield_surgeon","botanist"],"social","🌿"),
 _n("ranger_lore","Ranger Lore","Expertise in one terrain type.",2,3,{"wisdom":13},["survival_skill"]
    ,["pathfinder"],"social","🗺"),
 _n("pathfinder","Pathfinder","Lead groups through any terrain without getting lost.",2,3,{"wisdom":13},["survival_skill","ranger_lore"]
    ,["master_pathfinder"],"social","🧭"),
 _n("master_crafter","Master Crafter","Craft simple magic items; identify any non-legendary item.",2,3,{"intelligence":13},["crafting"]
    ,["engineer_mastery","artificer"],"social","⚒"),
 _n("engineering","Engineering","Build siege weapons/fortifications at ×2 speed.",2,3,{"intelligence":13},["crafting"]
    ,["artificer","engineer_mastery"],"social","🏗"),
 _n("linguist","Linguist","Speak 3 extra languages; decipher unknown scripts.",2,3,{"intelligence":13},["lorekeeper"]
    ,["historian"],"social","🗣"),
 _n("master_negotiator","Master Negotiator","Never fail negotiation below DC 25; push DC 30 once/day.",3,7,{"charisma_stat":16},["silver_tongue","con_artist"]
    ,["grand_diplomat"],"social","🤝"),
 _n("con_master","Con Master","Never fail deception below DC 20; perfect forgery.",3,7,{"charisma_stat":16},["silver_tongue","con_artist"]
    ,["grand_diplomat"],"social","🃏"),
 _n("warcry","Warcry","All allies 60 ft gain adv. on next attack (bonus action).",3,7,{"charisma_stat":15},["battle_shout"]
    ,["legendary_leader"],"social","📣"),
 _n("political_power","Political Power","Gain political rank or noble title.",3,7,{"charisma_stat":16},["authority"]
    ,["legendary_leader","empire_builder"],"social","🏛"),
 _n("brilliant_analysis","Brilliant Analysis","ID enemy weakness; +1d8 damage on studied target.",3,7,{"intelligence":16},["deduction"]
    ,["tactical_genius"],"social","🧠"),
 _n("historian","Grand Historian","Know any event; predict future from patterns.",3,7,{"intelligence":15},["lorekeeper","linguist"]
    ,["sage_lore"],"social","📚"),
 _n("read_mind","Mind Reading","Sense surface thoughts 30 ft (WIS save).",3,7,{"wisdom":16},["empathy"]
    ,["psychic_link"],"social","🧠"),
 _n("counselor","Master Counselor","Advice grants permanent buffs in story context.",3,7,{"wisdom":15},["empathy","read_person"]
    ,["psychic_link"],"social","🌟"),
 _n("detect_lies","Lie Detector","Auto-know when anyone lies to you within 30 ft.",3,7,{"wisdom":16},["read_person"]
    ,["psychic_link"],"social","👁"),
 _n("battlefield_surgeon","Battlefield Surgeon","Restore 4d8+WIS; remove negative conditions.",3,7,{"wisdom":16},["field_medic","herbalist"]
    ,["legendary_healer"],"social","🏥"),
 _n("botanist","Master Botanist","Craft potions with ×2 effect; identify all plants.",3,7,{"wisdom":14},["herbalist"]
    ,["legendary_healer"],"social","🌱"),
 _n("master_pathfinder","Master Pathfinder","Can't get lost; lead armies through impossible terrain.",3,7,{"wisdom":16},["pathfinder"]
    ,["nature_sense"],"social","🗺"),
 _n("engineer_mastery","Siege Engineer","Build mechanical constructs; create magical devices.",3,7,{"intelligence":16},["engineering","master_crafter"]
    ,["grand_artificer"],"social","⚙"),
 _n("artificer","Artificer","Infuse items with magic; hold 3 infusions at once.",3,7,{"intelligence":16},["engineering","master_crafter"]
    ,["grand_artificer"],"social","⚗"),
 _n("tactical_genius","Tactical Genius","Once/combat: set perfect tactic → party +2 all rolls.",3,7,{"intelligence":17},["brilliant_analysis"]
    ,["grand_strategist"],"social","♟"),
 _n("sage_lore","Sage","Research any topic to perfection; write teaching tomes.",3,7,{"intelligence":16},["historian"]
    ,["grand_strategist"],"social","📖"),
 _n("grand_diplomat","Grand Diplomat","Start and end wars through words; nations respect you.",4,15,{"charisma_stat":18},["master_negotiator","con_master","diplomat_basic"],[],"social","🏛"),
 _n("legendary_leader","Legendary Leader","Legendary speech: allies immune to fear, +2 all rolls (1 hr).",4,15,{"charisma_stat":18},["warcry","political_power"],[],"social","👑"),
 _n("empire_builder","Empire Builder","Build organizations; govern territories.",4,15,{"charisma_stat":17},["political_power"],[],"social","🏰"),
 _n("grand_strategist","Grand Strategist","Predict and counter any enemy plan; party +3 combat rolls.",4,15,{"intelligence":18},["tactical_genius","sage_lore"],[],"social","🧠"),
 _n("psychic_link","Psychic Network","Mental link with ≤10 allies; share senses telepathically.",4,15,{"wisdom":18},["read_mind","counselor","detect_lies"],[],"social","💭"),
 _n("legendary_healer","Legendary Healer","Revive dead once/week; all healing doubled.",4,15,{"wisdom":18},["battlefield_surgeon","botanist"],[],"social","✨"),
 _n("nature_sense","Nature Sense","Commune with nature spirits; animals ally; predict disasters.",4,15,{"wisdom":17},["master_pathfinder"],[],"social","🌿"),
 _n("grand_artificer","Grand Artificer","Create legendary artifacts given materials (1 week).",4,15,{"intelligence":18},["engineer_mastery","artificer"],[],"social","⚗"),
]

# ── Compile ────────────────────────────────────────────────────────
ALL_NODES: dict[str,dict] = {}
for _node in _C+_D+_M+_MG+_ST+_SO:
    ALL_NODES[_node["id"]] = _node

CATEGORIES = ["combat","defense","movement","magic","stealth","social"]
CATEGORY_LABELS = {"combat":"Combat","defense":"Defense","movement":"Movement",
                   "magic":"Magic","stealth":"Stealth","social":"Social & Utility"}
CATEGORY_ICONS  = {"combat":"⚔","defense":"🛡","movement":"💨",
                   "magic":"✨","stealth":"👤","social":"💬"}

def get_category_nodes(category: str) -> list[dict]:
    return [n for n in ALL_NODES.values() if n["category"]==category]

def can_unlock(node_id: str, unlocked: list[str], char_stats: dict, char_level: int) -> tuple[bool,str]:
    """Check whether a node can be unlocked. Returns (ok, reason)."""
    node = ALL_NODES.get(node_id)
    if not node: return False,"Unknown skill"
    if node_id in unlocked: return False,"Already unlocked"
    if char_level < node["level_req"]:
        return False, f"Requires level {node['level_req']}"
    for attr,val in node["attr_req"].items():
        if char_stats.get(attr,10) < val:
            return False, f"Requires {attr.replace('_stat','')} {val}"
    for pid in node["parents"]:
        if pid not in unlocked:
            pname = ALL_NODES.get(pid,{}).get("name",pid)
            return False, f"Requires '{pname}' first"
    return True,""
