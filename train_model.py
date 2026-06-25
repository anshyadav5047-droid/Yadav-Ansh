import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import warnings
warnings.filterwarnings('ignore')

print("Generating synthetic UPI transaction data...")

# Generate synthetic data
np.random.seed(42)
n_samples = 8000

# Generate features
data = {
    'step': np.random.randint(1, 744, n_samples),
    'type': np.random.choice(['CASH_OUT', 'PAYMENT', 'TRANSFER', 'DEBIT'], n_samples),
    'amount': np.random.exponential(scale=10000, size=n_samples),
    'oldbalanceOrg': np.random.exponential(scale=50000, size=n_samples),
    'newbalanceOrig': np.random.exponential(scale=45000, size=n_samples),
    'oldbalanceDest': np.random.exponential(scale=30000, size=n_samples),
    'newbalanceDest': np.random.exponential(scale=35000, size=n_samples)
}

df = pd.DataFrame(data)

# Generate fraud labels based on patterns
fraud_prob = np.zeros(n_samples)

# Higher fraud probability for large amounts
fraud_prob += (df['amount'] > 50000).astype(int) * 0.3
fraud_prob += (df['amount'] > 100000).astype(int) * 0.4

# Higher fraud for certain transaction types
fraud_prob += (df['type'] == 'TRANSFER').astype(int) * 0.2
fraud_prob += (df['type'] == 'CASH_OUT').astype(int) * 0.15

# Balance anomalies
balance_change = df['oldbalanceOrg'] - df['newbalanceOrig']
fraud_prob += (balance_change < 0).astype(int) * 0.25
fraud_prob += ((df['newbalanceDest'] - df['oldbalanceDest']) > df['amount']).astype(int) * 0.3

# Add some randomness
fraud_prob += np.random.random(n_samples) * 0.1

# Normalize and create labels
fraud_prob = np.clip(fraud_prob, 0, 1)
df['isFraud'] = (fraud_prob > 0.5).astype(int)

print(f"Generated {n_samples} transactions with {df['isFraud'].sum()} fraud cases")

# Save dataset
df.to_csv('dataset.csv', index=False)
print("Dataset saved to dataset.csv")

print("\nTraining machine learning model...")

# Feature engineering
df['hour'] = df['step'] % 24
df['balance_diff_orig'] = df['oldbalanceOrg'] - df['newbalanceOrig']
df['balance_diff_dest'] = df['newbalanceDest'] - df['oldbalanceDest']
df['amount_ratio'] = df['amount'] / (df['oldbalanceOrg'] + 1)

# Encode categorical variables
label_encoder = LabelEncoder()
df['type_encoded'] = label_encoder.fit_transform(df['type'])

# Select features
feature_columns = ['step', 'type_encoded', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
                   'oldbalanceDest', 'newbalanceDest', 'hour', 'balance_diff_orig', 
                   'balance_diff_dest', 'amount_ratio']

X = df[feature_columns]
y = df['isFraud']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train model
print("Training Random Forest Classifier...")
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Evaluate
train_accuracy = model.score(X_train, y_train)
test_accuracy = model.score(X_test, y_test)

print(f"\nTraining Accuracy: {train_accuracy:.4f}")
print(f"Test Accuracy: {test_accuracy:.4f}")

# Save model
model_data = {
    'model': model,
    'label_encoder': label_encoder,
    'feature_columns': feature_columns
}

joblib.dump(model_data, 'upi_fraud_detection_model.pkl')
print("\nModel saved to upi_fraud_detection_model.pkl")
print("Training complete!")
