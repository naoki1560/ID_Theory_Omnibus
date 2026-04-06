import tkinter as tk
from tkinter import ttk, messagebox
import re
import math
import pandas as pd

class ID_Omnibus_Tool:
    def __init__(self, root):
        self.root = root
        self.root.title("ID Theory: 物性演繹オムニバス・チェッカー")
        self.root.geometry("700x500")

        # マスターデータの読み込み
        try:
            self.db = pd.read_csv('ID_Master_Database.csv')
        except:
            messagebox.showerror("Error", "ID_Master_Database.csv が見つかりません。")
            root.destroy()
            return

        self.setup_ui()

    def setup_ui(self):
        # --- 入力窓 ---
        input_frame = ttk.LabelFrame(self.root, text=" 化学式入力 (例: H2O, 13CO2, D2O ) ")
        input_frame.pack(padx=20, pady=20, fill="x")

        self.formula_entry = ttk.Entry(input_frame, font=("MS Gothic", 12))
        self.formula_entry.pack(padx=10, pady=10, fill="x")
        self.formula_entry.insert(0, "H2O, D2O, T2O") # デフォルト例

        btn = ttk.Button(input_frame, text=" 物性演繹・計算実行 ", command=self.run_calc)
        btn.pack(pady=5)

        # --- 出力窓 (最大3つの比較) ---
        output_frame = ttk.LabelFrame(self.root, text=" 演繹結果 (最大3種類の比較) ")
        output_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.result_text = tk.Text(output_frame, font=("Consolas", 10), bg="#f0f0f0")
        self.result_text.pack(padx=10, pady=10, fill="both", expand=True)

    def parse_element(self, token):
        """トークン(13C, D, H2等)から質量とシンボルを分離"""
        # 同位体指定(数字) + 元素記号 + 個数 のパターン
        match = re.match(r'(\d*)([A-Z][a-z]*)(\d*)', token)
        if not match: return None
        
        iso_mass, sym, count = match.groups()
        count = int(count) if count else 1
        
        # 特殊記号の対応
        if sym == 'D': sym = 'H'; iso_mass = 2.014
        if sym == 'T': sym = 'H'; iso_mass = 3.016
        
        row = self.db[self.db['Symbol'] == sym]
        if row.empty: return None
        row = row.iloc[0]

        # 質量の決定 (指定があればそれ、なければ標準質量)
        actual_mass = float(iso_mass) if iso_mass else float(row['Mass'])
        zc_int = int(str(row['Zc_Hex']), 16)
        w_int = int(str(row['W_Hex']), 16)
        if w_int == 0: w_int = 32768

        return {
            "mass": actual_mass * count,
            "depth": (w_int - zc_int) * count,
            "w_ratio": w_int / 32768.0
        }

    def run_calc(self):
        # カンマまたはスペースで複数の式を分割
        raw_input = self.formula_entry.get()
        formulas = re.split(r'[,\s]+', raw_input)[:3] # 最大3つまで
        
        self.result_text.delete(1.0, tk.END)
        
        headers = ["項目", "Case 1", "Case 2", "Case 3"]
        data_rows = {
            "Formula": [], "Mass": [], "Depth": [], "ZPE": [], "Lambda(nm)": [], "BP(C)": []
        }

        for f in formulas:
            tokens = re.findall(r'(\d*[A-Z][a-z]*\d*)', f)
            t_mass, t_depth, max_w = 0, 0, 1.0
            
            for t in tokens:
                res = self.parse_element(t)
                if res:
                    t_mass += res['mass']
                    t_depth += res['depth']
                    max_w = max(max_w, res['w_ratio'])
            
            if t_mass == 0: continue

            # ID演繹ロジック
            zpe = (t_depth / 100.0) * t_mass
            ev = (zpe / t_mass) * max_w * 4.5
            l_max = 1240.0 / ev if ev > 0 else 0
            tb = ((t_depth / t_mass) * 1.5) * math.exp(120.0 * (max_w - 1.0)) - 273.15

            data_rows["Formula"].append(f)
            data_rows["Mass"].append(f"{t_mass:.3f}")
            data_rows["Depth"].append(f"{t_depth:.1f}")
            data_rows["ZPE"].append(f"{zpe:.2f}")
            data_rows["Lambda(nm)"].append(f"{l_max:.2f}")
            data_rows["BP(C)"].append(f"{tb:.1f}")

        # 表形式で出力
        output = f"{'Item':<15}" + "".join([f"| {v:<15}" for v in data_rows["Formula"]]) + "\n"
        output += "-" * 65 + "\n"
        for label, values in data_rows.items():
            if label == "Formula": continue
            output += f"{label:<15}" + "".join([f"| {v:<15}" for v in values]) + "\n"
        
        self.result_text.insert(tk.END, output)

if __name__ == "__main__":
    root = tk.Tk()
    app = ID_Omnibus_Tool(root)
    root.mainloop()
