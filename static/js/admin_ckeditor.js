window.addEventListener('load', function() {
    function initAll() {
        if (typeof CKEDITOR === 'undefined') {
            // Wait 100ms and try again if CKEditor library is not loaded yet
            setTimeout(initAll, 100);
            return;
        }

        function initCKEditor(element) {
            if (element && !element.classList.contains('ckeditor-initialized') && !element.id.includes('__prefix__')) {
                CKEDITOR.replace(element.id, {
                    versionCheck: false
                });
                element.classList.add('ckeditor-initialized');
            }
        }

        // 1. Initialize existing textareas on load
        document.querySelectorAll('textarea').forEach(function(textarea) {
            if (textarea.id === 'id_content' || textarea.id.endsWith('-content')) {
                initCKEditor(textarea);
            }
        });

        // 2. Listen for dynamically added inline rows using standard Django jQuery event
        if (window.django && window.django.jQuery) {
            window.django.jQuery(document).on('formset:added', function(event, $row, formsetName) {
                $row.find('textarea').each(function() {
                    if (this.id === 'id_content' || this.id.endsWith('-content')) {
                        initCKEditor(this);
                    }
                });
            });
        }

        // 3. Fallback: MutationObserver to capture dynamically added elements as well
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        var textareas = node.querySelectorAll ? node.querySelectorAll('textarea') : [];
                        if (node.tagName === 'TEXTAREA') {
                            textareas = [node];
                        }
                        textareas.forEach(function(textarea) {
                            if (textarea.id === 'id_content' || textarea.id.endsWith('-content')) {
                                initCKEditor(textarea);
                            }
                        });
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    initAll();
});


