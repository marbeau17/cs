"""
Snippet to add to static/index.html in the loadChannel function.

In the loadChannel function, after the line:
    document.getElementById('channel-desc').textContent = ch.description || 'カスタマーサポートAI回答支援';

Add the following block (inside the `if (ch)` block):

                        if (ch.default_model) {
                            const modelSelect = document.getElementById('model-select');
                            if (modelSelect && !localStorage.getItem('preferred_model')) {
                                modelSelect.value = ch.default_model;
                            }
                        }

This ensures the model selector defaults to the channel's configured model,
unless the user has explicitly saved a preference via localStorage.
"""
