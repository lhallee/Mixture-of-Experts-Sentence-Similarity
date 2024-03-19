import argparse
import torch

from utils import get_yaml, load_model
from run_model import train_model, evaluate_model
from metrics import compute_metrics_sentence_similarity


def get_args():
    parser = argparse.ArgumentParser(description="MOE settings")
    parser.add_argument('--yaml_path', type=str, )
    parser.add_argument('--eval', action='store_true', help='Run model in evaluation mode.')
    return parser.parse_args()


def main():
    parse = get_args()
    
    yargs = get_yaml(parse.yaml_path)

    args = yargs['general_args']

    print('\n-----Load Model-----\n')
    model, tokenizer = load_model(args)

    model = model.to(torch.bfloat16)

    compute_metrics = compute_metrics_sentence_similarity

    if parse.eval:
        if args['weight_path'] != None:
            weight_path = args['weight_path']
            model.load_state_dict(torch.load(weight_path))
            print(f'Model loaded from {weight_path}')
        evaluate_model(yargs, tokenizer, compute_metrics=compute_metrics, model=model)
    else:
        train_model(yargs, model, tokenizer, compute_metrics=compute_metrics)


if __name__ == '__main__':
    main()