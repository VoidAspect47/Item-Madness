import json
import os
import random
import re
import sys
import webbrowser

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    tk = None
    filedialog = None
    messagebox = None
    ttk = None


COMMON_ITEMS = {
    "Coin": "dda002e9-02b1-4208-82a5-cf059f3c79cf",
    "Fiber Wire": "edd82229-9984-45db-802f-8584ecf38ef3",
    "Lockpick": "2eacd4f6-0018-41a5-800d-5fd85f9ecefe",
    "Lethal Poison Syringe": "af9ad679-6a7c-4f8e-9700-ceb5e6887666",
    "Sedative Poison Syringe": "c45e59f4-d8e1-4c37-b079-8b74b1fe9b24",
    "Emetic Poison Syringe": "1c50d6e0-11c8-4cbc-be05-f51a8e5013be",
    "ICA19 Goldballer": "028bcbf4-a0a3-42b5-beaf-163a777164e8",
    "Kalmer 1": "26b5496d-9a8c-4059-9d69-d8712078a33c",
    "Kalmer 2": "351c144c-8687-426a-a6f0-c4abd7021062",
    "Remote Explosive Duck": "7e52d861-481c-4f7c-87d2-6211d90586bf",
    "Sieger 300 Ghost": "f301f605-007c-4fe1-aa99-a8cd2cae033f",
    "Briefcase": "b20fc045-e453-4280-8b18-b0a0e5c17236",
}

ITEM_TYPE_OPTIONS = {
    "weapon": ["pistol", "smg", "shotgun", "assaultrifle", "sniperrifle", "melee"],
    "tool": ["distraction", "poison", "explosive", "remote", "misc"],
    "gear": ["container", "disguise", "misc"],
}

LOADOUT_SLOT_OPTIONS = [
    "concealedweapon",
    "carriedweapon",
    "gear1",
    "gear2",
    "gear3",
    "stashpoint",
]

RARITY_OPTIONS = ["common", "rare", "epic", "legendary"]

DEFAULT_WEAPON_STATS = {
    "range": 1.0,
    "damage": 1.0,
    "clipsize": 1.0,
    "rateoffire": 1.0,
}

GUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

DEFAULT_ENTITY_FILENAME = "00D347CBA29EE6BA.entity.patch.json"
DEFAULT_UNLOCKABLES_FILENAME = "unlockables.json"
REPO_SEARCH_URL = "https://hitman-resources.netlify.app/quicksearch/h3/"


