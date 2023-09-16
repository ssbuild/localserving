# -*- coding: utf-8 -*-
# @Author  : ssbuild
# @Time    : 2023/8/21 9:34
from template.baichuan_conf import baichuan_config
from template.baichuan2_conf import baichuan2_config
from template.bloom_conf import bloom_conf
from template.chatglm_conf import chatglm_conf
from template.chatglm2_conf import chatglm2_conf
from template.internlm_conf import internlm_conf
from template.llama_conf import llama_conf
from template.moss_conf import moss_conf
from template.opt_conf import opt_conf
from template.rwkv_conf import rwkv_conf
from template.qwen_conf import qwen_conf
from template.tiger_conf import tiger_conf
from template.xverse_conf import xverse_conf

import yaml

with open("../yamlconfig/baichuan.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(baichuan_config,f)

with open("../yamlconfig/baichuan2.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(baichuan2_config,f)


with open("../yamlconfig/bloom.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(bloom_conf,f)

with open("../yamlconfig/chatglm.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(chatglm_conf,f)

with open("../yamlconfig/chatglm2.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(chatglm2_conf,f)

with open("../yamlconfig/internlm.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(internlm_conf,f)


with open("../yamlconfig/llama.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(llama_conf,f)

with open("../yamlconfig/moss.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(moss_conf,f)


with open("../yamlconfig/opt.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(opt_conf,f)


with open("../yamlconfig/rwkvf.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(rwkv_conf,f)


with open("../yamlconfig/qwen.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(qwen_conf,f)


with open("../yamlconfig/tiger.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(tiger_conf,f)
    
with open("../yamlconfig/xverse.yaml", mode='w',encoding='utf-8',newline='\n') as f:
    yaml.dump(xverse_conf,f)