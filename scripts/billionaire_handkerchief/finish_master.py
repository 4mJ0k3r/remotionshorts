"""Create the labeled review sheet and measure color from its source frames."""
import json
from statistics import mean

from PIL import Image, ImageDraw, ImageStat

from mux_preview import OUT
from shots import MASTER_CALIBRATION


def make_sheet():
    directory = OUT / 'calibration_v3_polished'
    progress = json.loads((directory / 'progress.json').read_text())
    assert progress['state'] == 'complete' and progress['frames'] == list(MASTER_CALIBRATION)
    tile_width, tile_height, label_height = 240, 427, 23
    columns, rows = 7, 3
    sheet = Image.new('RGB', (columns * tile_width, rows * (tile_height + label_height)), '#151522')
    draw = ImageDraw.Draw(sheet)
    samples = {}
    for index, frame in enumerate(MASTER_CALIBRATION):
        x = index % columns * tile_width
        y = index // columns * (tile_height + label_height)
        with Image.open(directory / f'{frame:04d}.png') as still:
            assert still.size == (540, 960), (frame, still.size)
            rgb = still.convert('RGB')
            samples[frame] = (ImageStat.Stat(rgb.convert('L')).mean[0], ImageStat.Stat(rgb.convert('HSV')).mean[1])
            sheet.paste(rgb.resize((tile_width, tile_height), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 8, y + tile_height + 4), f'FRAME {frame:04d}', fill='white')
    sheet.save(OUT / 'sheet_v3.jpg', quality=94, subsampling=0)
    luma, saturation = (round(mean(values), 1) for values in zip(*samples.values()))
    report = {'mean_luma': luma, 'mean_hsv_saturation': saturation, 'by_frame': samples}
    (directory / 'color_checks.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    make_sheet()
