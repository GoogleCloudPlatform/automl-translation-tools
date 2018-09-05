# Cloud AutoML Translation Tools

This repository contains the util tools for Cloud AutoML Translation.
With this tool, you can validate, convert, count or randomly
autosplit dataset before uploading to AutoML.

## How to use this tool.

1. Check it out.
2. Optional: create and activate a new virtual env.
3. Install libraries.

```shell
git clone https://github.com/GoogleCloudPlatform/automl-translation-tools.git
cd automl-translation-tools
virtualenv env
. env/bin/activate
pip install -r requirements.txt
```

### Validate input file
```shell
# You can specify multiple input files.
python parser.py              \
    --cmd=validate            \
    --input_files=$INPUT_FILE \ 
    --src_lang_code=en        \
    --dst_lang_code=zh
```

### Convert file format
```shell
python parser.py              \
    --cmd=convert             \
    --input_files=$INPUT_FILE \
    --src_lang_code=en        \
    --dst_lang_code=zh        \
    --output_file=$OUTPUT_FILE
```

### Count the total number of sentence pairs
```shell
python parser.py              \
    --cmd=count               \
    --input_files=$INPUT_FILE \ 
    --src_lang_code=en        \
    --dst_lang_code=zh
```

### Randomly autosplit dataset
```shell
python parser.py                                     \
    --cmd=autosplit                                  \
    --input_files=$INPUT_FILE                        \ 
    --train_dataset=$TRAINING_DATASET_OUTPUT         \
    --validation_dataset=$VALIDATION_DATASET_OUTPUT  \
    --test_dataset=$TEST_DATASET_OUTPUT
```