class HitmanJSONGenerator:
    def __init__(self):
        self.items = []
        self.unlockables = {}
        self.parent_root = "feed9d3063a95cec"
        self.scene_root = "158cb860b1fce56d"

    def clear(self):
        self.items = []
        self.unlockables = {}

    def generate_entity_id(self, prefix="feed"):
        return prefix + "".join(random.choices("0123456789abcdef", k=12))

    def generate_guid(self):
        parts = [
            "feed" + "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=12)),
        ]
        return "-".join(parts)

    @staticmethod
    def is_valid_repository_id(repository_id):
        return bool(GUID_PATTERN.fullmatch(repository_id.strip()))

    @staticmethod
    def normalize_json_filename(filename, default_name):
        cleaned = filename.strip() or default_name
        if not cleaned.lower().endswith(".json"):
            cleaned += ".json"
        return cleaned

    @staticmethod
    def build_item_id(name):
        token = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")
        return f"CUSTOM_{token or 'ITEM'}"

    def add_item(self, name, repository_id, quantity=1):
        item = {
            "name": name.strip(),
            "repository_id": repository_id.strip(),
            "quantity": quantity,
        }
        self.items.append(item)
        return item

    def remove_item(self, index):
        self.items.pop(index)

    def add_unlockable(self, unlockable_data):
        item_id = unlockable_data.get("Id", self.build_item_id(unlockable_data["name"]))
        self.unlockables[item_id] = unlockable_data
        return unlockable_data

    def remove_unlockable(self, item_id):
        self.unlockables.pop(item_id, None)

    def create_unlockable(
        self,
        name,
        repository_id,
        item_type="weapon",
        subtype="pistol",
        loadout_slot="concealedweapon",
        quality=4,
        rarity="common",
        stats=None,
    ):
        item_id = self.build_item_id(name)
        if stats is None:
            stats = DEFAULT_WEAPON_STATS.copy()

        unlockable = {
            "Id": item_id,
            "Guid": self.generate_guid(),
            "Type": item_type,
            "Subtype": subtype,
            "Properties": {
                "Name": f"UI_{item_id}_NAME",
                "Description": f"UI_{item_id}_DESC",
                "Quality": quality,
                "Rarity": rarity,
                "LoadoutSlot": loadout_slot,
                "RepositoryId": repository_id,
                "UnlockOrder": len(self.unlockables) + 1,
                "Gameplay": stats,
            },
            "Rarity": rarity,
            "RMTPrice": 0,
            "GamePrice": 0,
            "IsPurchasable": False,
            "IsPublished": True,
            "IsDroppable": True,
            "Capabilities": [],
            "Qualities": {},
        }

        self.unlockables[item_id] = unlockable
        return unlockable

    def generate_entities(self):
        entities = []

        for item in self.items:
            name = item["name"]
            repo_id = item["repository_id"]
            quantity = item["quantity"]

            itemkey_id = self.generate_entity_id()
            entities.append(
                {
                    "AddEntity": [
                        itemkey_id,
                        {
                            "name": f"ItemKey_{name.upper()}",
                            "factory": "[modules:/zitemrepositorykeyentity.class].pc_entitytype",
                            "blueprint": "[modules:/zitemrepositorykeyentity.class].pc_entityblueprint",
                            "parent": self.parent_root,
                            "properties": {
                                "m_RepositoryId": {"type": "ZGuid", "value": repo_id}
                            },
                        },
                    ]
                }
            )

            for i in range(1, quantity + 1):
                spawner_id = self.generate_entity_id()
                hero_id = self.generate_entity_id()

                entities.append(
                    {
                        "AddEntity": [
                            spawner_id,
                            {
                                "parent": self.parent_root,
                                "name": f"ItemSpawner_{name.upper()}_{i:02d}"
                                if quantity > 1
                                else f"ItemSpawner_{name.upper()}",
                                "factory": "[modules:/zitemspawner.class].pc_entitytype",
                                "blueprint": "[modules:/zitemspawner.class].pc_entityblueprint",
                                "properties": {
                                    "m_rMainItemKey": {
                                        "type": "SEntityTemplateReference",
                                        "value": itemkey_id,
                                    },
                                    "m_bSpawnOnStart": {"type": "bool", "value": True},
                                    "m_eidParent": {
                                        "type": "SEntityTemplateReference",
                                        "value": self.scene_root,
                                    },
                                },
                                "events": {
                                    "Item": {"SetItem": [hero_id]},
                                    "ItemReady": {"PickupIntoPocket": [hero_id]},
                                },
                            },
                        ]
                    }
                )

                entities.append(
                    {
                        "AddEntity": [
                            hero_id,
                            {
                                "parent": self.parent_root,
                                "name": f"HeroItemAction_{name.upper()}_{i:02d}"
                                if quantity > 1
                                else f"HeroItemAction_{name.upper()}",
                                "factory": "[modules:/zheroitemaction.class].pc_entitytype",
                                "blueprint": "[modules:/zheroitemaction.class].pc_entityblueprint",
                                "properties": {},
                            },
                        ]
                    }
                )

        entities.append(
            {
                "AddEntity": [
                    self.parent_root,
                    {
                        "parent": self.scene_root,
                        "name": "CustomLoadout_Root",
                        "factory": "[modules:/zentity.class].pc_entitytype",
                        "blueprint": "[modules:/zentity.class].pc_entityblueprint",
                    },
                ]
            }
        )
        return entities

    def generate_entity_patch_file(self, output_path):
        patch_data = {
            "tempHash": "00D347CBA29EE6BA",
            "tbluHash": "000A263E54999100",
            "patch": self.generate_entities(),
            "patchVersion": 6,
        }
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(patch_data, handle, indent=2)
        return output_path

    def generate_unlockables_file(self, output_path):
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(self.unlockables, handle, indent=2)
        return output_path


def print_common_items():
    print("\n=== Common Item Repository IDs ===")
    for name, repo_id in COMMON_ITEMS.items():
        print(f"{name:.<30} {repo_id}")
    print("=" * 80)


def print_weapon_types():
    print("\n=== ITEM TYPES ===")
    for item_type, subtypes in ITEM_TYPE_OPTIONS.items():
        print(f"{item_type}: {', '.join(subtypes)}")
    print("\n=== LOADOUT SLOTS ===")
    for slot in LOADOUT_SLOT_OPTIONS:
        print(f"  {slot}")
    print("=" * 80)


