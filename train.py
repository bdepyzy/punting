import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from pathlib import Path

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
SUITS = ["c", "d", "h", "s"]
CLASSES = [
    f"{r}{s}" for r in RANKS for s in SUITS
]  # ['2c', '2d', '2h', '2s', '3c', ...]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}


class CardDataset(Dataset):
    def __init__(self, cards_dir: str, transform=None, augment_factor: int = 100):
        """
        Args:
            cards_dir: Path to directory containing card images (e.g., 'cards/')
            transform: Transforms to apply to images
            augment_factor: Number of times to repeat each card for training
        """
        self.cards_dir = Path(cards_dir)
        self.transform = transform
        self.augment_factor = augment_factor

        # Load all card paths and labels
        self.samples = []
        for card_path in self.cards_dir.glob("*.png"):
            label = card_path.stem  # e.g., '2c', 'Ah'
            if label in CLASS_TO_IDX:
                # Repeat each card augment_factor times for more training data
                for _ in range(augment_factor):
                    self.samples.append((card_path, CLASS_TO_IDX[label]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


class CardNet(nn.Module):
    def __init__(self, num_classes: int = 52):
        super(CardNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.5)

        # Will be computed dynamically based on input size
        self._fc_input_size = None
        self.fc1 = None
        self.fc2 = nn.Linear(256, num_classes)

    def _get_fc_input_size(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        return x.view(x.size(0), -1).size(1)

    def forward(self, x):
        # Dynamically create fc1 based on input size
        if self.fc1 is None:
            fc_input = self._get_fc_input_size(x)
            self.fc1 = nn.Linear(fc_input, 256).to(x.device)

        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(x.size(0), -1)
        x = self.dropout(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return x


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Transforms with data augmentation for training
    train_transform = transforms.Compose(
        [
            transforms.Resize((64, 64)),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]
    )

    # Transforms for evaluation (no augmentation)
    eval_transform = transforms.Compose(
        [
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]
    )

    # Create datasets
    train_dataset = CardDataset("cards/", transform=train_transform, augment_factor=100)
    eval_dataset = CardDataset("cards/", transform=eval_transform, augment_factor=1)

    print(f"Training samples: {len(train_dataset)}")
    print(f"Eval samples: {len(eval_dataset)}")
    print(f"Classes: {len(CLASSES)}")

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=2)
    eval_loader = DataLoader(eval_dataset, batch_size=32, shuffle=False, num_workers=2)

    # Model, loss, optimizer
    model = CardNet(num_classes=len(CLASSES)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    # Training loop
    num_epochs = 30
    best_accuracy = 0.0

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0

        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        scheduler.step()

        # Evaluate
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in eval_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        accuracy = 100 * correct / total
        avg_loss = running_loss / len(train_loader)
        print(
            f"Epoch [{epoch + 1}/{num_epochs}] Loss: {avg_loss:.4f} Accuracy: {accuracy:.2f}%"
        )

        # Save best model
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "classes": CLASSES,
                    "class_to_idx": CLASS_TO_IDX,
                },
                "card_model.pth",
            )
            print(f"  Saved new best model with accuracy: {accuracy:.2f}%")

    print(f"\nFinished Training. Best accuracy: {best_accuracy:.2f}%")


def predict(image_path: str, model_path: str = "card_model.pth") -> str:
    """Predict the card in an image."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load model
    checkpoint = torch.load(model_path, map_location=device)
    model = CardNet(num_classes=len(CLASSES)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Load and transform image
    transform = transforms.Compose(
        [
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]
    )

    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    # Predict
    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)

    return IDX_TO_CLASS[predicted.item()]


if __name__ == "__main__":
    train()
