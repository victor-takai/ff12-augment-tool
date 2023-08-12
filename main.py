import os
import re
import json
import shutil
from augments import FirstAugment, SecondAugment

set_unit_pattern = r'btlAtelSetUnit\(([0-9]+)\)'
set_ability_pattern = r'btlAtelSetAbility\((-?0x[0-9a-fA-F]+), (-?0x[0-9a-fA-F]+)\)'
entry_pattern = r'entry[0-9]+\(\)\s*{([^}]*btlAtelSetUnit[^}]*btlAtelSetAbility[^}]*)}'

def find_and_edit_files(input_folder, output_folder, target_filename, new_first_augs, new_second_augs, should_add):
    log_entries = []
    
    for folder_path, _, filenames in os.walk(input_folder):
        for file_name in filenames:
            source_path = os.path.join(folder_path, file_name)

            relative_path = os.path.relpath(source_path, input_folder)
            output_path = os.path.join(output_folder, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if file_name == target_filename:
                with open(source_path, 'r', encoding='utf-8') as file:
                    current_file = file.read()

                edited_file, log_entries = edit_file(current_file, source_path, new_first_augs, new_second_augs, log_entries, should_add)

                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(edited_file)
            else:
                shutil.copy(source_path, output_path)

        # Check if the folder is empty and copy it
        if not filenames and not os.path.samefile(folder_path, output_folder):
            output_dir = os.path.join(output_folder, os.path.relpath(folder_path, input_folder))
            print("output dir", output_dir)
            os.makedirs(output_dir, exist_ok=True)

    log_json_path = os.path.join(output_folder, "log.json")
    with open(log_json_path, 'w', encoding='utf-8') as log_file:
        json.dump(log_entries, log_file, indent=4)

    print(f"Log written to {log_json_path}")

# Matches the 'entry_pattern' to find all 'entryXX' functions 
# and also checks if 'btlAtelSetUnit' and 'btlAtelSetAbility' exists
def edit_file(current_file, source_path, first_augs, second_augs, log_entries, should_add):
    edited_file = current_file

    for match in re.finditer(entry_pattern, current_file):
        matched_string = match.group(1)
        if 'btlAtelSetUnit' in matched_string and 'btlAtelSetAbility' in matched_string:
            edited_file, log_entries = edit_augments(edited_file, matched_string, source_path, first_augs, second_augs, log_entries, should_add)
        else:
            print(f'Could not find entry in file: {source_path}')

    return edited_file, log_entries

# Matches the 'set_ability_pattern' and then captures the first and second argument of 'btlAtelSetAbility'
# It will edit the hex values of both arguments to remove the enums passed
def edit_augments(edited_file, matched_string, source_path, new_first_augs, new_second_augs, log_entries, should_add):
    for unit_match in re.finditer(set_unit_pattern, matched_string):
        unit_number = f"{int(unit_match.group(1))}"
        set_ability_match = re.search(set_ability_pattern, matched_string)
        
        if set_ability_match:
            # Hexdecimal representation of augments bitfield
            first_augs_hex = set_ability_match.group(1)
            second_augs_hex = set_ability_match.group(2)
        
            # Decimal representation of augments bitfields, also makes it positive
            orig_first_augs = abs(int(first_augs_hex, 16))
            orig_second_augs = abs(int(second_augs_hex, 16))

            alt_first_augs, alt_second_augs = modify_orig_augs(orig_first_augs, orig_second_augs, new_first_augs, new_second_augs, should_add)

            if alt_first_augs == 0:
                alt_first_augs_hex = "0"
            else:
                alt_first_augs_hex = hex(alt_first_augs).lower()

            if alt_second_augs == 0:
                alt_second_augs_hex = "0"
            else:
                alt_second_augs_hex = hex(alt_second_augs).lower()

            unpacked_entry = f"btlAtelSetAbility({first_augs_hex}, {second_augs_hex})"
            edited_entry = f"btlAtelSetAbility({alt_first_augs_hex}, {alt_second_augs_hex})"

            log_entry = {
                "path": source_path,
                "entries": [
                    {
                        "unit": unit_number,
                        "unpacked": {
                            "btl_atel_set_ability": f"{first_augs_hex}, {second_augs_hex}",
                            "first_arg_augments":  map_augments(orig_first_augs, FirstAugment),
                            "second_arg_augments": map_augments(orig_second_augs, SecondAugment)
                        },
                        "edited": {
                            "btl_atel_set_ability": f"{alt_first_augs_hex}, {alt_second_augs_hex}",
                            "first_arg_augments": map_augments(alt_first_augs, FirstAugment),
                            "second_arg_augments": map_augments(alt_second_augs, SecondAugment)
                        }
                    }
                ]
            }

            # Check if entries are different, we don't want to add stuff that doesn't have any changes
            if orig_first_augs != alt_first_augs or orig_second_augs != alt_second_augs:
                index = next((index for index, entry in enumerate(log_entries) if entry["path"] == source_path), None)
                if index is None:
                    log_entries.append(log_entry)
                else:
                    entries = log_entries[index]["entries"] + log_entry["entries"]
                    log_entries[index]["entries"] = entries
                edited_file = edited_file.replace(unpacked_entry, edited_entry)
            else:
                print(f'Nothing to change on: {source_path} - btlAtelSetUnit({unit_number}) - btlAtelSetAbility({unpacked_entry})')

    return edited_file, log_entries

def modify_orig_augs(orig_first_augs, orig_second_augs, new_first_augs, new_second_augs, should_add):
    alt_first_augs = orig_first_augs
    for aug_enum in new_first_augs:
        modify_bitfield(alt_first_augs, aug_enum.value, should_add)

    alt_second_augs = orig_second_augs
    for aug_enum in new_second_augs:
        modify_bitfield(alt_second_augs, aug_enum.value, should_add)
   
    return alt_first_augs, alt_second_augs
    
def modify_bitfield(original_bitfield, modifying_bitfield, should_add):
    if should_add:
        # Check if modifying bitfield is not present
        if not (original_bitfield & modifying_bitfield):
            original_bitfield = original_bitfield | modifying_bitfield
    else:
        # Check if modifying bitfield is present
        if (original_bitfield & modifying_bitfield) != 0:
            original_bitfield = original_bitfield & -modifying_bitfield

def map_augments(augs, aug_enum):
    mapped_augments = [aug.name for aug in aug_enum if augs & aug.value == aug.value]
    return mapped_augments

if __name__ == "__main__":
    input_folder = "unpacked"  # Replace with the actual root folder path
    output_folder = "edited"  # Replace with the output folder path
    target_filename = "section_000.c"   # Replace with the target file's name
    new_first_augs = []  # Replace with the desired enum values
    new_second_augs = [SecondAugment.ANTI_LIBRA, SecondAugment.ATTACK_IMMUNITY]  # Replace with the desired enum values
    should_add = True

    find_and_edit_files(input_folder, output_folder, target_filename, new_first_augs, new_second_augs, should_add)
