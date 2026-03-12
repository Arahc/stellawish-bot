from PIL import Image, ImageDraw
from pathlib import Path

from .sketchbox import FontManager as Font
from .sketchbox import GridManager as Grid
from .sketchbox import shadowed, truncate, wrap
from .utils import isFontBomb
from .static import DIFF_NAME_LIST, DIFF_COL_LIST, DIFF_FONT_COL_LIST, PIC_FOOTER_COL, VERSION_DICT

PIC_DIR = Path(__file__).parent / "pics"
COVER_DIR = PIC_DIR / "covers"

CONFIG = {
    "canvas": {
        "W": 1440,
        "H": 1440,
        "margin": {
            "top": 20,
            "bottom": 20,
            "left": 20,
            "right": 20
        },
        "song_diff_padding": 30,
        "diffcard_padding": 8
    },
    "songcard": {
        "W": 420,
        "H": 1400,
        "cover_size": 400
    },
    "diffcard": {
        "W": 970,
        "H": 270
    }
}

def rgb(r: int, g: int, b: int) -> tuple[int, int, int]:
    return (r, g, b)

COL_BLOCK_FILL = rgb(170, 204, 255) + (100,)
COL_BLOCK_LINE = rgb(94, 158, 255) + (200,)

class SongCard:
    W: int = CONFIG["songcard"]["W"]
    H: int = CONFIG["songcard"]["H"]
    cover_size: int = CONFIG["songcard"]["cover_size"]

    def __init__(self, song, chartpack):
        self.song = song
        self.pack = chartpack

        self.font_tit = Font.get("SourceHanSans-Bold.otf", 40)
        self.font_artist = Font.get("SourceHanSans-Bold.otf", 24)
        self.font_info = Font.get("MapleMono-CN-Bold.ttf", 24)

        self.col_font = rgb(80, 132, 211)
        self.col_block_fill = COL_BLOCK_FILL
        self.col_block_line = COL_BLOCK_LINE

    def render(self) -> Image.Image:
        img = Image.new("RGBA", (self.W, self.H))

        y = 0
        cover = self._draw_cover()
        img.alpha_composite(cover, (0, y))

        y += cover.height + 8
        bg = self._draw_bg()
        img.alpha_composite(bg, (0, y))

        y += 6
        info = self._draw_info()
        img.alpha_composite(info, (12, y))

        return img

    def _draw_cover(self) -> Image.Image:
        cover = Image.open(COVER_DIR / f"{self.song.id:04d}.png").convert("RGBA")
        cover = cover.resize((self.cover_size, self.cover_size), Image.LANCZOS)
        return shadowed(cover, offset=(0, 0), blur=2, scale=1.02, color=(0, 0, 0, 50))

    def _draw_bg(self) -> Image.Image:
        bg = Image.new("RGBA", (420, 960))
        ImageDraw.Draw(bg).rounded_rectangle(
            (0, 0, 412, 950),
            radius=16,
            fill=self.col_block_fill,
            outline=self.col_block_line,
            width=3
        )
        return bg

    def _draw_info(self) -> Image.Image:
        W = 400
        H = 960
        pad_info_H = 32
        res = Image.new("RGBA", (W, H))
        draw = ImageDraw.Draw(res)

        # title
        if self.pack.type == "宴":
            title = self.pack.tag + " " + self.song.title
        else:
            title = self.song.title

        lines = wrap(
            text=title,
            max_width=W - 8,
            font=self.font_tit
        )
        y = 0
        if len(lines) == 1:
            bbox = draw.textbbox((0, 0), title, font=self.font_tit)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            draw.text(
                ((W - w) // 2, y),
                title,
                font=self.font_tit,
                fill=self.col_font
            )
            y += h + 4
        else:
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=self.font_tit)
                h = bbox[3] - bbox[1]
                draw.text(
                    (0, y),
                    line,
                    font=self.font_tit,
                    fill=self.col_font
                )
                y += h + 4

        # artist
        artist = self.song.artist
        lines = wrap(
            text=artist,
            max_width=W - 8,
            font=self.font_artist
        )
        y += 24
        if len(lines) == 1:
            bbox = draw.textbbox((0, 0), artist, font=self.font_artist)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            draw.text(
                ((W - w) // 2, y),
                artist,
                font=self.font_artist,
                fill=self.col_font
            )
            y += h + 4
        else:
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=self.font_artist)
                h = bbox[3] - bbox[1]
                draw.text(
                    (0, y),
                    line,
                    font=self.font_artist,
                    fill=self.col_font
                )
                y += h + 4
        
        # info
        N_aliases = len(self.song.aliases)
        lines = [
            f"* ID: {self.pack.id} ({self.pack.type})",
            f"* BPM: {self.song.bpm}",
            f"* 版本: {self.pack.version.replace("舞萌 DX", "舞萌DX")}" + (f"〔{VERSION_DICT[self.pack.version]}〕" if VERSION_DICT[self.pack.version] else ""),
            f"* 分类：{self.song.genre}",
            f"* 别名：" + ("暂无" if N_aliases == 0 else "（最多显示 20 条）")
        ]
        if N_aliases > 0:
            cnt = 0
            for alias in self.song.aliases:
                if len(alias) > 11 or isFontBomb(alias):
                    continue
                lines.append(f"  - {alias}")
                cnt += 1
                if cnt == 20:
                    break
        y += 24
        for line in lines:
            draw.text(
                (0, y),
                line,
                font=self.font_info,
                fill=self.col_font
            )
            y += pad_info_H

        return res

