from vg_data_types import *

from google.cloud import storage
import io
import json
import gcsfs
import pandas as pd
import sys

#clobber other gloabls
PROJ = 'golden-sandbox-261322'
BUCKET = 'vg_for_ai'
FOLD = 'vg-analysis-data/'

fs = gcsfs.GCSFileSystem(project='golden-sandbox-261322')
with fs.open('vg_for_ai/GCP_IMG_DATA.json', 'r', encoding='utf-8') as f:
        FIN_IMGS = dict(json.load(f))

fs = gcsfs.GCSFileSystem(project='golden-sandbox-261322')
with fs.open('vg_for_ai/GCP_TXT_DATA.json', 'r', encoding='utf-8') as f:
        FIN_TXTS = dict(json.load(f))

#get files out of buckets (names specifically)
def list_blobs_with_prefix(bucket_name, fold, prefix, delimiter=None):
        storage_client = storage.Client()
        blobs = storage_client.list_blobs(bucket_name, prefix=fold+prefix,
                                                                          delimiter=delimiter)
        pull_name = lambda x: x.name
        return list(map(pull_name, list(blobs)))
imgs = list_blobs_with_prefix(BUCKET, FOLD, 'img', 'imgs/')
txts = list_blobs_with_prefix(BUCKET, '', 'txt', 'txts/')

img_file_name_only = lambda x: x[26:-4]
txt_file_name_only = lambda x: x[9:-5]
img_to_loc = dict(zip(map(img_file_name_only, imgs), imgs))
txt_to_loc = dict(zip(map(txt_file_name_only, txts), txts))

prev_len_imgs = len(img_to_loc)
prev_len_txts = len(txt_to_loc)

img_to_loc = {k : img_to_loc[k] for k in set(img_to_loc) - set(FIN_IMGS.keys())}
txt_to_loc = {k : txt_to_loc[k] for k in set(txt_to_loc) - set(FIN_TXTS.keys())}

if len(img_to_loc) < prev_len_imgs and len(txt_to_loc) < prev_len_txts:
        print(prev_len_imgs, len(img_to_loc))
        print(prev_len_txts, len(txt_to_loc))
else:
        print('No loading prior games')
        sys.exit()

ALL_IMG_DATA = FIN_IMGS
bckp_img = []
d = 0
for nm, loc in img_to_loc.items():
        t = game_img(nm)
        t.load(loc)
        t.set_api_vars()
        props = t.gcp_api_properties()
        labs = t.gcp_api_labels()
        ALL_IMG_DATA[nm] = {'properties':props, 'labels':labs}
        bckp_img.append((nm, props, labs))
        d += 1
        if d % 100 ==0:
                print(d, " games processed so far")
                fs = gcsfs.GCSFileSystem(project='golden-sandbox-261322')
                with fs.open('vg_for_ai/GCP_IMG_DATA.json', 'w', encoding='utf-8') as f:
                        json.dump(ALL_IMG_DATA, f)

fs = gcsfs.GCSFileSystem(project='golden-sandbox-261322')
with fs.open('vg_for_ai/GCP_IMG_DATA.json', 'w', encoding='utf-8') as f:
        json.dump(ALL_IMG_DATA, f)

ALL_TXT_DATA = FIN_TXTS
bckp_txt = []
d = 0
for nm, loc in txt_to_loc.items():
        t = game_txt(nm)
        t.load(loc)
        t.set_api_vars()
        sent = t.gcp_api_sentiment()
        ent = t.gcp_api_entities()
        ALL_TXT_DATA[nm] = {'sentiment':sent, 'entities':ent}
        bckp_txt.append((nm, sent, ent))
        d += 1
        if d % 100 ==0:
                print(d, " games processed so far")
                fs = gcsfs.GCSFileSystem(project='golden-sandbox-261322')
                with fs.open('vg_for_ai/GCP_TXT_DATA.json', 'w', encoding='utf-8') as f:
                        json.dump(ALL_TXT_DATA, f)

fs = gcsfs.GCSFileSystem(project='golden-sandbox-261322')
with fs.open('vg_for_ai/GCP_TXT_DATA.json', 'w', encoding='utf-8') as f:
        json.dump(ALL_TXT_DATA, f)