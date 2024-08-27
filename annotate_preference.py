from datasets import load_dataset
import requests
import time
import datasets
import json
import pandas as pd
import random

import os
import re
from copy import deepcopy
from tqdm import tqdm
MAX_API_RETRY=10
from openai import OpenAI
client = OpenAI()
api_key = "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"


def process(responses, aspect):
    responses = responses.split("\n\n")
    #remove responses that doesn't start with # or doesn't contain the word Feedback
    responses = [response for response in responses if response.startswith("#") and "Feedback" in response]
    assert len(responses) == 3, f"Expected 3 responses, got {len(responses)}"
    annotation = []
    try:
        if aspect in ["instruction_following", "honesty", "overall_quality"]:
            pattern = r"Rating: (.+?)\nRationale: (.+)"
            for response in responses:
                matches = re.search(pattern, response, re.DOTALL)
                annotation.append({
                    "Rating": re.findall(r'\b\d+\b', matches.group(1))[0] if matches.group(1) != "N/A" else "N/A",
                    "Rationale": matches.group(2)
                })
        elif aspect in ["truthfulness", "helpfulness"]:
            pattern = r"Type: (.+?)\nRationale: (.+?)\nRating: (.+?)\nRationale: (.+)"
            for response in responses:
                matches = re.search(pattern, response, re.DOTALL)
                annotation.append({
                    "Type": re.findall(r'\b\d+\b', matches.group(1)) if matches.group(1) != "None" else "None",
                    "Rationale": matches.group(2),
                    "Rating": re.findall(r'\b\d+\b', matches.group(3))[0],
                    "Rationale For Rating": matches.group(4)
                })

    except ValueError as e: # TODO: bug process when the response does not follow the format
        print(responses)
        raise ValueError(e)
    except AttributeError as e:
        print(responses)
        raise AttributeError(e)
    return annotation


def get_eval(sys_prompt:str, user_prompt: str, max_tokens: int = 500):
    for _ in range(MAX_API_RETRY):
        try:
            print("before_api_call")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # logprobs= True,
                # top_logprobs =  10
                )
            content = response.choices[0].message.content
        except Exception as e:
            print(e)
            time.sleep(1)
        else:
            break
    # print(content)
    return content


from preference_templates import system_prompt, instruction_following_template, overall_quality_template#, truthfulness_template, honesty_template, harmlessness_template, helpfulness_template