def makeNoteTable(chart) -> list[str]:
    basescore = chart.tap + chart.hold*2 + chart.slide*3 + chart.touch + chart.breaks*5
    TAPgr = 20 / basescore
    rewardscore = chart.breaks
    res = ["", "个数", "落", "粉", "绿", "灰"]

    res +=["TAP", str(chart.tap), "-"]
    if chart.tap != 0:
        res += [f"-{TAPgr:.4f}%", f"-{(TAPgr * 2.5):.4f}%", f"-{(TAPgr * 5):.4f}%"]
    else:
        res += ["-", "-", "-"]
    
    res += ["HOLD", str(chart.hold), "-"]
    if chart.hold != 0:
        res += [f"-{(TAPgr * 2):.4f}%", f"-{(TAPgr * 5):.4f}%", f"-{(TAPgr * 10):.4f}%"]
    else:
        res += ["-", "-", "-"]
    
    res += ["SLIDE", str(chart.slide), "-"]
    if chart.slide != 0:
        res += [f"-{(TAPgr * 3):.4f}%", f"-{(TAPgr * 7.5):.4f}%", f"-{(TAPgr * 15):.4f}%"]
    else:
        res += ["-", "-", "-"]
    
    res += ["TOUCH", str(chart.touch), "-"]
    if chart.touch != 0:
        res += [f"-{TAPgr:.4f}%", f"-{(TAPgr * 2.5):.4f}%", f"-{(TAPgr * 5):.4f}%"]
    else:
        res += ["-", "-", "-"]

    if chart.breaks != 0:
        res += ["", "", f"-{(0.25 / rewardscore):.4f}%", f"-{(100 / basescore + 0.6 / rewardscore):.4f}%", "", ""]
        res += ["BREAK", str(chart.breaks), "~", "~", f"-{(300 / basescore + 0.7 / rewardscore):.4f}%", f"-{(500 / basescore + 1 / rewardscore):.4f}%"]
        res += ["", "", f"-{(0.5 / rewardscore):.4f}%", f"-{(250 / basescore + 0.6 / rewardscore):.4f}%", "", ""]
    else:
        res += ["BREAK", "0", "-", "-", "-", "-"]
    
    res += ["TOTAL", str(chart.tap + chart.hold + chart.slide + chart.touch + chart.breaks), "-", "-", "-", "-"]

    return res

def makeRaTable(chart) -> list[str]:
    basescore = chart.tap + chart.hold*2 + chart.slide*3 + chart.touch + chart.breaks*5
    TAPgr = 20 / basescore
    res = ["评级", "SSS+", "SSS", "SS+", "SS", "S+", "S"]
    if chart.diffid > 4:
        res += ["ra", "-", "-", "-", "-", "-", "-"]
    else:
        res += ["ra", str(chart.getRating(100.5)), str(chart.getRating(100)), str(chart.getRating(99.5)), str(chart.getRating(99)), str(chart.getRating(98)), str(chart.getRating(97))]
    res += ["容错", f"{(0.5 / TAPgr):.2f}", f"{(1 / TAPgr):.2f}", f"{(1.5 / TAPgr):.2f}", f"{(2 / TAPgr):.2f}", f"{(3 / TAPgr):.2f}", f"{(4 / TAPgr):.2f}"]
    return res

