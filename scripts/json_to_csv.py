"""
JSON to CSV 转换脚本
将JSON文件转换为CSV格式，方便导入数据库
支持命令行和图形化界面两种模式
"""

import json
import csv
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


def flatten_value(value):
    """
    将复杂类型（列表、字典）转换为字符串
    """
    if value is None:
        return ""
    elif isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    else:
        return value


def json_to_csv(json_path, csv_path=None, encoding='utf-8', callback=None):
    """
    将单个JSON文件转换为CSV文件

    参数:
        json_path: JSON文件路径
        csv_path: CSV输出路径（可选，默认与JSON同名）
        encoding: 文件编码
        callback: 回调函数，用于更新GUI进度
    """
    json_path = Path(json_path)

    if csv_path is None:
        csv_path = json_path.with_suffix('.csv')
    else:
        csv_path = Path(csv_path)

    # 读取JSON文件
    with open(json_path, 'r', encoding=encoding) as f:
        data = json.load(f)

    # 确保数据是列表格式
    if isinstance(data, dict):
        # 如果是字典，尝试找到主数据数组
        if len(data) == 1:
            data = list(data.values())[0]
        else:
            # 将单个字典转换为列表
            data = [data]

    if not data:
        msg = f"警告: {json_path} 是空的，跳过"
        if callback:
            callback(msg, "warning")
        else:
            print(msg)
        return False, 0

    # 收集所有可能的列名（处理不同对象可能有不同字段的情况）
    all_keys = set()
    for item in data:
        if isinstance(item, dict):
            all_keys.update(item.keys())

    # 按照第一个对象的键顺序排列，然后添加其他键
    if data and isinstance(data[0], dict):
        fieldnames = list(data[0].keys())
        for key in all_keys:
            if key not in fieldnames:
                fieldnames.append(key)
    else:
        fieldnames = sorted(list(all_keys))

    # 写入CSV文件
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for item in data:
            if isinstance(item, dict):
                # 处理每个值，将复杂类型转换为字符串
                row = {k: flatten_value(v) for k, v in item.items()}
                writer.writerow(row)

    msg = f"✓ 转换成功: {json_path.name} -> {csv_path.name} ({len(data)} 条记录)"
    if callback:
        callback(msg, "success")
    else:
        print(msg)
    return True, len(data)


def batch_convert(input_dir, output_dir=None, encoding='utf-8', callback=None, progress_callback=None):
    """
    批量转换目录中的所有JSON文件

    参数:
        input_dir: 输入目录
        output_dir: 输出目录（可选，默认为输入目录下的csv子目录）
        encoding: 文件编码
        callback: 日志回调函数
        progress_callback: 进度回调函数 (current, total)
    """
    input_dir = Path(input_dir)

    if output_dir is None:
        output_dir = input_dir / 'csv_output'
    else:
        output_dir = Path(output_dir)

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 查找所有JSON文件
    json_files = list(input_dir.glob('*.json'))

    if not json_files:
        msg = f"在 {input_dir} 中没有找到JSON文件"
        if callback:
            callback(msg, "warning")
        else:
            print(msg)
        return 0, 0, str(output_dir)

    msg = f"找到 {len(json_files)} 个JSON文件，开始转换..."
    if callback:
        callback(msg, "info")
    else:
        print(msg + "\n")

    success_count = 0
    fail_count = 0
    total = len(json_files)

    for i, json_file in enumerate(json_files):
        csv_file = output_dir / json_file.with_suffix('.csv').name
        try:
            success, _ = json_to_csv(json_file, csv_file, encoding, callback)
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            msg = f"✗ 转换失败: {json_file.name} - {e}"
            if callback:
                callback(msg, "error")
            else:
                print(msg)
            fail_count += 1

        if progress_callback:
            progress_callback(i + 1, total)

    return success_count, fail_count, str(output_dir)


# ============================================================
# 图形化界面
# ============================================================

