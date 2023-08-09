import os
import re
import json
from augments import FirstAugment, SecondAugment

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

    log_json_path = os.path.join(output_folder, "log.json")
    with open(log_json_path, 'w', encoding='utf-8') as log_file:
        json.dump(log_entries, log_file, indent=4)

    print(f"Log written to {log_json_path}")

# Matches the 'entry_pattern' to find all 'entryXX' functions 
# and also checks if 'btlAtelSetUnit' and 'btlAtelSetAbility' exists
def edit_file(current_file, source_path, first_aug_enum, second_aug_enum, log_entries):
    edited_file = current_file

    for match in re.finditer(entry_pattern, current_file):
        matched_string = match.group(1)
        if 'btlAtelSetUnit' in matched_string and 'btlAtelSetAbility' in matched_string:
            edited_file, log_entries = edit_augments(edited_file, matched_string, source_path, first_aug_enum, second_aug_enum, log_entries)
        else:
            print(f'Could not find entry in file: {source_path}')

    return edited_file, log_entries

# Matches the 'set_ability_pattern' and then captures the first and second argument of 'btlAtelSetAbility'
# It will edit the hex values of both arguments to remove the enums passed
def edit_augments(edited_file, matched_string, source_path, first_aug_enum, second_aug_enum, log_entries):
    for unit_match in re.finditer(set_unit_pattern, matched_string):
        unit_number = int(unit_match.group(1))
        set_ability_match = re.search(set_ability_pattern, matched_string)
        
        if set_ability_match:
            # Hexdecimal representation of augments bitfield
            first_augs_hex = set_ability_match.group(1)
            second_augs_hex = set_ability_match.group(2)
        
            # Decimal representation of augments bitfields, also makes it positive
            first_augs_dec = abs(int(first_augs_hex, 16))
            second_augs_dec = abs(int(second_augs_hex, 16))

            alt_first_augs_dec, alt_second_augs_dec = remove_augments(first_augs_dec, second_augs_dec, first_aug_enum, second_aug_enum)
            alt_first_augs_hex = hex(alt_first_augs_dec).lower()
            alt_second_augs_hex = hex(alt_second_augs_dec).lower()

            unpacked_entry = f"btlAtelSetAbility({first_augs_hex}, {second_augs_hex})"
            edited_entry = f"btlAtelSetAbility({alt_first_augs_hex}, {alt_second_augs_hex})"

            log_entry = {
                "path": source_path,
                "units": [
                    {
                        "btl_atel_set_unit": unit_number,
                        "unpacked": {
                            "btl_atel_set_ability": unpacked_entry,
                            "first_arg_augments":  map_augments(first_augs_dec, FirstAugment),
                            "second_arg_augments": map_augments(second_augs_dec, SecondAugment)
                        },
                        "edited": {
                            "btl_atel_set_ability": edited_entry,
                            "first_arg_augments": map_augments(alt_first_augs_dec, FirstAugment),
                            "second_arg_augments": map_augments(alt_second_augs_dec, SecondAugment)
                        }
                    }
                ]
            }

            # Check if entries are different, we don't want to add stuff that doesn't have any changes
            if first_augs_dec != alt_first_augs_dec or second_augs_dec != alt_second_augs_dec:
                index = next((index for index, entry in enumerate(log_entries) if entry["path"] == source_path), None)
                if index is None:
                    log_entries.append(log_entry)
                else:
                    units = log_entries[index]["units"] + log_entry["units"]
                    log_entries[index]["units"] = units
                edited_file = edited_file.replace(unpacked_entry, edited_entry)
            else:
                print(f'Nothing to change: {source_path} - btlAtelSetUnit({unit_number}) - {unpacked_entry}')

    return edited_file, log_entries

def remove_augments(first_augs, second_augs, first_aug_enum, second_aug_enum):
    if first_augs & first_aug_enum.value and first_aug_enum != FirstAugment.NONE:
        alt_first_aug = first_augs ^ first_aug_enum.value
    else:
        alt_first_aug = first_augs

    if second_augs & second_aug_enum.value and second_aug_enum != SecondAugment.NONE:
        alt_second_aug = second_augs ^ second_aug_enum.value
    else:
        alt_second_aug = second_augs

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