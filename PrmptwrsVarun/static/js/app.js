document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('incident-form');
    const descriptionInput = document.getElementById('incident-description');
    const photoInput = document.getElementById('incident-photo');
    const photoPreviewContainer = document.getElementById('photo-preview-container');
    const photoPreview = document.getElementById('photo-preview');
    const removePhotoBtn = document.getElementById('remove-photo');
    const loadingIndicator = document.getElementById('loading-indicator');
    const inputSection = document.getElementById('input-section');
    const resultsSection = document.getElementById('results-section');
    const resetBtn = document.getElementById('reset-btn');
    const focusToggle = document.getElementById('focus-toggle');
    const languageSelect = document.getElementById('language-select');

    let currentPhotoFile = null;

    // Photo Upload Handling
    photoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate MIME type client-side
            if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
                alert('Please upload a valid image (JPEG, PNG, WEBP).');
                photoInput.value = '';
                return;
            }
            
            // Validate Size limit client-side
            if (file.size > 5 * 1024 * 1024) {
                alert('Image is too large. Max size is 5MB.');
                photoInput.value = '';
                return;
            }

            currentPhotoFile = file;
            const objectURL = URL.createObjectURL(file);
            photoPreview.src = objectURL;
            photoPreviewContainer.classList.remove('hidden');
        }
    });

    removePhotoBtn.addEventListener('click', () => {
        currentPhotoFile = null;
        photoInput.value = '';
        photoPreview.src = '';
        photoPreviewContainer.classList.add('hidden');
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const text = descriptionInput.value.trim();
        const language = languageSelect.value;

        if (!text && !currentPhotoFile) {
            alert('Please provide a description or a photo.');
            return;
        }

        // Show Loading State
        form.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');

        try {
            let imageBase64 = null;
            let mimeType = null;

            if (currentPhotoFile) {
                // Compress image before sending
                const compressedBlob = await compressImage(currentPhotoFile);
                
                // Convert to Base64
                imageBase64 = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result.split(',')[1]);
                    reader.readAsDataURL(compressedBlob);
                });
                mimeType = currentPhotoFile.type;
            }

            const payload = {
                text: text,
                language: language,
                image_base64: imageBase64,
                mime_type: mimeType
            };

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to analyze situation');
            }

            displayResults(data);

        } catch (error) {
            console.error(error);
            alert(`Error: ${error.message}`);
            
            // Revert UI on error
            form.classList.remove('hidden');
            loadingIndicator.classList.add('hidden');
        }
    });

    function displayResults(data) {
        // Hide Input, Show Results
        inputSection.classList.add('hidden');
        loadingIndicator.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        // Focus for screen readers
        document.getElementById('assessment-heading').focus();

        // Urgency Badge
        const badge = document.getElementById('urgency-badge');
        badge.textContent = data.urgency;
        badge.className = 'badge'; // Reset
        if (data.urgency.toLowerCase() === 'low') badge.classList.add('badge-low');
        else if (data.urgency.toLowerCase() === 'medium') badge.classList.add('badge-medium');
        else badge.classList.add('badge-high');

        // Summary
        document.getElementById('result-summary').textContent = data.summary;

        // Immediate Actions
        const actionsList = document.getElementById('result-immediate-actions');
        actionsList.innerHTML = '';
        data.immediateActions.forEach(action => {
            const li = document.createElement('li');
            li.textContent = action;
            actionsList.appendChild(li);
        });

        // Avoid
        const avoidList = document.getElementById('result-avoid');
        avoidList.innerHTML = '';
        data.avoid.forEach(avoid => {
            const li = document.createElement('li');
            li.textContent = avoid;
            avoidList.appendChild(li);
        });

        // Warning Signs
        const warningsList = document.getElementById('result-warnings');
        warningsList.innerHTML = '';
        data.warningSigns.forEach(warning => {
            const li = document.createElement('li');
            li.textContent = warning;
            warningsList.appendChild(li);
        });

        // Professional Help
        document.getElementById('result-professional-help').textContent = data.seekProfessionalHelp;
    }

    // Reset Flow
    resetBtn.addEventListener('click', () => {
        form.reset();
        descriptionInput.value = '';
        removePhotoBtn.click();
        
        resultsSection.classList.add('hidden');
        form.classList.remove('hidden');
        inputSection.classList.remove('hidden');
        
        // Reset focus
        descriptionInput.focus();
        
        // Remove focus mode if active
        document.body.classList.remove('focus-mode');
        focusToggle.setAttribute('aria-pressed', 'false');
    });

    // Focus Mode Toggle
    focusToggle.addEventListener('click', () => {
        document.body.classList.toggle('focus-mode');
        const isActive = document.body.classList.contains('focus-mode');
        focusToggle.setAttribute('aria-pressed', isActive.toString());
    });
});
