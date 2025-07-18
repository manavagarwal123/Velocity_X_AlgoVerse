document.addEventListener('DOMContentLoaded', function() {
    // Mode selection
    const modeButtons = document.querySelectorAll('.mode-btn');
    let currentMode = 'object';
    
    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            modeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentMode = this.dataset.mode;
        });
    });
    
    // File upload handling
    const fileInput = document.getElementById('file-input');
    const previewImage = document.getElementById('preview-image');
    const previewContainer = document.getElementById('preview-container');
    const resultText = document.getElementById('result-text');
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                previewImage.src = event.target.result;
                previewImage.style.display = 'block';
                
                // Process the image
                processUploadedImage(file);
            };
            reader.readAsDataURL(file);
        }
    });
    
    // Drag and drop functionality
    const uploadBox = document.querySelector('.upload-box');
    
    uploadBox.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = '#4285f4';
    });
    
    uploadBox.addEventListener('dragleave', function() {
        this.style.borderColor = '#6c757d';
    });
    
    uploadBox.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = '#6c757d';
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.match('image.*')) {
            fileInput.files = e.dataTransfer.files;
            
            const reader = new FileReader();
            reader.onload = function(event) {
                previewImage.src = event.target.result;
                previewImage.style.display = 'block';
                
                // Process the image
                processUploadedImage(file);
            };
            reader.readAsDataURL(file);
        }
    });
    
    function processUploadedImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', currentMode);
        
        resultText.textContent = 'Processing...';
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultText.textContent = 'Error: ' + data.error;
            } else {
                resultText.textContent = data.result;
                document.getElementById('speak-btn').disabled = false;
            }
        })
        .catch(error => {
            resultText.textContent = 'Error: ' + error.message;
        });
    }
    
    // Speak button
    const speakBtn = document.getElementById('speak-btn');
    speakBtn.addEventListener('click', function() {
        const text = resultText.textContent;
        if (text && text !== 'Processing...' && !text.startsWith('Error')) {
            fetch('/speak', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
        }
    });
    
    // Initialize camera
    initCamera();
});

function initCamera() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('capture-btn');
    const resultText = document.getElementById('result-text');
    const speakBtn = document.getElementById('speak-btn');
    
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
            })
            .catch(function(error) {
                console.error('Camera error: ', error);
                alert('Could not access the camera. Please check permissions.');
            });
    }
    
    captureBtn.addEventListener('click', function() {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Get the current mode
        const currentMode = document.querySelector('.mode-btn.active').dataset.mode;
        
        // Process the captured image
        canvas.toBlob(function(blob) {
            const formData = new FormData();
            formData.append('file', blob, 'capture.jpg');
            formData.append('mode', currentMode);
            
            resultText.textContent = 'Processing...';
            speakBtn.disabled = true;
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultText.textContent = 'Error: ' + data.error;
                } else {
                    resultText.textContent = data.result;
                    speakBtn.disabled = false;
                }
            })
            .catch(error => {
                resultText.textContent = 'Error: ' + error.message;
            });
        }, 'image/jpeg', 0.9);
    });
}