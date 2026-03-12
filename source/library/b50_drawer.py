from PIL import Image, ImageDraw
from pathlib import Path

from .sketchbox import shadowed, truncate, filter
from .sketchbox import FontManager as Font
from .sketchbox import GridManager as Grid
from .songlist_manager import SONG_LIST
from .static import DIFF_COL_LIST, DIFF_FONT_COL_LIST, PIC_FOOTER_COL, STAR_DXRATE_LIST

PIC_DIR = Path(__file__).parent.parent / "data" / "pics"
COVER_DIR = PIC_DIR / "covers"
UI_DIR = PIC_DIR / "ui"
PLATE_DIR = PIC_DIR / "plates"
AVATAR_DIR = PIC_DIR / "avatars"

CONFIG = {
    "canvas": {
        "W": 1440,
        "H": 1920,
        "user_score_gap": 5,
        "15_35_gap": 40,
        "card_gap": 4,
        "margin": {
            "top": 10,
            "bottom": 10,
            "left": 20,
            "right": 20
        }
    },
    "score_card": {
        "W": 272,
        "H": 161,
        "padding": 6,
        "cover_size": 105,
        "title_bar_H": 30,
        "tag_off": 6,
        "tag_W": 48,
        "tag_H": 30,
        "subtag_W": 72,
        "subtag_H": 24,
        "badge_radius": 20,
        "badge_margin": 5
    },
    "user_card": {
        "W": 1400,
        "H": 180,
        "plate_margin": {
            "top": 10,
            "left": 16
        }
    },
    "logo_size": 200
}

RATING_FILE_DICT = {
    15000: UI_DIR / "ra11.png",
    14500: UI_DIR / "ra10.png",
    14000: UI_DIR / "ra09.png",
    13000: UI_DIR / "ra08.png",
    12000: UI_DIR / "ra07.png",
    10000: UI_DIR / "ra06.png",
    7000: UI_DIR / "ra05.png",
    4999: UI_DIR / "ra04.png",
    2000: UI_DIR / "ra03.png",
    1000: UI_DIR / "ra02.png",
    0: UI_DIR / "ra01.png"
}
STAR_FILE_LIST = [
    UI_DIR / "star1.png", # 0 stars 0~84.99
    UI_DIR / "star1.png", # 1 star 85~89.99
    UI_DIR / "star1.png", # 2 stars 90~92.99
    UI_DIR / "star2.png", # 3 stars 93~94.99
    UI_DIR / "star2.png", # 4 stars 95~96.99
    UI_DIR / "star3.png", # 5 stars 97~98.99
    UI_DIR / "star3.png", # 6 stars 99~99.99
    UI_DIR / "star3.png"  # 7 stars 100
]

class GradeInfo:
    title: str
    type: str
    id: int
    ra: int
    rate: str
    level_id: str
    diff: float
    acc: float
    fc: str | None = None
    fs: str | None = None
    dxScore: int
    max_dxScore: int
    count: int

    def __init__(self, data: dict, count: int):
        self.title = data['title']
        self.type = data['type']
        self.id = int(data['song_id'])
        self.ra = int(data['ra'])
        self.rate = data['rate']
        self.level_id = data['level_index']
        self.diff = float(data['ds'])
        self.acc = float(data['achievements'])
        self.fc = data['fc']
        self.fs = data['fs']
        self.dxScore = int(data['dxScore'])
        self.count = count

        res = SONG_LIST.getSongList().findByID(self.id)
        if not res:
            raise ValueError(f"Song ID {self.id} not found in song list")

        chartpack = res[1]
        chart = chartpack.charts[data['level_index']]
        self.max_dxScore = (chart.tap + chart.hold + chart.slide + chart.touch + chart.breaks) * 3

