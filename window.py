import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QGridLayout, QCheckBox, QPushButton, QFrame, QMessageBox
from augments import FirstAugment, SecondAugment
from main import find_and_edit_files

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FFXII Augment Tool")
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
        
        self.layout.addWidget(self.grid_frame)
        
        self.edit_button = QPushButton("Edit Augments")
        self.layout.addWidget(self.edit_button)
        
        self.edit_button.clicked.connect(self.edit_button_clicked)
        
        self.grid_frame.setStyleSheet("background-color: rgb(211, 211, 211);")

    def select_all_clicked(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all_clicked(self):
            for checkbox in self.checkboxes:
                checkbox.setChecked(False)

    def edit_button_clicked(self):
        selected_augs = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        first_augs = []
        second_augs = []

        for aug_name in selected_augs:
            first_aug = next((enum for enum in FirstAugment if enum.name == aug_name), None)
            if first_aug != None:
                first_augs.append(first_aug)

            second_aug = next((enum for enum in SecondAugment if enum.name == aug_name), None)
            if second_aug != None:
                second_augs.append(second_aug)

        root_folder = "unpacked"  # Replace with the actual root folder path
        target_filename = "section_000.c"   # Replace with the target file's name
        output_folder = "edited"  # Replace with the output folder path
        find_and_edit_files(root_folder, target_filename, output_folder, first_augs, second_augs, self.add_radio.isChecked())

        if selected_augs:
            mode = "added" if self.add_radio.isChecked() else "removed"
            message = f"Augments {mode}!"
            QMessageBox.information(self, "Info", message)
        else:
            QMessageBox.warning(self, "Info", "No items selected.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
