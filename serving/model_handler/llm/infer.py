# -*- coding: utf-8 -*-
# @Time:  19:26
# @Author: tk
# @File：infer
import json
import os
import torch
from torch.nn import functional as F
from deep_training.trainer.pl.modelweighter import default_peft_weight_preprocess
from deep_training.data_helper import ModelArguments, DataHelper
from transformers import HfArgumentParser
from aigc_zoo.model_zoo.llm.llm_model import MyTransformer,PetlArguments,PetlModel,AutoConfig
from aigc_zoo.generator_utils.generator_llm import Generate
from serving.model_handler.base import EngineAPI_Base, CompletionResult, flat_input, LoraModelState, load_lora_config, \
    GenerateProcess, WorkMode
from serving.prompt import get_chat_openbuddy,get_chat_tiger,get_chat_default


class NN_DataHelper(DataHelper):pass



class EngineAPI(EngineAPI_Base):
    def _load_model(self,device_id=None):
        parser = HfArgumentParser((ModelArguments,))
        (model_args,) = parser.parse_dict(self.model_config_dict["model_config"], allow_extra_keys=True)

        dataHelper = NN_DataHelper(model_args)
        tokenizer, config, _, _ = dataHelper.load_tokenizer_and_config()
        if config.pad_token_id is None or config.pad_token_id >= config.vocab_size:
            config.pad_token_id = tokenizer.eos_token_id

        pl_model = MyTransformer(config=config, model_args=model_args, torch_dtype=config.torch_dtype, )
        model = pl_model.get_llm_model()
        model.eval().half()

        if self.work_mode != WorkMode.ACCELERATE:
            if device_id is None:
                model.cuda()
            else:
                model.cuda(device_id)
        self.gen_core = Generate(model, tokenizer)
        return model, config, tokenizer

    def _load_model_lora(self, device_id=None):
        parser = HfArgumentParser((ModelArguments,))
        (model_args,) = parser.parse_dict(self.model_config_dict["model_config"], allow_extra_keys=True)

        dataHelper = NN_DataHelper(model_args)
        tokenizer, config, _, _ = dataHelper.load_tokenizer_and_config()
        if config.pad_token_id is None or config.pad_token_id >= config.vocab_size:
            config.pad_token_id = tokenizer.eos_token_id

        ckpt_dir = list(self.lora_conf.values())[0]
        if os.path.exists(os.path.join(ckpt_dir, 'config.json')):
            config = AutoConfig.from_pretrained(ckpt_dir)
        config.initializer_weight = False
        lora_args,ls_peft = load_lora_config(ckpt_dir)

        assert lora_args.inference_mode == True

        new_num_tokens = config.vocab_size
        if config.task_specific_params is not None and config.task_specific_params.get('vocab_size', None) is not None:
            config.vocab_size = config.task_specific_params['vocab_size']

        pl_model = MyTransformer(config=config, model_args=model_args,
                                 lora_args=lora_args,
                                 torch_dtype=torch.float16, new_num_tokens=new_num_tokens,
                                 
                                 # # device_map="auto",
                                 # device_map = {"":0} # 第一块卡
                                 )


        for adapter_name, ckpt_dir in self.lora_conf.items():
            lora_args,ls_peft = load_lora_config(ckpt_dir)
            pl_model.load_sft_weight(ckpt_dir, adapter_name=adapter_name,
                                     lora_config=lora_args,
                                     map_preprocess=default_peft_weight_preprocess if ls_peft else None)
        self.lora_model = pl_model.backbone
        if len(self.lora_conf) == 1:
            if self.auto_merge_lora_single:
                self.lora_state = LoraModelState.MERGE_AND_LOCKED
                self.lora_model.merge_and_unload()
                self.lora_model.eval()
                model = self.lora_model
                if hasattr(model,'quantize') and self.auto_quantize:
                    model.half().quantize(4)
                else:
                    model.half()
            else:
                self.lora_model = self.lora_model.half().eval()
        else:
            self.lora_model = self.lora_model.half().eval()

        if self.work_mode != WorkMode.ACCELERATE:
            if device_id is None:
                self.lora_model.cuda()
            else:
                self.lora_model.cuda(device_id)
        self.gen_core = Generate(self.lora_model, tokenizer)
        return self.lora_model, config, tokenizer

    def chat_stream(self, query, history=None, **kwargs):
        args_process = GenerateProcess(self.tokenizer, self.config,is_stream=True)
        args_process.preprocess(kwargs)
        prompt = get_chat_default(self.tokenizer, query, history)
        default_kwargs = dict(
            eos_token_id=self.config.eos_token_id,
            pad_token_id=self.config.eos_token_id,
            do_sample=True, top_p=0.7, temperature=0.95,
        )
        default_kwargs.update(kwargs)
        args_process.postprocess(default_kwargs)
        skip_word_list = default_kwargs.get('eos_token_id', None) or [self.tokenizer.eos_token_id]
        streamer = args_process.get_streamer(self, skip_word_list)
        self.gen_core.model.generate(**self.gen_core.build_tokens(prompt),streamer=streamer,  **default_kwargs)
        ret = CompletionResult(result={
            "response": "",
            #"history": history,
            "num_token": args_process.get_num_tokens()
        }, complete=True)
        self.push_response(ret)
        return None


    def chat(self, query, history=None, **kwargs):
        args_process = GenerateProcess(self.tokenizer, self.config)
        args_process.preprocess(kwargs)
        prompt = get_chat_default(self.tokenizer, query, history)
        default_kwargs = dict(
            eos_token_id=self.config.eos_token_id,
            pad_token_id=self.config.eos_token_id,
            do_sample=True, top_p=0.7, temperature=0.95,
        )
        default_kwargs.update(kwargs)
        args_process.postprocess(default_kwargs)
        response =  self.gen_core.generate(query=prompt, **default_kwargs)
        response = args_process.postprocess_response(response, **kwargs)
        # history = history + [(query, response)]
        return CompletionResult(result={
            "response": response,
            #"history": history
        })



    def embedding(self, query, **kwargs):
        model = self.get_model()
        inputs = self.tokenizer(query, return_tensors="pt")
        inputs = inputs.to(model.device)
        model_output = model.forward(**inputs,return_dict=True, output_hidden_states=True, **kwargs)
        data = model_output.hidden_states[-1]
        data = F.normalize(torch.mean(data, dim=1), p=2, dim=1)
        embedding = data.detach().tolist()
        return CompletionResult(result={
            "response": embedding,
        })
