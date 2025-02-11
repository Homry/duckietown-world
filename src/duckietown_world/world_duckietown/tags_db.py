import os

import yaml
from PIL import Image
from six import BytesIO

from duckietown_serialization_ds1 import Serializable
from duckietown_world import logger, PlacedObject
from duckietown_world.utils import memoized_reset

# DEFAULT_FAMILY = '36h11'


__all__ = ["get_apriltagsDB_raw", "get_sign_type_from_tag_id", "FloorTag"]


class TagInstance(Serializable):
    def __init__(self, tag_id, family, size):
        self.tag_id = tag_id
        self.family = family
        self.size = size
        f = family.replace("h", "_")
        texture = f"tag{f}_{tag_id:05d}"
        try:
            from duckietown_world.world_duckietown.map_loading import get_texture_file

            self.fn = get_texture_file(texture)[0]
        except KeyError:
            msg = f"Cannot find april tag image for {texture}"
            logger.warning(msg)
            self.fn = None

    def draw_svg(self, drawing, g):
        # L = self.size
        # rect = drawing.rect(insert=insert,(-L / 2, -L / 2),
        #                     size=(L, L),
        #                     fill="white",
        #                     # style='opacity:0.4',
        #                     stroke_width="0.005",
        #                     stroke="black", )
        # g.add(rect)
        if self.fn:
            with Image.open(self.fn) as _:
                image = _.convert("RGB")
            image = image.resize((64, 64), resample=Image.NEAREST)
            out = BytesIO()
            image.save(out, format="png")
            texture = out.getvalue()

            from duckietown_world import data_encoded_for_src

            href = data_encoded_for_src(texture, "image/png")
            T = self.size
            insert = (-T / 2, -T / 2)

            img = drawing.image(
                href=href,
                size=(T, T),
                insert=insert,
                style="transform: rotate(90deg) scaleX(-1)  rotate(-90deg) ",
            )
            img.attribs["class"] = "tile-textures"
            g.add(img)


class FloorTag(PlacedObject):
    def __init__(self, tag=None, **kwargs):
        # noinspection PyArgumentList
        PlacedObject.__init__(self, **kwargs)
        self.tag = tag

    def draw_svg(self, drawing, g):
        self.tag.draw_svg(drawing, g)


@memoized_reset
def get_apriltagsDB_raw():
    abs_path_module = os.path.realpath(__file__)
    module_dir = os.path.dirname(abs_path_module)

    fn = os.path.join(module_dir, "../data/apriltagsDB.yaml")
    with open(fn) as _:
        d = _.read()
    return yaml.load(d, Loader=yaml.Loader)


def get_sign_type_from_tag_id(tag_id):
    tag_id = int(tag_id)
    db = get_apriltagsDB_raw()
    # logger.debug(set(_['traffic_sign_type'] for _ in db))
    # logger.debug(set(_['tag_type'] for _ in db))

    #
    #       street_name: BLUM ST.
    #       vehicle_name:
    #       traffic_sign_type:

    from .other_objects import get_canonical_sign_name

    for entry in db:
        if entry["tag_id"] == tag_id:
            tstype = entry["traffic_sign_type"]
            return get_canonical_sign_name(tstype)
    raise KeyError(tag_id)
