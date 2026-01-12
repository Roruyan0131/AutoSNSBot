import os
import shutil
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import pickle

# 入力画像フォルダ
input_dir = r"E:\ファイル\ドキュメント\GUI\image"

# 出力フォルダ定義（キャラクター名に合わせて定義）
output_dirs = {
    "aya": r"E:\ファイル\ドキュメント\GUI\image\アヤ",
    "yuna": r"E:\ファイル\ドキュメント\GUI\image\ユナ",
    "alicia": r"E:\ファイル\ドキュメント\GUI\image\アリシア",
    "momoka": r"E:\ファイル\ドキュメント\GUI\image\雪村ももか"
}

# デバイス設定
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"使用デバイス: {device}")

# モデルロード
def load_character_model():
    try:
        with open("class_names.pkl", "rb") as f:
            class_names = pickle.load(f)

        num_classes = len(class_names)
        model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        model.load_state_dict(torch.load("character_classifier.pth", map_location=device, weights_only=True))
        model = model.to(device)
        model.eval()

        print("キャラクター分類モデルロード完了")
        return model, class_names
    except Exception as e:
        print(f"モデルロードエラー: {e}")
        return None, None

# 画像変換
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# キャラクター分類処理
def predict_character(model, class_names, image_path):
    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        _, predicted = torch.max(outputs, 1)

    return class_names[predicted.item()]

# メイン処理
def process_images():
    model, class_names = load_character_model()
    if model is None:
        return

    # 出力先フォルダ作成
    for out_dir in output_dirs.values():
        os.makedirs(out_dir, exist_ok=True)

    # 入力画像一覧取得
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

    for idx, filename in enumerate(images, 1):
        image_path = os.path.join(input_dir, filename)
        try:
            character = predict_character(model, class_names, image_path)
            target_dir = output_dirs.get(character.lower())

            if target_dir:
                shutil.move(image_path, os.path.join(target_dir, filename))
                print(f"[{idx}/{len(images)}] {filename} → {character} フォルダへ移動")
            else:
                print(f"[{idx}/{len(images)}] {filename} → 不明なキャラ: {character}")

        except Exception as e:
            print(f"[{idx}/{len(images)}] {filename} → エラー: {e}")

if __name__ == "__main__":
    process_images()
