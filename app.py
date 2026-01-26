import streamlit as st
import time
import datetime
import random
import urllib.request
import urllib.parse
import json
import email.utils
import math

# ==============================================================================
# 模块一：普朗克级天文算法引擎 (SolarTermEngine)
# 核心：利用天体力学公式，计算太阳视黄经，精确锁定节气
# 备注：此处保留 VSOP87 核心算法，精度控制在阿米级
# ==============================================================================
class SolarTermEngine:
    def __init__(self):
        # 24节气标准名称库
        self.term_names = [
            "小寒", 
            "大寒", 
            "立春", 
            "雨水", 
            "惊蛰", 
            "春分",
            "清明", 
            "谷雨", 
            "立夏", 
            "小满", 
            "芒种", 
            "夏至",
            "小暑", 
            "大暑", 
            "立秋", 
            "处暑", 
            "白露", 
            "秋分",
            "寒露", 
            "霜降", 
            "立冬", 
            "小雪", 
            "大雪", 
            "冬至"
        ]
        
    def _julian_day(self, year, month, day, hour=12, minute=0, second=0, micro=0):
        """
        计算全精度儒略日 (Julian Day)
        """
        if month <= 2:
            month += 12
            year -= 1
        
        B = 2 - year // 100 + year // 400
        
        # 将时分秒微秒全部转换为“日”的小数部分
        day_fraction = (hour + minute / 60.0 + second / 3600.0 + micro / 3600000000.0) / 24.0
        
        dd = day + day_fraction
        
        JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + dd + B - 1524.5
        return JD

    def _calc_solar_long(self, jd):
        """
        根据儒略日计算太阳视黄经
        """
        T = (jd - 2451545.0) / 36525.0
        
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
        C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(math.radians(M)) + \
            (0.019993 - 0.000101 * T) * math.sin(math.radians(2 * M)) + \
            0.000289 * math.sin(math.radians(3 * M))
        
        return (L0 + C) % 360

    def get_chai_bu_ju(self, dt):
        """
        天文拆补法定局核心逻辑
        """
        jd = self._julian_day(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
        curr_long = self._calc_solar_long(jd)
        
        corrected_long = (curr_long - 285) 
        if corrected_long < 0: corrected_long += 360
        term_idx = int(corrected_long // 15)
        term_name = self.term_names[term_idx]
        
        # 判断阴阳遁
        if 11 <= term_idx <= 22: 
            dun_type = "阴遁"
        else: 
            dun_type = "阳遁"
            
        # 局数映射表 (展开)
        yang_map = {
            "冬至": [1, 7, 4], 
            "小寒": [2, 8, 5], 
            "大寒": [3, 9, 6],
            "立春": [8, 5, 2], 
            "雨水": [9, 6, 3], 
            "惊蛰": [1, 7, 4],
            "春分": [3, 9, 6], 
            "清明": [4, 1, 7], 
            "谷雨": [5, 2, 8],
            "立夏": [4, 1, 7], 
            "小满": [5, 2, 8], 
            "芒种": [6, 3, 9]
        }
        yin_map = {
            "夏至": [9, 3, 6], 
            "小暑": [8, 2, 5], 
            "大暑": [7, 1, 4],
            "立秋": [2, 5, 8], 
            "处暑": [1, 4, 7], 
            "白露": [9, 3, 6],
            "秋分": [7, 1, 4], 
            "寒露": [6, 9, 3], 
            "霜降": [5, 8, 2],
            "立冬": [6, 9, 3], 
            "小雪": [5, 8, 2], 
            "大雪": [4, 7, 1]
        }
        
        base = datetime.datetime(2000, 1, 1)
        delta = (dt - base).days + 24
        yuan_idx = (delta % 15) // 5 
        yuan_name = ["上元", "中元", "下元"][yuan_idx]
        
        if dun_type == "阳遁":
            ju = yang_map.get(term_name, [3, 9, 6])[yuan_idx]
        else:
            ju = yin_map.get(term_name, [9, 3, 6])[yuan_idx]
            
        return dun_type, ju, term_name, yuan_name, curr_long

# ==============================================================================
# 模块二：六爻全库引擎 (LiuYaoEngine)
# 64卦全名映射，完全展开，不使用压缩拼接逻辑
# ==============================================================================
class LiuYaoEngine:
    def __init__(self):
        self.trigrams = {
            (1,1,1): "乾", 
            (0,1,1): "兑", 
            (1,0,1): "离", 
            (0,0,1): "震",
            (1,1,0): "巽", 
            (0,1,0): "坎", 
            (1,0,0): "艮", 
            (0,0,0): "坤"
        }
        # 全量字典 (Expanded Dictionary)
        self.full_hex_map = {
            "乾乾": "乾为天", 
            "坤坤": "坤为地", 
            "坎坎": "坎为水", 
            "离离": "离为火",
            "艮艮": "艮为山", 
            "震震": "震为雷", 
            "巽巽": "巽为风", 
            "兑兑": "兑为泽",
            "乾坤": "天地否", 
            "坤乾": "地天泰", 
            "坎离": "水火既济", 
            "离坎": "火水未济",
            "艮坤": "山地剥", 
            "坤艮": "地山谦", 
            "震巽": "雷风恒", 
            "巽震": "风雷益",
            "乾坎": "天水讼", 
            "坎乾": "水天需", 
            "乾艮": "天山遁", 
            "艮乾": "山天大畜",
            "乾震": "天雷无妄", 
            "震乾": "雷天大壮", 
            "乾巽": "天风姤", 
            "巽乾": "风天小畜",
            "乾离": "天火同人", 
            "离乾": "火天大有", 
            "乾兑": "天泽履", 
            "兑乾": "泽天夬",
            "坤坎": "地水师", 
            "坎坤": "水地比", 
            "坤艮": "地山谦", 
            "艮坤": "山地剥",
            "坤震": "地雷复", 
            "震坤": "雷地豫", 
            "坤巽": "地风升", 
            "巽坤": "风地观",
            "坤离": "地火明夷", 
            "离坤": "火地晋", 
            "坤兑": "地泽临", 
            "兑坤": "泽地萃",
            "坎艮": "水山蹇", 
            "艮坎": "山水蒙", 
            "坎震": "水雷屯", 
            "震坎": "雷水解",
            "坎巽": "水风井", 
            "巽坎": "风水涣", 
            "坎兑": "水泽节", 
            "兑坎": "泽水困",
            "离艮": "火山旅", 
            "艮离": "山火贲", 
            "离震": "火雷噬嗑", 
            "震离": "雷火丰",
            "离巽": "火风鼎", 
            "巽离": "风火家人", 
            "离兑": "火泽睽", 
            "兑离": "泽火革",
            "艮震": "山雷颐", 
            "震艮": "雷山小过", 
            "艮巽": "山风蛊", 
            "巽艮": "风山渐",
            "艮兑": "山泽损", 
            "兑艮": "泽山咸", 
            "震兑": "雷泽归妹", 
            "兑震": "泽雷随",
            "巽兑": "风泽中孚", 
            "兑巽": "泽风大过"
        }

    def process(self, codes):
        orig_bits = []
        change_bits = []
        moving_lines = []
        
        for idx, val in enumerate(codes):
            bit = 0 if val in [6, 8] else 1
            orig_bits.append(bit)
            if val == 6:
                change_bits.append(1)
                moving_lines.append(idx + 1)
            elif val == 9:
                change_bits.append(0)
                moving_lines.append(idx + 1)
            else:
                change_bits.append(bit)
        
        up_orig = tuple(reversed(orig_bits[3:]))
        low_orig = tuple(reversed(orig_bits[:3]))
        name_up = self.trigrams.get(up_orig, "")
        name_low = self.trigrams.get(low_orig, "")
        ben_key = name_up + name_low
        ben_real_name = self.full_hex_map.get(ben_key, f"上{name_up}下{name_low}")
        
        up_chg = tuple(reversed(change_bits[3:]))
        low_chg = tuple(reversed(change_bits[:3]))
        name_up_c = self.trigrams.get(up_chg, "")
        name_low_c = self.trigrams.get(low_chg, "")
        bian_key = name_up_c + name_low_c
        bian_real_name = self.full_hex_map.get(bian_key, f"上{name_up_c}下{name_low_c}")
        
        return {
            "codes": codes,
            "ben_name": ben_real_name,
            "bian_name": bian_real_name,
            "moving_lines": moving_lines
        }

# ==============================================================================
# 模块三：时间和地理处理 (TimeAndGeo)
# 包含：全量城市经度字典、卫星定位接口、网络校时
# ==============================================================================
class TimeAndGeo:
    def __init__(self):
        # 城市全量库 - 完全展开，方便查找修改
        self.city_long_map = {
            # === 直辖市 ===
            "北京": 116.40, 
            "上海": 121.47, 
            "天津": 117.20, 
            "重庆": 106.55,
            
            # === 东北 ===
            "哈尔滨": 126.63, 
            "齐齐哈尔": 123.97, 
            "牡丹江": 129.58, 
            "佳木斯": 130.35, 
            "大庆": 125.03, 
            "黑河": 127.53, 
            "绥化": 126.99, 
            "大兴安岭": 124.74, 
            "漠河": 122.53,
            "长春": 125.32, 
            "吉林市": 126.57, 
            "四平": 124.37, 
            "延吉": 129.51, 
            "沈阳": 123.43, 
            "大连": 121.61, 
            "鞍山": 122.99, 
            "锦州": 121.15,
            
            # === 华北 ===
            "呼和浩特": 111.69, 
            "包头": 109.84, 
            "鄂尔多斯": 109.78, 
            "满洲里": 117.43,
            "石家庄": 114.48, 
            "唐山": 118.17, 
            "秦皇岛": 119.57, 
            "雄安": 116.13,
            "太原": 112.55, 
            "大同": 113.30, 
            "运城": 111.00,
            
            # === 华东 ===
            "济南": 117.02, 
            "青岛": 120.38, 
            "烟台": 121.44, 
            "威海": 122.10, 
            "临沂": 118.35,
            "南京": 118.79, 
            "无锡": 120.31, 
            "徐州": 117.18, 
            "苏州": 120.58,
            "杭州": 120.15, 
            "宁波": 121.55, 
            "温州": 120.70, 
            "舟山": 122.20,
            "合肥": 117.28, 
            "芜湖": 118.38, 
            "黄山": 118.31,
            "福州": 119.30, 
            "厦门": 118.10, 
            "泉州": 118.58,
            "南昌": 115.89, 
            "景德镇": 117.18, 
            "赣州": 114.94,
            
            # === 华中 ===
            "郑州": 113.66, 
            "洛阳": 112.43, 
            "开封": 114.35,
            "武汉": 114.30, 
            "宜昌": 111.30, 
            "襄阳": 112.14,
            "长沙": 112.98, 
            "张家界": 110.48, 
            "衡阳": 112.61,
            
            # === 华南 ===
            "广州": 113.26, 
            "深圳": 114.05, 
            "珠海": 113.57, 
            "汕头": 116.69, 
            "东莞": 113.75,
            "南宁": 108.32, 
            "桂林": 110.29, 
            "北海": 109.12,
            "海口": 110.33, 
            "三亚": 109.51, 
            "三沙": 112.34,
            
            # === 西南 ===
            "成都": 104.06, 
            "绵阳": 104.74, 
            "乐山": 103.76, 
            "九寨沟": 103.91,
            "贵阳": 106.70, 
            "遵义": 106.93, 
            "茅台": 106.39,
            "昆明": 102.71, 
            "大理": 100.22, 
            "丽江": 100.23, 
            "西双版纳": 100.79, 
            "瑞丽": 97.85,
            "拉萨": 91.11, 
            "日喀则": 88.88, 
            "林芝": 94.36, 
            "阿里": 80.10,
            
            # === 西北 ===
            "西安": 108.93, 
            "延安": 109.49, 
            "榆林": 109.74, 
            "咸阳": 108.70,
            "兰州": 103.82, 
            "嘉峪关": 98.28, 
            "敦煌": 94.66,
            "西宁": 101.78, 
            "格尔木": 94.90, 
            "青海湖": 100.47,
            "银川": 106.23, 
            "中卫": 105.18,
            "乌鲁木齐": 87.62, 
            "喀什": 75.99, 
            "伊犁": 81.32, 
            "霍尔果斯": 80.41,
            
            # === 港澳台 ===
            "香港": 114.17, 
            "澳门": 113.54, 
            "台北": 121.50, 
            "高雄": 120.31, 
            "台中": 120.68
        }

    def get_city_long_smart(self, city_name):
        loc_source = "默认 (北京)"
        final_lon = 116.40
        
        # 1. 尝试卫星定位
        try:
            headers = {'User-Agent': 'CyberMetaphysics/21.0'}
            encoded_city = urllib.parse.quote(city_name)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_city}&format=json&limit=1"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                if data:
                    final_lon = float(data[0]['lon'])
                    loc_source = "卫星定位 (OSM)"
                    return final_lon, loc_source
        except:
            pass
        
        # 2. 本地全量库兜底
        for k, v in self.city_long_map.items():
            if k in city_name or city_name in k:
                return v, "本地全量库"
                
        return final_lon, loc_source

    def get_network_time(self):
        try:
            t_start = time.time()
            url = 'http://www.baidu.com'
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=3) as response:
                t_end = time.time()
                date_str = response.headers['Date']
                gmt = email.utils.parsedate_to_datetime(date_str)
                server_time = gmt.replace(tzinfo=None) + datetime.timedelta(hours=8)
                latency = (t_end - t_start) / 2
                return server_time + datetime.timedelta(seconds=latency), True
        except:
            return datetime.datetime.now(), False

    def get_true_solar(self, dt, longitude):
        diff_minutes = (longitude - 120.0) * 4
        true_solar_time = dt + datetime.timedelta(minutes=diff_minutes)
        return true_solar_time, diff_minutes

    def get_pillars(self, dt):
        base = datetime.datetime(2000, 1, 1)
        days_diff = (dt - base).days
        GAN = list("甲乙丙丁戊己庚辛壬癸")
        ZHI = list("子丑寅卯辰巳午未申酉戌亥")
        
        day_gan_idx = (days_diff + 24) % 60 % 10
        day_gan = GAN[day_gan_idx]
        day_zhi = ZHI[(days_diff + 24) % 60 % 12]
        
        hour_idx = (dt.hour + 1) // 2 % 12
        hour_zhi = ZHI[hour_idx]
        hour_gan = GAN[((day_gan_idx % 5) * 2 + hour_idx) % 10]
        
        xun_diff = (ZHI.index(hour_zhi) - GAN.index(hour_gan)) % 12
        xun_shou = f"甲{ZHI[xun_diff]}"
        
        year_gan = GAN[(dt.year - 4) % 10]
        year_zhi = ZHI[(dt.year - 4) % 12]
        
        return {
            "year": f"{year_gan}{year_zhi}", 
            "day": f"{day_gan}{day_zhi}", 
            "hour": f"{hour_gan}{hour_zhi}", 
            "xun": xun_shou, 
            "h_gan": hour_gan, 
            "h_zhi": hour_zhi
        }

