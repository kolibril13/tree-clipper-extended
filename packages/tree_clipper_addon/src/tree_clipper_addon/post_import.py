import bpy

from ._vendor.tree_clipper.import_nodes import ImportReport

TREE_TYPE_TO_GROUP_TYPE = {
    bpy.types.CompositorNodeTree: bpy.types.CompositorNodeGroup,
    bpy.types.GeometryNodeTree: bpy.types.GeometryNodeGroup,
    bpy.types.ShaderNodeTree: bpy.types.ShaderNodeGroup,
    bpy.types.TextureNodeTree: bpy.types.TextureNodeGroup,
}


def post_import(
    *,
    context: bpy.types.Context,
    event: bpy.types.Event,
    report: ImportReport,
    unpack: bool = False,
) -> None:
    def add_unpacked() -> str | None:
        if not isinstance(context.space_data, bpy.types.SpaceNodeEditor):
            return "Not a node editor."

        space = context.space_data
        target_tree = space.edit_tree
        if target_tree is None:
            return "No active tree to attach to."

        assert report.last_getter is not None
        imported_root = report.last_getter()

        if target_tree.bl_rna.identifier != imported_root.bl_rna.identifier:  # ty:ignore[unresolved-attribute]
            return f"Editor type is {target_tree.bl_rna.identifier}, but imported {imported_root.bl_rna.identifier}."  # ty:ignore[unresolved-attribute]

        # Only a reusable node-group datablock can be unpacked; an embedded
        # tree (e.g. a material's node tree) has no entry here and stays grouped.
        if imported_root.name not in bpy.data.node_groups:
            return "Imported tree is embedded (not a node group); cannot unpack it onto the canvas."

        # The group interface nodes only make sense inside a group; once the
        # contents are pasted loose into an existing tree they're just noise, so
        # drop them (and their now-dangling links) before copying.
        for node in list(imported_root.nodes):  # ty:ignore[unresolved-attribute]
            if node.bl_idname in {"NodeGroupInput", "NodeGroupOutput"}:
                imported_root.nodes.remove(node)  # ty:ignore[unresolved-attribute]

        # Reproduce the imported nodes in the active tree via Blender's own node
        # clipboard, so links, nested groups and every property come across
        # faithfully. We briefly push the imported root onto the editor path to
        # copy from it, then pop back so the user's current location is restored.
        try:
            space.path.append(imported_root)  # ty:ignore[possibly-missing-attribute]
            try:
                for node in imported_root.nodes:  # ty:ignore[unresolved-attribute]
                    node.select = True
                bpy.ops.node.clipboard_copy()
            finally:
                space.path.pop()  # ty:ignore[possibly-missing-attribute]
        except RuntimeError as exception:
            return f"Could not copy imported nodes: {exception}"

        for node in target_tree.nodes:  # ty:ignore[unresolved-attribute]
            node.select = False

        bpy.ops.node.clipboard_paste()

        # Move the freshly pasted (and selected) nodes so their center sits at the
        # mouse cursor. We only shift parentless nodes so framed nodes aren't moved
        # twice. The region->view conversion and ui_scale division mirror the
        # single-group placement in add_as_group (node space = view space / ui_scale).
        pasted_roots = [
            node
            for node in target_tree.nodes  # ty:ignore[unresolved-attribute]
            if node.select and node.parent is None
        ]
        if pasted_roots:
            target = context.region.view2d.region_to_view(  # ty:ignore[possibly-missing-attribute]
                event.mouse_region_x, event.mouse_region_y
            )
            ui_scale = context.preferences.system.ui_scale  # ty:ignore[possibly-missing-attribute]
            target_x = target[0] / ui_scale
            target_y = target[1] / ui_scale

            center_x = (
                min(node.location.x for node in pasted_roots)
                + max(node.location.x for node in pasted_roots)
            ) / 2
            center_y = (
                min(node.location.y for node in pasted_roots)
                + max(node.location.y for node in pasted_roots)
            ) / 2

            offset_x = target_x - center_x
            offset_y = target_y - center_y
            for node in pasted_roots:
                node.location.x += offset_x
                node.location.y += offset_y

        # The root group only existed to ferry the nodes across; the pasted nodes
        # are now independent in the active tree. Nested groups are referenced, not
        # owned by it, so they survive its removal.
        bpy.data.node_groups.remove(imported_root)  # ty:ignore[invalid-argument-type]

        # leave the user in a grab so they can reposition before dropping
        bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")

    def add_as_group() -> str | None:
        if not isinstance(context.space_data, bpy.types.SpaceNodeEditor):
            return "Not a node editor."

        node_tree = context.space_data.edit_tree
        if node_tree is None:
            return "No active tree to attach to."

        assert report.last_getter is not None
        imported_root = report.last_getter()

        if node_tree.bl_rna.identifier != imported_root.bl_rna.identifier:  # ty:ignore[unresolved-attribute]
            return f"Editor type is {node_tree.bl_rna.identifier}, but imported {imported_root.bl_rna.identifier}."  # ty:ignore[unresolved-attribute]

        group = node_tree.nodes.new(
            type=TREE_TYPE_TO_GROUP_TYPE[type(imported_root)].bl_rna.identifier,  # ty:ignore[possibly-missing-attribute]
        )
        group.node_tree = imported_root  # ty:ignore[unresolved-attribute]

        # fix offset
        group.location = context.region.view2d.region_to_view(  # ty:ignore[possibly-missing-attribute, invalid-assignment]
            event.mouse_region_x, event.mouse_region_y
        )

        # account for DPI settings
        group.location /= context.preferences.system.ui_scale  # ty:ignore[possibly-missing-attribute]

        # otherwise the others will be moved as well
        for node in node_tree.nodes:
            node.select = False
        group.select = True

        bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")

    failure_reason = add_unpacked() if unpack else add_as_group()
    if failure_reason is not None:

        def warn_popup():
            def draw(self, context: bpy.types.Context):
                self.layout.label(text="The import succeeded! 🎉")
                self.layout.label(text="Could not attached the root to current editor:")
                self.layout.label(text=failure_reason)
                self.layout.separator()
                self.layout.label(text="Please check the INFO for the imported trees.")

            bpy.context.window_manager.popup_menu(  # ty:ignore[possibly-missing-attribute]
                draw, title="Where's My Import?", icon="INFO"
            )

        # we need to defer, otherwise Blender crashes
        bpy.app.timers.register(warn_popup)
