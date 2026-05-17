export default {
    "task_id": "7d2286d8-6f02-4706-a55d-4b40415d4e9f",
    "document_id": "c971d3df-9266-4dcd-bb22-10f78539ffb4",
    "status": "completed",
    "progress": 100,
    "current_step": null,
    "created_at": "2026-01-23T07:11:43",
    "started_at": "2026-01-23T07:11:45.868104",
    "completed_at": "2026-01-23T07:12:33.057839",
    "error_message": null,
    "processing_mode": "pipeline",
    "priority": 2,
    "retry_count": 0,
    "worker_id": null,
    "metadata": {
        "source_file": "data/7d2286d8-6f02-4706-a55d-4b40415d4e9f/deepseek-ocr.pdf",
        "converter": "pdf_converter",
        "file_size": 7631170,
        "title": "DeepSeek-OCR: Contexts Optical Compression",
        "author": "Haoran Wei; Yaofeng Sun; Yukun Li",
        "subject": "",
        "creator": "arXiv GenPDF (tex2pdf:e76afa9)",
        "producer": "pikepdf 8.15.1",
        "creation_date": "",
        "modification_date": "",
        "pages": 22,
        "format": "png",
        "dpi": 200,
        "page_size": {
            "width": 1654,
            "height": 2339,
            "dpi": 200
        },
        "width": 1654,
        "height": 2339
    },
    "full_markdown": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/fb8e9edb-054a-408b-91c2-1781e0092587_split_1_0001.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=G%2BPNdK5gDZ0YMLSKpHRnYS7EI5c%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n# DeepSeek-OCR: Contexts Optical Compression\nHaoran Wei, Yaofeng Sun, Yukun Li\nDeepSeek-AI\n## Abstract\nWe present DeepSeek-OCR as an initial investigation into the feasibility of compressing long contexts via optical 2D mapping. DeepSeek-OCR consists of two components: DeepEncoder and DeepSeek3B-MoE-A570M as the decoder. Specifically, DeepEncoder serves as the core engine, designed to maintain low activations under high-resolution input while achieving high compression ratios to ensure an optimal and manageable number of vision tokens. Experiments show that when the number of text tokens is within 10 times that of vision tokens (i.e., a compression ratio $< 10\\times$ ), the model can achieve decoding (OCR) precision of $97\\%$. Even at a compression ratio of $20\\times$, the OCR accuracy still remains at about $60\\%$. This shows considerable promise for research areas such as historical long-context compression and memory forgetting mechanisms in LLMs. Beyond this, DeepSeek-OCR also demonstrates high practical value. On OmniDocBench, it surpasses GOT-OCR2.0 (256 tokens/page) using only 100 vision tokens, and outperforms MinerU2.0 (6000+ tokens per page on average) while utilizing fewer than 800 vision tokens. In production, DeepSeek-OCR can generate training data for LLMs/VLMs at a scale of $200k+$ pages per day (a single A100-40G). Codes and model weights are publicly accessible at http://github.com/deepseek-ai/DeepSeek-OCR.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/29cb864e-9870-4235-982d-dc239882a60c_split_1_0007.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=hY2oATLLeLPxBN1tC2ptBSBRLhE%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n(a) Compression on Fox benchmark\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/deb2596c-368d-408d-a044-ad47d47e8160_split_1_0009.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=ASeIRDeZxhlEoM5Y488i8aVCILw%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n(b) Performance on Omnidocbench\nFigure 1 | Figure (a) shows the compression ratio (number of text tokens in ground truth/number of vision tokens model used) testing on Fox [21] benchmark; Figure (b) shows performance comparisons on OmniDocBench [27]. DeepSeek-OCR can achieve state-of-the-art performance among end-to-end models enjoying the fewest vision tokens.\n## Contents\n| Section                                                                 | Page |\n|-------------------------------------------------------------------------|------|\n| 1 Introduction                                                           | 3    |\n| 2 Related Works                                                          | 4    |\n| 2.1 Typical Vision Encoders in VLMs                                       | 4    |\n| 2.2 End-to-end OCR Models                                                 | 4    |\n| 3 Methodology                                                            | 5    |\n| 3.1 Architecture                                                         | 5    |\n| 3.2 DeepEncoder                                                          | 5    |\n| 3.2.1 Architecture of DeepEncoder                                         | 5    |\n| 3.2.2 Multiple resolution support                                        | 6    |\n| 3.3 The MoE Decoder                                                        | 7    |\n| 3.4 Data Engine                                                         | 7    |\n| 3.4.1 OCR 1.0 data                                                        | 7    |\n| 3.4.2 OCR 2.0 data                                                        | 8    |\n| 3.4.3 General vision data                                                | 9    |\n| 3.4.4 Text-only data                                                       | 9    |\n| 3.5 Training Pipelines                                                    | 9    |\n| 3.5.1 Training DeepEncoder                                                  | 10   |\n| 3.5.2 Training DeepSeek-OCR                                               | 10   |\n| 4 Evaluation                                                             | 10   |\n| 4.1 Vision-text Compression Study                                          | 10   |\n| 4.2 OCR Practical Performance                                             | 12   |\n| 4.3 Qualitative Study                                                     | 12   |\n| 4.3.1 Deep parsing                                                         | 12   |\n| 4.3.2 Multilingual recognition                                              | 16   |\n| 4.3.3 General vision understanding                                         | 17   |\n| 5 Discussion                                                             | 18   |\n| 6 Conclusion                                                             | 19   |\n## 1. Introduction\nCurrent Large Language Models (LLMs) face significant computational challenges when processing long textual content due to quadratic scaling with sequence length. We explore a potential solution: leveraging visual modality as an efficient compression medium for textual information. A single image containing document text can represent rich information using substantially fewer tokens than the equivalent digital text, suggesting that optical compression through vision tokens could achieve much higher compression ratios.\nThis insight motivates us to reexamine vision-language models (VLMs) from an LLM-centric perspective, focusing on how vision encoders can enhance LLMs' efficiency in processing textual information rather than basic VQA [12, 16, 24, 32, 41] what humans excel at. OCR tasks, as an intermediate modality bridging vision and language, provide an ideal testbed for this vision-text compression paradigm, as they establish a natural compression-decompression mapping between visual and textual representations while offering quantitative evaluation metrics.\nAccordingly, we present DeepSeek-OCR, a VLM designed as a preliminary proof-of-concept for efficient vision-text compression. Our work makes three primary contributions:\nFirst, we provide comprehensive quantitative analysis of vision-text token compression ratios. Our method achieves $96\\% +$ OCR decoding precision at 9-10x text compression, $\\sim 90\\%$ at 10-12x compression, and $\\sim 60\\%$ at 20x compression on Fox [21] benchmarks featuring diverse document layouts (with actual accuracy being even higher when accounting for formatting differences between output and ground truth), as shown in Figure 1(a). The results demonstrate that compact language models can effectively learn to decode compressed visual representations, suggesting that larger LLMs could readily acquire similar capabilities through appropriate pretraining design.\nSecond, we introduce DeepEncoder, a novel architecture that maintains low activation memory and minimal vision tokens even with high-resolution inputs. It serially connects window attention and global attention encoder components through a $1 6 \\times$ convolutional compressor. This design ensures that the window attention component processes a large number of vision tokens, while the compressor reduces vision tokens before they enter the dense global attention component, achieving effective memory and token compression.\nThird, we develop DeepSeek-OCR based on DeepEncoder and DeepSeek3B-MoE [19, 20]. As shown in Figure 1(b), it achieves state-of-the-art performance within end-to-end models on OmniDocBench while using the fewest vision tokens. Additionally, we equip the model with capabilities for parsing charts, chemical formulas, simple geometric figures, and natural images to enhance its practical utility further. In production, DeepSeek-OCR can generate 33 million pages of data per day for LLMs or VLMs using 20 nodes (each with 8 A100-40G GPUs).\nIn summary, this work presents a preliminary exploration of using visual modality as an efficient compression medium for textual information processing in LLMs. Through DeepSeek- OCR, we demonstrate that vision-text compression can achieve significant token reduction $(7 - 20\\times)$ for different historical context stages, offering a promising direction for addressing long-context challenges in large language models. Our quantitative analysis provides empirical guidelines for VLM token allocation optimization, while the proposed DeepEncoder architecture showcases practical feasibility with real-world deployment capabilities. Although focused on OCR as a proof-of-concept, this paradigm opens new possibilities for rethinking how vision and language modalities can be synergistically combined to enhance computational efficiency in large-scale text processing and agent systems.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/9c92c808-b74f-40c7-a300-72a89509bb7d_split_4_0022.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=BHB9SvJy5jh92xQZzVtnzOFpYA0%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 2 | Typical vision encoders in popular VLMs. Here are three types of encoders commonly used in current open-source VLMs, all of which suffer from their respective deficiencies.\n## 2. Related Works\n## 2.1. Typical Vision Encoders in VLMs\nCurrent open-source VLMs employ three main types of vision encoders, as illustrated in Figure 2. The first type is a dual-tower architecture represented by Vary [36], which utilizes parallel SAM [17] encoder to increase visual vocabulary parameters for high-resolution image processing. While offering controllable parameters and activation memory, this approach suffers from significant drawbacks: it requires dual image preprocessing that complicates deployment and makes encoder pipeline parallelism challenging during training. The second type is tile-based method exemplified by InternVL2.0 [8], which processes images by dividing them into small tiles for parallel computation, reducing activation memory under high-resolution settings. Although capable of handling extremely high resolutions, this approach has notable limitations due to its typically low native encoder resolution (below $512\\times 512$), causing large images to be excessively fragmented and resulting in numerous vision tokens. The third type is adaptive resolution encoding represented by Qwen2-VL [35], which adopts the NaViT [10] paradigm to directly process full images through patch-based segmentation without tile parallelization. While this encoder can handle diverse resolutions flexibly, it faces substantial challenges with large images due to massive activation memory consumption that can cause GPU memory overflow, and sequence packing requires extremely long sequence lengths during training. Long vision tokens will slow down both prefill and generation phases of inference.\n## 2.2. End-to-end OCR Models\nOCR, particularly document parsing task, has been a highly active topic in the image-to-text domain. With the advancement of VLMs, a large number of end-to-end OCR models have emerged, fundamentally transforming the traditional pipeline architecture (which required separate detection and recognition expert models) by simplifying OCR systems. Nougat [6] first employs end-to-end framework for academic paper OCR on arXiv, demonstrating the potential of models in handling dense perception tasks. GOT-OCR2.0 [38] expands the scope of OCR2.0 to include more synthetic image parsing tasks and designs an OCR model with performance-efficiency trade-offs, further highlighting the potential of end-to-end OCR researches. Additionally, general vision models such as Qwen-VL series [35], InternVL series [8], and many their derivatives continuously enhance their document OCR capabilities to explore dense visual perception boundaries. However, a crucial research question that current models have not addressed is: for a document containing 1000 words, how many vision tokens are at least needed for decoding? This question holds significant importance for research in the principle that \"a picture is worth a thousand words.\"\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/cfc28b7b-f2c2-4027-b8a7-451a034e9925_split_5_0029.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=B%2BVrTF1ZkkSq9GSDA34t1WKYp%2Bs%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 3 | The architecture of DeepSeek-OCR. DeepSeek-OCR consists of a DeepEncoder and a DeepSeek-3B-MoE decoder. DeepEncoder is the core of DeepSeek-OCR, comprising three components: a SAM [17] for perception dominated by window attention, a CLIP [29] for knowledge with dense global attention, and a $ 16\\times $ token compressor that bridges between them.\n## 3. Methodology\n## 3.1. Architecture\nAs shown in Figure 3, DeepSeek-OCR enjoys a unified end-to-end VLM architecture consisting of an encoder and a decoder. The encoder (namely DeepEncoder) is responsible for extracting image features and tokenizing as well as compressing visual representations. The decoder is used for generating the required result based on image tokens and prompts. DeepEncoder is approximately 380M in parameters, mainly composed of an 80M SAM-base [17] and a 300M CLIP-large [29] connected in series. The decoder adopts a 3B MoE [19, 20] architecture with 570M activated parameters. In the following paragraphs, we will delve into the model components, data engineering, and training skills.\n## 3.2. DeepEncoder\nTo explore the feasibility of contexts optical compression, we need a vision encoder with the following features: 1.Capable of processing high resolutions; 2.Low activation at high resolutions; 3.Few vision tokens; 4.Support for multiple resolution inputs; 5. Moderate parameter count. However, as described in the Section 2.1, current open-source encoders cannot fully satisfy all these conditions. Therefore, we design a novel vision encoder ourselves, named DeepEncoder.\n## 3.2.1. Architecture of DeepEncoder\nDeepEncoder mainly consists of two components: a visual perception feature extraction component dominated by window attention, and a visual knowledge feature extraction component with dense global attention. To benefit from the pretraining gains of previous works, we use SAM-base (patch-size 16) and CLIP-large as the main architectures for the two components respectively. For CLIP, we remove the first patch embedding layer since its input is no longer images but output tokens from the previous pipeline. Between the two components, we borrow from Vary [36] and use a 2-layer convolutional module to perform $16\\times$ downsampling of vision tokens. Each convolutional layer has a kernel size of 3, stride of 2, padding of 1, and channels increase from 256 to 1024. Assuming we input a $1024\\times 1024$ image, the DeepEncoder will segment it into $1024 / 16 \\times 1024 / 16 = 4096$ patch tokens. Since the first half of encoder is dominated by window attention and only 80M, the activation is acceptable. Before entering global attention,\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/01a3defc-069e-4352-8e2e-9308002dd4c7_split_6_0038.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=Odi00erC0NWwTwF%2FfyVMQ95Sb%2BA%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 4 | To test model performance under different compression ratios (requiring different numbers of vision tokens) and enhance the practicality of DeepSeek-OCR, we configure it with multiple resolution modes.\nthe 4096 tokens go through the compression module and the token count becomes $ 4 0 9 6 / 1 6 = 2 5 6 $ thus making the overall activation memory controllable.\nTable 1 | Multi resolution support of DeepEncoder. For both research and application purposes, we design DeepEncoder with diverse native resolution and dynamic resolution modes.\n<table><thead><tr><th rowspan=\"2\">Mode</th><th colspan=\"4\">Native Resolution</th><th colspan=\"2\">Dynamic Resolution</th></tr><tr><th>Tiny</th><th>Small</th><th>Base</th><th>Large</th><th>Gundam</th><th>Gundam-M</th></tr></thead><tbody><tr><td>Resolution</td><td>512</td><td>640</td><td>1024</td><td>1280</td><td>640+1024</td><td>1024+1280</td></tr><tr><td>Tokens</td><td>64</td><td>100</td><td>256</td><td>400</td><td>n×100+256</td><td>n×256+400</td></tr><tr><td>Process</td><td>resize</td><td>resize</td><td>padding</td><td>padding</td><td>resize + padding</td><td>resize + padding</td></tr></tbody></table>\n## 3.2.2.Multiple resolution support\nSuppose we have an image with 1000 optical characters and we want to test how many vision tokens are needed for decoding. This requires the model to support a variable number of vision tokens. That is to say the DeepEncoder needs to support multiple resolutions.\nWe meet the requirement aforementioned through dynamic interpolation of positional encodings, and design several resolution modes for simultaneous model training to achieve the capability of a single DeepSeek-OCR model supporting multiple resolutions. As shown in Figure 4, DeepEncoder mainly supports two major input modes: native resolution and dynamic resolution. Each of them contains multiple sub-modes.\nNative resolution supports four sub-modes: Tiny, Small, Base, and Large, with corresponding resolutions and token counts of $512 \\times 512$ (64), $640 \\times 640$ (100), $1024 \\times 1024$ (256), and $1280 \\times 1280$ (400) respectively. Since Tiny and Small modes have relatively small resolutions, to avoid wasting vision tokens, images are processed by directly resizing the original shape. For Base and Large modes, in order to preserve the original image aspect ratio, images are padded to the corresponding size. After padding, the number of valid vision tokens is less than the actual number of vision tokens, with the calculation formula being:\n$$\nN _ {\\text {v a l i d}} = \\lceil N _ {\\text {a c t u a l}} \\times [ 1 - ((\\max (w, h) - \\min (w, h)) / (\\max (w, h))) ] \\rceil\n$$\nwhere $ w $ and $ h $ represent the width and height of the original input image.\nDynamic resolution can be composed of two native resolutions. For example, Gundam mode consists of $n \\times 640 \\times 640$ tiles (local views) and a $1024 \\times 1024$ global view. The tiling method following InternVL2.0 [8]. Supporting dynamic resolution is mainly for application considerations, especially for ultra-high-resolution inputs (such as newspaper images). Tiling is a form of secondary window attention that can effectively reduce activation memory further. It's worth noting that due to our relatively large native resolutions, images won't be fragmented too much under dynamic resolution (the number of tiles is controlled within the range of 2 to 9). The vision token number output by the DeepEncoder under Gundam mode is: $n \\times 100 + 256$, where $n$ is the number of tiles. For images with both width and height smaller than 640, $n$ is set to 0, i.e., Gundam mode will degrade to Base mode.\nGundam mode is trained together with the four native resolution modes to achieve the goal of one model supporting multiple resolutions. Note that Gundam-master mode $ ( 1024 \\times 1024 $ local views+1280x1280 global view) is obtained through continued training on a trained DeepSeek- OCR model. This is mainly for load balancing, as Gundam-master's resolution is too large and training it together would slow down the overall training speed.\n## 3.3. The MoE Decoder\nOur decoder uses the DeepSeekMoE [19, 20], specifically DeepSeek-3B-MoE. During inference, the model activates 6 out of 64 routed experts and 2 shared experts, with about 570M activated parameters. The 3B DeepSeekMoE is very suitable for domain-centric (OCR for us) VLM research, as it obtains the expressive capability of a 3B model while enjoying the inference efficiency of a 500M small model.\nThe decoder reconstructs the original text representation from the compressed latent vision tokens of DeepEncoder as:\n$$\nf _ {\\mathrm {d e c}}: \\mathbb {R} ^ {n \\times d _ {\\text {l a t e n t}}} \\rightarrow \\mathbb {R} ^ {N \\times d _ {\\text {t e x t}}}; \\quad \\hat {\\mathbf {X}} = f _ {\\mathrm {d e c}} (\\mathbf {Z}) \\quad \\text {w h e r e} n \\leq N\n$$\nwhere $ \\mathbf{Z} \\in \\mathbb{R}^{n\\times d_{\\mathrm{latent}}} $ are the compressed latent(vision) tokens from DeepEncoder and $ \\hat{\\mathbf{X}} \\in \\mathbb{R}^{N\\times d_{\\mathrm{text}}} $ is the reconstructed text representation. The function $ f_{\\mathrm{dec}} $ represents a non-linear mapping that can be effectively learned by compact language models through OCR-style training. It is reasonable to conjecture that LLMs, through specialized pretraining optimization, would demonstrate more natural integration of such capabilities.\n## 3.4. Data Engine\nWe constructe complex and diverse training data for DeepSeek-OCR, including OCR 1.0 data, which mainly consists of traditional OCR tasks such as scene image OCR and document OCR; OCR 2.0 data, which mainly includes parsing tasks for complex artificial images, such as common charts, chemical formulas, and plane geometry parsing data; General vision data, which is mainly used to inject certain general image understanding capabilities into DeepSeek-OCR and preserve the general vision interface.\n## 3.4.1.OCR 1.0 data\nDocument data is the top priority for DeepSeek-OCR. We collect 30M pages of diverse PDF data covering about 100 languages from the Internet, with Chinese and English accounting for approximately 25M and other languages accounting for 5M. For this data, we create two types of ground truth: coarse annotations and fine annotations. Coarse annotations are extracted\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/e2463129-a237-46b3-bbb6-87e68ced04e9_split_8_0060.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=wQMCMXsngpGysWd6E6RM2vmDhSY%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n(a) Ground truth image\n(b) Fine annotations with layouts\nFigure 5 | OCR 1.0 fine annotations display. We format the ground truth into an interleaved layout and text format, where each paragraph of text is preceded by the coordinates and label of it in the original image. All coordinates are normalized into 1000 bins.\ndirectly from the full dataset using fitz, aimed at teaching the model to recognize optical text, especially in minority languages. Fine annotations include 2M pages each for Chinese and English, labeled using advanced layout models (such as PP-DocLayout [33]) and OCR models (such as MinuerU [34] and GOT-OCR2.0 [38]) to construct detection and recognition interleaved data. For minority languages, in the detection part, we find that the layout model enjoys certain generalization capabilities. In the recognition part, we use fitz to create small patch data to train a GOT-OCR2.0, then use the trained model to label small patches after layout processing, employing a model flywheel to create 600K data samples. During the training of DeepSeek-OCR, coarse labels and fine labels are distinguished using different prompts. The ground truth for fine annotation image-text pairs can be seen in Figure 5. We also collect 3M Word data, constructing high-quality image-text pairs without layout by directly extracting content. This data mainly brings benefits to formulas and HTML-formatted tables. Additionally, we select some open-source data [28, 37] as supplements.\nFor natural scene OCR, our model mainly supports Chinese and English. The image data sources come from LAION [31] and Wukong [13], labeled using PaddleOCR [9], with 10M data samples each for Chinese and English. Like document OCR, natural scene OCR can also control whether to output detection boxes through prompts.\n## 3.4.2.OCR 2.0 data\nFollowing GOT-OCR2.0 [38], we refer to chart, chemical formula, and plane geometry parsing data as OCR 2.0 data. For chart data, following OneChart [7], we use pyecharts and matplotlib\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/cc826af0-e3c0-4383-a3a3-54e686b6d4f8_split_9_0068.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=hUcd%2B1r9VEZdMdI8for9nyKRHMs%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n(a) Image-text ground truth of chart\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/15aeac22-0e29-4d2c-b60c-910dbb27dee1_split_9_0070.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=zvU9NKezNNRZPTlLP4U15S8PsKk%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n(b) Image-text ground truth of geometry\nFigure 6 | For charts, we do not use OneChart's [7] dictionary format, but instead use HTML table format as labels, which can save a certain amount of tokens. For plane geometry, we convert the ground truth to dictionary format, where the dictionary contains keys such as line segments, endpoint coordinates, line segment types, etc., for better readability. Each line segment is encoded using the Slow Perception [39] manner.\nto render 10M images, mainly including commonly used line, bar, pie, and composite charts. We define chart parsing as image-to-HTML-table conversion task, as shown in Figure 6(a). For chemical formulas, we utilize SMILES format from PubChem as the data source and render them into images using RDKit, constructing 5M image-text pairs. For plane geometry images, we follow Slow Perception [39] for generation. Specifically, we use perception-ruler size as 4 to model each line segment. To increase the diversity of rendered data, we introduce geometric translation-invariant data augmentation, where the same geometric image is translated in the original image, corresponding to the same ground truth drawn at the centered position in the coordinate system. Based on this, we construct a total of 1M plane geometry parsing data, as illustrated in Figure 6(b).\n## 3.4.3. General vision data\nDeepEncoder can benefit from CLIP's pretraining gains and has sufficient parameters to incorporate general visual knowledge. Therefore, we also prepare some corresponding data for DeepSeek-OCR.Following DeepSeek-VL2 [40],we generate relevant data for tasks such as caption, detection, and grounding.Note that DeepSeek-OCR is not a general VLM model,and this portion of data accounts for only $ 20\\% $ of the total data.We introduce such type of data mainly to preserve the general vision interface, so that researchers interested in our model and general vision task can conveniently advance their work in the future.\n## 3.4.4.Text-only data\nTo ensure the model's language capabilities, we introduced 10% of in-house text-only pretrain data, with all data processed to a length of 8192 tokens, which is also the sequence length for DeepSeek-OCR. In summary, when training DeepSeek-OCR, OCR data accounts for 70%, general vision data accounts for 20%, and text-only data accounts for 10%.\n## 3.5. Training Pipelines\nOur training pipeline is very simple and consists mainly of two stages: a).Training DeepEncoder independently; b).Training the DeepSeek-OCR. Note that the Gundam-master mode is obtained by continuing training on a pre-trained DeepSeek-OCR model with 6M sampled data. Since the training protocol is identical to other modes, we omit the detailed description hereafter.\n## 3.5.1. Training DeepEncoder\nFollowing Vary [36], we utilize a compact language model [15] and use the next token prediction framework to train DeepEncoder. In this stage, we use all OCR 1.0 and 2.0 data aforementioned, as well as 100M general data sampled from the LAION [31] dataset. All data is trained for 2 epochs with a batch size of 1280, using the AdamW [23] optimizer with cosine annealing scheduler [22] and a learning rate of 5e-5. The training sequence length is 4096.\n## 3.5.2. Training DeepSeek-OCR\nAfter DeepEncoder is ready, we use data mentioned in Section 3.4 to train the DeepSeek-OCR with the entire training process conducted on the HAI-LLM [14] platform. The entire model uses pipeline parallelism (PP) and is divided into 4 parts, with DeepEncoder taking two parts and the decoder taking two parts. For DeepEncoder, we treat SAM and the compressor as the vision tokenizer, place them in PP0 and freeze their parameters, while treating the CLIP part as input embedding layer and place it in PP1 with unfrozen weights for training. For the language model part, since DeepSeek3B-MoE has 12 layers, we place 6 layers each on PP2 and PP3. We use 20 nodes (each with 8 A100-40G GPUs) for training, with a data parallelism (DP) of 40 and a global batch size of 640. We use the AdamW optimizer with a step-based scheduler and an initial learning rate of 3e-5. For text-only data, the training speed is 90B tokens/day, while for multimodal data, the training speed is 70B tokens/day.\nTable 2 | We test DeepSeek-OCR's vision-text compression ratio using all English documents with 600-1300 tokens from the Fox [21] benchmarks. Text tokens represent the number of tokens after tokenizing the ground truth text using DeepSeek-OCR's tokenizer. Vision Tokens=64 or 100 respectively represent the number of vision tokens output by DeepEncoder after resizing input images to $512\\times 512$ and $640\\times 640$.\n<table><thead><tr><th rowspan=\"2\">Text Tokens</th><th colspan=\"2\">Vision Tokens =64</th><th colspan=\"2\">Vision Tokens=100</th><th rowspan=\"2\">Pages</th></tr><tr><th>Precision</th><th>Compression</th><th>Precision</th><th>Compression</th></tr></thead><tbody><tr><td>600-700</td><td>96.5%</td><td>10.5×</td><td>98.5%</td><td>6.7×</td><td>7</td></tr><tr><td>700-800</td><td>93.8%</td><td>11.8×</td><td>97.3%</td><td>7.5×</td><td>28</td></tr><tr><td>800-900</td><td>83.8%</td><td>13.2×</td><td>96.8%</td><td>8.5×</td><td>28</td></tr><tr><td>900-1000</td><td>85.9%</td><td>15.1×</td><td>96.8%</td><td>9.7×</td><td>14</td></tr><tr><td>1000-1100</td><td>79.3%</td><td>16.5×</td><td>91.5%</td><td>10.6×</td><td>11</td></tr><tr><td>1100-1200</td><td>76.4%</td><td>17.7×</td><td>89.8%</td><td>11.3×</td><td>8</td></tr><tr><td>1200-1300</td><td>59.1%</td><td>19.7×</td><td>87.1%</td><td>12.6×</td><td>4</td></tr></tbody></table>\n## 4. Evaluation\n## 4.1. Vision-text Compression Study\nWe select Fox [21] benchmarks to verify DeepSeek-OCR's compression-decompression capability for text-rich documents, in order to preliminarily explore the feasibility and boundaries of contexts optical compression. We use the English document portion of Fox, tokenize the ground truth text with DeepSeek-OCR's tokenizer (vocabulary size of approximately 129k), and select documents with 600-1300 tokens for testing, which happens to be 100 pages. Since the number of text tokens is not large, we only need to test performance in Tiny and Small modes, where Tiny mode corresponds to 64 tokens and Small mode corresponds to 100 tokens. We use the prompt\nTable 3 | We use OmniDocBench [27] to test the performance of DeepSeek-OCR on real document parsing tasks. All metrics in the table are edit distances, where smaller values indicate better performance. \"Tokens\" represents the average number of vision tokens used per page, and \"†200dpi\" means using fitz to interpolate the original image to 200dpi. For the DeepSeek-OCR model, the values in parentheses in the \"Tokens\" column represent valid vision tokens, calculated according to Equation 1.\n<table><thead><tr><th rowspan=\"2\">Model</th><th rowspan=\"2\">Tokens</th><th colspan=\"5\">English</th><th colspan=\"5\">Chinese</th></tr><tr><th>overall</th><th>text</th><th>formula</th><th>table</th><th>order</th><th>overall</th><th>text</th><th>formula</th><th>table</th><th>order</th></tr></thead><tbody><tr><td colspan=\"13\"><strong>Pipline Models</strong></td></tr><tr><td>Dolphin [11]</td><td>-</td><td>0.356</td><td>0.352</td><td>0.465</td><td>0.258</td><td>0.35</td><td>0.44</td><td>0.44</td><td>0.604</td><td>0.367</td><td>0.351</td></tr><tr><td>Marker [1]</td><td>-</td><td>0.296</td><td>0.085</td><td>0.374</td><td>0.609</td><td>0.116</td><td>0.497</td><td>0.293</td><td>0.688</td><td>0.678</td><td>0.329</td></tr><tr><td>Mathpix [2]</td><td>-</td><td>0.191</td><td>0.105</td><td>0.306</td><td>0.243</td><td>0.108</td><td>0.364</td><td>0.381</td><td>0.454</td><td>0.32</td><td>0.30</td></tr><tr><td>MinerU-2.1.1 [34]</td><td>-</td><td>0.162</td><td>0.072</td><td>0.313</td><td>0.166</td><td>0.097</td><td>0.244</td><td>0.111</td><td>0.581</td><td>0.15</td><td>0.136</td></tr><tr><td>MonkeyOCR-1.2B [18]</td><td>-</td><td>0.154</td><td>0.062</td><td>0.295</td><td>0.164</td><td>0.094</td><td>0.263</td><td>0.179</td><td>0.464</td><td>0.168</td><td>0.243</td></tr><tr><td>PPstructure-v3 [9]</td><td>-</td><td>0.152</td><td>0.073</td><td>0.295</td><td>0.162</td><td>0.077</td><td>0.223</td><td>0.136</td><td>0.535</td><td>0.111</td><td>0.11</td></tr><tr><td colspan=\"13\"><strong>End-to-end Models</strong></td></tr><tr><td>Nougat [6]</td><td>2352</td><td>0.452</td><td>0.365</td><td>0.488</td><td>0.572</td><td>0.382</td><td>0.973</td><td>0.998</td><td>0.941</td><td>1.00</td><td>0.954</td></tr><tr><td>SmolDocling [25]</td><td>392</td><td>0.493</td><td>0.262</td><td>0.753</td><td>0.729</td><td>0.227</td><td>0.816</td><td>0.838</td><td>0.997</td><td>0.907</td><td>0.522</td></tr><tr><td>InternVL2-76B [8]</td><td>6790</td><td>0.44</td><td>0.353</td><td>0.543</td><td>0.547</td><td>0.317</td><td>0.443</td><td>0.29</td><td>0.701</td><td>0.555</td><td>0.228</td></tr><tr><td>Qwen2.5-VL-7B [5]</td><td>3949</td><td>0.316</td><td>0.151</td><td>0.376</td><td>0.598</td><td>0.138</td><td>0.399</td><td>0.243</td><td>0.5</td><td>0.627</td><td>0.226</td></tr><tr><td>OLMOCR [28]</td><td>3949</td><td>0.326</td><td>0.097</td><td>0.455</td><td>0.608</td><td>0.145</td><td>0.469</td><td>0.293</td><td>0.655</td><td>0.652</td><td>0.277</td></tr><tr><td>GOT-OCR2.0 [38]</td><td>256</td><td>0.287</td><td>0.189</td><td>0.360</td><td>0.459</td><td>0.141</td><td>0.411</td><td>0.315</td><td>0.528</td><td>0.52</td><td>0.28</td></tr><tr><td>OCRFlux-3B [3]</td><td>3949</td><td>0.238</td><td>0.112</td><td>0.447</td><td>0.269</td><td>0.126</td><td>0.349</td><td>0.256</td><td>0.716</td><td>0.162</td><td>0.263</td></tr><tr><td>GPT4o [26]</td><td>-</td><td>0.233</td><td>0.144</td><td>0.425</td><td>0.234</td><td>0.128</td><td>0.399</td><td>0.409</td><td>0.606</td><td>0.329</td><td>0.251</td></tr><tr><td>InternVL3-78B [42]</td><td>6790</td><td>0.218</td><td>0.117</td><td>0.38</td><td>0.279</td><td>0.095</td><td>0.296</td><td>0.21</td><td>0.533</td><td>0.282</td><td>0.161</td></tr><tr><td>Qwen2.5-VL-72B [5]</td><td>3949</td><td>0.214</td><td>0.092</td><td>0.315</td><td>0.341</td><td>0.106</td><td>0.261</td><td>0.18</td><td>0.434</td><td>0.262</td><td>0.168</td></tr><tr><td>dots.ocr [30]</td><td>3949</td><td>0.182</td><td>0.137</td><td>0.320</td><td>0.166</td><td>0.182</td><td>0.261</td><td>0.229</td><td>0.468</td><td>0.160</td><td>0.261</td></tr><tr><td>Gemini2.5-Pro [4]</td><td>-</td><td>0.148</td><td>0.055</td><td>0.356</td><td>0.13</td><td>0.049</td><td>0.212</td><td>0.168</td><td>0.439</td><td>0.119</td><td>0.121</td></tr><tr><td>MinerU2.0 [34]</td><td>6790</td><td>0.133</td><td>0.045</td><td>0.273</td><td>0.15</td><td>0.066</td><td>0.238</td><td>0.115</td><td>0.506</td><td>0.209</td><td>0.122</td></tr><tr><td>dots.ocr†200dpi [30]</td><td>5545</td><td>0.125</td><td>0.032</td><td>0.329</td><td>0.099</td><td>0.04</td><td>0.16</td><td>0.066</td><td>0.416</td><td>0.092</td><td>0.067</td></tr><tr><td colspan=\"13\"><strong>DeepSeek-OCR (end2end)</strong></td></tr><tr><td>Tiny</td><td>64</td><td>0.386</td><td>0.373</td><td>0.469</td><td>0.422</td><td>0.283</td><td>0.361</td><td>0.307</td><td>0.635</td><td>0.266</td><td>0.236</td></tr><tr><td>Small</td><td>100</td><td>0.221</td><td>0.142</td><td>0.373</td><td>0.242</td><td>0.125</td><td>0.284</td><td>0.24</td><td>0.53</td><td>0.159</td><td>0.205</td></tr><tr><td>Base</td><td>256(182)</td><td>0.137</td><td>0.054</td><td>0.267</td><td>0.163</td><td>0.064</td><td>0.24</td><td>0.205</td><td>0.474</td><td>0.1</td><td>0.181</td></tr><tr><td>Large</td><td>400(285)</td><td>0.138</td><td>0.054</td><td>0.277</td><td>0.152</td><td>0.067</td><td>0.208</td><td>0.143</td><td>0.461</td><td>0.104</td><td>0.123</td></tr><tr><td>Gundam</td><td>795</td><td>0.127</td><td>0.043</td><td>0.269</td><td>0.134</td><td>0.062</td><td>0.181</td><td>0.097</td><td>0.432</td><td>0.089</td><td>0.103</td></tr><tr><td>Gundam-M†200dpi</td><td>1853</td><td>0.123</td><td>0.049</td><td>0.242</td><td>0.147</td><td>0.056</td><td>0.157</td><td>0.087</td><td>0.377</td><td>0.08</td><td>0.085</td></tr></tbody></table>\nwithout layout:\"<image>\\nFree OCR.\" to control the model's output format. Nevertheless, the output format still cannot completely match Fox benchmarks, so the actual performance would be somewhat higher than the test results.\nAs shown in Table 2, within a $10\\times$ compression ratio, the model's decoding precision can reach approximately 97%, which is a very promising result. In the future, it may be possible to achieve nearly $10\\times$ lossless contexts compression through text-to-image approaches. When the compression ratio exceeds $10\\times$, performance begins to decline, which may have two reasons: one is that the layout of long documents becomes more complex, and another reason may be that long texts become blurred at $512\\times 512$ or $640\\times 640$ resolution. The first issue can be solved by rendering texts onto a single layout page, while we believe the second issue will become\na feature of the forgetting mechanism. When compressing tokens by nearly $ 20\\times $ , we find that precision can still approach $ 60\\% $ . These results indicate that optical contexts compression is a very promising and worthwhile research direction, and this approach does not bring any overhead because it can leverage VLM infrastructure, as multimodal systems inherently require an additional vision encoder.\nTable 4 | Edit distances for different categories of documents in OmniDocBench. The results show that some types of documents can achieve good performance with just 64 or 100 vision tokens, while others require Gundam mode.\n<table><thead><tr><th>Mode \\ Type</th><th>Book Slides</th><th>Financial Report</th><th>Textbook</th><th>Exam Paper</th><th>Magazine</th><th>Academic Papers</th><th>Notes</th><th>Newspaper</th><th>Overall</th></tr></thead><tbody><tr><td>Tiny</td><td>0.147</td><td>0.116</td><td>0.207</td><td>0.173</td><td>0.294</td><td>0.201</td><td>0.395</td><td>0.297</td><td>0.94</td><td>0.32</td></tr><tr><td>Small</td><td>0.085</td><td>0.111</td><td>0.079</td><td>0.147</td><td>0.171</td><td>0.107</td><td>0.131</td><td>0.187</td><td>0.744</td><td>0.205</td></tr><tr><td>Base</td><td>0.037</td><td>0.08</td><td>0.027</td><td>0.1</td><td>0.13</td><td>0.073</td><td>0.052</td><td>0.176</td><td>0.645</td><td>0.156</td></tr><tr><td>Large</td><td>0.038</td><td>0.108</td><td>0.022</td><td>0.084</td><td>0.109</td><td>0.06</td><td>0.053</td><td>0.155</td><td>0.353</td><td>0.117</td></tr><tr><td>Gundam</td><td>0.035</td><td>0.085</td><td>0.289</td><td>0.095</td><td>0.094</td><td>0.059</td><td>0.039</td><td>0.153</td><td>0.122</td><td>0.083</td></tr><tr><td>Guandam-M</td><td>0.052</td><td>0.09</td><td>0.034</td><td>0.091</td><td>0.079</td><td>0.079</td><td>0.048</td><td>0.1</td><td>0.099</td><td>0.077</td></tr></tbody></table>\n## 4.2. OCR Practical Performance\nDeepSeek-OCR is not only an experimental model; it has strong practical capabilities and can construct data for LLM/VLM pretraining. To quantify OCR performance, we test DeepSeek-OCR on OmniDocBench [27], with results shown in Table 3. Requiring only 100 vision tokens (640x640 resolution), DeepSeek-OCR surpasses GOT-OCR2.0 [38] which uses 256 tokens; with 400 tokens (285 valid tokens, $1280\\times 1280$ resolution), it achieves on-par performance with state-of-the-arts on this benchmark. Using fewer than 800 tokens (Gundam mode), DeepSeek-OCR outperforms MinerU2.0 [34] which needs nearly 7,000 vision tokens. These results demonstrate that our DeepSeek-OCR model is powerful in practical applications, and because the higher tokens compression, it enjoys a higher research ceiling.\nAs shown in Table 4, some categories of documents require very few tokens to achieve satisfactory performance, such as slides which only need 64 vision tokens. For book and report documents, DeepSeek-OCR can achieve good performance with only 100 vision tokens. Combined with the analysis from Section 4.1, this may be because most text tokens in these document categories are within 1,000, meaning the vision-token compression ratio does not exceed $10\\times$. For newspapers, Gundam or even Gundam-master mode is required to achieve acceptable edit distances, because the text tokens in newspapers are 4-5,000, far exceeding the $10\\times$ compression of other modes. These experimental results further demonstrate the boundaries of contexts optical compression, which may provide effective references for researches on the vision token optimization in VLMs and context compression, forgetting mechanisms in LLMs.\n## 4.3. Qualitative Study\n## 4.3.1. Deep parsing\nDeepSeek-OCR possesses both layout and OCR 2.0 capabilities, enabling it to further parse images within documents through secondary model calls, a feature we refer to as \"deep parsing\". As shown in Figures 7,8,9,10, our model can perform deep parsing on charts, geometry, chemical formulas, and even natural images, requiring only a unified prompt.\nA European defense renaissance likely ahead\nA much more adverse tariff base case\n## Macro news and views\n## We provide a brief snapshot on the most important economies for the global markets\n## US\nLatest GS proprietary datapoints/major changes in views  \n- We now assume a $70\\%$ increase in the US effective tariff rate. IVs 45p prior to reapplied tariffs and further increase in product-specific tariffs now seem likely.\n- We raised our Dec 2025 core inflation rate to $3\\%$ from $(3.9\\%)$, lowered our 2025 GDP growth forecast to $1.7\\%$ from $1.8\\%$ and increased our 2026 GDP growth forecast to $2.5\\%$ and slightly raised our end-2025 unemployment rate forecast to $4.2\\%$ from $4.1\\%$ and our 12m recession forecast to $4.3\\%$ from $4.2\\%$.\n- Fed cuts; we still expect two in 2025 and one more in 2026.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/185472ff-3bc6-41e6-911f-e77bf1b55efa_split_13_0110.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=DnCsH2oDx14WupX6R5AN0kZZ9%2Bs%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nSource Goldman Sachs GR\n## Europe\nLatest GS property datapoints/major changes in views  \n- We recently raised our 2015/2026/2027 euro area real GDP growth forecast to $3.8\\%$ and projected a $4.9\\%$ increase in turn, our ECB terminal rate forecast to $2\\%$ in Jun from $1.75\\%$ in Jul to reflect the higher European defense spending.\n- Germany's substantial fiscal package, which we expect to pass, though it is far from a done deal given political hurdles. Potential Russia-Ukraine ceasefire, which we think would be a major factor in the conflict, entails a comprehensive resolution to the conflict $(+0.5\\%)$.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/e19010c6-ed2f-457e-958a-79f7c36aa80f_split_13_0115.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=oG0G%2B0sfYbB48UtQ7aqX3wVom70%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n## Japan\nLatest GS proprietary datapoints/major changes in views No major changes in views\n- $Bo$ policy: we expect the $Bo$ to continue raising rates at a pace of two per year, with next the hike in July.\n- Shunto spring wage negotiations, we expect a shunto base pay rise of least in the low 3% range for this year, with risks to the base pay and wage growth.\n- Japanese consumer sentiment, which softened for a third consecutive month in February.\n- Japan's industrial production, which fell for a third consecutive month in January.\nA strong spring wage negotiation season\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c1c7da9d-669e-42f4-8888-29bcb575492a_split_13_0123.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=zjbpc3JPFXmNw87AnUx8Px5IjRs%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n## Emerging Markets (EM)\nLatest GS proprietary datapoints/major changes in views No major changes in views\nDatapoints/trends we're focused on\n- China growth; we expect high-tech manufacturing to continue playing an important role in supporting China's growth ahead.\n- China CPI inflation, which fell sharply in February, though this is not surprising given the economic relations related to the earlier-than-usual Lunar New Year holiday.\n- India's cyclical growth slowdown, the worst of which we think is now over, but we expect an ongoing recovery.\n- CEEMEA growth, which would benefit from a potential resolution to the Russia-Ukraine conflict.\nGoldman Sachs Global Investment Research\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f5cd54b3-aa20-4acd-897a-39b4d022a886_split_13_0130.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=vHWHyHK3vpz9LdsvN76FvH1H8%2Bk%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nInput image\n<image>\\nParse the figure.\nDeep Parsing\n## Top of Mind\n## Macro news and views\n## We provide a brief snapshot on the most important economies for the global markets.\n## US\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f5f5b11e-a073-4b92-9220-9a9f0ca53a56_split_13_0138.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=AdWHYGFIPfTuH%2FNVe0ZJJ7SjfTY%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n- Test QS GDP deteriorates/major changes in the US effective tariff rate. - We now assume a 10ppp increase in the effective tariff rate. - A 4ppp prior to recalcitrant tariffs and further increases in product-specific tariffs now seem likely.\n<table border=\"1\"><tr><td></td><td>2024</td><td>2025</td><td>2026</td><td>2027</td></tr><tr><td>Germany</td><td>2.1</td><td>2.3</td><td>2.7</td><td>3.0</td></tr><tr><td>France</td><td>2.05</td><td>2.15</td><td>2.4</td><td>2.8</td></tr><tr><td>Italy</td><td>1.45</td><td>1.65</td><td>2.05</td><td>2.55</td></tr><tr><td>Spain</td><td>1.25</td><td>1.55</td><td>2.0</td><td>2.55</td></tr><tr><td>Euro area</td><td>1.85</td><td>2.05</td><td>2.4</td><td>2.8</td></tr></table>\nWe raised our Dec 2025 core PSE inflation forecast to $3% from 2.5%, based on our 2025 GDP growth forecast to $4.1% and the latest revised 2026 GDP forecast to $4.8%. We also raised our 2.5-years and slightly raised our end-2025 unemployment rate to $7.9% and our latest revised 2026 unemployment rate to $7.6% (from 20% to 15%) in refect of our new base case data.\n- Fed cuts, we still expect two in 2025 and one more in 2026.\n- More advanced hedge fund base case.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/2161966c-d229-45b7-9e00-73ff30cead1b_split_13_0143.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=z%2FuW3bma68QqZVFbNOikTwqEpyA%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nSource Goldman Sachs GW.\n## Europe\nGoldman Sachs Global Investment Research\n- Most GSI quantitative datapoints/major changes in latest week. We recently raised our 2020/2022/2023 area real GDP growth forecast to $1.5 per cent, and revised the 2021/2022/2023 area real GDP growth forecast to $1.4 per cent in turn, our ECB terminal rate forecast to 2% in June from the latest week. The latest weekly rate forecast is $1.6 per cent, pending we expect next year the new low level.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f75084ea-b769-498f-a224-15ddea596c35_split_13_0148.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=2mAKur1rZadAF29NM3fa%2FRfaBvA%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n## Japan\n- latest US quantitative datapoints/major changes in views\n- No more changes in views on\nDatapoints/trends we're focused on\n- The latest data from Fed to continue hikating rates at a pace of two per week (half year) with the next hike in July.\n- Shunto spring wage negotiations; we expect a shuttle base for the next three months, and we are looking to skype up the issued strong wage requests.\n- Japanese consumer sentiment, which softened for a third quarter, is improving.\n- Japan's industrial production, which fell for a third consecutive month in January.\n\n- strong spring wage negotiation season\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c35ea21f-1f83-40c5-a553-427ee40d4277_split_13_0151.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=YlVJHFODW9iv9%2BaS2EhR4wK8ohI%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n## Emerging Markets (EM)\n*test GS proprietary datapoints/minor changes in views No major changes in views.\n- China growth, we expect high tech manufacturing to continue playing an important role in supporting China's growth ahead.\n- The China inflation, which fell sharply in February, though this is expected to slow down as the reader-related to earlier-time Lunar New Year holiday.\n- India's cyclical growth slowdown, the word of which we think is now over, but we expect an only gradual recovery.\n- CEEMEA growth, which would benefit from a potential revolution in the Russia-Iran conflict\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/bb3457d3-e810-4785-9e61-40303747422e_split_13_0156.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=fuqc8v689BdDdOXdNcaVixAjL1s%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n## Result\n## Europe\n## Latest GS proprietary datapoints/major changes in views\nWe recently raised our 2025/2026/2027 Euro area real GDP forecasts to $0.83\\% /1.15\\% /1.3\\%$ (from $0.7\\% /1.15\\% /1.3\\%$), and in our Euro ECB rate forecast increase of $2\\%$ in June (in $1.75\\%$ vs. July) to reflect the higher European spending we expect over the next year.\nDatapoints/trends we're focused on\nGermany's substantial fiscal package, which we expect to pass, though it's far from a done deal given political hurdles. Potential Russia-Ukraine ceasefire, which we think would result in a middle euro area GDP boost (0.27%), unless it relates to the US-China trade war.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c7f1839f-692f-4b2a-9d71-505b44ca0b0c_split_13_0163.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=uwpQJw%2FEtw3sD6sEuaoKovXJwgY%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nNo major changes in views. Datapoints/trends were focused on BoJ policy; we expect the BoJ to continue hikes rate at a pace of two hikers per week, with the next hike in July. Shuttle wage negotiations would; extend a shuttle base pay rise of less than the low $3% range for this year; with risks skewed to the upside given strong wage requests. Japanese consumer sentiment, which softened for a third consecutive month in February, Japan's industrial production, which fell for a third consecutive month in January.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/41f44900-468f-42e1-8c88-fd1d84254ae2_split_13_0165.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=pI%2FCsUXwDhmmNENA%2FAy26f8kScI%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nRendering\nFigure 7 | In the field of financial research reports, the deep parsing mode of DeepSeek-OCR can be used to obtain structured results of charts within documents. Charts are a crucial form of data representation in finance and scientific fields, and the chart structured extraction is an indispensable capability for future OCR models.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/3bec5c81-2a02-483f-bd4a-517f375bdfc2_split_14_0168.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=F4c9cdi734aVpthpTtXqhz8%2FTPQ%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 8 | For books and articles, the deep parsing mode can output dense captions for natural images in the documents. With just a prompt, the model can automatically identify what type of image it is and output the required results.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/d9ed8d00-97cc-4d31-97b9-b46971756e95_split_15_0170.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=lVJ0B0Ft1wBTtLaA8lIsvGrkYDM%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 9 | DeepSeek-OCR in deep parsing mode can also recognize chemical formulas within chemical documents and convert them to SMILES format. In the future, OCR 1.0+2.0 technology may play a significant role in the development of VLM/LLM in STEM fields.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c30e9b1c-64bd-417c-8ec2-3e5a3e841395_split_16_0172.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=wsZdeu1apKojWaQMcOBRIdFr3gk%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 10 | DeepSeek-OCR also possesses the capability to copy (structure) simple planar geometric figures. Due to the intricate interdependencies among line segments in geometric shapes, parsing geometry task is extremely challenging and has a long way to go.\n## 4.3.2. Multilingual recognition\nPDF data on the Internet contains not only Chinese and English, but also a large amount of multilingual data, which is also crucial when training LLMs. For PDF documents, DeepSeek- OCR can handle nearly 100 languages. Like Chinese and English documents, multilingual data also supports both layout and non-layout OCR formats. The visualization results are shown in Figure 11, where we select Arabic and Sinhala languages to demonstrate results.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/72cd03c4-239a-4b57-bdc1-b188ae957981_split_17_0176.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=z95yvb5hR2CMvUPHJCmWJnzdcns%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 11 | To endow the capability of processing widely crawled PDFs (multilingual data), we train our model with OCR capabilities for nearly 100 languages. Minority language documents can also support both layout and non-layout outputs through different prompts.\n## 4.3.3. General vision understanding\nWe also provide DeepSeek-OCR with a certain degree of general image understanding capabilities. The related visualization results are shown in Figure 12.\n<image>\\nLocate <|ref|>the teacher</|ref|> in the image.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/459e232f-8b1d-4064-bc43-f79e55048bd6_split_18_0181.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=6YWFOPZXqPcNVMAv7oxEXTtIY2E%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/a4212f01-268a-4858-ab86-b1f8aab9a1f8_split_18_0182.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=HAG24Ulj6CpB7NjCk194vd33Yao%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nA green plastic container labeled for food purposes. The lid is yellow and appears slightly worn out.\n\nOn the front label:\n- At the top left corner, some Chinese characters.\n- In bold black letters near the center-top reads \"6月香\" (June Fragrance).\n- Below that, smaller white font states \"新鲜甜瓜香\" which translates roughly to \"Fresh Sweet Saffron Fruit.\"\n- A small part of the label is large lettering stating \"豆蔻酱,\" meaning \"Bean Paste Sauce.\"\nAdditional information includes:\n- A small circular logo indicating quality assurance (\"优质品质\").\n- An illustration showing what seems like a dish made using bean paste sauce.\n- Text below the main title says \"专注25年, 只做原浆酱\" translating to \"Focusing since 1998, only making authentic fermented bean paste\".\n- On the bottom right side, additional product specifications include \"净含量: $500\\mathrm{g}$\".\nOverall Style/Type: It looks like commercial packaging designed specifically for preserving food items within the jar. It has clear labeling intended for easy identification and understanding among consumers who read Mandarin.\nNote: There might be slight variations due to handwriting styles but overall maintains readability regarding brand identity and contents description.\n<image>\\nldentify all objects in the image and output them in bounding boxes.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/fc249b7a-78e3-492f-854e-757ff7bd7a89_split_18_0188.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=JTENRyhV4Ktovi5ZafL20MQq3ko%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/67aaa422-b93a-4e09-aec7-4360739e8854_split_18_0189.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=8wK30pybpyGtG2XI3GWnsCQFnJo%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n## <image>\\n这是一张\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f4147a15-0adb-4c84-b8d4-c5e83a6bdfee_split_18_0191.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=jlGP3kv9ZUnyjxPgFTE1GwGkr4U%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n，展示了一辆红色的消防栓上有一个笑 显得非常友好和亲切。 消防栓的顶部有一个黑色的盖子，周围有一些金属脚 在消防栓的底部，有一个粉红色的贴纸，上面写着“bowtie”。背景中可以看到一条街道，街道上有几辆停放的汽车和一些树木。 条画面给人一种温馨和友好的感觉。\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/60792794-3a37-43a2-a720-71d32793f546_split_18_0193.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=p1czRBIsFCaCHxNlVDawpWymHIg%3D\" alt=\"Image\" width=\"3%\" /></div>\n\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/9dba89cb-6cab-41e7-b408-bca0ae1f2a4a_split_18_0194.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=DiFXcJzE%2FrFgbf8qWcDubKGycZo%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 12 | We retain DeepSeek-OCR's capabilities in general visual understanding, mainly including image description, object detection, grounding, etc. Meanwhile, due to the inclusion of text-only data, DeepSeek-OCR's language capabilities are also retained. Note that since we do not include SFT (Supervised Fine-Tuning) stage, the model is not a chatbot, and some capabilities need completion prompts to be activated.\n## 5. Discussion\nOur work represents an initial exploration into the boundaries of vision-text compression, investigating how many vision tokens are required to decode N text tokens. The preliminary results are encouraging: DeepSeek-OCR achieves near-lossless OCR compression at approximately 10x ratios, while 20x compression still retains 60% accuracy. These findings suggest promising directions for future applications, such as implementing optical processing for dialogue histories beyond k rounds in multi-turn conversations to achieve 10x compression efficiency.\n<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/03107544-1058-44b2-b940-901b265fabc8_split_19_0198.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688353&Signature=WCnxq9DdeveYxqS%2Bgw3%2BPu2qe5M%3D\" alt=\"Image\" width=\"3%\" /></div>\n\nFigure 13 | Forgetting mechanisms constitute one of the most fundamental characteristics of human memory. The contexts optical compression approach can simulate this mechanism by rendering previous rounds of historical text onto images for initial compression, then progressively resizing older images to achieve multi-level compression, where token counts gradually decrease and text becomes increasingly blurred, thereby accomplishing textual forgetting.\nFor older contexts, we could progressively downsizing the rendered images to further reduce token consumption. This assumption draws inspiration from the natural parallel between human memory decay over time and visual perception degradation over spatial distance—both exhibit similar patterns of progressive information loss, as shown in Figure 13. By combining these mechanisms, contexts optical compression method enables a form of memory decay that mirrors biological forgetting curves, where recent information maintains high fidelity while distant memories naturally fade through increased compression ratios.\nWhile our initial exploration shows potential for scalable ultra-long context processing, where recent contexts preserve high resolution and older contexts consume fewer resources, we acknowledge this is early-stage work that requires further investigation. The approach suggests a path toward theoretically unlimited context architectures that balance information retention with computational constraints, though the practical implications and limitations of such vision-text compression systems warrant deeper study in future research.\n## 6. Conclusion\nIn this technical report, we propose DeepSeek-OCR and preliminarily validate the feasibility of contexts optical compression through this model, demonstrating that the model can effectively decode text tokens exceeding 10 times the quantity from a small number of vision tokens. We believe this finding will facilitate the development of VLMs and LLMs in the future. Additionally, DeepSeek-OCR is a highly practical model capable of large-scale pretraining data production, serving as an indispensable assistant for LLMs. Of course, OCR alone is insufficient to fully validate true context optical compression and we will conduct digital-optical text interleaved pretraining, needle-in-a-haystack testing, and other evaluations in the future. From another perspective, optical contexts compression still offers substantial room for research and improvement, representing a promising new direction.\n## References\n[1] Marker. URL https://github.com/datalab-to/marker.\n[2] Mathpix. URL https://mathpix.com/.\n[3] Ocrflux, 2025. URL https://github.com/chatdoc-com/OCRFlux.\n[4] G. AI. Gemini 2.5-pro, 2025. URL https://gemini.google.com/.\n[5] S. Bai, K. Chen, X. Liu, J. Wang, W. Ge, S. Song, K. Dang, P. Wang, S. Wang, J. Tang, H. Zhong, Y. Zhu, M. Yang, Z. Li, J. Wan, P. Wang, W. Ding, Z. Fu, Y. Xu, J. Ye, X. Zhang, T. Xie, Z. Cheng, H. Zhang, Z. Yang, H. Xu, and J. Lin. Qwen2.5-vl technical report. arXiv preprint arXiv:2502.13923, 2025.\n[6] L. Blecher, G. Cucurull, T. Scialom, and R. Stojnic. Nougat: Neural optical understanding for academic documents. arXiv preprint arXiv:2308.13418, 2023.\n[7] J. Chen, L. Kong, H. Wei, C. Liu, Z. Ge, L. Zhao, J. Sun, C. Han, and X. Zhang. Onechart Purify the chart structural extraction via one auxiliary token. In Proceedings of the 32nd ACM International Conference on Multimedia, pages 147-155, 2024.\n[8] Z. Chen, W. Wang, H. Tian, S. Ye, Z. Gao, E. Cui, W. Tong, K. Hu, J. Luo, Z. Ma, et al. How far are we to gpt-4v? closing the gap to commercial multimodal models with open-source suites. arXiv preprint arXiv:2404.16821, 2024.\n[9] C. Cui, T. Sun, M. Lin, T. Gao, Y. Zhang, J. Liu, X. Wang, Z. Zhang, C. Zhou, H. Liu, et al. Paddleocr 3.0 technical report. arXiv preprint arXiv:2507.05595, 2025.\n[10] M. Dehghani, J. Djolonga, B. Mustafa, P. Padlewski, J. Heek, J. Gilmer, A. Steiner, M. Caron, R. Geirhos, I. Alabdulmohsin, et al. Patch n' pack: Navit, a vision transformer for any aspect ratio and resolution. Advances in Neural Information Processing Systems, 36:3632-3656, 2023.\n[11] H. Feng, S. Wei, X. Fei, W. Shi, Y. Han, L. Liao, J. Lu, B. Wu, Q. Liu, C. Lin, et al. Dolphin: Document image parsing via heterogeneous anchor prompting. arXiv preprint arXiv:2505.14059, 2025.\n[12] Y. Goyal, T. Khot, D. Summers-Stay, D. Batra, and D. Parikh. Making the v in vqa matter: Elevating the role of image understanding in visual question answering. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 6904-6913, 2017.\n[13] J. Gu, X. Meng, G. Lu, L. Hou, N. Minzhe, X. Liang, L. Yao, R. Huang, W. Zhang, X. Jiang, et al. Wukong: A 100 million large-scale chinese cross-modal pre-training benchmark. Advances in Neural Information Processing Systems, 35:26418-26431, 2022.\n[14] High-flyer. HAI-LLM: Efficient and lightweight training tool for large models, 2023. URL https://www.high-flyer.cn/en/blog/hai-llm.\n[15] S. Iyer, X. V. Lin, R. Pasunuru, T. Mihaylov, D. Simig, P. Yu, K. Shuster, T. Wang, Q. Liu, P. S. Koura, et al. Opt-impl: Scaling language model instruction meta learning through the lens of generalization. arXiv preprint arXiv:2212.12017, 2022.\n[16] S. Kazemzadeh, V. Ordonez, M. Matten, and T. Berg. Referitgame: Referring to objects in photographs of natural scenes. In Proceedings of the 2014 conference on empirical methods in natural language processing (EMNLP), pages 787-798, 2014.\n[17] A. Kirillov, E. Mintun, N. Ravi, H. Mao, C. Rolland, L. Gustafson, T. Xiao, S. Whitehead, A. C. Berg, W.-Y. Lo, et al. Segment anything. arXiv preprint arXiv:2304.02643, 2023.\n[18] Z. Li, Y. Liu, Q. Liu, Z. Ma, Z. Zhang, S. Zhang, Z. Guo, J. Zhang, X. Wang, and X. Bai. Monkeyocr: Document parsing with a structure-recognition-relation triplet paradigm. arXiv preprint arXiv:2506.05218, 2025.\n[19] A. Liu, B. Feng, B. Wang, B. Wang, B. Liu, C. Zhao, C. Dengr, C. Ruan, D. Dai, D. Guo, et al. Deepseek-v2: A strong, economical, and efficient mixture-of-experts language model. arXiv preprint arXiv:2405.04434, 2024.\n[20] A. Liu, B. Feng, B. Xue, B. Wang, B. Wu, C. Lu, C. Zhao, C. Deng, C. Zhang, C. Ruan, et al. Deepseek-v3 technical report. arXiv preprint arXiv:2412.19437, 2024.\n[21] C. Liu, H. Wei, J. Chen, L. Kong, Z. Ge, Z. Zhu, L. Zhao, J. Sun, C. Han, and X. Zhang. Focus anywhere for fine-grained multi-page document understanding. arXiv preprint arXiv:2405.14295, 2024.\n[22] I. Loshchilov and F. Hutter. Sgdr: Stochastic gradient descent with warm restarts. arXiv preprint arXiv:1608.03983, 2016.\n[23] I. Loshchilov and F. Hutter. Decoupled weight decay regularization. In ICLR, 2019.\n[24] A. Masry, D. X. Long, J. Q. Tan, S. Joty, and E. Hoque. Chartqa: A benchmark for question answering about charts with visual and logical reasoning. arXiv preprint arXiv:2203.10244, 2022.\n[25] A. Nassar, A. Marafioti, M. Omenetti, M. Lysak, N. Livathinos, C. Auer, L. Morin, R. T. de Lima, Y. Kim, A. S. Gurbuz, et al. Smoldocling: An ultra-compact vision-language model for end-to-end multi-modal document conversion. arXiv preprint arXiv:2503.11576, 2025.\n[26] OpenAI. Gpt-4 technical report, 2023.\n[27] L. Ouyang, Y. Qu, H. Zhou, J. Zhu, R. Zhang, Q. Lin, B. Wang, Z. Zhao, M. Jiang, X. Zhao, et al. Omnidocbench: Benchmarking diverse pdf document parsing with comprehensive annotations. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 24838-24848, 2025.\n[28] J. Poznanski, A. Rangapur, J. Borchardt, J. Dunkelberger, R. Huff, D. Lin, C. Wilhelm, K. Lo and L. Soldaini. olmocr: Unlocking trillions of tokens in pdfs with vision language models. arXiv preprint arXiv:2502.18443, 2025.\n[29] A. Radford, J.W.Kim,C.Hallacy,A.Ramesh,G.Goh,S.Agarwal,G.Sastry,A. Askell P.Mishkin,J.Clark,etal.Learning transferable visual models from natural language supervision.In International conference on machine learning, pages 8748-8763.PMLR, 2021.\n[30] Rednote. dots.ocr, 2025. URL https://github.com/rednote-hilab/dots.ocr.\n[31] C. Schuhmann, R. Vencu, R. Beaumont, R. Kaczmarczyk, C. Mullis, A. Katta, T. Coombes, J. Jitsev, and A. Komatsuzaki. Laion-400m: Open dataset of clip-filtered 400 million image-text pairs. arXiv preprint arXiv:2111.02114, 2021.\n[32] A. Singh, V. Natarajan, M. Shah, Y. Jiang, X. Chen, D. Batra, D. Parikh, and M. Rohrbach. Towards vqa models that can read. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 8317-8326, 2019.\n[33] T. Sun, C. Cui, Y. Du, and Y. Liu. Pp-doclayout: A unified document layout detection model to accelerate large-scale data construction. arXiv preprint arXiv:2503.17213, 2025.\n[34] B. Wang, C. Xu, X. Zhao, L. Ouyang, F. Wu, Z. Zhao, R. Xu, K. Liu, Y. Qu, F. Shang, et al. Mineru: An open-source solution for precise document content extraction. arXiv preprint arXiv:2409.18839, 2024.\n[35] P. Wang, S. Bai, S. Tan, S. Wang, Z. Fan, J. Bai, K. Chen, X. Liu, J. Wang, W. Ge, et al. Qwen2-vl: Enhancing vision-language model's perception of the world at any resolution. arXiv preprint arXiv:2409.12191, 2024.\n[36] H. Wei, L. Kong, J. Chen, L. Zhao, Z. Ge, J. Yang, J. Sun, C. Han, and X. Zhang. Vary: Scaling up the vision vocabulary for large vision-language model. In European Conference on Computer Vision, pages 408-424. Springer, 2024.\n[37] H. Wei, L. Kong, J. Chen, L. Zhao, Z. Ge, E. Yu, J. Sun, C. Han, and X. Zhang. Small language model meets with reinforced vision vocabulary. arXiv preprint arXiv:2401.12503, 2024.\n[38] H. Wei, C. Liu, J. Chen, J. Wang, L. Kong, Y. Xu, Z. Ge, L. Zhao, J. Sun, Y. Peng, et al. General ocr theory: Towards ocr-2.0 via a unified end-to-end model. arXiv preprint arXiv:2409.01704, 2024.\n[39] H. Wei, Y. Yin, Y. Li, J. Wang, L. Zhao, J. Sun, Z. Ge, X. Zhang, and D. Jiang. Slow perception: Let's perceive geometric figures step-by-step. arXiv preprint arXiv:2412.20631, 2024.\n[40] Z. Wu, X. Chen, Z. Pan, X. Liu, W. Liu, D. Dai, H. Gao, Y. Ma, C. Wu, B. Wang, et al. Deepseek-vl2: Mixture-of-experts vision-language models for advanced multimodal understanding. arXiv preprint arXiv:2412.10302, 2024.\n[41] W. Yu, Z. Yang, L. Li, J. Wang, K. Lin, Z. Liu, X. Wang, and L. Wang. Mm-vet: Evaluating large multimodal models for integrated capabilities. arXiv preprint arXiv:2308.02490, 2023.\n[42] J. Zhu, W. Wang, Z. Chen, Z. Liu, S. Ye, L. Gu, H. Tian, Y. Duan, W. Su, J. Shao, et al. Internvl3: Exploring advanced training and test-time recipes for open-source multimodal models. arXiv preprint arXiv:2504.10479, 2025.\n",
    "layout": [
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/fb8e9edb-054a-408b-91c2-1781e0092587_split_1_0001.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=G%2BPNdK5gDZ0YMLSKpHRnYS7EI5c%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                196,
                93,
                544,
                173
            ],
            "block_id": 1,
            "page_index": 1
        },
        {
            "block_content": "# DeepSeek-OCR: Contexts Optical Compression",
            "bbox": [
                339,
                311,
                1309,
                369
            ],
            "block_id": 2,
            "page_index": 1
        },
        {
            "block_content": "Haoran Wei, Yaofeng Sun, Yukun Li",
            "bbox": [
                577,
                442,
                1073,
                479
            ],
            "block_id": 3,
            "page_index": 1
        },
        {
            "block_content": "DeepSeek-AI",
            "bbox": [
                734,
                507,
                916,
                542
            ],
            "block_id": 4,
            "page_index": 1
        },
        {
            "block_content": "## Abstract",
            "bbox": [
                740,
                617,
                911,
                664
            ],
            "block_id": 5,
            "page_index": 1
        },
        {
            "block_content": "We present DeepSeek-OCR as an initial investigation into the feasibility of compressing long contexts via optical 2D mapping. DeepSeek-OCR consists of two components: DeepEncoder and DeepSeek3B-MoE-A570M as the decoder. Specifically, DeepEncoder serves as the core engine, designed to maintain low activations under high-resolution input while achieving high compression ratios to ensure an optimal and manageable number of vision tokens. Experiments show that when the number of text tokens is within 10 times that of vision tokens (i.e., a compression ratio $< 10\\times$ ), the model can achieve decoding (OCR) precision of $97\\%$. Even at a compression ratio of $20\\times$, the OCR accuracy still remains at about $60\\%$. This shows considerable promise for research areas such as historical long-context compression and memory forgetting mechanisms in LLMs. Beyond this, DeepSeek-OCR also demonstrates high practical value. On OmniDocBench, it surpasses GOT-OCR2.0 (256 tokens/page) using only 100 vision tokens, and outperforms MinerU2.0 (6000+ tokens per page on average) while utilizing fewer than 800 vision tokens. In production, DeepSeek-OCR can generate training data for LLMs/VLMs at a scale of $200k+$ pages per day (a single A100-40G). Codes and model weights are publicly accessible at http://github.com/deepseek-ai/DeepSeek-OCR.",
            "bbox": [
                186,
                720,
                1463,
                1323
            ],
            "block_id": 6,
            "page_index": 1
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/29cb864e-9870-4235-982d-dc239882a60c_split_1_0007.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=hY2oATLLeLPxBN1tC2ptBSBRLhE%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                219,
                1372,
                810,
                1847
            ],
            "block_id": 7,
            "page_index": 1
        },
        {
            "block_content": "(a) Compression on Fox benchmark",
            "bbox": [
                314,
                1866,
                721,
                1899
            ],
            "block_id": 8,
            "page_index": 1
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/deb2596c-368d-408d-a044-ad47d47e8160_split_1_0009.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=ASeIRDeZxhlEoM5Y488i8aVCILw%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                838,
                1361,
                1432,
                1847
            ],
            "block_id": 9,
            "page_index": 1
        },
        {
            "block_content": "(b) Performance on Omnidocbench",
            "bbox": [
                936,
                1866,
                1336,
                1899
            ],
            "block_id": 10,
            "page_index": 1
        },
        {
            "block_content": "Figure 1 | Figure (a) shows the compression ratio (number of text tokens in ground truth/number of vision tokens model used) testing on Fox [21] benchmark; Figure (b) shows performance comparisons on OmniDocBench [27]. DeepSeek-OCR can achieve state-of-the-art performance among end-to-end models enjoying the fewest vision tokens.",
            "bbox": [
                186,
                1936,
                1462,
                2091
            ],
            "block_id": 11,
            "page_index": 1
        },
        {
            "block_content": "## Contents",
            "bbox": [
                190,
                231,
                348,
                276
            ],
            "block_id": 12,
            "page_index": 2
        },
        {
            "block_content": "| Section                                                                 | Page |\n|-------------------------------------------------------------------------|------|\n| 1 Introduction                                                           | 3    |\n| 2 Related Works                                                          | 4    |\n| 2.1 Typical Vision Encoders in VLMs                                       | 4    |\n| 2.2 End-to-end OCR Models                                                 | 4    |\n| 3 Methodology                                                            | 5    |\n| 3.1 Architecture                                                         | 5    |\n| 3.2 DeepEncoder                                                          | 5    |\n| 3.2.1 Architecture of DeepEncoder                                         | 5    |\n| 3.2.2 Multiple resolution support                                        | 6    |\n| 3.3 The MoE Decoder                                                        | 7    |\n| 3.4 Data Engine                                                         | 7    |\n| 3.4.1 OCR 1.0 data                                                        | 7    |\n| 3.4.2 OCR 2.0 data                                                        | 8    |\n| 3.4.3 General vision data                                                | 9    |\n| 3.4.4 Text-only data                                                       | 9    |\n| 3.5 Training Pipelines                                                    | 9    |\n| 3.5.1 Training DeepEncoder                                                  | 10   |\n| 3.5.2 Training DeepSeek-OCR                                               | 10   |\n| 4 Evaluation                                                             | 10   |\n| 4.1 Vision-text Compression Study                                          | 10   |\n| 4.2 OCR Practical Performance                                             | 12   |\n| 4.3 Qualitative Study                                                     | 12   |\n| 4.3.1 Deep parsing                                                         | 12   |\n| 4.3.2 Multilingual recognition                                              | 16   |\n| 4.3.3 General vision understanding                                         | 17   |\n| 5 Discussion                                                             | 18   |\n| 6 Conclusion                                                             | 19   |",
            "bbox": [
                186,
                320,
                1465,
                1906
            ],
            "block_id": 13,
            "page_index": 2
        },
        {
            "block_content": "## 1. Introduction",
            "bbox": [
                190,
                236,
                453,
                273
            ],
            "block_id": 14,
            "page_index": 3
        },
        {
            "block_content": "Current Large Language Models (LLMs) face significant computational challenges when processing long textual content due to quadratic scaling with sequence length. We explore a potential solution: leveraging visual modality as an efficient compression medium for textual information. A single image containing document text can represent rich information using substantially fewer tokens than the equivalent digital text, suggesting that optical compression through vision tokens could achieve much higher compression ratios.",
            "bbox": [
                186,
                308,
                1465,
                537
            ],
            "block_id": 15,
            "page_index": 3
        },
        {
            "block_content": "This insight motivates us to reexamine vision-language models (VLMs) from an LLM-centric perspective, focusing on how vision encoders can enhance LLMs' efficiency in processing textual information rather than basic VQA [12, 16, 24, 32, 41] what humans excel at. OCR tasks, as an intermediate modality bridging vision and language, provide an ideal testbed for this vision-text compression paradigm, as they establish a natural compression-decompression mapping between visual and textual representations while offering quantitative evaluation metrics.",
            "bbox": [
                185,
                554,
                1463,
                781
            ],
            "block_id": 16,
            "page_index": 3
        },
        {
            "block_content": "Accordingly, we present DeepSeek-OCR, a VLM designed as a preliminary proof-of-concept for efficient vision-text compression. Our work makes three primary contributions:",
            "bbox": [
                188,
                797,
                1462,
                874
            ],
            "block_id": 17,
            "page_index": 3
        },
        {
            "block_content": "First, we provide comprehensive quantitative analysis of vision-text token compression ratios. Our method achieves $96\\% +$ OCR decoding precision at 9-10x text compression, $\\sim 90\\%$ at 10-12x compression, and $\\sim 60\\%$ at 20x compression on Fox [21] benchmarks featuring diverse document layouts (with actual accuracy being even higher when accounting for formatting differences between output and ground truth), as shown in Figure 1(a). The results demonstrate that compact language models can effectively learn to decode compressed visual representations, suggesting that larger LLMs could readily acquire similar capabilities through appropriate pretraining design.",
            "bbox": [
                186,
                893,
                1463,
                1197
            ],
            "block_id": 18,
            "page_index": 3
        },
        {
            "block_content": "Second, we introduce DeepEncoder, a novel architecture that maintains low activation memory and minimal vision tokens even with high-resolution inputs. It serially connects window attention and global attention encoder components through a $1 6 \\times$ convolutional compressor. This design ensures that the window attention component processes a large number of vision tokens, while the compressor reduces vision tokens before they enter the dense global attention component, achieving effective memory and token compression.",
            "bbox": [
                186,
                1211,
                1467,
                1440
            ],
            "block_id": 19,
            "page_index": 3
        },
        {
            "block_content": "Third, we develop DeepSeek-OCR based on DeepEncoder and DeepSeek3B-MoE [19, 20]. As shown in Figure 1(b), it achieves state-of-the-art performance within end-to-end models on OmniDocBench while using the fewest vision tokens. Additionally, we equip the model with capabilities for parsing charts, chemical formulas, simple geometric figures, and natural images to enhance its practical utility further. In production, DeepSeek-OCR can generate 33 million pages of data per day for LLMs or VLMs using 20 nodes (each with 8 A100-40G GPUs).",
            "bbox": [
                186,
                1457,
                1463,
                1686
            ],
            "block_id": 20,
            "page_index": 3
        },
        {
            "block_content": "In summary, this work presents a preliminary exploration of using visual modality as an efficient compression medium for textual information processing in LLMs. Through DeepSeek- OCR, we demonstrate that vision-text compression can achieve significant token reduction $(7 - 20\\times)$ for different historical context stages, offering a promising direction for addressing long-context challenges in large language models. Our quantitative analysis provides empirical guidelines for VLM token allocation optimization, while the proposed DeepEncoder architecture showcases practical feasibility with real-world deployment capabilities. Although focused on OCR as a proof-of-concept, this paradigm opens new possibilities for rethinking how vision and language modalities can be synergistically combined to enhance computational efficiency in large-scale text processing and agent systems.",
            "bbox": [
                186,
                1702,
                1465,
                2081
            ],
            "block_id": 21,
            "page_index": 3
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/9c92c808-b74f-40c7-a300-72a89509bb7d_split_4_0022.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=BHB9SvJy5jh92xQZzVtnzOFpYA0%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                211,
                233,
                1430,
                526
            ],
            "block_id": 22,
            "page_index": 4
        },
        {
            "block_content": "Figure 2 | Typical vision encoders in popular VLMs. Here are three types of encoders commonly used in current open-source VLMs, all of which suffer from their respective deficiencies.",
            "bbox": [
                188,
                552,
                1462,
                629
            ],
            "block_id": 23,
            "page_index": 4
        },
        {
            "block_content": "## 2. Related Works",
            "bbox": [
                190,
                685,
                486,
                722
            ],
            "block_id": 24,
            "page_index": 4
        },
        {
            "block_content": "## 2.1. Typical Vision Encoders in VLMs",
            "bbox": [
                188,
                760,
                724,
                797
            ],
            "block_id": 25,
            "page_index": 4
        },
        {
            "block_content": "Current open-source VLMs employ three main types of vision encoders, as illustrated in Figure 2. The first type is a dual-tower architecture represented by Vary [36], which utilizes parallel SAM [17] encoder to increase visual vocabulary parameters for high-resolution image processing. While offering controllable parameters and activation memory, this approach suffers from significant drawbacks: it requires dual image preprocessing that complicates deployment and makes encoder pipeline parallelism challenging during training. The second type is tile-based method exemplified by InternVL2.0 [8], which processes images by dividing them into small tiles for parallel computation, reducing activation memory under high-resolution settings. Although capable of handling extremely high resolutions, this approach has notable limitations due to its typically low native encoder resolution (below $512\\times 512$), causing large images to be excessively fragmented and resulting in numerous vision tokens. The third type is adaptive resolution encoding represented by Qwen2-VL [35], which adopts the NaViT [10] paradigm to directly process full images through patch-based segmentation without tile parallelization. While this encoder can handle diverse resolutions flexibly, it faces substantial challenges with large images due to massive activation memory consumption that can cause GPU memory overflow, and sequence packing requires extremely long sequence lengths during training. Long vision tokens will slow down both prefill and generation phases of inference.",
            "bbox": [
                185,
                823,
                1465,
                1466
            ],
            "block_id": 26,
            "page_index": 4
        },
        {
            "block_content": "## 2.2. End-to-end OCR Models",
            "bbox": [
                188,
                1518,
                605,
                1553
            ],
            "block_id": 27,
            "page_index": 4
        },
        {
            "block_content": "OCR, particularly document parsing task, has been a highly active topic in the image-to-text domain. With the advancement of VLMs, a large number of end-to-end OCR models have emerged, fundamentally transforming the traditional pipeline architecture (which required separate detection and recognition expert models) by simplifying OCR systems. Nougat [6] first employs end-to-end framework for academic paper OCR on arXiv, demonstrating the potential of models in handling dense perception tasks. GOT-OCR2.0 [38] expands the scope of OCR2.0 to include more synthetic image parsing tasks and designs an OCR model with performance-efficiency trade-offs, further highlighting the potential of end-to-end OCR researches. Additionally, general vision models such as Qwen-VL series [35], InternVL series [8], and many their derivatives continuously enhance their document OCR capabilities to explore dense visual perception boundaries. However, a crucial research question that current models have not addressed is: for a document containing 1000 words, how many vision tokens are at least needed for decoding? This question holds significant importance for research in the principle that \"a picture is worth a thousand words.\"",
            "bbox": [
                185,
                1578,
                1465,
                2109
            ],
            "block_id": 28,
            "page_index": 4
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/cfc28b7b-f2c2-4027-b8a7-451a034e9925_split_5_0029.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688350&Signature=B%2BVrTF1ZkkSq9GSDA34t1WKYp%2Bs%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                200,
                245,
                1440,
                580
            ],
            "block_id": 29,
            "page_index": 5
        },
        {
            "block_content": "Figure 3 | The architecture of DeepSeek-OCR. DeepSeek-OCR consists of a DeepEncoder and a DeepSeek-3B-MoE decoder. DeepEncoder is the core of DeepSeek-OCR, comprising three components: a SAM [17] for perception dominated by window attention, a CLIP [29] for knowledge with dense global attention, and a $ 16\\times $ token compressor that bridges between them.",
            "bbox": [
                186,
                612,
                1462,
                769
            ],
            "block_id": 30,
            "page_index": 5
        },
        {
            "block_content": "## 3. Methodology",
            "bbox": [
                188,
                820,
                468,
                863
            ],
            "block_id": 31,
            "page_index": 5
        },
        {
            "block_content": "## 3.1. Architecture",
            "bbox": [
                190,
                898,
                433,
                933
            ],
            "block_id": 32,
            "page_index": 5
        },
        {
            "block_content": "As shown in Figure 3, DeepSeek-OCR enjoys a unified end-to-end VLM architecture consisting of an encoder and a decoder. The encoder (namely DeepEncoder) is responsible for extracting image features and tokenizing as well as compressing visual representations. The decoder is used for generating the required result based on image tokens and prompts. DeepEncoder is approximately 380M in parameters, mainly composed of an 80M SAM-base [17] and a 300M CLIP-large [29] connected in series. The decoder adopts a 3B MoE [19, 20] architecture with 570M activated parameters. In the following paragraphs, we will delve into the model components, data engineering, and training skills.",
            "bbox": [
                186,
                958,
                1465,
                1265
            ],
            "block_id": 33,
            "page_index": 5
        },
        {
            "block_content": "## 3.2. DeepEncoder",
            "bbox": [
                190,
                1314,
                449,
                1351
            ],
            "block_id": 34,
            "page_index": 5
        },
        {
            "block_content": "To explore the feasibility of contexts optical compression, we need a vision encoder with the following features: 1.Capable of processing high resolutions; 2.Low activation at high resolutions; 3.Few vision tokens; 4.Support for multiple resolution inputs; 5. Moderate parameter count. However, as described in the Section 2.1, current open-source encoders cannot fully satisfy all these conditions. Therefore, we design a novel vision encoder ourselves, named DeepEncoder.",
            "bbox": [
                185,
                1375,
                1465,
                1569
            ],
            "block_id": 35,
            "page_index": 5
        },
        {
            "block_content": "## 3.2.1. Architecture of DeepEncoder",
            "bbox": [
                188,
                1611,
                669,
                1648
            ],
            "block_id": 36,
            "page_index": 5
        },
        {
            "block_content": "DeepEncoder mainly consists of two components: a visual perception feature extraction component dominated by window attention, and a visual knowledge feature extraction component with dense global attention. To benefit from the pretraining gains of previous works, we use SAM-base (patch-size 16) and CLIP-large as the main architectures for the two components respectively. For CLIP, we remove the first patch embedding layer since its input is no longer images but output tokens from the previous pipeline. Between the two components, we borrow from Vary [36] and use a 2-layer convolutional module to perform $16\\times$ downsampling of vision tokens. Each convolutional layer has a kernel size of 3, stride of 2, padding of 1, and channels increase from 256 to 1024. Assuming we input a $1024\\times 1024$ image, the DeepEncoder will segment it into $1024 / 16 \\times 1024 / 16 = 4096$ patch tokens. Since the first half of encoder is dominated by window attention and only 80M, the activation is acceptable. Before entering global attention,",
            "bbox": [
                185,
                1674,
                1467,
                2093
            ],
            "block_id": 37,
            "page_index": 5
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/01a3defc-069e-4352-8e2e-9308002dd4c7_split_6_0038.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=Odi00erC0NWwTwF%2FfyVMQ95Sb%2BA%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                213,
                238,
                1430,
                605
            ],
            "block_id": 38,
            "page_index": 6
        },
        {
            "block_content": "Figure 4 | To test model performance under different compression ratios (requiring different numbers of vision tokens) and enhance the practicality of DeepSeek-OCR, we configure it with multiple resolution modes.",
            "bbox": [
                186,
                631,
                1460,
                746
            ],
            "block_id": 39,
            "page_index": 6
        },
        {
            "block_content": "the 4096 tokens go through the compression module and the token count becomes $ 4 0 9 6 / 1 6 = 2 5 6 $ thus making the overall activation memory controllable.",
            "bbox": [
                188,
                804,
                1462,
                881
            ],
            "block_id": 40,
            "page_index": 6
        },
        {
            "block_content": "Table 1 | Multi resolution support of DeepEncoder. For both research and application purposes, we design DeepEncoder with diverse native resolution and dynamic resolution modes.",
            "bbox": [
                186,
                907,
                1463,
                987
            ],
            "block_id": 41,
            "page_index": 6
        },
        {
            "block_content": "<table><thead><tr><th rowspan=\"2\">Mode</th><th colspan=\"4\">Native Resolution</th><th colspan=\"2\">Dynamic Resolution</th></tr><tr><th>Tiny</th><th>Small</th><th>Base</th><th>Large</th><th>Gundam</th><th>Gundam-M</th></tr></thead><tbody><tr><td>Resolution</td><td>512</td><td>640</td><td>1024</td><td>1280</td><td>640+1024</td><td>1024+1280</td></tr><tr><td>Tokens</td><td>64</td><td>100</td><td>256</td><td>400</td><td>n×100+256</td><td>n×256+400</td></tr><tr><td>Process</td><td>resize</td><td>resize</td><td>padding</td><td>padding</td><td>resize + padding</td><td>resize + padding</td></tr></tbody></table>",
            "bbox": [
                277,
                1010,
                1369,
                1246
            ],
            "block_id": 42,
            "page_index": 6
        },
        {
            "block_content": "## 3.2.2.Multiple resolution support",
            "bbox": [
                190,
                1312,
                661,
                1349
            ],
            "block_id": 43,
            "page_index": 6
        },
        {
            "block_content": "Suppose we have an image with 1000 optical characters and we want to test how many vision tokens are needed for decoding. This requires the model to support a variable number of vision tokens. That is to say the DeepEncoder needs to support multiple resolutions.",
            "bbox": [
                186,
                1372,
                1462,
                1489
            ],
            "block_id": 44,
            "page_index": 6
        },
        {
            "block_content": "We meet the requirement aforementioned through dynamic interpolation of positional encodings, and design several resolution modes for simultaneous model training to achieve the capability of a single DeepSeek-OCR model supporting multiple resolutions. As shown in Figure 4, DeepEncoder mainly supports two major input modes: native resolution and dynamic resolution. Each of them contains multiple sub-modes.",
            "bbox": [
                186,
                1506,
                1463,
                1698
            ],
            "block_id": 45,
            "page_index": 6
        },
        {
            "block_content": "Native resolution supports four sub-modes: Tiny, Small, Base, and Large, with corresponding resolutions and token counts of $512 \\times 512$ (64), $640 \\times 640$ (100), $1024 \\times 1024$ (256), and $1280 \\times 1280$ (400) respectively. Since Tiny and Small modes have relatively small resolutions, to avoid wasting vision tokens, images are processed by directly resizing the original shape. For Base and Large modes, in order to preserve the original image aspect ratio, images are padded to the corresponding size. After padding, the number of valid vision tokens is less than the actual number of vision tokens, with the calculation formula being:",
            "bbox": [
                185,
                1712,
                1463,
                1978
            ],
            "block_id": 46,
            "page_index": 6
        },
        {
            "block_content": "$$\nN _ {\\text {v a l i d}} = \\lceil N _ {\\text {a c t u a l}} \\times [ 1 - ((\\max (w, h) - \\min (w, h)) / (\\max (w, h))) ] \\rceil\n$$",
            "bbox": [
                411,
                2004,
                1235,
                2046
            ],
            "block_id": 47,
            "page_index": 6
        },
        {
            "block_content": "where $ w $ and $ h $ represent the width and height of the original input image.",
            "bbox": [
                186,
                2072,
                1190,
                2114
            ],
            "block_id": 48,
            "page_index": 6
        },
        {
            "block_content": "Dynamic resolution can be composed of two native resolutions. For example, Gundam mode consists of $n \\times 640 \\times 640$ tiles (local views) and a $1024 \\times 1024$ global view. The tiling method following InternVL2.0 [8]. Supporting dynamic resolution is mainly for application considerations, especially for ultra-high-resolution inputs (such as newspaper images). Tiling is a form of secondary window attention that can effectively reduce activation memory further. It's worth noting that due to our relatively large native resolutions, images won't be fragmented too much under dynamic resolution (the number of tiles is controlled within the range of 2 to 9). The vision token number output by the DeepEncoder under Gundam mode is: $n \\times 100 + 256$, where $n$ is the number of tiles. For images with both width and height smaller than 640, $n$ is set to 0, i.e., Gundam mode will degrade to Base mode.",
            "bbox": [
                186,
                238,
                1465,
                617
            ],
            "block_id": 49,
            "page_index": 7
        },
        {
            "block_content": "Gundam mode is trained together with the four native resolution modes to achieve the goal of one model supporting multiple resolutions. Note that Gundam-master mode $ ( 1024 \\times 1024 $ local views+1280x1280 global view) is obtained through continued training on a trained DeepSeek- OCR model. This is mainly for load balancing, as Gundam-master's resolution is too large and training it together would slow down the overall training speed.",
            "bbox": [
                186,
                633,
                1465,
                823
            ],
            "block_id": 50,
            "page_index": 7
        },
        {
            "block_content": "## 3.3. The MoE Decoder",
            "bbox": [
                190,
                874,
                514,
                909
            ],
            "block_id": 51,
            "page_index": 7
        },
        {
            "block_content": "Our decoder uses the DeepSeekMoE [19, 20], specifically DeepSeek-3B-MoE. During inference, the model activates 6 out of 64 routed experts and 2 shared experts, with about 570M activated parameters. The 3B DeepSeekMoE is very suitable for domain-centric (OCR for us) VLM research, as it obtains the expressive capability of a 3B model while enjoying the inference efficiency of a 500M small model.",
            "bbox": [
                186,
                935,
                1463,
                1127
            ],
            "block_id": 52,
            "page_index": 7
        },
        {
            "block_content": "The decoder reconstructs the original text representation from the compressed latent vision tokens of DeepEncoder as:",
            "bbox": [
                188,
                1143,
                1458,
                1220
            ],
            "block_id": 53,
            "page_index": 7
        },
        {
            "block_content": "$$\nf _ {\\mathrm {d e c}}: \\mathbb {R} ^ {n \\times d _ {\\text {l a t e n t}}} \\rightarrow \\mathbb {R} ^ {N \\times d _ {\\text {t e x t}}}; \\quad \\hat {\\mathbf {X}} = f _ {\\mathrm {d e c}} (\\mathbf {Z}) \\quad \\text {w h e r e} n \\leq N\n$$",
            "bbox": [
                459,
                1246,
                1187,
                1288
            ],
            "block_id": 54,
            "page_index": 7
        },
        {
            "block_content": "where $ \\mathbf{Z} \\in \\mathbb{R}^{n\\times d_{\\mathrm{latent}}} $ are the compressed latent(vision) tokens from DeepEncoder and $ \\hat{\\mathbf{X}} \\in \\mathbb{R}^{N\\times d_{\\mathrm{text}}} $ is the reconstructed text representation. The function $ f_{\\mathrm{dec}} $ represents a non-linear mapping that can be effectively learned by compact language models through OCR-style training. It is reasonable to conjecture that LLMs, through specialized pretraining optimization, would demonstrate more natural integration of such capabilities.",
            "bbox": [
                186,
                1316,
                1462,
                1508
            ],
            "block_id": 55,
            "page_index": 7
        },
        {
            "block_content": "## 3.4. Data Engine",
            "bbox": [
                188,
                1562,
                433,
                1599
            ],
            "block_id": 56,
            "page_index": 7
        },
        {
            "block_content": "We constructe complex and diverse training data for DeepSeek-OCR, including OCR 1.0 data, which mainly consists of traditional OCR tasks such as scene image OCR and document OCR; OCR 2.0 data, which mainly includes parsing tasks for complex artificial images, such as common charts, chemical formulas, and plane geometry parsing data; General vision data, which is mainly used to inject certain general image understanding capabilities into DeepSeek-OCR and preserve the general vision interface.",
            "bbox": [
                185,
                1623,
                1467,
                1850
            ],
            "block_id": 57,
            "page_index": 7
        },
        {
            "block_content": "## 3.4.1.OCR 1.0 data",
            "bbox": [
                190,
                1894,
                468,
                1932
            ],
            "block_id": 58,
            "page_index": 7
        },
        {
            "block_content": "Document data is the top priority for DeepSeek-OCR. We collect 30M pages of diverse PDF data covering about 100 languages from the Internet, with Chinese and English accounting for approximately 25M and other languages accounting for 5M. For this data, we create two types of ground truth: coarse annotations and fine annotations. Coarse annotations are extracted",
            "bbox": [
                186,
                1957,
                1463,
                2109
            ],
            "block_id": 59,
            "page_index": 7
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/e2463129-a237-46b3-bbb6-87e68ced04e9_split_8_0060.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=wQMCMXsngpGysWd6E6RM2vmDhSY%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                219,
                238,
                1434,
                1005
            ],
            "block_id": 60,
            "page_index": 8
        },
        {
            "block_content": "(a) Ground truth image",
            "bbox": [
                382,
                991,
                654,
                1024
            ],
            "block_id": 61,
            "page_index": 8
        },
        {
            "block_content": "(b) Fine annotations with layouts",
            "bbox": [
                942,
                991,
                1323,
                1024
            ],
            "block_id": 62,
            "page_index": 8
        },
        {
            "block_content": "Figure 5 | OCR 1.0 fine annotations display. We format the ground truth into an interleaved layout and text format, where each paragraph of text is preceded by the coordinates and label of it in the original image. All coordinates are normalized into 1000 bins.",
            "bbox": [
                186,
                1061,
                1462,
                1181
            ],
            "block_id": 63,
            "page_index": 8
        },
        {
            "block_content": "directly from the full dataset using fitz, aimed at teaching the model to recognize optical text, especially in minority languages. Fine annotations include 2M pages each for Chinese and English, labeled using advanced layout models (such as PP-DocLayout [33]) and OCR models (such as MinuerU [34] and GOT-OCR2.0 [38]) to construct detection and recognition interleaved data. For minority languages, in the detection part, we find that the layout model enjoys certain generalization capabilities. In the recognition part, we use fitz to create small patch data to train a GOT-OCR2.0, then use the trained model to label small patches after layout processing, employing a model flywheel to create 600K data samples. During the training of DeepSeek-OCR, coarse labels and fine labels are distinguished using different prompts. The ground truth for fine annotation image-text pairs can be seen in Figure 5. We also collect 3M Word data, constructing high-quality image-text pairs without layout by directly extracting content. This data mainly brings benefits to formulas and HTML-formatted tables. Additionally, we select some open-source data [28, 37] as supplements.",
            "bbox": [
                186,
                1234,
                1465,
                1730
            ],
            "block_id": 64,
            "page_index": 8
        },
        {
            "block_content": "For natural scene OCR, our model mainly supports Chinese and English. The image data sources come from LAION [31] and Wukong [13], labeled using PaddleOCR [9], with 10M data samples each for Chinese and English. Like document OCR, natural scene OCR can also control whether to output detection boxes through prompts.",
            "bbox": [
                186,
                1742,
                1462,
                1899
            ],
            "block_id": 65,
            "page_index": 8
        },
        {
            "block_content": "## 3.4.2.OCR 2.0 data",
            "bbox": [
                188,
                1941,
                469,
                1978
            ],
            "block_id": 66,
            "page_index": 8
        },
        {
            "block_content": "Following GOT-OCR2.0 [38], we refer to chart, chemical formula, and plane geometry parsing data as OCR 2.0 data. For chart data, following OneChart [7], we use pyecharts and matplotlib",
            "bbox": [
                186,
                2002,
                1462,
                2081
            ],
            "block_id": 67,
            "page_index": 8
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/cc826af0-e3c0-4383-a3a3-54e686b6d4f8_split_9_0068.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=hUcd%2B1r9VEZdMdI8for9nyKRHMs%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                206,
                271,
                815,
                472
            ],
            "block_id": 68,
            "page_index": 9
        },
        {
            "block_content": "(a) Image-text ground truth of chart",
            "bbox": [
                307,
                493,
                717,
                528
            ],
            "block_id": 69,
            "page_index": 9
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/15aeac22-0e29-4d2c-b60c-910dbb27dee1_split_9_0070.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=zvU9NKezNNRZPTlLP4U15S8PsKk%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                831,
                245,
                1442,
                477
            ],
            "block_id": 70,
            "page_index": 9
        },
        {
            "block_content": "(b) Image-text ground truth of geometry",
            "bbox": [
                909,
                493,
                1367,
                530
            ],
            "block_id": 71,
            "page_index": 9
        },
        {
            "block_content": "Figure 6 | For charts, we do not use OneChart's [7] dictionary format, but instead use HTML table format as labels, which can save a certain amount of tokens. For plane geometry, we convert the ground truth to dictionary format, where the dictionary contains keys such as line segments, endpoint coordinates, line segment types, etc., for better readability. Each line segment is encoded using the Slow Perception [39] manner.",
            "bbox": [
                188,
                563,
                1462,
                757
            ],
            "block_id": 72,
            "page_index": 9
        },
        {
            "block_content": "to render 10M images, mainly including commonly used line, bar, pie, and composite charts. We define chart parsing as image-to-HTML-table conversion task, as shown in Figure 6(a). For chemical formulas, we utilize SMILES format from PubChem as the data source and render them into images using RDKit, constructing 5M image-text pairs. For plane geometry images, we follow Slow Perception [39] for generation. Specifically, we use perception-ruler size as 4 to model each line segment. To increase the diversity of rendered data, we introduce geometric translation-invariant data augmentation, where the same geometric image is translated in the original image, corresponding to the same ground truth drawn at the centered position in the coordinate system. Based on this, we construct a total of 1M plane geometry parsing data, as illustrated in Figure 6(b).",
            "bbox": [
                185,
                811,
                1465,
                1192
            ],
            "block_id": 73,
            "page_index": 9
        },
        {
            "block_content": "## 3.4.3. General vision data",
            "bbox": [
                188,
                1234,
                552,
                1274
            ],
            "block_id": 74,
            "page_index": 9
        },
        {
            "block_content": "DeepEncoder can benefit from CLIP's pretraining gains and has sufficient parameters to incorporate general visual knowledge. Therefore, we also prepare some corresponding data for DeepSeek-OCR.Following DeepSeek-VL2 [40],we generate relevant data for tasks such as caption, detection, and grounding.Note that DeepSeek-OCR is not a general VLM model,and this portion of data accounts for only $ 20\\% $ of the total data.We introduce such type of data mainly to preserve the general vision interface, so that researchers interested in our model and general vision task can conveniently advance their work in the future.",
            "bbox": [
                185,
                1298,
                1465,
                1564
            ],
            "block_id": 75,
            "page_index": 9
        },
        {
            "block_content": "## 3.4.4.Text-only data",
            "bbox": [
                188,
                1609,
                482,
                1646
            ],
            "block_id": 76,
            "page_index": 9
        },
        {
            "block_content": "To ensure the model's language capabilities, we introduced 10% of in-house text-only pretrain data, with all data processed to a length of 8192 tokens, which is also the sequence length for DeepSeek-OCR. In summary, when training DeepSeek-OCR, OCR data accounts for 70%, general vision data accounts for 20%, and text-only data accounts for 10%.",
            "bbox": [
                186,
                1670,
                1463,
                1824
            ],
            "block_id": 77,
            "page_index": 9
        },
        {
            "block_content": "## 3.5. Training Pipelines",
            "bbox": [
                188,
                1875,
                517,
                1915
            ],
            "block_id": 78,
            "page_index": 9
        },
        {
            "block_content": "Our training pipeline is very simple and consists mainly of two stages: a).Training DeepEncoder independently; b).Training the DeepSeek-OCR. Note that the Gundam-master mode is obtained by continuing training on a pre-trained DeepSeek-OCR model with 6M sampled data. Since the training protocol is identical to other modes, we omit the detailed description hereafter.",
            "bbox": [
                185,
                1936,
                1463,
                2091
            ],
            "block_id": 79,
            "page_index": 9
        },
        {
            "block_content": "## 3.5.1. Training DeepEncoder",
            "bbox": [
                190,
                238,
                582,
                276
            ],
            "block_id": 80,
            "page_index": 10
        },
        {
            "block_content": "Following Vary [36], we utilize a compact language model [15] and use the next token prediction framework to train DeepEncoder. In this stage, we use all OCR 1.0 and 2.0 data aforementioned, as well as 100M general data sampled from the LAION [31] dataset. All data is trained for 2 epochs with a batch size of 1280, using the AdamW [23] optimizer with cosine annealing scheduler [22] and a learning rate of 5e-5. The training sequence length is 4096.",
            "bbox": [
                186,
                299,
                1465,
                491
            ],
            "block_id": 81,
            "page_index": 10
        },
        {
            "block_content": "## 3.5.2. Training DeepSeek-OCR",
            "bbox": [
                188,
                530,
                613,
                570
            ],
            "block_id": 82,
            "page_index": 10
        },
        {
            "block_content": "After DeepEncoder is ready, we use data mentioned in Section 3.4 to train the DeepSeek-OCR with the entire training process conducted on the HAI-LLM [14] platform. The entire model uses pipeline parallelism (PP) and is divided into 4 parts, with DeepEncoder taking two parts and the decoder taking two parts. For DeepEncoder, we treat SAM and the compressor as the vision tokenizer, place them in PP0 and freeze their parameters, while treating the CLIP part as input embedding layer and place it in PP1 with unfrozen weights for training. For the language model part, since DeepSeek3B-MoE has 12 layers, we place 6 layers each on PP2 and PP3. We use 20 nodes (each with 8 A100-40G GPUs) for training, with a data parallelism (DP) of 40 and a global batch size of 640. We use the AdamW optimizer with a step-based scheduler and an initial learning rate of 3e-5. For text-only data, the training speed is 90B tokens/day, while for multimodal data, the training speed is 70B tokens/day.",
            "bbox": [
                185,
                594,
                1463,
                1012
            ],
            "block_id": 83,
            "page_index": 10
        },
        {
            "block_content": "Table 2 | We test DeepSeek-OCR's vision-text compression ratio using all English documents with 600-1300 tokens from the Fox [21] benchmarks. Text tokens represent the number of tokens after tokenizing the ground truth text using DeepSeek-OCR's tokenizer. Vision Tokens=64 or 100 respectively represent the number of vision tokens output by DeepEncoder after resizing input images to $512\\times 512$ and $640\\times 640$.",
            "bbox": [
                186,
                1036,
                1462,
                1227
            ],
            "block_id": 84,
            "page_index": 10
        },
        {
            "block_content": "<table><thead><tr><th rowspan=\"2\">Text Tokens</th><th colspan=\"2\">Vision Tokens =64</th><th colspan=\"2\">Vision Tokens=100</th><th rowspan=\"2\">Pages</th></tr><tr><th>Precision</th><th>Compression</th><th>Precision</th><th>Compression</th></tr></thead><tbody><tr><td>600-700</td><td>96.5%</td><td>10.5×</td><td>98.5%</td><td>6.7×</td><td>7</td></tr><tr><td>700-800</td><td>93.8%</td><td>11.8×</td><td>97.3%</td><td>7.5×</td><td>28</td></tr><tr><td>800-900</td><td>83.8%</td><td>13.2×</td><td>96.8%</td><td>8.5×</td><td>28</td></tr><tr><td>900-1000</td><td>85.9%</td><td>15.1×</td><td>96.8%</td><td>9.7×</td><td>14</td></tr><tr><td>1000-1100</td><td>79.3%</td><td>16.5×</td><td>91.5%</td><td>10.6×</td><td>11</td></tr><tr><td>1100-1200</td><td>76.4%</td><td>17.7×</td><td>89.8%</td><td>11.3×</td><td>8</td></tr><tr><td>1200-1300</td><td>59.1%</td><td>19.7×</td><td>87.1%</td><td>12.6×</td><td>4</td></tr></tbody></table>",
            "bbox": [
                355,
                1251,
                1295,
                1639
            ],
            "block_id": 85,
            "page_index": 10
        },
        {
            "block_content": "## 4. Evaluation",
            "bbox": [
                190,
                1709,
                423,
                1747
            ],
            "block_id": 86,
            "page_index": 10
        },
        {
            "block_content": "## 4.1. Vision-text Compression Study",
            "bbox": [
                188,
                1786,
                693,
                1824
            ],
            "block_id": 87,
            "page_index": 10
        },
        {
            "block_content": "We select Fox [21] benchmarks to verify DeepSeek-OCR's compression-decompression capability for text-rich documents, in order to preliminarily explore the feasibility and boundaries of contexts optical compression. We use the English document portion of Fox, tokenize the ground truth text with DeepSeek-OCR's tokenizer (vocabulary size of approximately 129k), and select documents with 600-1300 tokens for testing, which happens to be 100 pages. Since the number of text tokens is not large, we only need to test performance in Tiny and Small modes, where Tiny mode corresponds to 64 tokens and Small mode corresponds to 100 tokens. We use the prompt",
            "bbox": [
                185,
                1847,
                1465,
                2114
            ],
            "block_id": 88,
            "page_index": 10
        },
        {
            "block_content": "Table 3 | We use OmniDocBench [27] to test the performance of DeepSeek-OCR on real document parsing tasks. All metrics in the table are edit distances, where smaller values indicate better performance. \"Tokens\" represents the average number of vision tokens used per page, and \"†200dpi\" means using fitz to interpolate the original image to 200dpi. For the DeepSeek-OCR model, the values in parentheses in the \"Tokens\" column represent valid vision tokens, calculated according to Equation 1.",
            "bbox": [
                186,
                233,
                1462,
                463
            ],
            "block_id": 89,
            "page_index": 11
        },
        {
            "block_content": "<table><thead><tr><th rowspan=\"2\">Model</th><th rowspan=\"2\">Tokens</th><th colspan=\"5\">English</th><th colspan=\"5\">Chinese</th></tr><tr><th>overall</th><th>text</th><th>formula</th><th>table</th><th>order</th><th>overall</th><th>text</th><th>formula</th><th>table</th><th>order</th></tr></thead><tbody><tr><td colspan=\"13\"><strong>Pipline Models</strong></td></tr><tr><td>Dolphin [11]</td><td>-</td><td>0.356</td><td>0.352</td><td>0.465</td><td>0.258</td><td>0.35</td><td>0.44</td><td>0.44</td><td>0.604</td><td>0.367</td><td>0.351</td></tr><tr><td>Marker [1]</td><td>-</td><td>0.296</td><td>0.085</td><td>0.374</td><td>0.609</td><td>0.116</td><td>0.497</td><td>0.293</td><td>0.688</td><td>0.678</td><td>0.329</td></tr><tr><td>Mathpix [2]</td><td>-</td><td>0.191</td><td>0.105</td><td>0.306</td><td>0.243</td><td>0.108</td><td>0.364</td><td>0.381</td><td>0.454</td><td>0.32</td><td>0.30</td></tr><tr><td>MinerU-2.1.1 [34]</td><td>-</td><td>0.162</td><td>0.072</td><td>0.313</td><td>0.166</td><td>0.097</td><td>0.244</td><td>0.111</td><td>0.581</td><td>0.15</td><td>0.136</td></tr><tr><td>MonkeyOCR-1.2B [18]</td><td>-</td><td>0.154</td><td>0.062</td><td>0.295</td><td>0.164</td><td>0.094</td><td>0.263</td><td>0.179</td><td>0.464</td><td>0.168</td><td>0.243</td></tr><tr><td>PPstructure-v3 [9]</td><td>-</td><td>0.152</td><td>0.073</td><td>0.295</td><td>0.162</td><td>0.077</td><td>0.223</td><td>0.136</td><td>0.535</td><td>0.111</td><td>0.11</td></tr><tr><td colspan=\"13\"><strong>End-to-end Models</strong></td></tr><tr><td>Nougat [6]</td><td>2352</td><td>0.452</td><td>0.365</td><td>0.488</td><td>0.572</td><td>0.382</td><td>0.973</td><td>0.998</td><td>0.941</td><td>1.00</td><td>0.954</td></tr><tr><td>SmolDocling [25]</td><td>392</td><td>0.493</td><td>0.262</td><td>0.753</td><td>0.729</td><td>0.227</td><td>0.816</td><td>0.838</td><td>0.997</td><td>0.907</td><td>0.522</td></tr><tr><td>InternVL2-76B [8]</td><td>6790</td><td>0.44</td><td>0.353</td><td>0.543</td><td>0.547</td><td>0.317</td><td>0.443</td><td>0.29</td><td>0.701</td><td>0.555</td><td>0.228</td></tr><tr><td>Qwen2.5-VL-7B [5]</td><td>3949</td><td>0.316</td><td>0.151</td><td>0.376</td><td>0.598</td><td>0.138</td><td>0.399</td><td>0.243</td><td>0.5</td><td>0.627</td><td>0.226</td></tr><tr><td>OLMOCR [28]</td><td>3949</td><td>0.326</td><td>0.097</td><td>0.455</td><td>0.608</td><td>0.145</td><td>0.469</td><td>0.293</td><td>0.655</td><td>0.652</td><td>0.277</td></tr><tr><td>GOT-OCR2.0 [38]</td><td>256</td><td>0.287</td><td>0.189</td><td>0.360</td><td>0.459</td><td>0.141</td><td>0.411</td><td>0.315</td><td>0.528</td><td>0.52</td><td>0.28</td></tr><tr><td>OCRFlux-3B [3]</td><td>3949</td><td>0.238</td><td>0.112</td><td>0.447</td><td>0.269</td><td>0.126</td><td>0.349</td><td>0.256</td><td>0.716</td><td>0.162</td><td>0.263</td></tr><tr><td>GPT4o [26]</td><td>-</td><td>0.233</td><td>0.144</td><td>0.425</td><td>0.234</td><td>0.128</td><td>0.399</td><td>0.409</td><td>0.606</td><td>0.329</td><td>0.251</td></tr><tr><td>InternVL3-78B [42]</td><td>6790</td><td>0.218</td><td>0.117</td><td>0.38</td><td>0.279</td><td>0.095</td><td>0.296</td><td>0.21</td><td>0.533</td><td>0.282</td><td>0.161</td></tr><tr><td>Qwen2.5-VL-72B [5]</td><td>3949</td><td>0.214</td><td>0.092</td><td>0.315</td><td>0.341</td><td>0.106</td><td>0.261</td><td>0.18</td><td>0.434</td><td>0.262</td><td>0.168</td></tr><tr><td>dots.ocr [30]</td><td>3949</td><td>0.182</td><td>0.137</td><td>0.320</td><td>0.166</td><td>0.182</td><td>0.261</td><td>0.229</td><td>0.468</td><td>0.160</td><td>0.261</td></tr><tr><td>Gemini2.5-Pro [4]</td><td>-</td><td>0.148</td><td>0.055</td><td>0.356</td><td>0.13</td><td>0.049</td><td>0.212</td><td>0.168</td><td>0.439</td><td>0.119</td><td>0.121</td></tr><tr><td>MinerU2.0 [34]</td><td>6790</td><td>0.133</td><td>0.045</td><td>0.273</td><td>0.15</td><td>0.066</td><td>0.238</td><td>0.115</td><td>0.506</td><td>0.209</td><td>0.122</td></tr><tr><td>dots.ocr†200dpi [30]</td><td>5545</td><td>0.125</td><td>0.032</td><td>0.329</td><td>0.099</td><td>0.04</td><td>0.16</td><td>0.066</td><td>0.416</td><td>0.092</td><td>0.067</td></tr><tr><td colspan=\"13\"><strong>DeepSeek-OCR (end2end)</strong></td></tr><tr><td>Tiny</td><td>64</td><td>0.386</td><td>0.373</td><td>0.469</td><td>0.422</td><td>0.283</td><td>0.361</td><td>0.307</td><td>0.635</td><td>0.266</td><td>0.236</td></tr><tr><td>Small</td><td>100</td><td>0.221</td><td>0.142</td><td>0.373</td><td>0.242</td><td>0.125</td><td>0.284</td><td>0.24</td><td>0.53</td><td>0.159</td><td>0.205</td></tr><tr><td>Base</td><td>256(182)</td><td>0.137</td><td>0.054</td><td>0.267</td><td>0.163</td><td>0.064</td><td>0.24</td><td>0.205</td><td>0.474</td><td>0.1</td><td>0.181</td></tr><tr><td>Large</td><td>400(285)</td><td>0.138</td><td>0.054</td><td>0.277</td><td>0.152</td><td>0.067</td><td>0.208</td><td>0.143</td><td>0.461</td><td>0.104</td><td>0.123</td></tr><tr><td>Gundam</td><td>795</td><td>0.127</td><td>0.043</td><td>0.269</td><td>0.134</td><td>0.062</td><td>0.181</td><td>0.097</td><td>0.432</td><td>0.089</td><td>0.103</td></tr><tr><td>Gundam-M†200dpi</td><td>1853</td><td>0.123</td><td>0.049</td><td>0.242</td><td>0.147</td><td>0.056</td><td>0.157</td><td>0.087</td><td>0.377</td><td>0.08</td><td>0.085</td></tr></tbody></table>",
            "bbox": [
                203,
                484,
                1443,
                1641
            ],
            "block_id": 90,
            "page_index": 11
        },
        {
            "block_content": "without layout:\"<image>\\nFree OCR.\" to control the model's output format. Nevertheless, the output format still cannot completely match Fox benchmarks, so the actual performance would be somewhat higher than the test results.",
            "bbox": [
                185,
                1702,
                1460,
                1819
            ],
            "block_id": 91,
            "page_index": 11
        },
        {
            "block_content": "As shown in Table 2, within a $10\\times$ compression ratio, the model's decoding precision can reach approximately 97%, which is a very promising result. In the future, it may be possible to achieve nearly $10\\times$ lossless contexts compression through text-to-image approaches. When the compression ratio exceeds $10\\times$, performance begins to decline, which may have two reasons: one is that the layout of long documents becomes more complex, and another reason may be that long texts become blurred at $512\\times 512$ or $640\\times 640$ resolution. The first issue can be solved by rendering texts onto a single layout page, while we believe the second issue will become",
            "bbox": [
                185,
                1833,
                1465,
                2105
            ],
            "block_id": 92,
            "page_index": 11
        },
        {
            "block_content": "a feature of the forgetting mechanism. When compressing tokens by nearly $ 20\\times $ , we find that precision can still approach $ 60\\% $ . These results indicate that optical contexts compression is a very promising and worthwhile research direction, and this approach does not bring any overhead because it can leverage VLM infrastructure, as multimodal systems inherently require an additional vision encoder.",
            "bbox": [
                185,
                238,
                1463,
                428
            ],
            "block_id": 93,
            "page_index": 12
        },
        {
            "block_content": "Table 4 | Edit distances for different categories of documents in OmniDocBench. The results show that some types of documents can achieve good performance with just 64 or 100 vision tokens, while others require Gundam mode.",
            "bbox": [
                188,
                446,
                1460,
                563
            ],
            "block_id": 94,
            "page_index": 12
        },
        {
            "block_content": "<table><thead><tr><th>Mode \\ Type</th><th>Book Slides</th><th>Financial Report</th><th>Textbook</th><th>Exam Paper</th><th>Magazine</th><th>Academic Papers</th><th>Notes</th><th>Newspaper</th><th>Overall</th></tr></thead><tbody><tr><td>Tiny</td><td>0.147</td><td>0.116</td><td>0.207</td><td>0.173</td><td>0.294</td><td>0.201</td><td>0.395</td><td>0.297</td><td>0.94</td><td>0.32</td></tr><tr><td>Small</td><td>0.085</td><td>0.111</td><td>0.079</td><td>0.147</td><td>0.171</td><td>0.107</td><td>0.131</td><td>0.187</td><td>0.744</td><td>0.205</td></tr><tr><td>Base</td><td>0.037</td><td>0.08</td><td>0.027</td><td>0.1</td><td>0.13</td><td>0.073</td><td>0.052</td><td>0.176</td><td>0.645</td><td>0.156</td></tr><tr><td>Large</td><td>0.038</td><td>0.108</td><td>0.022</td><td>0.084</td><td>0.109</td><td>0.06</td><td>0.053</td><td>0.155</td><td>0.353</td><td>0.117</td></tr><tr><td>Gundam</td><td>0.035</td><td>0.085</td><td>0.289</td><td>0.095</td><td>0.094</td><td>0.059</td><td>0.039</td><td>0.153</td><td>0.122</td><td>0.083</td></tr><tr><td>Guandam-M</td><td>0.052</td><td>0.09</td><td>0.034</td><td>0.091</td><td>0.079</td><td>0.079</td><td>0.048</td><td>0.1</td><td>0.099</td><td>0.077</td></tr></tbody></table>",
            "bbox": [
                208,
                589,
                1438,
                886
            ],
            "block_id": 95,
            "page_index": 12
        },
        {
            "block_content": "## 4.2. OCR Practical Performance",
            "bbox": [
                190,
                968,
                638,
                1003
            ],
            "block_id": 96,
            "page_index": 12
        },
        {
            "block_content": "DeepSeek-OCR is not only an experimental model; it has strong practical capabilities and can construct data for LLM/VLM pretraining. To quantify OCR performance, we test DeepSeek-OCR on OmniDocBench [27], with results shown in Table 3. Requiring only 100 vision tokens (640x640 resolution), DeepSeek-OCR surpasses GOT-OCR2.0 [38] which uses 256 tokens; with 400 tokens (285 valid tokens, $1280\\times 1280$ resolution), it achieves on-par performance with state-of-the-arts on this benchmark. Using fewer than 800 tokens (Gundam mode), DeepSeek-OCR outperforms MinerU2.0 [34] which needs nearly 7,000 vision tokens. These results demonstrate that our DeepSeek-OCR model is powerful in practical applications, and because the higher tokens compression, it enjoys a higher research ceiling.",
            "bbox": [
                186,
                1029,
                1465,
                1372
            ],
            "block_id": 97,
            "page_index": 12
        },
        {
            "block_content": "As shown in Table 4, some categories of documents require very few tokens to achieve satisfactory performance, such as slides which only need 64 vision tokens. For book and report documents, DeepSeek-OCR can achieve good performance with only 100 vision tokens. Combined with the analysis from Section 4.1, this may be because most text tokens in these document categories are within 1,000, meaning the vision-token compression ratio does not exceed $10\\times$. For newspapers, Gundam or even Gundam-master mode is required to achieve acceptable edit distances, because the text tokens in newspapers are 4-5,000, far exceeding the $10\\times$ compression of other modes. These experimental results further demonstrate the boundaries of contexts optical compression, which may provide effective references for researches on the vision token optimization in VLMs and context compression, forgetting mechanisms in LLMs.",
            "bbox": [
                185,
                1387,
                1463,
                1768
            ],
            "block_id": 98,
            "page_index": 12
        },
        {
            "block_content": "## 4.3. Qualitative Study",
            "bbox": [
                188,
                1817,
                507,
                1857
            ],
            "block_id": 99,
            "page_index": 12
        },
        {
            "block_content": "## 4.3.1. Deep parsing",
            "bbox": [
                190,
                1880,
                463,
                1920
            ],
            "block_id": 100,
            "page_index": 12
        },
        {
            "block_content": "DeepSeek-OCR possesses both layout and OCR 2.0 capabilities, enabling it to further parse images within documents through secondary model calls, a feature we refer to as \"deep parsing\". As shown in Figures 7,8,9,10, our model can perform deep parsing on charts, geometry, chemical formulas, and even natural images, requiring only a unified prompt.",
            "bbox": [
                186,
                1941,
                1463,
                2095
            ],
            "block_id": 101,
            "page_index": 12
        },
        {
            "block_content": "A European defense renaissance likely ahead",
            "bbox": [
                914,
                1284,
                1164,
                1302
            ],
            "block_id": 102,
            "page_index": 13
        },
        {
            "block_content": "A much more adverse tariff base case",
            "bbox": [
                258,
                535,
                431,
                549
            ],
            "block_id": 103,
            "page_index": 13
        },
        {
            "block_content": "## Macro news and views",
            "bbox": [
                254,
                341,
                530,
                367
            ],
            "block_id": 104,
            "page_index": 13
        },
        {
            "block_content": "## We provide a brief snapshot on the most important economies for the global markets",
            "bbox": [
                254,
                369,
                678,
                385
            ],
            "block_id": 105,
            "page_index": 13
        },
        {
            "block_content": "## US",
            "bbox": [
                372,
                390,
                391,
                402
            ],
            "block_id": 106,
            "page_index": 13
        },
        {
            "block_content": "Latest GS proprietary datapoints/major changes in views  \n- We now assume a $70\\%$ increase in the US effective tariff rate. IVs 45p prior to reapplied tariffs and further increase in product-specific tariffs now seem likely.",
            "bbox": [
                256,
                402,
                499,
                446
            ],
            "block_id": 107,
            "page_index": 13
        },
        {
            "block_content": "- We raised our Dec 2025 core inflation rate to $3\\%$ from $(3.9\\%)$, lowered our 2025 GDP growth forecast to $1.7\\%$ from $1.8\\%$ and increased our 2026 GDP growth forecast to $2.5\\%$ and slightly raised our end-2025 unemployment rate forecast to $4.2\\%$ from $4.1\\%$ and our 12m recession forecast to $4.3\\%$ from $4.2\\%$.",
            "bbox": [
                258,
                444,
                499,
                512
            ],
            "block_id": 108,
            "page_index": 13
        },
        {
            "block_content": "- Fed cuts; we still expect two in 2025 and one more in 2026.",
            "bbox": [
                258,
                519,
                497,
                542
            ],
            "block_id": 109,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/185472ff-3bc6-41e6-911f-e77bf1b55efa_split_13_0110.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=DnCsH2oDx14WupX6R5AN0kZZ9%2Bs%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                258,
                552,
                492,
                704
            ],
            "block_id": 110,
            "page_index": 13
        },
        {
            "block_content": "Source Goldman Sachs GR",
            "bbox": [
                259,
                701,
                348,
                715
            ],
            "block_id": 111,
            "page_index": 13
        },
        {
            "block_content": "## Europe",
            "bbox": [
                363,
                718,
                400,
                734
            ],
            "block_id": 112,
            "page_index": 13
        },
        {
            "block_content": "Latest GS property datapoints/major changes in views  \n- We recently raised our 2015/2026/2027 euro area real GDP growth forecast to $3.8\\%$ and projected a $4.9\\%$ increase in turn, our ECB terminal rate forecast to $2\\%$ in Jun from $1.75\\%$ in Jul to reflect the higher European defense spending.",
            "bbox": [
                256,
                732,
                496,
                797
            ],
            "block_id": 113,
            "page_index": 13
        },
        {
            "block_content": "- Germany's substantial fiscal package, which we expect to pass, though it is far from a done deal given political hurdles. Potential Russia-Ukraine ceasefire, which we think would be a major factor in the conflict, entails a comprehensive resolution to the conflict $(+0.5\\%)$.",
            "bbox": [
                258,
                809,
                499,
                865
            ],
            "block_id": 114,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/e19010c6-ed2f-457e-958a-79f7c36aa80f_split_13_0115.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=oG0G%2B0sfYbB48UtQ7aqX3wVom70%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                258,
                870,
                494,
                1050
            ],
            "block_id": 115,
            "page_index": 13
        },
        {
            "block_content": "## Japan",
            "bbox": [
                616,
                390,
                648,
                404
            ],
            "block_id": 116,
            "page_index": 13
        },
        {
            "block_content": "Latest GS proprietary datapoints/major changes in views No major changes in views",
            "bbox": [
                509,
                404,
                745,
                432
            ],
            "block_id": 117,
            "page_index": 13
        },
        {
            "block_content": "- $Bo$ policy: we expect the $Bo$ to continue raising rates at a pace of two per year, with next the hike in July.",
            "bbox": [
                509,
                435,
                745,
                458
            ],
            "block_id": 118,
            "page_index": 13
        },
        {
            "block_content": "- Shunto spring wage negotiations, we expect a shunto base pay rise of least in the low 3% range for this year, with risks to the base pay and wage growth.",
            "bbox": [
                509,
                458,
                749,
                491
            ],
            "block_id": 119,
            "page_index": 13
        },
        {
            "block_content": "- Japanese consumer sentiment, which softened for a third consecutive month in February.",
            "bbox": [
                509,
                491,
                744,
                514
            ],
            "block_id": 120,
            "page_index": 13
        },
        {
            "block_content": "- Japan's industrial production, which fell for a third consecutive month in January.",
            "bbox": [
                507,
                509,
                712,
                533
            ],
            "block_id": 121,
            "page_index": 13
        },
        {
            "block_content": "A strong spring wage negotiation season",
            "bbox": [
                509,
                533,
                696,
                549
            ],
            "block_id": 122,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c1c7da9d-669e-42f4-8888-29bcb575492a_split_13_0123.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=zjbpc3JPFXmNw87AnUx8Px5IjRs%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                507,
                556,
                750,
                718
            ],
            "block_id": 123,
            "page_index": 13
        },
        {
            "block_content": "## Emerging Markets (EM)",
            "bbox": [
                578,
                720,
                684,
                734
            ],
            "block_id": 124,
            "page_index": 13
        },
        {
            "block_content": "Latest GS proprietary datapoints/major changes in views No major changes in views",
            "bbox": [
                507,
                734,
                744,
                764
            ],
            "block_id": 125,
            "page_index": 13
        },
        {
            "block_content": "Datapoints/trends we're focused on",
            "bbox": [
                507,
                755,
                659,
                769
            ],
            "block_id": 126,
            "page_index": 13
        },
        {
            "block_content": "- China growth; we expect high-tech manufacturing to continue playing an important role in supporting China's growth ahead.\n- China CPI inflation, which fell sharply in February, though this is not surprising given the economic relations related to the earlier-than-usual Lunar New Year holiday.",
            "bbox": [
                507,
                767,
                755,
                820
            ],
            "block_id": 127,
            "page_index": 13
        },
        {
            "block_content": "- India's cyclical growth slowdown, the worst of which we think is now over, but we expect an ongoing recovery.\n- CEEMEA growth, which would benefit from a potential resolution to the Russia-Ukraine conflict.",
            "bbox": [
                507,
                818,
                740,
                865
            ],
            "block_id": 128,
            "page_index": 13
        },
        {
            "block_content": "Goldman Sachs Global Investment Research",
            "bbox": [
                254,
                1057,
                388,
                1073
            ],
            "block_id": 129,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f5cd54b3-aa20-4acd-897a-39b4d022a886_split_13_0130.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=vHWHyHK3vpz9LdsvN76FvH1H8%2Bk%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                506,
                863,
                754,
                1050
            ],
            "block_id": 130,
            "page_index": 13
        },
        {
            "block_content": "Input image",
            "bbox": [
                426,
                1087,
                564,
                1118
            ],
            "block_id": 131,
            "page_index": 13
        },
        {
            "block_content": "<image>\\nParse the figure.",
            "bbox": [
                215,
                1143,
                471,
                1171
            ],
            "block_id": 132,
            "page_index": 13
        },
        {
            "block_content": "Deep Parsing",
            "bbox": [
                375,
                1822,
                535,
                1857
            ],
            "block_id": 133,
            "page_index": 13
        },
        {
            "block_content": "## Top of Mind",
            "bbox": [
                914,
                362,
                959,
                378
            ],
            "block_id": 134,
            "page_index": 13
        },
        {
            "block_content": "## Macro news and views",
            "bbox": [
                916,
                383,
                1172,
                406
            ],
            "block_id": 135,
            "page_index": 13
        },
        {
            "block_content": "## We provide a brief snapshot on the most important economies for the global markets.",
            "bbox": [
                916,
                406,
                1311,
                432
            ],
            "block_id": 136,
            "page_index": 13
        },
        {
            "block_content": "## US",
            "bbox": [
                1025,
                425,
                1046,
                439
            ],
            "block_id": 137,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f5f5b11e-a073-4b92-9220-9a9f0ca53a56_split_13_0138.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=AdWHYGFIPfTuH%2FNVe0ZJJ7SjfTY%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                218,
                1178,
                731,
                1506
            ],
            "block_id": 138,
            "page_index": 13
        },
        {
            "block_content": "- Test QS GDP deteriorates/major changes in the US effective tariff rate. - We now assume a 10ppp increase in the effective tariff rate. - A 4ppp prior to recalcitrant tariffs and further increases in product-specific tariffs now seem likely.",
            "bbox": [
                919,
                437,
                1146,
                479
            ],
            "block_id": 139,
            "page_index": 13
        },
        {
            "block_content": "<table border=\"1\"><tr><td></td><td>2024</td><td>2025</td><td>2026</td><td>2027</td></tr><tr><td>Germany</td><td>2.1</td><td>2.3</td><td>2.7</td><td>3.0</td></tr><tr><td>France</td><td>2.05</td><td>2.15</td><td>2.4</td><td>2.8</td></tr><tr><td>Italy</td><td>1.45</td><td>1.65</td><td>2.05</td><td>2.55</td></tr><tr><td>Spain</td><td>1.25</td><td>1.55</td><td>2.0</td><td>2.55</td></tr><tr><td>Euro area</td><td>1.85</td><td>2.05</td><td>2.4</td><td>2.8</td></tr></table>",
            "bbox": [
                253,
                1520,
                699,
                1801
            ],
            "block_id": 140,
            "page_index": 13
        },
        {
            "block_content": "We raised our Dec 2025 core PSE inflation forecast to $3% from 2.5%, based on our 2025 GDP growth forecast to $4.1% and the latest revised 2026 GDP forecast to $4.8%. We also raised our 2.5-years and slightly raised our end-2025 unemployment rate to $7.9% and our latest revised 2026 unemployment rate to $7.6% (from 20% to 15%) in refect of our new base case data.",
            "bbox": [
                924,
                479,
                1146,
                540
            ],
            "block_id": 141,
            "page_index": 13
        },
        {
            "block_content": "- Fed cuts, we still expect two in 2025 and one more in 2026.\n- More advanced hedge fund base case.",
            "bbox": [
                919,
                544,
                1144,
                577
            ],
            "block_id": 142,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/2161966c-d229-45b7-9e00-73ff30cead1b_split_13_0143.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=z%2FuW3bma68QqZVFbNOikTwqEpyA%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                917,
                577,
                1146,
                713
            ],
            "block_id": 143,
            "page_index": 13
        },
        {
            "block_content": "Source Goldman Sachs GW.",
            "bbox": [
                919,
                713,
                1008,
                727
            ],
            "block_id": 144,
            "page_index": 13
        },
        {
            "block_content": "## Europe",
            "bbox": [
                1017,
                727,
                1055,
                741
            ],
            "block_id": 145,
            "page_index": 13
        },
        {
            "block_content": "Goldman Sachs Global Investment Research",
            "bbox": [
                916,
                1038,
                1040,
                1057
            ],
            "block_id": 146,
            "page_index": 13
        },
        {
            "block_content": "- Most GSI quantitative datapoints/major changes in latest week. We recently raised our 2020/2022/2023 area real GDP growth forecast to $1.5 per cent, and revised the 2021/2022/2023 area real GDP growth forecast to $1.4 per cent in turn, our ECB terminal rate forecast to 2% in June from the latest week. The latest weekly rate forecast is $1.6 per cent, pending we expect next year the new low level.",
            "bbox": [
                919,
                739,
                1142,
                809
            ],
            "block_id": 147,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f75084ea-b769-498f-a224-15ddea596c35_split_13_0148.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=2mAKur1rZadAF29NM3fa%2FRfaBvA%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                917,
                872,
                1146,
                1033
            ],
            "block_id": 148,
            "page_index": 13
        },
        {
            "block_content": "## Japan",
            "bbox": [
                1255,
                423,
                1286,
                437
            ],
            "block_id": 149,
            "page_index": 13
        },
        {
            "block_content": "- latest US quantitative datapoints/major changes in views\n- No more changes in views on\nDatapoints/trends we're focused on\n- The latest data from Fed to continue hikating rates at a pace of two per week (half year) with the next hike in July.\n- Shunto spring wage negotiations; we expect a shuttle base for the next three months, and we are looking to skype up the issued strong wage requests.\n- Japanese consumer sentiment, which softened for a third quarter, is improving.\n- Japan's industrial production, which fell for a third consecutive month in January.\n\n- strong spring wage negotiation season",
            "bbox": [
                1152,
                439,
                1376,
                577
            ],
            "block_id": 150,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c35ea21f-1f83-40c5-a553-427ee40d4277_split_13_0151.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688351&Signature=YlVJHFODW9iv9%2BaS2EhR4wK8ohI%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                1152,
                575,
                1379,
                729
            ],
            "block_id": 151,
            "page_index": 13
        },
        {
            "block_content": "## Emerging Markets (EM)",
            "bbox": [
                1217,
                729,
                1321,
                743
            ],
            "block_id": 152,
            "page_index": 13
        },
        {
            "block_content": "*test GS proprietary datapoints/minor changes in views No major changes in views.",
            "bbox": [
                1152,
                743,
                1376,
                771
            ],
            "block_id": 153,
            "page_index": 13
        },
        {
            "block_content": "- China growth, we expect high tech manufacturing to continue playing an important role in supporting China's growth ahead.\n- The China inflation, which fell sharply in February, though this is expected to slow down as the reader-related to earlier-time Lunar New Year holiday.",
            "bbox": [
                1154,
                774,
                1384,
                823
            ],
            "block_id": 154,
            "page_index": 13
        },
        {
            "block_content": "- India's cyclical growth slowdown, the word of which we think is now over, but we expect an only gradual recovery.\n- CEEMEA growth, which would benefit from a potential revolution in the Russia-Iran conflict",
            "bbox": [
                1152,
                820,
                1372,
                863
            ],
            "block_id": 155,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/bb3457d3-e810-4785-9e61-40303747422e_split_13_0156.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=fuqc8v689BdDdOXdNcaVixAjL1s%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                1151,
                867,
                1379,
                1031
            ],
            "block_id": 156,
            "page_index": 13
        },
        {
            "block_content": "## Result",
            "bbox": [
                1106,
                1080,
                1184,
                1108
            ],
            "block_id": 157,
            "page_index": 13
        },
        {
            "block_content": "## Europe",
            "bbox": [
                914,
                1127,
                960,
                1148
            ],
            "block_id": 158,
            "page_index": 13
        },
        {
            "block_content": "## Latest GS proprietary datapoints/major changes in views",
            "bbox": [
                914,
                1155,
                1227,
                1174
            ],
            "block_id": 159,
            "page_index": 13
        },
        {
            "block_content": "We recently raised our 2025/2026/2027 Euro area real GDP forecasts to $0.83\\% /1.15\\% /1.3\\%$ (from $0.7\\% /1.15\\% /1.3\\%$), and in our Euro ECB rate forecast increase of $2\\%$ in June (in $1.75\\%$ vs. July) to reflect the higher European spending we expect over the next year.",
            "bbox": [
                913,
                1176,
                1376,
                1216
            ],
            "block_id": 160,
            "page_index": 13
        },
        {
            "block_content": "Datapoints/trends we're focused on",
            "bbox": [
                914,
                1218,
                1116,
                1237
            ],
            "block_id": 161,
            "page_index": 13
        },
        {
            "block_content": "Germany's substantial fiscal package, which we expect to pass, though it's far from a done deal given political hurdles. Potential Russia-Ukraine ceasefire, which we think would result in a middle euro area GDP boost (0.27%), unless it relates to the US-China trade war.",
            "bbox": [
                913,
                1242,
                1372,
                1281
            ],
            "block_id": 162,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c7f1839f-692f-4b2a-9d71-505b44ca0b0c_split_13_0163.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=uwpQJw%2FEtw3sD6sEuaoKovXJwgY%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                967,
                1314,
                1309,
                1553
            ],
            "block_id": 163,
            "page_index": 13
        },
        {
            "block_content": "No major changes in views. Datapoints/trends were focused on BoJ policy; we expect the BoJ to continue hikes rate at a pace of two hikers per week, with the next hike in July. Shuttle wage negotiations would; extend a shuttle base pay rise of less than the low $3% range for this year; with risks skewed to the upside given strong wage requests. Japanese consumer sentiment, which softened for a third consecutive month in February, Japan's industrial production, which fell for a third consecutive month in January.",
            "bbox": [
                908,
                1599,
                1379,
                1653
            ],
            "block_id": 164,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/41f44900-468f-42e1-8c88-fd1d84254ae2_split_13_0165.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=pI%2FCsUXwDhmmNENA%2FAy26f8kScI%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                989,
                1684,
                1305,
                1808
            ],
            "block_id": 165,
            "page_index": 13
        },
        {
            "block_content": "Rendering",
            "bbox": [
                1086,
                1815,
                1212,
                1847
            ],
            "block_id": 166,
            "page_index": 13
        },
        {
            "block_content": "Figure 7 | In the field of financial research reports, the deep parsing mode of DeepSeek-OCR can be used to obtain structured results of charts within documents. Charts are a crucial form of data representation in finance and scientific fields, and the chart structured extraction is an indispensable capability for future OCR models.",
            "bbox": [
                186,
                1896,
                1462,
                2051
            ],
            "block_id": 167,
            "page_index": 13
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/3bec5c81-2a02-483f-bd4a-517f375bdfc2_split_14_0168.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=F4c9cdi734aVpthpTtXqhz8%2FTPQ%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                224,
                320,
                1427,
                1864
            ],
            "block_id": 168,
            "page_index": 14
        },
        {
            "block_content": "Figure 8 | For books and articles, the deep parsing mode can output dense captions for natural images in the documents. With just a prompt, the model can automatically identify what type of image it is and output the required results.",
            "bbox": [
                188,
                1915,
                1460,
                2032
            ],
            "block_id": 169,
            "page_index": 14
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/d9ed8d00-97cc-4d31-97b9-b46971756e95_split_15_0170.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=lVJ0B0Ft1wBTtLaA8lIsvGrkYDM%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                219,
                311,
                1445,
                1875
            ],
            "block_id": 170,
            "page_index": 15
        },
        {
            "block_content": "Figure 9 | DeepSeek-OCR in deep parsing mode can also recognize chemical formulas within chemical documents and convert them to SMILES format. In the future, OCR 1.0+2.0 technology may play a significant role in the development of VLM/LLM in STEM fields.",
            "bbox": [
                186,
                1913,
                1462,
                2034
            ],
            "block_id": 171,
            "page_index": 15
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/c30e9b1c-64bd-417c-8ec2-3e5a3e841395_split_16_0172.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=wsZdeu1apKojWaQMcOBRIdFr3gk%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                205,
                250,
                1429,
                1653
            ],
            "block_id": 172,
            "page_index": 16
        },
        {
            "block_content": "Figure 10 | DeepSeek-OCR also possesses the capability to copy (structure) simple planar geometric figures. Due to the intricate interdependencies among line segments in geometric shapes, parsing geometry task is extremely challenging and has a long way to go.",
            "bbox": [
                186,
                1691,
                1462,
                1812
            ],
            "block_id": 173,
            "page_index": 16
        },
        {
            "block_content": "## 4.3.2. Multilingual recognition",
            "bbox": [
                188,
                1859,
                618,
                1899
            ],
            "block_id": 174,
            "page_index": 16
        },
        {
            "block_content": "PDF data on the Internet contains not only Chinese and English, but also a large amount of multilingual data, which is also crucial when training LLMs. For PDF documents, DeepSeek- OCR can handle nearly 100 languages. Like Chinese and English documents, multilingual data also supports both layout and non-layout OCR formats. The visualization results are shown in Figure 11, where we select Arabic and Sinhala languages to demonstrate results.",
            "bbox": [
                185,
                1922,
                1465,
                2114
            ],
            "block_id": 175,
            "page_index": 16
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/72cd03c4-239a-4b57-bdc1-b188ae957981_split_17_0176.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=z95yvb5hR2CMvUPHJCmWJnzdcns%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                205,
                294,
                1445,
                1805
            ],
            "block_id": 176,
            "page_index": 17
        },
        {
            "block_content": "Figure 11 | To endow the capability of processing widely crawled PDFs (multilingual data), we train our model with OCR capabilities for nearly 100 languages. Minority language documents can also support both layout and non-layout outputs through different prompts.",
            "bbox": [
                186,
                1845,
                1462,
                1967
            ],
            "block_id": 177,
            "page_index": 17
        },
        {
            "block_content": "## 4.3.3. General vision understanding",
            "bbox": [
                190,
                2006,
                686,
                2048
            ],
            "block_id": 178,
            "page_index": 17
        },
        {
            "block_content": "We also provide DeepSeek-OCR with a certain degree of general image understanding capabilities. The related visualization results are shown in Figure 12.",
            "bbox": [
                186,
                2067,
                1465,
                2147
            ],
            "block_id": 179,
            "page_index": 17
        },
        {
            "block_content": "<image>\\nLocate <|ref|>the teacher</|ref|> in the image.",
            "bbox": [
                216,
                647,
                749,
                675
            ],
            "block_id": 180,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/459e232f-8b1d-4064-bc43-f79e55048bd6_split_18_0181.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=6YWFOPZXqPcNVMAv7oxEXTtIY2E%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                208,
                252,
                694,
                622
            ],
            "block_id": 181,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/a4212f01-268a-4858-ab86-b1f8aab9a1f8_split_18_0182.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=HAG24Ulj6CpB7NjCk194vd33Yao%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                726,
                259,
                1099,
                617
            ],
            "block_id": 182,
            "page_index": 18
        },
        {
            "block_content": "A green plastic container labeled for food purposes. The lid is yellow and appears slightly worn out.\n\nOn the front label:\n- At the top left corner, some Chinese characters.\n- In bold black letters near the center-top reads \"6月香\" (June Fragrance).\n- Below that, smaller white font states \"新鲜甜瓜香\" which translates roughly to \"Fresh Sweet Saffron Fruit.\"\n- A small part of the label is large lettering stating \"豆蔻酱,\" meaning \"Bean Paste Sauce.\"",
            "bbox": [
                1071,
                308,
                1443,
                432
            ],
            "block_id": 183,
            "page_index": 18
        },
        {
            "block_content": "Additional information includes:\n- A small circular logo indicating quality assurance (\"优质品质\").\n- An illustration showing what seems like a dish made using bean paste sauce.\n- Text below the main title says \"专注25年, 只做原浆酱\" translating to \"Focusing since 1998, only making authentic fermented bean paste\".\n- On the bottom right side, additional product specifications include \"净含量: $500\\mathrm{g}$\".",
            "bbox": [
                1073,
                439,
                1440,
                519
            ],
            "block_id": 184,
            "page_index": 18
        },
        {
            "block_content": "Overall Style/Type: It looks like commercial packaging designed specifically for preserving food items within the jar. It has clear labeling intended for easy identification and understanding among consumers who read Mandarin.",
            "bbox": [
                1073,
                526,
                1435,
                577
            ],
            "block_id": 185,
            "page_index": 18
        },
        {
            "block_content": "Note: There might be slight variations due to handwriting styles but overall maintains readability regarding brand identity and contents description.",
            "bbox": [
                1075,
                582,
                1402,
                612
            ],
            "block_id": 186,
            "page_index": 18
        },
        {
            "block_content": "<image>\\nldentify all objects in the image and output them in bounding boxes.",
            "bbox": [
                800,
                633,
                1376,
                685
            ],
            "block_id": 187,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/fc249b7a-78e3-492f-854e-757ff7bd7a89_split_18_0188.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=JTENRyhV4Ktovi5ZafL20MQq3ko%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                259,
                682,
                701,
                1015
            ],
            "block_id": 188,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/67aaa422-b93a-4e09-aec7-4360739e8854_split_18_0189.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=8wK30pybpyGtG2XI3GWnsCQFnJo%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                807,
                692,
                1434,
                1087
            ],
            "block_id": 189,
            "page_index": 18
        },
        {
            "block_content": "## <image>\\n这是一张",
            "bbox": [
                221,
                1061,
                411,
                1087
            ],
            "block_id": 190,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/f4147a15-0adb-4c84-b8d4-c5e83a6bdfee_split_18_0191.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=jlGP3kv9ZUnyjxPgFTE1GwGkr4U%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                213,
                1101,
                473,
                1496
            ],
            "block_id": 191,
            "page_index": 18
        },
        {
            "block_content": "，展示了一辆红色的消防栓上有一个笑 显得非常友好和亲切。 消防栓的顶部有一个黑色的盖子，周围有一些金属脚 在消防栓的底部，有一个粉红色的贴纸，上面写着“bowtie”。背景中可以看到一条街道，街道上有几辆停放的汽车和一些树木。 条画面给人一种温馨和友好的感觉。",
            "bbox": [
                484,
                1167,
                654,
                1450
            ],
            "block_id": 192,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/60792794-3a37-43a2-a720-71d32793f546_split_18_0193.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=p1czRBIsFCaCHxNlVDawpWymHIg%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                709,
                1125,
                1099,
                1506
            ],
            "block_id": 193,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/9dba89cb-6cab-41e7-b408-bca0ae1f2a4a_split_18_0194.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688352&Signature=DiFXcJzE%2FrFgbf8qWcDubKGycZo%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                1131,
                1153,
                1422,
                1506
            ],
            "block_id": 194,
            "page_index": 18
        },
        {
            "block_content": "Figure 12 | We retain DeepSeek-OCR's capabilities in general visual understanding, mainly including image description, object detection, grounding, etc. Meanwhile, due to the inclusion of text-only data, DeepSeek-OCR's language capabilities are also retained. Note that since we do not include SFT (Supervised Fine-Tuning) stage, the model is not a chatbot, and some capabilities need completion prompts to be activated.",
            "bbox": [
                186,
                1550,
                1462,
                1742
            ],
            "block_id": 195,
            "page_index": 18
        },
        {
            "block_content": "## 5. Discussion",
            "bbox": [
                190,
                1794,
                426,
                1833
            ],
            "block_id": 196,
            "page_index": 18
        },
        {
            "block_content": "Our work represents an initial exploration into the boundaries of vision-text compression, investigating how many vision tokens are required to decode N text tokens. The preliminary results are encouraging: DeepSeek-OCR achieves near-lossless OCR compression at approximately 10x ratios, while 20x compression still retains 60% accuracy. These findings suggest promising directions for future applications, such as implementing optical processing for dialogue histories beyond k rounds in multi-turn conversations to achieve 10x compression efficiency.",
            "bbox": [
                185,
                1868,
                1465,
                2098
            ],
            "block_id": 197,
            "page_index": 18
        },
        {
            "block_content": "<div style=\"text-align: center;\"><img src=\"https://ai-agent.cn-bj.ufileos.com/03107544-1058-44b2-b940-901b265fabc8_split_19_0198.png?UCloudPublicKey=TOKEN_f8539b44-c9dd-42fc-99b3-d77f6aabbdc1&Expires=1800688353&Signature=WCnxq9DdeveYxqS%2Bgw3%2BPu2qe5M%3D\" alt=\"Image\" width=\"3%\" /></div>\n",
            "bbox": [
                223,
                233,
                1438,
                629
            ],
            "block_id": 198,
            "page_index": 19
        },
        {
            "block_content": "Figure 13 | Forgetting mechanisms constitute one of the most fundamental characteristics of human memory. The contexts optical compression approach can simulate this mechanism by rendering previous rounds of historical text onto images for initial compression, then progressively resizing older images to achieve multi-level compression, where token counts gradually decrease and text becomes increasingly blurred, thereby accomplishing textual forgetting.",
            "bbox": [
                186,
                654,
                1465,
                849
            ],
            "block_id": 199,
            "page_index": 19
        },
        {
            "block_content": "For older contexts, we could progressively downsizing the rendered images to further reduce token consumption. This assumption draws inspiration from the natural parallel between human memory decay over time and visual perception degradation over spatial distance—both exhibit similar patterns of progressive information loss, as shown in Figure 13. By combining these mechanisms, contexts optical compression method enables a form of memory decay that mirrors biological forgetting curves, where recent information maintains high fidelity while distant memories naturally fade through increased compression ratios.",
            "bbox": [
                186,
                902,
                1463,
                1169
            ],
            "block_id": 200,
            "page_index": 19
        },
        {
            "block_content": "While our initial exploration shows potential for scalable ultra-long context processing, where recent contexts preserve high resolution and older contexts consume fewer resources, we acknowledge this is early-stage work that requires further investigation. The approach suggests a path toward theoretically unlimited context architectures that balance information retention with computational constraints, though the practical implications and limitations of such vision-text compression systems warrant deeper study in future research.",
            "bbox": [
                185,
                1185,
                1467,
                1415
            ],
            "block_id": 201,
            "page_index": 19
        },
        {
            "block_content": "## 6. Conclusion",
            "bbox": [
                188,
                1468,
                433,
                1508
            ],
            "block_id": 202,
            "page_index": 19
        },
        {
            "block_content": "In this technical report, we propose DeepSeek-OCR and preliminarily validate the feasibility of contexts optical compression through this model, demonstrating that the model can effectively decode text tokens exceeding 10 times the quantity from a small number of vision tokens. We believe this finding will facilitate the development of VLMs and LLMs in the future. Additionally, DeepSeek-OCR is a highly practical model capable of large-scale pretraining data production, serving as an indispensable assistant for LLMs. Of course, OCR alone is insufficient to fully validate true context optical compression and we will conduct digital-optical text interleaved pretraining, needle-in-a-haystack testing, and other evaluations in the future. From another perspective, optical contexts compression still offers substantial room for research and improvement, representing a promising new direction.",
            "bbox": [
                186,
                1543,
                1465,
                1924
            ],
            "block_id": 203,
            "page_index": 19
        },
        {
            "block_content": "## References",
            "bbox": [
                190,
                231,
                382,
                273
            ],
            "block_id": 204,
            "page_index": 20
        },
        {
            "block_content": "[1] Marker. URL https://github.com/datalab-to/marker.",
            "bbox": [
                203,
                306,
                1091,
                346
            ],
            "block_id": 205,
            "page_index": 20
        },
        {
            "block_content": "[2] Mathpix. URL https://mathpix.com/.",
            "bbox": [
                205,
                364,
                828,
                406
            ],
            "block_id": 206,
            "page_index": 20
        },
        {
            "block_content": "[3] Ocrflux, 2025. URL https://github.com/chatdoc-com/OCRFlux.",
            "bbox": [
                206,
                425,
                1205,
                465
            ],
            "block_id": 207,
            "page_index": 20
        },
        {
            "block_content": "[4] G. AI. Gemini 2.5-pro, 2025. URL https://gemini.google.com/.",
            "bbox": [
                206,
                486,
                1187,
                526
            ],
            "block_id": 208,
            "page_index": 20
        },
        {
            "block_content": "[5] S. Bai, K. Chen, X. Liu, J. Wang, W. Ge, S. Song, K. Dang, P. Wang, S. Wang, J. Tang, H. Zhong, Y. Zhu, M. Yang, Z. Li, J. Wan, P. Wang, W. Ding, Z. Fu, Y. Xu, J. Ye, X. Zhang, T. Xie, Z. Cheng, H. Zhang, Z. Yang, H. Xu, and J. Lin. Qwen2.5-vl technical report. arXiv preprint arXiv:2502.13923, 2025.",
            "bbox": [
                208,
                547,
                1465,
                699
            ],
            "block_id": 209,
            "page_index": 20
        },
        {
            "block_content": "[6] L. Blecher, G. Cucurull, T. Scialom, and R. Stojnic. Nougat: Neural optical understanding for academic documents. arXiv preprint arXiv:2308.13418, 2023.",
            "bbox": [
                206,
                718,
                1460,
                795
            ],
            "block_id": 210,
            "page_index": 20
        },
        {
            "block_content": "[7] J. Chen, L. Kong, H. Wei, C. Liu, Z. Ge, L. Zhao, J. Sun, C. Han, and X. Zhang. Onechart Purify the chart structural extraction via one auxiliary token. In Proceedings of the 32nd ACM International Conference on Multimedia, pages 147-155, 2024.",
            "bbox": [
                206,
                816,
                1463,
                930
            ],
            "block_id": 211,
            "page_index": 20
        },
        {
            "block_content": "[8] Z. Chen, W. Wang, H. Tian, S. Ye, Z. Gao, E. Cui, W. Tong, K. Hu, J. Luo, Z. Ma, et al. How far are we to gpt-4v? closing the gap to commercial multimodal models with open-source suites. arXiv preprint arXiv:2404.16821, 2024.",
            "bbox": [
                206,
                951,
                1462,
                1066
            ],
            "block_id": 212,
            "page_index": 20
        },
        {
            "block_content": "[9] C. Cui, T. Sun, M. Lin, T. Gao, Y. Zhang, J. Liu, X. Wang, Z. Zhang, C. Zhou, H. Liu, et al. Paddleocr 3.0 technical report. arXiv preprint arXiv:2507.05595, 2025.",
            "bbox": [
                206,
                1087,
                1463,
                1164
            ],
            "block_id": 213,
            "page_index": 20
        },
        {
            "block_content": "[10] M. Dehghani, J. Djolonga, B. Mustafa, P. Padlewski, J. Heek, J. Gilmer, A. Steiner, M. Caron, R. Geirhos, I. Alabdulmohsin, et al. Patch n' pack: Navit, a vision transformer for any aspect ratio and resolution. Advances in Neural Information Processing Systems, 36:3632-3656, 2023.",
            "bbox": [
                191,
                1185,
                1465,
                1333
            ],
            "block_id": 214,
            "page_index": 20
        },
        {
            "block_content": "[11] H. Feng, S. Wei, X. Fei, W. Shi, Y. Han, L. Liao, J. Lu, B. Wu, Q. Liu, C. Lin, et al. Dolphin: Document image parsing via heterogeneous anchor prompting. arXiv preprint arXiv:2505.14059, 2025.",
            "bbox": [
                190,
                1356,
                1463,
                1471
            ],
            "block_id": 215,
            "page_index": 20
        },
        {
            "block_content": "[12] Y. Goyal, T. Khot, D. Summers-Stay, D. Batra, and D. Parikh. Making the v in vqa matter: Elevating the role of image understanding in visual question answering. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 6904-6913, 2017.",
            "bbox": [
                190,
                1492,
                1463,
                1609
            ],
            "block_id": 216,
            "page_index": 20
        },
        {
            "block_content": "[13] J. Gu, X. Meng, G. Lu, L. Hou, N. Minzhe, X. Liang, L. Yao, R. Huang, W. Zhang, X. Jiang, et al. Wukong: A 100 million large-scale chinese cross-modal pre-training benchmark. Advances in Neural Information Processing Systems, 35:26418-26431, 2022.",
            "bbox": [
                190,
                1627,
                1465,
                1742
            ],
            "block_id": 217,
            "page_index": 20
        },
        {
            "block_content": "[14] High-flyer. HAI-LLM: Efficient and lightweight training tool for large models, 2023. URL https://www.high-flyer.cn/en/blog/hai-llm.",
            "bbox": [
                190,
                1763,
                1460,
                1840
            ],
            "block_id": 218,
            "page_index": 20
        },
        {
            "block_content": "[15] S. Iyer, X. V. Lin, R. Pasunuru, T. Mihaylov, D. Simig, P. Yu, K. Shuster, T. Wang, Q. Liu, P. S. Koura, et al. Opt-impl: Scaling language model instruction meta learning through the lens of generalization. arXiv preprint arXiv:2212.12017, 2022.",
            "bbox": [
                190,
                1861,
                1463,
                1976
            ],
            "block_id": 219,
            "page_index": 20
        },
        {
            "block_content": "[16] S. Kazemzadeh, V. Ordonez, M. Matten, and T. Berg. Referitgame: Referring to objects in photographs of natural scenes. In Proceedings of the 2014 conference on empirical methods in natural language processing (EMNLP), pages 787-798, 2014.",
            "bbox": [
                190,
                1997,
                1462,
                2112
            ],
            "block_id": 220,
            "page_index": 20
        },
        {
            "block_content": "[17] A. Kirillov, E. Mintun, N. Ravi, H. Mao, C. Rolland, L. Gustafson, T. Xiao, S. Whitehead, A. C. Berg, W.-Y. Lo, et al. Segment anything. arXiv preprint arXiv:2304.02643, 2023.",
            "bbox": [
                190,
                236,
                1463,
                315
            ],
            "block_id": 221,
            "page_index": 21
        },
        {
            "block_content": "[18] Z. Li, Y. Liu, Q. Liu, Z. Ma, Z. Zhang, S. Zhang, Z. Guo, J. Zhang, X. Wang, and X. Bai. Monkeyocr: Document parsing with a structure-recognition-relation triplet paradigm. arXiv preprint arXiv:2506.05218, 2025.",
            "bbox": [
                191,
                336,
                1465,
                451
            ],
            "block_id": 222,
            "page_index": 21
        },
        {
            "block_content": "[19] A. Liu, B. Feng, B. Wang, B. Wang, B. Liu, C. Zhao, C. Dengr, C. Ruan, D. Dai, D. Guo, et al. Deepseek-v2: A strong, economical, and efficient mixture-of-experts language model. arXiv preprint arXiv:2405.04434, 2024.",
            "bbox": [
                191,
                474,
                1463,
                589
            ],
            "block_id": 223,
            "page_index": 21
        },
        {
            "block_content": "[20] A. Liu, B. Feng, B. Xue, B. Wang, B. Wu, C. Lu, C. Zhao, C. Deng, C. Zhang, C. Ruan, et al. Deepseek-v3 technical report. arXiv preprint arXiv:2412.19437, 2024.",
            "bbox": [
                191,
                610,
                1463,
                690
            ],
            "block_id": 224,
            "page_index": 21
        },
        {
            "block_content": "[21] C. Liu, H. Wei, J. Chen, L. Kong, Z. Ge, Z. Zhu, L. Zhao, J. Sun, C. Han, and X. Zhang. Focus anywhere for fine-grained multi-page document understanding. arXiv preprint arXiv:2405.14295, 2024.",
            "bbox": [
                191,
                713,
                1463,
                825
            ],
            "block_id": 225,
            "page_index": 21
        },
        {
            "block_content": "[22] I. Loshchilov and F. Hutter. Sgdr: Stochastic gradient descent with warm restarts. arXiv preprint arXiv:1608.03983, 2016.",
            "bbox": [
                191,
                849,
                1462,
                928
            ],
            "block_id": 226,
            "page_index": 21
        },
        {
            "block_content": "[23] I. Loshchilov and F. Hutter. Decoupled weight decay regularization. In ICLR, 2019.",
            "bbox": [
                191,
                949,
                1377,
                991
            ],
            "block_id": 227,
            "page_index": 21
        },
        {
            "block_content": "[24] A. Masry, D. X. Long, J. Q. Tan, S. Joty, and E. Hoque. Chartqa: A benchmark for question answering about charts with visual and logical reasoning. arXiv preprint arXiv:2203.10244, 2022.",
            "bbox": [
                191,
                1012,
                1462,
                1122
            ],
            "block_id": 228,
            "page_index": 21
        },
        {
            "block_content": "[25] A. Nassar, A. Marafioti, M. Omenetti, M. Lysak, N. Livathinos, C. Auer, L. Morin, R. T. de Lima, Y. Kim, A. S. Gurbuz, et al. Smoldocling: An ultra-compact vision-language model for end-to-end multi-modal document conversion. arXiv preprint arXiv:2503.11576, 2025.",
            "bbox": [
                191,
                1150,
                1465,
                1300
            ],
            "block_id": 229,
            "page_index": 21
        },
        {
            "block_content": "[26] OpenAI. Gpt-4 technical report, 2023.",
            "bbox": [
                191,
                1323,
                767,
                1368
            ],
            "block_id": 230,
            "page_index": 21
        },
        {
            "block_content": "[27] L. Ouyang, Y. Qu, H. Zhou, J. Zhu, R. Zhang, Q. Lin, B. Wang, Z. Zhao, M. Jiang, X. Zhao, et al. Omnidocbench: Benchmarking diverse pdf document parsing with comprehensive annotations. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 24838-24848, 2025.",
            "bbox": [
                190,
                1387,
                1465,
                1541
            ],
            "block_id": 231,
            "page_index": 21
        },
        {
            "block_content": "[28] J. Poznanski, A. Rangapur, J. Borchardt, J. Dunkelberger, R. Huff, D. Lin, C. Wilhelm, K. Lo and L. Soldaini. olmocr: Unlocking trillions of tokens in pdfs with vision language models. arXiv preprint arXiv:2502.18443, 2025.",
            "bbox": [
                190,
                1562,
                1463,
                1679
            ],
            "block_id": 232,
            "page_index": 21
        },
        {
            "block_content": "[29] A. Radford, J.W.Kim,C.Hallacy,A.Ramesh,G.Goh,S.Agarwal,G.Sastry,A. Askell P.Mishkin,J.Clark,etal.Learning transferable visual models from natural language supervision.In International conference on machine learning, pages 8748-8763.PMLR, 2021.",
            "bbox": [
                191,
                1700,
                1465,
                1850
            ],
            "block_id": 233,
            "page_index": 21
        },
        {
            "block_content": "[30] Rednote. dots.ocr, 2025. URL https://github.com/rednote-hilab/dots.ocr.",
            "bbox": [
                191,
                1878,
                1392,
                1917
            ],
            "block_id": 234,
            "page_index": 21
        },
        {
            "block_content": "[31] C. Schuhmann, R. Vencu, R. Beaumont, R. Kaczmarczyk, C. Mullis, A. Katta, T. Coombes, J. Jitsev, and A. Komatsuzaki. Laion-400m: Open dataset of clip-filtered 400 million image-text pairs. arXiv preprint arXiv:2111.02114, 2021.",
            "bbox": [
                191,
                1939,
                1465,
                2053
            ],
            "block_id": 235,
            "page_index": 21
        },
        {
            "block_content": "[32] A. Singh, V. Natarajan, M. Shah, Y. Jiang, X. Chen, D. Batra, D. Parikh, and M. Rohrbach. Towards vqa models that can read. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 8317-8326, 2019.",
            "bbox": [
                190,
                236,
                1465,
                353
            ],
            "block_id": 236,
            "page_index": 22
        },
        {
            "block_content": "[33] T. Sun, C. Cui, Y. Du, and Y. Liu. Pp-doclayout: A unified document layout detection model to accelerate large-scale data construction. arXiv preprint arXiv:2503.17213, 2025.",
            "bbox": [
                190,
                374,
                1460,
                451
            ],
            "block_id": 237,
            "page_index": 22
        },
        {
            "block_content": "[34] B. Wang, C. Xu, X. Zhao, L. Ouyang, F. Wu, Z. Zhao, R. Xu, K. Liu, Y. Qu, F. Shang, et al. Mineru: An open-source solution for precise document content extraction. arXiv preprint arXiv:2409.18839, 2024.",
            "bbox": [
                191,
                474,
                1465,
                587
            ],
            "block_id": 238,
            "page_index": 22
        },
        {
            "block_content": "[35] P. Wang, S. Bai, S. Tan, S. Wang, Z. Fan, J. Bai, K. Chen, X. Liu, J. Wang, W. Ge, et al. Qwen2-vl: Enhancing vision-language model's perception of the world at any resolution. arXiv preprint arXiv:2409.12191, 2024.",
            "bbox": [
                190,
                610,
                1465,
                727
            ],
            "block_id": 239,
            "page_index": 22
        },
        {
            "block_content": "[36] H. Wei, L. Kong, J. Chen, L. Zhao, Z. Ge, J. Yang, J. Sun, C. Han, and X. Zhang. Vary: Scaling up the vision vocabulary for large vision-language model. In European Conference on Computer Vision, pages 408-424. Springer, 2024.",
            "bbox": [
                190,
                748,
                1463,
                867
            ],
            "block_id": 240,
            "page_index": 22
        },
        {
            "block_content": "[37] H. Wei, L. Kong, J. Chen, L. Zhao, Z. Ge, E. Yu, J. Sun, C. Han, and X. Zhang. Small language model meets with reinforced vision vocabulary. arXiv preprint arXiv:2401.12503, 2024.",
            "bbox": [
                191,
                886,
                1463,
                1001
            ],
            "block_id": 241,
            "page_index": 22
        },
        {
            "block_content": "[38] H. Wei, C. Liu, J. Chen, J. Wang, L. Kong, Y. Xu, Z. Ge, L. Zhao, J. Sun, Y. Peng, et al. General ocr theory: Towards ocr-2.0 via a unified end-to-end model. arXiv preprint arXiv:2409.01704, 2024.",
            "bbox": [
                190,
                1024,
                1463,
                1139
            ],
            "block_id": 242,
            "page_index": 22
        },
        {
            "block_content": "[39] H. Wei, Y. Yin, Y. Li, J. Wang, L. Zhao, J. Sun, Z. Ge, X. Zhang, and D. Jiang. Slow perception: Let's perceive geometric figures step-by-step. arXiv preprint arXiv:2412.20631, 2024.",
            "bbox": [
                190,
                1162,
                1463,
                1242
            ],
            "block_id": 243,
            "page_index": 22
        },
        {
            "block_content": "[40] Z. Wu, X. Chen, Z. Pan, X. Liu, W. Liu, D. Dai, H. Gao, Y. Ma, C. Wu, B. Wang, et al. Deepseek-vl2: Mixture-of-experts vision-language models for advanced multimodal understanding. arXiv preprint arXiv:2412.10302, 2024.",
            "bbox": [
                191,
                1263,
                1465,
                1377
            ],
            "block_id": 244,
            "page_index": 22
        },
        {
            "block_content": "[41] W. Yu, Z. Yang, L. Li, J. Wang, K. Lin, Z. Liu, X. Wang, and L. Wang. Mm-vet: Evaluating large multimodal models for integrated capabilities. arXiv preprint arXiv:2308.02490, 2023.",
            "bbox": [
                191,
                1401,
                1463,
                1480
            ],
            "block_id": 245,
            "page_index": 22
        },
        {
            "block_content": "[42] J. Zhu, W. Wang, Z. Chen, Z. Liu, S. Ye, L. Gu, H. Tian, Y. Duan, W. Su, J. Shao, et al. Internvl3: Exploring advanced training and test-time recipes for open-source multimodal models. arXiv preprint arXiv:2504.10479, 2025.",
            "bbox": [
                191,
                1501,
                1463,
                1613
            ],
            "block_id": 246,
            "page_index": 22
        }
    ]
}