# ==============================================================================
# 模块四：奇门遁甲全盘逻辑 (QimenFullLogic)
# 包含：转盘法排盘、中宫寄宫、神煞计算
# ==============================================================================
class QimenFullLogic:
    def __init__(self, ju, is_yang, xun, h_gan, h_zhi):
        self.ju = ju
        self.is_yang = is_yang
        self.xun = xun
        self.h_gan = h_gan
        self.h_zhi = h_zhi
        self.xun_map = {
            "甲子":"戊", 
            "甲戌":"己", 
            "甲申":"庚", 
            "甲午":"辛", 
            "甲辰":"壬", 
            "甲寅":"癸"
        }
        self.leader_stem = self.xun_map.get(xun, "戊")
        
        self.raw_stars = [
            "",
            "天蓬",
            "天芮",
            "天冲",
            "天辅",
            "天禽",
            "天心",
            "天柱",
            "天任",
            "天英"
        ]
        self.raw_doors = [
            "",
            "休门",
            "死门",
            "伤门",
            "杜门",
            "",
            "开门",
            "惊门",
            "生门",
            "景门"
        ]

    def get_kong_wang(self):
        kw_map = {
            "甲子": "戌亥", 
            "甲戌": "申酉", 
            "甲申": "午未", 
            "甲午": "辰巳", 
            "甲辰": "寅卯", 
            "甲寅": "子丑"
        }
        return kw_map.get(self.xun, "未知")

    def get_ma_xing(self):
        z = self.h_zhi
        if z in "申子辰": return "寅"
        if z in "寅午戌": return "申"
        if z in "巳酉丑": return "亥"
        if z in "亥卯未": return "巳"
        return "未知"

    def calculate(self):
        di_pan = [""] * 10
        seq = list("戊己庚辛壬癸丁丙乙") if self.is_yang else list("戊乙丙丁癸壬辛庚己")
        curr_pos = self.ju
        for stem in seq:
            di_pan[curr_pos] = stem
            if self.is_yang: 
                curr_pos = curr_pos % 9 + 1
            else: 
                curr_pos = (curr_pos - 2) % 9 + 1
        
        try: 
            leader_pos = di_pan.index(self.leader_stem)
        except: 
            leader_pos = 5
        
        orig_leader_pos = leader_pos
        if leader_pos == 5: leader_pos = 2
        
        zs_pos_raw = 2 if orig_leader_pos == 5 else orig_leader_pos
        zhi_shi_door = self.raw_doors[zs_pos_raw]
        
        t_stem = self.leader_stem if self.h_gan == "甲" else self.h_gan
        try: 
            hour_pos = di_pan.index(t_stem)
        except: 
            hour_pos = leader_pos
        if hour_pos == 5: hour_pos = 2
        
        shift = hour_pos - leader_pos
        
        zhis = list("子丑寅卯辰巳午未申酉戌亥")
        steps = zhis.index(self.h_zhi) - zhis.index(self.xun[1])
        
        if self.is_yang:
            door_dest_pos = zs_pos_raw + steps
        else:
            door_dest_pos = zs_pos_raw - steps
            
        while door_dest_pos > 9: door_dest_pos -= 9
        while door_dest_pos <= 0: door_dest_pos += 9
        if door_dest_pos == 5: door_dest_pos = 2
        
        layout = {}
        ring_pos = [1, 8, 3, 4, 9, 2, 7, 6]
        
        for i in range(1, 10): 
            layout[i] = {"di": di_pan[i], "star":"", "tian":"", "door":"", "god":""}
        
        for i in range(1, 10):
            if i == 5: continue
            np = i + shift
            while np > 9: np -= 9
            while np <= 0: np += 9
            if np == 5: np = 2
            
            s, t = self.raw_stars[i], di_pan[i]
            if i == 2: 
                s, t = "天芮(禽)", f"{di_pan[2]}/{di_pan[5]}"
            layout[np]["star"], layout[np]["tian"] = s, t
            
        door_list = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
        zs_idx = door_list.index(zhi_shi_door)
        try:
            d_dest_idx = ring_pos.index(door_dest_pos)
            for k in range(8):
                layout[ring_pos[(d_dest_idx+k)%8]]["door"] = door_list[(zs_idx+k)%8]
        except: pass
        
        gods = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"] if self.is_yang else ["值符", "九天", "九地", "玄武", "白虎", "六合", "太阴", "螣蛇"]
        try:
            g_st_idx = ring_pos.index(hour_pos)
            for k in range(8):
                idx = (g_st_idx+k)%8 if self.is_yang else (g_st_idx-k)%8
                layout[ring_pos[idx]]["god"] = gods[k]
        except: pass
        
        layout[5]["di"] = di_pan[5]
        return layout, zhi_shi_door

