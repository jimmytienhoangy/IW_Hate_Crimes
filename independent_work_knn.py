# -*- coding: utf-8 -*-
"""Independent Work KNN

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17QDmlkhzeXRtmK5VQvgUwF5DtNkt8u9j

# **Predicting Hate Crime Biases Using Multiclass Classification Machine Learning Models**

**Setup**

Import the necessary libraries.
"""

## for data manipulation
import pandas as pd
import numpy as np

## for plotting
import matplotlib.pyplot as plt

## for grouping sparse values
from statistics import median

## to normalize numerical features
from sklearn.preprocessing import MinMaxScaler

## for splitting the data
from sklearn.model_selection import train_test_split

## for knn training
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, ConfusionMatrixDisplay, balanced_accuracy_score

"""# **Data Collection, Analysis, and Preparation**

Read the hate crime data into a pandas dataframe.
"""

dtf = pd.read_csv('hate_crime.csv')
dtf = dtf.sort_values(by=['incident_id'])

"""Remove preliminary features and data points that will not be needed."""

# remove duplicate rows
dtf.drop_duplicates(inplace = True)

# remove columns that are duplicates or unnecessary
dtf = dtf.drop(columns=['incident_id', 'ori', 'pug_agency_name',
                        'pub_agency_unit', 'agency_type_name',
                        'state_abbr', 'population_group_code',
                        'incident_date', 'adult_victim_count',
                        'juvenile_victim_count', 'adult_offender_count',
                        'juvenile_offender_count'])

"""Categorical Variable to Dataframe Function"""

# returns a dataframe of one hot vectors for all categories of a variable
def cat_to_dat(dtf, col, years, year_sensitive):
  # one hot vectors over years in years
 if year_sensitive:
   return (dtf[dtf.data_year.isin(years)])[col].astype(str).str.get_dummies(sep = ";")
  # one hot vectors over all years available
 else:
   return dtf[col].astype(str).str.get_dummies(sep = ";")

"""**Cleaning**"""

# just take the first value if a row has multiple values for a single column
dtf['offense_name'] = dtf['offense_name'].str.split(';').str[0]
dtf['location_name'] = dtf['location_name'].str.split(';').str[0]
dtf['victim_types'] = dtf['victim_types'].str.split(';').str[0]

# only keep the 50 states plus D.C. plus federal
remove_states = ['Guam']
dtf = dtf[~dtf.state_name.isin(remove_states)]

dtf['state_name'] = dtf['state_name'].replace('Federal', 'Federal (State)')

# only keep the 9 U.S. divisions
# remove_divisions = ['Other', 'U.S. Territories']
# dtf = dtf[~dtf.division_name.isin(remove_divisions)]

dtf['division_name'] = dtf['division_name'].replace('Other', 'Federal (Division)')
dtf['division_name'] = dtf['division_name'].replace('U.S. Territories', 'U.S. Territories (Division)')

# only keep the 4 U.S. regions
# remove_regions = ['Other', 'U.S. Territories']
# dtf = dtf[~dtf.region_name.isin(remove_regions)]

dtf['region_name'] = dtf['region_name'].replace('Other', 'Federal (Region)')
dtf['region_name'] = dtf['region_name'].replace('U.S. Territories', 'U.S. Territories (Region)')

# remove State Police densities
# remove_densities = ['MSA State Police', 'Non-MSA State Police']
# dtf = dtf[~dtf.population_group_description.isin(remove_densities)]

# remove rows that have a null value for population densities
dtf = dtf[dtf.population_group_description.notnull()]

# keep relevant offenses
# keep_offenses = ['Aggravated Assault', 'Arson', 'Burglary/Breaking & Entering',
#                 'Destruction/Damage/Vandalism of Property', 'Intimidation',
#                 'Kidnapping/Abduction', 'Murder and Nonnegligent Manslaughter',
#                 'Rape', 'Robbery', 'Simple Assault', 'All Other Larceny',
#                 'Stolen Property Offenses', 'Theft From Building',
#                 'Theft From Motor Vehicle',
#                 'Theft of Motor Vehicle Parts or Accessories',
#                 'Motor Vehicle Theft']
# dtf = dtf[dtf.offense_name.isin(keep_offenses)]