def add_unlockable_wizard(generator):
    print("\n=== ADD UNLOCKABLE ITEM ===")
    print("This will add an item to your inventory/loadout menu.")

    name = input("Item name (e.g., 'Custom Sniper Rifle'): ").strip()
    if not name:
        print("Error: Name cannot be empty!")
        return

    repo_id = input("Repository ID (GUID): ").strip()
    if not generator.is_valid_repository_id(repo_id):
        print("Error: Repository ID must be a GUID.")
        return

    print("\nItem type:")
    print("  1. Weapon")
    print("  2. Tool")
    print("  3. Gear")
    item_type_choice = input("Choose (1-3, default: 1): ").strip() or "1"
    type_map = {"1": "weapon", "2": "tool", "3": "gear"}
    item_type = type_map.get(item_type_choice, "weapon")

    subtypes = ITEM_TYPE_OPTIONS[item_type]
    print("\nSubtype options:")
    for index, subtype in enumerate(subtypes, start=1):
        print(f"  {index}. {subtype}")
    subtype_choice = input(f"Choose (1-{len(subtypes)}, default: 1): ").strip() or "1"
    try:
        subtype = subtypes[int(subtype_choice) - 1]
    except (ValueError, IndexError):
        subtype = subtypes[0]

    print("\nLoadout slot:")
    for index, slot in enumerate(LOADOUT_SLOT_OPTIONS, start=1):
        print(f"  {index}. {slot}")
    slot_choice = input(f"Choose (1-{len(LOADOUT_SLOT_OPTIONS)}, default: 1): ").strip() or "1"
    try:
        loadout_slot = LOADOUT_SLOT_OPTIONS[int(slot_choice) - 1]
    except (ValueError, IndexError):
        loadout_slot = LOADOUT_SLOT_OPTIONS[0]

    try:
        quality = int(input("Quality (1-4, default: 4): ").strip() or "4")
    except ValueError:
        quality = 4

    print("\nRarity:")
    for index, rarity_name in enumerate(RARITY_OPTIONS, start=1):
        print(f"  {index}. {rarity_name}")
    rarity_choice = input("Choose (1-4, default: 1): ").strip() or "1"
    try:
        rarity = RARITY_OPTIONS[int(rarity_choice) - 1]
    except (ValueError, IndexError):
        rarity = RARITY_OPTIONS[0]

    stats = None
    if item_type == "weapon":
        print("\nWeapon stats (0.0 - 1.0, press Enter for defaults):")
        try:
            stats = {
                "range": float(input("  Range (default: 1.0): ").strip() or "1.0"),
                "damage": float(input("  Damage (default: 1.0): ").strip() or "1.0"),
                "clipsize": float(input("  Clip Size (default: 1.0): ").strip() or "1.0"),
                "rateoffire": float(input("  Rate of Fire (default: 1.0): ").strip() or "1.0"),
            }
        except ValueError:
            print("Invalid stat value, using defaults.")
            stats = DEFAULT_WEAPON_STATS.copy()

    generator.create_unlockable(
        name=name,
        repository_id=repo_id,
        item_type=item_type,
        subtype=subtype,
        loadout_slot=loadout_slot,
        quality=quality,
        rarity=rarity,
        stats=stats,
    )

    spawn_in_mission = input("\nAlso spawn this item in missions? (y/n, default: y): ").strip().lower()
    if spawn_in_mission != "n":
        try:
            quantity = int(input("Quantity to spawn (default 1): ").strip() or "1")
        except ValueError:
            quantity = 0
        if quantity >= 1:
            generator.add_item(name, repo_id, quantity)
        else:
            print("Skipping entity patch - invalid quantity.")