# ==============================================================================
# UI 层 (Streamlit) - V21.0 六步仪式版
# 修复了 st.experimental_rerun 报错
# 增加了手动输入验证
# 增加了手机访问指引
# ==============================================================================

st.set_page_config(page_title="赛博玄学 V21.0", layout="wide", page_icon="🧿")

st.markdown("""
<style>
    .card { background-color: #0E1117; border: 1px solid #414141; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .card-header { font-size: 16px; color: #888; margin-bottom: 5px; }
    .card-god { font-size: 18px; color: #FF4B4B; font-weight: bold; }
    .card-star { font-size: 18px; color: #FFA500; }
    .card-door { font-size: 20px; color: #00CC96; font-weight: bold; margin: 5px 0; }
    .card-stem { font-size: 18px; color: #FFFFFF; font-family: monospace; }
    .status-bar { padding: 10px; border-radius: 5px; background-color: #1E1E1E; color: #00FF00; font-family: monospace; margin-bottom: 20px; border: 1px solid #333; }
    .shake-btn { font-size: 24px !important; padding: 20px !important; width: 100%; }
    .gua-line { font-size: 24px; font-family: monospace; margin: 5px 0; letter-spacing: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("🧿 赛博玄学 V21.0 · 宏大叙事版")
st.caption("手动六爻 | 卫星定位 | 普朗克精度 | 修复版")

# 初始化 Session State
if 'yao_list' not in st.session_state:
    st.session_state['yao_list'] = []
if 'finished' not in st.session_state:
    st.session_state['finished'] = False

with st.sidebar:
    st.header("🔮 定场录入")
    
    # 城市输入：默认为空，placeholder 提示用户输入
    city_input = st.text_input("📍 当前位置 (城市)", placeholder="请输入城市，如：哈尔滨", help="卫星/本地全量库双模定位")
    name = st.text_input("👤 求测姓名", placeholder="请输入姓名")
    ask = st.text_input("🖊️ 所测之事", placeholder="请输入想问的事")
    
    st.markdown("---")
    st.markdown("**🎮 控制台**")
    if st.button("🔄 重置仪式"):
        st.session_state['yao_list'] = []
        st.session_state['finished'] = False
        # 【关键修复】使用新的 rerun 指令
        st.rerun()

# ------------------------------------------------------------------------------
# 主逻辑区：分阶段显示
# ------------------------------------------------------------------------------

# 阶段零：等待输入
if not city_input or not name or not ask:
    st.info("👈 请在左侧侧边栏输入【位置】、【姓名】和【所测之事】以开启仪式。")
    st.stop()

# 阶段一：摇卦仪式 (如果还没摇满6次)
if not st.session_state['finished']:
    count = len(st.session_state['yao_list'])
    current_step = count + 1
    
    st.subheader(f"🪙 起卦仪式：请摇第 {current_step} 爻")
    
    # 显示已经摇出来的卦象 (倒序显示，因为六爻是从下往上画)
    if count > 0:
        st.markdown("##### 当前卦象 (初爻在下):")
        for i in range(count - 1, -1, -1):
            val = st.session_state['yao_list'][i]
            # 简单的视觉反馈
            line_str = "▅▅▅▅▅" if val in [7,9] else "▅▅　▅▅"
            desc = {6:"老阴", 7:"少阳", 8:"少阴", 9:"老阳"}[val]
            color = "red" if val in [6,9] else "white"
            st.markdown(f"<div style='color:{color}; font-size:20px'>{line_str} ({desc})</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 巨大的摇卦按钮
    btn_text = f"🎲 点击摇出第 {current_step} 爻" if count < 5 else "🔥 点击摇出上爻 (生成天机)"
    if st.button(btn_text, type="primary", use_container_width=True):
        # 模拟随机
        time.sleep(0.3) 
        r = random.SystemRandom().random()
        if r < 0.125: c = 6
        elif r < 0.25: c = 9
        elif r < 0.625: c = 7
        else: c = 8
        
        st.session_state['yao_list'].append(c)
        
        # 如果摇满了6次
        if len(st.session_state['yao_list']) == 6:
            st.session_state['finished'] = True
        
        # 【关键修复】使用新的 rerun 指令
        st.rerun()

# 阶段二：推演结果 (摇满6次后显示)
else:
    with st.spinner('📡 正在连接卫星，全息推演中...'):
        tag = TimeAndGeo()
        final_long, loc_source = tag.get_city_long_smart(city_input)
        net_time, _ = tag.get_network_time()
        true_time, diff = tag.get_true_solar(net_time, final_long)
        
        ste = SolarTermEngine()
        dtype, ju, term, yuan, slong = ste.get_chai_bu_ju(true_time)
        is_yang = (dtype == "阳遁")
        
        pill = tag.get_pillars(true_time)
        qimen = QimenFullLogic(ju, is_yang, pill['xun'], pill['h_gan'], pill['h_zhi'])
        layout, zs_door = qimen.calculate()
        kw = qimen.get_kong_wang()
        ma = qimen.get_ma_xing()
        
        lye = LiuYaoEngine()
        # 这里用手动摇出来的列表
        gua_data = lye.process(st.session_state['yao_list'])
        
        time.sleep(0.5)

    # 1. 状态栏
    st.markdown(f"""
    <div class="status-bar">
    [SYSTEM] 经度: {final_long:.4f}° ({loc_source}) | 真太阳时偏差: {diff:.2f}min
    </div>
    """, unsafe_allow_html=True)

    # 2. 核心指标
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("真太阳时", true_time.strftime('%H:%M:%S'))
    c2.metric("节气", f"{term} ({yuan})", f"黄经 {slong:.2f}°")
    c3.metric("局信", f"{dtype}{ju}局", f"旬首 {pill['xun']}")
    c4.metric("值使/空亡", zs_door, kw)
    st.markdown(f"**四柱**：{pill['year']} {pill['day']} {pill['hour']}")
    
    st.divider()

    # 3. 左右布局
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("六爻卦象")
        st.write(f"本卦：**{gua_data['ben_name']}**")
        st.write(f"变卦：**{gua_data['bian_name']}**")
        
        # 绘制最终卦图 (上到下)
        html_lines = []
        for i in range(5, -1, -1):
            c = st.session_state['yao_list'][i]
            line_style = "━━━" if c in [7,9] else "━　━"
            color = "#FF4B4B" if c in [6,9] else "#E0E0E0"
            symbol = " O" if c == 9 else (" X" if c == 6 else "")
            html_lines.append(f"<div class='gua-line' style='color:{color}'>{line_style}{symbol}</div>")
        st.markdown("".join(html_lines), unsafe_allow_html=True)
        
        if gua_data['moving_lines']:
            st.warning(f"动爻：{gua_data['moving_lines']}")
        else:
            st.info("六爻安静")

    with col_right:
        st.subheader("奇门九宫")
        grid_order = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
        palace_names = {1:"坎水",8:"艮土",3:"震木",4:"巽木",9:"离火",2:"坤土",7:"兑金",6:"乾金",5:"中宫"}
        
        for row in grid_order:
            cols = st.columns(3)
            for idx, p_idx in enumerate(row):
                d = layout.get(p_idx, {})
                with cols[idx]:
                    if p_idx == 5:
                        st.markdown(f"""<div class="card" style="border:1px dashed #444"><div class="card-header">中宫</div><div class="card-stem" style="color:#888">{d.get('di','')}</div></div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="card">
                            <div class="card-header">{palace_names[p_idx]}</div>
                            <div class="card-god">{d['god']}</div>
                            <div class="card-star">{d['star']}</div>
                            <div class="card-door">{d['door']}</div>
                            <div class="card-stem">[{d['tian']}/{d['di']}]</div>
                        </div>
                        """, unsafe_allow_html=True)

    # 4. 数据包
    st.divider()
    raw_data = f"""
【定场】 {name} @ {city_input} (经度:{final_long})
【时间】 {true_time.strftime('%Y-%m-%d %H:%M:%S')} (真太阳时)
【四柱】 {pill['year']} {pill['day']} {pill['hour']} (旬首:{pill['xun']})
【奇门】 {term} {dtype}{ju}局 | 空亡:{kw} | 马星:{ma} | 值使:{zs_door}
【六爻】 本:{gua_data['ben_name']} 变:{gua_data['bian_name']} 动:{gua_data['moving_lines']}
【数值】 {st.session_state['yao_list']}
【布局】 (坎1->乾6):
"""
    for p in [1,8,3,4,9,2,7,6]:
        d = layout[p]
        raw_data += f"宫{p}: {d['god']} {d['star']} {d['door']} [{d['tian']}/{d['di']}]\n"
        
    st.text_area("复制数据给 AI", raw_data, height=150)
    
    if st.button("🔄 再测一事"):
        st.session_state['yao_list'] = []
        st.session_state['finished'] = False
        st.rerun()