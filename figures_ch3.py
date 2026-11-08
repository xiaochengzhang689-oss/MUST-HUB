# -*- coding: utf-8 -*-
"""
Chapter 3 figures for the MUSTHub Task 3 report.
绘制 Chapter 3 的两张图（UML 对象图 / 帖子状态图）。

    Figure 3-1  Object diagram of a MUSTHub snapshot
    Figure 3-2  State machine of a post (Normal / Downgraded / Flagged)

运行方式：
    pip install pillow
    python figures_ch3.py                # 输出到脚本所在目录
    python figures_ch3.py D:\\输出目录     # 或指定输出目录

输出：
    Figure3-1_Object_Diagram.png   1310 x 790
    Figure3-2_Post_State_Diagram.png  1300 x 650

实现说明：
  * 只用 Pillow，不依赖 matplotlib / graphviz / drawio。
  * 所有坐标是"逻辑坐标"，实际按 S=2 倍超采样绘制，最后 LANCZOS 缩小，
    这样线条和文字边缘不会有锯齿。
  * 字体优先用 Windows 的 Arial；找不到就退到 DejaVu Sans / Liberation Sans，
    再找不到用 Pillow 内置位图字体（能跑，但排版会变，仅作兜底）。
"""

import math
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("缺少 Pillow，请先运行：pip install pillow")

# --------------------------------------------------------------------------
# 全局设定
# --------------------------------------------------------------------------
S = 2                      # 超采样倍数：先画 2 倍大，最后缩小
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

INK = (33, 37, 41)         # 正文黑
EDGE = (60, 66, 74)        # 对象框边线
FILL_NAME = (232, 240, 250)  # 对象名栏底色
LINK = (60, 90, 150)       # 关联线（蓝）
ACCENT = (176, 58, 46)     # 主线 / 主要关联（红）
GUARD = (117, 76, 41)      # 状态图守卫条件（褐）

_FONT_CANDIDATES = {
    False: [r"C:\Windows\Fonts\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf"],
    True: [r"C:\Windows\Fonts\arialbd.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
}
_ITALIC_CANDIDATES = [r"C:\Windows\Fonts\ariali.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
                      "/System/Library/Fonts/Supplemental/Arial Italic.ttf"]
_font_cache = {}


def _pick(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def font(size, bold=False, italic=False):
    """按逻辑字号取字体；内部乘 S，因为画布是超采样的。"""
    paths = _ITALIC_CANDIDATES if italic else _FONT_CANDIDATES[bold]
    key = (round(size, 2), bold, italic)
    if key not in _font_cache:
        path = _pick(paths) or _pick(_FONT_CANDIDATES[False])
        px = max(1, int(size * S))
        _font_cache[key] = (ImageFont.truetype(path, px) if path
                            else ImageFont.load_default())
    return _font_cache[key]


def draw_text(d, xy, text, f, fill=INK):
    """在逻辑坐标 xy 处写字（内部换算成像素）。"""
    d.text((xy[0] * S, xy[1] * S), text, font=f, fill=fill)


def text_w(text, f):
    """文字的逻辑宽度。"""
    return f.getlength(text) / S


class Canvas:
    """薄封装：所有方法都接收逻辑坐标，内部乘 S。"""

    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.img)

    def save(self, path):
        self.img.resize((self.w, self.h), Image.LANCZOS).save(path)

    def rect(self, x, y, w, h, fill=(255, 255, 255), outline=EDGE, width=1.2, radius=6):
        self.d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                                 radius=radius * S, fill=fill, outline=outline,
                                 width=max(1, int(width * S)))

    def circle(self, cx, cy, r, fill=None, outline=None, width=1.2):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
                       fill=fill, outline=outline, width=max(1, int(width * S)))

    def line(self, pts, color=LINK, width=1.3):
        self.d.line([(p[0] * S, p[1] * S) for p in pts], fill=color,
                    width=max(1, int(width * S)), joint="curve")

    def label(self, x, y, text, f, color=INK, pad=3, ha="center"):
        """带白色衬底的标签，避免压住连线。"""
        w = text_w(text, f)
        h = f.size / S * 1.3
        x0 = x - w / 2 if ha == "center" else (x - w if ha == "right" else x)
        self.d.rectangle([(x0 - pad) * S, (y - h / 2) * S,
                          (x0 + w + pad) * S, (y + h / 2) * S], fill=(255, 255, 255))
        draw_text(self.d, (x0, y - h / 2 + 0.5), text, f, color)

    def arrow(self, x, y, ang_deg, color=LINK, size=7):
        """在 (x, y) 画一个指向 ang_deg 的实心箭头。"""
        pts = [(x * S, y * S)]
        for da in (152, -152):
            b = math.radians(ang_deg + da)
            pts.append(((x + size * math.cos(b)) * S, (y + size * math.sin(b)) * S))
        self.d.polygon(pts, fill=color)


