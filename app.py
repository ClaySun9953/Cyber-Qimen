import streamlit as st
import streamlit.components.v1 as components
import time
import datetime
import random
import urllib.request
import urllib.parse
import json
import email.utils
import math

# ==============================================================================
# UI 层 (Streamlit) - V29.1 最终优化版
# 1. 引入 st.form 解决输入不生效的问题
# 2. 注入 JS 补丁修复安卓兼容性
# 3. 代码完全解压，单行单写
# 4. 修复奇门遁甲核心逻辑 BUG
# 5. 优化「复制数据给 AI」文本输出格式
# 6. 新增【空间面向】选择
# 7. 新增【五行用事提示】
# 8. 强化【断卦指导】
# ==============================================================================
st.set_page_config(page_title="赛博玄学 V29.1", layout="wide", page_icon="🧿")

# 注入安卓兼容补丁
components.html("""
<script>
    if (!window.structuredClone) {
        window.structuredClone = function(obj) {
            return JSON.parse(JSON.stringify(obj));
        };
    }
</script>
""", height=0, width=0)

st.markdown("""
<style>
    .card { 
        background-color: #0E1117 !important; 
        border: 1px solid #414141 !important; 
        border-radius: 10px; 
        padding: 15px; 
        text-align: center; 
        margin-bottom: 10px; 
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .card-header { font-size: 16px; color: #CCCCCC !important; margin-bottom: 5px; }
    .card-god { font-size: 18px; color: #FF4B4B; font-weight: bold; }
    .card-star { font-size: 18px; color: #FFA500; }
    .card-door { font-size: 20px; color: #00CC96; font-weight: bold; margin: 5px 0; }
    .card-stem { font-size: 18px; color: #FFFFFF !important; font-family: monospace; }
    .mobile-hint {
        background-color: #FF4B4B;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
        border: 2px solid #fff;
    }
    .status-bar { 
        padding: 10px; 
        border-radius: 5px; 
        background-color: #1E1E1E; 
        color: #00FF00; 
        font-family: monospace; 
        margin-bottom: 20px; 
        border: 1px solid #333;
    }
    .shake-btn { font-size: 24px !important; padding: 20px !important; width: 100%; }
    .gua-line { 
        font-size: 24px; 
        font-family: 'Courier New', monospace; 
        font-weight: bold;
        margin: 5px 0; 
        letter-spacing: 2px; 
    }
</style>
""", unsafe_allow_html=True)

st.title("🧿 赛博玄学 V29.1 (最终优化版)")

