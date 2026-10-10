import torch
import torch.nn.functional as F

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer


def _tiny_model():
    return OMTransformer(
        ModelConfig(
            vocab_size=32,
            max_seq_len=8,
            n_layers=1,
            n_heads=2,
            n_kv_heads=2,
            d_model=16,
            d_ff=32,
            dropout=0.0,
        )
    )


def test_pre_shifted_training_labels_are_not_shifted_twice():
    torch.manual_seed(7)
    model = _tiny_model()
    input_ids = torch.tensor([[1, 2, 3]])
    # Same convention used by the SFT and pretraining datasets: x=ids[:-1],
    # y=ids[1:]. Each logit position must predict its corresponding label.
    labels = torch.tensor([[2, 3, 4]])

    output = model(input_ids, labels=labels)
    expected = F.cross_entropy(
        output["logits"].reshape(-1, 32),
        labels.reshape(-1),
    )

    torch.testing.assert_close(output["loss"], expected)


def test_full_sequence_labels_can_request_explicit_shift():
    torch.manual_seed(7)
    model = _tiny_model()
    input_ids = torch.tensor([[1, 2, 3, 4]])
    labels = input_ids.clone()

    output = model(input_ids, labels=labels, shift_labels=True)
    expected = F.cross_entropy(
        output["logits"][:, :-1, :].reshape(-1, 32),
        labels[:, 1:].reshape(-1),
    )

    torch.testing.assert_close(output["loss"], expected)
