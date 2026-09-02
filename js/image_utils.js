/**
 * Compresses an image file before uploading to save bandwidth and improve latency.
 * @param {File} file - The original image file.
 * @param {number} maxWidth - Maximum width of the compressed image.
 * @param {number} maxHeight - Maximum height of the compressed image.
 * @param {number} quality - JPEG quality (0.0 to 1.0).
 * @returns {Promise<Blob>} A promise that resolves to the compressed image blob.
 */
function compressImage(file, maxWidth = 1024, maxHeight = 1024, quality = 0.7) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (event) => {
            const img = new Image();
            img.src = event.target.result;
            img.onload = () => {
                let width = img.width;
                let height = img.height;

                if (width > height) {
                    if (width > maxWidth) {
                        height = Math.round(height * maxWidth / width);
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width = Math.round(width * maxHeight / height);
                        height = maxHeight;
                    }
                }

                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob(
                    (blob) => {
                        resolve(blob);
                    },
                    file.type, // Maintain original type, though will output jpeg/webp usually
                    quality
                );
            };
            img.onerror = (error) => reject(error);
        };
        reader.onerror = (error) => reject(error);
    });
}
