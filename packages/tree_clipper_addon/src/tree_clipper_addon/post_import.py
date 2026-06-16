import bpy

from ._vendor.tree_clipper.import_nodes import ImportReport

TREE_TYPE_TO_GROUP_TYPE = {
    bpy.types.CompositorNodeTree: bpy.types.CompositorNodeGroup,
    bpy.types.GeometryNodeTree: bpy.types.GeometryNodeGroup,
    bpy.types.ShaderNodeTree: bpy.types.ShaderNodeGroup,
    bpy.types.TextureNodeTree: bpy.types.TextureNodeGroup,
}

GROUP_IO_IDNAMES = {"NodeGroupInput", "NodeGroupOutput"}


def _merge_interface(
    src_tree: bpy.types.NodeTree, dst_tree: bpy.types.NodeTree
) -> dict[str, str]:
    """Copy ``src_tree``'s interface onto ``dst_tree`` and return a map from each
    source interface item identifier to the matching identifier on ``dst_tree``.

    Blender's node clipboard cannot carry a tree interface, so when the imported
    nodes are pasted loose into the active tree their Group Input/Output nodes
    would otherwise bind to the target tree's interface. We append the imported
    sockets (reusing pre-existing ones so a second paste doesn't pile up
    duplicates) and hand back the mapping so the group-io links can be rebuilt.

    We deliberately work with identifier strings rather than item references:
    adding interface items can invalidate previously fetched Python wrappers.
    """
    src_iface = src_tree.interface
    dst_iface = dst_tree.interface
    assert src_iface is not None and dst_iface is not None

    # Snapshot the sockets that already existed on the target as plain data and
    # consume each match once, so repeated names (e.g. several "Scale" inputs)
    # still map to distinct sockets.
    existing = [
        (item.identifier, (item.name, item.in_out, item.socket_type))
        for item in dst_iface.items_tree
        if item.item_type == "SOCKET"
    ]
    consumed: set[str] = set()

    def match_existing(key: tuple) -> str | None:
        for identifier, existing_key in existing:
            if identifier in consumed:
                continue
            if existing_key == key:
                consumed.add(identifier)
                return identifier
        return None

    def find_panel(identifier: str) -> bpy.types.NodeTreeInterfacePanel | None:
        for item in dst_iface.items_tree:
            if item.item_type == "PANEL" and item.identifier == identifier:
                return item  # ty:ignore[invalid-return-type, unresolved-attribute]
        return None

    iface_map: dict[str, str] = {}
    panel_map: dict[str, str] = {}  # src panel identifier -> dst panel identifier

    for item in src_iface.items_tree:
        parent_dst_id: str | None = None
        if item.parent is not None and item.parent.index >= 0:
            parent_dst_id = panel_map.get(item.parent.identifier)  # ty:ignore[unresolved-attribute]

        if item.item_type == "PANEL":
            new_panel = dst_iface.new_panel(
                name=item.name,
                description=item.description,
                default_closed=item.default_closed,
            )
            new_identifier = new_panel.identifier  # ty:ignore[unresolved-attribute]
            if parent_dst_id is not None:
                parent = find_panel(parent_dst_id)
                if parent is not None:
                    dst_iface.move_to_parent(
                        item=new_panel,
                        parent=parent,
                        to_position=len(parent.interface_items),
                    )
            panel_map[item.identifier] = new_identifier
            iface_map[item.identifier] = new_identifier
            continue

        matched = match_existing((item.name, item.in_out, item.socket_type))
        if matched is not None:
            iface_map[item.identifier] = matched
            continue

        parent = find_panel(parent_dst_id) if parent_dst_id is not None else None
        new_socket = dst_iface.new_socket(
            name=item.name,
            description=item.description,
            in_out=item.in_out,
            socket_type=item.socket_type,
            parent=parent,
        )
        iface_map[item.identifier] = new_socket.identifier

    return iface_map


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

        def is_group_io(node: bpy.types.Node) -> bool:
            return node.bl_idname in GROUP_IO_IDNAMES

        # A self-contained group carries its own interface *and* Group
        # Input/Output nodes. Pasted loose it would duplicate the host tree's
        # interface nodes, blend unrelated interface sockets together and leave a
        # dead "Unused Output", so such content belongs in a group node: hand it
        # to the grouped path instead of unpacking it.
        interface = imported_root.interface  # ty:ignore[unresolved-attribute]
        if (
            interface is not None
            and len(interface.items_tree) > 0
            and any(is_group_io(node) for node in imported_root.nodes)  # ty:ignore[unresolved-attribute]
        ):
            return add_as_group()

        # Selection is expressed by what's present in the magic string: the web
        # renderer filters unselected nodes out on copy, so any Group Input/Output
        # node that survived into the import was meant to come across. We keep them
        # (with the group's interface) whenever they're present, and otherwise
        # skip the interface merge so we don't pollute the target tree.
        keep_group_io = any(
            is_group_io(node)
            for node in imported_root.nodes  # ty:ignore[unresolved-attribute]
        )

        # The clipboard can't carry a tree interface or its Group Input/Output
        # links, so when we keep those nodes we capture both before copying. We
        # tag every imported node with a unique sentinel name (the clipboard
        # preserves unique names) to pair it with its pasted copy afterwards, and
        # record each link touching a group-io node to rebuild once the interface
        # is in place.
        sentinel_prefix = "_tc_unpack_sentinel_"
        original_names: dict[str, str] = {}
        # (from_sentinel, from_socket_id, from_via_iface,
        #  to_sentinel, to_socket_id, to_via_iface)
        group_io_links: list[tuple[str, str, bool, str, str, bool]] = []
        if keep_group_io:
            for index, node in enumerate(imported_root.nodes):  # ty:ignore[unresolved-attribute]
                sentinel = f"{sentinel_prefix}{index}"
                original_names[sentinel] = node.name
                node.name = sentinel

            for link in imported_root.links:  # ty:ignore[unresolved-attribute]
                if not (is_group_io(link.from_node) or is_group_io(link.to_node)):
                    continue
                group_io_links.append(
                    (
                        link.from_node.name,
                        link.from_socket.identifier,
                        is_group_io(link.from_node),
                        link.to_node.name,
                        link.to_socket.identifier,
                        is_group_io(link.to_node),
                    )
                )

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
            for sentinel, name in original_names.items():
                imported_root.nodes[sentinel].name = name  # ty:ignore[unresolved-attribute]
            return f"Could not copy imported nodes: {exception}"

        for node in target_tree.nodes:  # ty:ignore[unresolved-attribute]
            node.select = False

        bpy.ops.node.clipboard_paste()

        # Bring the imported group's interface onto the target tree so the pasted
        # Group Input/Output nodes expose the right sockets, then rebuild the
        # links the clipboard dropped. Sentinel names still identify the freshly
        # pasted nodes at this point; we restore the original names afterwards.
        if keep_group_io:
            iface_map = _merge_interface(imported_root, target_tree)  # ty:ignore[invalid-argument-type]
            pasted_by_sentinel = {
                node.name: node
                for node in target_tree.nodes  # ty:ignore[unresolved-attribute]
                if node.name in original_names
            }

            def resolve_socket(
                node: bpy.types.Node,
                socket_id: str,
                *,
                want_input: bool,
                via_iface: bool,
            ) -> bpy.types.NodeSocket | None:
                if via_iface:
                    mapped = iface_map.get(socket_id)
                    if mapped is None:
                        return None
                    socket_id = mapped
                sockets = node.inputs if want_input else node.outputs
                for socket in sockets:
                    if socket.identifier == socket_id:
                        return socket
                return None

            for (
                from_sentinel,
                from_socket_id,
                from_via_iface,
                to_sentinel,
                to_socket_id,
                to_via_iface,
            ) in group_io_links:
                from_node = pasted_by_sentinel.get(from_sentinel)
                to_node = pasted_by_sentinel.get(to_sentinel)
                if from_node is None or to_node is None:
                    continue
                from_socket = resolve_socket(
                    from_node, from_socket_id, want_input=False, via_iface=from_via_iface
                )
                to_socket = resolve_socket(
                    to_node, to_socket_id, want_input=True, via_iface=to_via_iface
                )
                if from_socket is not None and to_socket is not None:
                    target_tree.links.new(from_socket, to_socket)  # ty:ignore[unresolved-attribute]

            # Hand the user-facing names back to the pasted nodes (Blender
            # resolves any collisions with existing nodes automatically).
            for sentinel, name in original_names.items():
                node = pasted_by_sentinel.get(sentinel)
                if node is not None:
                    node.name = name

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