# --------------------------------------------------------------------------
# Figure 3-1  UML 对象图
# --------------------------------------------------------------------------
def obj_height(n_attrs):
    """对象框高度：名栏 30 + 每行属性 17 + 下边留白 12。"""
    return 30 + 17 * n_attrs + 12


def uml_object(c, x, y, w, name, attrs, accent=None):
    """画一个 UML 对象框：上栏是带下划线的 inst : Type，下面列属性值。"""
    h = obj_height(len(attrs))
    c.rect(x, y, w, h, outline=accent or EDGE, width=1.6 if accent else 1.2)

    # 名栏底色 + 分隔线
    c.d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + 29) * S],
                          radius=6 * S, fill=FILL_NAME, outline=None)
    c.d.rectangle([x * S, (y + 22) * S, (x + w) * S, (y + 29) * S], fill=FILL_NAME)
    c.line([(x, y + 29), (x + w, y + 29)], color=EDGE, width=1.1)

    # 对象名（居中 + 下划线，UML 实例写法）
    f_name = font(12.5, bold=True)
    tw = text_w(name, f_name)
    nx = x + (w - tw) / 2
    draw_text(c.d, (nx, y + 7), name, f_name, (20, 40, 80))
    c.line([(nx, y + 23), (nx + tw, y + 23)], color=(20, 40, 80), width=1.0)

    # 属性值
    f_attr = font(10.5)
    ty = y + 36
    for a in attrs:
        draw_text(c.d, (x + 10, ty), a, f_attr, (45, 50, 58))
        ty += 17
    return (x, y, w, h)


