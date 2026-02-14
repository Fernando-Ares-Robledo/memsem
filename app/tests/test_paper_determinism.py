from app.core.paper_model import PaperModel
from app.core.rendering import RenderColors, render_sector_thumbnail_rgb


def test_preset_identical_sector_signatures():
    model = PaperModel()
    assert model.sector_signature(0) == model.sector_signature(12)
    assert model.sector_signature(7) == model.sector_signature(10)
    assert model.sector_signature(5) == model.sector_signature(8)


def test_preset_identical_sector_thumbnails():
    model = PaperModel()
    colors = RenderColors()
    img0 = render_sector_thumbnail_rgb(model, 0, colors, 1)
    img12 = render_sector_thumbnail_rgb(model, 12, colors, 1)
    assert img0.shape == img12.shape
    assert (img0 == img12).all()