class JsonToCsvGUI:
    """JSON转CSV图形化界面"""

    def __init__(self):
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox, scrolledtext

        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.scrolledtext = scrolledtext

        self.root = tk.Tk()
        self.root.title("JSON to CSV 转换工具")
        self.root.geometry("750x650")
        self.root.minsize(700, 600)

        # 设置样式
        self.style = ttk.Style()
        self.style.configure('Title.TLabel', font=('Microsoft YaHei UI', 14, 'bold'))
        self.style.configure('Info.TLabel', font=('Microsoft YaHei UI', 9))

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        tk = self.tk
        ttk = self.ttk

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="JSON to CSV 转换工具", style='Title.TLabel')
        title_label.pack(pady=(0, 10))

        # ========== 模式选择 ==========
        mode_frame = ttk.LabelFrame(main_frame, text="转换模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.mode_var = tk.StringVar(value="batch")

        ttk.Radiobutton(mode_frame, text="批量转换（整个文件夹）",
                       variable=self.mode_var, value="batch",
                       command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="单文件转换",
                       variable=self.mode_var, value="single",
                       command=self.on_mode_change).pack(anchor=tk.W)

        # ========== 输入选择 ==========
        input_frame = ttk.LabelFrame(main_frame, text="输入", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        input_row = ttk.Frame(input_frame)
        input_row.pack(fill=tk.X)

        self.input_label = ttk.Label(input_row, text="JSON文件夹:")
        self.input_label.pack(side=tk.LEFT)

        self.input_path = tk.StringVar()
        self.input_entry = ttk.Entry(input_row, textvariable=self.input_path, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)

        self.input_btn = ttk.Button(input_row, text="浏览...", command=self.browse_input)
        self.input_btn.pack(side=tk.LEFT)

        # ========== 输出选择 ==========
        output_frame = ttk.LabelFrame(main_frame, text="输出", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))

        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X)

        ttk.Label(output_row, text="输出文件夹:").pack(side=tk.LEFT)

        self.output_path = tk.StringVar()
        self.output_entry = ttk.Entry(output_row, textvariable=self.output_path, width=50)
        self.output_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)

        self.output_btn = ttk.Button(output_row, text="浏览...", command=self.browse_output)
        self.output_btn.pack(side=tk.LEFT)

        ttk.Label(output_frame, text="(留空则自动在输入目录下创建 csv_output 文件夹)",
                 style='Info.TLabel').pack(anchor=tk.W, pady=(5, 0))

        # ========== 进度条 ==========
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="就绪", style='Info.TLabel')
        self.progress_label.pack(anchor=tk.W, pady=(5, 0))

        # ========== 日志区域 ==========
        log_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = self.scrolledtext.ScrolledText(log_frame, height=10,
                                                        font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志颜色标签
        self.log_text.tag_configure('success', foreground='green')
        self.log_text.tag_configure('error', foreground='red')
        self.log_text.tag_configure('warning', foreground='orange')
        self.log_text.tag_configure('info', foreground='blue')

        # ========== 按钮区域 ==========
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        self.convert_btn = ttk.Button(btn_frame, text="开始转换", command=self.start_convert)
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_btn = ttk.Button(btn_frame, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.open_folder_btn = ttk.Button(btn_frame, text="打开输出目录",
                                          command=self.open_output_folder, state=tk.DISABLED)
        self.open_folder_btn.pack(side=tk.LEFT)

        # 记录最后的输出目录
        self.last_output_dir = None

    def on_mode_change(self):
        """模式切换时更新界面"""
        if self.mode_var.get() == "batch":
            self.input_label.config(text="JSON文件夹:")
        else:
            self.input_label.config(text="JSON文件:")

    def browse_input(self):
        """浏览输入路径"""
        if self.mode_var.get() == "batch":
            path = self.filedialog.askdirectory(title="选择JSON文件所在目录")
        else:
            path = self.filedialog.askopenfilename(
                title="选择JSON文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
        if path:
            self.input_path.set(path)

    def browse_output(self):
        """浏览输出路径"""
        path = self.filedialog.askdirectory(title="选择CSV输出目录")
        if path:
            self.output_path.set(path)

    def log(self, message, tag=None):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(self.tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(self.tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, self.tk.END)

    def update_progress(self, current, total):
        """更新进度条"""
        percent = (current / total) * 100 if total > 0 else 0
        self.progress_var.set(percent)
        self.progress_label.config(text=f"进度: {current}/{total} ({percent:.1f}%)")
        self.root.update_idletasks()

    def start_convert(self):
        """开始转换"""
        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip() or None

        if not input_path:
            self.messagebox.showwarning("警告", "请选择输入路径！")
            return

        if not os.path.exists(input_path):
            self.messagebox.showerror("错误", f"路径不存在: {input_path}")
            return

        # 禁用按钮
        self.convert_btn.config(state=self.tk.DISABLED)
        self.progress_var.set(0)

        try:
            if self.mode_var.get() == "batch":
                # 批量转换
                self.log("开始批量转换...", "info")
                success, fail, output_dir = batch_convert(
                    input_path,
                    output_path,
                    callback=self.log,
                    progress_callback=self.update_progress
                )
                self.last_output_dir = output_dir
                self.log(f"\n转换完成! 成功: {success}, 失败: {fail}", "info")
                self.log(f"CSV文件保存在: {output_dir}", "info")

                if success > 0:
                    self.open_folder_btn.config(state=self.tk.NORMAL)
                    self.messagebox.showinfo("完成",
                        f"转换完成!\n成功: {success} 个文件\n失败: {fail} 个文件\n\n输出目录: {output_dir}")
            else:
                # 单文件转换
                self.log("开始转换文件...", "info")

                if output_path:
                    csv_path = Path(output_path) / Path(input_path).with_suffix('.csv').name
                else:
                    csv_path = None

                success, count = json_to_csv(input_path, csv_path, callback=self.log)

                if success:
                    self.last_output_dir = str(Path(csv_path or input_path).parent)
                    self.open_folder_btn.config(state=self.tk.NORMAL)
                    self.progress_var.set(100)
                    self.progress_label.config(text="完成")
                    self.messagebox.showinfo("完成", f"转换成功!\n共 {count} 条记录")

        except Exception as e:
            self.log(f"发生错误: {e}", "error")
            self.messagebox.showerror("错误", str(e))
        finally:
            self.convert_btn.config(state=self.tk.NORMAL)

    def open_output_folder(self):
        """打开输出目录"""
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            os.startfile(self.last_output_dir)

    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description='将JSON文件转换为CSV格式')
    parser.add_argument('input', nargs='?', help='输入的JSON文件或目录路径')
    parser.add_argument('-o', '--output', help='输出的CSV文件或目录路径')
    parser.add_argument('-e', '--encoding', default='utf-8', help='文件编码 (默认: utf-8)')
    parser.add_argument('-b', '--batch', action='store_true', help='批量转换目录中的所有JSON文件')
    parser.add_argument('-g', '--gui', action='store_true', help='启动图形化界面')

    args = parser.parse_args()

    # 如果没有参数或指定了--gui，启动图形界面
    if args.gui or (args.input is None and len(sys.argv) == 1):
        try:
            app = JsonToCsvGUI()
            app.run()
        except ImportError:
            print("错误: 无法加载tkinter，请确保已安装Python GUI支持")
            sys.exit(1)
    elif args.input:
        input_path = Path(args.input)
        if args.batch or input_path.is_dir():
            success, fail, output_dir = batch_convert(input_path, args.output, args.encoding)
            print(f"\n转换完成! 成功: {success}, 失败: {fail}")
            print(f"CSV文件保存在: {output_dir}")
        else:
            json_to_csv(input_path, args.output, args.encoding)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
