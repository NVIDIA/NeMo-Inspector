# NeMo Inspector

NeMo Inspector is a tool designed to help you analyze Large Language Model (LLM) generations. It provides two main pages:

- **Inference Page:** Interactively generate and analyze model responses.
- **Analyze Page:** Explore and manipulate existing generations, apply filters, sorting criteria, and compute statistics.

## About the NeMo Inspector

The Inference page allows you to experiment with model prompts and responses in real-time, adjusting various parameters. The Analyze page lets you load previously generated outputs and apply filtering, sorting, labeling, and statistic calculations for in-depth exploration.

## Prerequisites

1. **Clone and Install the Tool:**
   ```shell
   git clone git@github.com:NVIDIA/NeMo-Inspector.git
   cd nemo-inspector
   pip install .
   ```

2. **Launch the Tool:**
   ```shell
   nemo_inspector
   ```

This will start a local server that you can access through your browser.

## Inference Page

The Inference page allows you to generate responses using an LLM and analyze them immediately. It supports two generation modes:

- **Prompt-based Mode:** You write the entire prompt that will be sent to the model.
- **Template-based Mode:** You select from predefined templates, fill in placeholders, and let the tool automatically construct the final prompt.

The Inference page utilizes [NeMo-Skills](https://github.com/NVIDIA/NeMo-Skills) pipelines for inference.

## Analyze Page

The Analyze page helps you work with pre-generated outputs. To use it, provide paths to the generation files using command-line arguments. For example:

```shell
nemo_inspector --inspector_params.model_prediction \
  generation1='/path/to/generation1/output-greedy.jsonl' \
  generation2='/path/to/generation2/output-rs*.jsonl'
```
Once loaded, the Analyze page lets you:

- **Sort and Filter Results:** Apply custom filtering and sorting functions to refine the displayed data.
- **Compare Generations:** View outputs from multiple generation runs side-by-side.
- **Modify and Label Data:** Update or annotate samples and save the changes for future reference.
- **Compute Statistics:** Generate both custom and general statistics to summarize your data.

### Filtering

The tool supports two filtering modes: **Filter Files** mode and **Filter Questions** mode. You can define custom filtering functions in Python and run them directly in the UI.

#### Filter Files Mode

- In this mode, the filtering function will be run on each sample across different files simultaneously.
- The input to the filtering function is a dictionary where keys represent generation names and values are JSON objects for that sample.
- The custom function should return a Boolean value (`True` to keep the sample, `False` to filter it out).

Example of a custom filtering function:

```python
def custom_filtering_function(error_message: str) -> bool:
    # Implement your logic here
    return 'timeout' not in error_message

# This line will be used for the filtering:
custom_filtering_function(data['generation1']['error_message'])
```

**Note:** The last line of the custom filtering function is used for filtering. All preceding lines are just for computation.

To apply multiple conditions to multiple generations, use the `&&` separator. For instance:

```python
data['generation1']['is_correct'] && not data['generation2']['is_correct']
```

**Important:** In Filter Files mode, do not write multi-generation conditions without using `&&`. Each condition should be separated by `&&`.

#### Filter Questions Mode

- In this mode, the function filters each question across multiple files without filtering out entire files.
- The input is a dictionary of generation names mapping to **lists** of JSON data for that question.

In this mode, you write conditions without the `&&` operator. For example:

```python
data['generation1'][0]['is_correct'] and not data['generation2'][0]['is_correct']
```

This example filters out questions where the first generation is correct and the second generation is incorrect. It can also compare fields directly:

```python
data['generation1'][0]['is_correct'] != data['generation2'][0]['is_correct']
```

**Note:** These examples cannot be used in Filter Files mode.

### Sorting

Sorting functions are similar to filtering functions, but there are key differences:

1. **Scope:** Sorting functions operate on individual data entries (not dictionaries with multiple generations).
2. **Cross-Generations:** Sorting cannot be applied across multiple generations at once. You must sort one generation at a time.

A correct sorting function might look like this:

```python
def custom_sorting_function(generation: str):
    # Sort by the length of the generation text
    return len(generation)

# This line will be used for the sorting:
custom_sorting_function(data['generation'])
```

### Statistics

NeMo Inspector supports two types of statistics:

1. **Custom Statistics:** Applied to the samples of a single question (for each generation).
   
   Default custom statistics include:
   - `correct_responses`
   - `wrong_responses`
   - `no_responses`

2. **General Custom Statistics:** Applied across all questions and all generations.  
   
   Default general custom statistics include:
   - `dataset size`
   - `overall number of samples`
   - `generations per sample`

You can change the existing or define your own Custom and General Custom Statistics functions.

**Custom Statistics Example:**

```python
def unique_error_counter(datas):
    # `datas` is a list of JSONs (one per file) for a single question
    unique_errors = set()
    for data in datas:
        unique_errors.add(data.get('error_message'))
    return len(unique_errors)

def number_of_runs(datas):
    return len(datas)

# Map function names to functions
{'unique_errors': unique_error_counter, 'number_of_runs': number_of_runs}
```

**General Custom Statistics Example:**

```python
def overall_unique_error_counter(datas):
    # `datas` is a list of lists of dictionaries, 
    # where datas[question_index][file_index] is a JSON record
    unique_errors = set()
    for question_data in datas:
        for file_data in question_data:
            unique_errors.add(file_data.get('error_message'))
    return len(unique_errors)

# Map function names to functions
{'unique_errors': overall_unique_error_counter}
```

**Note:** The final line in both the Custom and General Custom Statistics code blocks should be a dictionary mapping function names to their corresponding functions.

### Modifications

You can update each sample in the dataset programmatically. At the end of the code block, return the updated sample dictionary:

```python
# For example, strip leading and trailing whitespace from the "generation" field
{**data, 'generation': data['generation'].strip()}
```
