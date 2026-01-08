import bpy


class TreeClipperPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    max_clipboard_bytes: bpy.props.IntProperty(
        name="Max Clipboard Bytes",
        description="""Maximum clipboard size in bytes (UTF-8 encoded).

The export fails (safely) if the limit is exceeded.
If this setting is beyond your system's capabilities,
Blender might crash on export.

The default value is somewhat conservative, but not guaranteed to be safe.""",
        default=240_000,
    )  # type: ignore

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.prop(self, "max_clipboard_bytes")


def get_max_clipboard_bytes():
    return bpy.context.preferences.addons.get(
        __package__  # ty:ignore[invalid-argument-type]
    ).preferences.max_clipboard_bytes  # ty:ignore[possibly-missing-attribute]
