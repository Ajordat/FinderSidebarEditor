
# Finder Sidebar Editor

![PyPI](https://img.shields.io/pypi/v/finder-sidebar-editor)
![PyPI - Downloads](https://img.shields.io/pypi/dm/finder-sidebar-editor)
![PyPI - License](https://img.shields.io/pypi/l/finder-sidebar-editor)

![GitHub issues](https://img.shields.io/github/issues/ajordat/finder-sidebar-editor)
![GitHub pull requests](https://img.shields.io/github/issues-pr/ajordat/finder-sidebar-editor)

Python module for easily adding, removing, and moving favorites on the Finder sidebar in the context of the logged in user.

### Installation

Install the [PyPI package][1] using pip:

```
pip install finder-sidebar-editor
```

### Example usage

```python
from finder_sidebar_editor import FinderSidebar                # Import the module

sidebar = FinderSidebar()                                      # Create a Finder sidebar instance to act on.

sidebar.remove("All My Files")                                 # Remove 'All My Files' favorite from sidebar
sidebar.remove("iCloud")                                       # Remove 'iCloud' favorite from sidebar
sidebar.add("/Library")                                        # Add '/Library' favorite to sidebar
sidebar.add("/SomeShare", uri="smb://shares")                  # Mount 'smb://shares/SomeShare' to '/Volumes/SomeShare' and add as favorite to sidebar
sidebar.add("/SomeOtherShare", uri="afp://username:pw@server") # Mount pw protected 'afp://server/SomeOtherShare' to '/Volumes/SomeOtherShare' and add as favorite to sidebar
sidebar.move("Library", "Applications")                        # Move 'Library' favorite to slot just below 'Applications'
```

[1]: https://pypi.org/project/finder-sidebar-editor/