def breakCalcer(chart) -> list[tuple[float, float]]:
    basescore = chart.tap + chart.hold*2 + chart.slide*3 + chart.touch + chart.breaks*5
    TAPgr = 20 / basescore
    rewardscore = chart.breaks
    return [
        ((0.25 / rewardscore) / TAPgr, (0.5 / rewardscore) / TAPgr), # 落
        ((100 / basescore + 0.6 / rewardscore) / TAPgr, (250 / basescore + 0.6 / rewardscore) / TAPgr), # 粉
        ((300 / basescore + 0.7 / rewardscore) / TAPgr, (300 / basescore + 0.7 / rewardscore) / TAPgr), # 绿
        ((500 / basescore + 1 / rewardscore) / TAPgr, (500 / basescore + 1 / rewardscore) / TAPgr) # 灰
    ]


class DiffCard:
    W: int = CONFIG["diffcard"]["W"]
    H: int = CONFIG["diffcard"]["H"]

    def __init__(self, chart):
        self.chart = chart
        self.cols = DIFF_COL_LIST[chart.diffid]

        self.font_tit = Font.get("SourceHanSans-Bold.otf", 30)
        self.font_sub = Font.get("SourceHanSans-Regular.otf", 20)
        self.font_table = Font.get("MapleMono-CN-Medium.ttf", 16)
        self.font_info = Font.get("MapleMono-CN-Medium.ttf", 16)

        self.col_font = DIFF_FONT_COL_LIST[chart.diffid]

    def render(self) -> Image.Image:
        img = Image.new("RGBA", (self.W, self.H), tuple(self.cols[0]) + (255,))
        x = 8
        y = 0
        title = self._draw_title()
        img.alpha_composite(title, (x, y))

        y += title.height + 5
        table1 = self._draw_note_table()
        img.alpha_composite(table1, (x, y))

        x += table1.width + 10
        table2 = self._draw_ra_table()
        img.alpha_composite(table2, (x, y))

        x_off = -2
        y += table2.height + 5
        info = self._draw_break_info()
        img.alpha_composite(info, (x + x_off, y))

        return shadowed(img, (3, 3), 3, 1, (50, 50, 50, 50))
    
    def _draw_title(self) -> Image.Image:
        W = self.W - 16
        H = 45
        tit_off = (0, 0)
        sub_off = (0, 12)
        res = Image.new("RGBA", (W, H))
        tit_text = f"{DIFF_NAME_LIST[self.chart.diffid]} {self.chart.diff}"
        bbox = ImageDraw.Draw(res).textbbox((0, 0), tit_text, font=self.font_tit)
        tit_w = bbox[2] - bbox[0]
        ImageDraw.Draw(res).text(
            tit_off,
            tit_text,
            font=self.font_tit,
            fill=self.col_font
        )
        sub_text = truncate(f"by {self.chart.charter}", W - 10 - tit_w, font=self.font_sub)
        ImageDraw.Draw(res).text(
            (tit_w + 10 + sub_off[0], sub_off[1]),
            sub_text,
            font=self.font_sub,
            fill=self.col_font
        )
        ImageDraw.Draw(res).line(
            ((0, H - 2), (W, H - 2)),
            fill=self.col_font,
            width=2
        )
        return res
    
    def _draw_note_table(self) -> Image.Image:
        W = 500
        H = 220
        ele_W = [60, 50, 90, 90, 90, 90]
        ele_H = [25, 25, 25, 25, 25, 15, 15, 25, 25]
        tab_W = sum(ele_W) + 24
        tab_H = sum(ele_H) + 18
        res = Image.new("RGBA", (W, H))
        grid = Grid(
            width=tab_W,
            height=tab_H,
            element_w=ele_W,
            element_h=ele_H
        )
        tab = makeNoteTable(self.chart)
        positions = grid.places(len(tab))
        for text, (i, (x, y)) in zip(tab, enumerate(positions)):
            j = i % 6
            ImageDraw.Draw(res).text(
                (x + ele_W[j] // 2 - self.font_table.getlength(text) // 2, y),
                text,
                font=self.font_table,
                fill=self.col_font
            )
        ImageDraw.Draw(res).line(
            ((W - 5, 2), (W - 5, H - 6)),
            fill=self.col_font,
            width=2
        )
        return res
    
    def _draw_ra_table(self) -> Image.Image:
        W = 450
        H = 100
        ele_W = [35, 60, 60, 65, 65, 65, 65]
        ele_H = [25] * 3 
        tab_W = sum(ele_W) + 36
        tab_H = sum(ele_H) + 18
        res = Image.new("RGBA", (W, H))
        grid = Grid(
            width=tab_W,
            height=tab_H,
            element_w=ele_W,
            element_h=ele_H
        )
        tab = makeRaTable(self.chart)
        positions = grid.places(len(tab))
        for text, (i, (x, y)) in zip(tab, enumerate(positions)):
            j = i % 7
            ImageDraw.Draw(res).text(
                (x + ele_W[j] // 2 - self.font_table.getlength(text) // 2, y),
                text,
                font=self.font_table,
                fill=self.col_font
            )
        return res

    def _draw_break_info(self) -> Image.Image:
        W = 450
        H = 220
        line_gap=4
        data = breakCalcer(self.chart)
        lines = [
            "* 容错单位为 TAP great.",
            f"* 落绝赞等效 {data[0][0]:.3f}~{data[0][1]:.3f} TAP great.",
            f"* 粉绝赞等效 {data[1][0]:.3f}~{data[1][1]:.3f} TAP great.",
            f"* 绿绝赞等效 {data[2][0]:.3f} TAP great.",
            f"* 灰绝赞等效 {data[3][0]:.3f} TAP great.",
        ]
        y = 0
        res = Image.new("RGBA", (W, H))
        for line in lines:
            ImageDraw.Draw(res).text(
                (0, y),
                line,
                font=self.font_info,
                fill=self.col_font
            )
            bbox = ImageDraw.Draw(res).textbbox((0, 0), line, font=self.font_info)
            h = bbox[3] - bbox[1]
            y += h + line_gap
        return res

class Canvas:
    W: int = CONFIG["canvas"]["W"]
    H: int = CONFIG["canvas"]["H"]
    margin: dict[str, int] = CONFIG["canvas"]["margin"]
    diff_padding: int = CONFIG["canvas"]["diffcard_padding"]
    song_diff_padding: int = CONFIG["canvas"]["song_diff_padding"]

    def __init__(self):
        self.img = Image.new("RGB", (self.W, self.H))
        self.draw = ImageDraw.Draw(self.img)
        self.paste = self.img.paste

        self.footer_font = Font.get("MapleMono-CN-Medium.ttf", 20)

        self.col_font = PIC_FOOTER_COL
        self.col_block_fill = COL_BLOCK_FILL
        self.col_block_line = COL_BLOCK_LINE

    def render(self, song, chartpack) -> Image.Image:
        self._draw_bg()
        self._draw_songcard(song, chartpack)
        self._draw_diffcards(chartpack.charts)
        self._draw_footer()
        return self.img

    def _draw_bg(self):
        bg = Image.open(PIC_DIR / "bg.png").convert("RGBA")
        bg_ratio = bg.width / bg.height
        canvas_ratio = self.W / self.H
        if bg_ratio > canvas_ratio:
            new_height = self.H
            new_width = int(new_height * bg_ratio)
        else:
            new_width = self.W
            new_height = int(new_width / bg_ratio)
        bg = bg.resize((new_width, new_height), Image.LANCZOS)
        bg = bg.crop((
            (new_width - self.W) // 2,
            (new_height - self.H) // 2,
            (new_width + self.W) // 2,
            (new_height + self.H) // 2
        ))
        self.paste(bg, (0, 0), bg)
    
    def _draw_songcard(self, song, chartpack):
        card = SongCard(song, chartpack).render()
        self.paste(card, (self.margin["left"], self.margin["top"]), card)

    def _draw_diffcards(self, charts):
        Y_OFF = -6
        left_up = (SongCard.W + self.song_diff_padding - 8, self.margin["top"] - 6)
        right_bottom = (self.W - self.margin["right"] + 16, self.H - self.margin["bottom"] - 2)
        W = right_bottom[0] - left_up[0]
        H = right_bottom[1] - left_up[1]
        bg = Image.new("RGBA", (W, H))
        ImageDraw.Draw(bg).rounded_rectangle(
            (0, 0, W, H),
            radius=16,
            fill=self.col_block_fill,
            outline=self.col_block_line,
            width=3
        )
        self.paste(bg, (left_up[0], left_up[1] + Y_OFF), bg)
        for i in range(len(charts)):
            card = DiffCard(charts[i]).render()
            x = SongCard.W + self.song_diff_padding
            y = self.margin["top"] + (DiffCard.H + self.diff_padding) * i
            self.paste(card, (x, y + Y_OFF), card)

    def _draw_footer(self):
        text = "Generated by 星愿 (Stellawish Bot) @_Arahc_"
        bbox = self.draw.textbbox((0, 0), text, font=self.footer_font)
        w = bbox[2] - bbox[0]
        x = (self.W - w) // 2
        y = self.H - 30
        ImageDraw.Draw(self.img).text(
            (x, y),
            text,
            font=self.footer_font,
            fill=self.col_font
        )

def generateSongInfo(song, chartpack) -> Image.Image:
    canvas = Canvas()
    img = canvas.render(song, chartpack)
    return img
