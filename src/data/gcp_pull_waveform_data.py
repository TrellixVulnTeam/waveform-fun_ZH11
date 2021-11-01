import os
import pandas as pd
import numpy as np
import wfdb
import datetime



def fetch_settings():
    return {
        'fetch_clinical_data': False,
        'verbose': True,
        'google_cloud': {
            'project': os.environ['PROJECT_ID']
        }
    }

def generate_record_map(bucket, fs, training_set):
    settings = fetch_settings()
    df = pd.read_csv(
        fs.open(f'{bucket}/mimic2cdb/MAP', 'rb'),
        sep="\t", 
        names = ['Clinical', 'Wave', 'Sex', 'Age', 'Birthdate', 'Waveform'],
        index_col = False, 
        skiprows = [0,1])
    df = df[df['Clinical'].isin(training_set)]
    if settings['verbose']:
        print(f"Dimensions of data set: {df.shape}")
        print(f"Data set reflects data for {len(df['Clinical'].unique().tolist())} clinical IDs")
        print(f"Data set reflects data for {len(df['Wave'].unique().tolist())} waveform IDs")
    return({'data':df, 
            'clinical_entities': df['Clinical'].unique().tolist(),
            'waveform_entities': df['Wave'].unique().tolist()
           })


def filter_data_to_entity(df, entity_colname, entity):
    return df[df[entity_colname] == entity]


def format_df(df, record):
    """ Format df
    """
    df["time"] = df.index * 0.008 # from 8 ms to 1 s
    df["ts"] = df["time"].apply(lambda x: record["waveform_record"]["base_datetime"] \
                                + datetime.timedelta(seconds=x))

    df["age"] = record["raw_data"]["Age"]
    df["sex"] = record["raw_data"]["Sex"]
    df["clinical"] = record["raw_data"]["Clinical"]

    #surrogate = t0[record["raw_data"]["Wave"]]
    #df["before_t0"] = df["ts"].apply(lambda x: x < surrogate)

    #name = df["clinical"]
    #if not os.path.isdir("data/mimic2db"):
    #    os.mkdir("data/mimic2db")
    #fs.get(f'{bucket_name}/mimic2cdb/{name}/{name}.txt', f'data/mimic2db/{name}/{name}.txt')

    #clinical = parse_txt(f"data/mimic2db/{name}/{name}.txt")

    return df



def generate_waveform_dataset(e, record_map):
    settings = fetch_settings()
    df = record_map['data']
    data = filter_data_to_entity(df, 'Wave', e)
    data = data.squeeze().to_dict()
    result = {'raw_data': data}
    
    if settings['verbose']: print(data)
    record = wfdb.rdrecord(f"data/train_wave/{data['Wave']}")
    record_dict = {
        'raw_data': data,
        'waveform_record': record.__dict__
    }
    df_indiv = pd.DataFrame(record_dict['waveform_record']['p_signal'], columns = record_dict['waveform_record']['sig_name'])
    #if settings['verbose']: print(record_dict)
    #print(record_dict)
    #if settings['verbose']: print(df_indiv)
    
    df2 = format_df(df_indiv,record_dict)
    #return {
    #    'raw_data': data,
    #    'waveform_record': record.__dict__
    #}
    return df2
    