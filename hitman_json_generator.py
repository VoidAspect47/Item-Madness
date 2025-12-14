import json
import random
import os

class HitmanJSONGenerator:
    def __init__(self):
        self.items = []
        self.unlockables = {}
        self.parent_root = "feed9d3063a95cec"
        self.scene_root = "158cb860b1fce56d"
        self.entity_counter = 0

    def generate_entity_id(self, prefix="feed"):
        """Generate a unique 16-character hex entity ID"""
        return prefix + "".join(random.choices("0123456789abcdef", k=12))

    def generate_guid(self):
        """Generate a custom GUID for unlockables"""
        parts = [
            "feed" + "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=4)),
            "".join(random.choices("0123456789abcdef", k=12))
        ]
        return "-".join(parts)

    def add_item(self, name, repository_id, quantity=1):
        """Add an item to the entity patch generation queue"""
        self.items.append({
            "name": name,
            "repository_id": repository_id,
            "quantity": quantity
        })
        print(f"Added to entity patch: {quantity}x {name} (Repo ID: {repository_id})")

    def add_unlockable(self, unlockable_data):
        """Add an unlockable item"""
        item_id = unlockable_data.get("Id", f"CUSTOM_{unlockable_data['name'].upper()}")
        self.unlockables[item_id] = unlockable_data
        print(f"Added to unlockables: {unlockable_data['name']} (ID: {item_id})")

    def create_unlockable(self, name, repository_id, item_type="weapon", subtype="pistol",
                         loadout_slot="concealedweapon", quality=4, rarity="common",
                         stats=None):
        """Create an unlockable item with default values"""
        item_id = f"CUSTOM_{name.upper().replace(' ', '_')}"

        if stats is None:
            stats = {"range": 1.0, "damage": 1.0, "clipsize": 1.0, "rateoffire": 1.0}

        unlockable = {
            "Id": item_id,
            "Guid": self.generate_guid(),
            "Type": item_type,
            "Subtype": subtype,
            "Properties": {
                "Name": f"UI_{name.upper().replace(' ', '_')}_NAME",
                "Description": f"UI_{name.upper().replace(' ', '_')}_DESC",
                "Quality": quality,
                "Rarity": rarity,
                "LoadoutSlot": loadout_slot,
                "RepositoryId": repository_id,
                "UnlockOrder": len(self.unlockables) + 1,
                "Gameplay": stats
            },
            "Rarity": rarity,
            "RMTPrice": 0,
            "GamePrice": 0,
            "IsPurchasable": False,
            "IsPublished": True,
            "IsDroppable": True,
            "Capabilities": [],
            "Qualities": {}
        }

        self.unlockables[item_id] = unlockable
        return unlockable

    def generate_entities(self):
        """Generate all entities for the entity patch"""
        entities = []

        for item in self.items:
            name = item["name"]
            repo_id = item["repository_id"]
            quantity = item["quantity"]

            # Generate ItemKey entity (only one per item type)
            itemkey_id = self.generate_entity_id()
            itemkey_entity = {
                "AddEntity": [
                    itemkey_id,
                    {
                        "name": f"ItemKey_{name.upper()}",
                        "factory": "[modules:/zitemrepositorykeyentity.class].pc_entitytype",
                        "blueprint": "[modules:/zitemrepositorykeyentity.class].pc_entityblueprint",
                        "parent": self.parent_root,
                        "properties": {
                            "m_RepositoryId": {
                                "type": "ZGuid",
                                "value": repo_id
                            }
                        }
                    }
                ]
            }
            entities.append(itemkey_entity)

            # Generate ItemSpawner and HeroItemAction for each quantity
            for i in range(1, quantity + 1):
                spawner_id = self.generate_entity_id()
                hero_id = self.generate_entity_id()

                # ItemSpawner entity
                spawner_entity = {
                    "AddEntity": [
                        spawner_id,
                        {
                            "parent": self.parent_root,
                            "name": f"ItemSpawner_{name.upper()}_{i:02d}" if quantity > 1 else f"ItemSpawner_{name.upper()}",
                            "factory": "[modules:/zitemspawner.class].pc_entitytype",
                            "blueprint": "[modules:/zitemspawner.class].pc_entityblueprint",
                            "properties": {
                                "m_rMainItemKey": {
                                    "type": "SEntityTemplateReference",
                                    "value": itemkey_id
                                },
                                "m_bSpawnOnStart": {
                                    "type": "bool",
                                    "value": True
                                },
                                "m_eidParent": {
                                    "type": "SEntityTemplateReference",
                                    "value": self.scene_root
                                }
                            },
                            "events": {
                                "Item": {
                                    "SetItem": [hero_id]
                                },
                                "ItemReady": {
                                    "PickupIntoPocket": [hero_id]
                                }
                            }
                        }
                    ]
                }
                entities.append(spawner_entity)

                # HeroItemAction entity
                hero_entity = {
                    "AddEntity": [
                        hero_id,
                        {
                            "parent": self.parent_root,
                            "name": f"HeroItemAction_{name.upper()}_{i:02d}" if quantity > 1 else f"HeroItemAction_{name.upper()}",
                            "factory": "[modules:/zheroitemaction.class].pc_entitytype",
                            "blueprint": "[modules:/zheroitemaction.class].pc_entityblueprint",
                            "properties": {}
                        }
                    ]
                }
                entities.append(hero_entity)

        # Add root entity at the end
        root_entity = {
            "AddEntity": [
                self.parent_root,
                {
                    "parent": self.scene_root,
                    "name": "CustomLoadout_Root",
                    "factory": "[modules:/zentity.class].pc_entitytype",
                    "blueprint": "[modules:/zentity.class].pc_entityblueprint"
                }
            ]
        }
        entities.append(root_entity)

        return entities

    def generate_entity_patch_file(self, output_path):
        """Generate the complete entity patch JSON file"""
        patch_data = {
            "tempHash": "00D347CBA29EE6BA",
            "tbluHash": "000A263E54999100",
            "patch": self.generate_entities(),
            "patchVersion": 6
        }

        with open(output_path, 'w') as f:
            json.dump(patch_data, f, indent=2)

        print(f"\nEntity patch file generated: {output_path}")
        return output_path

    def generate_unlockables_file(self, output_path):
        """Generate the unlockables JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.unlockables, f, indent=2)

        print(f"\nUnlockables file generated: {output_path}")
        return output_path

def print_common_items():
    """Display common item repository IDs"""
    items = {
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
        "Briefcase": "b20fc045-e453-4280-8b18-b0a0e5c17236"
    }

    print("\n=== Common Item Repository IDs ===")
    for name, repo_id in items.items():
        print(f"{name:.<30} {repo_id}")
    print("=" * 80)

def print_weapon_types():
    """Display weapon type and subtype options"""
    print("\n=== WEAPON TYPES ===")
    print("Type: weapon")
    print("  Subtypes: pistol, smg, shotgun, assaultrifle, sniperrifle, melee")
    print("\nType: tool")
    print("  Subtypes: distraction, poison, explosive, remote")
    print("\nType: gear")
    print("  Subtypes: container, disguise")
    print("\n=== LOADOUT SLOTS ===")
    print("  concealedweapon - Small weapons (pistols, fiber wire)")
    print("  carriedweapon   - Large weapons (rifles, shotguns, SMGs)")
    print("  gear1-3         - Gear slots")
    print("  stashpoint      - Items in briefcase/container")
    print("=" * 80)

def add_unlockable_wizard(generator):
    """Interactive wizard for adding unlockables"""
    print("\n=== ADD UNLOCKABLE ITEM ===")
    print("This will add an item to your inventory/loadout menu.")

    # Basic info
    name = input("Item name (e.g., 'Custom Sniper Rifle'): ").strip()
    if not name:
        print("Error: Name cannot be empty!")
        return

    repo_id = input("Repository ID (GUID): ").strip()
    if not repo_id:
        print("Error: Repository ID cannot be empty!")
        return

    # Item type
    print("\nItem type:")
    print("  1. Weapon")
    print("  2. Tool")
    print("  3. Gear")
    item_type_choice = input("Choose (1-3, default: 1): ").strip() or "1"

    type_map = {"1": "weapon", "2": "tool", "3": "gear"}
    item_type = type_map.get(item_type_choice, "weapon")

    # Subtype
    if item_type == "weapon":
        print("\nWeapon subtype:")
        print("  1. Pistol")
        print("  2. SMG")
        print("  3. Shotgun")
        print("  4. Assault Rifle")
        print("  5. Sniper Rifle")
        print("  6. Melee")
        subtype_choice = input("Choose (1-6, default: 1): ").strip() or "1"
        subtype_map = {
            "1": "pistol", "2": "smg", "3": "shotgun",
            "4": "assaultrifle", "5": "sniperrifle", "6": "melee"
        }
        subtype = subtype_map.get(subtype_choice, "pistol")
    else:
        subtype = input(f"Enter subtype for {item_type}: ").strip() or "misc"

    # Loadout slot
    print("\nLoadout slot:")
    print("  1. Concealed Weapon (small weapons)")
    print("  2. Carried Weapon (large weapons)")
    print("  3. Gear Slot")
    slot_choice = input("Choose (1-3, default: 1): ").strip() or "1"
    slot_map = {
        "1": "concealedweapon",
        "2": "carriedweapon",
        "3": "gear1"
    }
    loadout_slot = slot_map.get(slot_choice, "concealedweapon")

    # Quality and rarity
    quality = int(input("Quality (1-4, default: 4): ").strip() or "4")

    print("\nRarity:")
    print("  1. Common")
    print("  2. Rare")
    print("  3. Epic")
    print("  4. Legendary")
    rarity_choice = input("Choose (1-4, default: 1): ").strip() or "1"
    rarity_map = {"1": "common", "2": "rare", "3": "epic", "4": "legendary"}
    rarity = rarity_map.get(rarity_choice, "common")

    # Stats (for weapons)
    stats = None
    if item_type == "weapon":
        print("\nWeapon stats (0.0 - 1.0, press Enter for defaults):")
        try:
            range_stat = float(input("  Range (default: 1.0): ").strip() or "1.0")
            damage_stat = float(input("  Damage (default: 1.0): ").strip() or "1.0")
            clipsize_stat = float(input("  Clip Size (default: 1.0): ").strip() or "1.0")
            rof_stat = float(input("  Rate of Fire (default: 1.0): ").strip() or "1.0")
            stats = {
                "range": range_stat,
                "damage": damage_stat,
                "clipsize": clipsize_stat,
                "rateoffire": rof_stat
            }
        except ValueError:
            print("Invalid stat value, using defaults.")
            stats = {"range": 1.0, "damage": 1.0, "clipsize": 1.0, "rateoffire": 1.0}

    # Create the unlockable
    generator.create_unlockable(
        name=name,
        repository_id=repo_id,
        item_type=item_type,
        subtype=subtype,
        loadout_slot=loadout_slot,
        quality=quality,
        rarity=rarity,
        stats=stats
    )

    # Ask if they want to also spawn it in missions
    spawn_in_mission = input("\nAlso spawn this item in missions? (y/n, default: y): ").strip().lower()
    if spawn_in_mission != 'n':
        try:
            quantity = int(input("Quantity to spawn (default 1): ").strip() or "1")
            if quantity >= 1:
                generator.add_item(name, repo_id, quantity)
            else:
                print("Skipping entity patch - invalid quantity.")
        except ValueError:
            print("Skipping entity patch - invalid quantity.")

def main():
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
            if not name:
                print("Error: Item name cannot be empty!")
                continue

            repo_id = input("Repository ID (GUID format): ").strip()
            if not repo_id:
                print("Error: Repository ID cannot be empty!")
                continue

            try:
                quantity = int(input("Quantity (default 1): ").strip() or "1")
                if quantity < 1:
                    print("Error: Quantity must be at least 1!")
                    continue
            except ValueError:
                print("Error: Invalid quantity!")
                continue

            generator.add_item(name, repo_id, quantity)

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
                    props = unlockable['Properties']
                    print(f"  {idx}. {item_id} - {unlockable['Type']}/{unlockable['Subtype']} ({props['LoadoutSlot']})")

        elif choice == "6":
            if not generator.items and not generator.unlockables:
                print("\nError: No items added! Please add items first.")
                continue

            print("\n--- GENERATE JSON FILES ---")

            # Entity patch
            if generator.items:
                entity_filename = input("Entity patch filename (default: 00D347CBA29EE6BA.entity.patch.json): ").strip()
                if not entity_filename:
                    entity_filename = "00D347CBA29EE6BA.entity.patch.json"
                if not entity_filename.endswith('.json'):
                    entity_filename += '.json'

                entity_path = os.path.join(os.getcwd(), entity_filename)
                generator.generate_entity_patch_file(entity_path)
                print(f"Copy to: YourModFolder/content/chunk0/{entity_filename}")

            # Unlockables
            if generator.unlockables:
                unlockables_filename = input("\nUnlockables filename (default: unlockables.json): ").strip()
                if not unlockables_filename:
                    unlockables_filename = "unlockables.json"
                if not unlockables_filename.endswith('.json'):
                    unlockables_filename += '.json'

                unlockables_path = os.path.join(os.getcwd(), unlockables_filename)
                generator.generate_unlockables_file(unlockables_path)
                print(f"Copy to: YourModFolder/{unlockables_filename}")

            restart = input("\nStart a new project? (y/n): ").strip().lower()
            if restart == 'y':
                generator = HitmanJSONGenerator()
                print("New project started!")

        elif choice == "7":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice! Please enter 1-7.")

if __name__ == "__main__":
    main()
