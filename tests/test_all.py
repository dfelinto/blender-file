# -*- coding: utf-8 -*-
"""Unitests for blender_format"""

import os
import blendfile

# Utils

def get_sample_filepath(filepath):
    """Return the full path of the sample file"""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, 'samples', filepath)


def listbase_iter(data, struct, listbase):
    element = data.get_pointer((struct, listbase, b'first'))
    while element is not None:
        yield element
        element = element.get_pointer(b'next')


def idprop_group_iter(idprops, ):
    return listbase_iter(idprops, b'data', b'group')


def views_iter(scene):
    """Return an iterator for all views of scene"""
    return listbase_iter(scene, b'r', b'views')


def query_main_scene(filepath, callbacks):
    """Return the equivalent to bpy.context.scene"""
    with blendfile.open_blend(filepath) as blend:
        # There is no bpy.context.scene, we get it from the main window
        window_manager = [block for block in blend.blocks if block.code == b'WM'][0]
        window = window_manager.get_pointer(b'winactive')
        screen = window.get_pointer(b'screen')
        scene = screen.get_pointer(b'scene')

        output = []
        for callback in callbacks:
            output.append(callback(scene))
        return output

# Main tests

def test_scene_name():
    def get_name(scene):
        return scene.get((b'id', b'name'))

    filepath = get_sample_filepath("monkeys.blend")
    scene_name, = query_main_scene(filepath, [get_name])

    # 'SC猿のシーン'
    assert scene_name == u'SC\u733f\u306e\u30b7\u30fc\u30f3'


def test_scene_frames():
    def get_frame_start(scene):
        return scene.get((b'r', b'sfra'))

    def get_frame_end(scene):
        return scene.get((b'r', b'efra'))

    def get_frame_current(scene):
        return scene.get((b'r', b'cfra'))

    filepath = get_sample_filepath("monkeys.blend")
    frame_start, frame_end, frame_current = query_main_scene(filepath, [
        get_frame_start,
        get_frame_end,
        get_frame_current,
        ])

    assert frame_start == 1
    assert frame_end == 250
    assert frame_current == 101


def test_scene_resolution():
    def get_resolution_x(scene):
        return scene.get((b'r', b'xsch'))

    def get_resolution_y(scene):
        return scene.get((b'r', b'ysch'))

    filepath = get_sample_filepath("monkeys.blend")
    resolution_x, resolution_y = query_main_scene(filepath, [
        get_resolution_x,
        get_resolution_y,
        ])

    assert resolution_x == 1920
    assert resolution_y == 1080


def test_camera():
    def get_camera_name(scene):
        camera = scene.get_pointer(b'camera')
        assert camera
        return camera.get((b'id', b'name'))

    def get_camera_lens(scene):
        camera = scene.get_pointer(b'camera')
        assert camera
        camera_data = camera.get_pointer(b'data')
        return camera_data.get(b'lens')

    filepath = get_sample_filepath("monkeys.blend")
    camera_name, camera_lens = query_main_scene(filepath, [
        get_camera_name,
        get_camera_lens,
        ])

    assert camera_name == 'OBMainCamera'
    assert "{0:4.2f}".format(camera_lens) == "37.22"


def test_views():
    def get_views_name_status(scene):
        name_status = []
        for view in views_iter(scene):
            name_status.append((
                view.get(b'name'),
                view.get(b'viewflag'),
                ))
        return name_status

    filepath = get_sample_filepath("monkeys.blend")
    views_data, = query_main_scene(filepath, [get_views_name_status])

    assert len(views_data) == 4
    assert views_data[3][0] == "south"
    assert views_data[2][0] == u'\u5317' # '北'
    assert (views_data[2][1] & (1 << 0)) != 0
    assert (views_data[3][1] & (1 << 0)) == 0


def test_cycles_samples():
    def get_samples(scene):
        # get custom properties
        properties = scene.get_pointer((b'id', b'properties'))

        if properties is None:
            return -1

        # iterate through all the property groups
        for itor in idprop_group_iter(properties):
            if itor.get(b'name') == "cycles":
                for itor2 in idprop_group_iter(itor):
                    if itor2.get(b'name') == "samples":
                        return itor2.get((b'data', b'val'))

    filepath = get_sample_filepath("monkeys.blend")
    samples, = query_main_scene(filepath, [get_samples])
    assert samples == 72