# group larceny and theft offenses
# larceny_theft = ['All Other Larceny', 'Stolen Property Offenses',
#                 'Theft From Building', 'Theft From Motor Vehicle',
#                 'Theft of Motor Vehicle Parts or Accessories',
#                'Motor Vehicle Theft']
# for offense in larceny_theft:
#  dtf['offense_name'] = dtf['offense_name'].replace(offense, 'Larceny/Theft')

# remove sparse offenses
threshold = 0.0001 * dtf.shape[0]

offense_dtf = cat_to_dat(dtf, 'offense_name', years = [], year_sensitive = False)
offenses_to_remove = []

for col in offense_dtf.columns:
  if offense_dtf[col].sum() < threshold:
    offenses_to_remove.append(str(col))

dtf = dtf[~dtf.offense_name.isin(offenses_to_remove)]

# remove null total individual victim counts
dtf = dtf[dtf.total_individual_victims.notnull()]

# remove sparse locations
threshold = 0.0001 * dtf.shape[0]

location_dtf = cat_to_dat(dtf, 'location_name', years = [], year_sensitive = False)
locations_to_remove = []

for col in location_dtf.columns:
    if location_dtf[col].sum() < threshold:
      locations_to_remove.append(str(col))

dtf = dtf[~dtf.location_name.isin(locations_to_remove)]

dtf['offender_race'] = dtf['offender_race'].replace("Other/Unknown", 'Other/Unknown Location Type')

# remove unknown offender race
# remove_races = ['Unknown', 'Not Specified']
# dtf = dtf[~dtf.offender_race.isin(remove_races)]

dtf['offender_race'] = dtf['offender_race'].replace("Unknown", 'Unknown Race')
dtf['offender_race'] = dtf['offender_race'].replace("Not Specified", 'Unknown Race')
dtf['offender_race'] = dtf['offender_race'].replace("Multiple", 'Mixed Race')

# remove rows with unknown biases
dtf = dtf[dtf.bias_desc != "Unknown (offender's motivation not known)"]

# remove unknown victim types
#remove_victim_types = ['Unknown', 'Other']
# dtf = dtf[~dtf.victim_types.isin(remove_victim_types)]

dtf['victim_types'] = dtf['victim_types'].replace("Unknown", 'Unknown Victim Type')
dtf['victim_types'] = dtf['victim_types'].replace("Other", 'Other Victim Type')

# remove rows with multiple biases
dtf = dtf[dtf.multiple_bias != "M"]

# remove columns that are too empty or unnecessary
dtf = dtf.drop(columns=['offender_ethnicity', 'multiple_offense', 'multiple_bias'])

"""Create classification classes."""

# group biases for more general classification
anti_disability = ['Anti-Mental Disability', 'Anti-Physical Disability']

anti_gender = ['Anti-Female', 'Anti-Male']

anti_gender_identity = ['Anti-Gender Non-Conforming', 'Anti-Transgender']

anti_race_ethnicity_ancestry = ['Anti-American Indian or Alaska Native',
                                'Anti-Arab', 'Anti-Asian', 'Anti-Black or African American',
                                'Anti-Native Hawaiian or Other Pacific Islander',
                                'Anti-Hispanic or Latino', 'Anti-Multiple Races, Group',
                                'Anti-Other Race/Ethnicity/Ancestry', 'Anti-White']

anti_religion = ['Anti-Atheism/Agnosticism', 'Anti-Buddhist', 'Anti-Catholic',
                 'Anti-Eastern Orthodox (Russian, Greek, Other)', 'Anti-Hindu',
                 'Anti-Islamic (Muslim)', "Anti-Jehovah's Witness", 'Anti-Jewish',
                 'Anti-Mormon', 'Anti-Multiple Religions, Group', 'Anti-Other Christian',
                 'Anti-Other Religion', 'Anti-Protestant', 'Anti-Sikh', 'Anti-Church of Jesus Christ']

