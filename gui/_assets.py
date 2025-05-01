from PySide6.QtGui import QImage, QPixmap
import os
import urllib.parse

class Assets:
    def __init__(self):
        self.cafilepath = None # Initialize to None
        self.cachedImages = {}
        self.missing_assets = set()

    def set_cafilepath(self, cafilepath):
        """Sets the base path for resolving assets."""
        self.cafilepath = cafilepath
        # Optionally clear cache/missing assets when path changes,
        # but clear_cache() is called separately in openFile now.

    def clear_cache(self):
        """Clears the image cache and missing assets set."""
        self.cachedImages = {}
        self.missing_assets = set()

    def loadImage(self, src_path):
        """Loads an image from the given source path, using the cache."""
        if not src_path or not self.cafilepath: # Need cafilepath to resolve
            return None

        # Use filename as cache key, consistent with findAssetPath logic
        cache_key = os.path.basename(src_path)
        if cache_key in self.cachedImages:
            return self.cachedImages[cache_key]

        asset_path = self.findAssetPath(src_path)

        if not asset_path or not os.path.exists(asset_path):
            print(f"Could not find asset: {src_path} (resolved to: {asset_path})")
            self.missing_assets.add(cache_key) # Add filename to missing set
            return None

        # If found previously missing asset, remove it from the set
        if cache_key in self.missing_assets:
             self.missing_assets.remove(cache_key)

        try:
            # Load directly from the resolved asset_path
            img = QImage(asset_path)
            if img.isNull():
                print(f"Failed to load image (QImage isNull): {asset_path}")
                self.missing_assets.add(cache_key)
                return None

            pixmap = QPixmap.fromImage(img)
            self.cachedImages[cache_key] = pixmap # Cache using filename
            # print(f"Loaded image successfully: {asset_path} (cache key: {cache_key})")
            return pixmap
        except Exception as e:
            print(f"Error loading image {asset_path}: {e}")
            self.missing_assets.add(cache_key)
            return None

    def findAssetPath(self, src_path):
        """Resolves the asset filename to an absolute path."""
        if not src_path or not self.cafilepath:
            return None

        filename = os.path.basename(src_path) # Work with the filename

        # 1. Check assets directory within the .ca path
        assets_dir = os.path.join(self.cafilepath, "assets")
        potential_path = os.path.join(assets_dir, filename)
        if os.path.exists(potential_path) and os.path.isfile(potential_path):
            return potential_path

        # 2. Check case-insensitively in assets directory (useful for some systems)
        if os.path.exists(assets_dir) and os.path.isdir(assets_dir):
            for file in os.listdir(assets_dir):
                if file.lower() == filename.lower():
                    case_insensitive_path = os.path.join(assets_dir, file)
                    if os.path.isfile(case_insensitive_path):
                         return case_insensitive_path

        # Add more fallback search locations if necessary (e.g., parent dir assets),
        # but prioritize the assets folder within the opened .ca directory.

        # Consider adding recursive search if needed, but start simple.
        # recursive_path = self.findAssetRecursive(self.cafilepath, filename)
        # if recursive_path:
        #    return recursive_path

        return None # Indicate asset not found in expected locations

    # findAssetRecursive (keep if needed, otherwise remove for simplicity)
    # def findAssetRecursive(self, directory, filename, max_depth=3, current_depth=0): ...