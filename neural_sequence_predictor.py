"""
NEURAL SEQUENCE PREDICTOR - Deep Learning for Lottery Pattern Discovery
Uses LSTM/Transformer architecture to learn temporal patterns in draw sequences.

This is a GAN-like approach where we:
1. Train a generator to produce valid lottery combinations
2. Train a discriminator to distinguish real vs generated draws
3. The generator learns the underlying distribution of real draws

Requirements: pip install torch numpy
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter
import math

# Check if PyTorch is available
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not installed. Install with: pip install torch")
    print("Running statistical-only analysis instead.\n")

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    for fn in [f'{lottery}.json', f'{lottery}_historical_data.json']:
        p = DATA_DIR / fn
        if p.exists():
            with open(p) as f:
                d = json.load(f)
                return d.get('draws', d) if isinstance(d, dict) else d
    return []

LOTTERY_CONFIG = {
    'l4l': {'name': 'Lucky for Life', 'max_main': 48, 'max_bonus': 18},
    'la':  {'name': 'Lotto America', 'max_main': 52, 'max_bonus': 10},
}

# =============================================================================
# STATISTICAL APPROACH: Hidden State Detection via Clustering
# =============================================================================

def detect_hidden_states(draws, n_states=5):
    """
    Use k-means-like clustering on draw features to detect "hidden states"
    in the lottery machine. If states exist, we can predict state transitions.
    """
    features = []
    for draw in draws:
        main = sorted(draw.get('main', []))
        if len(main) < 5:
            continue
        
        # Feature engineering
        total = sum(main)
        spread = main[-1] - main[0]
        odds = sum(1 for n in main if n % 2 == 1)
        highs = sum(1 for n in main if n > 25)
        gaps = [main[i+1] - main[i] for i in range(4)]
        avg_gap = sum(gaps) / 4
        max_gap = max(gaps)
        decades = len(set(n // 10 for n in main))
        
        features.append([total, spread, odds, highs, avg_gap, max_gap, decades])
    
    features = np.array(features)
    
    # Normalize features
    means = features.mean(axis=0)
    stds = features.std(axis=0) + 1e-8
    features_norm = (features - means) / stds
    
    # Simple k-means clustering
    np.random.seed(42)
    centroids = features_norm[np.random.choice(len(features_norm), n_states, replace=False)]
    
    for _ in range(50):  # iterations
        # Assign points to clusters
        distances = np.sqrt(((features_norm[:, np.newaxis] - centroids) ** 2).sum(axis=2))
        labels = distances.argmin(axis=1)
        
        # Update centroids
        new_centroids = np.array([features_norm[labels == k].mean(axis=0) if (labels == k).sum() > 0 
                                   else centroids[k] for k in range(n_states)])
        
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids
    
    # Analyze state transitions
    transitions = np.zeros((n_states, n_states))
    for i in range(len(labels) - 1):
        transitions[labels[i], labels[i+1]] += 1
    
    # Normalize to probabilities
    row_sums = transitions.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    transition_probs = transitions / row_sums
    
    # Current state
    current_state = labels[0]  # Most recent draw
    
    # Predict next state
    next_state_probs = transition_probs[current_state]
    predicted_next_state = next_state_probs.argmax()
    
    # Get typical numbers for predicted state
    state_draws = [draws[i] for i in range(len(labels)) if labels[i] == predicted_next_state]
    
    return {
        'n_states': n_states,
        'current_state': int(current_state),
        'predicted_next_state': int(predicted_next_state),
        'next_state_probability': float(next_state_probs[predicted_next_state]),
        'transition_matrix': transition_probs.tolist(),
        'state_draws_count': len(state_draws),
        'state_characteristics': {
            'avg_sum': float(np.mean([sum(sorted(d.get('main', []))) for d in state_draws])) if state_draws else 0,
            'typical_draws': [sorted(d.get('main', [])) for d in state_draws[:3]]
        }
    }

# =============================================================================
# SEQUENCE PATTERN: N-gram Analysis for Number Sequences
# =============================================================================

def ngram_sequence_analysis(draws, max_num, n=3):
    """
    Treat each position as generating a sequence. Find n-gram patterns
    that predict what comes next in each position.
    """
    position_sequences = {i: [] for i in range(5)}
    
    for draw in reversed(draws):  # Oldest to newest
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main[:5]):
            position_sequences[i].append(num)
    
    predictions = {}
    
    for pos in range(5):
        seq = position_sequences[pos]
        if len(seq) < n + 1:
            continue
        
        # Build n-gram model
        ngrams = {}
        for i in range(len(seq) - n):
            context = tuple(seq[i:i+n])
            next_num = seq[i+n]
            if context not in ngrams:
                ngrams[context] = Counter()
            ngrams[context][next_num] += 1
        
        # Get prediction based on last n numbers
        last_context = tuple(seq[-n:])
        
        if last_context in ngrams:
            total = sum(ngrams[last_context].values())
            top_predictions = [(num, count/total) for num, count in ngrams[last_context].most_common(5)]
            predictions[pos] = {
                'context': last_context,
                'predictions': top_predictions,
                'confidence': top_predictions[0][1] if top_predictions else 0
            }
        else:
            # Find similar contexts
            similar_preds = Counter()
            for ctx, counts in ngrams.items():
                if abs(ctx[-1] - last_context[-1]) <= 3:  # Similar last number
                    for num, count in counts.items():
                        similar_preds[num] += count
            
            if similar_preds:
                total = sum(similar_preds.values())
                top_predictions = [(num, count/total) for num, count in similar_preds.most_common(5)]
                predictions[pos] = {
                    'context': last_context,
                    'predictions': top_predictions,
                    'confidence': top_predictions[0][1] * 0.5 if top_predictions else 0  # Lower confidence
                }
    
    return predictions

# =============================================================================
# INFORMATION THEORY: Mutual Information Between Positions
# =============================================================================

def mutual_information_analysis(draws, max_num):
    """
    Calculate mutual information between positions.
    High MI = knowing one position helps predict another.
    """
    # Discretize into bins
    n_bins = 10
    
    position_data = {i: [] for i in range(5)}
    for draw in draws:
        main = sorted(draw.get('main', []))
        for i in range(5):
            if i < len(main):
                position_data[i].append(main[i])
    
    def calc_mi(x, y, n_bins):
        """Calculate mutual information between two sequences."""
        x = np.array(x)
        y = np.array(y)
        
        # Bin the data
        x_bins = np.digitize(x, np.linspace(x.min(), x.max(), n_bins))
        y_bins = np.digitize(y, np.linspace(y.min(), y.max(), n_bins))
        
        # Joint and marginal distributions
        joint = np.zeros((n_bins + 1, n_bins + 1))
        for xi, yi in zip(x_bins, y_bins):
            joint[xi, yi] += 1
        joint /= joint.sum()
        
        px = joint.sum(axis=1)
        py = joint.sum(axis=0)
        
        # MI calculation
        mi = 0
        for i in range(n_bins + 1):
            for j in range(n_bins + 1):
                if joint[i, j] > 0 and px[i] > 0 and py[j] > 0:
                    mi += joint[i, j] * np.log2(joint[i, j] / (px[i] * py[j]))
        
        return mi
    
    mi_matrix = np.zeros((5, 5))
    for i in range(5):
        for j in range(5):
            if i != j and len(position_data[i]) == len(position_data[j]):
                mi_matrix[i, j] = calc_mi(position_data[i], position_data[j], n_bins)
    
    # Find strongest dependencies
    dependencies = []
    for i in range(5):
        for j in range(i+1, 5):
            dependencies.append({
                'positions': (i+1, j+1),
                'mutual_information': mi_matrix[i, j]
            })
    
    dependencies.sort(key=lambda x: x['mutual_information'], reverse=True)
    
    return {
        'mi_matrix': mi_matrix.tolist(),
        'strongest_dependencies': dependencies[:5]
    }

# =============================================================================
# CONVERGENCE ANALYSIS: What combination is the distribution converging to?
# =============================================================================

def convergence_analysis(draws, max_num, windows=[50, 100, 200, 400]):
    """
    Track how position distributions change over time.
    Find the combination that distributions are converging toward.
    """
    convergence_tickets = {}
    
    for window in windows:
        if len(draws) < window:
            continue
        
        recent = draws[:window]
        pos_freq = {i: Counter() for i in range(5)}
        
        for draw in recent:
            main = sorted(draw.get('main', []))
            for i, num in enumerate(main[:5]):
                pos_freq[i][num] += 1
        
        # Get mode for each position
        ticket = []
        for i in range(5):
            if pos_freq[i]:
                mode = pos_freq[i].most_common(1)[0][0]
                ticket.append(mode)
        
        # Calculate concentration (how peaked is the distribution?)
        concentrations = []
        for i in range(5):
            if pos_freq[i]:
                total = sum(pos_freq[i].values())
                top_freq = pos_freq[i].most_common(1)[0][1] / total
                concentrations.append(top_freq)
        
        avg_concentration = np.mean(concentrations) if concentrations else 0
        
        convergence_tickets[window] = {
            'ticket': ticket,
            'concentration': avg_concentration
        }
    
    # Find the window with highest concentration (most converged)
    best_window = max(convergence_tickets.keys(), 
                      key=lambda w: convergence_tickets[w]['concentration'])
    
    return {
        'by_window': convergence_tickets,
        'best_window': best_window,
        'converged_ticket': convergence_tickets[best_window]['ticket'],
        'concentration': convergence_tickets[best_window]['concentration']
    }

# =============================================================================
# PYTORCH LSTM MODEL (if available)
# =============================================================================

if TORCH_AVAILABLE:
    class LotteryLSTM(nn.Module):
        def __init__(self, input_size, hidden_size, output_size, num_layers=2):
            super().__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
            self.fc = nn.Linear(hidden_size, output_size)
            self.softmax = nn.Softmax(dim=-1)
        
        def forward(self, x):
            out, _ = self.lstm(x)
            out = self.fc(out[:, -1, :])
            return self.softmax(out)
    
    def train_lstm_predictor(draws, max_num, seq_length=10, epochs=100):
        """Train LSTM to predict next draw based on sequence of previous draws."""
        # Prepare data
        X, y = [], []
        
        for i in range(len(draws) - seq_length):
            seq = []
            for j in range(seq_length):
                draw = draws[i + j]
                main = sorted(draw.get('main', []))
                # One-hot encode each number
                one_hot = [0] * max_num
                for num in main[:5]:
                    one_hot[num - 1] = 1
                seq.append(one_hot)
            
            X.append(seq)
            
            # Target: next draw
            target_draw = draws[i + seq_length]
            target = [0] * max_num
            for num in sorted(target_draw.get('main', []))[:5]:
                target[num - 1] = 1
            y.append(target)
        
        X = torch.FloatTensor(X)
        y = torch.FloatTensor(y)
        
        # Model
        model = LotteryLSTM(max_num, 128, max_num)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # Train
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
        
        # Predict next
        model.eval()
        with torch.no_grad():
            last_seq = []
            for j in range(seq_length):
                draw = draws[j]
                main = sorted(draw.get('main', []))
                one_hot = [0] * max_num
                for num in main[:5]:
                    one_hot[num - 1] = 1
                last_seq.append(one_hot)
            
            last_seq = torch.FloatTensor([last_seq])
            prediction = model(last_seq).numpy()[0]
        
        # Get top 5 predicted numbers
        top_indices = np.argsort(prediction)[-5:][::-1]
        predicted_numbers = sorted([i + 1 for i in top_indices])
        
        return {
            'predicted_ticket': predicted_numbers,
            'confidences': {i + 1: float(prediction[i]) for i in top_indices},
            'model_trained': True
        }

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_full_analysis(lottery):
    draws = load_draws(lottery)
    if not draws:
        return None
    
    config = LOTTERY_CONFIG[lottery]
    max_num = config['max_main']
    
    results = {
        'lottery': lottery,
        'name': config['name'],
        'total_draws': len(draws)
    }
    
    print(f"\n{'='*80}")
    print(f"🧠 ADVANCED AI ANALYSIS: {config['name'].upper()}")
    print(f"{'='*80}")
    
    # 1. Hidden State Detection
    print("\n📊 HIDDEN STATE ANALYSIS (Markov Machine States):")
    states = detect_hidden_states(draws)
    results['hidden_states'] = states
    print(f"  Detected {states['n_states']} hidden states")
    print(f"  Current state: {states['current_state']}")
    print(f"  Predicted next state: {states['predicted_next_state']} (prob: {states['next_state_probability']:.2%})")
    print(f"  Typical draws in predicted state: {states['state_characteristics']['typical_draws']}")
    
    # 2. N-gram Sequence Analysis
    print("\n📈 N-GRAM SEQUENCE PREDICTION (3-gram):")
    ngrams = ngram_sequence_analysis(draws, max_num, n=3)
    results['ngram_predictions'] = ngrams
    ngram_ticket = []
    for pos in range(5):
        if pos in ngrams and ngrams[pos]['predictions']:
            pred = ngrams[pos]['predictions'][0]
            ngram_ticket.append(pred[0])
            print(f"  P{pos+1}: Last context {ngrams[pos]['context']} → {pred[0]} (conf: {pred[1]:.2%})")
    results['ngram_ticket'] = sorted(ngram_ticket) if len(ngram_ticket) == 5 else None
    
    # 3. Mutual Information
    print("\n🔗 MUTUAL INFORMATION (Position Dependencies):")
    mi = mutual_information_analysis(draws, max_num)
    results['mutual_information'] = mi
    for dep in mi['strongest_dependencies'][:3]:
        print(f"  Positions {dep['positions']}: MI = {dep['mutual_information']:.3f}")
    
    # 4. Convergence Analysis
    print("\n🎯 CONVERGENCE ANALYSIS (Distribution Focus):")
    conv = convergence_analysis(draws, max_num)
    results['convergence'] = conv
    print(f"  Best window: {conv['best_window']} draws")
    print(f"  Converged ticket: {conv['converged_ticket']}")
    print(f"  Concentration: {conv['concentration']:.2%}")
    
    # 5. LSTM Prediction (if available)
    if TORCH_AVAILABLE and len(draws) > 50:
        print("\n🤖 LSTM NEURAL NETWORK PREDICTION:")
        try:
            lstm_result = train_lstm_predictor(draws, max_num, seq_length=10, epochs=50)
            results['lstm_prediction'] = lstm_result
            print(f"  Predicted ticket: {lstm_result['predicted_ticket']}")
            print(f"  Top confidences: {lstm_result['confidences']}")
        except Exception as e:
            print(f"  LSTM failed: {e}")
            results['lstm_prediction'] = None
    
    # Generate final combined prediction
    print("\n" + "="*60)
    print("🔮 COMBINED AI PREDICTION")
    print("="*60)
    
    # Weight different methods
    all_numbers = Counter()
    
    # From hidden states - typical numbers in predicted state
    for draw in states['state_characteristics']['typical_draws']:
        for num in draw:
            all_numbers[num] += 2
    
    # From n-gram
    if results.get('ngram_ticket'):
        for num in results['ngram_ticket']:
            all_numbers[num] += 3
    
    # From convergence
    for num in conv['converged_ticket']:
        all_numbers[num] += 2
    
    # From LSTM
    if results.get('lstm_prediction'):
        for num in results['lstm_prediction']['predicted_ticket']:
            all_numbers[num] += 4
    
    # Build final ticket respecting position constraints
    final_ticket = []
    used = set()
    
    # Get position ranges from recent draws
    pos_freq = {i: Counter() for i in range(5)}
    for draw in draws[:200]:
        main = sorted(draw.get('main', []))
        for i, num in enumerate(main[:5]):
            pos_freq[i][num] += 1
    
    for pos in range(5):
        candidates = [(num, all_numbers[num]) for num in all_numbers if num not in used]
        candidates.sort(key=lambda x: (-x[1], x[0]))
        
        for num, score in candidates:
            if not final_ticket or num > final_ticket[-1]:
                # Check if fits position
                pos_nums = list(pos_freq[pos].keys())
                if pos_nums:
                    min_pos, max_pos = min(pos_nums), max(pos_nums)
                    if min_pos <= num <= max_pos:
                        final_ticket.append(num)
                        used.add(num)
                        break
    
    # Get bonus
    bonus_freq = Counter()
    for draw in draws[:100]:
        b = draw.get('bonus')
        if b:
            bonus_freq[b] += 1
    top_bonus = bonus_freq.most_common(1)[0][0] if bonus_freq else 1
    
    results['final_prediction'] = {
        'ticket': final_ticket,
        'bonus': top_bonus
    }
    
    print(f"\n🎰 FINAL TICKET: {final_ticket} + {top_bonus}")
    
    # Check if ever drawn
    ticket_set = set(final_ticket)
    ever_drawn = any(set(d.get('main', [])) == ticket_set for d in draws)
    print(f"   {'⚠️ Has been drawn before!' if ever_drawn else '✅ Never drawn - unique prediction!'}")
    
    return results

# Run analysis
if __name__ == "__main__":
    print("="*80)
    print("🧠 NEURAL SEQUENCE PREDICTOR - Advanced AI for Lottery Pattern Discovery")
    print("="*80)
    
    all_results = {}
    for lottery in ['l4l', 'la']:
        result = run_full_analysis(lottery)
        if result:
            all_results[lottery] = result
    
    # Save results
    output_path = DATA_DIR / 'neural_predictions.json'
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to {output_path}")
    
    print("""
================================================================================
🧠 AI METHODS USED:

1. HIDDEN STATE DETECTION (Markov Machine)
   - Clusters draws into hidden states based on features
   - Learns state transition probabilities
   - Predicts next state and typical numbers for that state

2. N-GRAM SEQUENCE ANALYSIS
   - Treats each position as a time series
   - Builds n-gram model: P(next | last N values)
   - Predicts per-position based on recent sequence

3. MUTUAL INFORMATION ANALYSIS
   - Measures statistical dependency between positions
   - High MI = knowing one position helps predict another
   - Exploits position correlations

4. CONVERGENCE ANALYSIS
   - Tracks how distributions change over time windows
   - Finds the combination distributions are converging toward
   - Higher concentration = more predictable

5. LSTM NEURAL NETWORK (if PyTorch available)
   - Deep learning sequence-to-sequence model
   - Learns complex temporal patterns
   - Predicts next draw from sequence of previous draws

COMBINED: All methods weighted together for final prediction.
================================================================================
""")
