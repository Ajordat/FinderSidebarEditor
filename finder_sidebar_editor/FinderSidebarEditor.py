from platform import mac_ver

from Cocoa import NSURL
from CoreFoundation import CFPreferencesAppSynchronize
from CoreFoundation import CFURLCreateWithString
from CoreFoundation import kCFAllocatorDefault
from Foundation import NSBundle
from LaunchServices import kLSSharedFileListFavoriteItems
from objc import loadBundleFunctions, initFrameworkWrapper, pathForFramework

os_version = int(mac_ver()[0].split('.')[1])
if os_version > 10:
    SFL_bundle = NSBundle.bundleWithIdentifier_(
        'com.apple.coreservices.SharedFileList'
    )
    functions = [
        ('LSSharedFileListCreate',              b'^{OpaqueLSSharedFileListRef=}^{__CFAllocator=}^{__CFString=}@'),
        ('LSSharedFileListCopySnapshot',        b'^{__CFArray=}^{OpaqueLSSharedFileListRef=}o^I'),
        ('LSSharedFileListItemCopyDisplayName', b'^{__CFString=}^{OpaqueLSSharedFileListItemRef=}'),
        ('LSSharedFileListItemResolve',         b'i^{OpaqueLSSharedFileListItemRef=}Io^^{__CFURL=}o^{FSRef=[80C]}'),
        ('LSSharedFileListItemMove',            b'i^{OpaqueLSSharedFileListRef=}^{OpaqueLSSharedFileListItemRef=}^{OpaqueLSSharedFileListItemRef=}'),
        ('LSSharedFileListItemRemove',          b'i^{OpaqueLSSharedFileListRef=}^{OpaqueLSSharedFileListItemRef=}'),
        ('LSSharedFileListRemoveAllItems',      b'i^{OpaqueLSSharedFileListRef=}'),
        ('LSSharedFileListInsertItemURL',       b'^{OpaqueLSSharedFileListItemRef=}^{OpaqueLSSharedFileListRef=}^{OpaqueLSSharedFileListItemRef=}^{__CFString=}^{OpaqueIconRef=}^{__CFURL=}^{__CFDictionary=}^{__CFArray=}'),
        ('kLSSharedFileListItemBeforeFirst',    b'^{OpaqueLSSharedFileListItemRef=}')
    ]
    loadBundleFunctions(SFL_bundle, globals(), functions)
    from LaunchServices import LSSharedFileListItemCopyResolvedURL
else:
    from LaunchServices import kLSSharedFileListItemBeforeFirst
    from LaunchServices import LSSharedFileListCreate
    from LaunchServices import LSSharedFileListCopySnapshot
    from LaunchServices import LSSharedFileListItemCopyDisplayName
    from LaunchServices import LSSharedFileListItemResolve
    from LaunchServices import LSSharedFileListItemMove
    from LaunchServices import LSSharedFileListItemRemove
    from LaunchServices import LSSharedFileListRemoveAllItems
    from LaunchServices import LSSharedFileListInsertItemURL


# Shoutout to Mike Lynn for the mount_share function below, allowing for the
# scripting of mounting network shares. See his blog post for more details:
# http://michaellynn.github.io/2015/08/08/learn-you-a-better-pyobjc-bridgesupport-signature/
class attrdict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


NetFS = attrdict()
# Can cheat and provide 'None' for the identifier, it'll just use
# frameworkPath instead scan_classes=False means only add the
# contents of this Framework


netfs_path = 'NetFS.framework'

if os_version >= 11:
    netfs_path = 'System/Library/Frameworks/' + netfs_path

NetFS_bundle = initFrameworkWrapper(
    'NetFS', frameworkIdentifier=None,
    frameworkPath=pathForFramework(netfs_path), globals=NetFS,
    scan_classes=False
)


def mount_share(share_path: str) -> str:
    """Mount a share at /Volumes.

    :param str share_path: Path of the share.

    :returns: The mount path.

    :raises Exception: If there's an error mounting.
    """

    # Mounts a share at /Volumes, returns the mount point or raises an error
    sh_url = CFURLCreateWithString(None, share_path, None)
    # Set UI to reduced interaction
    open_options = {NetFS.kNAUIOptionKey: NetFS.kNAUIOptionNoUI}
    # Allow mounting sub-directories of root shares
    mount_options = {NetFS.kNetFSAllowSubMountsKey: True}
    # Mount!
    result, output = NetFS.NetFSMountURLSync(
        sh_url, None, None, None, open_options, mount_options, None
    )
    # Check if it worked
    if result != 0:
        raise Exception('Error mounting url "{}": {}'.format(share_path, output))
    # Return the mount path
    return str(output[0])