def figure_object_diagram(out_dir=OUT_DIR):
    W, H = 1310, 790
    c = Canvas(W, H)
    f_lbl = font(10.5)
    f_acc = font(10.5, bold=True)

    col_x, col_w = 340, 272
    centers = {"v1": 120, "f1": 250, "rep1": 452, "r1": 620}

    # 中间一列：四张"动作"对象
    v1 = uml_object(c, col_x, centers["v1"] - obj_height(3) / 2, col_w, "v1 : Vote", [
        'voteId = "V3311"', 'value = +1', 'votedAt = "2026-10-27 21:11"'])
    f1 = uml_object(c, col_x, centers["f1"] - obj_height(2) / 2, col_w, "f1 : Favourite", [
        'favouriteId = "F4102"', 'savedAt = "2026-10-27 21:12"'])
    rep1 = uml_object(c, col_x, centers["rep1"] - obj_height(2) / 2, col_w, "rep1 : Report", [
        'reportId = "RP5077"', 'createdAt = "2026-10-27 21:31"'])
    r1 = uml_object(c, col_x, centers["r1"] - obj_height(3) / 2, col_w, "r1 : Reply", [
        'replyId = "R2087"', 'content = "Try official samples."',
        'createdAt = "2026-10-27 21:19"'])

    # 右侧：Post 与 Board
    p_cy = 420
    p1 = uml_object(c, 880, p_cy - obj_height(8) / 2, 390, "p1 : Post", [
        'postId = "P1042"',
        'title = "IELTS writing samples?"',
        'status = VISIBLE',
        'score = +15',
        'replyCount = 7',
        'reportCount = 1',
        'createdAt = "2026-10-27 21:04"',
        'lastActivityAt = "2026-10-27 21:30"'])

    b_cy = 178
    b1 = uml_object(c, 880, b_cy - obj_height(4) / 2, 390, "b1 : Board", [
        'boardId = "B03"', 'boardName = "Study Abroad"',
        'postCount = 128', 'visibility = PUBLIC'])

    # 左侧：User（红框 = 本章主要关联的起点）
    u_cy = 370
    u1 = uml_object(c, 20, u_cy - obj_height(4) / 2, 252, "u1 : User", [
        'username = "yyang"',
        'password = "******"',
        'createdAt = "2026-09-02 10:15"',
        'tags = {"IELTS", "cs"}'], accent=ACCENT)

    # User -> 四张动作对象（水平直线）
    for obj, label in ((v1, "casts"), (f1, "saves"), (rep1, "files"), (r1, "writes")):
        oy = obj[1] + obj[3] / 2
        c.line([(u1[0] + u1[2], oy), (obj[0], oy)])
        c.arrow(obj[0], oy, 0)
        c.label((u1[0] + u1[2] + obj[0]) / 2, oy - 9, label, f_lbl, LINK)

    # 四张动作对象 -> Post（拐两个弯，走中间空走廊，避免穿过对象）
    routes = ((v1, "targets", 652, 362), (f1, "refersTo", 702, 402),
              (rep1, "reports", 752, 458), (r1, "answers", 802, 492))
    for obj, label, corr, ty in routes:
        oy = obj[1] + obj[3] / 2
        c.line([(obj[0] + obj[2], oy), (corr, oy), (corr, ty), (p1[0], ty)])
        c.arrow(p1[0], ty, 0)
        c.label(corr + 5, oy + 13, label, f_lbl, LINK, ha="left")

    # Board contains Post
    bx = b1[0] + b1[2] / 2
    c.line([(bx, b1[1] + b1[3]), (bx, p1[1])])
    c.arrow(bx, p1[1], 90)
    c.label(bx + 10, (b1[1] + b1[3] + p1[1]) / 2, "contains", f_lbl, LINK, ha="left")

    # User -- Post 的 authorOf：从下方绕过去，避免横穿中间一列
    ycorr = 706
    xin = p1[0] + 140
    c.line([(u1[0] + u1[2] / 2, u1[1] + u1[3]),
            (u1[0] + u1[2] / 2, ycorr), (xin, ycorr), (xin, p1[1] + p1[3])])
    c.arrow(xin, p1[1] + p1[3], -90)
    c.label((u1[0] + u1[2] / 2 + xin) / 2, ycorr - 10, "authorOf", f_acc, ACCENT)

    # 图例
    lx, ly = 20, 70
    c.rect(lx, ly, 300, 116, fill=(250, 250, 250), outline=(203, 207, 213), width=0.9)
    draw_text(c.d, (lx + 12, ly + 10), "Notation (UML 2.x object diagram)", font(9.5, bold=True))
    draw_text(c.d, (lx + 12, ly + 30), "underlined  inst : Type   object instance", font(8.6))
    draw_text(c.d, (lx + 12, ly + 48), "compartment     attribute values", font(8.6))
    draw_text(c.d, (lx + 12, ly + 66), "solid line     link (association instance)", font(8.6))
    draw_text(c.d, (lx + 12, ly + 84), "red line       principal association", font(8.6))

    path = os.path.join(out_dir, "Figure3-1_Object_Diagram.png")
    c.save(path)
    return path


