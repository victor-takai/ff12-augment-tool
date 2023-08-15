import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QGridLayout, QCheckBox, QPushButton, QFrame, QMessageBox, QLabel
from augments import FirstAugment, SecondAugment
from main import find_and_edit_files
from version import __version__

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"FFXII Augment Tool v{__version__}")
        self.setGeometry(100, 100, 400, 400)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        
        self.radio_layout = QHBoxLayout()
        
        self.add_radio = QRadioButton("Add")
        self.remove_radio = QRadioButton("Remove")
        self.add_radio.setChecked(True)
        
        self.radio_layout.addWidget(self.add_radio)
        self.radio_layout.addWidget(self.remove_radio)

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_clicked)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all_clicked)
        
        self.radio_layout.addWidget(self.select_all_button)
        self.radio_layout.addWidget(self.deselect_all_button)

        self.layout.addLayout(self.radio_layout)
        
        self.grid_frame = QFrame()
        self.grid_layout = QGridLayout(self.grid_frame)
        
        self.items = list(FirstAugment) + list(SecondAugment)
        
        col_count = 4
        self.checkboxes = []
        
        for index, item in enumerate(self.items):
            row = index // col_count
            col = index % col_count
            
            checkbox = QCheckBox(item.name)
            self.grid_layout.addWidget(checkbox, row, col)
            self.checkboxes.append(checkbox)

        for checkbox in self.checkboxes:
            self.add_checkbox_tooltip(checkbox)
        
        self.layout.addWidget(self.grid_frame)
        
        self.edit_button = QPushButton("Edit Augments")
        self.layout.addWidget(self.edit_button)
        
        self.edit_button.clicked.connect(self.edit_button_clicked)
        
        self.grid_frame.setStyleSheet("background-color: rgb(211, 211, 211);")

        self.name_label = QLabel("Made by Kalivos")
        self.name_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.name_label)

    def select_all_clicked(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all_clicked(self):
            for checkbox in self.checkboxes:
                checkbox.setChecked(False)

    def edit_button_clicked(self):
        selected_augs = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        should_add = self.add_radio.isChecked()
        
        self.edit_augments(selected_augs, should_add)

        if selected_augs:
            mode = "added" if should_add else "removed"
            message = f"Augments {mode}!"
            QMessageBox.information(self, "Info", message)
        else:
            QMessageBox.warning(self, "Info", "No items selected.")

    def add_checkbox_tooltip(self, checkbox):
        tooltip_text = self.get_tooltip_text(checkbox.text())  # Customize tooltip text based on checkbox text
        checkbox.setToolTip(tooltip_text)

    def get_tooltip_text(self, checkbox_text):

        first_augment_tooltips = {
            "STABILITY": "Prevents Knockback.",
            "SAFETY": "Prevents Instant Death, Warp and the like.",
            "ACCURACY_BOOST": "Improves chance to hit. (Ignore/Null Evade)",
            "SHIELD_BOOST": "Improves chance to block with a shield",
            "EVASION_BOOST": "Improvse chance of avoiding attacks.",
            "LAST_STAND": "Increases defense when HP Critical.",
            "COUNTER": "When attacked, automatically counter with weapon in hand. (Enables Counter)",
            "COUNTER_BOOST": "Improves chance to counter. (Gengi Gloves Effect)",
            "SPELLBREAKER": "Increases magick power when HP Critical.",
            "BRAWLER": "Increases attack power when fighting empty-handed.",
            "ADRENALINE": "Increases strength when HP Critical.",
            "FOCUS": "Increases strength when HP is full.",
            "LOBBYING": "Convert all license points earned to gil. (Cat Ear Hood Effect)",
            "COMBO_BOOST": "Improves chance of scoring multiple hits.",
            "ITEM_BOOST": "Improves potency of restorative items and fangs. (Pheasant Netsuke Effect)",
            "MEDICINE_REVERSE": "Reverses effects of restorative items such as potions. (Nihopalaoa Effect)",
            "WEATHERPROOF": "Nullifies weather and terrain effects. (Agate Ring Effect)",
            "THIEVERY": "Enables the theft of superior and rare items. (Thief Cuffs Effect)",
            "SABOTEUR": "Improves chance to strike with magicks. (Ignore/Null Vit | Indigo Pendant Effect)",
            "MAGICK_LORE_1": "Increases magick potency.",
            "WARMAGE": "Gain MP after dealing magick damage.",
            "MARTYR": "Gain MP after taking damage.",
            "MAGICK_LORE_2": "Increases magick potency.",
            "HEADSMAN": "Gain MP after defeating a foe.",
            "MAGICK_LORE_3": "Increases magick potency.",
            "TREASURE_HUNTER": "Search the deepest recesses of chests, coffers, and the like. (Diamond Armlet Effect)",
            "MAGICK_LORE_4": "Increases magick potency.",
            "DOUBLE_EXP": "Doubles EXP earned. (Embroidered Tipped Effect)",
            "DOUBLE_LP": "Doubles license points earned. (Golden Amulet Effect)",
            "NO_EXP": "Reduces EXP earned to 0. (Firefly Effect)",
            "SPELLBOUND": "Increases duration of status effects.",
            "PIERCING_MAGICK": "Magicks will not bounce off targets with Reflect status. (Opal Ring Effect)"
        }
        
        second_augment_tooltips = {
            "OFFERING": "Enables casting of magicks with gil, rather than MP. (Turtleshell Choker Effect)",
            "MUFFLE": "Avoid detection based on sound and magick.",
            "LIFE_CLOAK": "Avoid detection based on low HP.",
            "BATTLE_LORE_1": "Increases physical attack damage.",
            "PARSIMONY": "Reduces MP costs by half.",
            "TREAD_LIGHTLY": "Move safely past traps. (Steel Polyens Effect)",
            "UNUSED": "",
            "EMPTINESS": "Reduces max MP to 0.",
            "RESIST_PIERCE_DAMAGE": "Ignores the piercing effects of Guns and the like.",
            "ANTI_LIBRA": "Hides user's vital information from the effect of Libra.",
            "BATTLE_LORE_2": "Increases physical attack damage.",
            "BATTLE_LORE_3": "Increases physical attack damage.",
            "BATTLE_LORE_4": "Increases physical attack damage.",
            "BATTLE_LORE_5": "Increases physical attack damage.",
            "BATTLE_LORE_6": "Increases physical attack damage.",
            "BATTLE_LORE_7": "Increases physical attack damage.",
            "STONESKIN": "Reduces damage taken by 30%.",
            "ATTACK_BOOST": "Increases Attack damage by 20%.",
            "DOUBLE_EDGED": "Increases Attack damage by 50% and user receives damage equal to each Attack.",
            "SPELLSPRING": "Reduces MP costs to 0.",
            "ELEMENTAL_SHIFT": "User gains one elemental weakness and absorbs all others.",
            "CELERITY": "Reduces Attack charge time to 0.",
            "SWIFT_CAST": "Reduces Magick charge time to 0.",
            "ATTACK_IMMUNITY": "User becomes immune to attacks.",
            "MAGIC_IMMUNITY": "User becomes immune to magicks.",
            "STATUS_IMMUNITY": "User becomes immune to statuses.",
            "DAMAGE_SPIKES": "Returns 5% of all damage received to user's attackers.",
            "SUICIDAL": "Compels nearby allies to use Self-Destruct.",
            "BATTLE_LORE_8": "Increases physical attack damage.",
            "BATTLE_LORE_9": "Increases physical attack damage.",
            "BATTLE_LORE_10": "Increases physical attack damage.",
            "BATTLE_LORE_11": "Increases physical attack damage."
        }
     
        if checkbox_text in first_augment_tooltips:
            return first_augment_tooltips[checkbox_text]
        elif checkbox_text in second_augment_tooltips:
            return second_augment_tooltips[checkbox_text]
        else:
            return "No tooltip available."

    def edit_augments(self, selected_augs, should_add):
        first_augs = []
        second_augs = []

        for aug_name in selected_augs:
            first_aug = next((enum for enum in FirstAugment if enum.name == aug_name), None)
            if first_aug != None:
                first_augs.append(first_aug)

            second_aug = next((enum for enum in SecondAugment if enum.name == aug_name), None)
            if second_aug != None:
                second_augs.append(second_aug)

        input_folder = "unpacked"
        output_folder = "edited"
        target_filename = "section_000.c"
        find_and_edit_files(input_folder, output_folder, target_filename, first_augs, second_augs, should_add)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
