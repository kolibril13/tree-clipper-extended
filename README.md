![Featured Image](packages/tree_clipper/icon.svg)

# Tree Clipper

Easier version control and sharing of node trees via `.json` or copy-pasteable strings.

Sharing node trees between users and in communities usually involves screenshots of node setups (which a user has to try and exactly re-create manually) or `.blend` files, which can be cumbersome (and a security risk) to download and append relevant data blocks to scenes.

`Tree Clipper` aims to improve two main workflows:

- Storage of large collections of nodes in `.json` format, so that version control such as `git` can properly track changes in a node tree rather than a single binary `.blend` file
- Sharing of node groups in communities like Discord and Stack Exchange. Users can share a 'magic string' which will be de-serialized into a node tree by the add-on, enabling rapid sharing and collaboration between users

More to come once we actually finish building.

## Features

The following features are already available:
- Enables export/import of node trees, `Geometry`-, `Shader`-, `Compositor`-, and `TextureNodeTree`s.
- Either plain JSON or compressed strings of the form `TreeClipper::<base64>`.
- The trees' interfaces are included.
- For compositor trees, scene attributes are stored and verified on import.
- Explicit interface for referenced "external" items that are not part of the export.
- The core logic is available as [PyPI Package](#pypi-package).

We aim to maintain backwards compatibility, and in principle custom node trees can also be supported.

We plan to support the remaining, more niche node trees as well. For example, [node based worlds](https://docs.blender.org/api/current/bpy.types.World.html#bpy.types.World.node_tree).

## Installation

We plan to publish the extension on the [official site](https://extensions.blender.org/) soon.

In the meantime, you can download the [latest release](https://github.com/Algebraic-UG/tree_clipper/releases/latest): scroll down and download the `tree_clipper-x.x.x.zip` file, then drag and drop into Blender.

Alternatively, [you can add a repository](https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#repositories) and get automatic updates, for the URL use:
```https://github.com/Algebraic-UG/tree_clipper/releases/latest/download/index.json```

## Related Work

There are several projects that are similar, the ones we're aware of include
- [Node To Python](https://extensions.blender.org/add-ons/node-to-python/)
- [NodeKit](https://github.com/j10er/NodeKit)
- [Copy/Paste Nodes](https://extensions.blender.org/add-ons/copy-paste-nodes/)
- [Node Kit](https://superhivemarket.com/products/node-kit)
- [nodebpy](https://github.com/BradyAJohnston/nodebpy)
- [geometry-script](https://github.com/carson-katri/geometry-script)
- [geonodes](https://github.com/al1brn/geonodes)

[Node To Python](https://extensions.blender.org/add-ons/node-to-python/) differs in that it uses Python code as storage. While this alleviates the need of a dependency for import (other than Blender itself), it is inherently not backwards-compatible and doesn't allow reading without Blender. (There is a [plan](https://github.com/BrendanParmer/NodeToPython/issues/107) to support JSON export)

[NodeKit](https://github.com/j10er/NodeKit) is not developed actively anymore, and the author instead advises development of Tree Clipper.

[Copy/Paste Nodes](https://extensions.blender.org/add-ons/copy-paste-nodes/) appears to have a different scope. It supports copying nodes into a tree directly. Tree Clipper doesn't do this, see also this [issue](https://github.com/Algebraic-UG/tree_clipper/issues/74). There's also no documented way to re-use the core logic in another addon.

[Node Kit](https://superhivemarket.com/products/node-kit) appears to be similar. It differs in distribution, as it is sold on Superhive ($15 at the time of writing).

In comparison to Tree Clipper, [nodebpy](https://github.com/BradyAJohnston/nodebpy), [geometry-script](https://github.com/carson-katri/geometry-script), and [geonodes](https://github.com/al1brn/geonodes) are different as they do not support exporting trees from Blender, but rather make it easier to define nodes from Python.

## PyPI Package

The core logic is available as a [PyPI package](https://pypi.org/project/tree-clipper/).
For more info, check out this [README.md](./packages/tree_clipper/README.md).

## Testing

Testing leverages [pytest](https://docs.pytest.org/en/stable/), also see the [CI](.github/workflows/test.yml) setup.

### Binary Blend Files

The directory [packages/tree_clipper/tests/binary_blend_files/](packages/tree_clipper/tests/binary_blend_files/) contains binary blend files with relatively big node groups from various sources.
In certain cases, the files are generated from an add-on.

Note that these files within Git LFS are optional unless you want to test Tree Clipper.

#### Sources & Attribution

| Source                    | Description                            | License                 | Link                                                             |
| ------------------------- | -------------------------------------- | ----------------------- | ---------------------------------------------------------------- |
| **Erindale’s Nodevember** | Procedural awesomeness                 | **CC0** (public domain) | [Patreon Collection](https://www.patreon.com/collection/1812208) |
| **Molecular Nodes**       | Molecular animation toolbox            | **GPLv3**               | [GitHub](https://github.com/BradyAJohnston/MolecularNodes)       |
| **Microscopy Nodes**      | Microscopy data handling               | **GPLv3**               | [GitHub](https://github.com/aafkegros/MicroscopyNodes)           |
| **Typst Importer**        | Render Typst content in Blender        | **GPLv3**               | [GitHub](https://github.com/kolibril13/blender_typst_importer)   |
| **Squishy Volumes**       | Material Point Method (MPM) in Blender | **GPLv3**               | [GitHub](https://github.com/Algebraic-UG/squishy_volumes)        |

#### Licensing/permission

Included assets are used with permission from the respective authors for testing purposes in this repository.
If you reuse or redistribute them, please follow each project’s license/terms and attribution requirements.

## Development

It is recommended to use [vscode](https://code.visualstudio.com/) with these extensions:
- [ruff](https://github.com/astral-sh/ruff-vscode)
- [ty](https://github.com/astral-sh/ty-vscode)
- [Python Debugger](https://code.visualstudio.com/docs/python/debugging)
- [Blender Development](https://github.com/JacquesLucke/blender_vscode)

[uv](https://docs.astral.sh/uv/) is also required for this workflow.

### Vendorizing Tree Clipper

Ideally, the [core logic](packages/tree_clipper/) of Tree Clipper should not be used directly as a dependency in downstream addons, and it should be [vendorized](https://pypi.org/project/vendorize/) instead.
This is what the [Tree Clipper Addon](packages/tree_clipper_addon/) does as well.

The motivation for this is that we expect other addons like [Squishy Volumes](https://github.com/Algebraic-UG/squishy_volumes) to use potentially incompatible version of Tree Clipper.
Vendoring avoids version conflicts and ensures that all addons can load.
> [!IMPORTANT]
> Vendoring currently has two drawbacks developers must be aware of:
> 1. The editable core logic is in [packages/tree_clipper/](packages/tree_clipper/), and the vendorized code will reside in packages/tree_clipper_addon/src/tree_clipper_addon/_vendor/. The vendorized code runs and can be debugged, but should not be edited directly.

> 2. Depending on your version of the [Blender Development](https://github.com/JacquesLucke/blender_vscode) addon (whether it has [this change](https://github.com/JacquesLucke/blender_vscode/pull/258)), the task [`run-python-vendor`](.vscode/tasks.json) must run before starting Blender. Subsequent reloads will do this automatically.
