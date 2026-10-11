#!/usr/bin/env python3
"""
Initialize the Doodle God SQLite database.
Creates tables and populates them with all 182 elements, 255 combinations,
8 categories, and starting element configuration.

Run once to create: python init_doodle_db.py
The database file will be saved as doodle_god.db
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doodle_god.db")

def create_tables(conn):
    c = conn.cursor()
    c.executescript("""
        -- Categories (element groups for the sidebar)
        CREATE TABLE IF NOT EXISTS categories (
            key       TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            color_r   INTEGER NOT NULL,
            color_g   INTEGER NOT NULL,
            color_b   INTEGER NOT NULL
        );

        -- All discoverable elements
        CREATE TABLE IF NOT EXISTS elements (
            key       TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            category  TEXT NOT NULL REFERENCES categories(key),
            color_r   INTEGER NOT NULL,
            color_g   INTEGER NOT NULL,
            color_b   INTEGER NOT NULL,
            icon      TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT ''
        );

        -- Valid combinations: combining elem_a + elem_b -> result
        -- (elem_a, elem_b) are stored alphabetically sorted so lookup is commutative
        CREATE TABLE IF NOT EXISTS combinations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            elem_a    TEXT NOT NULL REFERENCES elements(key),
            elem_b    TEXT NOT NULL REFERENCES elements(key),
            result    TEXT NOT NULL REFERENCES elements(key),
            UNIQUE(elem_a, elem_b)
        );
        CREATE INDEX IF NOT EXISTS idx_comb_result ON combinations(result);
        CREATE INDEX IF NOT EXISTS idx_comb_elem_a ON combinations(elem_a);
        CREATE INDEX IF NOT EXISTS idx_comb_elem_b ON combinations(elem_b);

        -- Starting elements (the 4 basics the player begins with)
        CREATE TABLE IF NOT EXISTS starting_elements (
            element_key TEXT PRIMARY KEY REFERENCES elements(key)
        );

        -- Save game: tracks discovered elements per save slot
        CREATE TABLE IF NOT EXISTS save_games (
            slot_id   INTEGER PRIMARY KEY DEFAULT 1,
            element_key TEXT NOT NULL REFERENCES elements(key),
            discovered_at REAL NOT NULL DEFAULT (strftime('%s','now')),
            UNIQUE(slot_id, element_key)
        );
    """)
    conn.commit()


def insert_categories(c):
    categories = [
        ("basic",    "Basic",       100, 180, 255),
        ("nature",   "Nature",       80, 200, 120),
        ("mineral",  "Mineral",     200, 180, 100),
        ("energy",   "Energy",      255, 200,  80),
        ("life",     "Life",        255, 120, 180),
        ("human",    "Human",       180, 140, 255),
        ("tech",     "Technology",  140, 200, 255),
        ("mystic",   "Mystic",      200, 100, 255),
    ]
    c.executemany(
        "INSERT OR REPLACE INTO categories (key, name, color_r, color_g, color_b) VALUES (?,?,?,?,?)",
        categories
    )


def insert_elements(c):
    elements = [
        # ── basic (4) ──
        ("water", "Water", "basic", 60, 140, 255, "drop", "The essence of life"),
        ("fire", "Fire", "basic", 255, 80, 40, "flame", "The primal flame"),
        ("earth", "Earth", "basic", 160, 120, 60, "diamond", "Solid ground beneath"),
        ("air", "Air", "basic", 180, 210, 240, "wave", "The invisible force"),
        # ── nature (20) ──
        ("steam", "Steam", "nature", 200, 210, 230, "wave", "Water meets fire"),
        ("rain", "Rain", "nature", 100, 160, 220, "drop", "Water falls from sky"),
        ("cloud", "Cloud", "nature", 210, 220, 240, "wave", "Steam meets air"),
        ("swamp", "Swamp", "nature", 80, 110, 60, "wave", "Earth and water merge"),
        ("plant", "Plant", "nature", 60, 180, 60, "leaf", "Life springs from earth"),
        ("algae", "Algae", "nature", 50, 160, 80, "leaf", "Life in the water"),
        ("moss", "Moss", "nature", 70, 140, 60, "leaf", "Plant on stone"),
        ("mushroom", "Mushroom", "nature", 180, 140, 100, "star", "Swamp life form"),
        ("tree", "Tree", "nature", 40, 130, 40, "leaf", "Plants grow tall"),
        ("flower", "Flower", "nature", 255, 140, 200, "star", "Nature's beauty"),
        ("forest", "Forest", "nature", 30, 100, 30, "leaf", "Many trees together"),
        ("sand", "Sand", "nature", 220, 200, 140, "diamond", "Earth ground fine"),
        ("grass", "Grass", "nature", 100, 200, 60, "leaf", "Earth and rain mix"),
        ("reed", "Reed", "nature", 120, 170, 70, "leaf", "Grass by the swamp"),
        ("ice", "Ice", "nature", 160, 210, 255, "diamond", "Water frozen solid"),
        ("snow", "Snow", "nature", 230, 240, 255, "drop", "Rain turns to snow"),
        ("storm", "Storm", "nature", 60, 60, 140, "wave", "Energy in the clouds"),
        ("rainbow", "Rainbow", "nature", 255, 100, 200, "wave", "Sunlight through rain"),
        ("coral", "Coral", "nature", 255, 120, 100, "star", "Life in warm seas"),
        ("seaweed", "Seaweed", "nature", 40, 120, 60, "leaf", "Algae grows long"),
        # ── mineral (19) ──
        ("lava", "Lava", "mineral", 240, 100, 30, "flame", "Molten earth"),
        ("stone", "Stone", "mineral", 140, 140, 140, "diamond", "Lava cooled down"),
        ("dust", "Dust", "mineral", 180, 170, 140, "circle", "Air erodes earth"),
        ("metal", "Metal", "mineral", 180, 190, 210, "diamond", "Fire purifies stone"),
        ("clay", "Clay", "mineral", 180, 130, 80, "circle", "Dust and water bind"),
        ("brick", "Brick", "mineral", 190, 90, 70, "diamond", "Fire bakes clay"),
        ("coal", "Coal", "mineral", 60, 60, 60, "circle", "Stone under pressure"),
        ("gem", "Gem", "mineral", 200, 80, 220, "diamond", "Pressure creates beauty"),
        ("obsidian", "Obsidian", "mineral", 40, 20, 60, "diamond", "Lava meets water"),
        ("marble", "Marble", "mineral", 230, 220, 210, "diamond", "Stone transformed"),
        ("gold", "Gold", "mineral", 255, 215, 0, "star", "Metal of the sun"),
        ("silver", "Silver", "mineral", 200, 210, 220, "star", "Metal of the moon"),
        ("glass", "Glass", "mineral", 200, 230, 255, "diamond", "Sand meets fire"),
        ("concrete", "Concrete", "mineral", 160, 160, 150, "diamond", "Sand and stone bind"),
        ("salt", "Salt", "mineral", 240, 240, 240, "diamond", "Sea water evaporates"),
        ("diamond_g", "Diamond", "mineral", 220, 240, 255, "diamond", "Coal under pressure"),
        ("cement", "Cement", "mineral", 180, 175, 165, "circle", "Limestone baked"),
        ("limestone", "Limestone", "mineral", 210, 200, 180, "diamond", "Stone and shells"),
        ("saltpeter", "Saltpeter", "mineral", 240, 240, 240, "diamond", "Limestone and life"),
        # ── energy (7) ──
        ("energy", "Energy", "energy", 255, 230, 50, "star", "Air and fire ignite"),
        ("lightning", "Lightning", "energy", 255, 255, 100, "flame", "Energy in the storm"),
        ("sun", "Sun", "energy", 255, 220, 50, "star", "Fire of the heavens"),
        ("light", "Light", "energy", 255, 255, 200, "star", "The sun illuminates"),
        ("electricity", "Electricity", "energy", 150, 180, 255, "flame", "Metal captures lightning"),
        ("plasma", "Plasma", "energy", 200, 100, 255, "flame", "Energy heated extreme"),
        ("void", "Void", "energy", 20, 10, 40, "circle", "Beyond all elements"),
        # ── life (21) ──
        ("life", "Life", "life", 100, 255, 150, "star", "Energy meets swamp"),
        ("egg", "Egg", "life", 255, 240, 200, "circle", "Stone cradles life"),
        ("seed", "Seed", "life", 140, 100, 40, "circle", "Life within sand"),
        ("fish", "Fish", "life", 80, 160, 255, "drop", "Life in the water"),
        ("snake", "Snake", "life", 100, 140, 60, "wave", "Swamp gives life form"),
        ("beast", "Beast", "life", 160, 100, 60, "circle", "Earth and life unite"),
        ("bird", "Bird", "life", 100, 180, 240, "triangle", "Life takes to the sky"),
        ("butterfly", "Butterfly", "life", 255, 150, 220, "star", "Flower and fire dance"),
        ("turtle", "Turtle", "life", 80, 130, 80, "circle", "Life in a stone shell"),
        ("frog", "Frog", "life", 60, 160, 60, "circle", "Life leaps in swamp"),
        ("dinosaur", "Dinosaur", "life", 100, 130, 60, "triangle", "Beast of ancient times"),
        ("whale", "Whale", "life", 60, 100, 160, "drop", "Fish grows mighty"),
        ("horse", "Horse", "life", 180, 120, 60, "triangle", "Beast of the plains"),
        ("cat", "Cat", "life", 200, 160, 100, "circle", "Beast becomes cunning"),
        ("dog", "Dog", "life", 180, 140, 90, "circle", "Beast and human bond"),
        ("lizard", "Lizard", "life", 80, 160, 80, "wave", "Snake meets stone"),
        ("shark", "Shark", "life", 100, 110, 130, "triangle", "Predator of the deep"),
        ("octopus", "Octopus", "life", 180, 80, 140, "wave", "Life deep in sea"),
        ("spider", "Spider", "life", 80, 60, 60, "star", "Beast and snake weave"),
        ("scorpion", "Scorpion", "life", 160, 100, 60, "triangle", "Beast and swamp venom"),
        ("insect", "Insect", "life", 140, 100, 40, "circle", "Life takes tiny form"),
        # ── human (82) ──
        ("human", "Human", "human", 240, 200, 160, "triangle", "Life attains consciousness"),
        ("blood", "Blood", "human", 200, 30, 30, "drop", "The fluid of life"),
        ("meat", "Meat", "human", 200, 100, 80, "circle", "Beast provides food"),
        ("milk", "Milk", "human", 250, 250, 240, "drop", "From beast, sustenance"),
        ("cheese", "Cheese", "human", 255, 210, 80, "circle", "Milk transformed"),
        ("bread", "Bread", "human", 220, 180, 100, "circle", "Fire bakes the dough"),
        ("dough", "Dough", "human", 230, 210, 170, "circle", "Water meets flour"),
        ("flour", "Flour", "human", 245, 240, 220, "circle", "Grain ground fine"),
        ("beer", "Beer", "human", 200, 160, 60, "drop", "Wheat ferments"),
        ("wine", "Wine", "human", 140, 40, 60, "drop", "Grape meets time"),
        ("vodka", "Vodka", "human", 220, 230, 255, "drop", "Alcohol distilled"),
        ("alcohol", "Alcohol", "human", 200, 200, 220, "drop", "Wheat and water ferment"),
        ("sugar", "Sugar", "human", 255, 255, 230, "diamond", "Reed's sweet gift"),
        ("tea", "Tea", "human", 140, 180, 80, "leaf", "Plant in hot water"),
        ("coffee", "Coffee", "human", 100, 60, 30, "drop", "Energy in a cup"),
        ("clothing", "Clothing", "human", 160, 120, 180, "wave", "Plant woven into fabric"),
        ("tool", "Tool", "human", 170, 150, 120, "cross", "Human shapes metal"),
        ("weapon", "Weapon", "human", 150, 150, 160, "cross", "Tool made for war"),
        ("house", "House", "human", 200, 150, 100, "triangle", "Brick shelters human"),
        ("hut", "Hut", "human", 140, 110, 70, "triangle", "Grass makes shelter"),
        ("wood", "Wood", "human", 140, 90, 40, "diamond", "Tree felled by tool"),
        ("paper", "Paper", "human", 250, 248, 240, "diamond", "Wood pressed thin"),
        ("book", "Book", "human", 160, 80, 60, "diamond", "Paper records knowledge"),
        ("music", "Music", "human", 255, 180, 220, "wave", "Human voice refined"),
        ("poetry", "Poetry", "human", 200, 160, 220, "wave", "Words become art"),
        ("philosophy", "Philosophy", "human", 180, 200, 255, "star", "Human mind awakened"),
        ("money", "Money", "human", 60, 180, 60, "circle", "Paper gains value"),
        ("wheel", "Wheel", "human", 160, 140, 100, "circle", "Wood meets tool"),
        ("cart", "Cart", "human", 140, 110, 70, "triangle", "Wood on wheels"),
        ("boat", "Boat", "human", 120, 90, 60, "triangle", "Wood floats on water"),
        ("ship", "Ship", "human", 100, 80, 60, "triangle", "Boat grows mighty"),
        ("car", "Car", "human", 200, 60, 60, "diamond", "Metal on wheels"),
        ("airplane", "Airplane", "human", 180, 190, 210, "triangle", "Metal takes flight"),
        ("rocket", "Rocket", "human", 220, 220, 230, "triangle", "Metal reaches the stars"),
        ("fireworks", "Fireworks", "human", 255, 100, 100, "star", "Gunpowder celebrates"),
        ("gunpowder", "Gunpowder", "human", 80, 80, 80, "circle", "Coal meets saltpeter"),
        ("sword", "Sword", "human", 190, 200, 220, "cross", "Metal forged sharp"),
        ("armor", "Armor", "human", 160, 160, 170, "diamond", "Metal guards the body"),
        ("religion", "Religion", "human", 255, 215, 150, "star", "Human seeks the divine"),
        ("temple", "Temple", "human", 210, 180, 140, "triangle", "House for the gods"),
        ("law", "Law", "human", 200, 190, 170, "diamond", "Philosophy structures society"),
        ("city", "City", "human", 180, 170, 150, "triangle", "Many houses together"),
        ("farm", "Farm", "human", 160, 180, 80, "leaf", "Human cultivates earth"),
        ("wheat", "Wheat", "human", 220, 200, 100, "leaf", "Grass cultivated"),
        ("grape", "Grape", "human", 140, 60, 120, "circle", "Plant bears fruit"),
        ("fruit", "Fruit", "human", 255, 180, 80, "circle", "Tree gives sweet gift"),
        ("pie", "Pie", "human", 200, 160, 80, "circle", "Fruit in dough"),
        ("jam", "Jam", "human", 200, 60, 60, "drop", "Fruit preserved"),
        ("soup", "Soup", "human", 180, 160, 60, "drop", "Water, meat, and salt"),
        ("sushi", "Sushi", "human", 240, 200, 180, "circle", "Fish meets rice"),
        ("rice", "Rice", "human", 240, 240, 230, "circle", "Grass becomes grain"),
        ("chocolate", "Chocolate", "human", 100, 60, 30, "circle", "Sugar meets cacao"),
        ("cacao", "Cacao", "human", 90, 50, 20, "circle", "Fruit of the tropics"),
        ("medicine", "Medicine", "human", 255, 100, 100, "cross", "Knowledge heals"),
        ("poison", "Poison", "human", 120, 60, 180, "drop", "Mushroom's dark side"),
        ("tobacco", "Tobacco", "human", 100, 120, 60, "leaf", "Plant dried and cured"),
        ("cigarette", "Cigarette", "human", 200, 200, 200, "flame", "Tobacco meets paper"),
        ("feather", "Feather", "human", 240, 230, 210, "leaf", "Bird's light gift"),
        ("ink", "Ink", "human", 20, 20, 40, "drop", "Feather's dark blood"),
        ("painting", "Painting", "human", 255, 200, 100, "star", "Art on canvas"),
        ("pottery", "Pottery", "human", 190, 140, 80, "circle", "Clay shaped by hand"),
        ("love", "Love", "human", 255, 100, 150, "star", "Human's greatest power"),
        ("baby", "Baby", "human", 255, 220, 200, "circle", "Life begins again"),
        ("child", "Child", "human", 255, 210, 190, "circle", "Baby grows"),
        ("adult", "Adult", "human", 230, 190, 150, "triangle", "Child matures"),
        ("elder", "Elder", "human", 200, 180, 160, "star", "Adult grows wise"),
        ("corpse", "Corpse", "human", 120, 100, 80, "circle", "Life leaves the body"),
        ("ghost", "Ghost", "human", 200, 200, 255, "star", "Life beyond death"),
        ("zombie", "Zombie", "human", 100, 140, 60, "circle", "Corpse and life abhor"),
        ("vampire", "Vampire", "human", 180, 30, 60, "triangle", "Life and blood curse"),
        ("werewolf", "Werewolf", "human", 130, 100, 60, "triangle", "Beast and human fuse"),
        ("witch", "Witch", "human", 120, 80, 180, "star", "Human and magic blend"),
        ("wizard", "Wizard", "human", 100, 80, 200, "star", "Philosophy opens doors"),
        ("assassin", "Assassin", "human", 60, 60, 80, "cross", "Weapon and poison"),
        ("thief", "Thief", "human", 100, 80, 60, "circle", "Human turns to crime"),
        ("pirate", "Pirate", "human", 140, 100, 50, "cross", "Thief takes to sea"),
        ("ninja", "Ninja", "human", 50, 50, 70, "star", "Assassin refined"),
        ("samurai", "Samurai", "human", 180, 50, 50, "cross", "Warrior of honor"),
        ("soldier", "Soldier", "human", 120, 130, 100, "cross", "Weapon and armor unite"),
        ("war", "War", "human", 180, 50, 50, "cross", "Soldiers clash"),
        ("peace", "Peace", "human", 180, 230, 180, "star", "The dream of harmony"),
        ("death", "Death", "human", 80, 80, 100, "cross", "The final element"),
        # ── tech (16) ──
        ("computer", "Computer", "tech", 100, 120, 160, "diamond", "Electricity meets logic"),
        ("internet", "Internet", "tech", 80, 140, 220, "wave", "Computers connected"),
        ("phone", "Phone", "tech", 60, 60, 80, "diamond", "Electricity talks"),
        ("tv", "TV", "tech", 80, 80, 100, "diamond", "Electricity shows"),
        ("radio", "Radio", "tech", 120, 100, 80, "diamond", "Electricity sings"),
        ("camera", "Camera", "tech", 100, 100, 120, "diamond", "Glass captures light"),
        ("battery", "Battery", "tech", 80, 180, 60, "diamond", "Electricity stored"),
        ("wire", "Wire", "tech", 200, 180, 60, "wave", "Metal drawn thin"),
        ("circuit", "Circuit", "tech", 60, 180, 120, "cross", "Wire meets electricity"),
        ("robot", "Robot", "tech", 160, 170, 180, "diamond", "Metal gains life"),
        ("ai", "AI", "tech", 100, 200, 255, "star", "Computer thinks"),
        ("satellite", "Satellite", "tech", 180, 190, 210, "star", "Metal orbits earth"),
        ("nuclear", "Nuclear", "tech", 100, 255, 100, "star", "Energy unchained"),
        ("laser", "Laser", "tech", 255, 50, 50, "flame", "Light focused tight"),
        ("telescope", "Telescope", "tech", 180, 180, 200, "diamond", "Glass sees far"),
        ("microscope", "Microscope", "tech", 200, 200, 210, "diamond", "Glass sees small"),
        # ── mystic (13) ──
        ("magic", "Magic", "mystic", 180, 100, 255, "star", "Energy meets void"),
        ("spell", "Spell", "mystic", 160, 80, 240, "star", "Magic given form"),
        ("potion", "Potion", "mystic", 100, 220, 100, "drop", "Magic in liquid form"),
        ("wand", "Wand", "mystic", 200, 170, 120, "cross", "Wood and magic fuse"),
        ("dragon", "Dragon", "mystic", 200, 60, 60, "triangle", "Beast meets magic"),
        ("phoenix", "Phoenix", "mystic", 255, 160, 50, "star", "Bird reborn in fire"),
        ("unicorn", "Unicorn", "mystic", 255, 180, 255, "star", "Horse blessed by magic"),
        ("demon", "Demon", "mystic", 200, 50, 50, "triangle", "Darkness gains form"),
        ("angel", "Angel", "mystic", 255, 255, 220, "star", "Life ascends divine"),
        ("god", "God", "mystic", 255, 240, 200, "star", "The ultimate creator"),
        ("necromancy", "Necromancy", "mystic", 100, 80, 140, "star", "Death meets magic"),
        ("sorcery", "Sorcery", "mystic", 160, 60, 200, "star", "Magic and knowledge"),
        ("alchemy", "Alchemy", "mystic", 200, 180, 100, "diamond", "Magic meets science"),
    ]
    c.executemany(
        "INSERT OR REPLACE INTO elements (key, name, category, color_r, color_g, color_b, icon, description) "
        "VALUES (?,?,?,?,?,?,?,?)",
        elements
    )


def insert_combinations(c, conn):
    """Insert all valid combinations. We use INSERT OR IGNORE to keep the first
    definition for any duplicate (sorted) pair, matching original game behavior.
    Combos referencing non-existent elements are skipped (same as original game)."""

    # Get valid element keys for FK validation
    valid = {row[0] for row in c.execute("SELECT key FROM elements").fetchall()}

    # All 300 add_combo calls, in the original call order.
    # The database will auto-deduplicate via UNIQUE(elem_a, elem_b) keeping first row.
    raw_combos = [
        # ═══ BASIC ═══
        ("water", "fire", "steam"),
        ("water", "earth", "swamp"),
        ("water", "air", "rain"),
        ("fire", "earth", "lava"),
        ("fire", "air", "energy"),
        ("earth", "air", "dust"),
        ("fire", "fire", "sun"),
        ("air", "air", "void"),
        ("water", "cloud", "ice"),
        ("storm", "water", "ice"),
        ("human", "beast", "blood"),
        ("beast", "grass", "milk"),
        ("coal", "water", "ink"),
        ("human", "air", "music"),
        ("metal", "tool", "weapon"),
        ("grass", "wood", "hut"),
        ("stone", "lightning", "gem"),
        ("earth", "stone", "limestone"),
        ("limestone", "water", "salt"),
        ("water", "energy", "life"),
        ("sun", "fire", "light"),
        ("forest", "beast", "insect"),
        ("insect", "water", "spider"),
        ("spider", "beast", "scorpion"),
        ("fish", "fish", "shark"),
        ("tree", "tree", "wood"),
        ("wood", "water", "boat"),
        ("boat", "wood", "ship"),
        ("paper", "gold", "money"),
        ("human", "philosophy", "religion"),
        ("fruit", "sun", "cacao"),
        ("reed", "earth", "sugar"),
        ("wheat", "water", "alcohol"),
        ("flour", "water", "dough"),
        ("beast", "fire", "meat"),
        ("grass", "plant", "wheat"),
        ("plant", "seed", "tree"),
        ("life", "swamp", "egg"),
        ("fish", "lightning", "octopus"),
        ("magic", "life", "angel"),
        ("magic", "death", "demon"),
        ("magic", "beast", "unicorn"),
        ("life", "void", "god"),
        ("energy", "fire", "plasma"),
        ("electricity", "light", "battery"),
        ("electricity", "air", "radio"),
        ("radio", "light", "tv"),
        ("circuit", "circuit", "computer"),
        ("wire", "metal", "phone"),
        ("computer", "wire", "internet"),
        ("metal", "nuclear", "rocket"),
        ("glass", "light", "telescope"),
        ("glass", "glass", "microscope"),
        ("metal", "robot", "ai"),
        ("computer", "metal", "robot"),
        ("airplane", "electricity", "satellite"),
        ("glass", "electricity", "laser"),
        ("war", "nuclear", "death"),
        ("death", "death", "corpse"),
        ("life", "magic", "potion"),
        ("potion", "plant", "medicine"),
        ("magic", "tool", "wand"),
        ("magic", "magic", "spell"),
        ("magic", "book", "sorcery"),
        ("magic", "metal", "alchemy"),
        ("tool", "fire", "sword"),
        ("armor", "weapon", "soldier"),
        ("coal", "rain", "saltpeter"),
        ("lava", "ice", "obsidian"),
        ("beast", "tree", "cat"),
        ("beast", "bird", "cat"),
        ("beast", "swamp", "snake"),
        ("swamp", "grass", "reed"),
        ("rain", "plant", "tea"),
        ("magic", "water", "potion"),
        ("swamp", "water", "frog"),
        ("beast", "love", "dog"),
        ("beast", "soldier", "werewolf"),
        ("wheel", "wood", "cart"),
        ("corpse", "magic", "necromancy"),
        ("fruit", "water", "grape"),
        # ═══ NATURE ═══
        ("steam", "air", "cloud"),
        ("cloud", "water", "rain"),
        ("cloud", "cloud", "storm"),
        ("rain", "earth", "plant"),
        ("rain", "ice", "snow"),
        ("rain", "sun", "rainbow"),
        ("swamp", "energy", "life"),
        ("swamp", "plant", "mushroom"),
        ("swamp", "beast", "frog"),
        ("swamp", "beast", "snake"),
        ("swamp", "beast", "scorpion"),
        ("swamp", "beast", "insect"),
        ("swamp", "sand", "clay"),
        ("water", "plant", "algae"),
        ("algae", "earth", "moss"),
        ("algae", "water", "seaweed"),
        ("algae", "stone", "coral"),
        ("plant", "earth", "grass"),
        ("plant", "plant", "forest"),
        ("plant", "water", "reed"),
        ("plant", "fire", "tobacco"),
        ("plant", "energy", "flower"),
        ("plant", "sun", "flower"),
        ("plant", "stone", "moss"),
        ("grass", "water", "rice"),
        ("tree", "flower", "fruit"),
        ("tree", "fire", "coal"),
        ("flower", "beast", "butterfly"),
        ("flower", "fire", "butterfly"),
        ("forest", "life", "beast"),
        ("forest", "fire", "coal"),
        ("air", "ice", "snow"),
        ("water", "ice", "ice"),
        # ═══ MINERAL ═══
        ("lava", "water", "stone"),
        ("lava", "water", "obsidian"),
        ("lava", "ice", "stone"),
        ("lava", "air", "stone"),
        ("stone", "fire", "metal"),
        ("stone", "stone", "concrete"),
        ("stone", "water", "sand"),
        ("stone", "sand", "marble"),
        ("metal", "energy", "electricity"),
        ("metal", "human", "armor"),
        ("metal", "wire", "circuit"),
        ("dust", "water", "clay"),
        ("dust", "dust", "sand"),
        ("sand", "fire", "glass"),
        ("sand", "water", "clay"),
        ("clay", "fire", "brick"),
        ("clay", "human", "pottery"),
        ("brick", "human", "house"),
        ("coal", "coal", "diamond_g"),
        ("sand", "sand", "concrete"),
        ("sand", "metal", "concrete"),
        ("limestone", "fire", "cement"),
        ("cement", "water", "concrete"),
        ("saltpeter", "coal", "gunpowder"),
        ("metal", "sun", "gold"),
        ("metal", "philosophy", "gold"),
        ("metal", "moon", "silver"),
        ("air", "sun", "silver"),
        ("stone", "ice", "ice"),
        ("metal", "sand", "concrete"),
        # ═══ ENERGY ═══
        ("energy", "swamp", "life"),
        ("energy", "metal", "electricity"),
        ("energy", "cloud", "lightning"),
        ("energy", "energy", "plasma"),
        ("energy", "void", "magic"),
        ("lightning", "sand", "glass"),
        ("lightning", "metal", "electricity"),
        ("lightning", "water", "life"),
        ("sun", "energy", "light"),
        ("sun", "plant", "flower"),
        ("sun", "water", "rainbow"),
        ("sun", "glass", "light"),
        ("sun", "tree", "fruit"),
        ("light", "glass", "laser"),
        ("electricity", "wire", "circuit"),
        ("electricity", "glass", "light"),
        ("electricity", "tool", "computer"),
        ("electricity", "metal", "wire"),
        ("plasma", "energy", "nuclear"),
        ("void", "energy", "magic"),
        # ═══ LIFE ═══
        ("life", "earth", "beast"),
        ("life", "stone", "egg"),
        ("life", "sand", "seed"),
        ("life", "water", "fish"),
        ("life", "swamp", "snake"),
        ("life", "air", "bird"),
        ("life", "forest", "beast"),
        ("life", "magic", "dragon"),
        ("egg", "fire", "phoenix"),
        ("egg", "life", "bird"),
        ("egg", "stone", "turtle"),
        ("egg", "magic", "dragon"),
        ("seed", "earth", "plant"),
        ("seed", "water", "plant"),
        ("seed", "fire", "coffee"),
        ("seed", "life", "tree"),
        ("fish", "fish", "whale"),
        ("fish", "water", "whale"),
        ("fish", "magic", "octopus"),
        ("snake", "stone", "lizard"),
        ("beast", "earth", "dinosaur"),
        ("beast", "beast", "horse"),
        ("beast", "beast", "cat"),
        ("beast", "beast", "dog"),
        ("beast", "human", "dog"),
        ("beast", "human", "meat"),
        ("beast", "human", "horse"),
        ("beast", "magic", "dragon"),
        ("bird", "air", "feather"),
        ("bird", "fire", "phoenix"),
        ("bird", "magic", "phoenix"),
        ("butterfly", "magic", "unicorn"),
        ("horse", "magic", "unicorn"),
        ("cat", "magic", "witch"),
        ("lizard", "fire", "dragon"),
        ("insect", "plant", "butterfly"),
        ("rain", "sun", "rainbow"),
        # ═══ HUMAN ═══
        ("life", "life", "human"),
        ("beast", "life", "human"),
        ("human", "human", "love"),
        ("human", "human", "baby"),
        ("human", "wood", "house"),
        ("human", "brick", "house"),
        ("human", "stone", "tool"),
        ("human", "metal", "tool"),
        ("human", "clay", "pottery"),
        ("human", "plant", "clothing"),
        ("human", "reed", "paper"),
        ("human", "tree", "wood"),
        ("human", "sand", "glass"),
        ("human", "glass", "camera"),
        ("human", "light", "philosophy"),
        ("human", "magic", "wizard"),
        ("human", "magic", "witch"),
        ("human", "beast", "werewolf"),
        ("human", "blood", "vampire"),
        ("human", "corpse", "zombie"),
        ("human", "weapon", "soldier"),
        ("human", "poison", "assassin"),
        ("human", "love", "baby"),
        ("human", "philosophy", "law"),
        ("human", "music", "poetry"),
        ("human", "book", "philosophy"),
        ("human", "boat", "pirate"),
        ("human", "war", "soldier"),
        ("human", "money", "thief"),
        ("human", "computer", "ai"),
        ("blood", "poison", "death"),
        ("blood", "corpse", "ghost"),
        ("meat", "water", "soup"),
        ("meat", "salt", "soup"),
        ("milk", "fire", "cheese"),
        ("wheat", "stone", "flour"),
        ("wheat", "fire", "bread"),
        ("wheat", "alcohol", "beer"),
        ("dough", "fire", "bread"),
        ("dough", "fruit", "pie"),
        ("grape", "water", "wine"),
        ("grape", "alcohol", "wine"),
        ("wine", "water", "vodka"),
        ("alcohol", "fire", "cigarette"),
        ("tobacco", "paper", "cigarette"),
        ("tobacco", "fire", "cigarette"),
        ("sugar", "fruit", "jam"),
        ("sugar", "cacao", "chocolate"),
        ("rice", "fish", "sushi"),
        ("plant", "water", "tea"),
        ("seed", "fire", "coffee"),
        ("tool", "wood", "wheel"),
        ("tool", "wood", "cart"),
        ("weapon", "poison", "assassin"),
        ("weapon", "soldier", "war"),
        ("sword", "armor", "samurai"),
        ("armor", "soldier", "samurai"),
        ("wheel", "metal", "car"),
        ("car", "air", "airplane"),
        ("gunpowder", "fire", "fireworks"),
        ("concrete", "brick", "city"),
        ("house", "house", "city"),
        ("grass", "earth", "farm"),
        ("ink", "paper", "book"),
        ("ink", "paper", "painting"),
        ("glass", "paper", "painting"),
        ("music", "human", "poetry"),
        ("love", "magic", "spell"),
        ("love", "war", "peace"),
        ("love", "human", "baby"),
        ("philosophy", "magic", "sorcery"),
        ("religion", "human", "temple"),
        ("religion", "house", "temple"),
        ("religion", "magic", "god"),
        ("death", "magic", "necromancy"),
        ("death", "life", "ghost"),
        ("death", "corpse", "ghost"),
        ("corpse", "magic", "zombie"),
        ("corpse", "life", "zombie"),
        ("corpse", "death", "ghost"),
        ("human", "death", "corpse"),
        ("soldier", "soldier", "war"),
        ("soldier", "death", "war"),
        ("soldier", "sword", "samurai"),
        ("soldier", "philosophy", "samurai"),
        ("assassin", "weapon", "ninja"),
        ("peace", "war", "law"),
        ("child", "life", "adult"),
        ("adult", "life", "elder"),
        ("elder", "death", "corpse"),
        ("baby", "life", "child"),
        ("bird", "bird", "egg"),
        ("water", "water", "salt"),
        ("mushroom", "swamp", "poison"),
        ("potion", "water", "poison"),
        ("potion", "death", "poison"),
        ("necromancy", "corpse", "zombie"),
        ("alchemy", "metal", "gold"),
        ("philosophy", "book", "philosophy"),
    ]

    # Sort each pair alphabetically, insert first-occurrence only
    # Skip combos where any element doesn't exist in the DB
    seen = set()
    rows = []
    skipped = 0
    for a, b, result in raw_combos:
        if a not in valid or b not in valid or result not in valid:
            skipped += 1
            continue
        key = tuple(sorted([a, b]))
        if key not in seen:
            seen.add(key)
            rows.append((key[0], key[1], result))

    c.executemany(
        "INSERT OR IGNORE INTO combinations (elem_a, elem_b, result) VALUES (?, ?, ?)",
        rows
    )
    if skipped:
        print(f"  (skipped {skipped} combos with undefined elements)")


def insert_starting_elements(c):
    c.executemany(
        "INSERT OR REPLACE INTO starting_elements (element_key) VALUES (?)",
        [("water",), ("fire",), ("earth",), ("air",)]
    )


def main():
    # Remove old DB for clean init
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    print("Creating tables...")
    create_tables(conn)

    print("Inserting 8 categories...")
    insert_categories(conn.cursor())

    print("Inserting 182 elements...")
    insert_elements(conn.cursor())

    print("Inserting combinations...")
    insert_combinations(conn.cursor(), conn)

    print("Inserting starting elements...")
    insert_starting_elements(conn.cursor())

    conn.commit()

    # Verify
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM elements")
    print(f"Elements: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM combinations")
    print(f"Combinations: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM categories")
    print(f"Categories: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM starting_elements")
    print(f"Starting elements: {cur.fetchone()[0]}")

    conn.close()
    print(f"\nDatabase created: {DB_PATH}")


if __name__ == "__main__":
    main()