anti_sexual_orientation = ['Anti-Bisexual', 'Anti-Gay (Male)',
                  'Anti-Lesbian, Gay, Bisexual, or Transgender (Mixed Group)',
                  'Anti-Heterosexual', 'Anti-Lesbian (Female)']

bias_groups = [anti_disability, anti_gender, anti_gender_identity,
               anti_race_ethnicity_ancestry, anti_religion, anti_sexual_orientation]

bias_groups_str = ['Anti-Disability', 'Anti-Gender', 'Anti-Gender Identity',
                   'Anti-Race/Ethnicity/Ancestry', 'Anti-Religion',
                   'Anti-Sexual Orientation']

for index, bias_group in enumerate(bias_groups):
  for bias in bias_group:
    if index == 0:
          dtf['bias_desc'] = dtf['bias_desc'].replace(bias,'Anti-Disability')
    elif index == 1:
          dtf['bias_desc'] = dtf['bias_desc'].replace(bias,'Anti-Gender')
    elif index == 2:
          dtf['bias_desc'] = dtf['bias_desc'].replace(bias,'Anti-Gender Identity')
    elif index == 3:
          dtf['bias_desc'] = dtf['bias_desc'].replace(bias,'Anti-Race/Ethnicity/Ancestry')
    elif index == 4:
          dtf['bias_desc'] = dtf['bias_desc'].replace(bias,'Anti-Religion')
    elif index == 5:
          dtf['bias_desc'] = dtf['bias_desc'].replace(bias,'Anti-Sexual Orientation')

"""Missing Value Imputation"""

# always at least 1 offender (impute to mode)
dtf.loc[dtf['total_offender_count'] == 0, 'total_offender_count'] = 1

# re-index the rows
dtf = dtf.reset_index(drop = "True")

"""**Prepare data for training!**

Split the data into training and testing sets.
"""

y = dtf.bias_desc
X = dtf.drop(['bias_desc'], axis = 1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state = 100, stratify = y)

"""Group Sparse Numerical Columns and Normalize Numerical Columns"""

# Training Data

# replace numerical outliers with median
median_tiv_gt_10 = (X_train.loc[X_train['total_individual_victims'] > 10, 'total_individual_victims']).median()
X_train.loc[X_train['total_individual_victims'] > 10, 'total_individual_victims'] = median_tiv_gt_10

median_vc_gt_10 = (X_train.loc[X_train['victim_count'] > 10, 'victim_count']).median()
X_train.loc[X_train['victim_count'] > 10, 'victim_count'] = median_vc_gt_10

median_toc_gt_10 = (X_train.loc[X_train['total_offender_count'] > 10, 'total_offender_count']).median()
X_train.loc[X_train['total_offender_count'] > 10, 'total_offender_count'] = median_toc_gt_10

# normalize
mms1 = MinMaxScaler()
X_train[['total_individual_victims','victim_count', 'total_offender_count']] = mms1.fit_transform(X_train[['total_individual_victims','victim_count', 'total_offender_count']])

#Testing Data

# replace numerical outliers with median
median_tiv_gt_10 = (X_test.loc[X_test['total_individual_victims'] > 10, 'total_individual_victims']).median()
X_test.loc[X_test['total_individual_victims'] > 10, 'total_individual_victims'] = median_tiv_gt_10

median_vc_gt_10 = (X_test.loc[X_test['victim_count'] > 10, 'victim_count']).median()
X_test.loc[X_test['victim_count'] > 10, 'victim_count'] = median_vc_gt_10

median_toc_gt_10 = (X_test.loc[X_test['total_offender_count'] > 10, 'total_offender_count']).median()
X_test.loc[X_test['total_offender_count'] > 10, 'total_offender_count'] = median_toc_gt_10

