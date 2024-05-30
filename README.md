# Mixture-of-Experts-Sentence-Similarity
 
This repository serves as the official code base for the paper _Contrastive Learning and Mixture of Experts Enables Precise Vector Embeddings_

Logan Hallee, Rohan Kapur, Arjun Patel, Jason P. Gleghorn, and Bohdan Khomtchouk

Preprint: [Contrastive Learning and Mixture of Experts Enables Precise Vector Embeddings](https://arxiv.org/abs/2401.15713)

Peer review: _preparing submission_

## Data and models
[Huggingface](https://huggingface.co/collections/lhallee/sentence-similarity-65fb9545a1731c75dc5dd6a7)

## Main findings
* Extending BERT models with N experts copied from their MLP section is highly effective for fine-tuning on downstream tasks, including multitask or multidomain data.
* N experts are exactly as effective as N individual models trained on N domains for sentence similarity tasks.
* Small BERT models are not more effective with N experts, likely due to small shared attention layers. Our data supports that this threshold may be roughly 100 million parameters.
* Enforced routing of experts can be handled with added special tokens for sentence-wise routing or token type IDs for token-wise routing, even when the router is a single linear layer. Enforced routing can also be accomplished by passing a list of desired indices. Mutual information based loss with top-k outputs also works well to correlate expert activation with specific types of data.
* 
* Cocitation networks are highly effective for gathering similar niche papers.
* Using dot product with a learned temperature may be a more effective contrastive loss than standard Multiple Negatives Ranking loss.

## Applications of this work
* Better vector databases / retrieval augmentation
* Extending any sufficiently large BERT model with N experts for N tasks.
* Vocabulary extension of BERT models with N experts for N vocabularies.

## [Docs](https://github.com/Gleghorn-Lab/Mixture-of-Experts-Sentence-Similarity/tree/main/documentation)

## Please cite
```
@article{hallee2024contrastive,
      title={Contrastive Learning and Mixture of Experts Enables Precise Vector Embeddings}, 
      author={Rohan Kapur and Logan Hallee and Arjun Patel and Jason P. Gleghorn and Bohdan Khomtchouk},
      year={2024},
      eprint={2401.15713},
      archivePrefix={arXiv},
      primaryClass={cs.LG}
}
```
and upvote on [Huggingface](https://huggingface.co/papers/2401.15713)!
