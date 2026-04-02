# -*- coding: utf-8 -*-
"""
城市天气查询小程序
纯 Python + Tkinter 原生 GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

try:
    import pyperclip
except ImportError:
    pyperclip = None


class WeatherData:
    """天气数据实体类"""
    
    def __init__(self):
        self.city = ""
        self.weather = ""
        self.temperature = ""
        self.feels_like = ""
        self.humidity = ""
        self.wind = ""
        self.update_time = ""
    
    def to_text(self):
        """格式化天气文本"""
        text = f"""【{self.city} 天气信息】
━━━━━━━━━━━━━━━━
天气状况：{self.weather}
实时温度：{self.temperature}℃
体感温度：{self.feels_like}℃
相对湿度：{self.humidity}%
风力风向：{self.wind}
更新时间：{self.update_time}
━━━━━━━━━━━━━━━━"""
        return text
    
    def is_valid(self):
        """校验数据是否完整"""
        return all([self.city, self.weather, self.temperature])


class WeatherAPI:
    """天气接口请求类 - 高德地图天气API"""
    
    def __init__(self, api_key=""):
        self.api_key = api_key
        self.api_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.timeout = 10
    
    def check_key(self):
        """校验密钥有效性"""
        if not self.api_key or len(self.api_key) < 10:
            return False, "API密钥格式不正确"
        return True, "密钥格式校验通过"
    
    def get_weather(self, city_name):
        """请求天气数据"""
        if not requests:
            return None, "未安装 requests 库，请运行：pip install requests"
        
        if not self.api_key:
            return None, "请先设置 API 密钥"
        
        try:
            params = {
                "key": self.api_key,
                "city": city_name,
                "extensions": "base",
                "output": "json"
            }
            
            response = requests.get(self.api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return self.parse_response(response.json())
            
        except requests.exceptions.Timeout:
            return None, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return None, "网络连接失败，请检查网络设置"
        except requests.exceptions.RequestException as e:
            return None, f"请求错误：{str(e)}"
        except Exception as e:
            return None, f"未知错误：{str(e)}"
    
    def parse_response(self, resp):
        """解析  API  返回数据"""
        try:
            if resp.get("status") != "1":
                info = resp.get("info", "未知错误")
                if "INVALID_USER_KEY" in info:
                    return None, "API密钥无效，请检查密钥是否正确"
                elif "DAILY_QUERY_OVER_LIMIT" in info:
                    return None, "今日API调用次数已达上限"
                return None, f"查询失败：{info}"
            
            lives = resp.get("lives", [])
            if not lives:
                return None, "未找到该城市的天气数据，请检查城市名称"
            
            live = lives[0]
            data = WeatherData()
            data.city = live.get("city", "未知城市")
            data.weather = live.get("weather", "未知")
            data.temperature = live.get("temperature", "未知")
            data.feels_like = live.get("feels_like", "未知")
            data.humidity = live.get("humidity", "未知")
            
            wind_direction = live.get("winddirection", "未知")
            wind_power = live.get("windpower", "未知")
            data.wind = f"{wind_direction}风 {wind_power}级"
            
            report_time = live.get("reporttime", "")
            if report_time:
                data.update_time = report_time
            else:
                data.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if data.is_valid():
                return data, None
            return None, "天气数据不完整"
            
        except Exception as e:
            return None, f"解析数据失败：{str(e)}"


class WeatherStore:
    """本地数据存储类"""
    
    def __init__(self):
        app_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(app_dir, "weather_config.json")
        self.history_path = os.path.join(app_dir, "weather_history.json")
        self.max_history = 10
    
    def load_config(self):
        """加载 API 密钥"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("api_key", "")
        except:
            pass
        return ""
    
    def save_config(self, key):
        """保存 API 密钥"""
        try:
            config = {"api_key": key}
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def load_history(self):
        """加载查询历史"""
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    return history if isinstance(history, list) else []
        except:
            pass
        return []
    
    def save_history(self, city):
        """保存查询历史"""
        try:
            history = self.load_history()
            if city in history:
                history.remove(city)
            history.insert(0, city)
            history = history[:self.max_history]
            
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def clear_history(self):
        """清空历史"""
        try:
            if os.path.exists(self.history_path):
                os.remove(self.history_path)
            return True
        except:
            return False