class HitmanGeneratorGUI(tk.Tk if tk else object):
    def __init__(self):
        super().__init__()
        self.generator = HitmanJSONGenerator()
        self.title("Hitman WoA JSON Generator")
        self.geometry("1120x760")
        self.minsize(980, 680)

        self.status_var = tk.StringVar(value="Ready.")
        self.entity_filename_var = tk.StringVar(value=DEFAULT_ENTITY_FILENAME)
        self.unlockables_filename_var = tk.StringVar(value=DEFAULT_UNLOCKABLES_FILENAME)

        self.item_name_var = tk.StringVar()
        self.item_repo_var = tk.StringVar()
        self.item_quantity_var = tk.StringVar(value="1")
        self.item_common_var = tk.StringVar(value=next(iter(COMMON_ITEMS)))

        self.unlock_name_var = tk.StringVar()
        self.unlock_repo_var = tk.StringVar()
        self.unlock_type_var = tk.StringVar(value="weapon")
        self.unlock_subtype_var = tk.StringVar(value=ITEM_TYPE_OPTIONS["weapon"][0])
        self.unlock_slot_var = tk.StringVar(value="concealedweapon")
        self.unlock_quality_var = tk.StringVar(value="4")
        self.unlock_rarity_var = tk.StringVar(value="common")
        self.unlock_common_var = tk.StringVar(value=next(iter(COMMON_ITEMS)))
        self.unlock_spawn_var = tk.BooleanVar(value=True)
        self.unlock_spawn_quantity_var = tk.StringVar(value="1")

        self.weapon_stat_vars = {
            stat_name: tk.StringVar(value=str(default_value))
            for stat_name, default_value in DEFAULT_WEAPON_STATS.items()
        }
        self.project_summary_var = tk.StringVar()

        self._build_ui()
        self.refresh_views()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Hitman World of Assassination JSON Generator",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Use QuickSearch to find repository IDs, then add mission spawns or unlockables.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Button(
            header,
            text="Open Repo ID Search",
            command=self.open_repo_search,
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        mission_tab = ttk.Frame(notebook, padding=12)
        unlockables_tab = ttk.Frame(notebook, padding=12)
        project_tab = ttk.Frame(notebook, padding=12)
        reference_tab = ttk.Frame(notebook, padding=12)

        notebook.add(mission_tab, text="Mission Items")
        notebook.add(unlockables_tab, text="Unlockables")
        notebook.add(project_tab, text="Generate Files")
        notebook.add(reference_tab, text="Reference")

        self._build_mission_tab(mission_tab)
        self._build_unlockables_tab(unlockables_tab)
        self._build_project_tab(project_tab)
        self._build_reference_tab(reference_tab)

        ttk.Label(self, textvariable=self.status_var, padding=(12, 0, 12, 12)).grid(
            row=2, column=0, sticky="ew"
        )

    def _build_mission_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(parent, text="Add Item To Mission Patch", padding=12)
        form.grid(row=0, column=0, sticky="ew")
        for column in range(4):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Item Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.item_name_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Repository ID").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.item_repo_var).grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Quantity").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.item_quantity_var).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Common Item").grid(row=0, column=3, sticky="w")
        ttk.Combobox(
            form,
            textvariable=self.item_common_var,
            values=list(COMMON_ITEMS.keys()),
            state="readonly",
        ).grid(row=1, column=3, sticky="ew")

        ttk.Button(form, text="Use Common Item", command=self.apply_common_item_to_mission).grid(
            row=2, column=3, sticky="e", pady=(8, 0)
        )
        ttk.Button(form, text="Add Mission Item", command=self.add_mission_item).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        table_frame = ttk.LabelFrame(parent, text="Mission Spawn Queue", padding=12)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.items_tree = ttk.Treeview(
            table_frame,
            columns=("name", "repo_id", "quantity"),
            show="headings",
            height=14,
        )
        self.items_tree.heading("name", text="Item Name")
        self.items_tree.heading("repo_id", text="Repository ID")
        self.items_tree.heading("quantity", text="Quantity")
        self.items_tree.column("name", width=220, anchor="w")
        self.items_tree.column("repo_id", width=360, anchor="w")
        self.items_tree.column("quantity", width=90, anchor="center")
        self.items_tree.grid(row=0, column=0, sticky="nsew")

        items_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.items_tree.yview)
        items_scrollbar.grid(row=0, column=1, sticky="ns")
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)

        ttk.Button(table_frame, text="Remove Selected Item", command=self.remove_selected_item).grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )

    def _build_unlockables_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(parent, text="Add Unlockable", padding=12)
        form.grid(row=0, column=0, sticky="ew")
        for column in range(4):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Item Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.unlock_name_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Repository ID").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.unlock_repo_var).grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Type").grid(row=0, column=2, sticky="w")
        unlock_type_combo = ttk.Combobox(
            form,
            textvariable=self.unlock_type_var,
            values=list(ITEM_TYPE_OPTIONS.keys()),
            state="readonly",
        )
        unlock_type_combo.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        unlock_type_combo.bind("<<ComboboxSelected>>", self.update_subtype_options)

        ttk.Label(form, text="Subtype").grid(row=0, column=3, sticky="w")
        self.unlock_subtype_combo = ttk.Combobox(
            form,
            textvariable=self.unlock_subtype_var,
            values=ITEM_TYPE_OPTIONS["weapon"],
            state="readonly",
        )
        self.unlock_subtype_combo.grid(row=1, column=3, sticky="ew")

        ttk.Label(form, text="Loadout Slot").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(
            form,
            textvariable=self.unlock_slot_var,
            values=LOADOUT_SLOT_OPTIONS,
            state="readonly",
        ).grid(row=3, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Quality").grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Combobox(
            form,
            textvariable=self.unlock_quality_var,
            values=["1", "2", "3", "4"],
            state="readonly",
        ).grid(row=3, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Rarity").grid(row=2, column=2, sticky="w", pady=(8, 0))
        ttk.Combobox(
            form,
            textvariable=self.unlock_rarity_var,
            values=RARITY_OPTIONS,
            state="readonly",
        ).grid(row=3, column=2, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Common Item").grid(row=2, column=3, sticky="w", pady=(8, 0))
        ttk.Combobox(
            form,
            textvariable=self.unlock_common_var,
            values=list(COMMON_ITEMS.keys()),
            state="readonly",
        ).grid(row=3, column=3, sticky="ew")

        ttk.Button(form, text="Use Common Item", command=self.apply_common_item_to_unlockable).grid(
            row=4, column=3, sticky="e", pady=(8, 0)
        )

        self.stats_frame = ttk.LabelFrame(form, text="Weapon Stats", padding=10)
        self.stats_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        for column, stat_name in enumerate(DEFAULT_WEAPON_STATS):
            self.stats_frame.columnconfigure(column, weight=1)
            ttk.Label(self.stats_frame, text=stat_name.title()).grid(row=0, column=column, sticky="w")
            ttk.Entry(self.stats_frame, textvariable=self.weapon_stat_vars[stat_name]).grid(
                row=1, column=column, sticky="ew", padx=(0, 8)
            )

        spawn_frame = ttk.Frame(form)
        spawn_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        spawn_frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(
            spawn_frame,
            text="Also add this item to the mission patch",
            variable=self.unlock_spawn_var,
            command=self.update_spawn_state,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(spawn_frame, text="Spawn Quantity").grid(row=0, column=1, sticky="e")
        self.spawn_quantity_entry = ttk.Entry(
            spawn_frame,
            textvariable=self.unlock_spawn_quantity_var,
            width=8,
        )
        self.spawn_quantity_entry.grid(row=0, column=2, sticky="e", padx=(8, 0))

        ttk.Button(form, text="Add Unlockable", command=self.add_unlockable_item).grid(
            row=6, column=0, sticky="w", pady=(12, 0)
        )

        table_frame = ttk.LabelFrame(parent, text="Unlockables", padding=12)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.unlockables_tree = ttk.Treeview(
            table_frame,
            columns=("item_id", "type", "subtype", "slot", "repo_id"),
            show="headings",
            height=14,
        )
        self.unlockables_tree.heading("item_id", text="Unlockable ID")
        self.unlockables_tree.heading("type", text="Type")
        self.unlockables_tree.heading("subtype", text="Subtype")
        self.unlockables_tree.heading("slot", text="Loadout Slot")
        self.unlockables_tree.heading("repo_id", text="Repository ID")
        self.unlockables_tree.column("item_id", width=250, anchor="w")
        self.unlockables_tree.column("type", width=90, anchor="center")
        self.unlockables_tree.column("subtype", width=120, anchor="center")
        self.unlockables_tree.column("slot", width=140, anchor="center")
        self.unlockables_tree.column("repo_id", width=320, anchor="w")
        self.unlockables_tree.grid(row=0, column=0, sticky="nsew")

        unlock_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.unlockables_tree.yview)
        unlock_scrollbar.grid(row=0, column=1, sticky="ns")
        self.unlockables_tree.configure(yscrollcommand=unlock_scrollbar.set)

        ttk.Button(
            table_frame,
            text="Remove Selected Unlockable",
            command=self.remove_selected_unlockable,
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.update_subtype_options()
        self.update_spawn_state()

    def _build_project_tab(self, parent):
        parent.columnconfigure(0, weight=1)

        summary = ttk.LabelFrame(parent, text="Project Summary", padding=12)
        summary.grid(row=0, column=0, sticky="ew")
        summary.columnconfigure(0, weight=1)
        ttk.Label(summary, textvariable=self.project_summary_var, justify="left").grid(
            row=0, column=0, sticky="w"
        )

        files_frame = ttk.LabelFrame(parent, text="Output Files", padding=12)
        files_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        files_frame.columnconfigure(1, weight=1)

        ttk.Label(files_frame, text="Entity Patch Filename").grid(row=0, column=0, sticky="w")
        ttk.Entry(files_frame, textvariable=self.entity_filename_var).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )

        ttk.Label(files_frame, text="Unlockables Filename").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(files_frame, textvariable=self.unlockables_filename_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0)
        )

        actions = ttk.Frame(parent)
        actions.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(actions, text="Generate JSON Files", command=self.generate_files).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(actions, text="Clear Project", command=self.clear_project).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        help_text = (
            "Generate to any folder you want. The tool writes the same JSON structure as the original script.\n"
            "content/chunk0/<entity patch file> for mission spawns\n"
            "<mod root>/<unlockables file> for unlockables"
        )
        ttk.Label(parent, text=help_text, justify="left").grid(row=3, column=0, sticky="w", pady=(16, 0))

    def _build_reference_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(parent, text="Common Repository IDs", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        self.reference_tree = ttk.Treeview(
            left,
            columns=("name", "repo_id"),
            show="headings",
            height=16,
        )
        self.reference_tree.heading("name", text="Item")
        self.reference_tree.heading("repo_id", text="Repository ID")
        self.reference_tree.column("name", width=220, anchor="w")
        self.reference_tree.column("repo_id", width=360, anchor="w")
        self.reference_tree.grid(row=0, column=0, sticky="nsew")

        ref_scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.reference_tree.yview)
        ref_scrollbar.grid(row=0, column=1, sticky="ns")
        self.reference_tree.configure(yscrollcommand=ref_scrollbar.set)

        right = ttk.LabelFrame(parent, text="Type Reference", padding=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)

        lines = ["Item types and subtypes:"]
        for item_type, subtypes in ITEM_TYPE_OPTIONS.items():
            lines.append(f"{item_type}: {', '.join(subtypes)}")
        lines.append("")
        lines.append("Loadout slots:")
        lines.extend(LOADOUT_SLOT_OPTIONS)
        lines.append("")
        lines.append("Repository search:")
        lines.append(REPO_SEARCH_URL)
        ttk.Label(right, text="\n".join(lines), justify="left").grid(row=0, column=0, sticky="nw")

        for name, repo_id in COMMON_ITEMS.items():
            self.reference_tree.insert("", "end", values=(name, repo_id))

    def set_status(self, message):
        self.status_var.set(message)

    def open_repo_search(self):
        webbrowser.open(REPO_SEARCH_URL)
        self.set_status("Opened repository ID search in your browser.")

    def apply_common_item_to_mission(self):
        name = self.item_common_var.get()
        self.item_name_var.set(name)
        self.item_repo_var.set(COMMON_ITEMS[name])
        self.set_status(f"Loaded common item '{name}' into the mission form.")

    def apply_common_item_to_unlockable(self):
        name = self.unlock_common_var.get()
        self.unlock_name_var.set(name)
        self.unlock_repo_var.set(COMMON_ITEMS[name])
        self.set_status(f"Loaded common item '{name}' into the unlockable form.")

    def update_subtype_options(self, event=None):
        item_type = self.unlock_type_var.get()
        options = ITEM_TYPE_OPTIONS[item_type]
        self.unlock_subtype_combo["values"] = options
        if self.unlock_subtype_var.get() not in options:
            self.unlock_subtype_var.set(options[0])
        self.update_stats_state()

    def update_stats_state(self):
        state = "normal" if self.unlock_type_var.get() == "weapon" else "disabled"
        for child in self.stats_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                child.configure(state=state)

    def update_spawn_state(self):
        state = "normal" if self.unlock_spawn_var.get() else "disabled"
        self.spawn_quantity_entry.configure(state=state)

    def _validate_name_repo(self, name, repo_id):
        if not name.strip():
            raise ValueError("Item name cannot be empty.")
        if not self.generator.is_valid_repository_id(repo_id):
            raise ValueError("Repository ID must be a GUID.")

    def add_mission_item(self):
        try:
            name = self.item_name_var.get().strip()
            repo_id = self.item_repo_var.get().strip()
            self._validate_name_repo(name, repo_id)
            quantity = int(self.item_quantity_var.get().strip() or "1")
            if quantity < 1:
                raise ValueError("Quantity must be at least 1.")
        except ValueError as error:
            messagebox.showerror("Invalid Mission Item", str(error))
            return

        self.generator.add_item(name, repo_id, quantity)
        self.item_name_var.set("")
        self.item_repo_var.set("")
        self.item_quantity_var.set("1")
        self.refresh_views()
        self.set_status(f"Added mission item '{name}' x{quantity}.")

    def add_unlockable_item(self):
        unlockable = None
        try:
            name = self.unlock_name_var.get().strip()
            repo_id = self.unlock_repo_var.get().strip()
            self._validate_name_repo(name, repo_id)
            quality = int(self.unlock_quality_var.get())
            if quality < 1 or quality > 4:
                raise ValueError("Quality must be between 1 and 4.")

            stats = None
            if self.unlock_type_var.get() == "weapon":
                stats = {}
                for stat_name, stat_var in self.weapon_stat_vars.items():
                    stats[stat_name] = float(stat_var.get().strip() or "1.0")

            unlockable = self.generator.create_unlockable(
                name=name,
                repository_id=repo_id,
                item_type=self.unlock_type_var.get(),
                subtype=self.unlock_subtype_var.get(),
                loadout_slot=self.unlock_slot_var.get(),
                quality=quality,
                rarity=self.unlock_rarity_var.get(),
                stats=stats,
            )

            if self.unlock_spawn_var.get():
                spawn_quantity = int(self.unlock_spawn_quantity_var.get().strip() or "1")
                if spawn_quantity < 1:
                    raise ValueError("Spawn quantity must be at least 1.")
                self.generator.add_item(name, repo_id, spawn_quantity)
        except ValueError as error:
            if unlockable is not None:
                self.generator.remove_unlockable(unlockable["Id"])
            messagebox.showerror("Invalid Unlockable", str(error))
            return

        self.unlock_name_var.set("")
        self.unlock_repo_var.set("")
        self.unlock_quality_var.set("4")
        self.unlock_rarity_var.set("common")
        self.unlock_spawn_quantity_var.set("1")
        for stat_name, stat_var in self.weapon_stat_vars.items():
            stat_var.set(str(DEFAULT_WEAPON_STATS[stat_name]))

        self.refresh_views()
        self.set_status(f"Added unlockable '{unlockable['Id']}'.")

    def remove_selected_item(self):
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showinfo("Remove Mission Item", "Select a mission item first.")
            return

        index = int(selection[0])
        removed = self.generator.items[index]
        self.generator.remove_item(index)
        self.refresh_views()
        self.set_status(f"Removed mission item '{removed['name']}'.")

    def remove_selected_unlockable(self):
        selection = self.unlockables_tree.selection()
        if not selection:
            messagebox.showinfo("Remove Unlockable", "Select an unlockable first.")
            return

        item_id = selection[0]
        self.generator.remove_unlockable(item_id)
        self.refresh_views()
        self.set_status(f"Removed unlockable '{item_id}'.")

    def refresh_views(self):
        for item_id in self.items_tree.get_children():
            self.items_tree.delete(item_id)
        for index, item in enumerate(self.generator.items):
            self.items_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(item["name"], item["repository_id"], item["quantity"]),
            )

        for item_id in self.unlockables_tree.get_children():
            self.unlockables_tree.delete(item_id)
        for unlockable_id, unlockable in self.generator.unlockables.items():
            props = unlockable["Properties"]
            self.unlockables_tree.insert(
                "",
                "end",
                iid=unlockable_id,
                values=(
                    unlockable_id,
                    unlockable["Type"],
                    unlockable["Subtype"],
                    props["LoadoutSlot"],
                    props["RepositoryId"],
                ),
            )

        self.project_summary_var.set(
            f"Mission patch items: {len(self.generator.items)}\n"
            f"Unlockables: {len(self.generator.unlockables)}"
        )

    def generate_files(self):
        if not self.generator.items and not self.generator.unlockables:
            messagebox.showerror("Nothing To Generate", "Add at least one mission item or unlockable first.")
            return

        output_dir = filedialog.askdirectory(
            title="Choose where to save the generated JSON files",
            initialdir=os.getcwd(),
        )
        if not output_dir:
            return

        generated_files = []
        if self.generator.items:
            entity_name = self.generator.normalize_json_filename(
                self.entity_filename_var.get(),
                DEFAULT_ENTITY_FILENAME,
            )
            entity_path = os.path.join(output_dir, entity_name)
            self.generator.generate_entity_patch_file(entity_path)
            generated_files.append(entity_path)

        if self.generator.unlockables:
            unlockables_name = self.generator.normalize_json_filename(
                self.unlockables_filename_var.get(),
                DEFAULT_UNLOCKABLES_FILENAME,
            )
            unlockables_path = os.path.join(output_dir, unlockables_name)
            self.generator.generate_unlockables_file(unlockables_path)
            generated_files.append(unlockables_path)

        messagebox.showinfo("Files Generated", "Created:\n\n" + "\n".join(generated_files))
        self.set_status(f"Generated {len(generated_files)} JSON file(s) in {output_dir}.")

    def clear_project(self):
        confirmed = messagebox.askyesno(
            "Clear Project",
            "Remove all queued mission items and unlockables?",
        )
        if not confirmed:
            return

        self.generator.clear()
        self.refresh_views()
        self.set_status("Cleared the current project.")


