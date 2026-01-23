"""
AI-POWERED JACKPOT PREDICTOR
=============================

Uses multiple AI/ML approaches to predict lottery numbers:
1. LSTM Neural Network - Learns sequential patterns in RNG output
2. Transformer Model - Attention-based sequence prediction
3. LightGBM Gradient Boosting - Feature-based prediction
4. Ensemble - Combines all models with weighted voting

Specifically designed for:
- L4L, LA: RNG (Digital Drawing System) - more predictable, focus AI here
- PB, MM: Physical balls - use statistical methods primarily

The system continuously trains and improves predictions.
"""
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import lightgbm as lgb
from pathlib import Path
from datetime import datetime
from collections import Counter
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / 'data'
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(f"Using device: {DEVICE}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")


class LotteryDataset(Dataset):
    """Dataset for lottery sequence prediction."""
    
    def __init__(self, sequences, targets, positions=None):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.LongTensor(targets)
        self.positions = positions
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class LSTMPredictor(nn.Module):
    """LSTM-based sequence predictor for RNG patterns."""
    
    def __init__(self, input_size, hidden_size, num_layers, output_size, dropout=0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size)
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        out = self.fc(lstm_out[:, -1, :])
        return out


class TransformerPredictor(nn.Module):
    """Transformer-based predictor using attention mechanism."""
    
    def __init__(self, input_size, d_model, nhead, num_layers, output_size, dropout=0.1):
        super().__init__()
        self.input_proj = nn.Linear(input_size, d_model)
        self.pos_encoding = nn.Parameter(torch.randn(1, 100, d_model) * 0.1)
        
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, d_model * 4, dropout, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        self.fc = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, output_size)
        )
    
    def forward(self, x):
        x = self.input_proj(x)
        x = x + self.pos_encoding[:, :x.size(1), :]
        x = self.transformer(x)
        out = self.fc(x[:, -1, :])
        return out


