print("optuna_trial.py, new code")
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.2
#   kernelspec:
#     display_name: TFM
#     language: python
#     name: tfm
# ---

# %%
from new_train import main, load_files_wrapper
import pandas as pd
import gc
import os
import tensorflow as tf
import optuna
import multiprocessing
import datetime

from optuna.artifacts import FileSystemArtifactStore
from optuna.artifacts import upload_artifact


base_path = "./all_data_2024-07-17/"
os.makedirs(base_path, exist_ok=True)
artifact_store = FileSystemArtifactStore(base_path=base_path)

path = "all_data_2024-07-17/"
file_path = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
os.makedirs(path+file_path, exist_ok=True)
print("trial folder created:", path+file_path)

lightcurves = load_files_wrapper(path=path, use_wavelet=True)

def objective(trial):
    global lightcurves
    sigma = 20
    sigma_upper = 5
    num_bins_global = 2001
    bin_width_factor_global = 1 / 2001
    num_bins_local = 201
    bin_width_factor_local = 0.16
    num_durations = 4
    levels_global = 6
    levels_local = 3
    wavelet_family = "sym5"
    
    
    use_wavelet = True
    binary_classification = True
    k_fold = None
    global_level_list = (1, 5,)
    local_level_list = (1, 3,)
    epochs = 1
    batch_size = 128
    l1 = 0.00
    l2 = 0.0
    dropout = 0.0
    β = 2.0
    frac =  trial.suggest_float("frac", 0.1, 0.9)
    
    
    
    download_dir="data3/"
    path = "all_data_2024-07-17/"
    df_path = 'cumulative_2024.06.01_09.08.01.csv'
    use_download_cache = True
    lightcurve_cache = True
    
    n_proc = int(multiprocessing.cpu_count()*1.25)
    parallel = True

    
    precision, recall, F1, Fβ, cm, num2class, history_1 = main(sigma=sigma, sigma_upper=sigma_upper,
                num_bins_global=num_bins_global, bin_width_factor_global=bin_width_factor_global,
                num_bins_local=num_bins_local, bin_width_factor_local=bin_width_factor_local, num_durations=num_durations,
                levels_global=levels_global, levels_local=levels_local, wavelet_family=wavelet_family,
                use_wavelet=use_wavelet, binary_classification=binary_classification,
                k_fold=k_fold,
                global_level_list=global_level_list, local_level_list=local_level_list,
                l1=l1, l2=l2, dropout=dropout,
                epochs=epochs, batch_size=batch_size,
                frac=frac, β=β,
                download_dir=download_dir,
                path=path,
                df_path=df_path,
                use_download_cache=use_download_cache,
                n_proc=n_proc,
                parallel=parallel,
                lightcurve_cache=lightcurve_cache,
                lightcurves=lightcurves,
        )

    gc.collect()
    tf.keras.backend.clear_session()

    variables = ["sigma", "sigma_upper",
                "num_bins_global", "bin_width_factor_global",
                "num_bins_local", "bin_width_factor_local", "num_durations",
                "levels_global", "levels_local", "wavelet_family",
                "use_wavelet", "binary_classification",
                "k_fold",
                "global_level_list", "local_level_list",
                "l1", "l2","dropout",
                "epochs", "batch_size",
                "frac", "β",
                "download_dir",
                "path",
                "df_path",
                "use_download_cache",
                "n_proc",
                "parallel",
                "lightcurve_cache",
                ]
    local_dict = locals()
    variables_dict = {variable: local_dict.get(variable, trial.params.get(variable)) for variable in variables}
    variables_dict.update({ "precision": precision, "recall": recall, "F1": F1, "Fβ": Fβ,
                  "cm_00": cm[0][0], "cm_01": cm[0][1], "cm_10": cm[1][0], "cm_11": cm[1][1], "0": num2class[0], "1": num2class[1]})
    result_df = pd.DataFrame([variables_dict])

    now = datetime.datetime.now().strftime("%s")
    # upload_artifact(trial, path+file_path+"/"+now, artifact_store)
    result_df.to_csv(path+file_path+"/"+now+".csv", index=False)

    return F1

storage = optuna.storages.JournalStorage(
   optuna.storages.JournalFileStorage("./journal.log"),
)
study = optuna.create_study(direction="maximize", storage=storage)
study.optimize(objective, n_trials=10)

trial = study.best_trial

print("Accuracy: {}".format(trial.value))
print("Best hyperparameters: {}".format(trial.params))
