// sorting.js

// Sort gallery alphabetically
function sortGalleryAlphabetically(imageFilePaths) {
    return imageFilePaths.slice().sort((a, b) => a.localeCompare(b));
  }
  
  // Sort gallery by category
  function sortGalleryByCategory(imageFilePaths, category) {
    return imageFilePaths.filter((filePath) => filePath.includes(`images/${category}/`));
  }
  
  // Sort gallery by custom category
  function sortGalleryByCustomCategory(imageFilePaths, category) {
    return imageFilePaths.filter((filePath) => {
      const pathSegments = filePath.split("/");
      return pathSegments.includes(category);
    });
  }
  