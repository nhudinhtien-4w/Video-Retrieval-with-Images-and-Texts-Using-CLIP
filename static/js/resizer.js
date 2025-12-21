document.addEventListener('DOMContentLoaded', function() {
    const searchContainer = document.querySelector('.search_container');
    const resizer = document.createElement('div');
    resizer.className = 'resizer';
    searchContainer.appendChild(resizer);

    let isResizing = false;
    let startX;
    let startWidth;

    function startResizing(e) {
        isResizing = true;
        startX = e instanceof MouseEvent ? e.clientX : e.touches[0].clientX;
        startWidth = searchContainer.getBoundingClientRect().width;
        document.documentElement.classList.add('resizing');
    }

    function doResize(e) {
        if (!isResizing) return;

        const currentX = e instanceof MouseEvent ? e.clientX : e.touches[0].clientX;
        const newWidth = startWidth + (currentX - startX);

        // Constrain the width between min and max values
        if (newWidth >= 280 && newWidth <= 600) {
            searchContainer.style.width = newWidth + 'px';
        }
    }

    function stopResizing() {
        isResizing = false;
        document.documentElement.classList.remove('resizing');
    }

    // Mouse event listeners
    resizer.addEventListener('mousedown', function(e) {
        e.preventDefault();
        startResizing(e);

        document.addEventListener('mousemove', doResize);
        document.addEventListener('mouseup', function() {
            document.removeEventListener('mousemove', doResize);
            stopResizing();
        }, { once: true });
    });

    // Touch event listeners
    resizer.addEventListener('touchstart', function(e) {
        e.preventDefault();
        startResizing(e);

        document.addEventListener('touchmove', doResize);
        document.addEventListener('touchend', function() {
            document.removeEventListener('touchmove', doResize);
            stopResizing();
        }, { once: true });
    });
});