class UIManager:
    """GUI 界面管理类"""
    
    def __init__(self, root):
        self.root = root
        self.current_data = None
        
        self.store = WeatherStore()
        self.api = WeatherAPI(self.store.load_config())
        
        self.setup_ui()
        self.refresh_history()
        
        if not self.api.api_key:
            self.root.after(100, self.show_first_run_tip)
    
    def show_first_run_tip(self):
        """首次运行提示"""
        messagebox.showinfo(
            "欢迎使用",
            "欢迎使用城市天气查询！\n\n"
            "首次使用请先设置高德地图 API 密钥。\n"
            "点击【设置】按钮即可配置。\n\n"
            "详细申请教程请查看使用说明文档。"
        )
    
    def setup_ui(self):
        """设置界面"""
        self.root.title("城市天气查询")
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        
        self.root.configure(bg="#f5f5f5")
        
        style = ttk.Style()
        style.configure("TButton", font=("微软雅黑", 10))
        style.configure("TLabel", font=("微软雅黑", 10), background="#f5f5f5")
        
        main_frame = tk.Frame(self.root, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.create_search_bar(main_frame)
        self.create_history_bar(main_frame)
        self.create_weather_panel(main_frame)
        self.create_toolbar(main_frame)
    
    def create_search_bar(self, parent):
        """创建搜索栏"""
        frame = tk.Frame(parent, bg="#f5f5f5")
        frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            frame,
            text="城市名称：",
            font=("微软雅黑", 11),
            bg="#f5f5f5"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.city_entry = tk.Entry(
            frame,
            font=("微软雅黑", 11),
            width=25,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.city_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        self.city_entry.bind("<Return>", lambda e: self.search_weather())
        
        search_btn = tk.Button(
            frame,
            text="查询天气",
            font=("微软雅黑", 11, "bold"),
            bg="#2196F3",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.search_weather,
            cursor="hand2"
        )
        search_btn.pack(side=tk.LEFT)
    
    def create_history_bar(self, parent):
        """创建历史记录栏"""
        frame = tk.LabelFrame(
            parent,
            text=" 历史查询 ",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#666"
        )
        frame.pack(fill=tk.X, pady=(0, 15))
        
        self.history_frame = tk.Frame(frame, bg="#f5f5f5")
        self.history_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def create_weather_panel(self, parent):
        """创建天气展示面板"""
        panel_frame = tk.LabelFrame(
            parent,
            text=" 天气信息 ",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#666"
        )
        panel_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.weather_panel = tk.Frame(panel_frame, bg="white", relief=tk.SOLID, borderwidth=1)
        self.weather_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.weather_content = tk.Frame(self.weather_panel, bg="white")
        self.weather_content.pack(expand=True)
        
        self.empty_label = tk.Label(
            self.weather_content,
            text="请输入城市名称，点击查询天气",
            font=("微软雅黑", 12),
            fg="#999",
            bg="white"
        )
        self.empty_label.pack(pady=80)
        
        self.info_labels = {}
    
    def create_toolbar(self, parent):
        """创建工具栏"""
        frame = tk.Frame(parent, bg="#f5f5f5")
        frame.pack(fill=tk.X)
        
        copy_btn = tk.Button(
            frame,
            text="📋 复制天气",
            font=("微软雅黑", 10),
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.copy_weather,
            cursor="hand2"
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = tk.Button(
            frame,
            text="🗑️ 清空历史",
            font=("微软雅黑", 10),
            bg="#FF9800",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.clear_history,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        settings_btn = tk.Button(
            frame,
            text="⚙️ API设置",
            font=("微软雅黑", 10),
            bg="#9C27B0",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.open_settings,
            cursor="hand2"
        )
        settings_btn.pack(side=tk.LEFT)
    
    def refresh_history(self):
        """刷新历史按钮"""
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        history = self.store.load_history()
        
        if not history:
            tk.Label(
                self.history_frame,
                text="暂无历史记录",
                font=("微软雅黑", 9),
                fg="#999",
                bg="#f5f5f5"
            ).pack(side=tk.LEFT)
            return
        
        for city in history:
            btn = tk.Button(
                self.history_frame,
                text=city,
                font=("微软雅黑", 9),
                bg="#E3F2FD",
                fg="#1976D2",
                relief=tk.FLAT,
                padx=8,
                pady=3,
                command=lambda c=city: self.search_by_history(c),
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=(0, 8))
    
    def search_by_history(self, city):
        """通过历史记录查询"""
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self.search_weather()
    
    def search_weather(self):
        """查询天气"""
        city = self.city_entry.get().strip()
        if not city:
            self.show_error("请输入城市名称")
            return
        
        self.show_error("正在查询天气...", is_loading=True)
        
        self.root.update()
        
        data, error = self.api.get_weather(city)
        
        if error:
            self.show_error(error)
            return
        
        self.show_weather(data)
        self.store.save_history(city)
        self.refresh_history()
    
    def show_weather(self, data):
        """渲染天气数据"""
        self.current_data = data
        
        for widget in self.weather_content.winfo_children():
            widget.destroy()
        
        city_frame = tk.Frame(self.weather_content, bg="white")
        city_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            city_frame,
            text=data.city,
            font=("微软雅黑", 20, "bold"),
            fg="#333",
            bg="white"
        ).pack()
        
        main_frame = tk.Frame(self.weather_content, bg="white")
        main_frame.pack(fill=tk.X, pady=(0, 20))
        
        temp_frame = tk.Frame(main_frame, bg="white")
        temp_frame.pack(side=tk.LEFT, padx=(0, 40))
        
        tk.Label(
            temp_frame,
            text=f"{data.temperature}°",
            font=("微软雅黑", 48),
            fg="#FF5722",
            bg="white"
        ).pack()
        
        tk.Label(
            temp_frame,
            text=f"体感 {data.feels_like}°",
            font=("微软雅黑", 10),
            fg="#999",
            bg="white"
        ).pack()
        
        weather_frame = tk.Frame(main_frame, bg="white")
        weather_frame.pack(side=tk.LEFT)
        
        tk.Label(
            weather_frame,
            text=data.weather,
            font=("微软雅黑", 18),
            fg="#333",
            bg="white"
        ).pack(pady=(0, 10))
        
        tk.Label(
            weather_frame,
            text=f"💧 湿度 {data.humidity}%",
            font=("微软雅黑", 11),
            fg="#666",
            bg="white"
        ).pack(anchor=tk.W, pady=2)
        
        tk.Label(
            weather_frame,
            text=f"🌬️ {data.wind}",
            font=("微软雅黑", 11),
            fg="#666",
            bg="white"
        ).pack(anchor=tk.W, pady=2)
        
        tk.Label(
            self.weather_content,
            text=f"更新时间：{data.update_time}",
            font=("微软雅黑", 9),
            fg="#999",
            bg="white"
        ).pack(pady=(20, 0))
    
    def show_error(self, msg, is_loading=False):
        """显示错误提示"""
        if is_loading:
            color = "#2196F3"
        else:
            color = "#F44336"
        
        for widget in self.weather_content.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.weather_content,
            text=msg,
            font=("微软雅黑", 12),
            fg=color,
            bg="white",
            wraplength=350
        ).pack(pady=80)
    
    def copy_weather(self):
        """复制天气文本"""
        if not self.current_data:
            messagebox.showwarning("提示", "没有可复制的天气数据")
            return
        
        text = self.current_data.to_text()
        
        if pyperclip:
            try:
                pyperclip.copy(text)
                messagebox.showinfo("成功", "天气信息已复制到剪贴板")
                return
            except:
                pass
        
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("成功", "天气信息已复制到剪贴板")
    
    def clear_history(self):
        """清空历史记录"""
        result = messagebox.askyesno("确认", "确定要清空所有历史记录吗？")
        if result:
            self.store.clear_history()
            self.refresh_history()
            messagebox.showinfo("成功", "历史记录已清空")
    
    def open_settings(self):
        """打开 API 密钥设置窗口"""
        current_key = self.api.api_key
        masked_key = current_key[:6] + "*" * 20 + current_key[-4:] if current_key else "未设置"
        
        dialog = tk.Toplevel(self.root)
        dialog.title("API 密钥设置")
        dialog.geometry("450x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg="#f5f5f5")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            frame,
            text="高德地图 Web 服务 API 密钥",
            font=("微软雅黑", 12, "bold"),
            bg="#f5f5f5"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        tk.Label(
            frame,
            text=f"当前密钥：{masked_key}",
            font=("微软雅黑", 9),
            fg="#666",
            bg="#f5f5f5"
        ).pack(anchor=tk.W, pady=(0, 15))
        
        tk.Label(
            frame,
            text="请输入新的 API 密钥：",
            font=("微软雅黑", 10),
            bg="#f5f5f5"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        key_entry = tk.Entry(
            frame,
            font=("微软雅黑", 11),
            width=50,
            relief=tk.SOLID,
            borderwidth=1,
            show="*"
        )
        key_entry.pack(fill=tk.X, ipady=5, pady=(0, 15))
        key_entry.insert(0, current_key)
        
        def save_key():
            new_key = key_entry.get().strip()
            if not new_key:
                messagebox.showwarning("提示", "API密钥不能为空")
                return
            
            self.api.api_key = new_key
            self.store.save_config(new_key)
            messagebox.showinfo("成功", "API密钥已保存")
            dialog.destroy()
        
        btn_frame = tk.Frame(frame, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="保存",
            font=("微软雅黑", 10),
            bg="#2196F3",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            command=save_key
        ).pack(side=tk.RIGHT)


def main():
    """主函数"""
    root = tk.Tk()
    app = UIManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
