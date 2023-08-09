import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

import torch as th

from transformers import TrainingArguments
from transformers import (
    RobertaTokenizerFast,
    RobertaForSequenceClassification,
    RobertaConfig,
)

from clearml import Task


from utils import train_grader_model, prepare_grader_data


# Define constants
DEBUG = True
SUDY_NUMBER = 1

data_used = "famous"
layers_trained = "classifier"

EXPERIMENT_NAME = f'study_{SUDY_NUMBER}_{data_used}_{layers_trained}'

# Set up environment
task = Task.init(project_name="Kai/AMI", task_name="first train")
trained_model_path = f"./trained_models/{EXPERIMENT_NAME}.pt"
data_dir = f"textwash_data/study{SUDY_NUMBER}/intruder_test/full_data_study.csv"
DEVICE = "cuda" if th.cuda.is_available() else "cpu"

# Cancel wandb logging
os.environ["WANDB_DISABLED"] = "true"


# Set seeds
SEED = 42
np.random.seed(SEED)
th.manual_seed(SEED)


# Set up the training arguments
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=16,
    logging_dir="./logs",
    logging_strategy="steps",
    logging_steps=10,
    evaluation_strategy="epoch",
    save_total_limit=1,
    save_strategy="epoch",
    load_best_model_at_end=True,
    report_to="tensorboard",
    # dataloader_pin_memory=False,
)


# Read the data
columns_to_read = ["type", "text", "file_id", "name", "got_name_truth_q2"]
raw_data = pd.read_csv(data_dir, usecols=columns_to_read)


# Aggregate by file_id and calculate the rate of re-identification
data = (
    raw_data.groupby(["type", "file_id", "name", "text"])
    .agg({"got_name_truth_q2": "mean"})
    .reset_index()
)
data.rename(columns={"got_name_truth_q2": "human_rate"}, inplace=True)

# Use only type famous
data = data[data["type"] == "famous"]

datasets = prepare_grader_data(data, SEED, DEVICE)


model = train_grader_model(datasets, SEED, training_args, trained_model_path, DEVICE)

# save model
th.save(model.state_dict(), trained_model_path)
