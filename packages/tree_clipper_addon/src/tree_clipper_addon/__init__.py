# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

from .operators_export import (
    Tree_Clipper_Extended_External_Export_Item,
    SCENE_UL_Tree_Clipper_Extended_External_Export_List,
    SCENE_OT_Tree_Clipper_Extended_Export_Cache,
    SCENE_OT_Tree_Clipper_Extended_Export_Modal,
    SCENE_OT_Tree_Clipper_Extended_Export_Prepare,
)

from .operators_import import (
    Tree_Clipper_Extended_External_Import_Item,
    Tree_Clipper_Extended_External_Import_Items,
    SCENE_UL_Tree_Clipper_Extended_External_Import_List,
    SCENE_OT_Tree_Clipper_Extended_Import_Cache,
    SCENE_OT_Tree_Clipper_Extended_Import_File_Prepare,
    SCENE_OT_Tree_Clipper_Extended_Import_Clipboard_Prepare,
    SCENE_OT_Tree_Clipper_Extended_Paste_As_Nodes,
    SCENE_OT_Tree_Clipper_Extended_Import_Modal,
)

from .panel import SCENE_PT_Tree_Clipper_Extended_Panel

from .preferences import TreeClipperExtendedPreferences

classes = [
    Tree_Clipper_Extended_External_Export_Item,
    SCENE_UL_Tree_Clipper_Extended_External_Export_List,
    SCENE_OT_Tree_Clipper_Extended_Export_Cache,
    SCENE_OT_Tree_Clipper_Extended_Export_Modal,
    SCENE_OT_Tree_Clipper_Extended_Export_Prepare,
    Tree_Clipper_Extended_External_Import_Item,
    Tree_Clipper_Extended_External_Import_Items,
    SCENE_UL_Tree_Clipper_Extended_External_Import_List,
    SCENE_OT_Tree_Clipper_Extended_Import_Modal,
    SCENE_OT_Tree_Clipper_Extended_Import_Cache,
    SCENE_OT_Tree_Clipper_Extended_Import_File_Prepare,
    SCENE_OT_Tree_Clipper_Extended_Import_Clipboard_Prepare,
    SCENE_OT_Tree_Clipper_Extended_Paste_As_Nodes,
    SCENE_PT_Tree_Clipper_Extended_Panel,
    TreeClipperExtendedPreferences,
]


def register() -> None:
    print("Registering Tree Clipper Extended")
    for cls in classes:
        bpy.utils.register_class(cls)
    # the pointer properties in the items make it impossible to store on the operator
    bpy.types.Scene.tree_clipper_extended_external_import_items = bpy.props.PointerProperty(  # ty: ignore[unresolved-attribute]
        type=Tree_Clipper_Extended_External_Import_Items
    )


def unregister() -> None:
    del bpy.types.Scene.tree_clipper_extended_external_import_items  # ty: ignore[unresolved-attribute]
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