# normalize
mms2 = MinMaxScaler()
X_test[['total_individual_victims','victim_count', 'total_offender_count']] = mms2.fit_transform(X_test[['total_individual_victims','victim_count', 'total_offender_count']])

"""Create final dataframes for the training and testing sets."""

# create aggregate X dataframe with all categorical variables turned into one hot vectors
numerical_columns = ['total_offender_count', 'victim_count', 'total_individual_victims']

# X_train
new_dtf = pd.DataFrame()
for col in X_train.columns:
  if col not in numerical_columns:
    new_dtf = pd.concat([new_dtf, pd.get_dummies(X_train[col], drop_first = True)], axis = 1)
X_train = pd.concat([X_train[numerical_columns], new_dtf], axis = 1)

# X_test
new_dtf = pd.DataFrame()
for col in X_test.columns:
  if col not in numerical_columns:
    new_dtf = pd.concat([new_dtf, pd.get_dummies(X_test[col], drop_first = True)], axis = 1)
X_test = pd.concat([X_test[numerical_columns], new_dtf], axis = 1)

# make sure year columns are strings
X_train.columns = X_train.columns.astype(str)
X_test.columns = X_test.columns.astype(str)

"""Imbalanced Sampling"""

from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state = 100, sampling_strategy = 'not majority')
X_train, y_train = smote.fit_resample(X_train, y_train)

y_train.value_counts()

"""# **Model Training and Evaluation**

**K-Nearest Neighbors**

KNN Before Tuning
"""

knn = KNeighborsClassifier()

knn.fit(X_train, y_train)

y_pred_knn = knn.predict(X_test)

print(classification_report(y_test, y_pred_knn, digits = 4))
print("Balanced Accuracy Score: ", balanced_accuracy_score(y_test, y_pred_knn))

disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred_knn,
cmap=plt.cm.Blues, normalize = 'true', display_labels=bias_groups_str,
xticks_rotation = 'vertical')

fig = disp.figure_
fig.suptitle('K-Nearest Neighbors Untuned')

"""KNN Tuning (Weighted F1)"""

base_knn = KNeighborsClassifier()

knn_space = {'n_neighbors': [2, 3, 4],
         'weights': ['uniform'],
         'leaf_size': [5, 15, 30],
         'n_jobs': [-1]}

gs_knn = GridSearchCV(base_knn, knn_space, cv = 5, scoring = 'f1_weighted')

gs_knn.fit(X_train, y_train)

print('Best Weighted F1: %.2f' % gs_knn.best_score_)
print('Best Parameters: ', gs_knn.best_params_)

y_pred_knn_cv = gs_knn.predict(X_test)

print(classification_report(y_test, y_pred_knn_cv, digits = 4))

disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred_knn_cv,
cmap=plt.cm.Blues, normalize = 'true', display_labels=bias_groups_str, xticks_rotation = 'vertical')

fig = disp.figure_
fig.suptitle('K-Nearest Neighbors Tuned for Weighted F1')

"""KNN Tuning (Balanced Accuracy)"""

base_knn = KNeighborsClassifier()

knn_space = {'n_neighbors': [2, 3, 4],
         'weights': ['uniform'],
         'leaf_size': [5, 15, 30],
         'n_jobs': [-1]}

gs_knn = GridSearchCV(base_knn, knn_space, cv = 5, scoring = 'balanced_accuracy')

gs_knn.fit(X_train, y_train)

print('Best Balanced Accuracy: %.2f' % gs_knn.best_score_)
print('Best Parameters: ', gs_knn.best_params_)

y_pred_knn_cv = gs_knn.predict(X_test)

print(classification_report(y_test, y_pred_knn_cv, digits = 4))
print("Balanced Accuracy Score: ", balanced_accuracy_score(y_test, y_pred_knn_cv))

disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred_knn_cv,
normalize = 'true', cmap=plt.cm.Blues, display_labels=bias_groups_str,
xticks_rotation = 'vertical')

fig = disp.figure_
fig.suptitle('K-Nearest Neighbors Tuned for Balanced Accuracy')