import argparse
import json
import torch
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
from tqdm import tqdm
from pathlib import Path
import os
from llama import ModelArgs, Tokenizer, Transformer, LLaMA

class LLaMAInference:
    def __init__(self, llama_path, model, device_map="auto"):

        state_dict = os.path.join(llama_path, model, "state_dict.pth")
        params_file = os.path.join(llama_path, model, "params.json")
        tokenizer_path = os.path.join(llama_path, "tokenizer.model")

        assert os.path.exists(os.path.join(llama_path, model)), f"Model {model} does not exist"
        assert os.path.exists(state_dict), f"Model {model} does not exist"
        assert os.path.exists(params_file), f"Model {model} does not exist"
        assert os.path.exists(tokenizer_path), f"Missing tokenizer in {llama_path}"

        with open(params_file, "r") as f:
            params = json.load(f)

        model_args = ModelArgs(
            max_seq_len=2048,
            max_batch_size=1,
            **params
        )

        self.tokenizer = Tokenizer(model_path=tokenizer_path)
        model_args.vocab_size = self.tokenizer.n_words

        with init_empty_weights():
            torch.set_default_tensor_type(torch.HalfTensor)
            model = Transformer(model_args)
        torch.set_default_tensor_type(torch.FloatTensor)

        self.model = load_checkpoint_and_dispatch(
            model,
            state_dict,
            device_map=device_map,
            no_split_module_classes=["TransformerBlock"]
        )
        
        self.generator = LLaMA(self.model, self.tokenizer)

    def generate(self, texts, temperature=0.8, top_p=0.95, max_length=256):
        results = self.generator.generate(
            texts,
            max_gen_len=max_length,
            temperature=temperature,
            top_p=top_p
        )
        return results

if __name__ == "__main__":
    models = ["7B", "13B", "30B", "65B"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--llama-path", type=str, required=True)
    parser.add_argument("--model", type=str, required=True, choices=models)
    args = parser.parse_args()

    llama = LLaMAInference(args.llama_path, args.model)
    llama.generate(["My name is Kyle"])
    