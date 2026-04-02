# -*- coding: utf-8 -*-
"""
城市天气查询小程序
功能：查询城市实时天气、历史记录、一键复制、配置管理
作者：天气查询助手
依赖：tkinter（内置）、requests、json（内置）
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


# ==================== 天气数据实体类 ====================
class WeatherData:
    """天气数据实体类"""
    
    def __init__(self):
        self.city: str = ""           # 城市名
        self.weather: str = ""        # 天气状况
        self.temperature: str = ""    # 实时温度
        self.feels_like: str = ""     # 体感温度
        self.humidity: str = ""       # 湿度
        self.wind: str = ""           # 风力风向
        self.update_time: str = ""    # 更新时间
    
    def to_text(self) -> str:
        """格式化天气文本，用于复制和展示"""
        if not self.is_valid():
            return ""
        
        text = f"""【{self.city}天气】
天气状况：{self.weather}
实时温度：{self.temperature}
体感温度：{self.feels_like}
空气湿度：{self.humidity}
风力风向：{self.wind}
更新时间：{self.update_time}"""
        return text
    
    def is_valid(self) -> bool:
        """校验数据是否完整"""
        return bool(self.city and self.weather)


# ==================== 天气接口请求类 ====================
class WeatherAPI:
    """天气接口请求类 - 使用高德地图免费天气API"""
    
    def __init__(self, api_key: str = ""):
        self.api_key: str = api_key
        self.api_url: str = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.timeout: int = 10  # 请求超时时间
    
    def get_weather(self, city_name: str) -> Optional[WeatherData]:
        """请求天气数据"""
        if not self.api_key:
            return None
        
        try:
            # 先获取城市编码
            city_code = self._get_city_code(city_name)
            if not city_code:
                return None
            
            # 请求天气数据
            params = {
                "city": city_code,
                "key": self.api_key,
                "extensions": "base",  # base=实况天气
                "output": "JSON"
            }
            
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.timeout
            )
            
            return self.parse_response(response.json())
            
        except requests.exceptions.Timeout:
            raise Exception("网络请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise Exception("网络连接失败，请检查网络设置")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求异常：{str(e)}")
        except json.JSONDecodeError:
            raise Exception("API返回数据格式错误")
    
    def _get_city_code(self, city_name: str) -> Optional[str]:
        """获取城市编码（高德地图需要城市adcode）"""
        # 常用城市编码映射表（可扩展）
        city_code_map = {
            # 直辖市
            "北京": "110000", "北京市": "110000",
            "天津": "120000", "天津市": "120000",
            "上海": "310000", "上海市": "310000",
            "重庆": "500000", "重庆市": "500000",
            # 省会城市
            "广州": "440100", "广州市": "440100",
            "深圳": "440300", "深圳市": "440300",
            "杭州": "330100", "杭州市": "330100",
            "南京": "320100", "南京市": "320100",
            "武汉": "420100", "武汉市": "420100",
            "成都": "510100", "成都市": "510100",
            "西安": "610100", "西安市": "610100",
            "郑州": "410100", "郑州市": "410100",
            "长沙": "430100", "长沙市": "430100",
            "济南": "370100", "济南市": "370100",
            "青岛": "370200", "青岛市": "370200",
            "沈阳": "210100", "沈阳市": "210100",
            "大连": "210200", "大连市": "210200",
            "哈尔滨": "230100", "哈尔滨市": "230100",
            "长春": "220100", "长春市": "220100",
            "石家庄": "130100", "石家庄市": "130100",
            "太原": "140100", "太原市": "140100",
            "合肥": "340100", "合肥市": "340100",
            "福州": "350100", "福州市": "350100",
            "厦门": "350200", "厦门市": "350200",
            "南昌": "360100", "南昌市": "360100",
            "昆明": "530100", "昆明市": "530100",
            "贵阳": "520100", "贵阳市": "520100",
            "南宁": "450100", "南宁市": "450100",
            "海口": "460100", "海口市": "460100",
            "兰州": "620100", "兰州市": "620100",
            "西宁": "630100", "西宁市": "630100",
            "银川": "640100", "银川市": "640100",
            "乌鲁木齐": "650100", "乌鲁木齐市": "650100",
            "呼和浩特": "150100", "呼和浩特市": "150100",
            "拉萨": "540100", "拉萨市": "540100",
            # 其他城市
            "苏州": "320500", "苏州市": "320500",
            "无锡": "320200", "无锡市": "320200",
            "宁波": "330200", "宁波市": "330200",
            "温州": "330300", "温州市": "330300",
            "东莞": "441900", "东莞市": "441900",
            "佛山": "440600", "佛山市": "440600",
            "珠海": "440400", "珠海市": "440400",
            "中山": "442000", "中山市": "442000",
            "惠州": "441300", "惠州市": "441300",
            "烟台": "370600", "烟台市": "370600",
            "潍坊": "370700", "潍坊市": "370700",
            "临沂": "371300", "临沂市": "371300",
            "淄博": "370300", "淄博市": "370300",
            "唐山": "130200", "唐山市": "130200",
            "保定": "130600", "保定市": "130600",
            "廊坊": "131000", "廊坊市": "131000",
            "洛阳": "410300", "洛阳市": "410300",
            "开封": "410200", "开封市": "410200",
            "徐州": "320300", "徐州市": "320300",
            "常州": "320400", "常州市": "320400",
            "南通": "320600", "南通市": "320600",
            "扬州": "321000", "扬州市": "321000",
            "镇江": "321100", "镇江市": "321100",
            "泰州": "321200", "泰州市": "321200",
            "嘉兴": "330400", "嘉兴市": "330400",
            "金华": "330700", "金华市": "330700",
            "绍兴": "330600", "绍兴市": "330600",
            "台州": "331000", "台州市": "331000",
            "湖州": "330500", "湖州市": "330500",
        }
        
        # 去除空格并查找
        city_name = city_name.strip()
        return city_code_map.get(city_name)
    
    def parse_response(self, resp: Dict[str, Any]) -> Optional[WeatherData]:
        """解析API返回数据"""
        if not resp:
            return None
        
        # 检查返回状态
        if resp.get("status") != "1":
            info = resp.get("info", "未知错误")
            raise Exception(f"API返回错误：{info}")
        
        # 获取天气数据列表
        lives = resp.get("lives", [])
        if not lives:
            return None
        
        live_data = lives[0]
        
        # 构建天气数据对象
        weather_data = WeatherData()
        weather_data.city = live_data.get("city", "")
        weather_data.weather = live_data.get("weather", "")
        weather_data.temperature = live_data.get("temperature", "") + "°C"
        weather_data.feels_like = live_data.get("temperature", "") + "°C"  # 高德实况天气无体感温度
        weather_data.humidity = live_data.get("humidity", "") + "%"
        weather_data.wind = live_data.get("winddirection", "") + " " + live_data.get("windpower", "") + "级"
        weather_data.update_time = live_data.get("reporttime", "")
        
        return weather_data
    
    def check_key(self) -> bool:
        """校验密钥有效性"""
        if not self.api_key:
            return False
        
        try:
            params = {
                "city": "110000",  # 北京
                "key": self.api_key,
                "extensions": "base",
                "output": "JSON"
            }
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.timeout
            )
            result = response.json()
            return result.get("status") == "1"
        except:
            return False


# ==================== 本地数据存储类 ====================
class WeatherStore:
    """本地数据存储类 - 使用JSON文件存储配置和历史"""
    
    def __init__(self):
        # 获取程序所在目录
        self.app_dir: str = os.path.dirname(os.path.abspath(__file__))
        self.config_path: str = os.path.join(self.app_dir, "weather_config.json")
        self.history_path: str = os.path.join(self.app_dir, "weather_history.json")
        self.max_history: int = 10  # 最大历史记录数
    
    def load_config(self) -> str:
        """加载API密钥"""
        if not os.path.exists(self.config_path):
            return ""
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("api_key", "")
        except:
            return ""
    
    def save_config(self, key: str) -> bool:
        """保存API密钥"""
        try:
            config = {"api_key": key}
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def load_history(self) -> List[str]:
        """加载查询历史"""
        if not os.path.exists(self.history_path):
            return []
        
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                return history if isinstance(history, list) else []
        except:
            return []
    
    def save_history(self, city: str) -> bool:
        """保存查询历史"""
        try:
            history = self.load_history()
            
            # 如果城市已存在，先移除
            if city in history:
                history.remove(city)
            
            # 添加到最前面
            history.insert(0, city)
            
            # 保留最近10条
            history = history[:self.max_history]
            
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def clear_history(self) -> bool:
        """清空历史"""
        try:
            if os.path.exists(self.history_path):
                os.remove(self.history_path)
            return True
        except:
            return False


# ==================== GUI界面管理类 ====================
class UIManager:
    """GUI界面管理类 - 管理所有界面组件和交互"""
    
    def __init__(self, root: tk.Tk, store: WeatherStore, api: WeatherAPI):
        self.root = root
        self.store = store
        self.api = api
        self.current_weather: Optional[WeatherData] = None  # 当前天气数据
        
        # 初始化界面
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """初始化界面组件"""
        # 设置窗口属性
        self.root.title("城市天气查询助手")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # 设置窗口图标（如果有的话）
        try:
            # 居中显示窗口
            self.root.update_idletasks()
            width = 500
            height = 600
            x = (self.root.winfo_screenwidth() - width) // 2
            y = (self.root.winfo_screenheight() - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except:
            pass
        
        # 创建主容器
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个子组件
        self._create_search_bar()
        self._create_history_bar()
        self._create_weather_panel()
        self._create_toolbar()
        self._create_status_bar()
    
    def _create_search_bar(self):
        """创建顶部搜索栏"""
        search_frame = ttk.LabelFrame(self.main_frame, text="城市查询", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 输入框和按钮容器
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill=tk.X)
        
        # 城市输入框
        ttk.Label(input_frame, text="城市名称：").pack(side=tk.LEFT)
        self.city_entry = ttk.Entry(input_frame, width=20, font=("微软雅黑", 11))
        self.city_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.city_entry.bind("<Return>", lambda e: self._on_search())  # 回车查询
        
        # 查询按钮
        self.search_btn = ttk.Button(
            input_frame,
            text="查询天气",
            command=self._on_search,
            width=12
        )
        self.search_btn.pack(side=tk.LEFT)
    
    def _create_history_bar(self):
        """创建历史记录快捷按钮栏"""
        history_frame = ttk.LabelFrame(self.main_frame, text="历史记录", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 历史按钮容器（使用Frame便于动态更新）
        self.history_container = ttk.Frame(history_frame)
        self.history_container.pack(fill=tk.X)
        
        # 初始提示标签
        self.history_label = ttk.Label(
            self.history_container,
            text="暂无历史记录",
            foreground="gray"
        )
        self.history_label.pack()
    
    def _create_weather_panel(self):
        """创建中间天气展示面板"""
        weather_frame = ttk.LabelFrame(self.main_frame, text="天气信息", padding="15")
        weather_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 天气展示区域
        self.weather_text = tk.Text(
            weather_frame,
            font=("微软雅黑", 11),
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=15,
            padx=10,
            pady=10
        )
        self.weather_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始提示
        self._show_placeholder()
    
    def _create_toolbar(self):
        """创建底部工具栏"""
        toolbar_frame = ttk.Frame(self.main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 复制按钮
        self.copy_btn = ttk.Button(
            toolbar_frame,
            text="复制天气",
            command=self.copy_weather,
            width=12
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 清空历史按钮
        self.clear_btn = ttk.Button(
            toolbar_frame,
            text="清空历史",
            command=self._on_clear_history,
            width=12
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 设置按钮
        self.settings_btn = ttk.Button(
            toolbar_frame,
            text="API设置",
            command=self.open_settings,
            width=12
        )
        self.settings_btn.pack(side=tk.LEFT)
    
    def _create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            foreground="gray",
            font=("微软雅黑", 9)
        )
        self.status_label.pack(side=tk.LEFT)
    
    def _load_data(self):
        """加载本地数据"""
        # 加载API密钥
        api_key = self.store.load_config()
        if api_key:
            self.api.api_key = api_key
            self.status_label.config(text="已加载API密钥")
        else:
            self.status_label.config(text="请先设置API密钥")
        
        # 加载历史记录
        self.refresh_history()
    
    def _show_placeholder(self):
        """显示占位提示"""
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete("1.0", tk.END)
        self.weather_text.insert(
            "1.0",
            "\n\n    请输入城市名称查询天气\n\n"
            "    支持查询：直辖市、省会城市、主要地级市\n\n"
            "    首次使用请点击「API设置」配置密钥"
        )
        self.weather_text.config(state=tk.DISABLED)
    
    def _on_search(self):
        """查询按钮点击事件"""
        city_name = self.city_entry.get().strip()
        
        if not city_name:
            messagebox.showwarning("提示", "请输入城市名称")
            return
        
        if not self.api.api_key:
            messagebox.showwarning("提示", "请先设置API密钥")
            self.open_settings()
            return
        
        # 更新状态
        self.status_label.config(text=f"正在查询 {city_name} 的天气...")
        self.search_btn.config(state=tk.DISABLED)
        self.root.update()
        
        try:
            # 请求天气数据
            weather_data = self.api.get_weather(city_name)
            
            if weather_data and weather_data.is_valid():
                # 保存到历史记录
                self.store.save_history(city_name)
                self.refresh_history()
                
                # 显示天气
                self.show_weather(weather_data)
                self.current_weather = weather_data
                self.status_label.config(text=f"查询成功 - {weather_data.update_time}")
            else:
                self.show_error(f"未找到城市「{city_name}」的天气信息\n\n请检查城市名称是否正确\n支持：直辖市、省会城市、主要地级市")
                self.status_label.config(text="查询失败")
        
        except Exception as e:
            self.show_error(str(e))
            self.status_label.config(text="查询失败")
        
        finally:
            self.search_btn.config(state=tk.NORMAL)
    
    def _on_history_click(self, city: str):
        """历史记录按钮点击事件"""
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self._on_search()
    
    def _on_clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            if self.store.clear_history():
                self.refresh_history()
                self.status_label.config(text="已清空历史记录")
            else:
                messagebox.showerror("错误", "清空历史记录失败")
    
    def show_weather(self, data: WeatherData):
        """渲染天气数据"""
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete("1.0", tk.END)
        
        # 格式化显示
        display_text = f"""
  🏙️  城市：{data.city}
  
  ☁️  天气：{data.weather}
  
  🌡️  温度：{data.temperature}
  
  💧  湿度：{data.humidity}
  
  🌬️  风力：{data.wind}
  
  🕐  更新：{data.update_time}