class AIJackpotPredictor:
    """Main AI prediction system."""
    
    def __init__(self, lottery, sequence_length=20):
        self.lottery = lottery.lower()
        self.sequence_length = sequence_length
        self.draws = self._load_draws()
        self.exclusions = self._load_exclusions()
        self.patterns = self._load_patterns()
        
        # Lottery config
        self.config = {
            'l4l': {'max_main': 48, 'max_bonus': 18, 'type': 'rng'},
            'la':  {'max_main': 52, 'max_bonus': 10, 'type': 'rng'},
            'pb':  {'max_main': 69, 'max_bonus': 26, 'type': 'physical'},
            'mm':  {'max_main': 70, 'max_bonus': 25, 'type': 'physical'}
        }[self.lottery]
        
        self.max_main = self.config['max_main']
        self.max_bonus = self.config['max_bonus']
        self.is_rng = self.config['type'] == 'rng'
        
        # Models (will be initialized during training)
        self.lstm_models = [None] * 5  # One per position
        self.transformer_models = [None] * 5
        self.lgb_models = [None] * 5
        self.bonus_model = None
        
        print(f"\nInitialized {self.lottery.upper()} AI Predictor")
        print(f"  Draws: {len(self.draws)}")
        print(f"  Exclusions: {len(self.exclusions)}")
        print(f"  Type: {'RNG (focus AI)' if self.is_rng else 'Physical balls'}")
    
    def _load_draws(self):
        path = DATA_DIR / f'{self.lottery}.json'
        if path.exists():
            with open(path) as f:
                return json.load(f).get('draws', [])
        return []
    
    def _load_exclusions(self):
        path = DATA_DIR / 'past_winners_exclusions.json'
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                return set(tuple(sorted(c)) for c in data.get(self.lottery, []))
        return set()
    
    def _load_patterns(self):
        path = Path(__file__).parent / 'VALIDATED_PATTERNS.json'
        if path.exists():
            with open(path) as f:
                return json.load(f).get(self.lottery.upper(), {})
        return {}
    
    def prepare_sequences(self, position):
        """Prepare training sequences for a specific position."""
        if len(self.draws) < self.sequence_length + 1:
            return None, None
        
        sequences = []
        targets = []
        
        # Reverse to chronological order (oldest first)
        draws_chrono = list(reversed(self.draws))
        
        for i in range(len(draws_chrono) - self.sequence_length):
            # Get sequence of previous draws
            seq = []
            for j in range(self.sequence_length):
                draw = draws_chrono[i + j]
                main = sorted(draw['main'])
                # Features: all 5 main numbers + bonus, normalized
                features = [n / self.max_main for n in main] + [draw['bonus'] / self.max_bonus]
                seq.append(features)
            
            # Target: the number at this position in the next draw
            target_draw = draws_chrono[i + self.sequence_length]
            target_main = sorted(target_draw['main'])
            target = target_main[position]
            
            sequences.append(seq)
            targets.append(target - 1)  # 0-indexed for classification
        
        return np.array(sequences), np.array(targets)
    
    def train_lstm(self, position, epochs=50, batch_size=32, lr=0.001):
        """Train LSTM model for a specific position."""
        sequences, targets = self.prepare_sequences(position)
        if sequences is None:
            print(f"  Not enough data for position {position}")
            return
        
        # Split train/val
        split = int(len(sequences) * 0.8)
        train_dataset = LotteryDataset(sequences[:split], targets[:split])
        val_dataset = LotteryDataset(sequences[split:], targets[split:])
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Get position range from patterns
        pos_ranges = self.patterns.get('constraints', {}).get('position_ranges', [])
        if position < len(pos_ranges):
            min_val, max_val = pos_ranges[position]
            output_size = max_val - min_val + 1
        else:
            output_size = self.max_main
        
        # Create model
        model = LSTMPredictor(
            input_size=6,  # 5 main + 1 bonus
            hidden_size=128,
            num_layers=2,
            output_size=self.max_main,  # Predict any number
            dropout=0.3
        ).to(DEVICE)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
        
        best_acc = 0
        for epoch in range(epochs):
            model.train()
            train_loss = 0
            for seq, target in train_loader:
                seq, target = seq.to(DEVICE), target.to(DEVICE)
                
                optimizer.zero_grad()
                output = model(seq)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            # Validation
            model.eval()
            correct = 0
            total = 0
            with torch.no_grad():
                for seq, target in val_loader:
                    seq, target = seq.to(DEVICE), target.to(DEVICE)
                    output = model(seq)
                    pred = output.argmax(dim=1)
                    correct += (pred == target).sum().item()
                    total += target.size(0)
            
            val_acc = correct / total if total > 0 else 0
            scheduler.step(1 - val_acc)
            
            if val_acc > best_acc:
                best_acc = val_acc
                self.lstm_models[position] = model
            
            if (epoch + 1) % 10 == 0:
                print(f"    Epoch {epoch+1}: Loss={train_loss/len(train_loader):.4f}, Val Acc={val_acc:.4f}")
        
        print(f"    Best LSTM accuracy for P{position+1}: {best_acc:.4f}")
        return best_acc
    
    def train_transformer(self, position, epochs=50, batch_size=32, lr=0.0005):
        """Train Transformer model for a specific position."""
        sequences, targets = self.prepare_sequences(position)
        if sequences is None:
            return
        
        split = int(len(sequences) * 0.8)
        train_dataset = LotteryDataset(sequences[:split], targets[:split])
        val_dataset = LotteryDataset(sequences[split:], targets[split:])
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        model = TransformerPredictor(
            input_size=6,
            d_model=64,
            nhead=4,
            num_layers=2,
            output_size=self.max_main,
            dropout=0.2
        ).to(DEVICE)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        
        best_acc = 0
        for epoch in range(epochs):
            model.train()
            for seq, target in train_loader:
                seq, target = seq.to(DEVICE), target.to(DEVICE)
                optimizer.zero_grad()
                output = model(seq)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
            
            model.eval()
            correct = 0
            total = 0
            with torch.no_grad():
                for seq, target in val_loader:
                    seq, target = seq.to(DEVICE), target.to(DEVICE)
                    output = model(seq)
                    pred = output.argmax(dim=1)
                    correct += (pred == target).sum().item()
                    total += target.size(0)
            
            val_acc = correct / total if total > 0 else 0
            if val_acc > best_acc:
                best_acc = val_acc
                self.transformer_models[position] = model
        
        print(f"    Best Transformer accuracy for P{position+1}: {best_acc:.4f}")
        return best_acc
    
    def train_lightgbm(self, position):
        """Train LightGBM model for a specific position."""
        sequences, targets = self.prepare_sequences(position)
        if sequences is None:
            return
        
        # Flatten sequences to features
        X = sequences.reshape(len(sequences), -1)
        y = targets
        
        split = int(len(X) * 0.8)
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        params = {
            'objective': 'multiclass',
            'num_class': self.max_main,
            'metric': 'multi_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'verbose': -1
        }
        
        model = lgb.train(
            params, train_data, num_boost_round=200,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)]
        )
        
        # Calculate accuracy
        y_pred = model.predict(X_val).argmax(axis=1)
        acc = (y_pred == y_val).mean()
        
        self.lgb_models[position] = model
        print(f"    LightGBM accuracy for P{position+1}: {acc:.4f}")
        return acc
    
    def train_all(self, lstm_epochs=30, transformer_epochs=30):
        """Train all models for all positions."""
        print(f"\n{'='*60}")
        print(f"TRAINING AI MODELS FOR {self.lottery.upper()}")
        print(f"{'='*60}")
        
        if not self.is_rng:
            print(f"Note: {self.lottery.upper()} uses physical balls - AI may be less effective")
        
        results = {'lstm': [], 'transformer': [], 'lgb': []}
        
        for pos in range(5):
            print(f"\nPosition {pos + 1}:")
            
            # Train LSTM
            print("  Training LSTM...")
            lstm_acc = self.train_lstm(pos, epochs=lstm_epochs)
            results['lstm'].append(lstm_acc or 0)
            
            # Train Transformer
            print("  Training Transformer...")
            trans_acc = self.train_transformer(pos, epochs=transformer_epochs)
            results['transformer'].append(trans_acc or 0)
            
            # Train LightGBM
            print("  Training LightGBM...")
            lgb_acc = self.train_lightgbm(pos)
            results['lgb'].append(lgb_acc or 0)
        
        print(f"\n{'='*60}")
        print("TRAINING COMPLETE")
        print(f"{'='*60}")
        print(f"Average LSTM accuracy: {np.mean(results['lstm']):.4f}")
        print(f"Average Transformer accuracy: {np.mean(results['transformer']):.4f}")
        print(f"Average LightGBM accuracy: {np.mean(results['lgb']):.4f}")
        
        return results
    
    def predict_position(self, position, top_n=10):
        """Get top predictions for a position using ensemble."""
        # Get latest sequence
        if len(self.draws) < self.sequence_length:
            return list(range(1, top_n + 1))
        
        draws_chrono = list(reversed(self.draws))
        seq = []
        for j in range(self.sequence_length):
            draw = draws_chrono[-(self.sequence_length - j)]
            main = sorted(draw['main'])
            features = [n / self.max_main for n in main] + [draw['bonus'] / self.max_bonus]
            seq.append(features)
        
        seq = np.array([seq])
        
        # Collect predictions from all models
        all_probs = np.zeros(self.max_main)
        model_count = 0
        
        # LSTM prediction
        if self.lstm_models[position] is not None:
            model = self.lstm_models[position]
            model.eval()
            with torch.no_grad():
                seq_tensor = torch.FloatTensor(seq).to(DEVICE)
                probs = torch.softmax(model(seq_tensor), dim=1).cpu().numpy()[0]
                all_probs += probs * 1.0  # LSTM weight
                model_count += 1
        
        # Transformer prediction
        if self.transformer_models[position] is not None:
            model = self.transformer_models[position]
            model.eval()
            with torch.no_grad():
                seq_tensor = torch.FloatTensor(seq).to(DEVICE)
                probs = torch.softmax(model(seq_tensor), dim=1).cpu().numpy()[0]
                all_probs += probs * 1.0  # Transformer weight
                model_count += 1
        
        # LightGBM prediction
        if self.lgb_models[position] is not None:
            X = seq.reshape(1, -1)
            probs = self.lgb_models[position].predict(X)[0]
            all_probs += probs * 0.8  # LightGBM weight (slightly lower)
            model_count += 1
        
        if model_count == 0:
            return list(range(1, top_n + 1))
        
        # Average and get top predictions
        all_probs /= model_count
        
        # Apply position constraints
        pos_ranges = self.patterns.get('constraints', {}).get('position_ranges', [])
        if position < len(pos_ranges):
            min_val, max_val = pos_ranges[position]
            for i in range(self.max_main):
                if i + 1 < min_val or i + 1 > max_val:
                    all_probs[i] = 0
        
        # Get top predictions (1-indexed)
        top_indices = np.argsort(all_probs)[::-1][:top_n]
        return [i + 1 for i in top_indices]
    
    def generate_ticket(self):
        """Generate a complete ticket using AI predictions."""
        ticket = []
        used = set()
        
        for pos in range(5):
            candidates = self.predict_position(pos, top_n=20)
            
            # Pick best candidate not already used
            for num in candidates:
                if num not in used:
                    ticket.append(num)
                    used.add(num)
                    break
        
        # Sort ticket
        ticket = sorted(ticket)
        
        # Generate bonus (use frequency-based for now)
        bonus_freqs = Counter(d['bonus'] for d in self.draws)
        bonus = max(bonus_freqs.keys(), key=lambda x: bonus_freqs[x]) if bonus_freqs else 1
        
        return ticket, bonus
    
    def validate_and_score(self, ticket, bonus):
        """Validate ticket against constraints and score it."""
        ticket = sorted(ticket)
        
        # Check if excluded
        if tuple(ticket) in self.exclusions:
            return False, 0, "Past winner - excluded"
        
        # Check constraints
        constraints = self.patterns.get('constraints', {})
        
        # Sum range
        total = sum(ticket)
        sum_range = constraints.get('sum_range_95pct', [50, 200])
        if total < sum_range[0] or total > sum_range[1]:
            return False, 0, f"Sum {total} outside range {sum_range}"
        
        # Odd/even
        odds = sum(1 for n in ticket if n % 2 == 1)
        if odds < 2 or odds > 3:
            return False, 0, f"Odd count {odds} not optimal"
        
        # Consecutive pairs
        consec = sum(1 for i in range(len(ticket)-1) if ticket[i+1] - ticket[i] == 1)
        if consec > 1:
            return False, 0, f"Too many consecutive: {consec}"
        
        # Decades
        decades = len(set(n // 10 for n in ticket))
        if decades < 3:
            return False, 0, f"Only {decades} decades"
        
        # Score using position frequency
        score = 0
        draws_chrono = list(reversed(self.draws))
        pos_freqs = [{} for _ in range(5)]
        for draw in draws_chrono:
            main = sorted(draw['main'])
            for i, num in enumerate(main):
                pos_freqs[i][num] = pos_freqs[i].get(num, 0) + 1
        
        total_draws = len(draws_chrono)
        for i, num in enumerate(ticket):
            freq = pos_freqs[i].get(num, 0) / total_draws if total_draws > 0 else 0
            score += freq * 100
        
        return True, score, "Valid"
    
    def hunt_with_ai(self, num_tickets=100):
        """Generate tickets using AI and find the best ones."""
        print(f"\n{'='*60}")
        print(f"AI JACKPOT HUNT FOR {self.lottery.upper()}")
        print(f"{'='*60}")
        
        valid_tickets = []
        
        for i in range(num_tickets):
            ticket, bonus = self.generate_ticket()
            valid, score, reason = self.validate_and_score(ticket, bonus)
            
            if valid:
                valid_tickets.append({
                    'ticket': ticket,
                    'bonus': bonus,
                    'score': score
                })
        
        # Sort by score
        valid_tickets.sort(key=lambda x: -x['score'])
        
        print(f"\nGenerated {len(valid_tickets)} valid tickets out of {num_tickets}")
        
        if valid_tickets:
            print("\nTop 5 AI-Generated Tickets:")
            for i, t in enumerate(valid_tickets[:5]):
                print(f"  {i+1}. {t['ticket']} + Bonus: {t['bonus']} (Score: {t['score']:.2f})")
            
            best = valid_tickets[0]
            print(f"\n🎯 BEST AI TICKET: {best['ticket']} + Bonus: {best['bonus']}")
            return best
        
        return None


def main():
    """Run AI prediction for all RNG lotteries."""
    print("="*60)
    print("AI JACKPOT PREDICTOR")
    print("="*60)
    print(f"Device: {DEVICE}")
    
    results = {}
    
    # Focus on RNG lotteries (L4L and LA) - more predictable
    for lottery in ['l4l', 'la']:
        predictor = AIJackpotPredictor(lottery)
        
        # Train models
        predictor.train_all(lstm_epochs=30, transformer_epochs=30)
        
        # Generate tickets
        best = predictor.hunt_with_ai(num_tickets=200)
        if best:
            results[lottery] = best
    
    # Also generate for physical ball lotteries (less AI focus)
    for lottery in ['pb', 'mm']:
        predictor = AIJackpotPredictor(lottery)
        predictor.train_all(lstm_epochs=20, transformer_epochs=20)
        best = predictor.hunt_with_ai(num_tickets=100)
        if best:
            results[lottery] = best
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'method': 'AI Ensemble (LSTM + Transformer + LightGBM)',
        'ai_jackpot_tickets': {}
    }
    for lottery, result in results.items():
        output['ai_jackpot_tickets'][lottery] = {
            'main': result['ticket'],
            'bonus': result['bonus'],
            'score': result['score']
        }
    
    path = DATA_DIR / 'ai_jackpot_tickets.json'
    with open(path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "="*60)
    print("FINAL AI JACKPOT TICKETS")
    print("="*60)
    for lottery, result in results.items():
        print(f"{lottery.upper()}: {result['ticket']} + Bonus: {result['bonus']} (Score: {result['score']:.2f})")
    print(f"\n✅ Saved to {path}")


if __name__ == '__main__':
    main()
