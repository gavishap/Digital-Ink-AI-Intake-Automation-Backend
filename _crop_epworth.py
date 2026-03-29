"""Crop and save Epworth table sections for differential extraction."""
from pathlib import Path
from PIL import Image

TEMPLATES = Path("templates")
OUT = Path("report_learning/outputs/page3_retest")
OUT.mkdir(parents=True, exist_ok=True)

filled = Image.open("report_learning/outputs/e2e_v2/stage1_split/bachar_page_images/page_004.png")
blank  = Image.open(TEMPLATES / "orofacial_exam_blank_page_11.png")

fw, fh = filled.size  # 2108 x 2768
bw, bh = blank.size   # 2125 x 2750

# Filled page_004: Epworth title starts ~5%, table ends ~42%
filled_crop = filled.crop((0, int(fh * 0.05), fw, int(fh * 0.42)))
# Blank page_11: Epworth table is at the bottom ~58%–100%
blank_crop  = blank.crop( (0, int(bh * 0.58), bw, bh))

filled_crop.save(OUT / "epworth_filled_crop.png")
blank_crop.save( OUT / "epworth_blank_crop.png")

print(f"Filled crop: {filled_crop.size}")
print(f"Blank  crop: {blank_crop.size}")