"""
        self.weather_text.insert("1.0", display_text)
        self.weather_text.config(state=tk.DISABLED)
    
    def show_error(self, msg: str):
        """显示错误提示"""
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete("1.0", tk.END)
        self.weather_text.insert("1.0", f"\n\n    ❌ {msg}")
        self.weather_text.config(state=tk.DISABLED)
        self.current_weather = None
    
    def refresh_history(self):
        """刷新历史按钮"""
        # 清空现有按钮
        for widget in self.history_container.winfo_children():
            widget.destroy()
        
        # 加载历史记录
        history = self.store.load_history()
        
        if not history:
            self.history_label = ttk.Label(
                self.history_container,
                text="暂无历史记录",
                foreground="gray"
            )
            self.history_label.pack()
            return
        
        # 创建历史按钮（每行最多5个）
        row_frame = None
        for i, city in enumerate(history):
            if i % 5 == 0:
                row_frame = ttk.Frame(self.history_container)
                row_frame.pack(fill=tk.X, pady=2)
            
            btn = ttk.Button(
                row_frame,
                text=city,
                width=8,
                command=lambda c=city: self._on_history_click(c)
            )
            btn.pack(side=tk.LEFT, padx=2)
    
    def copy_weather(self):
        """复制天气文本到剪贴板"""
        if not self.current_weather:
            messagebox.showinfo("提示", "暂无天气数据可复制")
            return
        
        text = self.current_weather.to_text()
        
        try:
            # 尝试使用pyperclip
            try:
                import pyperclip
                pyperclip.copy(text)
            except ImportError:
                # 使用Tkinter内置剪贴板
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
            
            self.status_label.config(text="已复制到剪贴板")
            messagebox.showinfo("成功", "天气信息已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def open_settings(self):
        """打开API密钥设置窗口"""
        # 创建设置窗口
        settings_window = tk.Toplevel(self.root)
        settings_window.title("API密钥设置")
        settings_window.geometry("400x200")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 居中显示
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        settings_window.geometry(f"+{x}+{y}")
        
        # 内容框架
        content_frame = ttk.Frame(settings_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 说明标签
        ttk.Label(
            content_frame,
            text="请输入高德地图API密钥：",
            font=("微软雅黑", 10)
        ).pack(anchor=tk.W)
        
        ttk.Label(
            content_frame,
            text="（免费申请：https://console.amap.com/dev/key/app）",
            font=("微软雅黑", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 密钥输入框
        key_var = tk.StringVar(value=self.api.api_key)
        key_entry = ttk.Entry(
            content_frame,
            textvariable=key_var,
            width=45,
            font=("Consolas", 10)
        )
        key_entry.pack(fill=tk.X, pady=(0, 15))
        key_entry.focus_set()
        
        # 按钮框架
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(fill=tk.X)
        
        def on_save():
            new_key = key_var.get().strip()
            
            if not new_key:
                messagebox.showwarning("提示", "请输入API密钥")
                return
            
            # 验证密钥
            temp_api = WeatherAPI(new_key)
            if not temp_api.check_key():
                messagebox.showerror("错误", "API密钥无效，请检查后重试")
                return
            
            # 保存密钥
            if self.store.save_config(new_key):
                self.api.api_key = new_key
                self.status_label.config(text="API密钥已保存")
                messagebox.showinfo("成功", "API密钥保存成功")
                settings_window.destroy()
            else:
                messagebox.showerror("错误", "保存失败，请重试")
        
        def on_test():
            test_key = key_var.get().strip()
            if not test_key:
                messagebox.showwarning("提示", "请输入API密钥")
                return
            
            temp_api = WeatherAPI(test_key)
            if temp_api.check_key():
                messagebox.showinfo("成功", "API密钥有效")
            else:
                messagebox.showerror("失败", "API密钥无效")
        
        ttk.Button(
            btn_frame,
            text="验证密钥",
            command=on_test,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="保存",
            command=on_save,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="取消",
            command=settings_window.destroy,
            width=10
        ).pack(side=tk.LEFT)


# ==================== 主程序入口 ====================
class WeatherApp:
    """天气查询应用主类"""
    
    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        
        # 设置样式
        self._setup_style()
        
        # 初始化组件
        self.store = WeatherStore()
        self.api = WeatherAPI()
        self.ui = UIManager(self.root, self.store, self.api)
    
    def _setup_style(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 使用clam主题（跨平台兼容性好）
        available_themes = style.theme_names()
        if "clam" in available_themes:
            style.theme_use("clam")
        elif "vista" in available_themes:
            style.theme_use("vista")
        
        # 配置按钮样式
        style.configure(
            "TButton",
            font=("微软雅黑", 9),
            padding=5
        )
        
        # 配置标签框样式
        style.configure(
            "TLabelframe.Label",
            font=("微软雅黑", 10, "bold")
        )
        
        # 配置输入框样式
        style.configure(
            "TEntry",
            padding=5
        )
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    """程序入口"""
    app = WeatherApp()
    app.run()


if __name__ == "__main__":
    main()