# ==============================================================================
# 模块一：普朗克级天文算法引擎
# ==============================================================================
class SolarTermEngine:
    def __init__(self):
        self.term_names = [
            "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", 
            "清明", "谷雨", "立夏", "小满", "芒种", "夏至", 
            "小暑", "大暑", "立秋", "处暑", "白露", "秋分", 
            "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"
        ]
        # 节气对应五行/时空特征模板
        self.term_features = {
            "小寒": "水旺之时，宜静不宜动，利于谋划",
            "大寒": "水极转木，寒极生温，宜守正待时",
            "立春": "木气初升，万物复苏，宜动中求进",
            "雨水": "木火相生，雨露均沾，宜顺势而为",
            "惊蛰": "雷动木旺，万物惊醒，宜主动出击",
            "春分": "木气鼎盛，阴阳平衡，宜稳中求进",
            "清明": "木火通明，气清景明，宜积极作为",
            "谷雨": "土旺金相，雨生百谷，宜厚积薄发",
            "立夏": "火气初升，万物繁茂，宜开拓进取",
            "小满": "火土相生，小得盈满，宜稳步前行",
            "芒种": "火旺至极，忙碌充实，宜把握时机",
            "夏至": "阳极生阴，火气转土，宜静守心神",
            "小暑": "土旺金相，暑气初升，宜劳逸结合",
            "大暑": "土极转金，暑极生凉，宜以静制动",
            "立秋": "金气初升，万物收敛，宜审时度势",
            "处暑": "金水相生，暑气消退，宜收心养性",
            "白露": "金气鼎盛，露凝而白，宜果断行事",
            "秋分": "金气转水，阴阳平衡，宜权衡利弊",
            "寒露": "水旺金相，露寒而冷，宜谨慎前行",
            "霜降": "水极转木，霜降水涸，宜坚守本心",
            "立冬": "水气初升，万物闭藏，宜休养生息",
            "小雪": "水旺木相，雪落无声，宜默默积累",
            "大雪": "水旺至极，雪盛冰封，宜厚积薄发",
            "冬至": "阴极生阳，水极转火，宜静待转机"
        }
        # 五行用事提示（基于节气+阴阳遁）
        self.wuxing_hints = {
            "小寒": "水旺克火，宜补水抑火",
            "大寒": "水旺木相，宜水木相生",
            "立春": "木旺克土，宜补木疏土",
            "雨水": "木火相生，宜动中求进",
            "惊蛰": "雷动木旺，宜木火通明",
            "春分": "木气鼎盛，宜阴阳平衡",
            "清明": "木火通明，宜积极作为",
            "谷雨": "土旺金相，宜厚积薄发",
            "立夏": "火旺克金，宜补火抑金",
            "小满": "火土相生，宜稳步前行",
            "芒种": "火旺至极，宜把握时机",
            "夏至": "阳极生阴，宜以静制动",
            "小暑": "土旺克水，宜补土抑水",
            "大暑": "土极转金，宜劳逸结合",
            "立秋": "金旺克木，宜补金抑木",
            "处暑": "金水相生，宜收心养性",
            "白露": "金气鼎盛，宜果断行事",
            "秋分": "金气转水，宜权衡利弊",
            "寒露": "水旺金相，宜谨慎前行",
            "霜降": "水极转木，宜坚守本心",
            "立冬": "水旺克火，宜补水抑火",
            "小雪": "水旺木相，宜默默积累",
            "大雪": "水旺至极，宜厚积薄发",
            "冬至": "阴极生阳，宜静待转机"
        }
        
    def _julian_day(self, year, month, day, hour=12, minute=0, second=0, micro=0):
        if month <= 2:
            month = month + 12
            year = year - 1
        
        B = 2 - year // 100 + year // 400
        
        day_fraction = (hour + minute / 60.0 + second / 3600.0 + micro / 3600000000.0) / 24.0
        dd = day + day_fraction
        
        JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + dd + B - 1524.5
        return JD

    def _calc_solar_long(self, jd):
        T = (jd - 2451545.0) / 36525.0
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
        
        term1 = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(math.radians(M))
        term2 = (0.019993 - 0.000101 * T) * math.sin(math.radians(2 * M))
        term3 = 0.000289 * math.sin(math.radians(3 * M))
        
        C = term1 + term2 + term3
        return (L0 + C) % 360

    def get_chai_bu_ju(self, dt, time_geo):
        jd = self._julian_day(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
        curr_long = self._calc_solar_long(jd)
        
        corrected_long = (curr_long - 285) 
        if corrected_long < 0:
            corrected_long += 360
            
        term_idx = int(corrected_long // 15)
        term_name = self.term_names[term_idx]
        
        dun_type = "阳遁"
        if 11 <= term_idx <= 22:
            dun_type = "阴遁"
            
        yang_map = {"冬至": [1, 7, 4], "小寒": [2, 8, 5], "大寒": [3, 9, 6], "立春": [8, 5, 2], "雨水": [9, 6, 3], "惊蛰": [1, 7, 4], "春分": [3, 9, 6], "清明": [4, 1, 7], "谷雨": [5, 2, 8], "立夏": [4, 1, 7], "小满": [5, 2, 8], "芒种": [6, 3, 9]}
        yin_map = {"夏至": [9, 3, 6], "小暑": [8, 2, 5], "大暑": [7, 1, 4], "立秋": [2, 5, 8], "处暑": [1, 4, 7], "白露": [9, 3, 6], "秋分": [7, 1, 4], "寒露": [6, 9, 3], "霜降": [5, 8, 2], "立冬": [6, 9, 3], "小雪": [5, 8, 2], "大雪": [4, 7, 1]}
        
        yuan_idx = time_geo.get_yuan_idx(dt)
        yuan_name = ["上元", "中元", "下元"][yuan_idx]
        
        if dun_type == "阳遁":
            ju = yang_map.get(term_name, [3, 9, 6])[yuan_idx]
        else:
            ju = yin_map.get(term_name, [9, 3, 6])[yuan_idx]
            
        # 获取时空特征和五行提示
        feature = self.term_features.get(term_name, "五行流转，宜顺势而为")
        wuxing_hint = self.wuxing_hints.get(term_name, "五行平衡，宜守正待时")
            
        return dun_type, ju, term_name, yuan_name, curr_long, feature, wuxing_hint

# ==============================================================================
# 模块二：六爻全库引擎 (完全解压，防止报错)
# ==============================================================================
class LiuYaoEngine:
    def __init__(self):
        self.trigrams = {
            (1,1,1): "乾", (0,1,1): "兑", (1,0,1): "离", (0,0,1): "震",
            (1,1,0): "巽", (0,1,0): "坎", (1,0,0): "艮", (0,0,0): "坤"
        }
        self.full_hex_map = {
            "乾乾":"乾为天", "坤坤":"坤为地", "坎坎":"坎为水", "离离":"离为火", 
            "艮艮":"艮为山", "震震":"震为雷", "巽巽":"巽为风", "兑兑":"兑为泽",
            "乾坤":"天地否", "坤乾":"地天泰", "坎离":"水火既济", "离坎":"火水未济", 
            "艮坤":"山地剥", "坤艮":"地山谦", "震巽":"雷风恒", "巽震":"风雷益",
            "乾坎":"天水讼", "坎乾":"水天需", "乾艮":"天山遁", "艮乾":"山天大畜", 
            "乾震":"天雷无妄", "震乾":"雷天大壮", "乾巽":"天风姤", "巽乾":"风天小畜",
            "乾离":"天火同人", "离乾":"火天大有", "乾兑":"天泽履", "兑乾":"泽天夬", 
            "坤坎":"地水师", "坎坤":"水地比", "坤艮":"地山谦", "艮坤":"山地剥",
            "坤震":"地雷复", "震坤":"雷地豫", "坤巽":"地风升", "巽坤":"风地观", 
            "坤离":"地火明夷", "离坤":"火地晋", "坤兑":"地泽临", "兑坤":"泽地萃",
            "坎艮":"水山蹇", "艮坎":"山水蒙", "坎震":"水雷屯", "震坎":"雷水解", 
            "坎巽":"水风井", "巽坎":"风水涣", "坎兑":"水泽节", "兑坎":"泽水困",
            "离艮":"火山旅", "艮离":"山火贲", "离震":"火雷噬嗑", "震离":"雷火丰", 
            "离巽":"火风鼎", "巽离":"风火家人", "离兑":"火泽睽", "兑离":"泽火革",
            "艮震":"山雷颐", "震艮":"雷山小过", "艮巽":"山风蛊", "巽艮":"风山渐", 
            "艮兑":"山泽损", "兑艮":"泽山咸", "震兑":"雷泽归妹", "兑震":"泽雷随",
            "巽兑":"风泽中孚", "兑巽":"泽风大过"
        }

    def process(self, codes):
        orig_bits = []
        change_bits = []
        moving_lines = []
        
        for idx, val in enumerate(codes):
            bit = 0
            if val in [6, 8]:
                bit = 0
            else:
                bit = 1
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

    def get_gua_text(self, data):
        lines_text = "--------------------------------------------------\n"
        for i in range(5, -1, -1):
            val = data['codes'][i]
            line_char = "-------" if val in [7,9] else "-     -"
            change_note = ""
            if val == 6:
                change_note = " [X]老阴"
            elif val == 9:
                change_note = " [O]老阳"
            elif val == 7:
                change_note = " (7)"
            elif val == 8:
                change_note = " (8)"
            lines_text += f"  第{i+1}爻: {line_char} {change_note}\n"
        lines_text += "--------------------------------------------------"
        return lines_text

# ==============================================================================
# 模块三：时间和地理处理 (修复真太阳时归一化 + 新增拆补法三元判断)
# ==============================================================================
class TimeAndGeo:
    def __init__(self):
        self.city_long_map = {
            "北京": 116.40, "上海": 121.47, "天津": 117.20, "重庆": 106.55,
            "哈尔滨": 126.63, "齐齐哈尔": 123.97, "牡丹江": 129.58, "大庆": 125.03, 
            "漠河": 122.53, "长春": 125.32, "吉林市": 126.57, "延吉": 129.51,
            "沈阳": 123.43, "大连": 121.61, "丹东": 124.37,
            "呼和浩特": 111.69, "包头": 109.84, "石家庄": 114.48, "唐山": 118.17, 
            "秦皇岛": 119.57, "太原": 112.55, "大同": 113.30, "济南": 117.02, 
            "青岛": 120.38, "烟台": 121.44, "南京": 118.79, "苏州": 120.58, 
            "无锡": 120.31, "徐州": 117.18, "杭州": 120.15, "宁波": 121.55, 
            "温州": 120.70, "合肥": 117.28, "福州": 119.30, "厦门": 118.10,
            "南昌": 115.89, "郑州": 113.66, "洛阳": 112.43, "武汉": 114.30,
            "长沙": 112.98, "广州": 113.26, "深圳": 114.05, "珠海": 113.57,
            "海口": 110.33, "三亚": 109.51, "成都": 104.06, "贵阳": 106.70,
            "昆明": 102.71, "拉萨": 91.11, "西安": 108.93, "兰州": 103.82,
            "西宁": 101.78, "银川": 106.23, "乌鲁木齐": 87.62, "香港": 114.17, 
            "澳门": 113.54, "台北": 121.50, "高雄": 120.31
        }

    def get_yuan_idx(self, dt):
        pillars = self.get_pillars(dt)
        day_gan_zhi = pillars['day']
        current_gan = day_gan_zhi[0]
        offset = 0

        while current_gan not in ['甲', '己'] and offset < 10:
            offset += 1
            past_dt = dt - datetime.timedelta(days=offset)
            pillars = self.get_pillars(past_dt)
            day_gan_zhi = pillars['day']
            current_gan = day_gan_zhi[0]

        if offset >= 10:
            return 0

        zhi = day_gan_zhi[1]
        if zhi in '子午卯酉':
            return 0
        elif zhi in '寅申巳亥':
            return 1
        elif zhi in '辰戌丑未':
            return 2
        return 0

    def get_city_long_smart(self, city_name):
        loc_source = "默认 (北京)"
        final_lon = 116.40
        try:
            headers = {'User-Agent': 'CyberMetaphysics/29.0'}
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

    def calculate_eot(self, dt):
        day_of_year = dt.timetuple().tm_yday
        B = math.radians((day_of_year - 81) * 360 / 365)
        eot_minutes = 9.87 * math.sin(2*B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
        return eot_minutes

    def get_true_solar(self, dt, longitude):
        mean_diff = (longitude - 120.0) * 4
        eot_diff = self.calculate_eot(dt)
        total_diff = mean_diff + eot_diff
        true_solar_time = dt + datetime.timedelta(minutes=total_diff)
        
        true_solar_time = true_solar_time.replace(tzinfo=None)
        if true_solar_time.hour < 0 or true_solar_time.hour >= 24:
            day_offset = true_solar_time.hour // 24
            true_solar_time = true_solar_time - datetime.timedelta(days=day_offset)
            true_solar_time = true_solar_time.replace(hour=true_solar_time.hour % 24)
        
        return true_solar_time, mean_diff, eot_diff

    def get_pillars(self, dt):
        base = datetime.datetime(2000, 1, 1)
        days_diff = (dt - base).days
        GAN = list("甲乙丙丁戊己庚辛壬癸")
        ZHI = list("子丑寅卯辰巳午未申酉戌亥")
        day_gan = GAN[(days_diff + 24) % 60 % 10]
        day_zhi = ZHI[(days_diff + 24) % 60 % 12]
        hour_idx = (dt.hour + 1) // 2 % 12
        hour_zhi = ZHI[hour_idx]
        hour_gan_idx = ((GAN.index(day_gan) % 5) * 2 + hour_idx) % 10
        hour_gan = GAN[hour_gan_idx]
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
# 模块四：奇门遁甲全盘逻辑 (修复核心 BUG：八门索引、中宫处理、值使门)
# ==============================================================================
class QimenFullLogic:
    def __init__(self, ju, is_yang, xun, h_gan, h_zhi):
        self.ju = ju
        self.is_yang = is_yang
        self.xun = xun
        self.h_gan = h_gan
        self.h_zhi = h_zhi
        
        self.xun_map = {
            "甲子":"戊", "甲戌":"己", "甲申":"庚", "甲午":"辛", 
            "甲辰":"壬", "甲寅":"癸"
        }
        self.leader_stem = self.xun_map.get(xun, "戊")
        
        self.raw_stars = ["","天蓬","天芮","天冲","天辅","天禽","天心","天柱","天任","天英"]
        self.raw_doors = ["","休门","生门","伤门","杜门","景门","死门","惊门","开门",""]

    def get_kong_wang(self):
        kw_map = {
            "甲子":"戌亥", "甲戌":"申酉", "甲申":"午未", 
            "甲午":"辰巳", "甲辰":"寅卯", "甲寅":"子丑"
        }
        return kw_map.get(self.xun,"未知")

    def get_ma_xing(self):
        z = self.h_zhi
        if z in "申子辰": return "寅"
        if z in "寅午戌": return "申"
        if z in "巳酉丑": return "亥"
        if z in "亥卯未": return "巳"
        return ""

    def calculate(self):
        di_pan = [""] * 10
        seq = list("戊己庚辛壬癸丁丙乙") if self.is_yang else list("戊乙丙丁癸壬辛庚己")
        curr = self.ju
        for s in seq:
            di_pan[curr] = s
            if self.is_yang:
                curr = curr % 9 + 1
            else:
                curr = (curr - 2) % 9 + 1
            
        try:
            l_pos = di_pan.index(self.leader_stem)
        except:
            l_pos = 5
            
        real_l_pos = l_pos
        if l_pos == 5:
            l_pos = 2
        
        zs_pos_raw = real_l_pos
        if zs_pos_raw == 5:
            zs_pos_raw = 2
        if zs_pos_raw < 1 or zs_pos_raw >= len(self.raw_doors):
            zhi_shi_door = "未知"
        else:
            zhi_shi_door = self.raw_doors[zs_pos_raw]
        
        ring_order = [1, 8, 3, 4, 9, 2, 7, 6]
        
        t_stem = self.leader_stem if self.h_gan == "甲" else self.h_gan
        try:
            h_pos = di_pan.index(t_stem)
        except:
            h_pos = l_pos
        if h_pos == 5: h_pos = 2
        
        try:
            start_idx = ring_order.index(l_pos)
            end_idx = ring_order.index(h_pos)
            shift = end_idx - start_idx
        except:
            shift = 0
            
        layout = {}
        for i in range(1, 10):
            layout[i] = {"di": di_pan[i], "star":"", "tian":"", "door":"", "god":""}
            
        for original_pos in range(1, 10):
            if original_pos == 5: continue
            
            star_name = self.raw_stars[original_pos]
            stem_name = di_pan[original_pos]
            
            if original_pos == 2:
                star_name = "天芮"
                stem_name = f"{di_pan[2]}"
            
            try:
                curr_ring_idx = ring_order.index(original_pos)
                new_ring_idx = (curr_ring_idx + shift) % 8
                new_pos = ring_order[new_ring_idx]
                
                layout[new_pos]["star"] = star_name
                layout[new_pos]["tian"] = stem_name
            except:
                pass

        zhis = list("子丑寅卯辰巳午未申酉戌亥")
        steps = zhis.index(self.h_zhi) - zhis.index(self.xun[1])
        
        if self.is_yang:
            door_dest_pos = zs_pos_raw + steps
        else:
            door_dest_pos = zs_pos_raw - steps
            
        while door_dest_pos > 9: door_dest_pos -= 9
        while door_dest_pos <= 0: door_dest_pos += 9
        if door_dest_pos == 5: door_dest_pos = 2
        
        door_sequence = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
        
        try:
            zs_seq_idx = door_sequence.index(zhi_shi_door)
            dest_ring_idx = ring_order.index(door_dest_pos)
            
            for k in range(8):
                door_name = door_sequence[(zs_seq_idx + k) % 8]
                palace_idx = ring_order[(dest_ring_idx + k) % 8]
                layout[palace_idx]["door"] = door_name
        except:
            pass

        gods_yang = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
        gods_yin = ["值符", "九天", "九地", "玄武", "白虎", "六合", "太阴", "螣蛇"]
        gods = gods_yang if self.is_yang else gods_yin
        
        try:
            god_start_idx = ring_order.index(h_pos)
            for k in range(8):
                if self.is_yang:
                    p_idx = ring_order[(god_start_idx + k) % 8]
                else:
                    p_idx = ring_order[(god_start_idx - k) % 8]
                
                layout[p_idx]["god"] = gods[k]
        except:
            pass
        
        layout[5]["di"] = di_pan[5]
        layout[5]["star"] = "天禽"
        layout[5]["god"] = layout[2]["god"] if 2 in layout else ""
        layout[5]["door"] = layout[2]["door"] if 2 in layout else ""
        
        return layout, zhi_shi_door

# ==============================================================================
# UI 主逻辑
# ==============================================================================

if 'yao_list' not in st.session_state:
    st.session_state['yao_list'] = []
if 'finished' not in st.session_state:
    st.session_state['finished'] = False
if 'ceremony_started' not in st.session_state:
    st.session_state['ceremony_started'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}

with st.sidebar:
    st.header("🔮 定场录入")
    
    with st.form("entry_form"):
        city_input = st.text_input("📍 当前位置 (城市)", placeholder="请输入城市，如：哈尔滨", help="卫星/本地全量库双模定位")
        name = st.text_input("👤 求测姓名", placeholder="请输入姓名")
        ask = st.text_input("🖊️ 所测之事", placeholder="请输入想问的事")
        # 【新增】方向选择
        direction = st.selectbox("面向方向（可选，用于奇门用神参考）", ["未知", "北", "东北", "东", "东南", "南", "西南", "西", "西北"])
        
        st.markdown("---")
        
        submitted = st.form_submit_button("🔵 开启排盘仪式", type="primary")
        
        if submitted:
            if city_input and name and ask:
                st.session_state['ceremony_started'] = True
                st.session_state['yao_list'] = []
                st.session_state['finished'] = False
                # 保存数据（包含方向）
                st.session_state['user_info'] = {
                    "city": city_input,
                    "name": name,
                    "ask": ask,
                    "direction": direction
                }
                st.rerun()
            else:
                st.error("请先完善信息")
            
    st.markdown("---")
    if st.button("🔄 重置所有"):
        st.session_state['yao_list'] = []
        st.session_state['finished'] = False
        st.session_state['ceremony_started'] = False
        st.session_state['user_info'] = {}
        st.rerun()

if not st.session_state['ceremony_started']:
    st.markdown("""
    <div class="mobile-hint">
        📱 手机/平板用户请注意！<br>
        请点击屏幕左上角的 <b>></b> 箭头打开侧边栏输入信息
    </div>
    """, unsafe_allow_html=True)
    st.info("👈 电脑用户请在左侧侧边栏输入【位置】、【姓名】和【所测之事】以开启仪式。每点击一次重复一遍问题")
    st.stop()

if not st.session_state['finished']:
    count = len(st.session_state['yao_list'])
    
    if count < 6:
        current_step = count + 1
        st.subheader(f"🪙 起卦仪式：请摇第 {current_step} 爻")
    else:
        st.subheader("✅ 六爻已成，等待揭晓")
    
    if count > 0:
        st.markdown("##### 当前卦象 (初爻在下):")
        for i in range(count - 1, -1, -1):
            val = st.session_state['yao_list'][i]
            line_str = "▅▅▅▅▅" if val in [7,9] else "▅▅　▅▅"
            desc = {6:"老阴", 7:"少阳", 8:"少阴", 9:"老阳"}[val]
            if val in [6, 9]:
                color = "#FF0000"
            else:
                color = "#000000"
            st.markdown(f"<div class='gua-line' style='color:{color}'>{line_str} ({desc})</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    if count < 6:
        btn_text = f"🎲 点击摇出第 {current_step} 爻" if count < 5 else "🔥 点击摇出上爻 (最后一步)"
        if st.button(btn_text, type="primary", use_container_width=True):
            time.sleep(0.3) 
            r = random.SystemRandom().random()
            if r < 0.125:
                c = 6
            elif r < 0.25:
                c = 9
            elif r < 0.625:
                c = 7
            else:
                c = 8
            st.session_state['yao_list'].append(c)
            st.rerun()
    else:
        st.success("六爻已定！请保持心诚，点击下方按钮进行天地排盘。")
        if st.button("🔮 揭开天机 (生成全盘)", type="primary", use_container_width=True):
            st.session_state['finished'] = True
            st.rerun()

else:
    with st.spinner('📡 正在连接卫星，修正真太阳时...'):
        info = st.session_state['user_info']
        
        tag = TimeAndGeo()
        final_long, loc_source = tag.get_city_long_smart(info['city'])
        net_time, _ = tag.get_network_time()
        
        true_time, mean_diff, eot_diff = tag.get_true_solar(net_time, final_long)
        
        ste = SolarTermEngine()
        dtype, ju, term, yuan, slong, feature, wuxing_hint = ste.get_chai_bu_ju(true_time, tag)
        is_yang = (dtype == "阳遁")
        
        pill = tag.get_pillars(true_time)
        qimen = QimenFullLogic(ju, is_yang, pill['xun'], pill['h_gan'], pill['h_zhi'])
        layout, zs_door = qimen.calculate()
        kw = qimen.get_kong_wang()
        ma = qimen.get_ma_xing()
        
        lye = LiuYaoEngine()
        gua_data = lye.process(st.session_state['yao_list'])
        gua_text_visual = lye.get_gua_text(gua_data)
        
        time.sleep(0.5)

    total_diff = mean_diff + eot_diff
    st.markdown(f"""
    <div class="status-bar">
    [SYSTEM] 经度: {final_long:.4f}° ({loc_source}) <br>
    [CORRECTION] 经度偏差: {mean_diff:+.2f}m | 真太阳时差(EoT): {eot_diff:+.2f}m | 总修正: {total_diff:+.2f}m
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("真太阳时", true_time.strftime('%H:%M:%S'), f"总偏 {int(total_diff)}分")
    c2.metric("节气", f"{term} ({yuan})", f"黄经 {slong:.2f}°")
    c3.metric("局信", f"{dtype}{ju}局", f"旬首 {pill['xun']}")
    c4.metric("值使/空亡", zs_door, kw)
    st.markdown(f"**四柱**：{pill['year']} {pill['day']} {pill['hour']}")
    
    st.divider()

    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.subheader("六爻卦象")
        st.write(f"本卦：**{gua_data['ben_name']}**")
        st.write(f"变卦：**{gua_data['bian_name']}**")
        
        html_lines = []
        for i in range(5, -1, -1):
            c = st.session_state['yao_list'][i]
            line_style = "━━━" if c in [7,9] else "━　━"
            
            if c in [6, 9]:
                color = "#FF0000"
            else:
                color = "#000000"
            
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
        palace_names = {1:"坎水",8:"艮土",3:"震木",4:"巽木",9:"离火",2:"坤土",7:"兑金",6:"乾金",5:"中宫(寄坤二)"}
        for row in grid_order:
            cols = st.columns(3)
            for idx, p_idx in enumerate(row):
                d = layout.get(p_idx, {})
                with cols[idx]:
                    if p_idx == 5:
                        st.markdown(f"""
                        <div class="card">
                            <div class="card-header">{palace_names[p_idx]}</div>
                            <div class="card-god">{d.get('god','')}</div>
                            <div class="card-star">{d.get('star','')}</div>
                            <div class="card-door">{d.get('door','')}</div>
                            <div class="card-stem">{d.get('di','')}</div>
                        </div>""", unsafe_allow_html=True)
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

    st.divider()
    
    # ====================== 【最终优化】结构化 AI 断卦文本 ======================
    raw_data = f"""
【问测】 {info['ask']}
【定场】 {info['name']} @ {info['city']} (经度:{final_long:.4f}°，时空已校准)
【空间面向】：{info.get('direction', '未知')}（可参考值符/用神落宫权重）
【时间】 {true_time.strftime('%Y-%m-%d %H:%M:%S')} (真太阳时 | 总修正:{total_diff:+.2f}分钟)
【四柱】 {pill['year']} {pill['day']} {pill['hour']} (旬首:{pill['xun']})
【奇门】 {term} {dtype}{ju}局 | {yuan} | 空亡:{kw} | 马星:{ma} | 值使:{zs_door}
【时空特征】：{term}前后，{dtype}，{yuan}用事，利于{feature}
【五行用事提示】：{wuxing_hint}

【六爻】 本卦：{gua_data['ben_name']} | 变卦：{gua_data['bian_name']} | 动爻：{gua_data['moving_lines']}
{gua_text_visual}

【布局】 (中宫前置，宫1坎→宫9离顺时针)：
宫5: 中宫(5)地盘干: {layout[5]['di']} (寄坤二，神/门/星同2宫)
宫1: {layout[1]['god']} {layout[1]['star']} {layout[1]['door']} [{layout[1]['tian']}/{layout[1]['di']}]
宫2: {layout[2]['god']} {layout[2]['star']} {layout[2]['door']} [{layout[2]['tian']}/{layout[2]['di']}]
宫3: {layout[3]['god']} {layout[3]['star']} {layout[3]['door']} [{layout[3]['tian']}/{layout[3]['di']}]
宫4: {layout[4]['god']} {layout[4]['star']} {layout[4]['door']} [{layout[4]['tian']}/{layout[4]['di']}]
宫6: {layout[6]['god']} {layout[6]['star']} {layout[6]['door']} [{layout[6]['tian']}/{layout[6]['di']}]
宫7: {layout[7]['god']} {layout[7]['star']} {layout[7]['door']} [{layout[7]['tian']}/{layout[7]['di']}]
宫8: {layout[8]['god']} {layout[8]['star']} {layout[8]['door']} [{layout[8]['tian']}/{layout[8]['di']}]
宫9: {layout[9]['god']} {layout[9]['star']} {layout[9]['door']} [{layout[9]['tian']}/{layout[9]['di']}]

【断卦指导】请严格结合以上时空+六爻+奇门全信息，综合分析所测之事：
1. 结合用户所问之事【{info['ask']}】，优先用值符落宫对应六爻世爻/用神；
2. 值使门吉凶断应期；
3. 空亡/马星断成败/快慢；
4. 九宫生克/格局看整体趋势；
5. 给出详细、客观的断语，包括成败概率、时间节点、注意事项、具体策略建议。
"""
    # ==========================================================================
        
    st.text_area("复制数据给 AI", raw_data, height=450)
    
    if st.button("🔄 再测一事"):
        st.session_state['yao_list'] = []
        st.session_state['finished'] = False
        st.session_state['ceremony_started'] = False
        st.session_state['user_info'] = {}
        st.rerun()
