# The MIT License (MIT)

# Copyright (c) 2012-2019 CNRS

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# AUTHORS
# Gaofeng Cheng     chenggaofeng@hccl.ioa.ac.cn     (Institute of Acoustics, Chinese Academy of Science)
# Yifan Chen        chenyifan@hccl.ioa.ac.cn        (Institute of Acoustics, Chinese Academy of Science)
# Runyan Yang       yangrunyan@hccl.ioa.ac.cn       (Institute of Acoustics, Chinese Academy of Science)
# Qingxuan Li       liqx20@mails.tsinghua.edu.cn    (Tsinghua University)
#----------------------------------------------------------------------------------------------------------

# 2025 DSdC (Daniel Sáenz de Cosca) Copied from https://github.com/SpeechClub/CDER_Metric/tree/main slightly modified to fit our neccesities
# just get the CDER Metric.
# So credits to AUTHORS above (SpeechClub: Institute of Acoustics, Chinese Academy of Science and Tsinghua University)
from .diarization import CSSDErrorRate
import numpy as np
from .pre_process import rttm_read_cder

def get_cder(ref_path, hyp_path):

    ref_dict = rttm_read_cder(ref_path)
    hyp_dict = rttm_read_cder(hyp_path)
        
    CSSDER = CSSDErrorRate()
    results = []

    flag = 1
    for key, val in ref_dict.items():
        reference = val[1]
        if key not in hyp_dict:
            print("Warning:", key, "is missed!")
            flag = 0
            continue
        else:
            hypothesis = hyp_dict[key][1]
            result = CSSDER(reference, hypothesis)
        print(key, "CDER = {0:.3f}".format(result))
        results.append(result)

    if flag:
        print("Avg CDER : {0:.3f}".format(np.mean(results)))
        return np.mean(results)
    else:
        print("Avg CDER : Error!")
        return None