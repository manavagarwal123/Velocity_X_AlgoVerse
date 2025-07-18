import os
import numpy as np
import cv2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.model_selection import train_test_split

# Prepare data
data_dir = "dataset"
categories = [cat for cat in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, cat))]
label_dict = {i: cat for i, cat in enumerate(categories)}
images = []
labels = []

for i, category in enumerate(categories):
    path = os.path.join(data_dir, category)
    for img_name in os.listdir(path):
        if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        img_path = os.path.join(path, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            print(f"Skipped unreadable image: {img_path}")
            continue

        img = cv2.resize(img, (184, 184))
        images.append(img.flatten())
        labels.append(i)

X = np.array(images) / 255.0  # Normalize
y = np.array(labels)

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Build model
model = Sequential([
    Dense(128, activation='relu', input_shape=(33856,)),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dense(len(categories), activation='softmax')
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

# Save
model.save("currency_model.h5")
np.save("label_dict.npy", label_dict)