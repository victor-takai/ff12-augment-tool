import os
import re
import json
from enum import Enum

class FirstAugment(Enum):
    STABILITY =                 0x8000_0000 # Null Knockback
    SAFETY =                    0x4000_0000
    ACCURACY_BOOST =            0x2000_0000 # Null Evade
    SHIELD_BOOST =              0x1000_0000 # Shield Block
    EVASION_BOOST =             0x0800_0000 # Parry
    LAST_STAND =                0x0400_0000
    COUNTER =                   0x0200_0000
    COUNTER_BOOST =             0x0100_0000 # Counter Plus
    SPELLBREAKER =              0x0080_0000
    BRAWLER =                   0x0040_0000
    ADRENALINE =                0x0020_0000
    FOCUS =                     0x0010_0000
    LOBBYING =                  0x0008_0000 # ???
    COMBO_BOOST =               0x0004_0000 # Gengi Gloves Effect
    ITEM_BOOST =                0x0002_0000 # Item Plus
    MEDICINE_REVERSE =          0x0001_0000 # Item Reverse
    WEATHERPROOF =              0x0000_8000 # Null Weather & Terrain
    THIEVERY =                  0x0000_4000 # Thief Cuffs Effect
    SABOTEUR =                  0x0000_2000 # Null Vit
    MAGICK_LORE_1 =             0x0000_1000
    WARMAGE =                   0x0000_0800
    MARTYR =                    0x0000_0400
    MAGICK_LORE_2 =             0x0000_0200
    HEADSMAN =                  0x0000_0100
    MAGICK_LORE_3 =             0x0000_0080
    TREASURE_HUNTER =           0x0000_0040 # Diamong Armlet Effect
    MAGICK_LORE_4 =             0x0000_0020
    DOUBLE_EXP =                0x0000_0010
    DOUBLE_LP =                 0x0000_0008
    NO_EXP =                    0x0000_0004
    SPELLBOUND =                0x0000_0002
    PIERCING_MAGICK =           0x0000_0001
    NONE =                      0x0000_0000

class SecondAugment(Enum):
    OFFERING =                  0x8000_0000 # Turtleshell Choker Effect
    MUFFLE =                    0x4000_0000
    LIFE_CLOAK =                0x2000_0000
    BATTLE_LORE_1 =             0x1000_0000
    PARSIMONY =                 0x0800_0000 # Half MP Cost
    TREAD_LIGHTLY =             0x0400_0000 # Steel Polyens Effect
    UNUSED =                    0x0200_0000
    EMPTINESS =                 0x0100_0000 # Zero MP
    RESIST_PIERCE_DAMAGE =      0x0080_0000 # Resist Guns & Measures
    ANTI_LIBRA =                0x0040_0000
    BATTLE_LORE_2 =             0x0020_0000
    BATTLE_LORE_3 =             0x0010_0000
    BATTLE_LORE_4 =             0x0008_0000
    BATTLE_LORE_5 =             0x0004_0000
    BATTLE_LORE_6 =             0x0002_0000
    BATTLE_LORE_7 =             0x0001_0000
    STONESKIN =                 0x0000_8000 # Damage Resist
    ATTACK_BOOST =              0x0000_4000 # Attack Plus
    DOUBLE_EDGED =              0x0000_2000 # HP Devour
    SPELLSPRING =               0x0000_1000 # Mana Spring
    ELEMENTAL_SHIFT =           0x0000_0800 # Shift
    CELERITY =                  0x0000_0400 # Attack CT 0
    SWIFT_CAST =                0x0000_0200 # Magick CT 0
    ATTACK_IMMUNITY =           0x0000_0100 # Immune: Attack
    MAGIC_IMMUNITY =            0x0000_0080 # Immune: Magic
    STATUS_IMMUNITY =           0x0000_0040
    DAMAGE_SPIKES =             0x0000_0020 # Return Damage
    SUICIDAL =                  0x0000_0010 # ???
    BATTLE_LORE_8 =             0x0000_0008
    BATTLE_LORE_9 =             0x0000_0004
    BATTLE_LORE_10 =            0x0000_0002
    BATTLE_LORE_11 =            0x0000_0001
    NONE =                      0x0000_0000

set_unit_pattern = r'btlAtelSetUnit\(([0-9]+)\)'
set_ability_pattern = r'btlAtelSetAbility\((-?0x[0-9a-fA-F]+), (-?0x[0-9a-fA-F]+)\)'
entry_pattern = r'function entry[0-9]+\(\)\s*{([^}]*btlAtelSetUnit[^}]*btlAtelSetAbility[^}]*)}'

