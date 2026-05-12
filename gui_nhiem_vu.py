from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QMessageBox, QScrollArea, QSpinBox, QCheckBox,QInputDialog
)
import sys
import csv

class SubStep(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()

        self.xpath_input = QLineEdit()
        self.xpath_input.setPlaceholderText("XPath...")

        self.type_select = QComboBox()
        self.type_select.addItems(["click", "comment", "wait", "captcha"])
        self.type_select.currentTextChanged.connect(self.update_value_input)

        self.value_input = QWidget()
        self.value_layout = QHBoxLayout()
        self.value_input.setLayout(self.value_layout)

        self.remove_btn = QPushButton("❌")
        self.remove_btn.setFixedWidth(30)

        self.layout.addWidget(QLabel("XPath:"))
        self.layout.addWidget(self.xpath_input)
        self.layout.addWidget(QLabel("Loại thao tác:"))
        self.layout.addWidget(self.type_select)
        self.layout.addWidget(self.value_input)
        self.layout.addWidget(self.remove_btn)

        self.setLayout(self.layout)
        self.update_value_input("click")

    def update_value_input(self, value_type):
        # Clear layout
        while self.value_layout.count():
            item = self.value_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        if value_type in ["click", "captcha"]:
            self.checkbox = QComboBox()
            self.checkbox.addItems(["Yes", "No"])
            self.value_layout.addWidget(QLabel("Giá trị:"))
            self.value_layout.addWidget(self.checkbox)
        elif value_type == "comment":
            self.textbox = QLineEdit()
            self.textbox.setPlaceholderText("Nội dung comment")
            self.value_layout.addWidget(QLabel("Nội dung:"))
            self.value_layout.addWidget(self.textbox)
        elif value_type == "wait":
            self.spinbox = QSpinBox()
            self.spinbox.setRange(1, 300)
            self.value_layout.addWidget(QLabel("Chờ (giây):"))
            self.value_layout.addWidget(self.spinbox)

    def get_step(self):
        step_type = self.type_select.currentText()
        xpath = self.xpath_input.text()
        if step_type in ["click", "captcha"]:
            value = self.checkbox.currentText()
        elif step_type == "comment":
            value = self.textbox.text()
        elif step_type == "wait":
            value = self.spinbox.value()
        return {
            "type": step_type,
            "xpath": xpath,
            "value": value
        }


class TaskBlock(QWidget):
    def __init__(self, task_number):
        super().__init__()
        self.layout = QVBoxLayout()
        self.substeps = []

        self.title = QLabel(f"🧩 Nhiệm vụ #{task_number}")
        self.layout.addWidget(self.title)

        # Add input for link
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("Nhập link (ví dụ: https://discord.com/invite/haven1)")
        self.layout.addWidget(self.link_input)

        self.substep_container = QVBoxLayout()
        self.layout.addLayout(self.substep_container)

        self.add_btn = QPushButton("➕ Thêm thao tác con")
        self.add_btn.clicked.connect(self.add_substep)
        self.layout.addWidget(self.add_btn)

        self.remove_task_btn = QPushButton("❌ Xóa nhiệm vụ này")
        self.layout.addWidget(self.remove_task_btn)

        self.setLayout(self.layout)
        self.add_substep()

    def add_substep(self):
        sub = SubStep()
        sub.remove_btn.clicked.connect(lambda: self.remove_substep(sub))
        self.substeps.append(sub)
        self.substep_container.addWidget(sub)

    def remove_substep(self, sub):
        self.substep_container.removeWidget(sub)
        sub.setParent(None)
        self.substeps.remove(sub)

    def get_steps(self):
        return {
            "link": self.link_input.text(),
            "steps": [s.get_step() for s in self.substeps]
        }


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool Discord Nhiệm vụ")
        self.setGeometry(100, 100, 1000, 600)

        self.task_counter = 1
        self.tasks = []
        self.total_tasks = 0  # Số nhiệm vụ cần làm
        self.completion_xpath = ""  # XPath để kiểm tra hoàn thành

        self.layout = QVBoxLayout()

        # Input for comment text
        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Nhập nội dung comment vào server")
        self.layout.addWidget(self.comment_input)

        # Input for number of tasks
        self.task_count_input = QSpinBox()
        self.task_count_input.setRange(1, 100)  # Giới hạn số nhiệm vụ từ 1 đến 100
        self.task_count_input.setPrefix("Số nhiệm vụ cần làm: ")
        self.layout.addWidget(self.task_count_input)

        # Button to confirm task count
        self.confirm_task_btn = QPushButton("Xác nhận số nhiệm vụ")
        self.confirm_task_btn.clicked.connect(self.confirm_task_count)
        self.layout.addWidget(self.confirm_task_btn)

        # Scroll area for tasks
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll.setWidget(self.scroll_content)

        self.layout.addWidget(self.scroll)

        # Add task button (disabled initially)
        self.add_task_btn = QPushButton("➕ Thêm nhiệm vụ mới")
        self.add_task_btn.setEnabled(False)  # Chỉ bật khi xác nhận số nhiệm vụ
        self.add_task_btn.clicked.connect(self.add_task)
        self.layout.addWidget(self.add_task_btn)

        # Run all tasks button
        self.run_btn = QPushButton("🚀 Run tất cả nhiệm vụ")
     
        self.run_btn.clicked.connect(self.request_completion_xpath)
        self.layout.addWidget(self.run_btn)

        self.setLayout(self.layout)

    def confirm_task_count(self):
        # Lấy nội dung comment và số nhiệm vụ
        comment_text = self.comment_input.text()
        self.total_tasks = self.task_count_input.value()

        if not comment_text.strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập nội dung comment!")
            return

        QMessageBox.information(self, "Thành công", f"Đã xác nhận {self.total_tasks} nhiệm vụ cần làm.")
        self.add_task_btn.setEnabled(True)  # Cho phép thêm nhiệm vụ

    def add_task(self):
        if len(self.tasks) >= self.total_tasks:
            QMessageBox.warning(self, "Lỗi", "Bạn đã thêm đủ số nhiệm vụ!")
            return

        task = TaskBlock(self.task_counter)
        self.task_counter += 1
        self.tasks.append(task)
        self.scroll_layout.addWidget(task)
        task.remove_task_btn.clicked.connect(lambda: self.remove_task(task))

        # Bật nút "Run tất cả nhiệm vụ" khi đủ số nhiệm vụ
        if len(self.tasks) == self.total_tasks:
            self.run_btn.setEnabled(True)

    def remove_task(self, task):
        self.scroll_layout.removeWidget(task)
        task.setParent(None)
        self.tasks.remove(task)

        # Tắt nút "Run tất cả nhiệm vụ" nếu số nhiệm vụ không đủ
        if len(self.tasks) < self.total_tasks:
            self.run_btn.setEnabled(False)

    def request_completion_xpath(self):
        # Hiển thị hộp thoại để người dùng nhập XPath hoàn thành
        xpath, ok = QInputDialog.getText(self, "Nhập XPath hoàn thành", "Vui lòng nhập XPath để kiểm tra hoàn thành:")
        if ok and xpath.strip():
            self.completion_xpath = xpath.strip()
            self.run_all()
        else:
            QMessageBox.warning(self, "Lỗi", "Bạn chưa nhập XPath hoàn thành!")

    import csv

    def run_all(self):
        comment_text = self.comment_input.text()
        print(f"Nội dung comment: {comment_text}")
        print(f"XPath hoàn thành: {self.completion_xpath}")

        # Tên file CSV và TXT
        base_filename = "tasks_output"
        csv_file = f"{base_filename}.csv"
        txt_file = f"{base_filename}.txt"

        # Ghi dữ liệu nhiệm vụ vào file CSV
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Ghi tiêu đề cột
            writer.writerow(["Nhiệm vụ", "Link", "Loại thao tác", "XPath", "Giá trị"])

            # Ghi dữ liệu từng nhiệm vụ
            for i, task in enumerate(self.tasks):
                task_data = task.get_steps()
                link = task_data["link"]
                steps = task_data["steps"]

                for j, step in enumerate(steps):
                    writer.writerow([
                        f"Nhiệm vụ #{i + 1}",
                        link,
                        step["type"],
                        step["xpath"],
                        step["value"]
                    ])

        # Ghi dữ liệu comment text và XPath hoàn thành vào file TXT
        with open(txt_file, mode="w", encoding="utf-8") as file:
            file.write(f"{comment_text}\n")
            file.write(f"{self.completion_xpath}\n")

        QMessageBox.information(self, "Thành công", f"Đã lưu nhiệm vụ vào file {csv_file} và thông tin chung vào file {txt_file}!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())