# https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/ObjCRuntimeGuide/Articles/ocrtTypeEncodings.html
# Fix NetFSMountURLSync signature
del NetFS['NetFSMountURLSync']
loadBundleFunctions(
    NetFS_bundle, NetFS, [('NetFSMountURLSync', b'i@@@@@@o^@')]
)


class FinderSidebar:
    """Finder Sidebar instance for modifying favorites entries for logged in user.

    Attributes:
        sflRef (LSSharedFileList): Reference to sfl object containing Finder
                                   favorites data.
        snapshot (tuple): Snapshot of Finder sfl object containing readable
                          entries for each favorite.
        favorites (dict): Dictionary containing name: uri pairs for
                          each favorite.
    """

    def __init__(self):
        self.sflRef = LSSharedFileListCreate(
            kCFAllocatorDefault, kLSSharedFileListFavoriteItems, None
        )
        self.snapshot = LSSharedFileListCopySnapshot(self.sflRef, None)
        self.favorites = dict()
        self.update()

    def update(self) -> None:
        """Updates snapshot and favorites attributes.
        """

        self.favorites = dict()
        self.snapshot = LSSharedFileListCopySnapshot(self.sflRef, None)
        for item in self.snapshot[0]:
            name = LSSharedFileListItemCopyDisplayName(item)
            path = ""
            if name not in ["AirDrop", "All My Files", "iCloud"]:
                path = LSSharedFileListItemResolve(item, 0, None, None)[1]
            self.favorites[name] = path

    @staticmethod
    def synchronize() -> None:
        """Synchronizes CF preferences for the `sidebarlists` identifier.
        """

        CFPreferencesAppSynchronize("com.apple.sidebarlists")

    def move(self, to_mv: str, after: str) -> None:
        """Moves sidebar list item to position immediately other sidebar
        list item.

        :param str to_mv: Name of sidebar list item to move.
        :param str after: Name of sidebar list item to move "to_mv" after.
        """

        if to_mv not in self.favorites.keys() or \
                after not in self.favorites.keys() or to_mv == after:
            return

        for item in self.snapshot[0]:
            name = LSSharedFileListItemCopyDisplayName(item)

            if name == after:
                after = item
            elif name == to_mv:
                to_mv = item

        LSSharedFileListItemMove(self.sflRef, to_mv, after)
        self.synchronize()
        self.update()

    def remove(self, to_rm: str) -> None:
        """Removes sidebar list item.

        :param str to_rm: Name of sidebar list item to remove.
        """

        for item in self.snapshot[0]:
            name = LSSharedFileListItemCopyDisplayName(item)
            if to_rm.upper() == name.upper():
                LSSharedFileListItemRemove(self.sflRef, item)
        self.synchronize()
        self.update()

    def remove_all(self) -> None:
        """Removes all sidebar list items.
        """

        LSSharedFileListRemoveAllItems(self.sflRef)
        self.synchronize()
        self.update()

    def remove_by_path(self, path: str) -> None:
        """Removes sidebar list item.

        :param str path: Path of sidebar list item to remove.
        """

        comparison_path = 'file://{}/'.format(path).upper()
        for item in self.snapshot[0]:
            sidebar_item = LSSharedFileListItemCopyResolvedURL(item, 0, None)
            if comparison_path == str(sidebar_item[0]).upper():
                LSSharedFileListItemRemove(self.sflRef, item)
        self.synchronize()
        self.update()

    def add(self, to_add: str, uri: str = "file://localhost") -> None:
        """Append item to sidebar list items.

        :param str to_add: Path to item to append to sidebar list.
        :param str uri: URI of server where item resides if not on localhost.
        """

        if uri.startswith("afp") or uri.startswith("smb"):
            to_add = mount_share(uri + to_add)

        item = NSURL.alloc().initFileURLWithPath_(to_add)
        LSSharedFileListInsertItemURL(
            self.sflRef, kLSSharedFileListItemBeforeFirst,
            None, None, item, None, None
        )
        self.synchronize()
        self.update()

    def get_index_from_name(self, name: str) -> int:
        """Gets index of sidebar list item identified by name.

        :param str name: Display name to identify sidebar list item by.

        :returns: Index of sidebar list item identified by name.
        """

        for index, item in enumerate(self.snapshot[0]):
            found_name = LSSharedFileListItemCopyDisplayName(item)
            if name == found_name:
                return index

    def get_name_from_index(self, index: int) -> None:
        """Gets name of sidebar list item identified by index.

        :param int index: Index to identify sidebar list item by.

        :returns: Name of sidebar list item identified by index.
        """

        if index > len(self.snapshot[0]):
            index = -1
        return LSSharedFileListItemCopyDisplayName(self.snapshot[0][index])
