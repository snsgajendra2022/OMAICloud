from om_ai.tokenizer import ByteBPETokenizer

def test_roundtrip_unicode():
    text='Hello OM AI — नमस्ते'
    tok=ByteBPETokenizer.train([text,text],vocab_size=300,min_pair_freq=1)
    assert tok.decode(tok.encode(text)) == text
