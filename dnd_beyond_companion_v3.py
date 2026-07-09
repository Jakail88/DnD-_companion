import os
import json
import time
import random
import numpy as np
import streamlit as st

# ==========================================
# PAGE CONFIG & PALETTE
# ==========================================
st.set_page_config(
    page_title="D&D Beyond Interactive Companion",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-fidelity immersion (Parchment panels, crimson/gold highlights, custom metrics)
st.markdown("""
    <style>
    /* Main Background & Text styling */
    .stApp {
        background-color: #120c08;
        color: #e6dfc8;
        font-family: 'Georgia', 'Times New Roman', serif;
    }
    
    /* Parchment style cards */
    .parchment-card {
        background-color: #f7ebd3;
        color: #2e1d11;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #b88d40;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        margin-bottom: 20px;
    }
    
    /* Stat box (D&D Beyond Style block metrics) */
    .beyond-stat-box {
        background-color: #fcf6e8;
        border: 2px solid #8c1919;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        box-shadow: inset 0 0 6px rgba(140, 25, 25, 0.15);
        margin-bottom: 10px;
    }
    .stat-lbl {
        font-size: 0.75rem;
        font-weight: bold;
        color: #8c1919;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stat-val-mod {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1c1109;
        margin: 2px 0;
    }
    .stat-val-score {
        font-size: 0.85rem;
        background-color: #2e1d11;
        color: #f7ebd3;
        border-radius: 12px;
        display: inline-block;
        padding: 1px 8px;
        font-weight: bold;
    }

    /* Red Titles with ancient fantasy fonts */
    h1, h2, h3 {
        color: #b31b1b !important;
        font-family: 'Georgia', serif;
        font-weight: bold !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }
    
    /* Streamlit Tab customized labels */
    div.stTabs [data-baseweb="tab"] {
        color: #c9bfab !important;
        font-weight: bold !important;
        background-color: transparent !important;
        border-bottom: 2px solid transparent !important;
    }
    div.stTabs [data-baseweb="tab"]:hover {
        color: #ff3333 !important;
    }
    div.stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #ff3333 !important;
        border-bottom-color: #ff3333 !important;
    }
    
    /* Ancient metal action buttons */
    div.stButton > button {
        background-color: #8c1919 !important;
        color: #ffffff !important;
        border: 1px solid #d4af37 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        transition: all 0.25s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #b82525 !important;
        border-color: #ffffff !important;
        box-shadow: 0 0 10px #d4af37;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# DATABASE LOADERS
# ==========================================
@st.cache_data
def load_db(filename):
    paths = [
        f"/workspace/scratch/{filename}",
        f"/workspace/artifacts/{filename}",
        filename
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                pass
    st.error(f"Errore nel caricamento del database: {filename}")
    return {}

RACES_DB = load_db("dnd_races_database.json")
CLASSES_DB = load_db("dnd_classes_database.json")
SPELLS_DB = load_db("dnd_spells_database.json")
FEATS_DB = load_db("dnd_feats_backgrounds_database.json")
EQUIP_DB = load_db("dnd_equipment_items_database.json")
MONSTERS_DB = load_db("dnd_monsters_database.json")

# Banner Display
banner_path = "/workspace/artifacts/dnd_aesthetic_banner.jpg"
if os.path.exists(banner_path):
    st.image(banner_path, use_column_width=True)
else:
    st.title("🎲 D&D 5e Interactive Companion")

# ==========================================
# INITIALIZE STATE
# ==========================================
if "characters" not in st.session_state:
    # Set default characters
    st.session_state.characters = {
        "UNIT-X49 (Envoy)": {
            "name": "UNIT-X49 (Envoy)",
            "race": "Warforged",
            "classes": {"Artificer": 5},
            "subclass": "Armorer",
            "stats": {"STR": 12, "DEX": 15, "CON": 15, "INT": 15, "WIS": 10, "CHA": 8},
            "bg": "Guild Artisan",
            "align": "Neutral",
            "inventory": ["Scale Mail", "Shield", "Bag of Holding"],
            "max_hp": 38,
            "current_hp": 38,
            "temp_hp": 0,
            "spell_points": False,
            "feats": ["Alert"],
            "options": {"hero_points": False, "honor": False, "sanity": False}
        },
        "Oogway the Elder": {
            "name": "Oogway the Elder",
            "race": "Tortle",
            "classes": {"Druid": 3},
            "subclass": "Circle of the Moon",
            "stats": {"STR": 16, "DEX": 10, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8},
            "bg": "Hermit",
            "align": "Neutral",
            "inventory": ["Shield", "Herbalism kit"],
            "max_hp": 24,
            "current_hp": 24,
            "temp_hp": 0,
            "spell_points": True,
            "feats": ["War Caster"],
            "options": {"hero_points": False, "honor": False, "sanity": False}
        }
    }

if "active_char" not in st.session_state:
    st.session_state.active_char = "UNIT-X49 (Envoy)"

if "combat_tracker" not in st.session_state:
    st.session_state.combat_tracker = []

if "combat_logs" not in st.session_state:
    st.session_state.combat_logs = []

# ==========================================
# HELPER FORMULAS & MECHANICS
# ==========================================
def get_modifier(score):
    return (score - 10) // 2

def get_pb(total_level):
    if total_level < 5: return 2
    elif total_level < 9: return 3
    elif total_level < 13: return 4
    elif total_level < 17: return 5
    else: return 6

def compute_ac(char):
    dex_mod = get_modifier(char["stats"].get("DEX", 10))
    con_mod = get_modifier(char["stats"].get("CON", 10))
    wis_mod = get_modifier(char["stats"].get("WIS", 10))
    total_lvl = sum(char["classes"].values())
    pb = get_pb(total_lvl)

    # Check for shield
    has_shield = "Shield" in char["inventory"] or "scudo" in [x.lower() for x in char["inventory"]]
    shield_bonus = 2 if has_shield else 0

    # Race tortle
    if char["race"] == "Tortle":
        return 17 + shield_bonus, "Natural Armor (Base 17) + Scudo"

    # Loxodon
    if char["race"] == "Loxodon":
        ac_base = 12 + con_mod
        return ac_base + shield_bonus, f"Natural Armor Loxodon ({ac_base} + Scudo)"

    # Barbarian/Monk unarmored defense
    has_armor = any(x in EQUIP_DB.get("Armor", {}) and x != "None" for x in char["inventory"])
    if "Monk" in char["classes"] and not has_armor:
        ac_base = 10 + dex_mod + wis_mod
        return ac_base, f"Monk Unarmored Defense ({ac_base})"
    if "Barbarian" in char["classes"] and not has_armor:
        ac_base = 10 + dex_mod + con_mod
        return ac_base + shield_bonus, f"Barbarian Unarmored Defense ({ac_base})"

    # Warforged Integrated Protection
    if char["race"] == "Warforged":
        if "Scale Mail" in char["inventory"]:
            ac_base = 13 + dex_mod + 1 + pb
            return ac_base + shield_bonus, f"Warforged Composite Plating ({ac_base})"
        elif "Plate" in char["inventory"]:
            ac_base = 16 + 1 + pb
            return ac_base + shield_bonus, f"Warforged Heavy Plating ({ac_base})"
        else:
            ac_base = 11 + dex_mod + 1
            return ac_base + shield_bonus, f"Warforged Darkwood Core ({ac_base})"

    # Standard equipment calculation
    ac_base = 10 + dex_mod
    for item in char["inventory"]:
        if item in EQUIP_DB.get("Armor", {}):
            armor_data = EQUIP_DB["Armor"][item]
            if armor_data["dex_mod"] == "max_2":
                ac_base = armor_data["ac"] + min(dex_mod, 2)
            elif armor_data["dex_mod"] == False:
                ac_base = armor_data["ac"]
            else:
                ac_base = armor_data["ac"] + dex_mod
            return ac_base + shield_bonus, f"Armatura ({item}) + Scudo"

    return ac_base + shield_bonus, "Standard Unarmored"

def compute_carrying_capacity(char):
    str_val = char["stats"].get("STR", 10)
    mult = 15
    # Powerful Build checks
    pb_races = ["Goliath", "Loxodon", "Centaur", "Minotaur"]
    if char["race"] in pb_races:
        mult *= 2
    # Feats checks
    if "Brawny" in char.get("feats", []):
        mult *= 2
    # Standard capacity limits
    max_carry = str_val * mult
    push_drag = str_val * mult * 2
    return max_carry, push_drag


# ==========================================
# APP NAVIGATION / MENU (Sidebar select PG)
# ==========================================
with st.sidebar:
    st.markdown("### 🧙 Personaggio Attivo")
    char_keys = list(st.session_state.characters.keys())
    selected_char = st.selectbox("Seleziona PG della Sessione:", char_keys, index=char_keys.index(st.session_state.active_char))
    st.session_state.active_char = selected_char
    char = st.session_state.characters[selected_char]

    st.markdown("---")
    st.markdown("### 🎲 Quick Dice Roll")
    dice_map = {"d20": 20, "d12": 12, "d10": 10, "d8": 8, "d6": 6, "d4": 4}
    dice_sel = st.selectbox("Dado:", list(dice_map.keys()))
    adv_mode = st.radio("Metodo:", ["Normale", "Con Vantaggio", "Con Svantaggio"])
    
    if st.button("Lancia Dado!"):
        sides = dice_map[dice_sel]
        if sides == 20 and adv_mode != "Normale":
            r1 = random.randint(1, 20)
            r2 = random.randint(1, 20)
            res = max(r1, r2) if adv_mode == "Con Vantaggio" else min(r1, r2)
            st.success(f"Risultato (Tirato {r1} e {r2}): **{res}**")
        else:
            res = random.randint(1, sides)
            st.success(f"Risultato: **{res}**")

# ==========================================
# TABS DIVISION: BUILDER VS DM TOOLS
# ==========================================
m_tab1, m_tab2 = st.tabs(["🧙 BEYOND CHARACTER BUILDER", "🛡️ DUNGEON MASTER SUITE"])

# ==========================================
# TAB 1: BEYOND CHARACTER BUILDER
# ==========================================
with m_tab1:
    st.subheader(f"Character Builder & Sheet: {char['name']}")
    
    # Sub-tabs corresponding to D&D Beyond's steps
    b_tab1, b_tab2, b_tab3, b_tab4, b_tab5, b_tab6 = st.tabs([
        "⚙️ 1. Opzioni Generali",
        "🧬 2. Scelta Razza",
        "⚔️ 3. Classi & Level Up",
        "📊 4. Caratteristiche & Talenti",
        "🎒 5. Zaino & Ingombro",
        "🔮 6. Grimorio Incantesimi"
    ])

    # ------------------
    # TAB 1.1: GENERAL OPTIONS
    # ------------------
    with b_tab1:
        st.write("##### Imposta le opzioni della scheda e i parametri generali del Personaggio.")
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            char_name = st.text_input("Nome Eroe:", char["name"])
            if char_name != char["name"]:
                # Rename key in dict
                st.session_state.characters[char_name] = st.session_state.characters.pop(char["name"])
                st.session_state.characters[char_name]["name"] = char_name
                st.session_state.active_char = char_name
                st.rerun()

            c_align = st.selectbox("Allineamento:", ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"], index=["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"].index(char["align"]))
            char["align"] = c_align

        with col_opt2:
            st.write("**Regole Opzionali da Abilitare (DMG / Eberron):**")
            hero_pts = st.checkbox("Usa Punti Eroe (Hero Points - d6 extra per PG)", value=char["options"]["hero_points"])
            honor_san = st.checkbox("Usa statistiche opzionali Onore (HON) & Sanità (SAN)", value=char["options"]["honor"])
            
            char["options"]["hero_points"] = hero_pts
            char["options"]["honor"] = honor_san
            char["options"]["sanity"] = honor_san

            # Extra background picker from JSON
            bg_list = list(FEATS_DB.get("Backgrounds", {}).keys())
            c_bg = st.selectbox("Seleziona Background:", bg_list, index=bg_list.index(char["bg"]) if char["bg"] in bg_list else 0)
            char["bg"] = c_bg

        st.markdown("---")
        # Display the custom background privilege
        if char["bg"] in FEATS_DB.get("Backgrounds", {}):
            bg_data = FEATS_DB["Backgrounds"][char["bg"]]
            st.markdown(f"""
            <div class='parchment-card'>
                <h4>Privilegio di Background: {bg_data['privilege']}</h4>
                <p><b>Competenze fornite:</b> {', '.join(bg_data.get('skills', []))}</p>
                <p><i>Manuale Fonte: {bg_data.get('source', 'Core PHB')}</i></p>
            </div>
            """, unsafe_allow_html=True)

    # ------------------
    # TAB 1.2: RACE SELECTION
    # ------------------
    with b_tab2:
        st.write("##### Seleziona la Stirpe del tuo Personaggio.")
        races_list = list(RACES_DB.keys())
        # Safe select
        sel_race_name = st.selectbox("Razza o Sotto-razza:", races_list, index=races_list.index(char["race"]) if char["race"] in races_list else 0)
        
        # Tasha's optional customize origin toggle
        use_tasha = st.checkbox("Abilita Origini Personalizzate (Tasha's Cauldron of Everything)", help="Permette di riallocare liberamente i bonus delle caratteristiche (ASI) della razza.")
        
        if sel_race_name:
            race_data = RACES_DB[sel_race_name]
            char["race"] = sel_race_name
            
            # Show details in gorgeous parchment card
            st.markdown(f"""
            <div class='parchment-card'>
                <h3>Razza: {race_data['name']}</h3>
                <p><b>Taglia:</b> {race_data['size']} | <b>Velocità base:</b> {race_data['speed']} ft.</p>
                <p><b>Linguaggi Iniziali:</b> {', '.join(race_data['languages'])}</p>
                <p><b>Incrementi Caratteristiche Standard:</b> {', '.join([f'{k} +{v}' for k, v in race_data['asi'].items()]) if race_data['asi'] else 'Variabile / Custom'}</p>
                <p><b>Manuale di Espansione:</b> {race_data['source']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("**Tratti Razziali Attivi:**")
            for trait in race_data["traits"]:
                st.info(f"✨ **{trait}**")

    # ------------------
    # TAB 1.3: CLASSES & LEVEL UP
    # ------------------
    with b_tab3:
        st.write("##### Gestione della Classe, del Sottoclasse e dell'Avanzamento HP.")
        
        class_keys = list(CLASSES_DB.keys())
        col_c1, col_c2 = st.columns(2)
        
        # Safe fetch active class
        active_class = list(char["classes"].keys())[0] if char["classes"] else "Artificer"
        active_lvl = list(char["classes"].values())[0] if char["classes"] else 1
        
        with col_c1:
            sel_class = st.selectbox("Classe Primaria:", class_keys, index=class_keys.index(active_class) if active_class in class_keys else 0)
            
            # Level Up slider (1 to 20)
            new_lvl = st.slider("Livello del Personaggio:", 1, 20, active_lvl)
            
        with col_c2:
            # Subclasses dynamic
            sub_map = CLASSES_DB[sel_class]["subclasses"]
            sub_list = list(sub_map.keys())
            active_sub = char.get("subclass", sub_list[0])
            sel_sub = st.selectbox("Sottoclasse / Archetipo:", sub_list, index=sub_list.index(active_sub) if active_sub in sub_list else 0)
            char["subclass"] = sel_sub
            st.caption(f"ℹ️ **Dettagli Sottoclasse:** {sub_map[sel_sub]}")

        # Update character classes level
        char["classes"] = {sel_class: new_lvl}
        
        # Hit die of class
        hd_val = CLASSES_DB[sel_class]["hd"]
        st.write(f"Dado Vita della Classe: **d{hd_val}**")

        st.markdown("---")
        # HP LEVEL UP SECTION (Animation/Interactive roll!)
        st.write("#### ❤️ Calcolo & Incremento dei Punti Ferita (Level Up)")
        st.write(f"Attuali Punti Ferita Massimi: **{char['max_hp']}**")
        
        roll_hp_col1, roll_hp_col2 = st.columns(2)
        with roll_hp_col1:
            st.markdown(f"""
            <div style='text-align: center; border: 1px solid #b88d40; padding: 10px; border-radius:8px;'>
                <span style='font-size: 3rem;'>🎲</span><br>
                <b>Dado Vita: d{hd_val}</b>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Lancia il Dado Vita d{hd_val} per HP! 🌟"):
                # Rolling sequence
                with st.spinner("Tirando il dado..."):
                    time.sleep(0.4)
                rolled_val = random.randint(1, hd_val)
                con_mod = get_modifier(char["stats"].get("CON", 10))
                earned = max(rolled_val + con_mod, 1)
                
                # Update Max HP
                char["max_hp"] += earned
                char["current_hp"] += earned
                st.success(f"🔥 Hai ottenuto **{rolled_val}** con d{hd_val}! Con il tuo modificatore di CON (+{con_mod}), i tuoi HP aumentano di **+{earned}**!")
                st.balloons()
                
        with roll_hp_col2:
            st.write("In alternativa, applica l'aumento HP medio standard:")
            standard_avg = int(hd_val / 2 + 1)
            con_mod = get_modifier(char["stats"].get("CON", 10))
            standard_increase = max(standard_avg + con_mod, 1)
            
            if st.button(f"Applica Incremento Standard (+{standard_increase} HP) 💤"):
                char["max_hp"] += standard_increase
                char["current_hp"] += standard_increase
                st.success(f"HP Massimi aumentati di **+{standard_increase}** (Valore Medio: {standard_avg} + CON: {con_mod})!")

        st.markdown("---")
        # Display unlocked features level by level
        st.write(f"⚙️ **Progressione dei Privilegi Sbloccati fino al Livello {new_lvl}:**")
        features_prog = CLASSES_DB[sel_class]["progression"]
        for lv in range(1, new_lvl + 1):
            lv_str = str(lv)
            if lv_str in features_prog:
                st.markdown(f"**Livello {lv}:** " + ", ".join([f"`{f}`" for f in features_prog[lv_str]]))

    # ------------------
    # TAB 1.4: ABILITIES & FEATS
    # ------------------
    with b_tab4:
        st.write("##### Scheda Caratteristiche, Aumenti ASI e Acquisizione dei Talenti.")
        
        # Render the standard 6 stat modifiers beautifully (Beyond style)
        st.write("**Punteggi di Caratteristica Correnti (comprensivi di bonus):**")
        stat_cols = st.columns(6)
        abilities_list = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        for idx, ability in enumerate(abilities_list):
            with stat_cols[idx]:
                score = char["stats"].get(ability, 10)
                # Form slider to manually modify
                new_score = st.number_input(ability, min_value=3, max_value=20, value=score, key=f"sheet_stat_{ability}")
                char["stats"][ability] = new_score
                
                mod = get_modifier(new_score)
                sign = "+" if mod >= 0 else ""
                st.markdown(f"""
                <div class='beyond-stat-box'>
                    <div class='stat-lbl'>{ability}</div>
                    <div class='stat-val-mod'>{sign}{mod}</div>
                    <div class='stat-val-score'>{new_score}</div>
                </div>
                """, unsafe_allow_html=True)

        if char["options"]["honor"]:
            st.write("**Caratteristiche Speciali (DMG Variant):**")
            col_extra1, col_extra2 = st.columns(2)
            with col_extra1:
                hon_val = st.slider("Onore (Honor - HON):", 3, 20, char["stats"].get("HON", 10))
                char["stats"]["HON"] = hon_val
            with col_extra2:
                san_val = st.slider("Sanità (Sanity - SAN):", 3, 20, char["stats"].get("SAN", 10))
                char["stats"]["SAN"] = san_val

        st.markdown("---")
        # FEATS SBLOCCATI (Detect ASI level)
        total_class_levels = sum(char["classes"].values())
        st.write("#### 🏆 Slot dei Talenti e Aumenti ASI")
        
        # Determine how many ASI choices are sbloccati
        asi_slots = []
        if total_class_levels >= 4: asi_slots.append("ASI Livello 4")
        if total_class_levels >= 8: asi_slots.append("ASI Livello 8")
        if total_class_levels >= 12: asi_slots.append("ASI Livello 12")
        if total_class_levels >= 16: asi_slots.append("ASI Livello 16")
        if total_class_levels >= 19: asi_slots.append("ASI Livello 19")
        
        if asi_slots:
            st.info(f"Il tuo livello complessivo ({total_class_levels}) sblocca **{len(asi_slots)} slot** d'aumento di caratteristica o talenti!")
            
            for slot in asi_slots:
                with st.expander(f"🔑 Gestione Slot: {slot}"):
                    choice = st.radio("Scegli incremento statistico o talento:", ["Aumento dei Punteggi (+2 o +1/+1)", "Prendi un Talento"], key=f"choice_{slot}")
                    if choice == "Prendi un Talento":
                        feat_keys = list(FEATS_DB.get("Feats", {}).keys())
                        # safe index
                        sel_feat = st.selectbox("Seleziona Talento:", feat_keys, key=f"sel_feat_{slot}")
                        feat_desc = FEATS_DB["Feats"][sel_feat]["desc"]
                        st.markdown(f"*Effetto del Talento*: **{feat_desc}**")
                        # Add to character feats
                        if sel_feat not in char.get("feats", []):
                            char.setdefault("feats", []).append(sel_feat)
                    else:
                        st.success("Puoi aumentare manualmente una caratteristica nel pannello soprastante (+2 o +1/+1)!")
        else:
            st.info("I talenti e gli slot ASI si sbloccano ai livelli di classe 4, 8, 12, 16 e 19.")

    # ------------------
    # TAB 1.5: PACK & CARRY
    # ------------------
    with b_tab5:
        st.write("##### Calcolo automatico della Capacità di Carico e dell'ingombro zaino.")
        
        max_carry, push_drag = compute_carrying_capacity(char)
        
        st.write(f"💪 **Carico Massimo consentito (Forza x 15):** `{max_carry} libbre`")
        st.write(f"🏋️ **Spingere/Sollevare/Trascinare (Forza x 30):** `{push_drag} libbre`")

        st.markdown("---")
        st.write("#### 🎒 Zaino Interattivo")
        
        # Input for active inventory
        avail_items = list(EQUIP_DB.get("Armor", {}).keys()) + list(EQUIP_DB.get("Weapons", {}).keys()) + list(EQUIP_DB.get("Magic Items", {}).keys())
        col_eq1, col_eq2 = st.columns([3, 1])
        with col_eq1:
            add_item = st.selectbox("Aggiungi Equipaggiamento / Oggetto Magico:", avail_items)
        with col_eq2:
            if st.button("Inserisci nello Zaino 🎒"):
                char["inventory"].append(add_item)
                st.success(f"{add_item} aggiunto!")

        # Custom items
        with st.expander("Aggiungi Oggetto Personalizzato"):
            custom_name = st.text_input("Nome Oggetto:")
            custom_weight = st.number_input("Peso (in libbre):", min_value=0.0, value=1.0)
            if st.button("Aggiungi Oggetto Speciale"):
                char["inventory"].append(f"{custom_name} ({custom_weight} lbs)")
                st.success(f"Aggiunto: {custom_name}")

        st.write("**Contenuto Zaino PG:**")
        total_weight = 0.0
        
        for idx, item in enumerate(char["inventory"]):
            col_it1, col_it2 = st.columns([4, 1])
            item_weight = 1.0
            
            # Calculate item weight
            if item in EQUIP_DB.get("Armor", {}):
                item_weight = EQUIP_DB["Armor"][item]["weight"]
            elif item in EQUIP_DB.get("Weapons", {}):
                item_weight = EQUIP_DB["Weapons"][item]["weight"]
            elif item in EQUIP_DB.get("Magic Items", {}):
                item_weight = EQUIP_DB["Magic Items"][item]["weight"]
            elif "(" in item and "lbs)" in item:
                # parsed custom weight
                try:
                    item_weight = float(item.split("(")[1].split(" ")[0])
                except:
                    item_weight = 1.0
                    
            total_weight += item_weight
            
            with col_it1:
                st.write(f"• **{item}** ({item_weight} lbs)")
            with col_it2:
                if st.button("Rimuovi ❌", key=f"del_inv_{idx}"):
                    char["inventory"].remove(item)
                    st.rerun()

        st.markdown("---")
        # Visual Weight Capacity Progress bar
        pct = min(total_weight / max_carry, 1.0) if max_carry > 0 else 0.0
        
        # Dynamic coloring
        color = "green"
        if pct > 0.66: color = "orange"
        if pct > 0.9: color = "red"
        
        st.markdown(f"**Peso Attuale nello Zaino: {total_weight:.1f} / {max_carry} lbs**")
        st.progress(pct)
        if pct >= 1.0:
            st.error("💀 **SOVRACCARICO!** La tua velocità si riduce a 5 piedi.")
        elif pct > 0.66:
            st.warning("⚠️ **INGOMBRATO!** La tua velocità si riduce di 10 piedi.")

    # ------------------
    # TAB 1.6: SPELLBOOK & SLOTS
    # ------------------
    with b_tab6:
        st.write("##### Gestione degli slot incantesimo e consultazione del grimorio delle espansioni.")
        
        # Verify spellcasting contributing
        if char["spell_points"]:
            st.warning("🔮 **Regola Variante dei Punti Incantesimo attiva (DMG pg. 288)**")
            max_spell_pts = 14  # Default for level 3
            current_sp = st.number_input("Punti Magia Rimanenti:", min_value=0, max_value=max_spell_pts, value=14)
            st.write(f"Riserva Massima Punti: **{max_spell_pts}**")
        else:
            st.write("**Slot Incantesimo Standard:**")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.number_input("Slot 1° Livello:", min_value=0, max_value=4, value=4)
            with col_s2:
                st.number_input("Slot 2° Livello:", min_value=0, max_value=3, value=2)
            with col_s3:
                st.number_input("Slot 3° Livello:", min_value=0, max_value=3, value=0)

        st.markdown("---")
        st.write("🔍 **Cerca e Consulta Incantesimi del tuo grimorio:**")
        spell_keys = list(SPELLS_DB.keys())
        sel_spell = st.selectbox("Seleziona Incantesimo per consultarne la scheda:", spell_keys)
        
        if sel_spell:
            sp_data = SPELLS_DB[sel_spell]
            st.markdown(f"""
            <div class='parchment-card'>
                <h4>Incantesimo: {sel_spell} (Liv. {sp_data['level']})</h4>
                <p><b>Scuola:</b> {sp_data['school']} | <b>Tempo Lancio:</b> {sp_data['time']}</p>
                <p><b>Gittata:</b> {sp_data['range']} | <b>Componenti:</b> {sp_data['components']}</p>
                <p><b>Durata:</b> {sp_data['duration']}</p>
                <p><i>Classi idonee: {', '.join(sp_data['classes'])}</i></p>
                <hr>
                <p>{sp_data['desc']}</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# TAB 2: DUNGEON MASTER SUITE
# ==========================================
with m_tab2:
    st.subheader("🛡️ Strumenti Avanzati per il Dungeon Master")
    
    dm_tab1, dm_tab2, dm_tab3, dm_tab4 = st.tabs([
        "🦁 Bestiario Modificabile",
        "⚖️ Combat Tracker & Iniziativa",
        "🔎 Ricerca Unificata Categorizzata",
        "🧬 Generatore NPC DMG pg. 89"
    ])

    # ------------------
    # TAB 2.1: INTERACTIVE BESTIARY
    # ------------------
    with dm_tab1:
        st.write("##### Sfoglia tutti gli 83 mostri e creane varianti modificando le statistiche.")
        
        mon_list = list(MONSTERS_DB.keys())
        sel_mon_name = st.selectbox("Seleziona Mostro dal Database:", mon_list)
        
        if sel_mon_name:
            m_data = MONSTERS_DB[sel_mon_name]
            
            # Setup columns for modification fields
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                edit_name = st.text_input("Modifica Nome Mostro:", m_data["name"])
                edit_hp = st.number_input("Punti Ferita (HP):", min_value=1, value=m_data["hp"])
                edit_ac = st.number_input("Classe Armatura (AC):", min_value=1, value=m_data["ac"])
            with col_m2:
                edit_cr = st.text_input("Grado Sfida (CR):", m_data["cr"])
                edit_speed = st.text_input("Velocità:", m_data["speed"])
                edit_size = st.text_input("Taglia:", m_data["size"])
            with col_m3:
                st.write("**Caratteristiche Mostro:**")
                # Modified stats dictionary
                m_str = st.number_input("FOR", 1, 30, m_data["stats"].get("STR", 10))
                m_dex = st.number_input("DES", 1, 30, m_data["stats"].get("DEX", 10))
                m_con = st.number_input("COS", 1, 30, m_data["stats"].get("CON", 10))

            st.write("**Tratti & Abilità Speciali:**")
            st.info(", ".join(m_data["traits"]))
            st.write("**Azioni d'Attacco:**")
            st.warning(", ".join(m_data["actions"]))

            # Trigger to insert custom monster into tracker
            if st.button("Inietta questa Variante Modificata nel Combat Tracker 🤺"):
                st.session_state.combat_tracker.append({
                    "name": f"{edit_name} (Modificato)",
                    "hp": edit_hp,
                    "max_hp": edit_hp,
                    "ac": edit_ac,
                    "init": random.randint(1, 20) + get_modifier(m_dex),
                    "conditions": []
                })
                st.success(f"{edit_name} inserito in iniziativa con {edit_hp} HP!")

    # ------------------
    # TAB 2.2: COMBAT TRACKER
    # ------------------
    with dm_tab2:
        st.write("##### Gestisci i turni, applica i danni, le cure e le condizioni di stato.")
        
        # Setup fast insert PC
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            if st.button("Carica Personaggio Attivo della Sessione"):
                total_class_lvl = sum(char["classes"].values())
                pb = get_pb(total_class_lvl)
                ac_val, _ = compute_ac(char)
                st.session_state.combat_tracker.append({
                    "name": char["name"],
                    "hp": char["current_hp"],
                    "max_hp": char["max_hp"],
                    "ac": ac_val,
                    "init": random.randint(1, 20) + get_modifier(char["stats"].get("DEX", 10)),
                    "conditions": []
                })
                st.success(f"{char['name']} aggiunto allo scontro!")
        with col_in2:
            if st.button("Inserisci Goblin di Incursione"):
                st.session_state.combat_tracker.append({
                    "name": "Goblin Esploratore",
                    "hp": 7,
                    "max_hp": 7,
                    "ac": 15,
                    "init": random.randint(1, 20) + 2,
                    "conditions": []
                })
                st.success("Goblin Esploratore aggiunto allo scontro!")

        st.markdown("---")
        
        # Sort and render the tracker
        if st.session_state.combat_tracker:
            # Sort by initiative descending
            sorted_combatants = sorted(st.session_state.combat_tracker, key=lambda x: x["init"], reverse=True)
            
            st.write("#### 🛡️ Ordine dei Turni:")
            for idx, cb in enumerate(sorted_combatants):
                with st.container():
                    col_cb1, col_cb2, col_cb3, col_cb4 = st.columns([2, 2, 2, 1])
                    with col_cb1:
                        st.markdown(f"**[{cb['init']}]** **{cb['name']}** (CA: {cb['ac']})")
                        # Add state conditions
                        conds = ["Normal", "Abbattuto", "Privo di Sensi", "Stordito", "Avvelenato", "Charmed"]
                        sel_cond = st.multiselect("Stati:", conds, default=cb.get("conditions", []), key=f"cond_{cb['name']}_{idx}")
                        cb["conditions"] = sel_cond
                    with col_cb2:
                        st.write(f"HP: **{cb['hp']} / {cb['max_hp']}**")
                        # Slider to easily damage/heal
                        hp_delta = st.number_input("Cura (+) / Danno (-):", value=0, key=f"hp_delta_{cb['name']}_{idx}")
                        if hp_delta != 0:
                            cb["hp"] = min(max(cb["hp"] + hp_delta, 0), cb["max_hp"])
                            st.success(f"HP di {cb['name']} aggiornati a {cb['hp']}!")
                            st.rerun()
                    with col_cb3:
                        # HP Progress bar for enemy life
                        perc = cb["hp"] / cb["max_hp"] if cb["max_hp"] > 0 else 0
                        st.progress(perc)
                    with col_cb4:
                        if st.button("Elimina ❌", key=f"del_cb_{cb['name']}_{idx}"):
                            st.session_state.combat_tracker.remove(cb)
                            st.rerun()
            
            if st.button("Azzera Scontro Completo 🧹"):
                st.session_state.combat_tracker = []
                st.rerun()
        else:
            st.info("Nessuno scontro attivo. Carica i PG o i mostri per avviare il tracker d'iniziativa.")

    # ------------------
    # TAB 2.3: UNIFIED SEARCH
    # ------------------
    with dm_tab3:
        st.write("##### Ricerca istantanea su TUTTO il Compendio delle Espansioni.")
        
        search_query = st.text_input("Digita alcune lettere per cercare magie, talenti, o mostri:", "").lower()
        
        if search_query:
            # 1. Spells Search
            spell_matches = [k for k in SPELLS_DB.keys() if search_query in k.lower()]
            # 2. Feats Search
            feat_matches = [k for k in FEATS_DB.get("Feats", {}).keys() if search_query in k.lower()]
            # 3. Monsters Search
            mon_matches = [k for k in MONSTERS_DB.keys() if search_query in k.lower()]
            
            st.write("### Risultati Trovati:")
            
            if spell_matches:
                with st.expander(f"🔮 Incantesimi Trovati ({len(spell_matches)})"):
                    for m in spell_matches:
                        st.markdown(f"• **{m}** (Livello {SPELLS_DB[m]['level']}): *{SPELLS_DB[m]['desc']}*")
            if feat_matches:
                with st.expander(f"🏆 Talenti Trovati ({len(feat_matches)})"):
                    for m in feat_matches:
                        st.markdown(f"• **{m}**: *{FEATS_DB['Feats'][m]['desc']}*")
            if mon_matches:
                with st.expander(f"👹 Bestiario Trovato ({len(mon_matches)})"):
                    for m in mon_matches:
                        st.markdown(f"• **{m}** (CR {MONSTERS_DB[m]['cr']}): AC {MONSTERS_DB[m]['ac']}, HP {MONSTERS_DB[m]['hp']}. *{MONSTERS_DB[m]['type']}*")
            
            if not spell_matches and not feat_matches and not mon_matches:
                st.info("Nessun elemento corrispondente trovato.")

    # ------------------
    # TAB 2.4: NPC GENERATOR
    # ------------------
    with dm_tab4:
        st.write("##### Crea comparse ed alleati complessi per la campagna in base alle linee guida DMG pg. 89.")
        
        # Generation dictionaries (DMG standard)
        appearances = [
            "Tatuaggi tribali visibili", "Un vistoso tic nervoso all'occhio", "Orecchini pendenti o gioielli antichi",
            "Cicatrici di battaglia vistose sulla guancia", "Mancanza di alcuni denti", "Abiti sgargianti color porpora",
            "Abiti consunti e rattoppati da popolano", "Occhi di due colori diversi (eterocromia)", "Altezza eccezionale",
            "Postura insolitamente curva o rigida"
        ]
        talents = [
            "Suona divinamente uno strumento musicale", "Parla perfettamente più lingue esotiche", "Incredibilmente fortunato in ogni scommessa",
            "Memoria fotografica impeccabile", "Grande empatia e addestramento con gli animali", "Bravissimo a risolvere enigmi",
            "Abilissimo truffatore e manipolatore", "Ottimo cuoco e conoscitore di erbe"
        ]
        mannerisms = [
            "Canta o canticchia costantemente sottovoce", "Parla usando rime insolite", "Sussurra anche quando parla a voce alta",
            "Gesticola con le dita costantemente", "Usa parole eccessivamente complesse", "Morde le unghie quando è nervoso"
        ]
        ideals = [
            "Ordine: La legge garantisce la stabilità.", "Pace: Il conflitto porta solo miseria.", "Aavidità: Accumulare ricchezze per sé stessi.",
            "Indipendenza: Nessuno deve dirmi cosa fare.", "Neutralità: Bilanciamento di forze del cosmo."
        ]
        secrets = [
            "Ha accumulato un enorme debito con la malavita di Ravnica", "Custodisce un antico frammento di schema magico",
            "È una spia segreta per un casato di Eberron", "Conosce la reale locazione di un tempio elementale perduto",
            "È legato da un patto segreto con un'entità planare"
        ]

        if st.button("Genera NPC Casuale! ⚡"):
            # Random selections
            npc_app = random.choice(appearances)
            npc_tal = random.choice(talents)
            npc_man = random.choice(mannerisms)
            npc_id = random.choice(ideals)
            npc_sec = random.choice(secrets)
            
            st.markdown(f"""
            <div class='parchment-card'>
                <h3>Scheda NPC Compilata:</h3>
                <p><b>Aspetto Fisico:</b> {npc_app}</p>
                <p><b>Talento Speciale:</b> {npc_tal}</p>
                <p><b>Mannerismo & Tic:</b> {npc_man}</p>
                <p><b>Ideale Guida:</b> {npc_id}</p>
                <p><b>Segreto Oscuro / Legame:</b> {npc_sec}</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
