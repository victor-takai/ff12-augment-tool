import os
import re
import json
import shutil
from augments import FirstAugment, SecondAugment

set_unit_pattern = r'btlAtelSetUnit\(([0-9]+)\)'
set_ability_pattern = r'btlAtelSetAbility\((-?(?:0x[0-9a-fA-F]+|0)), (-?(?:0x[0-9a-fA-F]+|0))\)'
entry_pattern = r'entry[0-9]+\(\)\s*{([^}]*btlAtelSetUnit[^}]*btlAtelSetAbility[^}]*)}'

def find_and_edit_files(input_folder, output_folder, target_filename, first_augs, second_augs, should_add):
    log_objects = []
    
    for folder_path, _, filenames in os.walk(input_folder):
        for file_name in filenames:
            source_path = os.path.join(folder_path, file_name)

            relative_path = os.path.relpath(source_path, input_folder)
            output_path = os.path.join(output_folder, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if file_name == target_filename:
                with open(source_path, 'r', encoding='utf-8') as file:
                    current_file = file.read()

                edited_file, log_objects = edit_file(current_file, source_path, first_augs, second_augs, log_objects, should_add)

                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(edited_file)
            else:
                shutil.copy(source_path, output_path)

        # Check if the folder is empty and copy it
        if not filenames and not os.path.samefile(folder_path, output_folder):
            output_dir = os.path.join(output_folder, os.path.relpath(folder_path, input_folder))
            os.makedirs(output_dir, exist_ok=True)

    log_json_path = os.path.join(output_folder, "log.json")
    with open(log_json_path, 'w', encoding='utf-8') as log_file:
        json.dump(log_objects, log_file, indent=4)

    print(f"Log written to {log_json_path}")

# Matches the "entry_pattern" to find all "entryXX" functions 
# and also checks if "btlAtelSetUnit" and "btlAtelSetAbility" exists
def edit_file(current_file, source_path, first_augs, second_augs, log_objects, should_add):
    edited_file = current_file

    matches = re.findall(entry_pattern, current_file)
    total_entries = len(matches)
    print(f"Entries in file {source_path}: {total_entries}")

    if total_entries == 0:
        log_entry = {
            "path": source_path,
            "total_entries": 0,
            "edited_entries": {
                "total": 0,
                "entries": []
            },
             "unchanged_entries": {
                "total": 0,
                "entries": []
            }
        }
        log_objects.append(log_entry)
    else:
        for match_string in matches:
            if "btlAtelSetUnit" in match_string and "btlAtelSetAbility" in match_string:
                edited_file, log_objects = edit_augments(edited_file, match_string, source_path, first_augs, second_augs, log_objects, total_entries, should_add)
            else:
                print(f"Could not find entry in file: {source_path}")

    return edited_file, log_objects

# Matches the "set_ability_pattern" and then captures the first and second argument of "btlAtelSetAbility"
# It will edit the hex values of both arguments to remove the enums passed
def edit_augments(edited_file, matched_string, source_path, first_augs, second_augs, log_objects, total_entries, should_add):
    for unit_match in re.finditer(set_unit_pattern, matched_string):
        unit_number = f"{int(unit_match.group(1))}"
        set_ability_match = re.search(set_ability_pattern, matched_string)
        
        if set_ability_match:
            # Hexdecimal representation of augments bitfield
            original_augs_hex = set_ability_match.group(1)
            original_augs_hex = set_ability_match.group(2)
        
            # Decimal representation of augments bitfields, also makes it positive
            original_first_augs = abs(int(original_augs_hex, 16))
            original_second_augs = abs(int(original_augs_hex, 16))

            edited_first_augs, edited_second_augs = modify_orig_augs(original_first_augs, original_second_augs, first_augs, second_augs, should_add)

            if edited_first_augs == 0:
                edited_first_augs_hex = "0"
            else:
                edited_first_augs_hex = "0x" + hex(edited_first_augs)[2:].zfill(8).lower()

            if edited_second_augs == 0:
                edited_second_augs_hex = "0"
            else:
                edited_second_augs_hex = "0x" + hex(edited_second_augs)[2:].zfill(8).lower()

            new_object = {
                "path": source_path,
                "total_entries": total_entries,
                "edited_entries": {
                    "total": 0,
                    "entries": []
                },
                "unchanged_entries": {
                    "total": 0,
                    "entries": []
                }
            }

            # Check if entries are different, we don't want to add stuff that doesn't have any changes
            index = next((index for index, entry in enumerate(log_objects) if entry["path"] == source_path), None)
            if original_first_augs != edited_first_augs or original_second_augs != edited_second_augs:
                edited_entry = {
                    "unit": unit_number,
                    "unpacked": {
                        "btl_atel_set_ability": f"{original_augs_hex}, {original_augs_hex}",
                        "first_arg_augments":  map_augments(original_first_augs, FirstAugment),
                        "second_arg_augments": map_augments(original_second_augs, SecondAugment)
                    },
                    "edited": {
                        "btl_atel_set_ability": f"{edited_first_augs_hex}, {edited_second_augs_hex}",
                        "first_arg_augments": map_augments(edited_first_augs, FirstAugment),
                        "second_arg_augments": map_augments(edited_second_augs, SecondAugment)
                    }
                }

                if index is None:
                    new_object["edited_entries"]["total"] += 1
                    new_object["edited_entries"]["entries"].append(edited_entry)
                    log_objects.append(new_object)
                else:
                    log_objects[index]["edited_entries"]["total"] += 1
                    log_objects[index]["edited_entries"]["entries"].append(edited_entry)

                unpacked_set_ability = f"btlAtelSetAbility({original_augs_hex}, {original_augs_hex})"
                edited_set_ability = f"btlAtelSetAbility({edited_first_augs_hex}, {edited_second_augs_hex})"
                edited_file = edited_file.replace(unpacked_set_ability, edited_set_ability)
            else:
                unchanged_entry = {
                        "unit": unit_number,
                        "unpacked": {
                            "btl_atel_set_ability": f"{original_augs_hex}, {original_augs_hex}",
                            "first_arg_augments":  map_augments(original_first_augs, FirstAugment),
                            "second_arg_augments": map_augments(original_second_augs, SecondAugment)
                        }
                }
                if index is None:
                    new_object["unchanged_entries"]["total"] += 1
                    new_object["unchanged_entries"]["entries"].append(unchanged_entry)
                    log_objects.append(new_object)
                else:
                    log_objects[index]["unchanged_entries"]["total"] += 1
                    log_objects[index]["unchanged_entries"]["entries"].append(unchanged_entry)

        else:
            print("Did not find match for btlAtelSetAbility")

    return edited_file, log_objects

def modify_orig_augs(original_first_augs, original_second_augs, first_augs, second_augs, should_add):
    edited_first_augs = original_first_augs
    edited_second_augs = original_second_augs

    for aug_enum in first_augs:
        edited_first_augs = modify_bitfield(edited_first_augs, aug_enum.value, should_add)

    for aug_enum in second_augs:
        edited_second_augs = modify_bitfield(edited_second_augs, aug_enum.value, should_add)
   
    return edited_first_augs, edited_second_augs
    
def modify_bitfield(original_bitfield, modifying_bitfield, should_add):
    edited_bitfield = original_bitfield

    if should_add:
        # Check if modifying bitfield is not present
        if not (original_bitfield & modifying_bitfield):
            edited_bitfield = original_bitfield | modifying_bitfield
    else:
        # Check if modifying bitfield is present
        if (original_bitfield & modifying_bitfield) != 0:
            edited_bitfield = original_bitfield ^ modifying_bitfield

    return edited_bitfield

def map_augments(augs, aug_enum):
    mapped_augments = [aug.name for aug in aug_enum if augs & aug.value == aug.value]
    return mapped_augments

if __name__ == "__main__":
    input_folder = "unpacked"  # Replace with the actual root folder path
    output_folder = "edited"  # Replace with the output folder path
    target_filename = "section_000.c"   # Replace with the target file's name
    first_augs = []  # Replace with the desired enum values
    second_augs = [SecondAugment.ANTI_LIBRA]  # Replace with the desired enum values
    should_add = False

    find_and_edit_files(input_folder, output_folder, target_filename, first_augs, second_augs, should_add)
