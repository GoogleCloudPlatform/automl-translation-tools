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

This tool validates whether the tsv/tmx file is valid or not.

#### Valid tsv file
We will split each line of tsv using `\t`. And a valid tsv line will contains
exact 2 sentence pairs.

#### Valid tmx file
  Currently, parser can parse the subset of tmx spec.
  1. &lt;tmx> element is required and should wrap all the content.
  2. &lt;header> is required. It should be the first element inside tmx element.
      But parser will not return any error when there is nothing in tmx.
      (eg, &lt;tmx>&lt;/tmx>). Attribute 'srclang' is required, but all other
      attributes is optional for now.
  3. &lt;body> is required. It should be right after header element. But parser
      will not return any error when there is no body element.
  4. &lt;tu> is element inside &lt;body>. Each &lt;tu> contains a (src_lang, dst_lang) pair,
      it is expected to have 2 &lt;tuv> elements.
  5. &lt;tuv> is element inside &lt;tu>. Attribute 'xml:lang' is required. Each &lt;tuv> is
      expected to have 1 &lt;seg> containing the phrase.
  6. &lt;seg> contains the parallel phrase in either source or target language.
  7. Other unsupported tags(e.g. &lt;entry_metadata>) are skipped.
  8. For each &lt;tu>, if we can not parse a (src_lang, dst_lang) pair from it, we
     skip this &lt;tu> and append the info into _skipped_phrases list.

  Example TMX structure:
  ```xml
  <tmx>
  <header srclang="en" />
    <body>
      <tu>
        <tuv xml:lang="en">
          <seg>XXX</seg>
        </tuv>
        <tuv xml:lang="zh">
          <seg>???</seg>
        </tuv>
      </tu>
    </body>
  </tmx>
  ```

```shell
# You can specify multiple input files.
python parser.py              \
    --cmd=validate            \
    --input_files=$INPUT_FILE \ 
    --src_lang_code=en        \
    --dst_lang_code=zh
```

### Randomly autosplit dataset
If number of sentence pairs smaller than 100k. We will randomly autosplit
dataset with split ratio: 8:1:1. Otherwise, we will split the dataset into
- Training: total_number - 20k
- Validation: 10k
- Test: 10k

```shell
python parser.py                                     \
    --cmd=autosplit                                  \
    --input_files=$INPUT_FILE                        \ 
    --train_dataset=$TRAINING_DATASET_OUTPUT         \
    --validation_dataset=$VALIDATION_DATASET_OUTPUT  \
    --test_dataset=$TEST_DATASET_OUTPUT
```

### Convert file format
This tool can convert file formats between tsv/tmx.

```shell
python parser.py              \
    --cmd=convert             \
    --input_files=$INPUT_FILE \
    --src_lang_code=en        \
    --dst_lang_code=zh        \
    --output_file=$OUTPUT_FILE
```

### Count the total number of sentence pairs
This tool will calculate the number of sentence pairs in input files.
```shell
python parser.py              \
    --cmd=count               \
    --input_files=$INPUT_FILE \ 
    --src_lang_code=en        \
    --dst_lang_code=zh
```