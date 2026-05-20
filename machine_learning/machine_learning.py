import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

from sqlalchemy import create_engine
from dotenv import load_dotenv

from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix, 
    ConfusionMatrixDisplay, 
    classification_report, 
    balanced_accuracy_score
)

warnings.filterwarnings("ignore")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables and initialize database connection
load_dotenv()
engine = create_engine(os.getenv('DB_URL'))


def preprocess_data(columns_to_encode):
    """
    Constructs a scikit-learn ColumnTransformer to apply One-Hot Encoding 
    to categorical features while passing through numerical features.

    Args:
        columns_to_encode (list): List of categorical column names to encode.

    Returns:
        ColumnTransformer: The configured scikit-learn preprocessing transformer.
    """
    preprocess = ColumnTransformer(
        transformers=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'), columns_to_encode)
        ],
        remainder='passthrough'
    )
    return preprocess 


def calculate_random_forest(trees, depth, min_samples_leaf, class_weight, preprocess, X_train, y_train):
    """
    Defines, compiles, and trains a Random Forest Classifier pipeline.

    Args:
        trees (int): Number of estimators (trees) in the forest.
        depth (int): Maximum depth of the trees.
        min_samples_leaf (int): Minimum number of samples required to be at a leaf node.
        class_weight (str): Weights associated with classes to handle imbalance.
        preprocess (ColumnTransformer): The preprocessing steps for the pipeline.
        X_train (pd.DataFrame): Training feature set.
        y_train (pd.Series): Target variable (runway configuration).

    Returns:
        Pipeline: The trained scikit-learn model pipeline.
    """
    runway_pipeline = Pipeline(steps=[
        ('preprocess', preprocess),
        ('classifier', RandomForestClassifier(
            n_estimators=trees,        
            max_depth=depth,              
            min_samples_leaf=min_samples_leaf,
            class_weight=class_weight,
            min_samples_split=10,
            max_features='sqrt',
            bootstrap=True,
            oob_score=True,
            random_state=42,
            n_jobs=-1
        ))
    ])
    runway_pipeline.fit(X_train, y_train)
    return runway_pipeline


def data_ml_conversion(df):
    """
    Prepares and transforms features for ML modeling, including cyclical 
    encoding (sine/cosine) for continuous temporal and directional data, 
    and applies custom logic for seasonal wind directions.

    Args:
        df (pd.DataFrame): The base feature dataframe.

    Returns:
        pd.DataFrame: The transformed dataframe ready for the ML pipeline.
    """
    df['ceiling_height'] = df['ceiling_height'].fillna(100000)
    df['min_clouds_height'] = df['min_clouds_height'].fillna(100000)

    df['hour_int'] = df['hour'].dt.hour

    # Cyclical encoding
    df['wind_dir_sin'] = np.sin(2 * np.pi * df['wind_dir'] / 360)
    df['wind_dir_cos'] = np.cos(2 * np.pi * df['wind_dir'] / 360)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour_int'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_int'] / 24)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    # Seasonal wind mapping created prior to dropping the base wind direction column
    df['spring_summer_wind'] = df.apply(lambda x: x['wind_dir'] if x['season'] in [1, 2] else 0, axis=1)

    df.drop(columns=['wind_dir', 'hour', 'month', 'hour_int'], inplace=True)
    return df


def features_plot(pipeline, categorical_columns, X):
    """
    Extracts feature importances from the trained Random Forest model 
    and saves a horizontal bar chart of the top 10 features to disk.

    Args:
        pipeline (Pipeline): The trained scikit-learn model pipeline.
        categorical_columns (list): List of categorical column names.
        X (pd.DataFrame): The feature dataset used during training.
    """
    ohe_feature_names = pipeline.named_steps['preprocess']\
        .named_transformers_['onehot']\
        .get_feature_names_out(categorical_columns)

    numeric_features = [col for col in X.columns if col not in categorical_columns]
    all_feature_names = list(ohe_feature_names) + numeric_features
    importances = pipeline.named_steps['classifier'].feature_importances_

    feat_importances = pd.Series(importances, index=all_feature_names)
    feat_importances.nlargest(10).plot(kind='barh', color='steelblue', figsize=(10,6))

    plt.title("Top 10 Features - Runway Selection Importance")
    plt.xlabel("Relative Importance Score")
    plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()