def find_and_edit_file(root_folder, target_filename, output_folder, first_aug_enum, second_aug_enum):
    log_entries = []
    
    for root, _, files in os.walk(root_folder):
        for file_name in files:
            if file_name == target_filename:
                source_path = os.path.join(root, file_name)

                with open(source_path, 'r', encoding='utf-8') as file:
                    current_file = file.read()

                edited_file, log_entries = edit_file(current_file, source_path, first_aug_enum, second_aug_enum, log_entries)

                relative_path = os.path.relpath(source_path, root_folder)
                output_path = os.path.join(output_folder, relative_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(edited_file)

                print(f"Modified content of {target_filename} written to {output_path}")

    log_json_path = os.path.join(output_folder, "modification_log.json")
    with open(log_json_path, 'w', encoding='utf-8') as log_file:
        json.dump(log_entries, log_file, indent=4)

    print(f"Modification log written to {log_json_path}")

# Matches the 'entry_pattern' to find all 'entryXX' functions 
# and also checks if 'btlAtelSetUnit' and 'btlAtelSetAbility' exists
def edit_file(current_file, source_path, first_aug_enum, second_aug_enum, log_entries):
    edited_file = current_file

    for match in re.finditer(entry_pattern, current_file):
        matched_string = match.group(1)
        if 'btlAtelSetUnit' in matched_string and 'btlAtelSetAbility' in matched_string:
            edited_file, log_entries = edit_augments(edited_file, matched_string, source_path, first_aug_enum, second_aug_enum, log_entries)

    return edited_file, log_entries

# Matches the 'set_ability_pattern' and then captures the first and second argument of 'btlAtelSetAbility'
# It will edit the hex values of both arguments to remove the enums passed
def edit_augments(edited_file, matched_string, source_path, first_aug_enum, second_aug_enum, log_entries):
    for unit_match in re.finditer(set_unit_pattern, matched_string):
        unit_number = int(unit_match.group(1))
        set_ability_match = re.search(set_ability_pattern, matched_string)
        
        if set_ability_match:
            # Hexdecimal representation of augments bitfield
            first_aug_hex = set_ability_match.group(1)
            second_aug_hex = set_ability_match.group(2)
        
            # Decimal representation of augments bitfields, also makes it positive
            first_aug_dec = abs(int(first_aug_hex, 16))
            second_aug_dec = abs(int(second_aug_hex, 16))

            alt_first_aug_dec, alt_second_aug_dec = remove_augments(first_aug_dec, second_aug_dec, first_aug_enum, second_aug_enum)
            alt_first_aug_hex = hex(alt_first_aug_dec).lower()
            alt_second_aug_hex = hex(alt_second_aug_dec).lower()

            original_entry = f"btlAtelSetAbility({first_aug_hex}, {second_aug_hex})"
            edited_entry = f"btlAtelSetAbility({alt_first_aug_hex}, {alt_second_aug_hex})"

            log_entry = {
                "path": source_path,
                "units": [
                    {
                        "btl_atel_set_unit": unit_number,
                        "unpacked": {
                            "btl_atel_set_ability": original_entry,
                            "first_arg_augments":  map_augments(first_aug_dec, FirstAugment),
                            "second_arg_augments": map_augments(second_aug_dec, SecondAugment)
                        },
                        "edited": {
                            "btl_atel_set_ability": edited_entry,
                            "first_arg_augments": map_augments(alt_first_aug_dec, FirstAugment),
                            "second_arg_augments": map_augments(alt_second_aug_dec, SecondAugment)
                        }
                    }
                ]
            }

            # Check if entries are different, we don't want to add stuff that doesn't have any changes
            if first_aug_dec != alt_first_aug_dec or second_aug_dec != alt_second_aug_dec:
                index = next((index for index, entry in enumerate(log_entries) if entry["path"] == source_path), None)
                if index is None:
                    log_entries.append(log_entry)
                else:
                    units = log_entries[index]["units"] + log_entry["units"]
                    log_entries[index]["units"] = units
                edited_file = edited_file.replace(original_entry, edited_entry)
            else:
                print(f'NOTHING TO CHANGE: {source_path} - btlAtelSetUnit({unit_number}) - {original_entry}')

    return edited_file, log_entries

def remove_augments(first_aug, second_aug, first_aug_enum, second_aug_enum):
    if first_aug & first_aug_enum.value and first_aug_enum != FirstAugment.NONE:
        alt_first_aug = first_aug ^ first_aug_enum.value
    else:
        alt_first_aug = first_aug

    if second_aug & second_aug_enum.value and second_aug_enum != SecondAugment.NONE:
        alt_second_aug = second_aug ^ second_aug_enum.value
    else:
        alt_second_aug = second_aug

    return alt_first_aug, alt_second_aug

def map_augments(aug_dec, aug_enum):
    mapped_augments = [aug.name for aug in aug_enum if aug_dec & aug.value == aug.value and aug.value != 0]
    return mapped_augments

if __name__ == "__main__":
    root_folder = "unpacked"  # Replace with the actual root folder path
    target_filename = "section_000.c"   # Replace with the target file's name
    output_folder = "edited"  # Replace with the output folder path
    first_aug_enum = FirstAugment.ACCURACY_BOOST  # Replace with the desired enum value
    second_aug_enum = SecondAugment.ANTI_LIBRA  # Replace with the desired enum value

    find_and_edit_file(root_folder, target_filename, output_folder, first_aug_enum, second_aug_enum)