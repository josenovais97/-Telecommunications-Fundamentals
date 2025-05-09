from PIL import Image, ImageDraw, ImageFont
import random
import argparse

# ─────────────────────────────────────────
# 1. CÓDIGO DE HAMMING (7,4)
# ─────────────────────────────────────────
def hamming_encode(block4):
    d1, d2, d3, d4 = block4
    return [
        d1 ^ d2 ^ d4,  # c1 paridade
        d1 ^ d3 ^ d4,  # c2 paridade
        d1,            # c3 dado
        d2 ^ d3 ^ d4,  # c4 paridade
        d2,            # c5 dado
        d3,            # c6 dado
        d4,            # c7 dado
    ]


def encode_sequence(bits):
    if len(bits) % 4:
        bits += [0] * (4 - len(bits) % 4)
    out = []
    for i in range(0, len(bits), 4):
        out.extend(hamming_encode(bits[i:i + 4]))
    return out


def hamming_decode(block7, correct=True):
    c = block7[:]
    s1 = c[0] ^ c[2] ^ c[4] ^ c[6]
    s2 = c[1] ^ c[2] ^ c[5] ^ c[6]
    s3 = c[3] ^ c[4] ^ c[5] ^ c[6]
    syndrome = s1 + (s2 << 1) + (s3 << 2)

    fixed = 0
    if correct and syndrome and syndrome <= 7:
        c[syndrome - 1] ^= 1
        fixed = 1

    return [c[2], c[4], c[5], c[6]], fixed


def decode_sequence(bits, correct=True):
    decoded, fixed_total = [], 0
    for i in range(0, len(bits), 7):
        data, fixed = hamming_decode(bits[i:i + 7], correct)
        decoded.extend(data)
        fixed_total += fixed
    return decoded, fixed_total

# ─────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────
def simulate_channel(bits, ber):
    return [b ^ 1 if random.random() < ber else b for b in bits]


def count_bit_errors(a, b):
    return sum(x != y for x, y in zip(a, b))


def image_to_bits(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    bits = []
    for r, g, b in img.getdata():
        for v in (r, g, b):
            bits.extend(int(bit) for bit in f"{v:08b}")
    return bits, w, h


def bits_to_image(bits, w, h):
    needed = w * h * 24
    bits = (bits + [0] * (needed - len(bits)))[:needed]
    pixels = []
    for i in range(0, needed, 24):
        r = int("".join(str(b) for b in bits[i:i + 8]), 2)
        g = int("".join(str(b) for b in bits[i + 8:i + 16]), 2)
        b = int("".join(str(b) for b in bits[i + 16:i + 24]), 2)
        pixels.append((r, g, b))
    out = Image.new("RGB", (w, h))
    out.putdata(pixels)
    return out


def annotate_image(img, text):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except:
        font = None
    draw.text((10, 10), text, fill=(255,255,255), font=font)
    return img


def simulate_image_tx(path, ber):
    src_bits, w, h = image_to_bits(path)
    print(f"Imagem: {w}×{h} — {len(src_bits):,} bits de dados")

    enc_bits = encode_sequence(src_bits)
    chan_bits = simulate_channel(enc_bits, ber)
    raw_errors = count_bit_errors(enc_bits, chan_bits)
    print(f"Bits alterados pelo canal: {raw_errors:,}/{len(enc_bits):,} ({raw_errors/len(enc_bits):.4%})")

    dec_bits_corr, fixed = decode_sequence(chan_bits, correct=True)
    residual = count_bit_errors(src_bits[:len(dec_bits_corr)], dec_bits_corr)
    print(f"Bits corrigidos pelo Hamming: {fixed:,}")
    print(f"Erros residuais após correção: {residual:,}/{len(dec_bits_corr):,} ({residual/len(dec_bits_corr):.4%})")

    img_raw = bits_to_image(decode_sequence(chan_bits, correct=False)[0], w, h)
    img_corr = bits_to_image(dec_bits_corr, w, h)
    img_raw = annotate_image(img_raw, "Imagem apos canal (sem correcao)")
    img_corr = annotate_image(img_corr, "Imagem apos canal + correcao")

    return img_raw, img_corr

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simulação de transmissão de imagem com código de Hamming (7,4)')
    parser.add_argument('caminho', help='Path da imagem de entrada')
    parser.add_argument('ber', type=float, help='Taxa de erro de bit (0 a 1)')
    args = parser.parse_args()

    img_ruido, img_corr = simulate_image_tx(args.caminho, args.ber)
    img_ruido.show()
    img_corr.show()