def confusion_matrix_plot(pipeline, X_test, y_test, model_name="Model"):
    """
    Generates and saves a confusion matrix plot for model evaluation.

    Args:
        pipeline (Pipeline): The trained ML pipeline.
        X_test (pd.DataFrame): The testing feature set.
        y_test (pd.Series): The actual target values for the testing set.
        model_name (str): Identifier used in the plot title and saved filename.
    """
    y_pred = pipeline.predict(X_test)
    labels = pipeline.classes_
    cm = confusion_matrix(y_test, y_pred, labels=labels)

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap=plt.cm.Blues)
    plt.title(f"Confusion Matrix: Predicted vs Actual Runway | {model_name}")
    
    safe_name = model_name.replace(" ", "_").lower()
    plt.savefig(f'confusion_matrix_{safe_name}.png', dpi=300, bbox_inches='tight')
    plt.close()


def classification_report_plot(pipeline, X_test, y_test):
    """
    Outputs the standard classification report and balanced accuracy score.

    Args:
        pipeline (Pipeline): The trained ML pipeline.
        X_test (pd.DataFrame): The testing feature set.
        y_test (pd.Series): The actual target values for the testing set.
    """
    y_pred = pipeline.predict(X_test)
    labels = pipeline.classes_
    print(classification_report(y_test, y_pred, labels=labels))
    print(f"Balanced Accuracy: {balanced_accuracy_score(y_test, y_pred):.4f}")


def set_data():
    """
    Connects to the database, retrieves historical feature data, applies ML 
    conversions, and identifies categorical columns for the pipeline.

    Returns:
        tuple: The processed dataframe and a list of categorical column names.
    """
    query = """
        SELECT wind_dir, wind_speed, is_wind_vrb,
        min_clouds_height, ceiling_height, ceiling_category, visibility,
        weather_intensity, weather_category,
        season, hour, is_night, month,
        runway_config 
        FROM final_features 
        ORDER BY timestamp
    """
    df = pd.read_sql(query, engine)
    df = data_ml_conversion(df)
    categorical_columns = ['weather_category', 'weather_intensity', 'ceiling_category', 'season']
    return df, categorical_columns


if __name__ == "__main__":
    
    df, categorical_columns = set_data()
    preprocess = preprocess_data(categorical_columns)

    # Feature and target separation
    X = df.drop(['runway_config'], axis=1)
    y = df['runway_config']

    tscv = TimeSeriesSplit(n_splits=5, test_size=len(df)//10, gap=24)
    all_balanced_acc = []

    print("--- Starting Forward Chaining Cross-Validation ---")

    for fold, (train_index, test_index) in enumerate(tscv.split(X), 1):
        X_train_fold, X_test_fold = X.iloc[train_index], X.iloc[test_index]
        y_train_fold, y_test_fold = y.iloc[train_index], y.iloc[test_index]
        
        pipeline = calculate_random_forest(
            trees=300, 
            depth=8, 
            min_samples_leaf=5, 
            class_weight='balanced',
            preprocess=preprocess,
            X_train=X_train_fold,
            y_train=y_train_fold
        )
        
        y_pred = pipeline.predict(X_test_fold)
        fold_acc = balanced_accuracy_score(y_test_fold, y_pred)
        all_balanced_acc.append(fold_acc)
        
        print(f"Fold {fold}: Training size: {len(X_train_fold)} | Test size: {len(X_test_fold)} | Balanced Acc: {fold_acc:.4f}")
        classification_report_plot(pipeline, X_test_fold, y_test_fold)
        confusion_matrix_plot(pipeline, X_test_fold, y_test_fold, model_name=f"RF Fold {fold}")

    print("\n--- Summary Results ---")
    print(f"Mean Balanced Accuracy: {np.mean(all_balanced_acc):.4f}")
    print(f"Standard Deviation: {np.std(all_balanced_acc):.4f}")

    # Generate the final feature importance plot using the last trained pipeline instance
    features_plot(pipeline, categorical_columns, X)