def cli_main():
    print("=" * 80)
    print("HITMAN WORLD OF ASSASSINATION - JSON GENERATOR")
    print("=" * 80)

    generator = HitmanJSONGenerator()

    while True:
        print("\n--- MAIN MENU ---")
        print("1. Add item to entity patch (spawns in mission)")
        print("2. Add unlockable item (adds to inventory)")
        print("3. View common item repository IDs")
        print("4. View weapon types & loadout slots")
        print("5. View current items")
        print("6. Generate JSON files")
        print("7. Exit")

        choice = input("\nEnter your choice (1-7): ").strip()

        if choice == "1":
            print("\n--- ADD ITEM TO ENTITY PATCH ---")
            name = input("Item name (e.g., 'COIN', 'FIBERWIRE'): ").strip()
            repo_id = input("Repository ID (GUID format): ").strip()

            if not name:
                print("Error: Item name cannot be empty!")
                continue
            if not generator.is_valid_repository_id(repo_id):
                print("Error: Repository ID must be a GUID.")
                continue

            try:
                quantity = int(input("Quantity (default 1): ").strip() or "1")
                if quantity < 1:
                    raise ValueError
            except ValueError:
                print("Error: Quantity must be at least 1!")
                continue

            generator.add_item(name, repo_id, quantity)
            print(f"Added: {quantity}x {name}")

        elif choice == "2":
            add_unlockable_wizard(generator)

        elif choice == "3":
            print_common_items()

        elif choice == "4":
            print_weapon_types()

        elif choice == "5":
            print("\n--- CURRENT ITEMS ---")
            print(f"\nEntity Patch Items ({len(generator.items)}):")
            if not generator.items:
                print("  No items added yet.")
            else:
                for idx, item in enumerate(generator.items, 1):
                    print(f"  {idx}. {item['quantity']}x {item['name']} ({item['repository_id']})")

            print(f"\nUnlockable Items ({len(generator.unlockables)}):")
            if not generator.unlockables:
                print("  No unlockables added yet.")
            else:
                for idx, (item_id, unlockable) in enumerate(generator.unlockables.items(), 1):
                    props = unlockable["Properties"]
                    print(f"  {idx}. {item_id} - {unlockable['Type']}/{unlockable['Subtype']} ({props['LoadoutSlot']})")

        elif choice == "6":
            if not generator.items and not generator.unlockables:
                print("\nError: No items added! Please add items first.")
                continue

            print("\n--- GENERATE JSON FILES ---")

            if generator.items:
                entity_filename = input(
                    f"Entity patch filename (default: {DEFAULT_ENTITY_FILENAME}): "
                ).strip()
                entity_filename = generator.normalize_json_filename(
                    entity_filename,
                    DEFAULT_ENTITY_FILENAME,
                )
                entity_path = os.path.join(os.getcwd(), entity_filename)
                generator.generate_entity_patch_file(entity_path)
                print(f"Entity patch file generated: {entity_path}")
                print(f"Copy to: YourModFolder/content/chunk0/{entity_filename}")

            if generator.unlockables:
                unlockables_filename = input(
                    f"\nUnlockables filename (default: {DEFAULT_UNLOCKABLES_FILENAME}): "
                ).strip()
                unlockables_filename = generator.normalize_json_filename(
                    unlockables_filename,
                    DEFAULT_UNLOCKABLES_FILENAME,
                )
                unlockables_path = os.path.join(os.getcwd(), unlockables_filename)
                generator.generate_unlockables_file(unlockables_path)
                print(f"Unlockables file generated: {unlockables_path}")
                print(f"Copy to: YourModFolder/{unlockables_filename}")

            restart = input("\nStart a new project? (y/n): ").strip().lower()
            if restart == "y":
                generator.clear()
                print("New project started!")

        elif choice == "7":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice! Please enter 1-7.")


def main():
    if "--cli" in sys.argv:
        cli_main()
        return

    if tk is None:
        print("Tkinter is not available in this Python installation. Run with --cli instead.")
        return

    app = HitmanGeneratorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