# --------------------------------------------------------------------------
# Figure 3-2  Post 状态图
# --------------------------------------------------------------------------
def figure_state_diagram(out_dir=OUT_DIR):
    W, H = 1300, 650
    c = Canvas(W, H)
    f_state = font(12.5, bold=True)
    f_sub = font(9.6)
    f_lbl = font(10.5)
    f_guard = font(9.6, italic=True)

    top, sh = 180, 110
    mid = top + sh / 2  # 235

    def state(x, w, name, internal, color):
        """圆角状态框：上栏状态名，下栏 status 值和 entry 动作。"""
        c.d.rounded_rectangle([x * S, top * S, (x + w) * S, (top + sh) * S],
                              radius=13 * S, fill=color, outline=(90, 96, 104),
                              width=max(1, int(1.3 * S)))
        tw = text_w(name, f_state)
        draw_text(c.d, (x + (w - tw) / 2, top + 10), name, f_state, (25, 30, 40))
        c.line([(x, top + 33), (x + w, top + 33)], color=(125, 131, 139), width=1.0)
        ty = top + 40
        for line in internal:
            draw_text(c.d, (x + 12, ty), line, f_sub, (50, 56, 64))
            ty += 15
        return x

    vx = state(170, 230, "Normal",
               ["status = VISIBLE", "listed in board, Hot eligible"], (232, 245, 234))
    dx = state(545, 260, "Downgraded",
               ["status = DOWNGRADED", "entry / hideFromBoardList()"], (253, 236, 226))
    fx = state(925, 240, "Flagged",
               ["status = FLAGGED", "entry / dropFromHotRanking()"], (238, 240, 248))

    # 初态 -> Normal
    c.circle(52, mid, 14, fill=(40, 44, 50))
    c.line([(66, mid), (vx, mid)], color=INK)
    c.arrow(vx, mid, 0, INK)
    c.label(118, mid - 15, "T1  createPost()", f_lbl)

    # Normal -> Downgraded（T2）
    c.line([(vx + 230, mid), (dx, mid)], color=INK)
    c.arrow(dx, mid, 0, INK)
    c.label((vx + 230 + dx) / 2, mid - 14, "T2  downgrade()", f_lbl, ACCENT)
    c.label((vx + 230 + dx) / 2, 318, "[net score reaches the", f_guard, GUARD)
    c.label((vx + 230 + dx) / 2, 334, "downgrade threshold]", f_guard, GUARD)

    # Downgraded -> Normal（T3，由一条成功回复触发，见 UC3）
    c.line([(dx + 130, top + sh), (dx + 130, 405), (vx + 115, 405), (vx + 115, top + sh)],
           color=INK)
    c.arrow(vx + 115, top + sh, -90, INK)
    c.label((dx + 130 + vx + 115) / 2, 393, "T3  restore()", f_lbl, ACCENT)
    c.label((dx + 130 + vx + 115) / 2, 426, "[one accepted reply is posted on it]", f_guard, GUARD)

    # Normal -> Flagged（T4，走上面的弧线）
    c.line([(vx + 115, top), (vx + 115, 96), (fx + 120, 96), (fx + 120, top)], color=INK)
    c.arrow(fx + 120, top, 90, INK)
    c.label((vx + 115 + fx + 120) / 2, 82, "T4  flag()", f_lbl, ACCENT)
    c.label((vx + 115 + fx + 120) / 2, 118, "[3 distinct reporters]", f_guard, GUARD)

    # Downgraded -> Flagged（T5：被回复恢复时已经满 3 个举报）
    c.line([(dx + 260, mid), (fx, mid)], color=INK)
    c.arrow(fx, mid, 0, INK)
    c.label((dx + 260 + fx) / 2, mid - 14, "T5  restore + flag()", f_lbl, ACCENT)
    c.label((dx + 260 + fx) / 2, 310, "[restored while it already has", f_guard, GUARD)
    c.label((dx + 260 + fx) / 2, 326, "reportCount >= 3]", f_guard, GUARD)

    # 业务规则说明框
    nx, ny, nw = 140, 470, 780
    c.rect(nx, ny, nw, 140, fill=(250, 250, 245), outline=(202, 197, 179), width=0.9)
    draw_text(c.d, (nx + 14, ny + 10),
              "Business rules (Chapter 2 sec. 2.3, 2.4.3, 2.4.4, 2.4.10)", font(9.5, bold=True))
    for i, line in enumerate([
        "Downgrade: after a vote, if the net score reaches the threshold, the post leaves the board list.",
        "Restore: one accepted reply (UC3) turns a downgraded post back to Normal, as Chapter 2 sec. 2.4.3 states.",
        "Flag: three distinct reporters (UC10) drop the post from the Hot ranking only; a flagged post is still",
        "listed in its board. Flagged is a terminal state: Version 1.0 has no appeal or review workflow.",
        "Sensitive-word filtering rejects content when it is written (an <<include>> of UC2/UC3), it does not",
        "downgrade an existing post. Version 1.0 has no delete-post function, so there is no Deleted state.",
    ]):
        draw_text(c.d, (nx + 14, ny + 30 + i * 17), line, font(8.8))

    path = os.path.join(out_dir, "Figure3-2_Post_State_Diagram.png")
    c.save(path)
    return path


# --------------------------------------------------------------------------
def main(argv):
    global OUT_DIR
    if len(argv) > 1:
        OUT_DIR = argv[1]
        os.makedirs(OUT_DIR, exist_ok=True)
    print(figure_object_diagram(OUT_DIR))
    print(figure_state_diagram(OUT_DIR))


if __name__ == "__main__":
    main(sys.argv)
