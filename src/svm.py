# Credits :
# https://github.com/syamkakarla98/Hyperspectral_Image_Analysis_Simplified
# https://medium.com/@pushkarmandot/what-is-the-significance-of-c-value-in-support-vector-machine-28224e852c5a

# Data sources :
# http://www.ehu.eus/ccwintco/uploads/6/67/Indian_pines_corrected.mat
# http://www.ehu.eus/ccwintco/uploads/c/c4/Indian_pines_gt.mat

import sys
import time
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from scipy.io import loadmat
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report
import numpy as np
from scipy.stats import norm

# !wget http://www.ehu.eus/ccwintco/uploads/6/67/Indian_pines_corrected.mat http://www.ehu.eus/ccwintco/uploads/c/c4/Indian_pines_gt.mat


def read_files(HSI_path, GT_path):
    X = loadmat(HSI_path)[HSI_path.replace("/", ".").split(".")[-2].split()[0].lower()]
    y = loadmat(GT_path)[GT_path.replace("/", ".").split(".")[-2].split()[0].lower()]
    print(f"\nX shape: {X.shape}\ny shape: {y.shape}\n")
    return X, y


def extract_pixels_one_vs_all_classes(X, y, class_number):
    q = X.reshape(-1, X.shape[2])
    df = pd.DataFrame(data=q)
    temp = y.ravel()
    for i in range(len(temp)):
        if temp[i] != class_number:
            temp[i] = class_number + 10
    df = pd.concat([df, pd.DataFrame(data=temp)], axis=1)
    df.columns = [f"band{i}" for i in range(1, 1 + X.shape[2])] + ["class"]
    df.to_csv("Dataset.csv")
    return df, np.reshape(temp, (145, 145))


def normalize_data(df):
    # Remove labels class
    temp = df.loc[:, df.columns != "class"]
    # Apply Z-Score normalisation
    temp = temp.apply(
        lambda column: (column - norm.fit(column)[0]) / norm.fit(column)[1], axis=0
    )
    df_norm = pd.concat([temp, df["class"]], axis=1)
    return df_norm


def split_into_train_test(df, test_percentage):
    x = df[df["class"] != 0]
    X = x.iloc[:, :-1].values
    y = x.loc[:, "class"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_percentage, random_state=11, stratify=y
    )
    return X_train, X_test, y_train, y_test


def plot_image(y, fig_name):
    plt.figure(figsize=(10, 8))
    plt.imshow(y, cmap="nipy_spectral")
    plt.colorbar()
    plt.axis("off")
    plt.savefig(fig_name)
    plt.show()


def get_probabilities(dataframe, model):
    probabilities = []
    for pixel in range(dataframe.shape[0]):
        probabilities.append(
            model.predict_proba(dataframe.iloc[pixel, :-1].values.reshape(1, -1))[0]
        )
    return np.array(probabilities)


def visualise_prediction(dataframe, model):
    l = []
    for pixel in range(dataframe.shape[0]):
        l.append(model.predict(dataframe.iloc[pixel, :-1].values.reshape(1, -1)))
    clmap = np.array(l).reshape(145, 145).astype("float")
    print("\n Prediction : \n")
    plot_image(clmap, "IP_cmap.png")


def main():

    start = time.time()

    X, gt = read_files("./Indian_pines_corrected.mat", "./Indian_pines_gt.mat")

    # One-vs-All classification
    df, ground_truth = extract_pixels_one_vs_all_classes(X, gt, 11)

    # Z-Score normalisation
    df = normalize_data(df)

    X_train, X_test, y_train, y_test = split_into_train_test(df, 0.75)

    ##### Comment one of the two different SVM implementations ###########################

    # ##### SVM with GridSearchCV ########################################################

    #     param_grid = {'C': [0.1, 10, 100],
    #                   'kernel': ['rbf', 'poly', 'sigmoid'],
    #                   'probability' : [True]
    #              }
    #     svm = GridSearchCV(SVC(), param_grid, refit = True, verbose = 3)
    #     svm.fit(X_train, y_train)

    #     print(svm.best_params_)
    #     print(svm.best_estimator_)

    #     grid_predictions = svm.predict(X_test)
    #     print(classification_report(y_test, grid_predictions))

    # ####################################################################################

    ##### Basic SVM ######################################################################

    svm = SVC(C=100, cache_size=1024, kernel="poly", probability=True)
    svm.fit(X_train, y_train)

    ######################################################################################

    ##### Prediction and visualization ###################################################

    # Class probability for each pixel
    probabilities = get_probabilities(df, svm)
    ret = np.savetxt("probabilities.txt", probabilities, delimiter=",")

    print(probabilities[0:3])

    print("\n Ground Truth : \n")
    plot_image(ground_truth, "IP_GT.png")
    visualise_prediction(df, svm)

    ######################################################################################

    end = time.time()
    print("The elapsed wall-clock time for the svm is: {}s".format(end - start))

    return 0


if __name__ == "__main__":
    sys.exit(main())
