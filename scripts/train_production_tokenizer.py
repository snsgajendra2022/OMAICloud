from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.decoders import ByteLevel as ByteLevelDecoder
from tokenizers.normalizers import NFKC

from pathlib import Path
import argparse
import json


SPECIAL_TOKENS = [
    "<pad>",
    "<bos>",
    "<eos>",
    "<unk>",
    "<system>",
    "</system>",
    "<user>",
    "</user>",
    "<assistant>",
    "</assistant>",
]


def iter_text(path: Path):
    with path.open(
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        batch = []

        for line in f:
            line = line.strip()

            if not line:
                continue

            batch.append(line)

            # Pass batches to Rust tokenizer trainer.
            if len(batch) >= 1000:
                yield batch
                batch = []

        if batch:
            yield batch


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
    )

    parser.add_argument(
        "--output",
        default="artifacts/tokenizer-production-65536.json",
    )

    parser.add_argument(
        "--vocab-size",
        type=int,
        default=65536,
    )

    parser.add_argument(
        "--min-frequency",
        type=int,
        default=2,
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(
            f"Corpus not found: {input_path}"
        )

    print(
        json.dumps(
            {
                "stage": "production-tokenizer",
                "input": str(input_path),
                "input_bytes": input_path.stat().st_size,
                "requested_vocab_size": args.vocab_size,
            },
            indent=2,
        )
    )

    tokenizer = Tokenizer(
        BPE(
            unk_token="<unk>",
        )
    )

    tokenizer.normalizer = NFKC()

    tokenizer.pre_tokenizer = ByteLevel(
        add_prefix_space=False,
    )

    tokenizer.decoder = ByteLevelDecoder()

    trainer = BpeTrainer(
        vocab_size=args.vocab_size,
        min_frequency=args.min_frequency,
        special_tokens=SPECIAL_TOKENS,
        initial_alphabet=ByteLevel.alphabet(),
        max_token_length=64,
        show_progress=True,
    )

    print("Training production tokenizer...")

    tokenizer.train_from_iterator(
        iter_text(input_path),
        trainer=trainer,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tokenizer.save(
        str(output_path),
        pretty=True,
    )

    vocab_size = tokenizer.get_vocab_size()

    print(
        json.dumps(
            {
                "status": "complete",
                "output": str(output_path),
                "vocab_size": vocab_size,
                "requested_vocab_size": args.vocab_size,
            },
            indent=2,
        )
    )

    required = {}

    for token in SPECIAL_TOKENS:
        required[token] = tokenizer.token_to_id(token)

    print(
        json.dumps(
            {
                "special_tokens": required,
            },
            indent=2,
        )
    )

    tests = [
        "Hello, my name is OM AI.",
        "You are Memories Assistant.",
        "Python function: def add(a, b): return a + b",
        "नमस्ते OM AI",
    ]

    print("\nRound-trip validation:")

    failed = False

    for text in tests:
        encoded = tokenizer.encode(text)

        decoded = tokenizer.decode(
            encoded.ids,
            skip_special_tokens=True,
        )

        ok = decoded == text

        print(
            json.dumps(
                {
                    "text": text,
                    "tokens": len(encoded.ids),
                    "roundtrip": ok,
                },
                ensure_ascii=False,
            )
        )

        if not ok:
            failed = True

    if vocab_size != args.vocab_size:
        raise SystemExit(
            f"Tokenizer only created {vocab_size} tokens; "
            f"requested {args.vocab_size}. "
            "Use a larger/more varied corpus."
        )

    if any(
        tokenizer.token_to_id(t) is None
        for t in SPECIAL_TOKENS
    ):
        raise SystemExit(
            "Required OM chat tokens are missing."
        )

    if failed:
        raise SystemExit(
            "Tokenizer round-trip validation failed."
        )

    print("\nPRODUCTION TOKENIZER: PASS")


if __name__ == "__main__":
    main()
