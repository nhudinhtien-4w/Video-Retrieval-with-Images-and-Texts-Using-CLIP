document.addEventListener('DOMContentLoaded', function() {
    function initializeImageGrid() {
        const images = document.querySelectorAll('.image-container');
        
        images.forEach(container => {
            const img = container.querySelector('.carousel-image');
            const irBtn = container.querySelector('.IR_Btn');
            
            // Create add to chat button
            const addButton = document.createElement('button');
            addButton.className = 'add-to-chat-btn';
            addButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/></svg>';
            
            // Add click handler
            addButton.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent image click
                const imgPath = img.getAttribute('src');
                const pathParts = imgPath.split('/');
                const fileName = pathParts[pathParts.length - 1];
                const videoId = pathParts[pathParts.length - 2];
                window.addImageToChat(imgPath, videoId, fileName);
            });
            
            // Create controls container
            const controls = document.createElement('div');
            controls.className = 'image-controls';
            
            // Move IR button into controls
            if (irBtn) {
                controls.appendChild(irBtn);
            }
            controls.appendChild(addButton);
            
            // Add controls to image container
            container.appendChild(controls);
        });
    }

    // Initialize on page load
    initializeImageGrid();

    // Re-initialize when new images are loaded (if you have pagination or lazy loading)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.target.classList.contains('image-grid')) {
                initializeImageGrid();
            }
        });
    });

    const imageGrid = document.querySelector('.image-grid');
    if (imageGrid) {
        observer.observe(imageGrid, { childList: true, subtree: true });
    }
});