class UserInfo:
    rating: int # = the sum of all ra
    ra35: int # = the sum of top 35 ra
    ra15: int # = the sum of recent 15 ra
    name: str
    plate: str | None
    grade: int

    def __init__(self, data: dict):
        self.rating = int(data['rating'])
        self.name = data['nickname']
        self.plate = data.get('plate', None)
        self.grade = int(data['additional_rating'])
        self.ra35 = 0
        self.ra15 = 0
        for c in data['charts']['sd']:
            self.ra35 += int(c['ra'])
        for c in data['charts']['dx']:
            self.ra15 += int(c['ra'])

class ScoreCard:
    W: int = CONFIG['score_card']['W']
    H: int = CONFIG['score_card']['H']
    PADDING: int = CONFIG['score_card']['padding']

    title_bar_H: int = CONFIG['score_card']['title_bar_H']
    cover_size: int = CONFIG['score_card']['cover_size']
    tag_offset: int = CONFIG['score_card']['tag_off']
    tag_W: int = CONFIG['score_card']['tag_W']
    tag_H: int = CONFIG['score_card']['tag_H']
    subtag_W: int = CONFIG['score_card']['subtag_W']
    subtag_H: int = CONFIG['score_card']['subtag_H']
    badge_R: int = CONFIG['score_card']['badge_radius']
    badge_padding: int = CONFIG['score_card']['badge_margin']

    badge_cost = badge_R - badge_padding
    base_W: int = W - badge_R - tag_offset + badge_padding
    base_H: int = H - title_bar_H - badge_R + badge_padding

    def __init__(self, grade: GradeInfo):
        self.grade = grade
    
        self.font_title = Font.get("SourceHanSans-Bold.otf", 18)
        self.font_count = Font.get("Exo-SemiBold.ttf", 20)
        self.font_id = Font.get("MapleMono-CN-Medium.ttf", 12)
        self.font_acc = Font.get("Exo-SemiBold.ttf", 24)
        self.font_dxscore = Font.get("Exo-Medium.ttf", 12)
        self.font_ra = Font.get("Exo-Medium.ttf", 12)
        self.font_diff = Font.get("Exo-Medium.ttf", 17)

        self.cols = DIFF_COL_LIST[self.grade.level_id]
        self.col_font = DIFF_FONT_COL_LIST[self.grade.level_id]
    
    def render(self) -> Image.Image:
        img = Image.new("RGBA", (self.W, self.H))

        base = self._draw_base()
        img.alpha_composite(base, (self.tag_offset, self.badge_cost))

        cover = self._draw_cover()
        img.alpha_composite(cover, (self.base_W + self.tag_offset - self.PADDING * 2 - self.cover_size, self.badge_cost + self.PADDING))

        title_bar = self._draw_title_bar()
        img.alpha_composite(title_bar, (self.tag_offset, self.H - self.title_bar_H))

        tag = self._draw_tag()
        img.alpha_composite(tag, (0, self.badge_cost + self.PADDING))

        content = self._draw_content()
        img.alpha_composite(content, (self.tag_offset + self.PADDING, self.badge_cost + self.PADDING + self.tag_H))

        badge = self._draw_badge()
        img.alpha_composite(badge, (self.W - self.badge_R * 2 - self.badge_padding, self.badge_padding))

        return shadowed(img, offset=(4, 4), blur=2, scale=1.0, color=(0, 0, 0, 100))

    def _draw_base(self) -> Image.Image:
        base = Image.new("RGBA", (self.base_W, self.base_H), self.cols[0] + (255,))
        return base

    def _draw_cover(self) -> Image.Image:
        cover_path = COVER_DIR / f"{self.grade.id % 10000:04d}.png"
        cover = Image.open(cover_path).convert("RGBA")
        cover = cover.resize((self.cover_size, self.cover_size), Image.LANCZOS)
        return shadowed(cover, offset=(0, 0), blur=2, scale=1.02, color=(0, 0, 0, 50))

    def _draw_title_bar(self) -> Image.Image:
        text_y_off = 5

        bar = Image.new("RGBA", (self.base_W, self.title_bar_H), self.cols[1] + (255,))
        title = truncate(
            self.grade.title,
            max_width=self.base_W - self.PADDING * 2,
            font=self.font_title
        )
        
        ImageDraw.Draw(bar).text(
            (self.PADDING, (self.title_bar_H - self.font_title.size) // 2 - text_y_off),
            title,
            font=self.font_title,
            fill=self.col_font
        )
        return bar

    def _draw_tag(self) -> Image.Image:
        text_count_y_off = 6
        text_id_y_off = 4

        res = Image.new("RGBA", (self.tag_W + self.subtag_W, self.tag_H))

        tag = Image.new("RGBA", (self.tag_W, self.tag_H), self.cols[1] + (255,))
        tag_text = f"#{self.grade.count}"
        bbox = ImageDraw.Draw(tag).textbbox((0, 0), tag_text, font=self.font_count)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        ImageDraw.Draw(tag).text(
            ((self.tag_W - w) // 2, (self.tag_H - h) // 2 - text_count_y_off),
            tag_text,
            font=self.font_count,
            fill=self.col_font
        )

        subtag = Image.new("RGBA", (self.subtag_W, self.subtag_H), self.cols[2] + (255,))
        subtag_text = f"{self.grade.type} {self.grade.id}"
        bbox = ImageDraw.Draw(subtag).textbbox((0, 0), subtag_text, font=self.font_id)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        ImageDraw.Draw(subtag).text(
            (self.PADDING // 2, (self.subtag_H - h) // 2 - text_id_y_off),
            subtag_text,
            font=self.font_id,
            fill=self.col_font
        )

        res.alpha_composite(tag, (0, 0))
        res.alpha_composite(subtag, (self.tag_W, (self.tag_H - self.subtag_H) // 2))
        return shadowed(res, offset=(2, 2), blur=1, scale=1.0, color=(50, 50, 50, 50))

    def _draw_content(self) -> Image.Image:
        text_y_off = -2
        text_padding = 10
        text_pic_padding = 6
        ra_text_x_off = 4

        y = 0
        content = Image.new("RGBA", (self.base_W - self.PADDING * 2 - self.cover_size, self.base_H - self.PADDING * 2 - self.tag_H + 5))

        # acc
        acc_text = f"{self.grade.acc:.4f}%"
        acc_box = ImageDraw.Draw(content).textbbox((0, 0), acc_text, font=self.font_acc)
        acc_h = acc_box[3] - acc_box[1]
        ImageDraw.Draw(content).text(
            (0, y - text_y_off),
            acc_text,
            font=self.font_acc,
            fill=self.col_font
        )
        y += acc_h + text_padding

        # dx score
        dx_score_text = f"{self.grade.dxScore} / {self.grade.max_dxScore}"
        dx_box = ImageDraw.Draw(content).textbbox((0, 0), dx_score_text, font=self.font_dxscore)
        dx_h = dx_box[3] - dx_box[1]
        ImageDraw.Draw(content).text(
            (0, y - text_y_off),
            dx_score_text,
            font=self.font_dxscore,
            fill=self.col_font
        )

        # rating
        ra_text = f"ra: {self.grade.ra}"
        ra_box = ImageDraw.Draw(content).textbbox((0, 0), ra_text, font=self.font_ra)
        ra_w = ra_box[2] - ra_box[0]
        ra_h = ra_box[3] - ra_box[1]
        ImageDraw.Draw(content).text(
            (content.width - ra_w - self.PADDING - ra_text_x_off, y - text_y_off),
            ra_text,
            font=self.font_ra,
            fill=self.col_font
        )
        y += max(ra_h, dx_h) + text_pic_padding

        # grade icons
        grade_pic_size = 32
        pic_padding = 2

        blank_pic = Image.open(UI_DIR / "blank.png").convert("RGBA")
        blank_pic = blank_pic.resize((grade_pic_size, grade_pic_size), Image.LANCZOS)
        blank_pic = filter(blank_pic, self.cols[0] + (180,))

        if self.grade.fc == "":
            fc_pic = blank_pic.copy()
        else:
            fc_pic = Image.open(UI_DIR / f"{self.grade.fc}.png").convert("RGBA")
            fc_pic = fc_pic.resize((grade_pic_size, grade_pic_size), Image.LANCZOS)
        content.alpha_composite(fc_pic, (0, y))
        
        if self.grade.fs == "":
            fs_pic = blank_pic.copy()
        else:
            fs_pic = Image.open(UI_DIR / f"{self.grade.fs}.png").convert("RGBA")
            fs_pic = fs_pic.resize((grade_pic_size, grade_pic_size), Image.LANCZOS)
        content.alpha_composite(fs_pic, (grade_pic_size + pic_padding, y))

        # star icons
        star_pic_size = 16
        star_pad_x = 7
        star_pad_y = 6
        x_off = 4

        star_score = int(self.grade.dxScore / self.grade.max_dxScore * 10000) / 100
        star_count = 0
        for i in range(len(STAR_DXRATE_LIST)):
            if star_score > STAR_DXRATE_LIST[i]:
                star_count = i + 1
        if star_count > 7:
            star_count = 7
        star_pic = Image.new("RGBA", (star_pic_size * 4 + 10, star_pic_size * 2 + 10))

        Ox = (grade_pic_size + pic_padding) * 2 + (content.width - (grade_pic_size + pic_padding) * 2) // 2
        Oy = y + grade_pic_size // 2
        Cx = star_pic.width // 2
        Cy = star_pic.height // 2
        Coff = star_pic_size // 2 
        single_star_ui = Image.open(STAR_FILE_LIST[star_count]).convert("RGBA")
        single_star_ui = single_star_ui.resize((star_pic_size, star_pic_size), Image.LANCZOS)

        if star_count == 0:
            pass
        elif star_count == 1:
            star_pic.alpha_composite(single_star_ui, (Cx, Cy))
        elif star_count == 2:
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x, Cy))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x, Cy))
        elif star_count == 3:
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx, Cy - star_pad_y))
        elif star_count == 4:
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x * 2, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x, Cy - star_pad_y))
        elif star_count == 5:
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x * 2, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x * 2, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x, Cy - star_pad_y))
        elif star_count == 6:
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x * 2, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x * 2, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x * 3, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x, Cy + star_pad_y))
        else: # star_count == 7
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x * 2, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x * 2, Cy - star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x * 3, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx - star_pad_x, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x, Cy + star_pad_y))
            star_pic.alpha_composite(single_star_ui, (Cx + star_pad_x * 3, Cy + star_pad_y))

        content.alpha_composite(star_pic, (Ox - Cx - Coff - x_off, Oy - Cy - Coff))

        return content

    def _draw_badge(self) -> Image.Image:
        text_y_off = 5

        size = self.badge_R * 2
        d = self.badge_R / (1 + 2 ** 0.5)
        points = [
            (d, 0),
            (size - d, 0),
            (size, d),
            (size, size - d),
            (size - d, size),
            (d, size),
            (0, size - d),
            (0, d),
        ]

        badge = Image.new("RGBA", (size, size))
        draw = ImageDraw.Draw(badge)
        draw.polygon(points, fill=self.cols[1] + (255,))

        diff_text = f"{self.grade.diff:.1f}"
        bbox = draw.textbbox((0, 0), diff_text, font=self.font_diff)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        draw.text(
            ((size - w) // 2, (size - h) // 2 - text_y_off),
            diff_text,
            font=self.font_diff,
            fill=self.col_font
        )
        return shadowed(badge, offset=(2, 2), blur=1, scale=1.0, color=(0, 0, 0, 100))

class UserCard:
    W: int = CONFIG['user_card']['W']
    H: int = CONFIG['user_card']['H']
    margin: dict[str, int] = CONFIG['user_card']['plate_margin']

    def __init__(self, user: UserInfo):
        self.user = user

        self.name_font = Font.get("SourceHanSans-Bold.otf", 32)
        self.ra_font = Font.get("MapleMono-CN-Medium.ttf", 22)

        self.col_font = (31, 30, 51, 255)
        self.font_ra_color = (255, 215, 0, 255) # gold

    def render(self) -> Image.Image:
        img = Image.new("RGBA", (self.W + 10, self.H + 10))
        x = 0
        y = 0

        plate = self._draw_plate()
        img.alpha_composite(plate, (x, (self.H - plate.height) // 2))

        x += self.margin['left']
        y += (self.H - plate.height) // 2
        avatar = self._draw_avatar()
        img.alpha_composite(avatar, (x, (self.H - avatar.height) // 2 - 2))

        x += avatar.width + 16
        y += self.margin['top']
        ra = self._draw_ra()
        img.alpha_composite(ra, (x, y))

        y += ra.height
        name = self._draw_name()
        img.alpha_composite(name, (x, y))

        y += name.height
        ra_detail = self._draw_detail()
        img.alpha_composite(ra_detail, (x, y))

        return img

    def _draw_logo(self) -> Image.Image:
        pic_size = 200

        logo = Image.open(PIC_DIR / "logo.png").convert("RGBA")
        logo = logo.resize((pic_size, pic_size), Image.LANCZOS)
        return logo
        # return shadowed(logo, offset=(2, 2), blur=2, scale=1.0, color=(0, 0, 0, 80))
    
    def _draw_plate(self) -> Image.Image:
        pic_h = self.H - 30
        bg = Image.open(PLATE_DIR / "00613X.png").convert("RGBA")
        rat = bg.width / bg.height
        pic_w = int(pic_h * rat)
        plate = bg.resize((pic_w, pic_h), Image.LANCZOS)
        # return plate
        return shadowed(plate, offset=(4, 4), blur=2, scale=1.0, color=(0, 0, 0, 100))

    def _draw_avatar(self) -> Image.Image:
        pic_size = self.H - 50

        avatar = Image.open(AVATAR_DIR / "309503.png").convert("RGBA")
        avatar = avatar.resize((pic_size, pic_size), Image.LANCZOS)
        return avatar

    def _draw_ra(self) -> Image.Image:
        ra_h = 50

        rating = self.user.rating
        ra_file = RATING_FILE_DICT[0]
        for r in sorted(RATING_FILE_DICT.keys(), reverse=True):
            if rating >= r:
                ra_file = RATING_FILE_DICT[r]
                break
        ra_img = Image.open(ra_file).convert("RGBA")
        rat = ra_img.width / ra_img.height
        ra_w = int(ra_h * rat)
        ra_img = ra_img.resize((ra_w, ra_h), Image.LANCZOS)
    
        text_img = Image.new("RGBA", ra_img.size)
        num = []
        ra_str = str(rating)
        for i in range(len(ra_str), 5):
            num.append("")
        for c in ra_str:
            num.append(c)

        text_padding = 18.7
        text_size = 26
        for i, c in enumerate(num):
            x = int(i * text_padding)
            if c == "":
                continue
            num_img = Image.open(UI_DIR / f"{c}.png").convert("RGBA")
            ratio = num_img.width / num_img.height
            num_img = num_img.resize((int(text_size * ratio), text_size), Image.LANCZOS)
            text_img.alpha_composite(num_img, (x, 0))
        x = int(ra_img.width * 0.485)
        y = int(ra_img.height * 0.26)
        ra_img.alpha_composite(text_img, (x, y))

        return ra_img

    def _draw_name(self) -> Image.Image:
        box_w = 300
        box_h = 50
        box_r = 12 # corner radius
        text_x_pad = 4
        text_y_pad = -2
        box = Image.new("RGBA", (box_w, box_h))

        ImageDraw.Draw(box).rounded_rectangle(
            (0, 0, box_w, box_h),
            radius=box_r,
            fill=(255, 255, 255, 180)
        )

        ImageDraw.Draw(box).text(
            (text_x_pad, text_y_pad),
            self.user.name,
            font=self.name_font,
            fill=self.col_font
        )

        return box

    def _draw_detail(self) -> Image.Image:
        box_w = 375
        box_h = 30
        box_r = 8
        text_x_pad = 4
        text_y_pad = 0
        box = Image.new("RGBA", (box_w, box_h))

        ImageDraw.Draw(box).rounded_rectangle(
            (0, 0, box_w, box_h),
            radius=box_r,
            fill=(170, 204, 255, 60)
        )

        text = f"b35 {self.user.ra35} + b15 {self.user.ra15} = {self.user.rating}"
        ImageDraw.Draw(box).text(
            (text_x_pad, text_y_pad),
            text,
            font=self.ra_font,
            fill=self.col_font
        )
        return box

class Canvas:
    W: int = CONFIG['canvas']['W']
    H: int = CONFIG['canvas']['H']
    user_score_gap: int = CONFIG['canvas']['user_score_gap']
    sd_dx_gap: int = CONFIG['canvas']['15_35_gap']
    card_gap: int = CONFIG['canvas']['card_gap']
    margin: dict[str, int] = CONFIG['canvas']['margin']
    logo_size: int = CONFIG['logo_size']

    def __init__(self):
        self.img = Image.new("RGBA", (self.W, self.H))
        self.draw = ImageDraw.Draw(self.img)
        self.paste = self.img.paste

        self.footer_font = Font.get("MapleMono-CN-Medium.ttf", 20)

        self.col_font = PIC_FOOTER_COL
    
    def render(self, user: UserInfo, b35: list[GradeInfo], b15: list[GradeInfo]) -> Image.Image:
        self._draw_bg()
        self._draw_logo()
        self._draw_user_card(user)
        self._draw_b35(b35)
        self._draw_b15(b15)
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

    def _draw_logo(self):
        logo = Image.open(PIC_DIR / "logo.png").convert("RGBA")
        logo = logo.resize((self.logo_size, self.logo_size), Image.LANCZOS)
        self.paste(logo, (self.margin['left'], self.margin['top']), logo)

    def _draw_user_card(self, user: UserInfo):
        card = UserCard(user)
        img = card.render()
        self.paste(img, (self.margin['left'] + self.logo_size + 20, self.margin['top']), img)
    
    def _draw_b35(self, grades: list[GradeInfo]):
        grids = Grid(
            width=self.W - self.margin['left'] - self.margin['right'],
            height=self.card_gap * 6 + ScoreCard.H * 7,
            element_w=[ScoreCard.W] * 5,
            element_h=[ScoreCard.H] * 7
        )
        positions = grids.places(len(grades))
        origin = (
            self.margin['left'],
            self.margin['top'] + self.user_score_gap + UserCard.H
        )
        for grade, (x, y) in zip(grades, positions):
            card = ScoreCard(grade)
            img = card.render()
            self.paste(img, (origin[0] + x, origin[1] + y), img)

    def _draw_b15(self, grades: list[GradeInfo]):
        grids = Grid(
            width=self.W - self.margin['left'] - self.margin['right'],
            height=self.card_gap * 2 + ScoreCard.H * 3,
            element_w=[ScoreCard.W] * 5,
            element_h=[ScoreCard.H] * 3
        )
        positions = grids.places(len(grades))
        origin = (
            self.margin['left'],
            self.margin['top'] + self.user_score_gap + UserCard.H + self.card_gap * 6 + ScoreCard.H * 7 + self.sd_dx_gap
        )
        for grade, (x, y) in zip(grades, positions):
            card = ScoreCard(grade)
            img = card.render()
            self.paste(img, (origin[0] + x, origin[1] + y), img)
    
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

def generateB50(data: dict) -> Image.Image:
    user_info = UserInfo(data)
    b35_info = [GradeInfo(s, i + 1) for i, s in enumerate(data['charts']['sd'])]
    b15_info = [GradeInfo(s, i + 1) for i, s in enumerate(data['charts']['dx'])]

    canvas = Canvas()
    img = canvas.render(user_info, b35_info, b15_info)
    return img