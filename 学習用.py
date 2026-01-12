
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import pickle

# ==== 設定 ====
data_dir = "./dataset"  # データ格納フォルダ (各キャラ名ごとのサブフォルダ構成)
num_epochs = 10
batch_size = 32
learning_rate = 0.0001
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==== データ前処理 ====
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

dataset = datasets.ImageFolder(root=data_dir, transform=transform)
class_names = dataset.classes
num_classes = len(class_names)
train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# ==== モデル定義 ====
model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# ==== 学習ループ ====
for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()

    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss/len(train_loader):.4f}")

# ==== モデル保存 ====
torch.save(model.state_dict(), "character_classifier.pth")
print("✅ モデル保存完了: character_classifier.pth")

# ==== クラス名保存 ====
with open("class_names.pkl", "wb") as f:
    pickle.dump(class_names, f)
print("✅ クラス名保存完了: class_names.pkl")