SHUFLLE_NUM = 1
def annotate(example, label_order="CABD", aspects = ["overall_quality"]):
    # print(type(example))
    # aspects = ["instruction_following", "honesty", "truthfulness", "helpfulness"]
    aspects = aspects
    deepcopy_example = deepcopy(example)
    # print(deepcopy_example.keys())
    deepcopy_completions = deepcopy_example["completions"]
    # keep only model and response key value pairs in each completions
    deepcopy_completions = [dict({"model": completion["model"], "response": completion["response"]}) for completion in deepcopy_completions]
    # print(deepcopy_example)
    
    # descending order by score
    descending_response_order_by_score = sorted([0,1,2,3], key=lambda x: example["completions"][x]["fine-grained_score"], reverse=True)
    
    
    label_order = list(label_order)
    label_order = {label_order[i]: i for i in range(len(label_order))}
    response_order_by_label = [descending_response_order_by_score[label_order[char]] for char in ['A', 'B', 'C', 'D']]
    # print(response_order_by_label)
    choice_sets = []
    choice_sets_ABC = [response_order_by_label[1], response_order_by_label[2], response_order_by_label[0]]
    choice_sets_ABD = [response_order_by_label[1], response_order_by_label[2], response_order_by_label[3]]
    choice_sets.append(choice_sets_ABC)
    choice_sets.append(choice_sets_ABD)
    # print(choice_sets)
    
    #remove the completions of deepcopy_example
    del deepcopy_example["completions"]
    del deepcopy_example["correct_answers"]
    del deepcopy_example["incorrect_answers"]
    
    deepcopy_example["choice_set_1"] = {}
    deepcopy_example["choice_set_2"] = {}
    deepcopy_example["correct_answers"] = ["None"]
    deepcopy_example["incorrect_answers"] = ["None"]
    #order the completions of deepcopy_completions based on choice_sets_ABC
    for i, order in enumerate(choice_sets):
        deepcopy_completion_order = [deepcopy(deepcopy_completions[o]) for o in order]
    
        deepcopy_example[f"choice_set_{i+1}"]["completions"] = [dict({"annotations": {aspect: [] for aspect in aspects}}, **completion)
                    for completion in deepcopy_completion_order]

    # make the order of completions
    for aspect in aspects:
        
        world_knowledge = "No additional world knowledge for reference."

        # generate several lists of a random order of 4 completions, no repetition
        count = 0
        # descending order by score
        descending_response_order_by_score = sorted([0,1,2,3], key=lambda x: example["completions"][x]["fine-grained_score"], reverse=True)
        # print(descending_response_order_by_score)
        
        label_order = list(label_order)
        label_order = {label_order[i]: i for i in range(len(label_order))}
        response_order_by_label = [descending_response_order_by_score[label_order[char]] for char in ['A', 'B', 'C', 'D']]

        choice_sets = []
        choice_sets_ABC = [response_order_by_label[1], response_order_by_label[2], response_order_by_label[0]]
        choice_sets_ABD = [response_order_by_label[1], response_order_by_label[2], response_order_by_label[3]]
        choice_sets.append(choice_sets_ABC)
        choice_sets.append(choice_sets_ABD)
        # print(choice_sets)
        for v, order in enumerate(choice_sets):        
            format_input = {"instruction": example["instruction"]}
            format_input.update({f"text_{i+1}": example["completions"][o]["response"] for i, o in enumerate(order)})
            print(format_input.keys())
            if aspect == "truthfulness":
                format_input.update({"world_knowledge": world_knowledge})
            # print('before_eval')
            print(len(format_input))
            responses = get_eval(system_prompt, user_prompt=TEMPLATE[aspect].format(**format_input))
            
            # print('after_eval')
            for i in range(10):
                try:
                    responses = process(responses, aspect) # gpt-4 format error
                    
                except Exception as e:
                    print(f'exception{i}')
                    print(e)
                    if i < 10:
                        responses = get_eval(system_prompt, user_prompt=TEMPLATE[aspect].format(**format_input))
                    else:
                        print(e)
                        break
                else:
                    for j in range(3):
                        print(order)
                        deepcopy_example[f'choice_set_{v+1}']['completions'][j]["annotations"][aspect].append(responses[j])
                    break
            
                    
    # deepcopy_example["completions"] = completions
    return deepcopy_example
    

def incorporate_annotation_to_completions(example):
    pass






if __name__ == "__main__":
    #=================CONFIGURATION=================
    label_order = "CABD"
    dataset_size = 1
    TEMPLATE = {
        "overall_quality": overall_quality_template,   
        # "instruction_following": instruction_following_template,
        # "honesty": honesty_template,
        # "truthfulness": truthfulness_template,
        # "harmlessness": harmlessness_template,
        # "helpfulness": helpfulness_template,
    }
    aspects = ["overall_quality"]
    #==============================================
    dataset = load_dataset("openbmb/UltraFeedback")["train"]
    # get the first 40 instances in dataset
    dataset = dataset[:dataset_size]
    # subsets = ["truthful_qa"]

    # for subset in subsets:
    #     with open(os.path.join("../comparison_data_generation", "completion_data", subset + ".json"), "r") as f:
    #         dataset = json.load(f)
    dataset = pd.DataFrame(dataset)
    dataset_dict = []

    #iterate the dataset using tqdm row by row
    for index, row in tqdm(dataset.iterrows(), total=len(dataset), desc="Annotating"):
        dataset_dict.append(annotate(row, label_order=label_order, aspects=aspects))
    
    os.makedirs("annotation", exist_ok=True)
    result_path = os.path.join("annotation", "_annotated.json")
    with open(result_path, "w") as f:
        json.dump([{k: v for k, v in data.items()} for data in dataset_dict], f, indent=4)
    #
    