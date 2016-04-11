#!/usr/bin/python

import objc
import platform

import CoreFoundation
from Cocoa import NSURL
from LaunchServices import kLSSharedFileListFavoriteItems
from Foundation import CFURLCreateWithString, NSBundle

os_vers = int(platform.mac_ver()[0].split('.')[1])
if os_vers > 10:
	SFL_bundle = NSBundle.bundleWithIdentifier_('com.apple.coreservices.SharedFileList')
	functions  = [('LSSharedFileListCreate',              '^{OpaqueLSSharedFileListRef=}^{__CFAllocator=}^{__CFString=}@'),
				('LSSharedFileListCopySnapshot',        '^{__CFArray=}^{OpaqueLSSharedFileListRef=}o^I'),
				('LSSharedFileListItemCopyDisplayName', '^{__CFString=}^{OpaqueLSSharedFileListItemRef=}'),
				('LSSharedFileListItemResolve',         'i^{OpaqueLSSharedFileListItemRef=}Io^^{__CFURL=}o^{FSRef=[80C]}'),
				('LSSharedFileListItemMove',            'i^{OpaqueLSSharedFileListRef=}^{OpaqueLSSharedFileListItemRef=}^{OpaqueLSSharedFileListItemRef=}'),
				('LSSharedFileListItemRemove',          'i^{OpaqueLSSharedFileListRef=}^{OpaqueLSSharedFileListItemRef=}'),
				('LSSharedFileListInsertItemURL',       '^{OpaqueLSSharedFileListItemRef=}^{OpaqueLSSharedFileListRef=}^{OpaqueLSSharedFileListItemRef=}^{__CFString=}^{OpaqueIconRef=}^{__CFURL=}^{__CFDictionary=}^{__CFArray=}'),
				('kLSSharedFileListItemBeforeFirst',    '^{OpaqueLSSharedFileListItemRef=}'),]
	objc.loadBundleFunctions(SFL_bundle, globals(), functions)
else:
	from LaunchServices import kLSSharedFileListItemBeforeFirst, LSSharedFileListCreate, LSSharedFileListCopySnapshot, LSSharedFileListItemCopyDisplayName, LSSharedFileListItemResolve, LSSharedFileListItemMove, LSSharedFileListItemRemove, LSSharedFileListInsertItemURL

# Shoutout to Mike Lynn for the mount_share function below, allowing for the scripting of mounting network shares.
# See his blog post for more details: http://michaellynn.github.io/2015/08/08/learn-you-a-better-pyobjc-bridgesupport-signature/
class attrdict(dict): 
	__getattr__ = dict.__getitem__
	__setattr__ = dict.__setitem__

NetFS = attrdict()
# Can cheat and provide 'None' for the identifier, it'll just use frameworkPath instead
# scan_classes=False means only add the contents of this Framework
NetFS_bundle = objc.initFrameworkWrapper('NetFS', frameworkIdentifier=None, frameworkPath=objc.pathForFramework('NetFS.framework'), globals=NetFS, scan_classes=False)

def mount_share(share_path):
	# Mounts a share at /Volumes, returns the mount point or raises an error
	sh_url = CoreFoundation.CFURLCreateWithString(None, share_path, None)
	# Set UI to reduced interaction
	open_options  = {NetFS.kNAUIOptionKey: NetFS.kNAUIOptionNoUI}
	# Allow mounting sub-directories of root shares
	mount_options = {NetFS.kNetFSAllowSubMountsKey: True}
	# Mount!
	result, output = NetFS.NetFSMountURLSync(sh_url, None, None, None, open_options, mount_options, None)
	# Check if it worked
	if result != 0:
		 raise Exception('Error mounting url "%s": %s' % (share_path, output))
	# Return the mountpath
	return str(output[0])

# https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/ObjCRuntimeGuide/Articles/ocrtTypeEncodings.html
# Fix NetFSMountURLSync signature
del NetFS['NetFSMountURLSync']
objc.loadBundleFunctions(NetFS_bundle, NetFS, [('NetFSMountURLSync', 'i@@@@@@o^@')])

class FinderSidebar(object):

	def __init__(self):
		self.sflRef    = LSSharedFileListCreate(CoreFoundation.kCFAllocatorDefault, kLSSharedFileListFavoriteItems, None)
		self.snapshot  = LSSharedFileListCopySnapshot(self.sflRef, None)
		self.favorites = dict()
		self.update()

	def update(self):
		self.favorites = dict()
		self.snapshot  = LSSharedFileListCopySnapshot(self.sflRef, None)
		for item in self.snapshot[0]:
			name = LSSharedFileListItemCopyDisplayName(item)
			path = ""
			if name not in ("AirDrop", "All My Files", "iCloud"):
				path = LSSharedFileListItemResolve(item,0,None,None)[1]
			self.favorites[name] = path

	def synchronize(self):
		CoreFoundation.CFPreferencesAppSynchronize("com.apple.sidebarlists")

	def move(self, to_mv, after):
		if to_mv not in self.favorites.keys() or after not in self.favorites.keys() or to_mv == after:
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

	def remove(self, to_rm):
		for item in self.snapshot[0]:
			name = LSSharedFileListItemCopyDisplayName(item)
			if to_rm.upper() == name.upper():
				LSSharedFileListItemRemove(self.sflRef, item)
		self.synchronize()
		self.update()

	def add(self, to_add, uri="file://localhost"):
		if uri.startswith("afp") or uri.startswith("smb"):
			path = "%s%s" % (uri, to_add)
			to_add = mount_share(path)
		item = NSURL.alloc().initFileURLWithPath_(to_add)
		LSSharedFileListInsertItemURL(self.sflRef, kLSSharedFileListItemBeforeFirst, None, None, item, None, None)
		self.synchronize()
		self.update()

