import torch
import torch.nn as nn
import torch.nn.functional as F


def specified_expert_loss(router_logits: torch.Tensor, router_labels: torch.Tensor) -> float:
    # enforces on average the router should route examples to the correct specified expert given the known origin of the input
    if router_logits is None:
        return 0
    if isinstance(router_logits, tuple):
        batch_size, num_experts = router_logits[0].shape
        router_logits = torch.stack(router_logits, dim=2).transpose(1, 2) # batch_size, num_hidden_layers, num_experts
    else:
        print('Must be tuple of all layers router logits')
    
    avg_logits = router_logits.mean(dim=1)
    return F.cross_entropy(avg_logits, router_labels)


# Adapted from https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/losses/MultipleNegativesRankingLoss.py
def MNR_loss(batch1: torch.Tensor, batch2: torch.Tensor, scale: float = 1.0) -> float:
    """
    batch1, batch2 - both torch.Tensor (batch_size, hidden_size)
    This function takes two batches of vectors and returns the Multiple Negatives Ranking (MNR) loss.
    It uses cosine similarity as the similarity function.
    The output of the similarity function can be multiplied by a scale value.
    """
    scores = F.cosine_similarity(batch1, batch2, dim=-1) * scale
    labels = torch.arange(len(scores), dtype=torch.float, device=scores.device)  # Example batch1[i] should match with batch2[i]
    return F.cross_entropy(scores, labels)


def clip_loss(batch1: torch.Tensor, batch2: torch.Tensor, temp: float = 1.0) -> float:
    """
    batch1, batch2 - both torch.Tensor (batch_size, hidden_size)
    This function takes two batches of vectors and returns the clip loss.
    It uses dot product as the similarity function.
    The output of the similarity function can be divided by a learned temperature value.
    """
    logits = (batch1 @ batch2.T) / temp
    batch1_similarity = batch1 @ batch1.T
    batch2_similarity = batch2 @ batch2.T
    targets = F.softmax((batch1_similarity + batch2_similarity) / 2 * temp, dim=-1)
    batch1_loss = F.cross_entropy(logits, targets.argmax(dim=1))
    batch2_loss = F.cross_entropy(logits.T, targets.T.argmax(dim=1))
    loss =  (batch1_loss + batch2_loss) / 2.0
    return loss


# Adapted from https://github.com/UMass-Foundation-Model/Mod-Squad/blob/1d17e81d090ac7e1a66dd420194c0b7679d820a4/parallel_linear/parallel_experts/moe.py#L25
class MILoss(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.wMI = torch.tensor(config.wMI, requires_grad=False)
        self.MI_task_gate = torch.zeros(config.num_tasks, config.num_experts)
        self.num_experts = config.num_experts
        self.topk = config.topk

    def update_MI_task_gate(self, probs, router_labels):
        """
        Update the MI_task_gate matrix with probabilities of selecting each expert for the current task.

        Args:
        probs (torch.Tensor): The probabilities of selecting each expert for the current task.
                            It should have shape [batch_size * seq_len, num_experts].
        router_labels (torch.Tensor): The labels indicating the task for each example in the batch.
                                    It should have shape [batch_size * seq_len].

        Returns:
        None
        """
        for task in router_labels:
            self.MI_task_gate[task] += probs[router_labels == task].sum(0)

    def calculate_mutual_information_loss(self):
        """
        Calculate the mutual information loss.

        Returns:
        torch.Tensor: The calculated mutual information loss.
        """
        MI_gate = self.MI_task_gate.clone()
        tot = MI_gate.sum() / self.topk
        MI_gate = MI_gate / (tot + 0.0001)
        P_TI = torch.sum(MI_gate, dim=1, keepdim=True) + 0.0001
        P_EI = torch.sum(MI_gate, dim=0, keepdim=True) + 0.0001

        MI_loss = -(MI_gate * torch.log(MI_gate / P_TI / P_EI + 0.0001)).sum()
        return self.wMI * MI_loss

    def call_update(self, router_logits, router_labels):
        router_logits = router_logits.float().detach().cpu()
        router_labels = router_labels.long().detach().cpu()
        probs = router_logits.softmax(dim=-1)
        probs = probs.view(-1, self.num_experts)
        self.update_MI_task_gate(probs, router_labels)

    def forward(self, router_logits: torch.Tensor, router_labels: torch.Tensor) -> torch.Tensor:
        if isinstance(router_logits, tuple):
            for layer_router_logits in router_logits:
                self.call_update(layer_router_logits, router_labels)
        else:
            self.call_update(router_logits, router_labels)
        return self.calculate_mutual_information_loss()


# Adapted from https://github.com/SimiaoZuo/MoEBERT/blob/master/src/transformers/moebert/moe_layer.py
class LoadBalancingLoss(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.wBAL = torch.tensor(config.wBAL, requires_grad=False)
        self.num_experts = config.num_experts

    def forward(self, router_logits: torch.Tensor) -> torch.Tensor: 
        # enforces experts should not be used widely more than another
        num_experts = self.num_experts
        wBAL = torch.abs(self.wBAL)
        if isinstance(router_logits, tuple):
            router_logits = torch.cat(router_logits, dim=0) # batch_size * num_hidden_layers, num_experts
        # can also be batchsize * num_tasks * num_hidden_layers, num_experts
        router_logits = router_logits.reshape(-1, num_experts)
        router_probs = F.softmax(router_logits, dim=-1)
        gate = torch.argmax(router_probs, dim=-1)
        num_tokens = F.one_hot(gate, num_experts).gt(0).sum(0)
        p = router_probs.mean(0)
        temp = num_tokens.float()
        f = temp / temp.sum(0, keepdim=True) 
        return wBAL * num_experts * torch.sum(p * f)